"""Stress testing and edge case validation for baseTs migration.

Tests extreme conditions, boundary cases, and stress scenarios
to ensure robustness across both numpy and Series backends.
"""

import pytest
import numpy as np
import pandas as pd
import gc
import psutil
import os
import warnings
from baseTs import baseTs


class TestStressCases:
    """Stress testing with extreme conditions."""
    
    def test_large_dataset_stress(self):
        """Test with large datasets to stress memory and performance."""
        # Test with 100k points (reasonable for stress test)
        size = 100000
        data = np.random.randn(size)
        times = np.linspace(0, 1000, size)
        
        for backend in ['numpy', 'series']:
            # Monitor memory usage
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            ts = baseTs(data=data, times=times, backend=backend)
            
            # Perform operations that should scale well
            filtered = ts.lowpass_filter(cutoff=0.1)
            normalized = filtered.zscale()
            
            # Verify operations completed
            assert len(normalized) == size
            assert abs(np.mean(normalized.data)) < 0.01
            
            # Clean up
            del ts, filtered, normalized
            gc.collect()
            
            # Check memory didn't grow excessively (allow 500MB growth)
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_growth = final_memory - initial_memory
            assert memory_growth < 500, f"Memory grew by {memory_growth:.1f}MB"
    
    def test_repeated_operations_stress(self):
        """Test repeated operations for memory leaks and performance degradation."""
        data = np.random.randn(1000)
        times = np.arange(1000)
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data=data, times=times, backend=backend)
            
            # Perform many repeated operations
            for i in range(100):
                result = ts.lowpass_filter(cutoff=0.3)
                result = result.zscale()
                
                # Verify consistency
                assert len(result) == 1000
                if i % 20 == 0:  # Check periodically
                    assert abs(np.mean(result.data)) < 0.1
    
    def test_method_chaining_stress(self):
        """Test extensive method chaining."""
        data = np.random.randn(500)
        times = np.arange(500)
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data=data, times=times, backend=backend)
            
            # Long chain of operations
            result = ts
            operations = [
                lambda x: x.zscale(),
                lambda x: x.lowpass_filter(cutoff=0.5),
                lambda x: x.normalize_range(),
                lambda x: x.apply_function(lambda y: np.sqrt(np.abs(y))),
                lambda x: x.zscale()
            ]
            
            # Chain operations multiple times
            for _ in range(10):
                for op in operations:
                    result = op(result)
            
            # Verify final result is valid
            assert len(result) == 500
            assert not np.any(np.isnan(result.data))
            assert not np.any(np.isinf(result.data))
    
    def test_concurrent_object_stress(self):
        """Test creating many baseTs objects simultaneously."""
        objects = []
        
        for backend in ['numpy', 'series']:
            # Create many objects
            for i in range(100):
                data = np.random.randn(100) + i * 0.1  # Slightly different each time
                times = np.arange(100)
                ts = baseTs(data=data, times=times, backend=backend)
                objects.append(ts)
            
            # Verify all objects are valid
            for i, ts in enumerate(objects):
                assert len(ts) == 100
                assert np.mean(ts.data) != 0 or i == 0  # Should have different means
            
            # Clean up
            objects.clear()
            gc.collect()
    
    def test_extreme_filter_parameters(self):
        """Test filtering with extreme parameters."""
        data = np.sin(np.linspace(0, 100, 1000)) + 0.1 * np.random.randn(1000)
        times = np.linspace(0, 100, 1000)
        
        extreme_cutoffs = [0.001, 0.999, 0.5]  # Very low, very high, normal
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data=data, times=times, backend=backend)
            
            for cutoff in extreme_cutoffs:
                try:
                    filtered = ts.lowpass_filter(cutoff=cutoff)
                    assert len(filtered) == len(ts)
                    assert not np.any(np.isnan(filtered.data))
                except (ValueError, RuntimeError) as e:
                    # Some extreme parameters might fail, which is acceptable
                    assert "cutoff" in str(e).lower() or "filter" in str(e).lower()


