"""Integration tests for real-world time series workflows.

Tests complete end-to-end workflows that users typically perform
with baseTs objects, ensuring both backends work seamlessly.
"""

import pytest
import numpy as np
import pandas as pd
from baseTs import baseTs


class TestRealWorldWorkflows:
    """Test realistic time series analysis workflows."""
    
    def test_signal_processing_workflow(self):
        """Test complete signal processing workflow."""
        # Generate noisy signal
        t = np.linspace(0, 10, 1000)
        signal = np.sin(2 * np.pi * t) + 0.1 * np.random.randn(1000)
        
        # Test with both backends
        for backend in ['numpy', 'series']:
            ts = baseTs(data=signal, times=t, backend=backend)
            
            # Typical workflow: filter, normalize, extract features
            filtered = ts.lowpass_filter(cutoff=0.1)
            normalized = filtered.zscale()
            windowed_stats = normalized.rolling_mean(window=50) if backend == 'series' else normalized
            
            # Verify workflow preserves data integrity
            assert len(filtered) == len(ts)
            assert len(normalized) == len(ts)
            assert abs(np.mean(normalized.data)) < 0.1  # Should be near zero after zscaling
            assert np.std(normalized.data) - 1.0 < 0.1  # Should be near 1 after zscaling
    
    def test_outlier_detection_workflow(self):
        """Test outlier detection and removal workflow."""
        # Generate data with outliers
        t = np.arange(100)
        data = np.random.randn(100)
        data[25] = 10  # Add outlier
        data[75] = -10  # Add outlier
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data=data, times=t, backend=backend)
            
            # Workflow: detect outliers, remove them, interpolate
            outliers = ts.outlier_indices(method='iqr')
            cleaned = ts.remove_outliers()
            interpolated = cleaned.interpolate() if hasattr(cleaned, 'interpolate') else cleaned
            
            # Verify outliers were detected
            assert len(outliers) >= 2  # Should detect the two outliers we added
            assert 25 in outliers or 75 in outliers  # At least one should be detected
            
            # Verify data length consistency
            assert len(interpolated) <= len(ts)  # Should be same or shorter after outlier removal
    
    def test_time_series_analysis_workflow(self):
        """Test time-based analysis workflow."""
        # Create time-indexed data
        dates = pd.date_range('2023-01-01', periods=365, freq='D')
        seasonal_data = np.sin(2 * np.pi * np.arange(365) / 365.25) + np.random.randn(365) * 0.1
        
        for backend in ['numpy', 'series']:
            if backend == 'series':
                ts = baseTs(data=seasonal_data, times=dates, backend=backend)
                
                # Time-based workflow
                monthly_mean = ts.rolling_mean(window=30)
                quarterly_slice = ts.time_slice(start='2023-04-01', end='2023-06-30')
                stats = ts.get_statistics()
                
                # Verify time-based operations
                assert len(monthly_mean) == len(ts)
                assert len(quarterly_slice) < len(ts)  # Should be a subset
                assert 'mean' in stats and 'std' in stats
            else:
                # Numpy backend with numeric times
                ts = baseTs(data=seasonal_data, times=np.arange(365), backend=backend)
                filtered = ts.lowpass_filter(cutoff=0.1)
                assert len(filtered) == len(ts)
    
    def test_data_transformation_workflow(self):
        """Test complex data transformation workflow."""
        # Multi-step transformation workflow
        data = np.random.exponential(2, 500)  # Skewed data
        times = np.linspace(0, 50, 500)
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data=data, times=times, backend=backend)
            
            # Complex workflow: log transform, normalize, filter, extract features
            log_transformed = ts.apply_function(np.log)
            normalized = log_transformed.zscale()
            filtered = normalized.lowpass_filter(cutoff=0.2)
            
            # Verify transformations
            assert len(filtered) == len(ts)
            assert not np.any(np.isnan(log_transformed.data))  # No NaN values
            assert abs(np.mean(normalized.data)) < 0.2  # Near zero mean
            
            # Test method chaining if available
            if backend == 'series':
                chained = ts.apply_function(np.log).zscale().lowpass_filter(cutoff=0.2)
                assert len(chained) == len(ts)
    
    def test_batch_processing_workflow(self):
        """Test batch processing multiple time series."""
        # Simulate batch processing workflow
        time_series_list = []
        
        for i in range(5):
            data = np.random.randn(100) + i  # Different means
            times = np.arange(100)
            ts = baseTs(data=data, times=times, backend='numpy')
            time_series_list.append(ts)
        
        # Batch processing: apply same operations to all
        processed_series = []
        for ts in time_series_list:
            processed = ts.zscale().lowpass_filter(cutoff=0.3)
            processed_series.append(processed)
        
        # Verify batch processing consistency
        assert len(processed_series) == 5
        for ts in processed_series:
            assert len(ts) == 100
            assert abs(np.mean(ts.data)) < 0.2  # All should be normalized
    
    def test_error_handling_workflow(self):
        """Test error handling in realistic scenarios."""
        for backend in ['numpy', 'series']:
            # Test with problematic data
            data_with_nan = np.array([1, 2, np.nan, 4, 5])
            times = np.arange(5)
            
            # Should handle NaN values gracefully
            ts = baseTs(data=data_with_nan, times=times, backend=backend)
            
            # Operations should either work or fail gracefully
            try:
                filtered = ts.lowpass_filter(cutoff=0.5)
                # If it succeeds, verify basic properties
                assert len(filtered) == len(ts)
            except (ValueError, RuntimeError):
                # If it fails, that's acceptable for NaN data
                pass
            
            # Test with mismatched data/times lengths
            with pytest.raises((ValueError, AssertionError)):
                baseTs(data=[1, 2, 3], times=[1, 2], backend=backend)
    
    def test_backend_switching_workflow(self):
        """Test switching between backends during workflow."""
        data = np.random.randn(100)
        times = np.arange(100)
        
        # Start with numpy backend
        ts_numpy = baseTs(data=data, times=times, backend='numpy')
        filtered_numpy = ts_numpy.lowpass_filter(cutoff=0.3)
        
        # Switch to series backend with same data
        ts_series = baseTs(data=data, times=times, backend='series')
        filtered_series = ts_series.lowpass_filter(cutoff=0.3)
        
        # Results should be nearly identical
        np.testing.assert_allclose(filtered_numpy.data, filtered_series.data, rtol=1e-10)
        np.testing.assert_allclose(filtered_numpy.times, filtered_series.times, rtol=1e-10)
    
    def test_memory_intensive_workflow(self):
        """Test workflow with larger datasets."""
        # Test with moderately large data (10k points)
        large_data = np.random.randn(10000)
        large_times = np.linspace(0, 100, 10000)
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data=large_data, times=large_times, backend=backend)
            
            # Memory-intensive operations
            filtered = ts.lowpass_filter(cutoff=0.1)
            normalized = filtered.zscale()
            
            # Verify operations complete successfully
            assert len(filtered) == 10000
            assert len(normalized) == 10000
            assert abs(np.mean(normalized.data)) < 0.01
    
    def test_scientific_workflow(self):
        """Test scientific analysis workflow."""
        # Simulate experimental data
        t = np.linspace(0, 10, 1000)
        # Signal with trend, seasonality, and noise
        trend = 0.1 * t
        seasonal = 2 * np.sin(2 * np.pi * t)
        noise = 0.5 * np.random.randn(1000)
        signal = trend + seasonal + noise
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data=signal, times=t, backend=backend)
            
            # Scientific workflow: detrend, filter, analyze
            detrended = ts.detrend() if hasattr(ts, 'detrend') else ts
            filtered = detrended.lowpass_filter(cutoff=0.5)
            normalized = filtered.zscale()
            
            # Statistical analysis
            mean_val = np.mean(normalized.data)
            std_val = np.std(normalized.data)
            
            # Verify scientific analysis results
            assert len(normalized) == len(ts)
            assert abs(mean_val) < 0.1  # Should be near zero after normalization
            assert abs(std_val - 1.0) < 0.1  # Should be near 1 after zscaling


