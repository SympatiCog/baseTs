"""Index gaps: gaps() finds them, segments() splits at them, the filters
refuse or warn about them, and info()/get_statistics() count them.

Motivated by a tester's cpCST crash session: 5788 samples over 218.4 s at a
declared 30 Hz, with ten ~2.6 s holes in the index right after each crash.
The NaN guard on the filters catches a hole that is marked (a NaN) but not
one that is unmarked (an index jump), so lowpass_at(2.0) ran a 30 Hz
Butterworth across the ten jumps as if they were single frames.
"""
import warnings

import numpy as np
import pandas as pd
import pytest

from baseTs import baseTs
from baseTs.filters import InvalidParameterError
from baseTs.frame import baseDf
from baseTs.utils import ValidationError

FS = 30.0
DT = 1.0 / FS


def _uniform(n: int = 600) -> baseTs:
    t = np.arange(n) * DT
    return baseTs(np.sin(2 * np.pi * 0.5 * t), t, freq=FS)


def _crash_session(n_gaps: int = 10, missing: int = 77, seconds: float = 220.0) -> baseTs:
    """A 30 Hz session with n_gaps holes, each `missing` frames wide.

    Built in frame counts so every hole is exactly (missing + 1) * DT wide:
    77 missing frames at 30 Hz is the tester's ~2.6 s post-crash hole.
    """
    t = np.arange(0.0, seconds, DT)
    keep = np.ones(len(t), dtype=bool)
    starts = np.linspace(600, len(t) - 600, n_gaps).astype(int)
    for k in starts:
        keep[k + 1:k + 1 + missing] = False
    t = t[keep]
    return baseTs(np.sin(2 * np.pi * 0.5 * t), t, freq=FS)


def _dropped_frames(n: int = 600, drop=(100, 350)) -> baseTs:
    t = np.arange(n) * DT
    t = np.delete(t, list(drop))
    return baseTs(np.sin(t), t)


class TestGaps:
    def test_uniform_series_has_no_gaps(self):
        got = _uniform().gaps()
        assert isinstance(got, pd.DataFrame)
        assert list(got.columns) == ["start", "end", "width", "n_missing"]
        assert len(got) == 0

    def test_crash_session_reports_every_hole(self):
        got = _crash_session().gaps()
        assert len(got) == 10
        assert np.allclose(got["width"], 2.6, atol=2 * DT)
        # 2.6 s at 30 Hz spans 78 intervals, so 77 frames are missing.
        assert np.all(got["n_missing"] == 77)
        assert np.all(got["end"] - got["start"] == got["width"])

    def test_default_threshold_is_the_median_spacing_not_the_mean_rate(self):
        """The mean rate is dragged down by the holes themselves; the median
        interval is the true frame period regardless of how many there are."""
        ts = _dropped_frames()
        assert ts.freq < FS  # the mean rate under-reports
        got = ts.gaps()
        assert len(got) == 2
        assert np.all(got["n_missing"] == 1)

    def test_explicit_max_gap_ignores_narrower_holes(self):
        ts = _crash_session()
        assert len(ts.gaps(max_gap=1.0)) == 10
        assert len(ts.gaps(max_gap=3.0)) == 0

    def test_an_interval_exactly_max_gap_wide_is_not_a_gap(self):
        """'Wider than max_gap' is strict: the boundary belongs to the data."""
        t = np.array([0.0, 1.0, 2.0, 4.0, 5.0])   # one 2.0 s interval
        ts = baseTs(np.arange(5.0), t)
        assert len(ts.gaps(max_gap=2.0)) == 0
        assert len(ts.gaps(max_gap=1.999)) == 1

    def test_start_and_end_are_the_bracketing_samples(self):
        ts = _crash_session(n_gaps=1)
        t = np.asarray(ts.times, float)
        row = ts.gaps().iloc[0]
        i = int(np.argmax(np.diff(t)))
        assert row["start"] == t[i] and row["end"] == t[i + 1]

    def test_fewer_than_two_samples_has_no_gaps(self):
        ts = baseTs(np.array([1.0]), np.array([0.0]))
        assert len(ts.gaps()) == 0

    @pytest.mark.parametrize("bad", [0, -1.0, "1", np.nan, np.inf, True])
    def test_refuses_non_positive_max_gap(self, bad):
        with pytest.raises(ValidationError, match="max_gap"):
            _uniform().gaps(max_gap=bad)


