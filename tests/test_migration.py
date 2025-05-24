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


class TestDualBackendBaseTs:
    """Test dual backend functionality in baseTs."""
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample time series data."""
        n_points = 50
        times = np.linspace(0, 5, n_points)
        data = np.sin(2 * np.pi * times) + 0.1 * np.random.randn(n_points)
        return data, times
    
    def test_backend_selection(self, sample_data):
        """Test backend selection mechanisms."""
        data, times = sample_data
        
        # Test default backend
        ts_default = baseTs(data, times)
        assert ts_default.backend == 'numpy'  # Current default
        
        # Test explicit numpy
        ts_numpy = baseTs(data, times, backend='numpy')
        assert ts_numpy.backend == 'numpy'
        assert ts_numpy.is_numpy_backend
        assert not ts_numpy.is_series_backend
        
        # Test explicit series
        ts_series = baseTs(data, times, backend='series')
        assert ts_series.backend == 'series'
        assert ts_series.is_series_backend
        assert not ts_series.is_numpy_backend
        
        # Test use_series parameter
        ts_use_series = baseTs(data, times, use_series=True)
        assert ts_use_series.backend == 'series'
    
    def test_data_property_compatibility(self, sample_data):
        """Test that data and times properties work identically."""
        data, times = sample_data
        
        ts_numpy = baseTs(data, times, freq=10.0, backend='numpy')
        ts_series = baseTs(data, times, freq=10.0, backend='series')
        
        # Test data access
        np.testing.assert_array_equal(ts_numpy.data, ts_series.data)
        np.testing.assert_array_equal(ts_numpy.times, ts_series.times)
        
        # Test data modification
        new_data = data * 2
        ts_numpy.data = new_data
        ts_series.data = new_data
        
        np.testing.assert_array_equal(ts_numpy.data, new_data)
        np.testing.assert_array_equal(ts_series.data, new_data)
    
    def test_metadata_property_compatibility(self, sample_data):
        """Test that metadata properties work identically."""
        data, times = sample_data
        
        ts_numpy = baseTs(data, times, freq=10.0, signal_name="test", backend='numpy')
        ts_series = baseTs(data, times, freq=10.0, signal_name="test", backend='series')
        
        # Test basic properties
        assert ts_numpy.freq == ts_series.freq
        assert ts_numpy.signal_name == ts_series.signal_name
        assert ts_numpy.len() == ts_series.len()
        assert abs(ts_numpy.duration() - ts_series.duration()) < 1e-10
        
        # Test property modification
        ts_numpy.signal_name = "new_name"
        ts_series.signal_name = "new_name"
        
        assert ts_numpy.signal_name == "NEW_NAME"
        assert ts_series.signal_name == "NEW_NAME"
    
    def test_method_equivalence(self, sample_data):
        """Test that basic methods produce equivalent results."""
        data, times = sample_data
        
        ts_numpy = baseTs(data, times, freq=10.0, backend='numpy')
        ts_series = baseTs(data, times, freq=10.0, backend='series')
        
        # Test basic methods
        assert ts_numpy.len() == ts_series.len()
        assert abs(ts_numpy.duration() - ts_series.duration()) < 1e-10
        
        # Test copy
        copy_numpy = ts_numpy.copy()
        copy_series = ts_series.copy()
        
        assert copy_numpy.backend == 'numpy'
        assert copy_series.backend == 'series'
        np.testing.assert_array_equal(copy_numpy.data, copy_series.data)
    
    def test_backend_manager_integration(self, sample_data):
        """Test BackendManager integration with baseTs."""
        data, times = sample_data
        
        # Save original default
        original_default = BackendManager.get_default_backend()
        
        try:
            # Test with numpy default
            BackendManager.set_default_backend('numpy')
            ts = baseTs(data, times)
            assert ts.backend == 'numpy'
            
            # Test with series default
            BackendManager.set_default_backend('series')
            ts = baseTs(data, times)
            assert ts.backend == 'series'
            
            # Test override
            ts_override = baseTs(data, times, use_series=False)
            assert ts_override.backend == 'numpy'
            
        finally:
            # Restore original default
            BackendManager.set_default_backend(original_default)


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
    
    def test_invalid_basetseries_backend(self):
        """Test error handling for invalid backend in baseTs."""
        data = np.array([1, 2, 3])
        times = np.array([0.0, 0.1, 0.2])
        
        with pytest.raises(ValueError):
            baseTs(data, times, backend='invalid')
    
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