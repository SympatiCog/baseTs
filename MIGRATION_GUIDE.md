# baseTs Migration Guide: NumPy to Pandas Series Backend

## Overview

baseTs now supports a dual backend architecture, allowing you to choose between the traditional NumPy arrays or the new Pandas Series backend. The Pandas Series backend provides enhanced time-series capabilities while maintaining 100% backward compatibility.

## Quick Start

### Using the New Series Backend

```python
from baseTs import baseTs
import numpy as np
import pandas as pd

# Create with Series backend
data = np.random.randn(1000)
times = pd.date_range('2023-01-01', periods=1000, freq='H')
ts = baseTs(data=data, times=times, backend='series')

# Enhanced time-series operations
monthly_avg = ts.rolling_mean(window=24*30)  # 30-day rolling average
recent_data = ts.time_slice(start='2023-01-15', end='2023-01-20')
stats = ts.get_statistics()
```

### Backward Compatibility

```python
# Existing code continues to work unchanged
ts_numpy = baseTs(data=data, times=times)  # Uses NumPy backend (default)
filtered = ts_numpy.lowpass_filter(cutoff=0.3)
normalized = filtered.zscale()
```

## Backend Comparison

| Feature | NumPy Backend | Series Backend | Notes |
|---------|---------------|----------------|-------|
| **Performance** | Faster for pure numerical ops | Competitive, optimized for time-series | <5x overhead typical |
| **Memory Usage** | Lower baseline | Slightly higher (metadata) | ~10-20% increase |
| **Time Indexing** | Numeric arrays only | Native datetime support | Pandas datetime objects |
| **Rolling Operations** | Manual implementation | Built-in optimized methods | `rolling_mean()`, etc. |
| **Time Slicing** | Index-based only | Date-aware slicing | `time_slice()` method |
| **Metadata** | Basic | Rich metadata preservation | History, filtering state |
| **Interoperability** | NumPy ecosystem | Pandas/NumPy ecosystem | Broader data science tools |

## Migration Strategies

### Strategy 1: Gradual Migration (Recommended)

Start by testing the Series backend on non-critical workflows:

```python
# Test with new backend
ts_series = baseTs(data=data, times=times, backend='series')
ts_numpy = baseTs(data=data, times=times, backend='numpy')

# Verify identical results
filtered_series = ts_series.lowpass_filter(cutoff=0.3)
filtered_numpy = ts_numpy.lowpass_filter(cutoff=0.3)

np.testing.assert_allclose(filtered_series.data, filtered_numpy.data)
```

### Strategy 2: Feature-Driven Migration

Migrate workflows that benefit from new features:

```python
# Time-series analysis workflows
if isinstance(times, pd.DatetimeIndex):
    ts = baseTs(data=data, times=times, backend='series')
    # Use enhanced time-series features
    daily_avg = ts.rolling_mean(window=24)
    weekend_data = ts.time_slice(start='2023-01-07', end='2023-01-08')
else:
    ts = baseTs(data=data, times=times, backend='numpy')
    # Standard numerical processing
```

### Strategy 3: Environment-Based Selection

Use environment variables for deployment control:

```python
import os

# Set via environment: export BASETS_DEFAULT_BACKEND=series
default_backend = os.getenv('BASETS_DEFAULT_BACKEND', 'numpy')
ts = baseTs(data=data, times=times, backend=default_backend)
```

## New Features with Series Backend

### 1. Rolling Statistics

```python
ts = baseTs(data=data, times=times, backend='series')

# Rolling operations with time-aware windows
hourly_mean = ts.rolling_mean(window=24)  # 24-hour rolling mean
daily_std = ts.rolling_std(window=24*7)   # Weekly rolling std
```

### 2. Time-Based Slicing

```python
# Date-aware slicing
ts = baseTs(data=data, times=pd.date_range('2023-01-01', periods=365, freq='D'), 
            backend='series')

# Extract specific time periods
january = ts.time_slice(start='2023-01-01', end='2023-01-31')
weekdays = ts.time_slice(start='2023-01-02', end='2023-01-06')  # Mon-Fri
```

### 3. Enhanced Statistics

```python
stats = ts.get_statistics()
print(f"Mean: {stats['mean']:.3f}")
print(f"Std: {stats['std']:.3f}")
print(f"Skewness: {stats['skew']:.3f}")
print(f"Kurtosis: {stats['kurtosis']:.3f}")
```

### 4. Metadata Preservation

```python
ts = baseTs(data=data, times=times, backend='series')
filtered = ts.lowpass_filter(cutoff=0.3)

# Access processing history
print(f"Filter applied: {filtered.is_filtered}")
print(f"Last operation: {filtered.last_process}")
print(f"Processing history: {filtered.history}")
```

## Performance Considerations

### When to Use Series Backend

✅ **Recommended for:**
- Time-series analysis with datetime indexing
- Rolling window operations
- Complex time-based slicing
- Integration with pandas workflows
- Rich metadata requirements

### When to Use NumPy Backend

✅ **Recommended for:**
- Pure numerical signal processing
- Memory-constrained environments
- High-frequency operations (>1000 Hz)
- Legacy codebases with tight performance requirements

### Performance Optimization Tips

```python
# For large datasets, consider chunking
def process_large_timeseries(data, times, chunk_size=10000):
    results = []
    for i in range(0, len(data), chunk_size):
        chunk_data = data[i:i+chunk_size]
        chunk_times = times[i:i+chunk_size]
        
        ts = baseTs(data=chunk_data, times=chunk_times, backend='series')
        processed = ts.lowpass_filter(cutoff=0.3)
        results.append(processed)
    
    return results

# Use appropriate data types
data = np.array(data, dtype=np.float32)  # Use float32 if precision allows
```