class TestIndexEdgeCases:
    """Findings from adversarial review of the first cut."""

    def test_empty_series_has_no_gaps_and_no_segments(self):
        ts = baseTs(np.array([]), np.array([]))
        assert len(ts.gaps()) == 0
        assert ts.segments() == []

    def test_duplicate_timestamp_at_a_gap_start_splits_after_the_last_copy(self):
        """searchsorted on the start value found the first copy, putting the
        gap inside the next segment."""
        t = np.array([0.0, 1.0, 1.0, 5.0, 6.0])
        segs = baseTs(np.arange(5.0), t).segments(max_gap=2.0)
        assert [list(np.asarray(s.times, float)) for s in segs] == [[0.0, 1.0, 1.0], [5.0, 6.0]]

    def test_decreasing_index_is_refused(self):
        ts = baseTs(np.arange(4.0), np.array([3.0, 2.0, 1.0, 0.0]))
        with pytest.raises(ValidationError, match="non-decreasing"):
            ts.gaps()
        with pytest.raises(ValidationError, match="non-decreasing"):
            ts.segments()

    def test_nan_timestamp_is_refused_not_silently_gap_free(self):
        """A NaN in the index made the median NaN, every comparison False,
        and the filters ran across a real hole with no warning."""
        t = np.arange(100) / FS
        t = np.delete(t, np.arange(50, 60))
        t[5] = np.nan
        ts = baseTs(np.sin(np.arange(len(t))), t)
        with pytest.raises(ValidationError, match="finite"):
            ts.gaps()
        # Filters keep their own exception type, so a caller catching
        # InvalidParameterError keeps catching it.
        with pytest.raises(InvalidParameterError, match="finite"):
            ts.lowpass_at(2.0)
        with pytest.raises(InvalidParameterError, match="finite"):
            ts.gauss_filter(2.0)

    def test_reporting_survives_a_bad_index(self, capsys):
        t = np.arange(10.0)
        t[3] = np.nan
        ts = baseTs(np.arange(10.0), t)
        stats = ts.get_statistics()
        assert np.isnan(stats["n_gaps"]) and np.isnan(stats["gapped_duration"])
        ts.info()
        assert "unavailable" in capsys.readouterr().out

    def test_mostly_duplicated_timestamps_are_refused(self):
        """Half the steps zero-width drove the median to 0, so every normal
        step became a 'gap wider than 0 s' with n_missing=0 (external panel)."""
        t = np.arange(150) * DT
        t[::2] = t[1::2][:len(t[::2])]
        ts = baseTs(np.sin(t), t)
        with pytest.raises(ValidationError, match="duplicate"):
            ts.gaps()
        with pytest.raises(InvalidParameterError, match="duplicate"):
            ts.lowpass_at(2.0)

    def test_degenerate_time_base_still_reports_the_rate_first(self):
        """All timestamps equal breaks the duplicate rule too, but the
        existing contract is 'Invalid sampling frequency' (filters check the
        rate before scanning the data)."""
        ts = baseTs(np.sin(np.arange(200) / 10.0), np.zeros(200))
        with pytest.raises(InvalidParameterError, match="Invalid sampling frequency"):
            ts.lowpass_at(0.1)
        with pytest.raises(InvalidParameterError, match="duplicate"):
            ts.gauss_filter(2.0)   # no rate to check, so the index rule speaks

    def test_statistics_do_not_report_a_median_for_an_index_they_cannot_count(self):
        """median_dt was computed outside the validated path, so a decreasing
        index showed a confident 1.0 next to NaN gap counts."""
        ts = baseTs(np.arange(6.0), np.array([0.0, 1.0, 2.0, 1.5, 3.0, 4.0]))
        stats = ts.get_statistics()
        assert np.isnan(stats["median_dt"]) and np.isnan(stats["n_gaps"])

    def test_n_missing_is_never_negative(self):
        t = np.array([0.0, 1.0, 2.0, 2.2, 3.2, 4.2])
        got = baseTs(np.arange(6.0), t).gaps(max_gap=0.1)   # every interval qualifies
        assert len(got) == 5
        assert (got["n_missing"] >= 0).all()
        assert int(got.loc[got["width"] < 0.5, "n_missing"].iloc[0]) == 0

    def test_half_frame_widths_round_up(self):
        """np.rint rounds half to even, so 2.5 and 3.5 frames went opposite ways."""
        t = np.concatenate([np.arange(0, 10.0), [11.5], np.arange(12.0, 20.0)])   # 9 -> 11.5
        assert int(baseTs(np.arange(len(t)), t).gaps()["n_missing"].iloc[0]) == 2
        t = np.concatenate([np.arange(0, 10.0), [12.5], np.arange(13.0, 20.0)])   # 9 -> 12.5
        assert int(baseTs(np.arange(len(t)), t).gaps()["n_missing"].iloc[0]) == 3

    def test_timing_jitter_does_not_count_as_gaps(self):
        """Software-timestamped streams jitter; +/-30% must stay silent."""
        rng = np.random.default_rng(1)
        t = np.cumsum(DT * rng.uniform(0.7, 1.3, 3000))
        ts = baseTs(np.sin(t), t)
        assert len(ts.gaps()) == 0
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            ts.lowpass_at(2.0)


