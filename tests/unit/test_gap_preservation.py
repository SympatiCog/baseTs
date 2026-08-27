"""Tests for issue #36: filter_outliers must not invent data in pre-existing gaps.

The filter blanks outliers it detects and interpolates them back - that is its
job. NaNs that were already in the input are a different population: an
acquisition dropout is not an outlier, and filling it silently returns
synthetic samples with nothing left to mark them.
"""
import logging

import numpy as np
import pytest

from baseTs import baseTs
from baseTs.LowessOutlierFilter import FilterConfig


@pytest.fixture(autouse=True)
def _quiet():
    logging.disable(logging.INFO)
    yield
    logging.disable(logging.NOTSET)


def _gappy(gap=slice(250, 350), spike_at=150, n=600):
    """A clean signal with one acquisition gap and one genuine outlier."""
    t = np.arange(n) / 10.0
    d = np.sin(t / 3.0) + 0.05 * np.random.RandomState(0).randn(n)
    if spike_at is not None:
        d[spike_at] += 6.0
    if gap is not None:
        d[gap] = np.nan
    ts = baseTs(d, t)
    ts.set_outlier_filter(frac=0.2)
    return ts


def _nan_mask(ts):
    return np.isnan(np.asarray(ts.data, float))


class TestInputGapsArePreserved:
    """Gaps present before filtering must still be gaps after."""

    @pytest.mark.parametrize("gap", [
        slice(300, 302),      # 2 samples
        slice(250, 350),      # 100 samples
        slice(100, 500),      # 400 of 600
    ])
    def test_gap_survives_filtering(self, gap):
        ts = _gappy(gap=gap)
        before = _nan_mask(ts)
        ts.filter_outliers(inplace=True)
        after = _nan_mask(ts)

        assert after[gap].all(), "the input gap was filled with synthetic data"
        assert before.sum() == after.sum()

    def test_leading_gap_is_not_forward_filled(self):
        """ffill/bfill filled edge gaps with a constant, which is worse than
        interpolation - a flat run reads as real low-variance signal."""
        ts = _gappy(gap=slice(0, 200), spike_at=400)
        ts.filter_outliers(inplace=True)
        assert _nan_mask(ts)[:200].all()

    def test_trailing_gap_is_not_back_filled(self):
        ts = _gappy(gap=slice(400, 600), spike_at=150)
        ts.filter_outliers(inplace=True)
        assert _nan_mask(ts)[400:].all()

    def test_lowess_fit_is_nan_across_the_gap(self):
        """The QC plot draws lowess_fit; it must not span a region with no data."""
        ts = _gappy()
        ts.filter_outliers(inplace=True)
        assert np.isnan(ts.lowess_fit[250:350]).all()


class TestOutliersAreStillInterpolated:
    """The filter's own blanked samples must still be filled - that is the point."""

    def test_spike_is_removed_and_filled(self):
        ts = _gappy(gap=None, spike_at=150)
        raw = float(np.asarray(ts.data, float)[150])
        ts.filter_outliers(inplace=True)
        cleaned = float(np.asarray(ts.data, float)[150])

        assert not np.isnan(cleaned), "a detected outlier must be interpolated, not left NaN"
        assert abs(cleaned) < abs(raw), "the spike should have been pulled toward the fit"

    def test_no_new_nans_on_a_gapless_series(self):
        ts = _gappy(gap=None, spike_at=150)
        ts.filter_outliers(inplace=True)
        assert not _nan_mask(ts).any()

    def test_outlier_adjacent_to_a_gap_is_still_filled(self):
        ts = _gappy(gap=slice(250, 350), spike_at=349 + 1)
        ts.filter_outliers(inplace=True)
        mask = _nan_mask(ts)
        assert mask[250:350].all()
        assert not mask[350]


class TestOptOut:
    """The old fill-everything behaviour stays reachable for anyone relying on it."""

    def test_fill_input_gaps_restores_old_behaviour(self):
        ts = _gappy()
        ts.set_outlier_filter(fill_input_gaps=True)
        ts.filter_outliers(inplace=True)
        assert not _nan_mask(ts).any()

    def test_default_is_the_safe_one(self):
        assert FilterConfig().fill_input_gaps is False


class TestItSaysWhatItDid:
    """Silent is the failure mode; the history entry should carry the count."""

    def test_history_records_gap_samples_left_unfilled(self):
        ts = _gappy()
        ts.filter_outliers(inplace=True)
        entry = ts.history[-1]
        assert '100' in entry, f"gap sample count missing from history: {entry!r}"


