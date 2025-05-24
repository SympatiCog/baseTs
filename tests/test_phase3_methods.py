# -*- coding: utf-8 -*-
"""
Comprehensive test suite for Phase 3 migrated methods.
Tests all mathematical operations, filtering, and new pandas-enhanced methods.
"""

import pytest
import numpy as np
import pandas as pd
from baseTs import baseTs, BackendManager
from baseTs.compat import convert_to_series, convert_to_basetseries


class TestMathematicalOperations:
    """Test all mathematical operations across both backends."""
    
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
    
    @pytest.mark.parametrize("backend", ["numpy", "series"])
    def test_zscale_operations(self, sample_data, backend):
        """Test z-scaling operations."""
        data, times = sample_data
        ts = baseTs(data, times, freq=10.0, backend=backend)
        
        # Test z-scaling
        ts_zscaled = ts.zscale()
        
        # Verify z-scaling properties
        assert abs(ts_zscaled.data.mean()) < 1e-10, "Z-scaled mean should be ~0"
        assert abs(ts_zscaled.data.std() - 1.0) < 1e-10, "Z-scaled std should be 1"
        assert ts_zscaled.backend == backend, "Backend should be preserved"
        assert len(ts_zscaled.history) > len(ts.history), "History should be updated"
        
        # Test inplace operation
        ts_inplace = ts.copy()
        result = ts_inplace.zscale(inplace=True)
        assert result is ts_inplace, "Inplace should return self"
        assert abs(ts_inplace.data.mean()) < 1e-10, "Inplace z-scaling should work"
    
    @pytest.mark.parametrize("backend", ["numpy", "series"])
    def test_normalize_range_operations(self, sample_data, backend):
        """Test range normalization operations."""
        data, times = sample_data
        ts = baseTs(data, times, freq=10.0, backend=backend)
        
        # Test default normalization (0-1)
        ts_norm = ts.normalize_range()
        assert abs(ts_norm.data.min() - 0.0) < 1e-10, "Min should be 0"
        assert abs(ts_norm.data.max() - 1.0) < 1e-10, "Max should be 1"
        assert ts_norm.backend == backend, "Backend should be preserved"
        
        # Test custom range
        ts_custom = ts.normalize_range(target_min=-5.0, target_max=5.0)
        assert abs(ts_custom.data.min() - (-5.0)) < 1e-10, "Custom min should work"
        assert abs(ts_custom.data.max() - 5.0) < 1e-10, "Custom max should work"
        
        # Test constant data (edge case)
        constant_data = np.ones(100)
        ts_constant = baseTs(constant_data, times, backend=backend)
        ts_const_norm = ts_constant.normalize_range()
        assert np.allclose(ts_const_norm.data, 0.5), "Constant data should normalize to midpoint"
    
    @pytest.mark.parametrize("backend", ["numpy", "series"])
    def test_center_operations(self, sample_data, backend):
        """Test centering operations."""
        data, times = sample_data
        ts = baseTs(data, times, freq=10.0, backend=backend)
        
        original_mean = ts.data.mean()
        ts_centered = ts.center()
        
        assert abs(ts_centered.data.mean()) < 1e-10, "Centered mean should be ~0"
        assert ts_centered.backend == backend, "Backend should be preserved"
        # Verify the transformation
        expected = data - original_mean
        np.testing.assert_array_almost_equal(ts_centered.data, expected)
    
    @pytest.mark.parametrize("backend", ["numpy", "series"])
    def test_scale_operations(self, sample_data, backend):
        """Test scaling operations."""
        data, times = sample_data
        ts = baseTs(data, times, freq=10.0, backend=backend)
        
        factor = 2.5
        ts_scaled = ts.scale(factor)
        
        expected = data * factor
        np.testing.assert_array_almost_equal(ts_scaled.data, expected)
        assert ts_scaled.backend == backend, "Backend should be preserved"
        
        # Test negative scaling
        ts_negative = ts.scale(-1.0)
        np.testing.assert_array_almost_equal(ts_negative.data, -data)
    
    @pytest.mark.parametrize("backend", ["numpy", "series"])
    def test_abs_operations(self, sample_data, backend):
        """Test absolute value operations."""
        data, times = sample_data
        
        # Create data with negative values
        mixed_data = data - data.mean()  # Center around zero
        ts = baseTs(mixed_data, times, freq=10.0, backend=backend)
        
        ts_abs = ts.abs()
        
        assert np.all(ts_abs.data >= 0), "All values should be non-negative"
        np.testing.assert_array_almost_equal(ts_abs.data, np.abs(mixed_data))
        assert ts_abs.backend == backend, "Backend should be preserved"
    
    @pytest.mark.parametrize("backend", ["numpy", "series"])
    def test_method_chaining(self, sample_data, backend):
        """Test chaining multiple mathematical operations."""
        data, times = sample_data
        ts = baseTs(data, times, freq=10.0, backend=backend)
        
        # Chain multiple operations
        ts_chained = ts.center().scale(2.0).abs().normalize_range()
        
        assert ts_chained.backend == backend, "Backend should be preserved through chaining"
        assert abs(ts_chained.data.min() - 0.0) < 1e-10, "Final min should be 0"
        assert abs(ts_chained.data.max() - 1.0) < 1e-10, "Final max should be 1"
        assert len(ts_chained.history) > len(ts.history), "History should accumulate"


