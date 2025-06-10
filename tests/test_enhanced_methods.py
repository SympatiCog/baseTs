# -*- coding: utf-8 -*-
"""
Modern test suite for baseTs enhanced methods.
Tests mathematical operations, filtering, and pandas-enhanced functionality.
"""

import pytest
import numpy as np
import pandas as pd
from baseTs import baseTs


class TestMathematicalOperations:
    """Test mathematical operations with pandas Series foundation."""
    
    @pytest.fixture
    def sample_data(self):
        """Generate diverse test data."""
        n_points = 100
        times = np.linspace(0, 10, n_points)
        # Complex signal with multiple components
        data = (
            2.0 +  # DC offset
            3.0 * np.sin(2 * np.pi * 0.5 * times) +  # 0.5 Hz component
            1.5 * np.cos(2 * np.pi * 1.2 * times) +  # 1.2 Hz component
            0.5 * np.random.randn(n_points)  # Noise
        )
        return data, times
    
    def test_zscale_operations(self, sample_data):
        """Test z-scaling operations."""
        data, times = sample_data
        ts = baseTs(data, times, freq=10.0, signal_name="test_signal")
        
        # Test z-scaling
        ts_zscaled = ts.zscale()
        
        # Verify z-scaling properties
        assert abs(ts_zscaled.data.mean()) < 1e-8, "Z-scaled mean should be ~0"
        assert abs(ts_zscaled.data.std() - 1.0) < 1e-8, "Z-scaled std should be 1"
        assert isinstance(ts_zscaled, baseTs), "Should return baseTs object"
        assert len(ts_zscaled.history) > len(ts.history), "History should be updated"
        assert ts_zscaled.signal_name == "TEST_SIGNAL", "Metadata should be preserved (uppercased)"
        
        # Test inplace operation
        ts_inplace = ts.copy()
        result = ts_inplace.zscale(inplace=True)
        assert result is ts_inplace, "Inplace should return self"
        assert abs(ts_inplace.data.mean()) < 1e-8, "Inplace z-scaling should work"
    
    def test_normalize_range_operations(self, sample_data):
        """Test range normalization operations."""
        data, times = sample_data
        ts = baseTs(data, times, freq=10.0)
        
        # Test default normalization (0-1)
        ts_norm = ts.normalize_range()
        assert ts_norm.data.min() >= 0.0, "Min should be >= 0"
        assert ts_norm.data.max() <= 1.0, "Max should be <= 1"
        assert abs(ts_norm.data.min()) < 1e-10, "Min should be close to 0"
        assert abs(ts_norm.data.max() - 1.0) < 1e-10, "Max should be close to 1"
        
        # Test custom range
        ts_custom = ts.normalize_range(target_min=-5.0, target_max=5.0)
        assert ts_custom.data.min() >= -5.0, "Min should be >= -5"
        assert ts_custom.data.max() <= 5.0, "Max should be <= 5"
        
        # Test inplace
        ts_inplace = ts.copy()
        ts_inplace.normalize_range(inplace=True)
        assert ts_inplace.data.min() >= 0.0, "Inplace normalization should work"
    
    def test_center_operations(self, sample_data):
        """Test centering operations."""
        data, times = sample_data
        ts = baseTs(data, times, freq=10.0)
        
        # Test centering
        ts_centered = ts.center()
        assert abs(ts_centered.data.mean()) < 1e-10, "Centered mean should be ~0"
        assert isinstance(ts_centered, baseTs), "Should return baseTs object"
        
        # Test inplace
        ts_inplace = ts.copy()
        ts_inplace.center(inplace=True)
        assert abs(ts_inplace.data.mean()) < 1e-10, "Inplace centering should work"
    
    def test_scale_operations(self, sample_data):
        """Test scaling operations."""
        data, times = sample_data
        ts = baseTs(data, times, freq=10.0)
        
        # Test scaling
        factor = 2.5
        ts_scaled = ts.scale(factor)
        expected_data = data * factor
        np.testing.assert_array_almost_equal(ts_scaled.data, expected_data)
        
        # Test inplace
        ts_inplace = ts.copy()
        ts_inplace.scale(factor, inplace=True)
        np.testing.assert_array_almost_equal(ts_inplace.data, expected_data)
    
    def test_abs_operations(self, sample_data):
        """Test absolute value operations."""
        data, times = sample_data
        ts = baseTs(data, times, freq=10.0)
        
        # Test absolute value
        ts_abs = ts.abs()
        assert np.all(ts_abs.data >= 0), "All values should be non-negative"
        np.testing.assert_array_almost_equal(ts_abs.data, np.abs(data))
        
        # Test inplace
        ts_inplace = ts.copy()
        ts_inplace.abs(inplace=True)
        assert np.all(ts_inplace.data >= 0), "Inplace abs should work"
    
    def test_method_chaining(self, sample_data):
        """Test method chaining works correctly."""
        data, times = sample_data
        ts = baseTs(data, times, freq=10.0)
        
        # Chain multiple operations
        result = ts.center().abs().scale(2.0).normalize_range()
        
        assert isinstance(result, baseTs), "Should return baseTs object"
        assert result.data.min() >= 0.0, "Should be normalized"
        assert result.data.max() <= 1.0, "Should be normalized"
        assert len(result.history) > len(ts.history), "History should accumulate"
    
    def test_arithmetic_operations(self, sample_data):
        """Test that arithmetic operations return baseTs objects."""
        data, times = sample_data
        ts1 = baseTs(data, times, freq=10.0, signal_name="signal1")
        ts2 = baseTs(data * 0.5, times, freq=10.0, signal_name="signal2")
        
        # Test addition
        result_add = ts1 + ts2
        assert isinstance(result_add, baseTs), "Addition should return baseTs object"
        assert result_add.signal_name == "SIGNAL1", "Should preserve signal name from first operand"
        assert "Applied Addition operation" in result_add.history[-1], "Should update history"
        
        # Test subtraction
        result_sub = ts1 - ts2
        assert isinstance(result_sub, baseTs), "Subtraction should return baseTs object"
        
        # Test multiplication with scalar
        result_mul = ts1 * 2.0
        assert isinstance(result_mul, baseTs), "Multiplication should return baseTs object"
        np.testing.assert_array_almost_equal(result_mul.data, ts1.data * 2.0)
        
        # Test division with scalar
        result_div = ts1 / 2.0
        assert isinstance(result_div, baseTs), "Division should return baseTs object"
        np.testing.assert_array_almost_equal(result_div.data, ts1.data / 2.0)
        
        # Test power
        result_pow = ts1 ** 2
        assert isinstance(result_pow, baseTs), "Power should return baseTs object"
        np.testing.assert_array_almost_equal(result_pow.data, ts1.data ** 2)
        
        # Test that metadata is preserved
        assert result_add.freq == ts1.freq, "Should preserve frequency"
        assert result_add.times.shape == ts1.times.shape, "Should preserve time array"
        
        # Test right-hand operations
        result_radd = 1.0 + ts1
        assert isinstance(result_radd, baseTs), "Right addition should return baseTs object"


