"""`is_interpolated` means one thing, and every producer follows it (#90).

The flag's docstring says "whether the data has been interpolated". On
main, the three regridders (`interpto_hz`, `interpto_samples`,
`interp_to_uniform_grid`) and `set_indices_to_nan_and_interpolate` set
it, while the two gap fillers (`interpolate_missing`, `interpolate_gaps`)
and `filter_outliers` - which replace measured samples with interpolated
ones too - never did, so the history and the flag disagreed about the
same operation.

The rule, decided here (the issue's second reading, the one the name and
docstring already state): **the flag is True once at least one value in
the series is an interpolated estimate rather than a measured sample.**
So a producer sets it exactly when it wrote at least one such value - a
regridder always (every value is re-estimated), a gap filler when it
filled a gap, the outlier filter when it replaced an outlier or filled
an input gap, and `set_indices_to_nan_and_interpolate` always (it refuses
an empty index list). A call that changed nothing leaves the flag as it found it,
and nothing resets it: a series derived from interpolated values is still
built on estimates, which is why `_metadata` carries it.
"""

import numpy as np
import pytest

from baseTs import baseTs

N = 200
FS = 10.0


def _clean():
    t = np.arange(N) / FS
    return baseTs(np.sin(2 * np.pi * 0.3 * t) + 2.0, t, freq=FS)


def _gappy():
    ts = _clean()
    values = ts.values.copy()
    values[[20, 21, 100]] = np.nan
    return baseTs(values, ts.times, freq=FS)


def _spiky():
    ts = _clean()
    values = ts.values.copy()
    values[[50, 120]] += 40.0
    return baseTs(values, ts.times, freq=FS)


# --- gap fillers: set when a gap was filled, untouched when there was none ---

GAP_FILLERS = [
    ("interpolate_missing", lambda ts, inplace: ts.interpolate_missing(inplace=inplace)),
    ("interpolate_gaps", lambda ts, inplace: ts.interpolate_gaps(inplace=inplace)),
    ("interpolate_gaps-spline", lambda ts, inplace: ts.interpolate_gaps(
        method="spline", order=2, inplace=inplace)),
]
GAP_IDS = [g[0] for g in GAP_FILLERS]


class TestGapFillersSetTheFlagWhenTheyFillAGap:

    @pytest.mark.parametrize("inplace", [False, True], ids=["copy", "inplace"])
    @pytest.mark.parametrize("name, run", GAP_FILLERS, ids=GAP_IDS)
    def test_filling_a_gap_sets_it(self, name, run, inplace):
        ts = _gappy()
        assert ts.is_interpolated is False

        out = run(ts, inplace)

        assert out.is_interpolated is True
        assert (out is ts) == inplace

    @pytest.mark.parametrize("inplace", [False, True], ids=["copy", "inplace"])
    @pytest.mark.parametrize("name, run", GAP_FILLERS, ids=GAP_IDS)
    def test_a_series_with_no_gap_is_left_as_found(self, name, run, inplace):
        """Nothing was estimated, so the call says nothing about the flag."""
        out = run(_clean(), inplace)
        assert out.is_interpolated is False

    def test_a_gap_the_call_did_not_fill_does_not_count(self):
        """interpolate_gaps(limit=1) on a two-sample gap fills one sample
        of it, and that one is an estimate; a call that fills nothing at
        all - a leading gap under the default forward fill - is not."""
        filled_one = _gappy().interpolate_gaps(limit=1)
        assert filled_one.is_interpolated is True
        assert np.isnan(filled_one.values).any()

        ts = _clean()
        values = ts.values.copy()
        values[0] = np.nan
        leading = baseTs(values, ts.times, freq=FS)
        out = leading.interpolate_gaps()
        assert np.isnan(out.values[0])
        assert out.is_interpolated is False


# --- the outlier filter: it replaces samples by interpolation ----------------

class TestTheOutlierFilterSetsTheFlagWhenItReplacesASample:

    @pytest.mark.parametrize("inplace", [False, True], ids=["copy", "inplace"])
    def test_replacing_an_outlier_sets_it(self, inplace):
        ts = _spiky().set_outlier_filter(z_threshold=3.0)

        out = ts.filter_outliers(inplace=inplace)

        assert len(out.outlier_indices) > 0
        assert out.is_interpolated is True

    def test_filling_an_input_gap_sets_it_even_with_no_outlier(self):
        ts = _gappy().set_outlier_filter(z_threshold=3.0, fill_input_gaps=True)

        out = ts.filter_outliers()

        assert len(out.outlier_indices) == 0
        assert out.is_interpolated is True

    def test_leaving_input_gaps_and_finding_no_outlier_leaves_it_as_found(self):
        """#36: input gaps stay NaN by default, so nothing was estimated."""
        ts = _gappy().set_outlier_filter(z_threshold=3.0)

        out = ts.filter_outliers()

        assert len(out.outlier_indices) == 0
        assert np.isnan(out.values).any()
        assert out.is_interpolated is False

    def test_clean_data_leaves_it_as_found(self):
        out = _clean().set_outlier_filter(z_threshold=3.0).filter_outliers()
        assert len(out.outlier_indices) == 0
        assert out.is_interpolated is False


# --- the producers that already set it, pinned under the same rule -----------

class TestTheRegriddersAlwaysSetIt:

    @pytest.mark.parametrize("run", [
        lambda ts: ts.interpto_hz(20.0),
        lambda ts: ts.interpto_samples(150),
        lambda ts: ts.interp_to_uniform_grid(inplace=False),
    ], ids=["interpto_hz", "interpto_samples", "interp_to_uniform_grid"])
    def test_every_value_is_re_estimated(self, run):
        assert run(_clean()).is_interpolated is True


class TestSetIndicesToNanAndInterpolate:

    def test_given_an_index_it_sets_it(self):
        assert _clean().set_indices_to_nan_and_interpolate([10, 11]).is_interpolated is True

    def test_given_no_index_it_is_refused(self):
        """So a call that returns has always estimated something, and the
        unconditional True it sets is the rule's, not a carve-out."""
        with pytest.raises(ValueError, match="Indices must be integers"):
            _clean().set_indices_to_nan_and_interpolate([])


# --- the flag is never reset, and it travels -----------------------------------

class TestTheFlagIsSticky:

    def test_a_derivation_of_an_interpolated_series_is_still_interpolated(self):
        out = _gappy().interpolate_gaps().lowpass_at(cutoff=1.0)
        assert out.is_interpolated is True

    def test_a_second_gap_fill_with_nothing_to_fill_keeps_it(self):
        out = _gappy().interpolate_gaps().interpolate_gaps()
        assert out.is_interpolated is True
