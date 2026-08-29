"""
Unit tests for baseTs core functionality.
"""
import pytest
import numpy as np
import pandas as pd
from baseTs import baseTs
from baseTs.core import from_df
from baseTs.series import TimeSeriesData


class TestBaseTsInitialization:
    """Tests for baseTs initialization and basic properties."""
    
    def test_init_with_data_and_times(self, sample_data):
        """Test initializing baseTs with data and times."""
        ts = baseTs(
            data=sample_data['data'],
            times=sample_data['times'],
            signal_name="TestSignal"
        )
        
        assert ts.data is not None
        assert ts.times is not None
        assert len(ts.data) == len(sample_data['data'])
        assert len(ts.times) == len(sample_data['times'])
        assert ts.signal_name == "TESTSIGNAL"  # Uppercase in the class implementation
        
    def test_init_with_data_and_freq(self):
        """Test initializing baseTs with data and frequency."""
        data = np.sin(np.linspace(0, 10, 1000))
        freq = 100  # 100 Hz
        
        ts = baseTs(data=data, freq=freq)
        
        assert ts.data is not None
        assert ts.times is not None
        assert len(ts.data) == 1000
        assert len(ts.times) == 1000
        assert ts.freq == freq
        
    def test_init_validation(self):
        """Test initialization validation requirements."""
        data = np.sin(np.linspace(0, 10, 1000))
        
        # Should raise an error if neither times nor freq is provided
        with pytest.raises(ValueError):
            baseTs(data=data)
            
    def test_len_and_duration(self, simple_baseTsObj):
        """Test length and duration calculations."""
        assert simple_baseTsObj.len() == 1000
        assert simple_baseTsObj.duration() == 10.0
        
    def test_from_df(self, sample_dataframe):
        """Test creating baseTs from DataFrame."""
        ts = from_df(sample_dataframe)
        
        assert ts.data is not None
        assert ts.times is not None
        assert len(ts.data) == len(sample_dataframe)
        assert ts.signal_name == "VALUE"  # Default to column name, uppercase


class TestBaseTsTransformations:
    """Tests for baseTs data transformations."""
    
    def test_interpolation_to_samples(self, simple_baseTsObj):
        """Test interpolation to specified number of samples."""
        new_len = 500
        ts_interp = simple_baseTsObj.interpto_samples(new_len)
        
        assert len(ts_interp.data) == new_len
        assert len(ts_interp.times) == new_len
        assert ts_interp.is_interpolated is True
        
        # Check that original object is unchanged
        assert len(simple_baseTsObj.data) == 1000
        
        # Test inplace version
        ts_inplace = simple_baseTsObj.interpto_samples(new_len, inplace=True)
        assert len(simple_baseTsObj.data) == new_len
        assert ts_inplace is simple_baseTsObj  # Should return self
        
    def test_interpolation_to_frequency(self, simple_baseTsObj):
        """Test interpolation to specified frequency."""
        original_len = len(simple_baseTsObj.data)
        new_freq = 200  # 200 Hz
        ts_interp = simple_baseTsObj.interpto_hz(new_freq)
        
        # Duration is 10 seconds at exactly 200 Hz: 2000 intervals, 2001 samples.
        # Was 2000 before the grid fix, when the points were spread across the
        # span and the real rate was 199.9 Hz.
        assert len(ts_interp.data) == 2001
        assert ts_interp.freq == new_freq
        assert ts_interp.is_interpolated is True
        
        # Check that original object is unchanged
        assert len(simple_baseTsObj.data) == original_len
        
    def test_normalization(self, simple_baseTsObj):
        """Test data normalization functions."""
        # Z-scale
        ts_z = simple_baseTsObj.zscale()
        assert np.isclose(ts_z.data.mean(), 0, atol=1e-10)
        assert np.isclose(ts_z.data.std(), 1, atol=1e-10)
        
        # Normalize to 0-1 range
        ts_norm = simple_baseTsObj.normalize_range()
        assert np.isclose(ts_norm.data.min(), 0, atol=1e-10)
        assert np.isclose(ts_norm.data.max(), 1, atol=1e-10)
        
    def test_detrend(self):
        """Test detrending functionality."""
        # Create signal with trend
        t = np.linspace(0, 10, 1000)
        trend = 0.5 * t + 2.0  # Linear trend: slope=0.5, offset=2.0
        signal = np.sin(2 * np.pi * 0.5 * t) + trend
        ts = baseTs(data=signal, times=t, freq=100.0)
        
        # Test linear detrending
        ts_linear = ts.detrend(method='linear')
        # After linear detrend, mean should be approximately zero
        assert np.abs(ts_linear.data.mean()) < 1e-10
        # Original signal should be unchanged
        assert not np.allclose(ts.data, ts_linear.data)
        
        # Test constant detrending (demean)
        ts_constant = ts.detrend(method='constant')
        # After constant detrend, mean should be exactly zero
        assert np.abs(ts_constant.data.mean()) < 1e-15
        # Should preserve the linear trend but remove the mean
        assert ts_constant.data.max() - ts_constant.data.min() > ts_linear.data.max() - ts_linear.data.min()
        
        # Test inplace operation
        ts_copy = ts.copy()
        original_data = ts_copy.data.copy()
        ts_inplace = ts_copy.detrend(method='linear', inplace=True)
        assert ts_inplace is ts_copy  # Should return self
        assert not np.allclose(original_data, ts_copy.data)  # Data should be modified
        
        # Test invalid method
        with pytest.raises(ValueError, match="Unsupported detrend method"):
            ts.detrend(method='invalid')
        
    def test_trimming(self, simple_baseTsObj):
        """Test trimming functionality."""
        start_val = 2.0  # Start at t=2s
        end_val = 8.0    # End at t=8s
        
        ts_trimmed = simple_baseTsObj.trimto_timepoints(start_val, end_val)
        
        # Check that the trimming worked
        assert ts_trimmed.times[0] >= start_val
        assert ts_trimmed.times[-1] <= end_val
        
        # Original should be unchanged
        assert simple_baseTsObj.times[0] < start_val
        assert simple_baseTsObj.times[-1] > end_val


