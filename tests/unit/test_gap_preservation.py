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