class TestSegments:
    def test_one_more_segment_than_gaps(self):
        segs = _crash_session().segments()
        assert len(segs) == 11
        assert all(isinstance(s, baseTs) for s in segs)

    def test_segments_concatenate_back_to_the_series(self):
        ts = _crash_session()
        segs = ts.segments()
        data = np.concatenate([np.asarray(s.data, float) for s in segs])
        times = np.concatenate([np.asarray(s.times, float) for s in segs])
        assert np.array_equal(data, np.asarray(ts.data, float))
        assert np.array_equal(times, np.asarray(ts.times, float))

    def test_no_interior_gap_inside_any_segment(self):
        for s in _crash_session().segments():
            assert len(s.gaps()) == 0

    def test_each_segment_derives_its_own_rate(self):
        for s in _crash_session().segments():
            assert np.isclose(s.freq, FS, rtol=1e-6)

    def test_ungapped_series_is_one_segment(self):
        ts = _uniform()
        segs = ts.segments()
        assert len(segs) == 1
        assert segs[0] is not ts

    def test_segment_history_names_its_place(self):
        segs = _crash_session().segments(max_gap=1.0)
        assert any("Segment 1 of 11" in e for e in segs[0].history)
        assert any("Segment 11 of 11" in e for e in segs[-1].history)
        assert any("max_gap=1.0s" in e for e in segs[0].history)

    def test_segment_keeps_signal_name_and_offset(self):
        ts = _crash_session(n_gaps=1)
        ts.signal_name = "cpCST"
        ts.set_timestamp_offset(1_700_000_000.0)
        seg = ts.segments()[1]
        assert seg.signal_name == "cpCST"
        assert seg.ts_offset == 1_700_000_000.0

    @pytest.mark.parametrize("bad", [0, -1.0, "1", np.nan, np.inf, True])
    def test_refuses_non_positive_max_gap(self, bad):
        with pytest.raises(ValidationError, match="max_gap"):
            _uniform().segments(max_gap=bad)


FILTERS = [
    ("lowpass_at", lambda ts, **kw: ts.lowpass_at(2.0, **kw)),
    ("highpass_at", lambda ts, **kw: ts.highpass_at(0.2, **kw)),
    ("bandpass_at", lambda ts, **kw: ts.bandpass_at(0.2, 2.0, **kw)),
    ("notch_at", lambda ts, **kw: ts.notch_at(5.0, **kw)),
    ("butterpass_at", lambda ts, **kw: ts.butterpass_at(0.2, 2.0, **kw)),
    ("gauss_filter", lambda ts, **kw: ts.gauss_filter(2.0, **kw)),
    ("sg_filter", lambda ts, **kw: ts.sg_filter(11, 2, **kw)),
    ("lowpass_filter", lambda ts, **kw: ts.lowpass_filter(2.0, **kw)),
    ("highpass_filter", lambda ts, **kw: ts.highpass_filter(0.2, **kw)),
    ("bandpass_filter", lambda ts, **kw: ts.bandpass_filter(0.2, 2.0, **kw)),
    ("notch_filter", lambda ts, **kw: ts.notch_filter(5.0, **kw)),
]
IDS = [f[0] for f in FILTERS]