class TestBaseTsFiltering:
    """Tests for baseTs filtering functionality."""
    
    def test_lowpass_filter(self, noisy_baseTsObj):
        """Test lowpass filter."""
        cutoff = 1.0  # 1 Hz cutoff
        ts_filtered = noisy_baseTsObj.lowpass_at(cutoff)
        
        assert ts_filtered.is_filtered is True
        assert ts_filtered is not noisy_baseTsObj  # Not modified in place
        
        # Basic verification - filter should reduce high frequency components
        # Calculate power in high frequencies before and after filtering
        f1, p1 = noisy_baseTsObj.compute_fft_power()
        f2, p2 = ts_filtered.compute_fft_power()
        
        # Find indices for frequencies > cutoff
        high_freq_indices = np.where(f1 > cutoff)[0]
        
        # Check that power in high frequencies is reduced
        high_freq_power_before = np.sum(p1[high_freq_indices])
        high_freq_power_after = np.sum(p2[high_freq_indices])
        assert high_freq_power_after < high_freq_power_before
        
    def test_highpass_filter(self, noisy_baseTsObj):
        """Test highpass filter."""
        cutoff = 1.0  # 1 Hz cutoff
        ts_filtered = noisy_baseTsObj.highpass_at(cutoff)
        
        assert ts_filtered.is_filtered is True
        
        # Basic verification - filter should reduce low frequency components
        f1, p1 = noisy_baseTsObj.compute_fft_power()
        f2, p2 = ts_filtered.compute_fft_power()
        
        # Find indices for frequencies < cutoff
        low_freq_indices = np.where(f1 < cutoff)[0]
        if len(low_freq_indices) > 0:  # Skip DC component
            low_freq_indices = low_freq_indices[1:]
            
        # Check that power in low frequencies is reduced
        if len(low_freq_indices) > 0:
            low_freq_power_before = np.sum(p1[low_freq_indices])
            low_freq_power_after = np.sum(p2[low_freq_indices])
            assert low_freq_power_after < low_freq_power_before
        
    def test_bandpass_filter(self, noisy_baseTsObj):
        """Test bandpass filter."""
        hp_hz = 0.3  # High-pass cutoff
        lp_hz = 0.8  # Low-pass cutoff
        
        ts_filtered = noisy_baseTsObj.bandpass_at(hp_hz=hp_hz, lp_hz=lp_hz)
        
        assert ts_filtered.is_filtered is True
        
        # Test with reset_mean=False
        ts_filtered_no_mean = noisy_baseTsObj.bandpass_at(
            hp_hz=hp_hz, lp_hz=lp_hz, reset_mean=False
        )
        
        # Mean should be closer to zero when reset_mean is False
        assert abs(ts_filtered_no_mean.data.mean()) < abs(noisy_baseTsObj.data.mean())
        
    def test_sg_filter(self, noisy_baseTsObj):
        """Test Savitzky-Golay filter."""
        window_length = 11
        polyorder = 2
        
        ts_filtered = noisy_baseTsObj.sg_filter(window_length, polyorder)
        
        assert ts_filtered.is_filtered is True
        
        # SG filter should smooth the data, so the standard deviation should be smaller
        assert ts_filtered.data.std() < noisy_baseTsObj.data.std()


class TestOutlierDetection:
    """Tests for outlier detection functionality."""
    
    def test_set_outlier_filter(self, outlier_baseTsObj):
        """Test setting outlier filter parameters."""
        # Test with individual parameters
        outlier_baseTsObj.set_outlier_filter(
            z_threshold=3.0,
            frac=0.1,
            max_iterations=5
        )
        
        params = outlier_baseTsObj.get_outlier_filter_params()
        assert params['z_threshold'] == 3.0
        assert params['frac'] == 0.1
        assert params['max_iterations'] == 5
        
        # Test with params dictionary
        params_dict = {
            'z_threshold': 4.0,
            'frac': 0.2,
            'use_median': False
        }
        
        outlier_baseTsObj.set_outlier_filter(params=params_dict)
        
        new_params = outlier_baseTsObj.get_outlier_filter_params()
        assert new_params['z_threshold'] == 4.0
        assert new_params['frac'] == 0.2
        assert new_params['use_median'] is False
        assert new_params['max_iterations'] == 5  # Unchanged from before
        
    def test_filter_outliers(self, outlier_baseTsObj, data_with_outliers):
        """Test outlier filtering."""
        # Configure the filter
        outlier_baseTsObj.set_outlier_filter(
            z_threshold=3.0,
            frac=0.07
        )
        
        # Apply the filter
        filtered_ts = outlier_baseTsObj.filter_outliers()
        
        assert filtered_ts.is_outlier_filtered is True
        assert filtered_ts.lowess_fit is not None
        
        # Check that the standard deviation is reduced after filtering
        assert filtered_ts.data.std() < outlier_baseTsObj.data.std()
        
        # Test the inplace version
        original_std = outlier_baseTsObj.data.std()
        outlier_baseTsObj.filter_outliers(inplace=True)
        assert outlier_baseTsObj.data.std() < original_std

