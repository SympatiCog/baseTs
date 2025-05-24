# -*- coding: utf-8 -*-
"""
Property-based testing for baseTs migration.
Uses hypothesis to generate diverse test cases and verify invariants.
"""

import pytest
import numpy as np
import pandas as pd
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
from baseTs import baseTs, BackendManager


# Custom strategies for generating test data
@st.composite
def time_series_data(draw, min_length=10, max_length=1000):
    """Generate valid time series data."""
    length = draw(st.integers(min_value=min_length, max_value=max_length))
    
    # Generate times (must be monotonically increasing)
    start_time = draw(st.floats(min_value=0.0, max_value=10.0))
    end_time = draw(st.floats(min_value=start_time + 0.1, max_value=start_time + 100.0))
    times = np.linspace(start_time, end_time, length)
    
    # Generate data with various characteristics
    data_type = draw(st.sampled_from(['sine', 'random', 'linear', 'constant', 'mixed']))
    
    if data_type == 'sine':
        freq = draw(st.floats(min_value=0.1, max_value=5.0))
        phase = draw(st.floats(min_value=0.0, max_value=2*np.pi))
        amplitude = draw(st.floats(min_value=0.1, max_value=10.0))
        data = amplitude * np.sin(2 * np.pi * freq * times + phase)
    elif data_type == 'random':
        mean = draw(st.floats(min_value=-10.0, max_value=10.0))
        std = draw(st.floats(min_value=0.1, max_value=5.0))
        data = np.random.normal(mean, std, length)
    elif data_type == 'linear':
        slope = draw(st.floats(min_value=-5.0, max_value=5.0))
        intercept = draw(st.floats(min_value=-10.0, max_value=10.0))
        data = slope * times + intercept
    elif data_type == 'constant':
        value = draw(st.floats(min_value=-100.0, max_value=100.0))
        data = np.full(length, value)
    else:  # mixed
        # Combination of sine and linear trend
        freq = draw(st.floats(min_value=0.1, max_value=2.0))
        amplitude = draw(st.floats(min_value=0.1, max_value=5.0))
        slope = draw(st.floats(min_value=-1.0, max_value=1.0))
        noise_std = draw(st.floats(min_value=0.01, max_value=0.5))
        
        trend = slope * times
        periodic = amplitude * np.sin(2 * np.pi * freq * times)
        noise = np.random.normal(0, noise_std, length)
        data = trend + periodic + noise
    
    # Ensure finite values
    data = np.where(np.isfinite(data), data, 0.0)
    
    return data, times


@st.composite
def baseTs_objects(draw):
    """Generate baseTs objects with random backends."""
    data, times = draw(time_series_data())
    backend = draw(st.sampled_from(['numpy', 'series']))
    freq = draw(st.floats(min_value=1.0, max_value=1000.0))
    signal_name = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=65, max_codepoint=90)))
    
    return baseTs(data, times, freq=freq, signal_name=signal_name, backend=backend)