class TestFilteringOperations:
    """Test all filtering operations across both backends."""
    
    @pytest.fixture
    def test_signal(self):
        """Generate test signal with known frequency components."""
        n_points = 2000
        fs = 100.0  # 100 Hz sampling
        t = np.arange(n_points) / fs
        
        # Signal: 2 Hz + 10 Hz + 30 Hz + noise
        signal = (
            np.sin(2 * np.pi * 2 * t) +
            0.5 * np.sin(2 * np.pi * 10 * t) +
            0.2 * np.sin(2 * np.pi * 30 * t) +
            0.1 * np.random.randn(n_points)
        )
        
        return signal, t, fs
    
    @pytest.mark.parametrize("backend", ["numpy", "series"])
    def test_lowpass_filter(self, test_signal, backend):
        """Test lowpass filtering."""
        signal, times, fs = test_signal
        ts = baseTs(signal, times, freq=fs, backend=backend)
        
        # Apply lowpass filter at 5 Hz (should preserve 2 Hz, attenuate 10 Hz and 30 Hz)
        ts_filtered = ts.lowpass_at(5.0, order=4)
        
        assert ts_filtered.backend == backend, "Backend should be preserved"
        assert ts_filtered._get_metadata_attr('is_filtered') is True, "Should be marked as filtered"
        assert ts_filtered.data.std() < ts.data.std(), "Filtered signal should have lower variance"
        
        # Test inplace operation
        ts_inplace = ts.copy()
        result = ts_inplace.lowpass_at(5.0, inplace=True)
        assert result is ts_inplace, "Inplace should return self"
        np.testing.assert_array_almost_equal(ts_inplace.data, ts_filtered.data, decimal=10)
    
    @pytest.mark.parametrize("backend", ["numpy", "series"])
    def test_highpass_filter(self, test_signal, backend):
        """Test highpass filtering."""
        signal, times, fs = test_signal
        ts = baseTs(signal, times, freq=fs, backend=backend)
        
        # Apply highpass filter at 15 Hz (should attenuate 2 Hz and 10 Hz, preserve 30 Hz)
        ts_filtered = ts.highpass_at(15.0, order=4)
        
        assert ts_filtered.backend == backend, "Backend should be preserved"
        assert ts_filtered._get_metadata_attr('is_filtered') is True, "Should be marked as filtered"
        # High-passed signal should have different characteristics
        assert ts_filtered.data.mean() != ts.data.mean(), "Mean should change with highpass"
    
    @pytest.mark.parametrize("backend", ["numpy", "series"])
    def test_bandpass_filter(self, test_signal, backend):
        """Test bandpass filtering."""
        signal, times, fs = test_signal
        ts = baseTs(signal, times, freq=fs, backend=backend)
        
        # Apply bandpass filter 8-12 Hz (should preserve 10 Hz component)
        ts_filtered = ts.bandpass_at(hp_hz=8.0, lp_hz=12.0, reset_mean=True)
        
        assert ts_filtered.backend == backend, "Backend should be preserved"
        assert ts_filtered._get_metadata_attr('is_filtered') is True, "Should be marked as filtered"
        
        # Test reset_mean functionality
        original_mean = ts.data.mean()
        filtered_mean = ts_filtered.data.mean()
        assert abs(filtered_mean - original_mean) < 0.1, "Mean should be approximately preserved"
    
    @pytest.mark.parametrize("backend", ["numpy", "series"])
    def test_notch_filter(self, test_signal, backend):
        """Test notch filtering."""
        signal, times, fs = test_signal
        ts = baseTs(signal, times, freq=fs, backend=backend)
        
        # Apply notch filter at 10 Hz (should remove 10 Hz component)
        ts_filtered = ts.notch_at(10.0, order=4)
        
        assert ts_filtered.backend == backend, "Backend should be preserved"
        assert ts_filtered._get_metadata_attr('is_filtered') is True, "Should be marked as filtered"
    
    @pytest.mark.parametrize("backend", ["numpy", "series"])
    def test_gaussian_filter(self, test_signal, backend):
        """Test Gaussian filtering."""
        signal, times, fs = test_signal
        ts = baseTs(signal, times, freq=fs, backend=backend)
        
        ts_filtered = ts.gauss_filter(sigma=2.0)
        
        assert ts_filtered.backend == backend, "Backend should be preserved"
        assert ts_filtered._get_metadata_attr('is_filtered') is True, "Should be marked as filtered"
        assert ts_filtered.data.std() < ts.data.std(), "Gaussian filter should reduce variance"
    
    @pytest.mark.parametrize("backend", ["numpy", "series"])
    def test_sg_filter(self, test_signal, backend):
        """Test Savitzky-Golay filtering."""
        signal, times, fs = test_signal
        ts = baseTs(signal, times, freq=fs, backend=backend)
        
        ts_filtered = ts.sg_filter(window_length=21, polyorder=3)
        
        assert ts_filtered.backend == backend, "Backend should be preserved"
        assert ts_filtered._get_metadata_attr('is_filtered') is True, "Should be marked as filtered"
        # SG filter should smooth the data
        assert ts_filtered.data.std() <= ts.data.std(), "SG filter should not increase variance"
    
    @pytest.mark.parametrize("backend", ["numpy", "series"])
    def test_filter_chaining(self, test_signal, backend):
        """Test chaining multiple filters."""
        signal, times, fs = test_signal
        ts = baseTs(signal, times, freq=fs, backend=backend)
        
        # Chain filters: bandpass -> lowpass -> gaussian
        ts_chained = ts.bandpass_at(hp_hz=1.0, lp_hz=20.0).lowpass_at(15.0).gauss_filter(sigma=1.0)
        
        assert ts_chained.backend == backend, "Backend should be preserved through chaining"
        assert ts_chained._get_metadata_attr('is_filtered') is True, "Should be marked as filtered"
        assert len(ts_chained.history) > len(ts.history), "History should accumulate"