class TestRelativeBandPower:
    """Tests for the relative_band_power / falff methods."""

    @staticmethod
    def _lf_ts(fs=2.0, duration=600.0, seed=42, offset=0.0):
        """Slow 0.05 Hz signal long enough to resolve the 0.01-0.1 Hz band."""
        np.random.seed(seed)
        n = int(duration * fs)
        t = np.arange(n) / fs
        sig = np.sin(2 * np.pi * 0.05 * t) + 0.5 * np.random.randn(n)
        return baseTs(sig + offset, t, freq=fs)

    def test_relative_band_power_method(self):
        """Method delegates correctly and returns a builtin float."""
        ts = self._lf_ts()
        ratio = ts.relative_band_power(0.01, 0.1)

        assert isinstance(ratio, float)
        assert not isinstance(ratio, np.floating)
        assert 0.6 < ratio < 0.8

    def test_dc_offset_does_not_change_result(self):
        """
        The headline robustness property: an undetrended mean offset must not
        move the number, because DC is excluded from both sums.
        """
        baseline = self._lf_ts().relative_band_power(0.01, 0.1)
        offset = self._lf_ts(offset=100.0).relative_band_power(0.01, 0.1)
        assert np.isclose(baseline, offset)

    def test_detrend_pipeline(self):
        """The documented pipeline produces the same answer."""
        ts = self._lf_ts(offset=5.0)
        assert np.isclose(
            ts.detrend('linear').relative_band_power(0.01, 0.1),
            ts.relative_band_power(0.01, 0.1),
            rtol=1e-3,
        )

    def test_falff_method(self):
        """falff() defaults to the amplitude convention."""
        ts = self._lf_ts()
        assert np.isclose(
            ts.falff(),
            ts.relative_band_power(0.01, 0.1, ratio='amplitude'),
        )
        # Amplitude reads lower than power for a peaked in-band spectrum
        assert ts.falff() < ts.relative_band_power(0.01, 0.1)

    def test_details_breakdown(self):
        """details=True carries the white-noise null alongside the ratio."""
        res = self._lf_ts().relative_band_power(0.01, 0.1, details=True)

        assert res.ratio_type == 'power'
        assert np.isclose(res.band_sum / res.total_sum, res.ratio)
        assert 0 < res.bin_fraction < res.ratio  # real structure beats the null

    def test_window_passthrough(self):
        """The window argument reaches get_frequency_content."""
        ts = self._lf_ts()
        windowed = ts.relative_band_power(0.01, 0.1, window='hann')
        assert 0.0 < windowed < 1.0

    def test_method_validation(self):
        """Invalid bands raise from the method as well as the function."""
        ts = self._lf_ts()
        with pytest.raises(ValueError):
            ts.relative_band_power(0.5, 0.1)
        with pytest.raises(ValueError):
            ts.relative_band_power(0.01, 99.0)

    def test_no_side_effects(self):
        """It is a pure measurement: no history entry, no data mutation."""
        ts = self._lf_ts()
        data_before = ts.data.copy()
        history_before = len(ts.history)
        last_process_before = ts.last_process

        ts.relative_band_power(0.01, 0.1)
        ts.falff()

        assert np.array_equal(ts.data, data_before)
        assert len(ts.history) == history_before
        assert ts.last_process == last_process_before


