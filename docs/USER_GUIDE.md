# baseTs User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Core Concepts](#core-concepts)
3. [Choosing a Backend](#choosing-a-backend)
4. [Basic Operations](#basic-operations)
5. [Advanced Features](#advanced-features)
6. [Time-Series Analysis](#time-series-analysis)
7. [Performance Guidelines](#performance-guidelines)
8. [Examples and Recipes](#examples-and-recipes)

## Getting Started

### Installation

```bash
pip install basets
```

For full Series backend functionality:
```bash
pip install basets[series]  # Includes pandas
```

### Your First baseTs Object

```python
import numpy as np
from baseTs import baseTs

# Create a simple time series
data = np.sin(np.linspace(0, 4*np.pi, 1000))
times = np.linspace(0, 10, 1000)

ts = baseTs(data=data, times=times)
print(f"Time series length: {ts.len()}")
print(f"Data range: {np.min(ts.data):.3f} to {np.max(ts.data):.3f}")
```

## Core Concepts

### baseTs Objects

A baseTs object represents a time series with:
- **Data**: The signal values (y-axis)
- **Times**: The time points (x-axis)
- **Metadata**: Processing history and properties

```python
# Access properties
print(f"Data: {ts.data[:5]}")        # First 5 data points
print(f"Times: {ts.times[:5]}")      # First 5 time points
print(f"Length: {ts.len()}")         # Number of points
```

### Backend Architecture

baseTs supports two backends:

1. **NumPy Backend** (default): Fast numerical processing
2. **Series Backend**: Enhanced time-series capabilities with pandas

```python
# NumPy backend (default)
ts_numpy = baseTs(data=data, times=times, backend='numpy')

# Series backend
ts_series = baseTs(data=data, times=times, backend='series')
```

## Choosing a Backend

### Decision Matrix

| Use Case | Recommended Backend | Reason |
|----------|-------------------|--------|
| Signal processing | NumPy | Faster numerical operations |
| Financial time series | Series | Date/time indexing |
| Scientific data | NumPy | Memory efficiency |
| Business analytics | Series | Pandas integration |
| Real-time processing | NumPy | Lower latency |
| Exploratory analysis | Series | Rich metadata |

### Example Selection Logic

```python
import pandas as pd

def choose_backend(times, data_size, use_case):
    """Helper function to choose appropriate backend."""
    
    # Use Series for datetime indexing
    if isinstance(times, (pd.DatetimeIndex, pd.TimedeltaIndex)):
        return 'series'
    
    # Use NumPy for large datasets requiring speed
    if data_size > 100000 and use_case == 'real_time':
        return 'numpy'
    
    # Use Series for analysis workflows
    if use_case in ['analysis', 'exploration', 'reporting']:
        return 'series'
    
    # Default to NumPy for compatibility
    return 'numpy'

# Usage
backend = choose_backend(times, len(data), 'analysis')
ts = baseTs(data=data, times=times, backend=backend)
```

## Basic Operations

### Filtering

```python
# Low-pass filtering
filtered = ts.lowpass_filter(cutoff=0.3)

# With different parameters
heavily_filtered = ts.lowpass_filter(cutoff=0.1)  # More aggressive
lightly_filtered = ts.lowpass_filter(cutoff=0.8)  # Less aggressive
```

### Normalization

```python
# Z-score normalization (mean=0, std=1)
normalized = ts.zscale()

# Range normalization (min=0, max=1)
range_normalized = ts.normalize_range()

# Custom range normalization
custom_range = ts.normalize_range(new_min=-1, new_max=1)
```

### Function Application

```python
# Apply mathematical functions
squared = ts.apply_function(lambda x: x**2)
sqrt_abs = ts.apply_function(lambda x: np.sqrt(np.abs(x)))
log_transform = ts.apply_function(lambda x: np.log(np.abs(x) + 1e-10))

# Apply with numpy functions
rectified = ts.apply_function(lambda x: np.maximum(x, 0))  # ReLU
```

### Outlier Detection and Removal

```python
# Detect outliers
outlier_indices = ts.outlier_indices(method='iqr', factor=1.5)
print(f"Found {len(outlier_indices)} outliers")

# Remove outliers
cleaned = ts.remove_outliers(method='iqr')
print(f"Removed {ts.len() - cleaned.len()} points")

# Different outlier detection methods
zscore_outliers = ts.outlier_indices(method='zscore', threshold=3)
modified_outliers = ts.outlier_indices(method='modified_zscore', threshold=3.5)
```

## Advanced Features

### Method Chaining

```python
# Chain operations together
processed = (ts
             .lowpass_filter(cutoff=0.3)
             .remove_outliers()
             .zscale()
             .apply_function(np.abs))

# Equivalent to:
step1 = ts.lowpass_filter(cutoff=0.3)
step2 = step1.remove_outliers()
step3 = step2.zscale()
processed = step3.apply_function(np.abs)
```

### Interpolation and Resampling

```python
# Interpolate missing values (if supported)
if hasattr(ts, 'interpolate'):
    interpolated = ts.interpolate(method='linear')

# Resample to different time grid
if hasattr(ts, 'resample'):
    # Upsample to higher frequency
    upsampled = ts.resample(factor=2)
    
    # Downsample to lower frequency
    downsampled = ts.resample(factor=0.5)
```

## Time-Series Analysis (Series Backend)

### Rolling Statistics

```python
# Create time series with datetime index
import pandas as pd

times = pd.date_range('2023-01-01', periods=365*24, freq='H')  # Hourly for 1 year
data = np.sin(2*np.pi*np.arange(len(times))/24) + np.random.randn(len(times))*0.1

ts = baseTs(data=data, times=times, backend='series')

# Rolling operations
daily_mean = ts.rolling_mean(window=24)          # 24-hour rolling mean
weekly_std = ts.rolling_std(window=24*7)         # Weekly rolling std
monthly_max = ts.rolling_max(window=24*30)       # Monthly rolling max
```

### Time-Based Slicing

```python
# Extract specific time periods
january = ts.time_slice(start='2023-01-01', end='2023-01-31')
summer = ts.time_slice(start='2023-06-01', end='2023-08-31')

# Extract specific days
monday = ts.time_slice(start='2023-01-02 00:00', end='2023-01-02 23:59')

# Working hours only
work_hours = ts.time_slice(start='2023-01-01 09:00', end='2023-01-01 17:00')
```

### Statistical Analysis

```python
# Comprehensive statistics
stats = ts.get_statistics()
print(f"""
Statistics Summary:
- Mean: {stats['mean']:.4f}
- Std Dev: {stats['std']:.4f}
- Skewness: {stats['skew']:.4f}
- Kurtosis: {stats['kurtosis']:.4f}
- Min: {stats['min']:.4f}
- Max: {stats['max']:.4f}
""")

# Seasonal decomposition (if available)
if hasattr(ts, 'seasonal_decompose'):
    trend, seasonal, residual = ts.seasonal_decompose(period=24)
```

### Metadata and History

```python
# Check processing history
print(f"Is filtered: {ts.is_filtered}")
print(f"Last process: {ts.last_process}")
print(f"History: {ts.history}")

# Access filter parameters
if hasattr(ts, 'filtered_indices'):
    print(f"Filtered indices: {ts.filtered_indices}")
```

## Performance Guidelines

### Memory Optimization

```python
# For large datasets, monitor memory usage
import psutil

def memory_efficient_processing(large_data, large_times):
    """Process large datasets efficiently."""
    
    # Monitor initial memory
    initial_memory = psutil.Process().memory_info().rss / 1024**2
    
    # Use appropriate data types
    if large_data.dtype == np.float64:
        large_data = large_data.astype(np.float32)  # Reduce memory by half
    
    # Choose backend based on size
    backend = 'numpy' if len(large_data) > 1000000 else 'series'
    
    ts = baseTs(data=large_data, times=large_times, backend=backend)
    
    # Process in chunks if very large
    if len(large_data) > 5000000:
        return process_in_chunks(ts)
    else:
        return ts.lowpass_filter(cutoff=0.3)

def process_in_chunks(ts, chunk_size=100000):
    """Process very large time series in chunks."""
    results = []
    
    for i in range(0, ts.len(), chunk_size):
        end_idx = min(i + chunk_size, ts.len())
        
        # Extract chunk
        chunk_data = ts.data[i:end_idx]
        chunk_times = ts.times[i:end_idx]
        
        # Process chunk
        chunk_ts = baseTs(data=chunk_data, times=chunk_times, backend=ts._backend)
        processed_chunk = chunk_ts.lowpass_filter(cutoff=0.3)
        
        results.append(processed_chunk)
    
    return combine_chunks(results)
```

### Performance Benchmarking

```python
import time

def benchmark_operation(data, times, operation, backends=['numpy', 'series']):
    """Benchmark operation across backends."""
    
    results = {}
    
    for backend in backends:
        ts = baseTs(data=data, times=times, backend=backend)
        
        # Warm up
        operation(ts)
        
        # Benchmark
        start_time = time.perf_counter()
        for _ in range(10):  # Run multiple times
            result = operation(ts)
        end_time = time.perf_counter()
        
        avg_time = (end_time - start_time) / 10
        results[backend] = avg_time
    
    # Print results
    for backend, exec_time in results.items():
        print(f"{backend}: {exec_time:.6f}s")
    
    if len(results) > 1:
        ratio = results['series'] / results['numpy']
        print(f"Series/NumPy ratio: {ratio:.2f}x")
    
    return results

# Example usage
data = np.random.randn(10000)
times = np.arange(10000)

print("Lowpass Filter Benchmark:")
benchmark_operation(data, times, lambda ts: ts.lowpass_filter(cutoff=0.3))

print("\nZ-Scale Benchmark:")
benchmark_operation(data, times, lambda ts: ts.zscale())
```

## Examples and Recipes

### Example 1: Signal Processing Workflow

```python
def process_eeg_signal(raw_data, sampling_rate):
    """Process EEG signal with filtering and artifact removal."""
    
    # Create time axis
    times = np.arange(len(raw_data)) / sampling_rate
    
    # Create baseTs object
    eeg = baseTs(data=raw_data, times=times, backend='numpy')
    
    # Processing pipeline
    # 1. Remove DC offset
    detrended = eeg.apply_function(lambda x: x - np.mean(x))
    
    # 2. Bandpass filter (1-50 Hz for EEG)
    filtered = detrended.lowpass_filter(cutoff=0.4)  # Adjust based on sampling rate
    
    # 3. Remove artifacts (outliers)
    cleaned = filtered.remove_outliers(method='zscore', threshold=4)
    
    # 4. Normalize
    normalized = cleaned.zscale()
    
    return normalized

# Usage
sampling_rate = 250  # Hz
raw_eeg = np.random.randn(10000) + 0.1 * np.sin(np.linspace(0, 100, 10000))
processed_eeg = process_eeg_signal(raw_eeg, sampling_rate)
```

### Example 2: Financial Time Series Analysis

```python
def analyze_stock_prices(prices, dates):
    """Analyze stock price time series."""
    
    # Convert to pandas datetime if needed
    if not isinstance(dates, pd.DatetimeIndex):
        dates = pd.to_datetime(dates)
    
    # Create time series with Series backend for datetime features
    stock = baseTs(data=prices, times=dates, backend='series')
    
    # Calculate returns
    log_returns = stock.apply_function(lambda x: np.diff(np.log(x), prepend=x[0]))
    
    # Rolling statistics
    sma_20 = stock.rolling_mean(window=20)    # 20-day moving average
    volatility = log_returns.rolling_std(window=20)  # 20-day volatility
    
    # Extract specific periods
    last_month = stock.time_slice(start=dates[-30])
    ytd = stock.time_slice(start=f"{dates[-1].year}-01-01")
    
    # Statistics
    stats = stock.get_statistics()
    
    return {
        'stock': stock,
        'returns': log_returns,
        'sma20': sma_20,
        'volatility': volatility,
        'last_month': last_month,
        'ytd': ytd,
        'statistics': stats
    }

# Usage
dates = pd.date_range('2022-01-01', '2023-12-31', freq='D')
prices = 100 * np.exp(np.cumsum(np.random.randn(len(dates)) * 0.02))
analysis = analyze_stock_prices(prices, dates)
```

### Example 3: Sensor Data Processing

```python
def process_sensor_data(sensor_readings, timestamps):
    """Process IoT sensor data with quality control."""
    
    # Convert timestamps to datetime
    times = pd.to_datetime(timestamps)
    
    # Create time series
    sensor = baseTs(data=sensor_readings, times=times, backend='series')
    
    # Quality control pipeline
    # 1. Remove impossible values (sensor-specific)
    valid_range = sensor.apply_function(lambda x: np.clip(x, -50, 100))  # Temperature range
    
    # 2. Remove outliers
    cleaned = valid_range.remove_outliers(method='iqr', factor=2.0)
    
    # 3. Interpolate missing data points
    if hasattr(cleaned, 'interpolate'):
        interpolated = cleaned.interpolate(method='linear')
    else:
        interpolated = cleaned
    
    # 4. Smooth signal
    smoothed = interpolated.lowpass_filter(cutoff=0.1)
    
    # 5. Calculate hourly averages
    hourly_avg = smoothed.rolling_mean(window=60)  # Assuming 1-minute intervals
    
    # Anomaly detection
    anomalies = smoothed.outlier_indices(method='zscore', threshold=3)
    
    return {
        'raw': sensor,
        'processed': smoothed,
        'hourly_avg': hourly_avg,
        'anomalies': anomalies,
        'data_quality': {
            'original_points': sensor.len(),
            'cleaned_points': smoothed.len(),
            'anomaly_count': len(anomalies)
        }
    }

# Usage
timestamps = pd.date_range('2023-01-01', periods=1440, freq='T')  # 1 day, 1-min intervals
readings = 20 + 5*np.sin(2*np.pi*np.arange(1440)/1440) + np.random.randn(1440)
sensor_analysis = process_sensor_data(readings, timestamps)
```

### Example 4: Comparative Analysis

```python
def compare_processing_methods(data, times):
    """Compare different processing approaches."""
    
    methods = {
        'light_filtering': lambda ts: ts.lowpass_filter(cutoff=0.8),
        'heavy_filtering': lambda ts: ts.lowpass_filter(cutoff=0.1),
        'zscore_norm': lambda ts: ts.zscale(),
        'range_norm': lambda ts: ts.normalize_range(),
        'combined': lambda ts: ts.lowpass_filter(cutoff=0.3).zscale()
    }
    
    results = {}
    
    # Test each method
    for method_name, method_func in methods.items():
        ts = baseTs(data=data, times=times, backend='series')
        
        # Apply method
        processed = method_func(ts)
        
        # Calculate metrics
        stats = processed.get_statistics() if hasattr(processed, 'get_statistics') else {
            'mean': np.mean(processed.data),
            'std': np.std(processed.data),
            'min': np.min(processed.data),
            'max': np.max(processed.data)
        }
        
        results[method_name] = {
            'processed_data': processed,
            'statistics': stats,
            'snr': calculate_snr(processed.data) if len(processed.data) > 100 else None
        }
    
    return results

def calculate_snr(signal):
    """Calculate signal-to-noise ratio."""
    signal_power = np.mean(signal**2)
    noise_power = np.var(signal)
    return 10 * np.log10(signal_power / noise_power) if noise_power > 0 else float('inf')

# Usage
test_data = np.sin(np.linspace(0, 4*np.pi, 1000)) + 0.1*np.random.randn(1000)
test_times = np.linspace(0, 10, 1000)
comparison = compare_processing_methods(test_data, test_times)

# Print results
for method, results in comparison.items():
    stats = results['statistics']
    print(f"\n{method}:")
    print(f"  Mean: {stats['mean']:.4f}")
    print(f"  Std:  {stats['std']:.4f}")
    if results['snr']:
        print(f"  SNR:  {results['snr']:.2f} dB")
```

## Tips and Best Practices

### 1. Backend Selection
- Use NumPy for pure numerical processing
- Use Series for datetime indexing and pandas integration
- Be explicit about backend choice in production code

### 2. Error Handling
```python
def robust_processing(data, times):
    """Example of robust error handling."""
    try:
        ts = baseTs(data=data, times=times, backend='series')
        
        # Validate data
        if ts.len() == 0:
            raise ValueError("Empty time series")
        
        if ts.len() < 10:
            warnings.warn("Very short time series, results may be unreliable")
        
        # Process with error handling
        try:
            filtered = ts.lowpass_filter(cutoff=0.3)
        except ValueError as e:
            print(f"Filtering failed: {e}")
            filtered = ts  # Use original data
        
        return filtered
        
    except Exception as e:
        print(f"Processing failed: {e}")
        return None
```

### 3. Performance Monitoring
```python
# Always monitor performance for production use
@monitor_performance  # Custom decorator from earlier examples
def production_pipeline(data, times):
    ts = baseTs(data=data, times=times, backend='series')
    return ts.lowpass_filter(cutoff=0.3).zscale()
```

This user guide provides comprehensive coverage of baseTs functionality with practical examples for different use cases.