class TestPandasEnhancedMethods:
    """Test new pandas-enhanced methods."""
    
    @pytest.fixture
    def trending_data(self):
        """Generate data with trend and seasonal patterns."""
        n_points = 500
        t = np.linspace(0, 50, n_points)
        
        # Trend + seasonal + noise
        trend = 0.1 * t
        seasonal = 2 * np.sin(2 * np.pi * t / 10)  # 10-unit period
        noise = 0.3 * np.random.randn(n_points)
        
        signal = trend + seasonal + noise
        return signal, t
    
    @pytest.mark.parametrize("backend", ["numpy", "series"])
    def test_rolling_mean(self, trending_data, backend):
        """Test rolling mean operations."""
        data, times = trending_data
        ts = baseTs(data, times, freq=10.0, backend=backend)
        
        window = 25
        ts_rolling = ts.rolling_mean(window=window, center=True)
        
        assert ts_rolling.backend == backend, "Backend should be preserved"
        assert ts_rolling.len() < ts.len(), "Rolling mean should reduce length (NaN removal)"
        assert ts_rolling.data.std() < ts.data.std(), "Rolling mean should reduce variance"
        
        # Test inplace operation
        ts_inplace = ts.copy()
        result = ts_inplace.rolling_mean(window=window, inplace=True)
        assert result is ts_inplace, "Inplace should return self"
        assert ts_inplace.len() == ts_rolling.len(), "Inplace should produce same result"
        
        # Test different center settings
        ts_no_center = ts.rolling_mean(window=window, center=False)
        assert ts_no_center.len() == ts_rolling.len(), "Center setting affects result"
    
    @pytest.mark.parametrize("backend", ["numpy", "series"])
    def test_time_slice(self, trending_data, backend):
        """Test time-based slicing."""
        data, times = trending_data
        ts = baseTs(data, times, freq=10.0, backend=backend)
        
        start_time, end_time = 10.0, 40.0
        ts_sliced = ts.time_slice(start_time=start_time, end_time=end_time)
        
        assert ts_sliced.backend == backend, "Backend should be preserved"
        assert ts_sliced.times[0] >= start_time, "First time should be >= start_time"
        assert ts_sliced.times[-1] <= end_time, "Last time should be <= end_time"
        assert ts_sliced.len() < ts.len(), "Sliced data should be shorter"
        
        # Test partial slicing
        ts_start_only = ts.time_slice(start_time=start_time)
        assert ts_start_only.times[0] >= start_time, "Start-only slice should work"
        assert ts_start_only.times[-1] == ts.times[-1], "End should be preserved"
        
        ts_end_only = ts.time_slice(end_time=end_time)
        assert ts_end_only.times[0] == ts.times[0], "Start should be preserved"
        assert ts_end_only.times[-1] <= end_time, "End-only slice should work"
        
        # Test inplace operation
        ts_inplace = ts.copy()
        result = ts_inplace.time_slice(start_time=start_time, end_time=end_time, inplace=True)
        assert result is ts_inplace, "Inplace should return self"
        np.testing.assert_array_equal(ts_inplace.data, ts_sliced.data)
    
    @pytest.mark.parametrize("backend", ["numpy", "series"])
    def test_get_statistics(self, trending_data, backend):
        """Test comprehensive statistics."""
        data, times = trending_data
        ts = baseTs(data, times, freq=10.0, backend=backend)
        
        stats = ts.get_statistics()
        
        # Verify all expected keys are present
        expected_keys = [
            'count', 'mean', 'std', 'min', 'max', 'median',
            'q25', 'q75', 'duration', 'frequency', 'sample_rate'
        ]
        for key in expected_keys:
            assert key in stats, f"Statistics should include {key}"
        
        # Verify statistical accuracy
        assert stats['count'] == len(ts.data), "Count should match data length"
        assert abs(stats['mean'] - np.mean(ts.data)) < 1e-10, "Mean should be accurate"
        assert abs(stats['std'] - np.std(ts.data)) < 1e-10, "Std should be accurate"
        assert abs(stats['min'] - np.min(ts.data)) < 1e-10, "Min should be accurate"
        assert abs(stats['max'] - np.max(ts.data)) < 1e-10, "Max should be accurate"
        assert abs(stats['median'] - np.median(ts.data)) < 1e-10, "Median should be accurate"
        assert stats['duration'] == ts.duration(), "Duration should match"
        assert stats['frequency'] == ts.freq, "Frequency should match"
        
        # Verify quartiles
        assert stats['q25'] == np.percentile(ts.data, 25), "Q25 should be accurate"
        assert stats['q75'] == np.percentile(ts.data, 75), "Q75 should be accurate"