class TestLowessDetrend:
    """Tests for lowess_detrend, centred on its inplace=False purity contract."""

    @staticmethod
    def _ts(spiked):
        d, t = spiked
        return baseTs(data=d.copy(), times=t.copy(), signal_name="SpikedSignal")

    def test_fixture_actually_triggers_the_filter(self, spiked):
        """
        Guard for the purity tests below.

        They assert that self.data survives lowess_detrend untouched. If the
        filter never finds an outlier there is nothing to interpolate away, so
        self.data would be unchanged even on the buggy implementation and the
        assertion would pass vacuously. Fail loudly here instead.
        """
        ts = self._ts(spiked)
        ts.set_outlier_filter(frac=0.25)
        ts.filter_outliers(inplace=True)

        assert len(ts.outlier_indices) > 0

    def test_inplace_false_leaves_self_untouched(self, spiked):
        """Issue #6: the caller's object must survive a non-inplace detrend."""
        ts = self._ts(spiked)
        before = {
            'data': np.asarray(ts.data, dtype=float).copy(),
            'lowess_fit': ts.lowess_fit,
            'outlier_indices': ts.outlier_indices,
            'is_outlier_filtered': ts.is_outlier_filtered,
            'history': list(ts.history),
            'last_process': ts.last_process,
        }

        out = ts.lowess_detrend(frac=0.25, inplace=False)

        assert out is not ts
        assert np.array_equal(np.asarray(ts.data, dtype=float), before['data'])
        assert ts.lowess_fit is before['lowess_fit']
        assert ts.outlier_indices is before['outlier_indices']
        assert ts.is_outlier_filtered == before['is_outlier_filtered']
        assert ts.history == before['history']
        assert ts.last_process == before['last_process']

    def test_inplace_false_does_not_reconfigure_filter(self, spiked):
        """
        Issue #6: detrending must not rewrite the caller's filter config.

        set_outlier_filter resets *every* parameter to its signature default,
        so a detrend at a different frac silently moves z_threshold too. Note
        that baseTs.copy() shares the outlier_filter by reference, so fixing
        this by detrending "on a copy" does not help.
        """
        ts = self._ts(spiked)
        ts.set_outlier_filter(frac=0.11, z_threshold=4.2)
        before = dict(ts.get_outlier_filter_params())

        ts.lowess_detrend(frac=0.25, inplace=False)

        assert ts.get_outlier_filter_params() == before

    def test_inplace_true_detrends_in_place(self, spiked):
        """The inplace path removes the trend and reports the fit it used."""
        d, t = spiked
        ramped = baseTs(data=d + 0.5 * t, times=t.copy())
        slope_before = np.polyfit(t, np.asarray(ramped.data, dtype=float), 1)[0]

        out = ramped.lowess_detrend(frac=0.25, inplace=True)

        assert out is ramped
        slope_after = np.polyfit(t, np.asarray(ramped.data, dtype=float), 1)[0]
        assert abs(slope_after) < 0.05 * abs(slope_before)
        assert ramped.lowess_fit is not None
        assert ramped.last_process == "_lowess_detrend"

    def test_outliers_survive_detrending(self, spiked):
        """
        Detrending subtracts a robust trend from the *original* data.

        The spikes are what the trend is made robust against, not something
        the operation removes: they must still be the extremes afterwards.
        """
        out = self._ts(spiked).lowess_detrend(frac=0.25, inplace=False)
        detrended = np.asarray(out.data, dtype=float)

        assert detrended.argmax() == 150
        assert detrended.argmin() == 350

    def test_qc_plot_still_draws_the_fit(self, spiked):
        """
        Regression guard for the is_outlier_filtered decoupling.

        lowess_detrend produces a lowess_fit without setting
        is_outlier_filtered. qc_plot used to gate the fit trace on that flag,
        so dropping it silently removed the trace from the plot.
        """
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from baseTs.plotting import qc_plot

        ts = self._ts(spiked)
        ts.lowess_detrend(frac=0.25, inplace=True)
        assert ts.is_outlier_filtered is False   # the flag is deliberately not set
        assert ts.lowess_fit is not None

        plt.close("all")
        ax = qc_plot(ts, np.asarray(ts.data, dtype=float), ts.times)
        assert "Lowess Fit" in [line.get_label() for line in ax.get_lines()]
        plt.close("all")

    @pytest.mark.parametrize("bad_frac", [0.0, -0.1, 1.5])
    def test_frac_validation(self, spiked, bad_frac):
        """
        frac is a LOWESS bandwidth in (0, 1] and is rejected up front.

        statsmodels already rejects <0 and >1 from inside the fit, but frac=0
        slips through and yields a degenerate fit. Match on our own message so
        the contract belongs to baseTs rather than to the backend's internals.
        """
        with pytest.raises(ValueError, match=r"must be in \(0, 1\]"):
            self._ts(spiked).lowess_detrend(frac=bad_frac)


class TestHistoryNoneGuard:
    """A `history` of None must not crash the next operation (issue #22).

    __finalize__ propagates metadata from whichever operand carries it, so a
    None history can reach a derived object from any operand lacking one. Both
    _update_history_and_process implementations must tolerate it.
    """

    def test_basets_update_history_tolerates_none(self):
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        ts.history = None

        derived = ts.copy()
        derived._update_history_and_process('did a thing', '_thing')

        assert derived.history == ['did a thing']
        assert derived.last_process == '_thing'

    def test_timeseriesdata_update_history_tolerates_none(self):
        """The superclass guard is hasattr-only, so None slips past it too."""
        from baseTs.series import TimeSeriesData

        tsd = TimeSeriesData(np.arange(10.0), index=np.arange(10) / 10.0)
        tsd.history = None

        tsd._update_history_and_process('did a thing', '_thing')

        assert tsd.history == ['did a thing']
        assert tsd.last_process == '_thing'

    def test_existing_history_is_appended_not_replaced(self):
        """The guard must not discard a history that is genuinely present."""
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        before = list(ts.history)

        ts._update_history_and_process('did a thing', '_thing')

        assert ts.history == before + ['did a thing']