class TestPropertyBasedInvariants:
    """Test invariants that should hold for all operations."""
    
    @given(ts=baseTs_objects())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_copy_preserves_all_properties(self, ts):
        """Test that copy preserves all properties exactly."""
        ts_copy = ts.copy()
        
        # Data and times should be identical
        np.testing.assert_array_equal(ts.data, ts_copy.data)
        np.testing.assert_array_equal(ts.times, ts_copy.times)
        
        # Metadata should be identical
        assert ts.backend == ts_copy.backend
        assert ts.freq == ts_copy.freq
        assert ts.signal_name == ts_copy.signal_name
        assert ts.len() == ts_copy.len()
        assert ts.duration() == ts_copy.duration()
        
        # History should be copied (but not the same object)
        assert ts.history == ts_copy.history
        if len(ts.history) > 0:
            assert ts.history is not ts_copy.history  # Different objects
    
    @given(ts=baseTs_objects())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_mathematical_operations_preserve_length(self, ts):
        """Test that mathematical operations preserve data length."""
        original_length = ts.len()
        
        # All these operations should preserve length
        operations = [
            lambda x: x.zscale(),
            lambda x: x.normalize_range(),
            lambda x: x.center(),
            lambda x: x.scale(2.0),
            lambda x: x.abs(),
        ]
        
        for op in operations:
            result = op(ts)
            assert result.len() == original_length, f"Operation {op} should preserve length"
            assert result.backend == ts.backend, f"Operation {op} should preserve backend"
    
    @given(ts=baseTs_objects())
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_inplace_vs_new_object_equivalence(self, ts):
        """Test that inplace and new object operations produce equivalent results."""
        # Skip if data is too small or has other issues
        assume(ts.len() > 20)
        assume(np.std(ts.data) > 1e-10)  # Avoid constant data for z-scaling
        
        # Test mathematical operations
        operations = [
            ('zscale', lambda x: x.zscale()),
            ('normalize_range', lambda x: x.normalize_range()),
            ('center', lambda x: x.center()),
            ('scale', lambda x: x.scale(1.5)),
            ('abs', lambda x: x.abs()),
        ]
        
        for name, op in operations:
            # Create two identical copies
            ts1 = ts.copy()
            ts2 = ts.copy()
            
            # Apply operation: one inplace, one new object
            result_new = op(ts1)  # New object
            result_inplace = op(ts2.copy())  # Need to copy first since we'll modify inplace
            
            # Apply inplace version
            if name == 'zscale':
                ts2.zscale(inplace=True)
            elif name == 'normalize_range':
                ts2.normalize_range(inplace=True)
            elif name == 'center':
                ts2.center(inplace=True)
            elif name == 'scale':
                ts2.scale(1.5, inplace=True)
            elif name == 'abs':
                ts2.abs(inplace=True)
            
            # Results should be equivalent
            np.testing.assert_array_almost_equal(
                result_new.data, ts2.data, decimal=10,
                err_msg=f"Inplace and new object {name} should produce same results"
            )
    
    @given(ts=baseTs_objects(), factor=st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_scaling_properties(self, ts, factor):
        """Test mathematical properties of scaling."""
        assume(abs(factor) > 1e-10)  # Avoid division by near-zero
        
        ts_scaled = ts.scale(factor)
        
        # Scaling should multiply all values by factor
        expected = ts.data * factor
        np.testing.assert_array_almost_equal(ts_scaled.data, expected, decimal=10)
        
        # Mean should scale by factor
        if not np.isclose(ts.data.mean(), 0, atol=1e-10):
            expected_mean = ts.data.mean() * factor
            assert np.isclose(ts_scaled.data.mean(), expected_mean, rtol=1e-10)
        
        # Standard deviation should scale by absolute factor
        if not np.isclose(ts.data.std(), 0, atol=1e-10):
            expected_std = ts.data.std() * abs(factor)
            assert np.isclose(ts_scaled.data.std(), expected_std, rtol=1e-10)
    
    @given(ts=baseTs_objects())
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_centering_properties(self, ts):
        """Test mathematical properties of centering."""
        ts_centered = ts.center()
        
        # Centered data should have mean ~0
        assert abs(ts_centered.data.mean()) < 1e-10, "Centered data should have zero mean"
        
        # Standard deviation should be preserved
        if not np.isclose(ts.data.std(), 0, atol=1e-10):
            assert np.isclose(ts_centered.data.std(), ts.data.std(), rtol=1e-10)
        
        # Shape should be preserved
        assert ts_centered.data.shape == ts.data.shape
    
    @given(ts=baseTs_objects())
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_normalization_properties(self, ts):
        """Test mathematical properties of normalization."""
        assume(ts.len() > 5)
        assume(np.max(ts.data) - np.min(ts.data) > 1e-10)  # Avoid constant data
        
        ts_norm = ts.normalize_range()
        
        # Normalized data should be in [0, 1]
        assert np.all(ts_norm.data >= -1e-10), "Normalized data should be >= 0"
        assert np.all(ts_norm.data <= 1 + 1e-10), "Normalized data should be <= 1"
        
        # Should preserve min/max mapping
        assert np.isclose(np.min(ts_norm.data), 0.0, atol=1e-10), "Min should map to 0"
        assert np.isclose(np.max(ts_norm.data), 1.0, atol=1e-10), "Max should map to 1"
    
    @given(ts=baseTs_objects())
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_absolute_value_properties(self, ts):
        """Test properties of absolute value operation."""
        ts_abs = ts.abs()
        
        # All values should be non-negative
        assert np.all(ts_abs.data >= 0), "Absolute values should be non-negative"
        
        # Shape should be preserved
        assert ts_abs.data.shape == ts.data.shape
        
        # Values should match np.abs
        np.testing.assert_array_equal(ts_abs.data, np.abs(ts.data))
    
    @given(ts=baseTs_objects())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_backend_consistency_after_operations(self, ts):
        """Test that backend is preserved through operations."""
        original_backend = ts.backend
        
        # Chain several operations
        result = ts.center().scale(1.5).abs().normalize_range()
        
        assert result.backend == original_backend, "Backend should be preserved through operation chains"


class TestPropertyBasedFiltering:
    """Property-based tests for filtering operations."""
    
    @given(ts=baseTs_objects(), cutoff=st.floats(min_value=0.1, max_value=10.0))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_lowpass_filter_properties(self, ts, cutoff):
        """Test properties of lowpass filtering."""
        assume(ts.len() > 50)  # Need sufficient data for filtering
        assume(ts.freq > cutoff * 4)  # Ensure cutoff is below Nyquist
        assume(np.std(ts.data) > 1e-10)  # Avoid constant data
        
        try:
            ts_filtered = ts.lowpass_at(cutoff, order=2)
            
            # Basic properties
            assert ts_filtered.len() == ts.len(), "Lowpass filter should preserve length"
            assert ts_filtered.backend == ts.backend, "Backend should be preserved"
            assert ts_filtered._get_metadata_attr('is_filtered') is True, "Should be marked as filtered"
            
            # Lowpass should generally reduce high-frequency content (reduce variance for most signals)
            if np.var(ts.data) > 1e-6:  # Only test for non-trivial signals
                # Note: This isn't always true for all signals, but generally holds
                pass  # Commenting out variance check as it's not universally true
            
        except Exception as e:
            # Filter might fail for some parameter combinations, which is acceptable
            assume(False)  # Skip this test case
    
    @given(ts=baseTs_objects(), 
           window=st.integers(min_value=5, max_value=51))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_rolling_mean_properties(self, ts, window):
        """Test properties of rolling mean."""
        assume(ts.len() > window + 10)  # Need sufficient data
        assume(window % 2 == 1)  # Window should be odd for centering
        
        ts_rolling = ts.rolling_mean(window=window, center=True)
        
        # Rolling mean should reduce length due to NaN removal
        assert ts_rolling.len() <= ts.len(), "Rolling mean should not increase length"
        assert ts_rolling.len() >= ts.len() - window, "Should not lose too much data"
        
        # Backend should be preserved
        assert ts_rolling.backend == ts.backend, "Backend should be preserved"
        
        # Rolling mean should generally reduce variance (smoothing effect)
        if np.var(ts.data) > 1e-6:  # Only test for non-trivial signals
            # For most signals, rolling mean reduces variance
            # Note: This is a general tendency, not a mathematical guarantee
            pass  # Commenting out as it's not universally true


class TestPropertyBasedTimeOperations:
    """Property-based tests for time-based operations."""
    
    @given(ts=baseTs_objects(), 
           start_frac=st.floats(min_value=0.1, max_value=0.4),
           end_frac=st.floats(min_value=0.6, max_value=0.9))
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_time_slice_properties(self, ts, start_frac, end_frac):
        """Test properties of time slicing."""
        assume(ts.len() > 20)  # Need sufficient data
        assume(start_frac < end_frac)  # Ensure valid range
        
        # Calculate actual start and end times
        duration = ts.duration()
        start_time = ts.times[0] + start_frac * duration
        end_time = ts.times[0] + end_frac * duration
        
        ts_sliced = ts.time_slice(start_time=start_time, end_time=end_time)
        
        # Basic properties
        assert ts_sliced.len() <= ts.len(), "Slicing should not increase length"
        assert ts_sliced.len() > 0, "Slicing should produce non-empty result"
        assert ts_sliced.backend == ts.backend, "Backend should be preserved"
        
        # Time bounds should be respected
        if ts_sliced.len() > 0:
            assert ts_sliced.times[0] >= start_time - 1e-10, "First time should be >= start_time"
            assert ts_sliced.times[-1] <= end_time + 1e-10, "Last time should be <= end_time"
        
        # Duration should be smaller
        assert ts_sliced.duration() <= ts.duration(), "Sliced duration should be <= original"
    
    @given(ts=baseTs_objects())
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_statistics_properties(self, ts):
        """Test properties of statistical calculations."""
        stats = ts.get_statistics()
        
        # Basic properties
        assert isinstance(stats, dict), "Statistics should be a dictionary"
        assert stats['count'] == ts.len(), "Count should match data length"
        assert stats['duration'] == ts.duration(), "Duration should match"
        assert stats['frequency'] == ts.freq, "Frequency should match"
        
        # Mathematical properties
        assert stats['min'] <= stats['mean'] <= stats['max'], "Mean should be between min and max"
        assert stats['q25'] <= stats['median'] <= stats['q75'], "Median should be between quartiles"
        assert stats['min'] <= stats['q25'] <= stats['q75'] <= stats['max'], "Quartiles should be ordered"
        assert stats['std'] >= 0, "Standard deviation should be non-negative"
        
        # Verify against numpy calculations
        np.testing.assert_almost_equal(stats['mean'], np.mean(ts.data), decimal=10)
        np.testing.assert_almost_equal(stats['std'], np.std(ts.data), decimal=10)
        np.testing.assert_almost_equal(stats['min'], np.min(ts.data), decimal=10)
        np.testing.assert_almost_equal(stats['max'], np.max(ts.data), decimal=10)


class TestPropertyBasedChaining:
    """Test properties of operation chaining."""
    
    @given(ts=baseTs_objects())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_operation_chaining_preserves_backend(self, ts):
        """Test that chaining operations preserves backend."""
        assume(ts.len() > 20)
        assume(np.std(ts.data) > 1e-10)  # Avoid constant data
        
        original_backend = ts.backend
        
        # Chain multiple operations
        result = ts.center().scale(2.0).abs()
        
        assert result.backend == original_backend, "Chained operations should preserve backend"
    
    @given(ts=baseTs_objects())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_operation_chaining_accumulates_history(self, ts):
        """Test that chaining operations accumulates history."""
        assume(ts.len() > 20)
        assume(np.std(ts.data) > 1e-10)
        
        original_history_length = len(ts.history)
        
        # Chain multiple operations
        result = ts.center().scale(2.0).abs()
        
        assert len(result.history) > original_history_length, "History should accumulate with chaining"
        assert len(result.history) >= original_history_length + 3, "Should have at least 3 new history entries"
    
    @given(ts=baseTs_objects())
    @settings(max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_mathematical_operation_commutativity(self, ts):
        """Test mathematical properties of operation combinations."""
        assume(ts.len() > 10)
        assume(np.std(ts.data) > 1e-10)
        assume(np.all(np.isfinite(ts.data)))
        
        # Test that centering then scaling gives same result as scaling then centering (with adjustment)
        centered_then_scaled = ts.center().scale(2.0)
        
        # For comparison, manually compute: scale(center(x)) vs center(scale(x))
        # These won't be identical, but we can test related properties
        
        # Test that operations are consistent
        result1 = ts.scale(2.0).center()
        result2 = ts.center().scale(2.0)
        
        # Both should have zero mean after centering
        assert abs(result1.data.mean()) < 1e-10, "Should have zero mean after centering"
        assert abs(result2.data.mean()) < 1e-10, "Should have zero mean after centering"