class TestEdgeCases:
    """Test boundary conditions and edge cases."""
    
    def test_minimal_data_sizes(self):
        """Test with minimal data sizes."""
        # Test with very small datasets
        sizes = [1, 2, 3, 5]
        
        for size in sizes:
            data = np.random.randn(size)
            times = np.arange(size)
            
            for backend in ['numpy', 'series']:
                ts = baseTs(data=data, times=times, backend=backend)
                assert ts.len() == size
                
                # Test operations that should work with small data
                if size >= 3:  # Some operations might need minimum size
                    try:
                        normalized = ts.normalize_range()
                        assert len(normalized) == size
                    except ValueError:
                        # Some operations might fail with tiny datasets
                        pass
    
    def test_uniform_data(self):
        """Test with uniform (constant) data."""
        constant_values = [0.0, 1.0, -1.0, 1e6, 1e-6]
        
        for value in constant_values:
            data = np.full(100, value)
            times = np.arange(100)
            
            for backend in ['numpy', 'series']:
                ts = baseTs(data=data, times=times, backend=backend)
                
                # Test operations with constant data
                try:
                    normalized = ts.normalize_range()
                    # Normalized constant data might be all zeros or all ones
                    assert len(normalized) == 100
                    unique_vals = np.unique(normalized.data)
                    assert len(unique_vals) <= 2  # Should be very few unique values
                except (ValueError, ZeroDivisionError):
                    # Some normalizations might fail with constant data
                    pass
                
                # zscale with constant data should fail or return zeros
                try:
                    zscaled = ts.zscale()
                    # If it succeeds, should be zeros (std=0)
                    assert np.all(np.abs(zscaled.data) < 1e-10)
                except (ValueError, ZeroDivisionError):
                    # Expected for constant data (std=0)
                    pass
    
    def test_extreme_values(self):
        """Test with extreme numerical values."""
        extreme_datasets = [
            np.array([1e-15, 1e-14, 1e-13]),  # Very small values
            np.array([1e15, 1e14, 1e13]),     # Very large values
            np.array([-1e10, 0, 1e10]),       # Large range
            np.array([np.finfo(float).min, 0, np.finfo(float).max])  # Extreme range
        ]
        
        for data in extreme_datasets:
            times = np.arange(len(data))
            
            for backend in ['numpy', 'series']:
                try:
                    ts = baseTs(data=data, times=times, backend=backend)
                    
                    # Test basic operations
                    assert ts.len() == len(data)
                    
                    # Test normalize_range (should work with extreme values)
                    try:
                        normalized = ts.normalize_range()
                        assert len(normalized) == len(data)
                        assert np.min(normalized.data) >= -1e-10  # Should be >= 0
                        assert np.max(normalized.data) <= 1 + 1e-10  # Should be <= 1
                    except (ValueError, OverflowError):
                        # Might fail with extreme values
                        pass
                        
                except (ValueError, OverflowError):
                    # Creation might fail with extreme values
                    pass
    
    def test_irregular_time_spacing(self):
        """Test with irregularly spaced time points."""
        # Create irregular time spacing
        times = np.array([0, 0.1, 1, 1.5, 10, 10.1, 100])
        data = np.random.randn(len(times))
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data=data, times=times, backend=backend)
            
            # Basic operations should still work
            assert ts.len() == len(times)
            
            # Some operations might behave differently with irregular spacing
            filtered = ts.lowpass_filter(cutoff=0.3)
            assert len(filtered) == len(times)
    
    def test_duplicate_time_points(self):
        """Test with duplicate time points."""
        times = np.array([0, 1, 1, 2, 2, 2, 3])  # Duplicates
        data = np.random.randn(len(times))
        
        for backend in ['numpy', 'series']:
            # This might fail or succeed depending on implementation
            try:
                ts = baseTs(data=data, times=times, backend=backend)
                assert ts.len() == len(times)
                
                # Basic operations
                normalized = ts.normalize_range()
                assert len(normalized) == len(times)
            except ValueError:
                # Duplicate times might be rejected
                pass
    
    def test_non_monotonic_times(self):
        """Test with non-monotonic time points."""
        times = np.array([0, 2, 1, 4, 3])  # Non-monotonic
        data = np.random.randn(len(times))
        
        for backend in ['numpy', 'series']:
            # This might fail or succeed depending on implementation
            try:
                ts = baseTs(data=data, times=times, backend=backend)
                assert ts.len() == len(times)
            except ValueError:
                # Non-monotonic times might be rejected
                pass
    
    def test_special_float_values(self):
        """Test with special float values."""
        special_values = [
            [1.0, np.inf, 3.0],
            [1.0, -np.inf, 3.0],
            [1.0, np.nan, 3.0],
            [np.inf, -np.inf, 0.0],
        ]
        
        for data in special_values:
            times = np.arange(len(data))
            
            for backend in ['numpy', 'series']:
                # Should either handle gracefully or raise appropriate error
                try:
                    ts = baseTs(data=data, times=times, backend=backend)
                    
                    # If creation succeeds, basic properties should work
                    assert ts.len() == len(data)
                    
                    # Operations might fail with special values
                    try:
                        filtered = ts.lowpass_filter(cutoff=0.3)
                        # Check that no operation introduced additional special values
                        if not np.any(np.isnan(data)) and not np.any(np.isinf(data)):
                            assert not np.any(np.isnan(filtered.data))
                    except (ValueError, RuntimeError):
                        # Operations might fail with special values
                        pass
                        
                except (ValueError, TypeError):
                    # Creation might fail with special values - that's acceptable
                    pass
    
    def test_data_type_edge_cases(self):
        """Test with different data types."""
        data_variants = [
            np.array([1, 2, 3], dtype=np.int32),
            np.array([1, 2, 3], dtype=np.int64),
            np.array([1.0, 2.0, 3.0], dtype=np.float32),
            np.array([1.0, 2.0, 3.0], dtype=np.float64),
            [1, 2, 3],  # Python list
            (1, 2, 3),  # Python tuple
        ]
        
        for data in data_variants:
            times = np.arange(len(data))
            
            for backend in ['numpy', 'series']:
                ts = baseTs(data=data, times=times, backend=backend)
                
                # Should work regardless of input type
                assert ts.len() == len(data)
                
                # Operations should work
                normalized = ts.normalize_range()
                assert len(normalized) == len(data)
    
    def test_memory_pressure_edge_cases(self):
        """Test behavior under memory pressure."""
        # Create several large objects to put pressure on memory
        large_objects = []
        
        try:
            for i in range(10):
                # Create moderately large datasets
                size = 10000
                data = np.random.randn(size)
                times = np.arange(size)
                
                for backend in ['numpy', 'series']:
                    ts = baseTs(data=data, times=times, backend=backend)
                    large_objects.append(ts)
                    
                    # Perform operations
                    filtered = ts.lowpass_filter(cutoff=0.3)
                    large_objects.append(filtered)
            
            # All objects should still be valid
            for obj in large_objects:
                assert obj.len() > 0
                
        finally:
            # Clean up
            large_objects.clear()
            gc.collect()