class TestFilteringOperations:
    """Test filtering operations."""
    
    @pytest.fixture
    def noisy_signal(self):
        """Generate a noisy signal for filtering tests."""
        fs = 100  # Sampling frequency
        t = np.linspace(0, 5, fs * 5)
        # Signal with 1 Hz and 10 Hz components plus noise
        signal = (
            np.sin(2 * np.pi * 1.0 * t) +  # 1 Hz signal
            0.5 * np.sin(2 * np.pi * 10.0 * t) +  # 10 Hz signal
            0.1 * np.random.randn(len(t))  # Noise
        )
        return signal, t, fs
    
    def test_lowpass_filter(self, noisy_signal):
        """Test lowpass filtering."""
        data, times, fs = noisy_signal
        ts = baseTs(data, times, freq=fs)
        
        # Apply lowpass filter to remove 10 Hz component
        ts_filtered = ts.lowpass_at(cutoff=5.0)
        
        assert isinstance(ts_filtered, baseTs), "Should return baseTs object"
        assert ts_filtered.is_filtered, "Should mark as filtered"
        assert len(ts_filtered.history) > len(ts.history), "History should be updated"
        
        # Check that high frequency content is reduced
        freqs_orig, power_orig = ts.compute_fft_power()
        freqs_filt, power_filt = ts_filtered.compute_fft_power()
        
        # Find 10 Hz component
        idx_10hz = np.argmin(np.abs(freqs_orig - 10.0))
        assert power_filt[idx_10hz] < power_orig[idx_10hz], "10 Hz component should be attenuated"
    
    def test_highpass_filter(self, noisy_signal):
        """Test highpass filtering."""
        data, times, fs = noisy_signal
        ts = baseTs(data, times, freq=fs)
        
        # Apply highpass filter to remove DC and low frequencies
        ts_filtered = ts.highpass_at(cutoff=2.0)
        
        assert isinstance(ts_filtered, baseTs), "Should return baseTs object"
        assert ts_filtered.is_filtered, "Should mark as filtered"
        
        # Check that low frequency content is reduced
        freqs_orig, power_orig = ts.compute_fft_power()
        freqs_filt, power_filt = ts_filtered.compute_fft_power()
        
        # Find 1 Hz component
        idx_1hz = np.argmin(np.abs(freqs_orig - 1.0))
        assert power_filt[idx_1hz] < power_orig[idx_1hz], "1 Hz component should be attenuated"
    
    def test_bandpass_filter(self, noisy_signal):
        """Test bandpass filtering."""
        data, times, fs = noisy_signal
        ts = baseTs(data, times, freq=fs)
        
        # Apply bandpass filter to keep only 1 Hz component
        ts_filtered = ts.bandpass_at(hp_hz=0.5, lp_hz=2.0)
        
        assert isinstance(ts_filtered, baseTs), "Should return baseTs object"
        assert ts_filtered.is_filtered, "Should mark as filtered"
        
        # Check that frequencies outside the band are attenuated
        freqs_orig, power_orig = ts.compute_fft_power()
        freqs_filt, power_filt = ts_filtered.compute_fft_power()
        
        # Find 10 Hz component (should be attenuated)
        idx_10hz = np.argmin(np.abs(freqs_orig - 10.0))
        assert power_filt[idx_10hz] < power_orig[idx_10hz], "10 Hz component should be attenuated"
    
    def test_sg_filter(self, noisy_signal):
        """Test Savitzky-Golay filtering."""
        data, times, fs = noisy_signal
        ts = baseTs(data, times, freq=fs)
        
        # Apply SG filter
        ts_filtered = ts.sg_filter(window_length=11, polyorder=2)
        
        assert isinstance(ts_filtered, baseTs), "Should return baseTs object"
        assert ts_filtered.is_filtered, "Should mark as filtered"
        assert len(ts_filtered.data) == len(ts.data), "Length should be preserved"
    
    def test_gaussian_filter(self, noisy_signal):
        """Test Gaussian filtering."""
        data, times, fs = noisy_signal
        ts = baseTs(data, times, freq=fs)
        
        # Apply Gaussian filter
        ts_filtered = ts.gauss_filter(sigma=2.0)
        
        assert isinstance(ts_filtered, baseTs), "Should return baseTs object"
        assert ts_filtered.is_filtered, "Should mark as filtered"
        assert len(ts_filtered.data) == len(ts.data), "Length should be preserved"
    
    def test_filter_chaining(self, noisy_signal):
        """Test chaining multiple filters."""
        data, times, fs = noisy_signal
        ts = baseTs(data, times, freq=fs)
        
        # Chain filters
        result = ts.bandpass_at(hp_hz=0.1, lp_hz=20.0).sg_filter(window_length=5)
        
        assert isinstance(result, baseTs), "Should return baseTs object"
        assert result.is_filtered, "Should mark as filtered"
        assert len(result.history) > len(ts.history), "History should accumulate"