## Common Migration Issues

### Issue 1: Time Index Compatibility

```python
# ❌ Problem: Mixed time formats
times = [0, 1.5, 'invalid', 3]  # Invalid mix

# ✅ Solution: Consistent time format
times = pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03'])
# or
times = np.array([0, 1.5, 2.0, 3.0])
```

### Issue 2: Memory Usage

```python
# ❌ Problem: Unexpected memory usage
ts = baseTs(data=large_array, times=large_times, backend='series')

# ✅ Solution: Monitor and optimize
import psutil
memory_before = psutil.Process().memory_info().rss / 1024**2
ts = baseTs(data=data, times=times, backend='series')
memory_after = psutil.Process().memory_info().rss / 1024**2
print(f"Memory usage: {memory_after - memory_before:.1f} MB")
```

### Issue 3: Performance Regression

```python
# ❌ Problem: Slower than expected
import time

start = time.time()
result = ts.lowpass_filter(cutoff=0.3)
duration = time.time() - start

# ✅ Solution: Profile and compare backends
def benchmark_backends(data, times, operation):
    # NumPy backend
    ts_numpy = baseTs(data=data, times=times, backend='numpy')
    start = time.time()
    result_numpy = operation(ts_numpy)
    numpy_time = time.time() - start
    
    # Series backend
    ts_series = baseTs(data=data, times=times, backend='series')
    start = time.time()
    result_series = operation(ts_series)
    series_time = time.time() - start
    
    print(f"NumPy: {numpy_time:.4f}s, Series: {series_time:.4f}s")
    print(f"Ratio: {series_time/numpy_time:.2f}x")
    
    return result_numpy, result_series
```

## Testing Your Migration

### Validation Script

```python
def validate_migration(data, times):
    """Validate that both backends produce identical results."""
    
    # Create both backends
    ts_numpy = baseTs(data=data, times=times, backend='numpy')
    ts_series = baseTs(data=data, times=times, backend='series')
    
    # Test core operations
    operations = [
        lambda ts: ts.lowpass_filter(cutoff=0.3),
        lambda ts: ts.zscale(),
        lambda ts: ts.normalize_range(),
        lambda ts: ts.apply_function(np.sqrt)
    ]
    
    for i, op in enumerate(operations):
        result_numpy = op(ts_numpy)
        result_series = op(ts_series)
        
        try:
            np.testing.assert_allclose(result_numpy.data, result_series.data, 
                                     rtol=1e-10, atol=1e-12)
            print(f"✅ Operation {i+1}: Results identical")
        except AssertionError as e:
            print(f"❌ Operation {i+1}: Results differ - {e}")
            return False
    
    return True

# Run validation
if validate_migration(your_data, your_times):
    print("✅ Migration validation passed!")
else:
    print("❌ Migration validation failed!")
```

### Automated Testing

```python
# Add to your test suite
def test_backend_compatibility():
    """Ensure your workflows work with both backends."""
    
    data = np.random.randn(1000)
    times = np.arange(1000)
    
    for backend in ['numpy', 'series']:
        ts = baseTs(data=data, times=times, backend=backend)
        
        # Test your typical workflow
        filtered = ts.lowpass_filter(cutoff=0.3)
        normalized = filtered.zscale()
        
        assert len(normalized) == 1000
        assert abs(np.mean(normalized.data)) < 0.01
```

## Best Practices

### 1. Explicit Backend Selection

```python
# ✅ Be explicit about backend choice
ts = baseTs(data=data, times=times, backend='series')  # Clear intent

# ❌ Avoid relying on defaults
ts = baseTs(data=data, times=times)  # Unclear which backend
```

### 2. Consistent Time Formats

```python
# ✅ Use consistent datetime objects
times = pd.date_range('2023-01-01', periods=1000, freq='H')

# ✅ Or consistent numeric arrays
times = np.linspace(0, 100, 1000)
```

### 3. Performance Monitoring

```python
# ✅ Monitor critical performance metrics
def monitor_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        print(f"Duration: {end_time - start_time:.4f}s")
        print(f"Memory: {(end_memory - start_memory)/1024**2:.1f}MB")
        
        return result
    return wrapper

@monitor_performance
def process_timeseries(data, times):
    ts = baseTs(data=data, times=times, backend='series')
    return ts.lowpass_filter(cutoff=0.3).zscale()
```

## Getting Help

### Troubleshooting Checklist

1. **Verify pandas installation**: `pip install pandas>=1.3.0`
2. **Check data types**: Ensure consistent numeric/datetime types
3. **Test with small datasets**: Isolate performance issues
4. **Compare backends**: Use validation script above
5. **Monitor resources**: Check memory and CPU usage

### Support Resources

- **GitHub Issues**: Report bugs or compatibility issues
- **Performance Issues**: Include benchmark results and data characteristics
- **Feature Requests**: Suggest improvements to Series backend

## Future Roadmap

### Version 2.0 (Planned)
- Series backend becomes default
- Additional pandas integration features
- Enhanced time-series analysis methods
- Improved performance optimizations

### Migration Timeline
- **Current**: Optional Series backend (opt-in)
- **v1.5**: Series backend recommended for new projects
- **v2.0**: Series backend default, NumPy backend deprecated
- **v3.0**: NumPy backend removed (breaking change)

This gives you 1-2 years to migrate existing codebases gradually.