class TestErrorHandling:
    """Test error handling in edge cases."""
    
    def test_invalid_parameters(self):
        """Test handling of invalid parameters."""
        data = np.random.randn(100)
        times = np.arange(100)
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data=data, times=times, backend=backend)
            
            # Test invalid filter parameters
            with pytest.raises((ValueError, TypeError)):
                ts.lowpass_filter(cutoff=-1)  # Negative cutoff
            
            with pytest.raises((ValueError, TypeError)):
                ts.lowpass_filter(cutoff=2)   # Cutoff > 1
    
    def test_operation_failures(self):
        """Test graceful handling of operation failures."""
        # Data that might cause operations to fail
        problematic_data = [
            np.array([0.0, 0.0, 0.0]),  # All zeros
            np.array([1.0]),            # Single point
            np.array([np.inf, np.inf])  # All infinite
        ]
        
        for data in problematic_data:
            times = np.arange(len(data))
            
            for backend in ['numpy', 'series']:
                try:
                    ts = baseTs(data=data, times=times, backend=backend)
                    
                    # These operations might fail, but should fail gracefully
                    operations = [
                        lambda x: x.zscale(),
                        lambda x: x.normalize_range(),
                        lambda x: x.lowpass_filter(cutoff=0.3)
                    ]
                    
                    for op in operations:
                        try:
                            result = op(ts)
                            # If it succeeds, result should be valid
                            assert result.len() == ts.len()
                        except (ValueError, RuntimeError, ZeroDivisionError):
                            # Graceful failure is acceptable
                            pass
                            
                except (ValueError, TypeError):
                    # Construction failure is acceptable for problematic data
                    pass
    
    def test_resource_cleanup(self):
        """Test proper resource cleanup."""
        # Create and destroy many objects
        for i in range(100):
            data = np.random.randn(1000)
            times = np.arange(1000)
            
            for backend in ['numpy', 'series']:
                ts = baseTs(data=data, times=times, backend=backend)
                filtered = ts.lowpass_filter(cutoff=0.3)
                
                # Objects should be properly cleaned up when they go out of scope
                del ts, filtered
        
        # Force garbage collection
        gc.collect()
        
        # Memory usage should be reasonable
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        assert memory_mb < 1000, f"Memory usage too high: {memory_mb:.1f}MB"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])