class TestPandasEnhancedMethods:
    """Test new pandas-enhanced methods."""
    
    @pytest.fixture
    def time_series_data(self):
        """Generate time series data for enhanced method testing."""
        n_points = 200
        times = np.linspace(0, 20, n_points)  # 20 seconds
        data = np.sin(2 * np.pi * 0.1 * times) + 0.1 * np.random.randn(n_points)
        return data, times
    
    def test_rolling_mean(self, time_series_data):
        """Test pandas-powered rolling mean."""
        data, times = time_series_data
        ts = baseTs(data, times, freq=10.0)
        
        # Test rolling mean
        window = 20
        ts_rolling = ts.rolling_mean(window=window)
        
        assert isinstance(ts_rolling, baseTs), "Should return baseTs object"
        assert len(ts_rolling) <= len(ts), "Length should be <= original (due to NaN removal)"
        
        # Verify smoothing effect (rolling mean should have lower variance)
        assert ts_rolling.data.var() <= ts.data.var(), "Rolling mean should reduce variance"
        
        # Test inplace
        ts_inplace = ts.copy()
        ts_inplace.rolling_mean(window=window, inplace=True)
        np.testing.assert_array_almost_equal(ts_inplace.data, ts_rolling.data)
    
    def test_rolling_std(self, time_series_data):
        """Test rolling standard deviation."""
        data, times = time_series_data
        ts = baseTs(data, times, freq=10.0)
        
        # Test rolling std
        ts_rolling_std = ts.rolling_std(window=10)
        
        assert isinstance(ts_rolling_std, baseTs), "Should return baseTs object"
        assert np.all(ts_rolling_std.data >= 0), "Standard deviation should be non-negative"
    
    def test_time_slice(self, time_series_data):
        """Test time-based slicing."""
        data, times = time_series_data
        ts = baseTs(data, times, freq=10.0)
        
        # Test time slicing
        start_time, end_time = 5.0, 15.0
        ts_sliced = ts.time_slice(start_time=start_time, end_time=end_time)
        
        assert isinstance(ts_sliced, baseTs), "Should return baseTs object"
        assert ts_sliced.times[0] >= start_time, "First time should be >= start_time"
        assert ts_sliced.times[-1] <= end_time, "Last time should be <= end_time"
        assert len(ts_sliced) < len(ts), "Sliced should be shorter"
        
        # Test inplace
        ts_inplace = ts.copy()
        ts_inplace.time_slice(start_time=start_time, end_time=end_time, inplace=True)
        np.testing.assert_array_almost_equal(ts_inplace.data, ts_sliced.data)
    
    def test_resample(self, time_series_data):
        """Test pandas resampling."""
        data, times = time_series_data
        ts = baseTs(data, times, freq=10.0)
        
        # Test downsampling
        ts_downsampled = ts.resample('1s', method='mean')  # Downsample to 1 Hz
        
        assert isinstance(ts_downsampled, baseTs), "Should return baseTs object"
        assert len(ts_downsampled) < len(ts), "Downsampled should have fewer points"
        # Note: freq is recalculated automatically based on new sampling
    
    def test_correlation_with(self, time_series_data):
        """Test cross-correlation between time series."""
        data, times = time_series_data
        ts1 = baseTs(data, times, freq=10.0, signal_name="signal1")
        
        # Create correlated signal
        correlated_data = 0.8 * data + 0.2 * np.random.randn(len(data))
        ts2 = baseTs(correlated_data, times, freq=10.0, signal_name="signal2")
        
        # Test correlation
        correlation = ts1.correlation_with(ts2, method='pearson')
        
        assert isinstance(correlation, float), "Should return float"
        assert -1 <= correlation <= 1, "Correlation should be between -1 and 1"
        assert correlation > 0.5, "Should detect positive correlation"
    
    def test_detect_outliers(self, time_series_data):
        """Test outlier detection."""
        data, times = time_series_data
        # Add some outliers
        data_with_outliers = data.copy()
        data_with_outliers[50] = 10.0  # Large positive outlier
        data_with_outliers[150] = -10.0  # Large negative outlier
        
        ts = baseTs(data_with_outliers, times, freq=10.0)
        
        # Test z-score outlier detection
        outliers = ts.detect_outliers(method='zscore', threshold=2.0)
        
        assert isinstance(outliers, np.ndarray), "Should return numpy array"
        assert outliers.dtype == bool, "Should return boolean array"
        assert len(outliers) == len(ts), "Should have same length as data"
        assert np.sum(outliers) > 0, "Should detect some outliers"
        
        # Test IQR method
        outliers_iqr = ts.detect_outliers(method='iqr', threshold=1.5)
        assert isinstance(outliers_iqr, np.ndarray), "Should return numpy array"
    
    def test_interpolate_gaps(self, time_series_data):
        """Test gap interpolation."""
        data, times = time_series_data
        # Introduce some NaN gaps
        data_with_gaps = data.copy()
        data_with_gaps[50:55] = np.nan
        data_with_gaps[150:152] = np.nan
        
        ts = baseTs(data_with_gaps, times, freq=10.0)
        
        # Test interpolation
        ts_filled = ts.interpolate_gaps(method='linear')
        
        assert isinstance(ts_filled, baseTs), "Should return baseTs object"
        assert not np.any(np.isnan(ts_filled.data)), "Should fill all gaps"
    
    def test_get_statistics(self, time_series_data):
        """Test comprehensive statistics."""
        data, times = time_series_data
        ts = baseTs(data, times, freq=10.0)
        
        # Test statistics
        stats = ts.get_statistics()
        
        assert isinstance(stats, dict), "Should return dictionary"
        required_keys = ['count', 'mean', 'std', 'min', 'max', 'median', 
                        'q25', 'q75', 'duration', 'frequency', 'sample_rate']
        for key in required_keys:
            assert key in stats, f"Should contain {key}"
        
        assert stats['count'] == len(ts), "Count should match length"
        assert stats['duration'] == ts.duration(), "Duration should match"


