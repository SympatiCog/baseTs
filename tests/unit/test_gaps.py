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
        with pytest.raises(ValidationError, match="max_gap"):
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