class TestBackendConsistency:
    """Test that operations produce identical results across backends."""
    
    @pytest.fixture
    def test_data(self):
        """Generate consistent test data."""
        np.random.seed(42)  # For reproducible results
        n_points = 200
        t = np.linspace(0, 20, n_points)
        signal = np.sin(2 * np.pi * 0.3 * t) + 0.5 * np.sin(2 * np.pi * 1.7 * t) + 0.2 * np.random.randn(n_points)
        return signal, t
    
    def test_mathematical_operations_consistency(self, test_data):
        """Test mathematical operations produce identical results."""
        data, times = test_data
        
        ts_numpy = baseTs(data, times, freq=10.0, backend='numpy')
        ts_series = baseTs(data, times, freq=10.0, backend='series')
        
        # Test all mathematical operations
        operations = [
            lambda ts: ts.zscale(),
            lambda ts: ts.normalize_range(),
            lambda ts: ts.center(),
            lambda ts: ts.scale(1.5),
            lambda ts: ts.abs(),
        ]
        
        for op in operations:
            result_numpy = op(ts_numpy)
            result_series = op(ts_series)
            
            np.testing.assert_array_almost_equal(
                result_numpy.data, result_series.data, decimal=12,
                err_msg=f"Operation {op.__name__} should produce identical results"
            )
            np.testing.assert_array_almost_equal(
                result_numpy.times, result_series.times, decimal=12,
                err_msg=f"Operation {op.__name__} should preserve times identically"
            )
    
    def test_filtering_operations_consistency(self, test_data):
        """Test filtering operations produce identical results."""
        data, times = test_data
        
        ts_numpy = baseTs(data, times, freq=10.0, backend='numpy')
        ts_series = baseTs(data, times, freq=10.0, backend='series')
        
        # Test filtering operations
        filter_ops = [
            lambda ts: ts.lowpass_at(2.0, order=3),
            lambda ts: ts.highpass_at(0.5, order=3),
            lambda ts: ts.bandpass_at(hp_hz=0.5, lp_hz=2.0),
            lambda ts: ts.gauss_filter(sigma=1.5),
            lambda ts: ts.sg_filter(window_length=11, polyorder=2),
        ]
        
        for op in filter_ops:
            result_numpy = op(ts_numpy)
            result_series = op(ts_series)
            
            np.testing.assert_array_almost_equal(
                result_numpy.data, result_series.data, decimal=10,
                err_msg=f"Filter operation should produce identical results"
            )
    
    def test_enhanced_methods_consistency(self, test_data):
        """Test pandas-enhanced methods work consistently."""
        data, times = test_data
        
        ts_numpy = baseTs(data, times, freq=10.0, backend='numpy')
        ts_series = baseTs(data, times, freq=10.0, backend='series')
        
        # Test enhanced methods that should work on both backends
        # Rolling mean
        roll_numpy = ts_numpy.rolling_mean(window=15)
        roll_series = ts_series.rolling_mean(window=15)
        
        assert roll_numpy.len() == roll_series.len(), "Rolling mean should produce same length"
        np.testing.assert_array_almost_equal(
            roll_numpy.data, roll_series.data, decimal=10,
            err_msg="Rolling mean should produce identical results"
        )
        
        # Time slice
        slice_numpy = ts_numpy.time_slice(start_time=5.0, end_time=15.0)
        slice_series = ts_series.time_slice(start_time=5.0, end_time=15.0)
        
        assert slice_numpy.len() == slice_series.len(), "Time slice should produce same length"
        np.testing.assert_array_almost_equal(
            slice_numpy.data, slice_series.data, decimal=12,
            err_msg="Time slice should produce identical results"
        )
        
        # Statistics
        stats_numpy = ts_numpy.get_statistics()
        stats_series = ts_series.get_statistics()
        
        for key in stats_numpy.keys():
            if isinstance(stats_numpy[key], (int, float)):
                assert abs(stats_numpy[key] - stats_series[key]) < 1e-10, f"Statistic {key} should match"


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_data_handling(self):
        """Test handling of empty data."""
        with pytest.raises(Exception):  # Should raise some kind of error
            baseTs(np.array([]), np.array([]))
    
    def test_single_point_data(self):
        """Test handling of single data point."""
        data = np.array([1.0])
        times = np.array([0.0])
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data, times, backend=backend)
            assert ts.len() == 1
            assert ts.duration() == 0.0
            
            # Mathematical operations should still work
            ts_scaled = ts.scale(2.0)
            assert ts_scaled.data[0] == 2.0
    
    def test_constant_data(self):
        """Test operations on constant data."""
        data = np.ones(100) * 5.0
        times = np.linspace(0, 10, 100)
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data, times, backend=backend)
            
            # Test operations that might have division by zero
            ts_zscaled = ts.zscale()
            assert np.all(np.isfinite(ts_zscaled.data)), "Z-scaling constant data should not produce NaN"
            
            ts_norm = ts.normalize_range()
            assert np.allclose(ts_norm.data, 0.5), "Normalizing constant data should give midpoint"
    
    def test_very_large_data(self):
        """Test with large datasets."""
        n_points = 50000
        data = np.random.randn(n_points)
        times = np.linspace(0, 100, n_points)
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data, times, freq=500.0, backend=backend)
            
            # Test that operations complete without memory issues
            ts_filtered = ts.lowpass_at(50.0)
            assert ts_filtered.len() == n_points
            
            ts_rolled = ts.rolling_mean(window=100)
            assert ts_rolled.len() < n_points  # Some data lost due to NaN removal
    
    @pytest.mark.parametrize("backend", ["numpy", "series"])
    def test_invalid_parameters(self, backend):
        """Test handling of invalid parameters."""
        data = np.random.randn(100)
        times = np.linspace(0, 10, 100)
        ts = baseTs(data, times, backend=backend)
        
        # Test invalid filter parameters
        with pytest.raises(Exception):
            ts.lowpass_at(-1.0)  # Negative frequency
        
        with pytest.raises(Exception):
            ts.lowpass_at(1000.0)  # Frequency above Nyquist
        
        # Test invalid rolling window
        with pytest.raises(Exception):
            ts.rolling_mean(window=0)  # Zero window
        
        with pytest.raises(Exception):
            ts.rolling_mean(window=200)  # Window larger than data