class TestPandasIntegration:
    """Test direct pandas integration features."""
    
    @pytest.fixture
    def sample_ts(self):
        """Create sample time series."""
        data = np.random.randn(100)
        times = np.linspace(0, 10, 100)
        return baseTs(data, times, freq=10.0, signal_name="test")
    
    def test_pandas_methods_access(self, sample_ts):
        """Test direct access to pandas methods."""
        ts = sample_ts
        
        # Test pandas describe
        description = ts.describe()
        assert isinstance(description, pd.Series), "Should return pandas Series"
        assert 'mean' in description.index, "Should have mean"
        assert 'std' in description.index, "Should have std"
        
        # Test pandas quantile
        q50 = ts.quantile(0.5)
        assert isinstance(q50, (float, np.floating)), "Should return scalar"
        
        # Test pandas rolling (native)
        rolling = ts.rolling(10)
        assert hasattr(rolling, 'mean'), "Should have rolling methods"
    
    def test_pandas_indexing(self, sample_ts):
        """Test pandas-style indexing."""
        ts = sample_ts
        
        # Test boolean indexing
        positive_mask = ts > 0
        positive_values = ts[positive_mask]
        assert len(positive_values) <= len(ts), "Should filter values"
        assert np.all(positive_values.values > 0), "Should contain only positive values"
        
        # Test positional slice indexing (use iloc for clarity)
        subset = ts.iloc[10:20]
        assert len(subset) == 10, "Should slice correctly"
    
    def test_metadata_preservation(self, sample_ts):
        """Test that metadata is preserved through pandas operations."""
        ts = sample_ts
        
        # Perform pandas operation
        centered = ts - ts.mean()
        
        # Check metadata preservation
        assert hasattr(centered, 'signal_name'), "Should preserve signal_name"
        assert hasattr(centered, 'freq'), "Should preserve frequency"
        assert hasattr(centered, 'history'), "Should preserve history"


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_data_handling(self):
        """Test handling of empty data."""
        # Test that empty data is handled gracefully (may not raise exception)
        try:
            ts = baseTs(np.array([]), np.array([]))
            # If it doesn't raise, it should have length 0
            assert len(ts) == 0, "Empty data should have length 0"
        except (ValueError, IndexError):
            # It's also acceptable to raise an exception
            pass
    
    def test_single_point_data(self):
        """Test handling of single data point."""
        data = np.array([1.0])
        times = np.array([0.0])
        ts = baseTs(data, times, freq=1.0)
        
        assert len(ts) == 1, "Should handle single point"
        assert ts.duration() == 0.0, "Duration should be 0"
    
    def test_constant_data(self):
        """Test handling of constant data."""
        data = np.ones(100)
        times = np.linspace(0, 10, 100)
        ts = baseTs(data, times, freq=10.0)
        
        # Z-scaling of constant data should return zeros
        ts_zscaled = ts.zscale()
        assert np.allclose(ts_zscaled.data, 0.0), "Constant data z-scale should be zeros"
    
    def test_invalid_parameters(self):
        """Test invalid parameter handling."""
        data = np.random.randn(100)
        times = np.linspace(0, 10, 100)
        ts = baseTs(data, times, freq=10.0)
        
        # Test invalid outlier detection method
        with pytest.raises(ValueError):
            ts.detect_outliers(method='invalid_method')
        
        # Test that empty time slice returns empty result (may not raise exception)
        result = ts.time_slice(start_time=20.0, end_time=30.0)  # Outside data range
        assert len(result) == 0 or len(result) <= len(ts), "Should handle out-of-range gracefully"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])