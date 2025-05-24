# -*- coding: utf-8 -*-
"""
Test suite for baseTs pandas migration.
Tests compatibility between numpy and Series backends.
"""

import pytest
import numpy as np
import pandas as pd
from baseTs.series import TimeSeriesData
from baseTs.compat import convert_to_series, convert_to_basetseries, BackendManager
from baseTs import baseTs


class TestTimeSeriesDataBasics:
    """Test basic TimeSeriesData functionality."""
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample time series data."""
        n_points = 100
        times = np.linspace(0, 10, n_points)
        data = np.sin(2 * np.pi * 0.5 * times) + 0.1 * np.random.randn(n_points)
        return data, times
    
    def test_creation_from_arrays(self, sample_data):
        """Test TimeSeriesData creation from numpy arrays."""
        data, times = sample_data
        ts_data = TimeSeriesData(data, index=times, freq=10.0, signal_name="TEST")
        
        assert len(ts_data) == len(data)
        assert ts_data.signal_name == "TEST"
        assert ts_data.freq == 10.0
        np.testing.assert_array_equal(ts_data.values, data)
        np.testing.assert_array_equal(ts_data.index.values, times)
    
    def test_creation_from_basetseries(self, sample_data):
        """Test TimeSeriesData creation from baseTs object."""
        data, times = sample_data
        base_ts = baseTs(data, times, signal_name="test_signal", freq=10.0)
        ts_data = TimeSeriesData(base_ts)
        
        assert len(ts_data) == len(data)
        assert ts_data.signal_name == "TEST_SIGNAL"  # Should be uppercase
        assert ts_data.freq == 10.0
        np.testing.assert_array_equal(ts_data.values, data)
        np.testing.assert_array_equal(ts_data.index.values, times)
    
    def test_basic_properties(self, sample_data):
        """Test basic properties and methods."""
        data, times = sample_data
        ts_data = TimeSeriesData(data, index=times)
        
        assert ts_data.len() == len(data)
        assert abs(ts_data.duration() - (times[-1] - times[0])) < 1e-10
        assert ts_data.freq > 0  # Should calculate effective frequency
    
    def test_copy_preserves_metadata(self, sample_data):
        """Test that copy preserves all metadata."""
        data, times = sample_data
        ts_data = TimeSeriesData(data, index=times, freq=10.0, signal_name="TEST")
        ts_data.is_filtered = True
        ts_data.history.append("Test operation")
        
        copied = ts_data.copy()
        
        assert copied.freq == ts_data.freq
        assert copied.signal_name == ts_data.signal_name
        assert copied.is_filtered == ts_data.is_filtered
        assert copied.history == ts_data.history
        assert copied.history is not ts_data.history  # Should be deep copy


class TestCompatibilityLayer:
    """Test compatibility layer functionality."""
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample time series data."""
        n_points = 50
        times = np.linspace(0, 5, n_points)
        data = np.cos(2 * np.pi * times) + 0.05 * np.random.randn(n_points)
        return data, times
    
    def test_convert_to_series(self, sample_data):
        """Test conversion from various types to TimeSeriesData."""
        data, times = sample_data
        
        # From numpy arrays
        ts_data = convert_to_series(data, times=times, freq=10.0)
        assert isinstance(ts_data, TimeSeriesData)
        np.testing.assert_array_equal(ts_data.values, data)
        
        # From baseTs object
        base_ts = baseTs(data, times, freq=10.0)
        ts_data2 = convert_to_series(base_ts)
        assert isinstance(ts_data2, TimeSeriesData)
        np.testing.assert_array_equal(ts_data2.values, data)
        
        # From pandas Series
        series = pd.Series(data, index=times)
        ts_data3 = convert_to_series(series, freq=10.0)
        assert isinstance(ts_data3, TimeSeriesData)
        np.testing.assert_array_equal(ts_data3.values, data)
    
    def test_convert_to_basetseries(self, sample_data):
        """Test conversion from TimeSeriesData back to baseTs."""
        data, times = sample_data
        ts_data = TimeSeriesData(data, index=times, freq=10.0, signal_name="TEST")
        
        base_ts = convert_to_basetseries(ts_data)
        
        assert isinstance(base_ts, baseTs)
        np.testing.assert_array_equal(base_ts.data, data)
        np.testing.assert_array_equal(base_ts.times, times)
        assert base_ts.freq == 10.0
    
    def test_backend_manager(self):
        """Test backend manager functionality."""
        # Test default backend
        assert BackendManager.get_default_backend() == 'numpy'
        
        # Test setting backend
        BackendManager.set_default_backend('series')
        assert BackendManager.get_default_backend() == 'series'
        
        # Test should_use_series
        assert BackendManager.should_use_series() == True
        assert BackendManager.should_use_series(False) == False
        
        # Reset to numpy for other tests
        BackendManager.set_default_backend('numpy')