class TestFiltersRefuseIndexGaps:
    @pytest.mark.parametrize("name, run", FILTERS, ids=IDS)
    def test_max_gap_refuses_a_gapped_index_with_the_remedy(self, name, run):
        with pytest.raises(InvalidParameterError,
                           match=r"10 gap\(s\) wider than 0.5 s.*segments\(\)"):
            run(_crash_session(), max_gap=0.5)

    @pytest.mark.parametrize("name, run", FILTERS, ids=IDS)
    def test_max_gap_passes_a_clean_index(self, name, run):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            out = run(_uniform(), max_gap=0.5)
        assert isinstance(out, baseTs)

    @pytest.mark.parametrize("name, run", FILTERS, ids=IDS)
    def test_default_warns_on_a_gapped_index(self, name, run):
        with pytest.warns(UserWarning, match=r"10 gap\(s\)"):
            run(_crash_session())

    @pytest.mark.parametrize("name, run", FILTERS, ids=IDS)
    def test_default_is_silent_on_a_clean_index(self, name, run):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            run(_uniform())

    def test_refusal_message_names_widest_gap_and_both_remedies(self):
        with pytest.raises(InvalidParameterError) as info:
            _crash_session().lowpass_at(2.0, max_gap=0.5)
        msg = str(info.value)
        assert "widest" in msg and "2.6" in msg
        assert "segments()" in msg and "interp_to_uniform_grid" in msg

    def test_max_gap_wider_than_every_hole_is_accepted(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            out = _crash_session().lowpass_at(2.0, max_gap=3.0)
        assert out.is_filtered

    def test_refusal_comes_before_the_filter_runs(self):
        ts = _crash_session()
        before = np.asarray(ts.data, float).copy()
        with pytest.raises(InvalidParameterError):
            ts.lowpass_at(2.0, max_gap=0.5, inplace=True)
        assert np.array_equal(np.asarray(ts.data, float), before)
        assert not ts.is_filtered

    @pytest.mark.parametrize("bad", [0, -1.0, "1", np.nan, np.inf, True])
    def test_refuses_non_positive_max_gap(self, bad):
        with pytest.raises(InvalidParameterError, match="max_gap"):
            _uniform().lowpass_at(2.0, max_gap=bad)

    def test_frame_broadcast_forwards_max_gap(self):
        ts = _crash_session()
        frame = baseDf.from_series([ts, ts.copy()], labels=["a", "b"])
        with pytest.raises(InvalidParameterError, match=r"gap\(s\) wider than"):
            frame.lowpass_at(2.0, max_gap=0.5)

    def test_segment_then_filter_is_the_remedy(self):
        for seg in _crash_session().segments():
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                seg.lowpass_at(2.0, max_gap=0.5)


class TestReporting:
    def test_get_statistics_counts_gaps(self):
        stats = _crash_session().get_statistics()
        assert stats["n_gaps"] == 10
        assert np.isclose(stats["gapped_duration"], 26.0, atol=20 * DT)
        assert np.isclose(stats["median_dt"], DT)

    def test_get_statistics_on_a_clean_series(self):
        stats = _uniform().get_statistics()
        assert stats["n_gaps"] == 0 and stats["gapped_duration"] == 0.0

    def test_info_prints_the_gap_count(self, capsys):
        _crash_session().info()
        out = capsys.readouterr().out
        assert "Gaps" in out and "10" in out
        assert "Gapped Duration" in out


class TestWarningIdentity:
    @pytest.mark.parametrize("name, run", FILTERS, ids=IDS)
    def test_warning_points_at_the_caller_for_every_entry_point(self, name, run):
        with pytest.warns(UserWarning) as rec:
            run(_crash_session())
        assert rec[0].filename == __file__

    def test_frame_broadcast_warns_once_and_points_at_the_caller(self):
        """Every column shares one index, so the gap warning is the same for
        all of them; 64 channels must not mean 64 lines (external panel)."""
        ts = _crash_session()
        import pandas as pd
        wide = pd.DataFrame({"time": np.asarray(ts.times, float),
                             **{c: np.asarray(ts.data, float) for c in ("Cz", "Pz", "Oz")}})
        frame = baseDf.from_df(wide, time_col="time")
        with pytest.warns(UserWarning, match=r"3 gap\(s\)|10 gap\(s\)") as rec:
            frame.lowpass_at(2.0)
        gap_warnings = [w for w in rec if "gap(s)" in str(w.message)]
        assert len(gap_warnings) == 1
        assert gap_warnings[0].filename == __file__

    def test_frame_broadcast_honours_warnings_as_errors(self):
        ts = _crash_session()
        frame = baseDf.from_series([ts, ts.copy()], labels=["a", "b"])
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            with pytest.raises(UserWarning, match=r"gap\(s\)"):
                frame.lowpass_at(2.0)

    def test_frame_refusal_names_the_column(self):
        ts = _crash_session()
        import pandas as pd
        wide = pd.DataFrame({"time": np.asarray(ts.times, float),
                             "Cz": np.asarray(ts.data, float)})
        frame = baseDf.from_df(wide, time_col="time")
        with pytest.raises(InvalidParameterError, match="'Cz'"):
            frame.lowpass_at(2.0, max_gap=0.5)

    def test_warning_says_how_to_silence_it(self):
        with pytest.warns(UserWarning, match="max_gap=") as rec:
            _crash_session().lowpass_at(2.0)
        assert "jitter" in str(rec[0].message)



class TestDocstrings:
    @pytest.mark.parametrize("name", IDS)
    def test_every_filter_documents_the_index_rules(self, name):
        doc = getattr(baseTs, name).__doc__
        assert "InvalidParameterError" in doc and "duplicate" in doc and "max_gap" in doc

    @pytest.mark.parametrize("name", ["gaps", "segments"])
    def test_gap_methods_document_the_index_rules(self, name):
        doc = getattr(baseTs, name).__doc__
        assert "non-finite" in doc and "non-decreasing" in doc and "duplicate" in doc