class TestFiltersRejectNanFreq:
    """A degenerate time base must not filter to silent all-NaN output.

    validate_filter_params guarded with `sampling_freq <= 0`, which is False
    for NaN, so butter()/filtfilt() returned an all-NaN array with only a
    RuntimeWarning. Same defect class as issue #24, different module.
    """

    @staticmethod
    def _degenerate():
        ts = baseTs(np.sin(np.arange(200) / 10.0), np.zeros(200))
        assert np.isnan(ts.freq)
        return ts

    def test_lowpass_filter_raises(self):
        from baseTs.filters import InvalidParameterError

        with pytest.raises(InvalidParameterError, match="Invalid sampling frequency"):
            self._degenerate().lowpass_filter(0.1)

    def test_highpass_filter_raises(self):
        from baseTs.filters import InvalidParameterError

        with pytest.raises(InvalidParameterError, match="Invalid sampling frequency"):
            self._degenerate().highpass_filter(0.1)

    def test_notch_filter_raises(self):
        from baseTs.filters import InvalidParameterError

        with pytest.raises(InvalidParameterError, match="Invalid sampling frequency"):
            self._degenerate().notch_filter(0.1)

    def test_bandpass_filter_raises(self):
        from baseTs.filters import InvalidParameterError

        with pytest.raises(InvalidParameterError, match="Invalid sampling frequency"):
            self._degenerate().bandpass_filter(0.1, 0.4)

    def test_butterpass_at_raises(self):
        """butterpass_at was absent from this family because it never ran (#27).

        It reached filters.bandpass_filter with keywords that do not exist, so
        it died on a TypeError long before any rate was validated. Delegating
        to bandpass_at is what puts it behind validate_filter_params.
        """
        from baseTs.filters import InvalidParameterError

        with pytest.raises(InvalidParameterError, match="Invalid sampling frequency"):
            self._degenerate().butterpass_at(0.1, 0.4)

    def test_healthy_series_still_filters(self):
        """The guard must not disturb an ordinary series."""
        ts = baseTs(np.sin(np.arange(500) / 10.0), np.arange(500) / 10.0)
        out = ts.lowpass_filter(0.5)
        assert not np.any(np.isnan(np.asarray(out.data, float)))


class TestHistoryNoneSurvivesRealOperations:
    """The None-history guard must hold on the paths users actually take.

    Guarding _update_history_and_process alone was not enough: every
    non-inplace method routes through _create_new_with_data, and eight sites
    appended to history directly rather than through the helper.
    """

    @staticmethod
    def _none_history():
        ts = baseTs(np.sin(np.arange(200) / 10.0), np.arange(200) / 10.0)
        ts.history = None
        return ts

    def test_create_new_with_data_path(self):
        """zscale() dies in _create_new_with_data's history.copy()."""
        out = self._none_history().zscale()
        assert isinstance(out.history, list)

    def test_interp_to_uniform_grid(self):
        ts = self._none_history()
        out = ts.interp_to_uniform_grid(np.arange(0, 19, 0.2), inplace=False)
        assert isinstance(out.history, list)
        assert any("uniform grid" in e for e in out.history)

    def test_set_outlier_filter(self):
        ts = self._none_history()
        ts.set_outlier_filter(frac=0.2)
        assert isinstance(ts.history, list)

    def test_set_timestamp_offset(self):
        ts = self._none_history()
        ts.set_timestamp_offset(1.5)
        assert isinstance(ts.history, list)
        assert any("timestamp offset" in e for e in ts.history)

    def test_summary_printer_tolerates_none(self, capsys):
        """info() iterates history; None raised TypeError."""
        ts = self._none_history()
        ts.info()
        assert "History:" in capsys.readouterr().out

    def test_finalize_normalises_none_history(self):
        """__finalize__ turns a propagated None into a list."""
        ts = self._none_history()
        assert isinstance(ts.iloc[:50].history, list)


class TestHistoryInvariantHoldsEverywhere:
    """"history is always a list" must hold on every derivation path.

    An earlier revision normalised only None, and only in __finalize__, which
    left copy(deep=True) and every non-list type still broken.
    """

    @staticmethod
    def _with_history(value):
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        ts.history = value
        return ts

    @pytest.mark.parametrize("bad", [None, 'note', ('a', 'b'), np.array(['a', 'b'])])
    def test_copy_deep_normalises(self, bad):
        """copy(deep=True) is the default path; deepcopy(None) is None."""
        assert isinstance(self._with_history(bad).copy().history, list)

    @pytest.mark.parametrize("bad", [None, 'note', ('a', 'b')])
    def test_copy_shallow_normalises(self, bad):
        assert isinstance(self._with_history(bad).copy(deep=False).history, list)

    @pytest.mark.parametrize("bad", [None, 'note', ('a', 'b')])
    def test_finalize_normalises(self, bad):
        assert isinstance(self._with_history(bad).iloc[:5].history, list)

    def test_string_history_is_wrapped_not_exploded(self):
        """list('note') would give four single-character entries."""
        assert self._with_history('note').iloc[:5].history == ['note']

    def test_string_history_survives_a_real_operation(self):
        """zscale() routes through _create_new_with_data's list(...) call."""
        out = self._with_history('note').zscale()
        assert out.history[0] == 'note'
        assert not any(len(e) == 1 for e in out.history)

    @pytest.mark.parametrize("bad", ['oops', ('a',), {'k': 'v'}, None])
    def test_append_with_no_intervening_pandas_op(self, bad):
        """No .iloc first - that would normalise before the helper runs.

        The earlier version of this test sliced first, so it passed with
        _update_history_and_process's own guard deleted. In-place methods
        never get that free normalisation.
        """
        ts = self._with_history(bad)
        ts._update_history_and_process('did a thing', '_thing')
        assert ts.history[-1] == 'did a thing'

    @pytest.mark.parametrize("bad", ['note', ('a', 'b'), {'k': 'v'}, np.array(['a', 'b'])])
    def test_inplace_methods_tolerate_non_list_history(self, bad):
        """_detach_shared_metadata never runs on the object you mutate.

        set_timestamp_offset, set_outlier_filter and inplace=True filters all
        append directly to the history of an object that was never derived,
        so they were still raising issue #22's AttributeError.
        """
        ts = baseTs(np.sin(np.arange(200) / 10.0), np.arange(200) / 10.0)
        ts.history = bad
        ts.set_timestamp_offset(1.5)
        assert isinstance(ts.history, list)
        assert ts.history[-1].startswith('Set timestamp offset')

    def test_dict_history_keeps_its_values(self):
        """list({'a': 'x'}) is ['a'] - the values vanish.

        A bare list() fallback turned a loud AttributeError into silent data
        loss, which is the failure normalise_history's docstring cites as the
        reason not to iterate a str.
        """
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        ts.history = {'created': 'note1', 'filtered': 'note2'}
        assert ts.dropna().history == [{'created': 'note1', 'filtered': 'note2'}]

    def test_constructor_history_kwarg_is_normalised(self):
        """The first place a history enters the system."""
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0, history='note')
        assert ts.history == ['note']
        assert baseTs(np.arange(5.0), np.arange(5) / 5.0, history=5).history == [5]