class TestDataCompatibility:
    """Test data compatibility between numpy and Series backends."""
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample time series data."""
        n_points = 100
        times = np.linspace(0, 10, n_points)
        # Create signal with known properties
        data = np.sin(2 * np.pi * 0.1 * times) + 0.5 * np.sin(2 * np.pi * 0.3 * times)
        return data, times
    
    def test_mathematical_operations_equivalence(self, sample_data):
        """Test that mathematical operations produce equivalent results."""
        data, times = sample_data
        
        # Create both backends
        base_ts = baseTs(data, times, freq=10.0)
        ts_data = TimeSeriesData(data, index=times, freq=10.0)
        
        # Test basic mathematical operations
        np.testing.assert_array_almost_equal(
            base_ts.data.mean(), ts_data.values.mean()
        )
        np.testing.assert_array_almost_equal(
            base_ts.data.std(), ts_data.values.std()
        )
        np.testing.assert_array_almost_equal(
            base_ts.data.min(), ts_data.values.min()
        )
        np.testing.assert_array_almost_equal(
            base_ts.data.max(), ts_data.values.max()
        )
    
    def test_property_access_equivalence(self, sample_data):
        """Test that property access produces equivalent results."""
        data, times = sample_data
        
        base_ts = baseTs(data, times, freq=10.0)
        ts_data = TimeSeriesData(data, index=times, freq=10.0)
        
        # Test length and duration
        assert base_ts.len() == ts_data.len()
        assert abs(base_ts.duration() - ts_data.duration()) < 1e-10
        assert abs(base_ts.freq - ts_data.freq) < 1e-10
    
    def test_indexing_equivalence(self, sample_data):
        """Test that indexing operations work equivalently."""
        data, times = sample_data
        
        base_ts = baseTs(data, times)
        ts_data = TimeSeriesData(data, index=times)
        
        # Test array access
        np.testing.assert_array_equal(base_ts.data, ts_data.values)
        np.testing.assert_array_equal(base_ts.times, ts_data.index.values)
        
        # Test individual element access
        assert base_ts.data[0] == ts_data.values[0]
        assert base_ts.data[-1] == ts_data.values[-1]
        assert base_ts.times[0] == ts_data.index.values[0]
        assert base_ts.times[-1] == ts_data.index.values[-1]


class TestErrorHandling:
    """Test error handling in migration components."""
    
    def test_invalid_conversion_inputs(self):
        """Test error handling for invalid conversion inputs."""
        with pytest.raises(ValueError):
            convert_to_series("invalid_input")
        
        with pytest.raises(ValueError):
            convert_to_series(np.array([1, 2, 3]))  # Missing times
    
    def test_invalid_backend_setting(self):
        """Test error handling for invalid backend settings."""
        with pytest.raises(ValueError):
            BackendManager.set_default_backend('invalid_backend')
    
    def test_empty_data_handling(self):
        """Test handling of empty data."""
        empty_data = np.array([])
        empty_times = np.array([])
        
        # Should handle empty data gracefully
        ts_data = TimeSeriesData(empty_data, index=empty_times)
        assert len(ts_data) == 0
        assert ts_data.duration() == 0.0


@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Performance benchmarks for migration components."""
    
    @pytest.fixture
    def large_dataset(self):
        """Generate large dataset for performance testing."""
        n_points = 10000
        times = np.linspace(0, 100, n_points)
        data = np.random.randn(n_points)
        return data, times
    
    def test_creation_speed(self, large_dataset, benchmark):
        """Benchmark TimeSeriesData creation speed."""
        data, times = large_dataset
        
        def create_timeseries():
            return TimeSeriesData(data, index=times, freq=100.0)
        
        result = benchmark(create_timeseries)
        assert len(result) == len(data)
    
    def test_conversion_speed(self, large_dataset, benchmark):
        """Benchmark conversion between backends."""
        data, times = large_dataset
        base_ts = baseTs(data, times, freq=100.0)
        
        def convert_and_back():
            ts_data = convert_to_series(base_ts)
            return convert_to_basetseries(ts_data)
        
        result = benchmark(convert_and_back)
        assert len(result.data) == len(data)
    
    def test_copy_speed(self, large_dataset, benchmark):
        """Benchmark copy operations."""
        data, times = large_dataset
        ts_data = TimeSeriesData(data, index=times, freq=100.0)
        
        def copy_timeseries():
            return ts_data.copy()
        
        result = benchmark(copy_timeseries)
        assert len(result) == len(data)