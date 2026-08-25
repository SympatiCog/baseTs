"""
Regression tests for pandas 2.x/3.x compatibility.

Each test here corresponds to an API that pandas removed after 1.x, or to a
guard that was lost. They are grouped separately from the feature tests because
they exist to catch environment drift, not behaviour changes.
"""
import warnings

import numpy as np
import pytest

from baseTs import baseTs


@pytest.fixture
def spiky_ts():
    """5000 normal samples with one unmistakable spike at index 100."""
    np.random.seed(0)
    data = np.random.randn(5000)
    data[100] = 12.0
    return baseTs(data, np.arange(5000) / 100.0, freq=100.0)


class TestInterpolateMissing:
    """pandas 3.0 removed fillna(method=...)."""

    def test_leading_and_trailing_nan(self):
        """
        Series.interpolate() does not fill leading/trailing NaN, so this path
        always reached the removed fillna(method=) call.
        """
        data = np.arange(20, dtype=float)
        data[0] = np.nan
        data[-1] = np.nan
        ts = baseTs(data, np.arange(20) / 10.0, freq=10.0)

        result = ts.interpolate_missing()

        assert not np.any(np.isnan(result.data))
        assert result.data[0] == 1.0    # back-filled
        assert result.data[-1] == 18.0  # forward-filled

    def test_interior_nan(self):
        data = np.arange(20, dtype=float)
        data[5] = np.nan
        ts = baseTs(data, np.arange(20) / 10.0, freq=10.0)
        assert not np.any(np.isnan(ts.interpolate_missing().data))


class TestDetectOutliers:
    """pandas 2.0 removed Series.mad()."""

    @pytest.mark.parametrize("method", ["zscore", "iqr", "modified_zscore"])
    def test_all_methods_return_bool_mask(self, spiky_ts, method):
        mask = spiky_ts.detect_outliers(method=method)

        assert isinstance(mask, np.ndarray)
        assert mask.dtype == bool
        assert len(mask) == len(spiky_ts)
        assert mask[100], f"{method} missed the 12-sigma spike"

    def test_modified_zscore_survives_nan(self, spiky_ts):
        """
        The denominator must skip NaN. Mixing pandas median() (which skips NaN)
        with a NaN-propagating np.median silently returns an all-False mask.
        """
        data = spiky_ts.data.copy()
        data[7] = np.nan
        ts = baseTs(data, spiky_ts.times, freq=spiky_ts.freq)

        mask = ts.detect_outliers(method='modified_zscore')

        assert mask[100], "NaN in the input suppressed all detections"
        assert not mask[7], "the NaN position itself should not be flagged"

    def test_modified_zscore_zero_mad_still_detects(self):
        """
        MAD is 0 when over half the values are identical, but an outlier can
        still be present. The Iglewicz-Hoaglin mean-absolute-deviation fallback
        handles this; both raising and returning all-False would be wrong.
        """
        data = np.ones(100)
        data[50] = 100.0
        ts = baseTs(data, np.arange(100) / 10.0, freq=10.0)

        mask = ts.detect_outliers(method='modified_zscore')

        assert mask[50]
        assert mask.sum() == 1

    def test_modified_zscore_constant_series_warns(self):
        """A genuinely constant series has no outliers; warn rather than raise."""
        ts = baseTs(np.ones(100), np.arange(100) / 10.0, freq=10.0)

        with pytest.warns(RuntimeWarning, match="constant"):
            mask = ts.detect_outliers(method='modified_zscore')

        assert not mask.any()

    def test_unknown_method_still_raises(self, spiky_ts):
        with pytest.raises(ValueError, match="Unknown outlier detection method"):
            spiky_ts.detect_outliers(method='nonsense')


class TestEmptySliceGuards:
    """baseTs.duration() shadowed the guarded TimeSeriesData.duration()."""

    @pytest.fixture
    def empty_slice(self):
        t = np.arange(1000) / 100.0
        ts = baseTs(np.sin(2 * np.pi * t), t, freq=100.0)
        return ts.time_slice(start_time=10.0, end_time=50.0)

    def test_slice_is_actually_empty(self, empty_slice):
        assert len(empty_slice) == 0

    def test_duration_of_empty_series(self, empty_slice):
        assert empty_slice.duration() == 0.0

    def test_get_statistics_of_empty_series(self, empty_slice):
        """get_statistics() calls duration(), so it inherited the crash."""
        stats = empty_slice.get_statistics()
        assert stats['duration'] == 0.0

    def test_duration_still_correct_when_populated(self):
        t = np.arange(1000) / 100.0
        ts = baseTs(np.sin(t), t, freq=100.0)
        assert np.isclose(ts.duration(), t[-1] - t[0])


class TestNaNSentinel:
    """`freq is np.nan` only matched the one np.nan object."""

    def test_float_nan_freq_is_treated_as_unset(self):
        """
        Previously this silently produced an all-NaN time index instead of
        raising, because float('nan') is not np.nan.
        """
        with pytest.raises(ValueError, match="times array or a frequency"):
            baseTs(np.arange(10, dtype=float), freq=float('nan'))

    def test_none_freq_is_treated_as_unset(self):
        with pytest.raises(ValueError, match="times array or a frequency"):
            baseTs(np.arange(10, dtype=float), freq=None)

    def test_real_freq_still_builds_times(self):
        ts = baseTs(np.arange(10, dtype=float), freq=10.0)
        assert len(ts.times) == 10
        assert not np.any(np.isnan(ts.times))

    def test_times_without_freq_still_works(self):
        """
        Deriving freq from the times array must still work. NB: the derived
        value is currently inflated by n/(n-1) - see the effective-frequency
        note in the PR description. That is a separate defect; this test only
        pins that the path works and yields a finite positive rate.
        """
        ts = baseTs(np.arange(10, dtype=float), np.arange(10) / 10.0)
        assert np.isfinite(ts.freq) and ts.freq > 0