class TestNanFreqIsNotLaundered:
    """A NaN rate must not become a fabricated healthy number.

    Reaches a NaN rate through a degenerate time base rather than by
    assigning one. Assignment is no longer a route: the freq setter validates,
    so a NaN can only enter by being derived. A zero-duration index is the
    only remaining way in, which makes it the honest subject for this test.
    """

    @staticmethod
    def _nan_freq():
        return baseTs(np.sin(np.arange(200) / 10.0), np.zeros(200))

    def test_derivation_paths_agree(self):
        ts = self._nan_freq()
        assert np.isnan(ts.zscale().freq)
        assert np.isnan(ts.iloc[:100].freq)

    def test_guard_still_fires_after_derivation(self):
        with pytest.raises(ValueError, match="Invalid sampling frequency"):
            self._nan_freq().zscale().get_frequency_content()

    def test_explicit_freq_still_honoured(self):
        """A real declared rate must survive an index-preserving transform."""
        ts = baseTs(np.sin(np.arange(200) / 10.0), np.arange(200) / 10.0, freq=999.0)
        assert ts.zscale().freq == 999.0


class TestInfoToleratesOddHistory:
    """info() must render fully whatever history holds.

    `self.history or []` adds a truthiness test that raises on an ndarray
    after the header is already printed, leaving a half-rendered report.
    """

    @pytest.mark.parametrize("value", [None, np.array(['a', 'b']), np.array([]), [], ['x']])
    def test_basets_info(self, value, capsys):
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        ts.history = value
        ts.info()
        assert "History:" in capsys.readouterr().out

    @pytest.mark.parametrize("value", [None, np.array(['a', 'b']), np.array([]), [], ['x']])
    def test_timeseriesdata_info(self, value, capsys):
        from baseTs.series import TimeSeriesData

        tsd = TimeSeriesData(np.arange(10.0), index=np.arange(10) / 10.0)
        tsd.history = value
        tsd.info()
        assert capsys.readouterr().out  # rendered without raising