class TestWorkflowCompatibility:
    """Test compatibility across different workflow scenarios."""
    
    def test_mixed_operation_workflow(self):
        """Test workflows mixing different types of operations."""
        data = np.random.randn(200)
        times = np.arange(200)
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data=data, times=times, backend=backend)
            
            # Mix mathematical, filtering, and transformation operations
            result = ts.zscale()  # Mathematical
            result = result.lowpass_filter(cutoff=0.3)  # Filtering
            result = result.apply_function(lambda x: x ** 2)  # Transformation
            
            # Verify mixed operations work
            assert len(result) == len(ts)
            assert np.all(result.data >= 0)  # Should be positive after squaring
    
    def test_conditional_workflow(self):
        """Test workflows with conditional logic."""
        data = np.random.randn(100)
        times = np.arange(100)
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data=data, times=times, backend=backend)
            
            # Conditional workflow based on data properties
            if np.std(ts.data) > 0.5:
                result = ts.zscale()
            else:
                result = ts.normalize_range()
            
            if backend == 'series' and hasattr(ts, 'rolling_mean'):
                result = result.rolling_mean(window=10)
            
            # Verify conditional logic works
            assert len(result) == len(ts)
    
    def test_iterative_workflow(self):
        """Test iterative processing workflows."""
        data = np.random.randn(100)
        times = np.arange(100)
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data=data, times=times, backend=backend)
            
            # Iterative refinement workflow
            current = ts
            for i in range(3):
                current = current.lowpass_filter(cutoff=0.5 - i * 0.1)
                current = current.zscale()
            
            # Verify iterative processing
            assert len(current) == len(ts)
            assert abs(np.mean(current.data)) < 0.2  # Should be normalized


if __name__ == '__main__':
    pytest.main([__file__, '-v'])