class TestNoInterpolationAcrossAGap:
    """An input gap is a boundary, not something to interpolate through.

    Filling the whole array and restoring gaps afterwards looks equivalent
    but is not: pandas bridges a combined outlier+gap NaN run, so an outlier
    beside a 10 s dropout was estimated from the first valid sample on the
    far side. The earlier test here asserted only "not NaN", never that the
    replacement was a sensible number.
    """

    @staticmethod
    def _outlier_beside_gap(n=600):
        t = np.arange(n) / 10.0
        clean = np.sin(t / 3.0)
        d = clean.copy()
        d[249] += 6.0            # outlier immediately before the gap
        d[250:350] = np.nan      # 10-second dropout
        ts = baseTs(d, t)
        ts.set_outlier_filter(frac=0.2)
        return ts, clean

    def test_replacement_is_close_to_local_truth(self):
        ts, clean = self._outlier_beside_gap()
        ts.filter_outliers(inplace=True)
        arr = np.asarray(ts.data, float)

        assert not np.isnan(arr[249]), "the outlier must still be filled"
        # The far side of the gap sits near -0.78 while the truth here is
        # near +0.90; anything dragged across the gap lands well outside this.
        assert abs(arr[249] - clean[249]) < 0.15, (
            f"replacement {arr[249]:.4f} is far from local truth "
            f"{clean[249]:.4f} - interpolated across the gap?"
        )

    def test_replacement_stays_on_its_own_side(self):
        """It must not be pulled toward the first valid sample after the gap."""
        ts, clean = self._outlier_beside_gap()
        ts.filter_outliers(inplace=True)
        arr = np.asarray(ts.data, float)

        far_side = arr[350]
        assert abs(arr[249] - arr[248]) < abs(arr[249] - far_side), (
            "replacement is closer to the far side of the gap than to its "
            "own neighbour"
        )

    def test_each_segment_is_filled_from_its_own_data(self):
        """Two gaps, three segments; an outlier in each must stay local."""
        t = np.arange(900) / 10.0
        clean = np.sin(t / 3.0)
        d = clean.copy()
        for spike in (100, 400, 800):
            d[spike] += 6.0
        d[250:350] = np.nan
        d[600:700] = np.nan
        ts = baseTs(d, t)
        ts.set_outlier_filter(frac=0.2)
        ts.filter_outliers(inplace=True)
        arr = np.asarray(ts.data, float)

        assert np.isnan(arr[250:350]).all()
        assert np.isnan(arr[600:700]).all()
        for spike in (100, 400, 800):
            assert abs(arr[spike] - clean[spike]) < 0.15, f"index {spike}"


class TestMaskedArrayGapsAreSeen:
    """np.asarray drops a mask and exposes the payload underneath."""

    def test_masked_positions_are_treated_as_gaps(self):
        from baseTs.LowessOutlierFilter import LowessOutlierFilter, FilterConfig

        t = np.arange(600) / 10.0
        payload = np.sin(t / 3.0)
        # Garbage under the mask: if the mask is ignored, np.asarray exposes
        # these and they contaminate the fit rather than being absent.
        payload[250:350] = 500.0
        mask = np.zeros(600, dtype=bool)
        mask[250:350] = True
        data = np.ma.array(payload, mask=mask)

        f = LowessOutlierFilter(FilterConfig(frac=0.2))
        cleaned, idx, line = f.filter(data, t, return_lowess=True)

        assert np.isnan(np.asarray(cleaned, float)[250:350]).all()
        assert not any(250 <= i < 350 for i in idx), (
            "a masked sample was flagged as an outlier"
        )
        # The fit either side must be unaffected by the masked payload.
        clean = np.sin(t / 3.0)
        arr = np.asarray(cleaned, float)
        assert np.allclose(arr[:250], clean[:250], atol=0.15)
        assert np.allclose(arr[350:], clean[350:], atol=0.15)


class TestBoolCoercion:
    """bool('False') is True - every non-empty string is truthy."""

    @pytest.mark.parametrize("given,expected", [
        ('true', True), ('True', True), ('1', True), ('yes', True),
        ('false', False), ('False', False), ('0', False), ('no', False),
        (True, True), (False, False), (1, True), (0, False),
    ])
    def test_recognised_values(self, given, expected):
        ts = _gappy()
        ts.set_outlier_filter(fill_input_gaps=given)
        assert ts.get_outlier_filter_params()['fill_input_gaps'] is expected

    def test_string_false_does_not_enable_gap_filling(self):
        """The end-to-end consequence: the caller's gaps must survive."""
        ts = _gappy()
        ts.set_outlier_filter(fill_input_gaps='False')
        ts.filter_outliers(inplace=True)
        assert _nan_mask(ts)[250:350].all()

    def test_unrecognised_string_raises(self):
        ts = _gappy()
        with pytest.raises(ValueError, match="fill_input_gaps"):
            ts.set_outlier_filter(fill_input_gaps='maybe')


class TestFilterCarriesNoPerCallState:
    """copy() shares outlier_filter by reference, deliberately."""

    def test_gap_count_is_not_stashed_on_the_shared_filter(self):
        a = _gappy()
        b = a.copy()
        assert a.outlier_filter is b.outlier_filter, "precondition: filter is shared"

        a.filter_outliers(inplace=True)
        b_gapless = baseTs(np.sin(np.arange(600) / 10.0), np.arange(600) / 10.0)
        b_gapless.outlier_filter = a.outlier_filter
        b_gapless.filter_outliers(inplace=True)

        # Each history must describe its own run. Matching on the specific
        # phrase, not the substring 'gap' - the config dict printed in the
        # same entry contains 'fill_input_gaps', so a loose match always hits.
        assert 'left 100 pre-existing gap sample(s) as NaN' in a.history[-1]
        assert 'pre-existing gap sample(s)' not in b_gapless.history[-1]