class TestButterpassAt:
    """butterpass_at must actually run, and must mean what its name says (#27).

    It called filters.bandpass_filter with `highpass_freq`/`lowpass_freq`/
    `sampling_freq`, none of which that function accepts, so every call raised
    TypeError. Nothing in the suite or the docs referenced it, so the method
    was dead from introduction. It is now an alias for bandpass_at, so it runs
    the object plumbing the sibling filters already have tests for. It also
    reaches the #24 rate guard, though that is not what the delegation buys -
    the keyword rename the issue suggested would have reached it too, by
    calling the same filters.bandpass_filter.
    """

    FS = 30.0
    LOW_HZ = 0.2
    HIGH_HZ = 5.0
    HP, LP = 1.0, 10.0  # a band that keeps HIGH_HZ and rejects LOW_HZ

    @classmethod
    def _two_tone(cls):
        t = np.arange(int(cls.FS * 50)) / cls.FS
        data = (np.sin(2 * np.pi * cls.LOW_HZ * t)
                + np.sin(2 * np.pi * cls.HIGH_HZ * t))
        return baseTs(data, t, signal_name="TwoTone")

    @staticmethod
    def _amplitude_at(ts, hz):
        """Amplitude of one tone by projection, so no FFT bin has to line up."""
        t = np.asarray(ts.times, float)
        values = np.asarray(ts.data, float)
        return abs(2.0 / len(t) * np.sum(values * np.exp(-2j * np.pi * hz * t)))

    def test_butterpass_at_runs(self):
        """The issue's reproduction: this raised TypeError on every call."""
        ts = baseTs(np.sin(np.arange(500) / 10.0), np.arange(500) / 10.0)

        out = ts.butterpass_at(0.05, 0.4)

        assert isinstance(out, baseTs)
        assert len(out) == len(ts)

    def test_hp_and_lp_are_not_transposed(self):
        """The band kept must be [hp_freq, lp_freq], not its mirror image.

        A positional signature this easy to swap needs the orientation pinned
        against the signal rather than against the call. Note a transposition
        fails here by raising rather than by tripping these assertions:
        scipy.signal.butter rejects a descending Wn pair, so the call dies
        before the amplitudes are measured. The measurements are still what
        pin the caller-facing meaning, and they would catch a swap that some
        future implementation sorted into range instead of rejecting.
        """
        ts = self._two_tone()
        before_low = self._amplitude_at(ts, self.LOW_HZ)
        before_high = self._amplitude_at(ts, self.HIGH_HZ)

        out = ts.butterpass_at(self.HP, self.LP)

        assert self._amplitude_at(out, self.HIGH_HZ) > 0.9 * before_high
        assert self._amplitude_at(out, self.LOW_HZ) < 0.1 * before_low

    def test_agrees_with_bandpass_at_sample_for_sample(self):
        """An alias that computes something else is not an alias."""
        ts = self._two_tone()

        alias = ts.butterpass_at(self.HP, self.LP)
        direct = ts.bandpass_at(hp_hz=self.HP, lp_hz=self.LP)

        np.testing.assert_array_equal(
            np.asarray(alias.data, float), np.asarray(direct.data, float)
        )

    @classmethod
    def _seeded(cls):
        """A source carrying a non-default value in every seedable metadata slot.

        The first version of the metadata test below ran on a freshly built
        series, so every field it compared was either a default or derived from
        the index. An implementation that dropped `ts_offset`, `_lowess_fit`,
        `is_interpolated` and the rest would have passed it unchanged - the
        inputs did not span the axis the test was named for.

        Census of TimeSeriesData._metadata, measured rather than asserted:
        ten fields are seeded off their constructor default and survive this
        call intact, and the other three (`is_filtered`, `last_process`,
        `history`) change because changing them is the operation's own effect.
        An earlier revision of this docstring claimed eleven and two. It was
        wrong on both counts, and wrong for an instructive reason: the probe
        behind it truncated each value to 26 characters, which hid the entry
        `history` gains. `_freq_declaration` was the field it miscounted -
        nothing here declared a rate, so that slot sat at None on both sides
        and compared equal no matter what the implementation did with it.
        """
        ts = cls._two_tone()
        ts.set_outlier_filter(frac=0.25)
        ts.set_timestamp_offset(1.5)
        ts.is_interpolated = True
        ts.is_uniform_grid = True
        ts.is_outlier_filtered = True
        ts.lowess_fit = np.arange(len(ts), dtype=float)
        ts.outlier_indices = np.array([3, 7, 11])
        # Declared last, on purpose: set_timestamp_offset shifts the index and
        # would expire a declaration made before it (#38), leaving a stale
        # token that says nothing about propagation. Declared here the token
        # is live, and filtering preserves the index, so it must still be live
        # on the far side. The value deliberately disagrees with the 30 Hz the
        # index derives, as at test_explicit_freq_still_honoured - a rate that
        # matched would be indistinguishable from re-derivation.
        ts.freq = 999.0
        return ts

    @staticmethod
    def _comparable(ts, field):
        """Render one metadata value so two objects' copies compare equal.

        No default on the getattr: _initialize_default_metadata sets all
        thirteen fields unconditionally, so absence is a real failure and must
        raise. A sentinel would compare equal to itself and quietly pass a
        field that had gone missing from both objects.

        Tuples are normalised element-wise rather than by assuming a shape.
        Two different ones live in _metadata - the (array, Index) stamps from
        #20 and the (rate, token) declaration from #38 - and an earlier
        revision handled only the first, so seeding a rate made this raise.
        """
        def norm(value):
            if isinstance(value, np.ndarray):
                return value.tolist()
            if isinstance(value, pd.Index):
                return value.tolist()
            if isinstance(value, tuple):
                return tuple(norm(v) for v in value)
            if type(value).__name__ == 'LowessOutlierFilter':
                return value.config  # frozen since #15, so == is meaningful
            return value

        return norm(getattr(ts, field))

    #: The census quoted in _seeded's docstring, in
    #: test_metadata_matches_bandpass_at's, and in the CHANGELOG entry for #27.
    #: Named here so those three prose copies are pinned by a test rather than
    #: maintained by hand - the previous revision asserted only that no field
    #: was vacuous, which let a field move between these two groups without
    #: anything noticing that the documented counts had gone stale.
    PRESERVED_BY_OP = frozenset({
        '_freq_declaration', 'signal_name', 'is_interpolated', 'is_uniform_grid',
        'ts_offset', 'has_timestamp_offset', '_outlier_indices', '_lowess_fit',
        'is_outlier_filtered', 'outlier_filter',
    })
    CHANGED_BY_OP = frozenset({'is_filtered', 'last_process', 'history'})

    def _census(self):
        """Partition _metadata by what the call does to each field."""
        source = self._seeded()
        result = self._seeded().butterpass_at(self.HP, self.LP)
        preserved, changed = set(), set()
        for field in TimeSeriesData._metadata:
            same = (self._comparable(result, field)
                    == self._comparable(source, field))
            (preserved if same else changed).add(field)
        return source, preserved, changed

    def test_metadata_census_is_exactly_what_the_docs_claim(self):
        """The 10-preserved / 3-changed split is asserted, not just described.

        Three places quote this census in prose - _seeded's docstring,
        test_metadata_matches_bandpass_at's, and the CHANGELOG entry. Prose
        drifts. If a future change made the call reset `is_interpolated`, say,
        that field would move from one group to the other, every existing
        assertion here would still pass, and all three descriptions would
        quietly become wrong.

        Splitting the sets by name rather than by count also means a field
        added to TimeSeriesData._metadata fails here until someone decides
        which group it belongs in.
        """
        _, preserved, changed = self._census()

        assert self.PRESERVED_BY_OP | self.CHANGED_BY_OP == set(
            TimeSeriesData._metadata
        ), "a field was added to or removed from _metadata; classify it here"
        assert preserved == self.PRESERVED_BY_OP
        assert changed == self.CHANGED_BY_OP
        assert (len(preserved), len(changed)) == (10, 3)  # the quoted numbers

    def test_seeding_leaves_no_metadata_field_vacuous(self):
        """No field may sit at its default and stay there across the call.

        This is the guard the two preceding review rounds each found missing,
        by hand, one field at a time. A field that starts at its constructor
        default and is not touched by the operation compares equal to itself
        in test_metadata_matches_bandpass_at no matter what the implementation
        does with it - which is how `_freq_declaration` sat there unnoticed
        through a rewrite that existed to close exactly that gap, and through
        the docstring census written to prove it closed.

        Asserting the census instead of describing it moves the check
        somewhere it cannot be bypassed: a field added to
        TimeSeriesData._metadata later fails here until someone either seeds
        it in _seeded or establishes that this operation changes it. Prose
        drifts from the code; this cannot.

        A field earns its place by being discriminating in one of two ways -
        it carries a seeded value the call must preserve, or the call changes
        it. `is_filtered` is the second kind, and deliberately left at its
        default of False on the source: seeding it True would make it
        indistinguishable from the True the operation sets.
        """
        t = np.arange(int(self.FS * 50)) / self.FS
        default = baseTs(np.sin(2 * np.pi * self.HIGH_HZ * t), t)
        source = self._seeded()
        result = self._seeded().butterpass_at(self.HP, self.LP)

        vacuous = []
        for field in TimeSeriesData._metadata:
            at_default = (self._comparable(source, field)
                          == self._comparable(default, field))
            unchanged = (self._comparable(result, field)
                         == self._comparable(source, field))
            if at_default and unchanged:
                vacuous.append(field)

        assert not vacuous, (
            f"{vacuous} sit at the constructor default and are not touched by "
            f"the call, so test_metadata_matches_bandpass_at compares them "
            f"equal for the wrong reason. Seed them in _seeded()."
        )

    @pytest.mark.parametrize("inplace", [False, True])
    def test_metadata_matches_bandpass_at(self, inplace):
        """Every metadata slot must come out where bandpass_at puts it.

        Asserted against the sibling rather than against fixed values, so a
        pre-existing propagation gap cannot fail this - it is an alias test,
        not an audit of _create_new_with_data.

        What this does NOT pin, stated plainly: it cannot tell delegation apart
        from a correct hand-rolled reimplementation. Measured, not assumed - a
        mutant restoring the old `self.copy()` / `newTs.data = ...` body with
        the keywords merely renamed produces identical metadata on all thirteen
        fields, both inplace modes. The two implementations are observably
        equivalent; delegation is preferred for having one code path rather
        than two, which is a maintainability claim and not a behavioral one.
        What this test does catch is an implementation that drops metadata -
        building a fresh baseTs from the filtered array, say.
        """
        alias = self._seeded().butterpass_at(self.HP, self.LP, inplace=inplace)
        direct = self._seeded().bandpass_at(
            hp_hz=self.HP, lp_hz=self.LP, inplace=inplace
        )

        for field in TimeSeriesData._metadata:
            assert self._comparable(alias, field) == self._comparable(direct, field), (
                f"metadata field {field!r} diverges from bandpass_at"
            )
        np.testing.assert_array_equal(alias.times, direct.times)
        assert alias.freq == direct.freq

    def test_records_the_bandpass_history_entry(self):
        """Delegation is deliberate: the entry reads bandpass, not butterworth.

        No caller can have seen the old `_btrp_` token - the method raised
        before reaching it - and the sibling bandpass_filter alias already
        records itself this way.
        """
        ts = self._two_tone()

        out = ts.butterpass_at(self.HP, self.LP)

        assert out.last_process == f"_bp_{self.LP}:{self.HP}Hz"
        assert out.history[-1] == f"Bandpass filtered at {self.LP} Hz and {self.HP} Hz"

    def test_inplace_mutates_and_returns_self(self):
        ts = self._two_tone()
        before_low = self._amplitude_at(ts, self.LOW_HZ)

        out = ts.butterpass_at(self.HP, self.LP, inplace=True)

        assert out is ts
        assert ts.is_filtered is True
        assert self._amplitude_at(ts, self.LOW_HZ) < 0.1 * before_low

    def test_not_inplace_leaves_the_original_alone(self):
        ts = self._two_tone()
        before = np.asarray(ts.data, float).copy()

        ts.butterpass_at(self.HP, self.LP)

        np.testing.assert_array_equal(np.asarray(ts.data, float), before)
        assert ts.is_filtered is False
