# Series Backend API Documentation

## Overview

The Series backend provides enhanced time-series functionality through a custom `TimeSeriesData` class that extends `pandas.Series`. This documentation covers the Series-specific implementation details and advanced features.

## Table of Contents
1. [TimeSeriesData Class](#timeseriesdataclass)
2. [Backend Management](#backend-management)
3. [Advanced Time-Series Features](#advanced-time-series-features)
4. [Metadata Management](#metadata-management)
5. [Performance Considerations](#performance-considerations)
6. [Integration with Pandas Ecosystem](#integration-with-pandas-ecosystem)

---

## TimeSeriesData Class

### Class Definition

```python
class TimeSeriesData(pd.Series):
    """
    Pandas Series subclass optimized for time series analysis.
    
    This class extends pandas Series to provide time-series specific functionality
    while maintaining compatibility with the existing baseTs API.
    """
```

### Metadata Attributes

The `TimeSeriesData` class preserves metadata through pandas' `_metadata` attribute:

```python
_metadata = [
    'freq',                    # Sampling frequency in Hz
    'signal_name',            # Name of the signal
    'history',                # Processing history list
    'is_filtered',            # Whether the data has been filtered
    'is_interpolated',        # Whether the data has been interpolated  
    'is_uniform_grid',        # Whether the data is on a uniform time grid
    'ts_offset',              # Timestamp offset in seconds
    'filtered_indices',       # Indices that were filtered/removed
    'lowess_fit',             # LOWESS fit data (if applicable)
    'last_process'            # Last processing operation performed
]
```

### Constructor

#### `TimeSeriesData.__init__(data, index=None, **metadata)`

Create a new TimeSeriesData object.

**Parameters:**
- `data` (array-like): The signal values
- `index` (array-like, optional): The time index (becomes pandas Index)
- `**metadata`: Additional metadata to preserve

**Example:**
```python
import pandas as pd
import numpy as np
from baseTs.series import TimeSeriesData

# Create with datetime index
dates = pd.date_range('2023-01-01', periods=100, freq='D')
data = np.random.randn(100)

ts_data = TimeSeriesData(
    data=data,
    index=dates,
    freq=1.0,  # Daily frequency
    signal_name="Daily Returns",
    history=['created']
)
```

### Core Methods

#### `copy(deep=True)`

Create a copy with metadata preservation.

**Parameters:**
- `deep` (bool, optional): Whether to make a deep copy. Default: True

**Returns:**
- `TimeSeriesData`: Copy with all metadata preserved

#### `_constructor()`

Internal constructor for pandas operations.

**Returns:**
- `TimeSeriesData`: New instance maintaining the same class type

---

## Backend Management

### BackendManager Class

```python
class BackendManager:
    """Manages backend selection and configuration for baseTs objects."""
```

#### Configuration Methods

##### `set_default_backend(backend)`

Set the global default backend.

**Parameters:**
- `backend` (str): 'numpy' or 'series'

**Example:**
```python
from baseTs.compat import BackendManager

# Make Series the default for all new baseTs objects
BackendManager.set_default_backend('series')
```

##### `get_default_backend()`

Get the current default backend.

**Returns:**
- `str`: Current default backend ('numpy' or 'series')

##### `should_use_series()`

Determine if Series backend should be used based on configuration.

**Returns:**
- `bool`: True if Series backend should be used

**Environment Variables:**
- `BASETS_USE_SERIES`: Set to 'true' to enable Series backend by default
- `BASETS_DEFAULT_BACKEND`: Set to 'series' or 'numpy'

**Example:**
```python
import os
os.environ['BASETS_DEFAULT_BACKEND'] = 'series'

# Now all baseTs objects will use Series backend by default
from baseTs import baseTs
ts = baseTs(data=data, times=times)  # Uses Series backend
```

### ArrayCompatMixin

Provides backward compatibility between backends.

```python
class ArrayCompatMixin:
    """
    Mixin providing compatibility layer between numpy and Series backends.
    
    Ensures that property access works consistently regardless of backend.
    """
```

#### Properties

##### `data`
```python
@property
def data(self) -> np.ndarray:
    """Access underlying data as numpy array, regardless of backend."""
```

##### `times` 
```python
@property
def times(self) -> np.ndarray:
    """Access underlying time values as numpy array, regardless of backend."""
```

---

## Advanced Time-Series Features

### Rolling Operations

The Series backend provides optimized rolling operations through pandas' built-in functionality.

#### Implementation Details

```python
def rolling_mean(self, window: int, center: bool = False) -> 'baseTs':
    """
    Calculate rolling mean using pandas rolling windows.
    
    Leverages pandas' optimized rolling operations for better performance
    compared to manual implementation.
    """
```

#### Performance Characteristics

- **Window-based operations**: O(n) complexity with pandas optimization
- **Memory efficient**: Streaming computation for large datasets  
- **NaN handling**: Automatic handling of missing values
- **Edge behavior**: Configurable behavior at series boundaries

#### Usage Examples

```python
# Basic rolling operations
ts = baseTs(data=data, times=dates, backend='series')

# Simple rolling mean
rolling_avg = ts.rolling_mean(window=30)

# Centered rolling mean (better for trend analysis)
centered_avg = ts.rolling_mean(window=30, center=True)

# Multiple rolling statistics
rolling_std = ts.rolling_std(window=30)
rolling_max = ts.rolling_max(window=30)
rolling_min = ts.rolling_min(window=30)

# Calculate rolling range
rolling_range = rolling_max.data - rolling_min.data
```

### Time-Based Slicing

#### `time_slice()` Implementation

```python
def time_slice(self, start=None, end=None):
    """
    Extract time series slice using pandas' powerful indexing.
    
    Supports various datetime formats and partial date matching.
    """
```

#### Supported Formats

- **ISO strings**: '2023-01-01', '2023-01-01 12:00:00'
- **Pandas Timestamp**: `pd.Timestamp('2023-01-01')`
- **Python datetime**: `datetime(2023, 1, 1)`
- **Partial dates**: '2023-01' (entire month), '2023' (entire year)

#### Advanced Slicing Examples

```python
ts = baseTs(data=data, times=pd.date_range('2023-01-01', periods=365, freq='D'), 
            backend='series')

# Date range slicing
q1 = ts.time_slice(start='2023-01-01', end='2023-03-31')
q2 = ts.time_slice(start='2023-04-01', end='2023-06-30')

# Partial date matching
january = ts.time_slice(start='2023-01', end='2023-01')  # Entire month
winter = ts.time_slice(start='2023-12', end='2024-02')   # Across year boundary

# Open-ended slicing
recent = ts.time_slice(start='2023-06-01')  # From June to end
early = ts.time_slice(end='2023-06-01')     # From start to June

# Time-of-day slicing (if datetime index includes time)
morning_data = ts.time_slice(start='2023-01-01 06:00', end='2023-01-01 12:00')
```

### Enhanced Statistics

#### `get_statistics()` Implementation

```python
def get_statistics(self) -> Dict[str, float]:
    """
    Comprehensive statistical analysis using pandas methods.
    
    Leverages pandas' optimized statistical functions for better performance
    and more comprehensive analysis than manual computation.
    """
```

#### Returned Statistics

```python
{
    'count': int,           # Number of non-null observations
    'mean': float,          # Arithmetic mean
    'std': float,           # Standard deviation (sample)
    'min': float,           # Minimum value
    'max': float,           # Maximum value
    'median': float,        # 50th percentile
    'q25': float,           # 25th percentile
    'q75': float,           # 75th percentile
    'skew': float,          # Skewness (scipy.stats)
    'kurtosis': float,      # Kurtosis (scipy.stats)
    'var': float,           # Variance
    'sem': float,           # Standard error of mean
    'mad': float            # Mean absolute deviation
}
```

#### Usage Example

```python
stats = ts.get_statistics()

# Comprehensive reporting
print(f"Data Quality:")
print(f"  Observations: {stats['count']}")
print(f"  Missing: {ts.len() - stats['count']}")

print(f"\nCentral Tendency:")
print(f"  Mean: {stats['mean']:.4f}")
print(f"  Median: {stats['median']:.4f}")

print(f"\nDispersion:")
print(f"  Std Dev: {stats['std']:.4f}")
print(f"  Range: {stats['max'] - stats['min']:.4f}")
print(f"  IQR: {stats['q75'] - stats['q25']:.4f}")

print(f"\nDistribution Shape:")
print(f"  Skewness: {stats['skew']:.4f}")
print(f"  Kurtosis: {stats['kurtosis']:.4f}")
```

---

## Metadata Management

### Automatic Metadata Preservation

The Series backend automatically preserves metadata through pandas operations:

```python
# Metadata is preserved through operations
ts = baseTs(data=data, times=times, backend='series', signal_name="Original")
filtered = ts.lowpass_filter(cutoff=0.3)

print(f"Original name: {ts.signal_name}")      # "Original"
print(f"Filtered name: {filtered.signal_name}") # "Original" (preserved)
print(f"Is filtered: {filtered.is_filtered}")   # True
print(f"History: {filtered.history}")           # ['created', 'lowpass_filter']
```

### Manual Metadata Management

#### Setting Metadata

```python
# Set metadata on existing object
ts._metadata_dict = {
    'signal_name': 'Sensor Data',
    'freq': 100.0,
    'history': ['imported', 'calibrated']
}

# Or set individual attributes
ts.signal_name = 'Updated Name'
ts.freq = 250.0
```

#### Accessing Metadata

```python
# Access metadata
print(f"Signal: {ts.signal_name}")
print(f"Frequency: {ts.freq} Hz")
print(f"Processing history: {ts.history}")

# Check processing state
if ts.is_filtered:
    print("Data has been filtered")
    if hasattr(ts, 'filtered_indices'):
        print(f"Filtered {len(ts.filtered_indices)} points")

if ts.is_interpolated:
    print("Data has been interpolated")
```

### History Tracking

#### Automatic History Updates

```python
ts = baseTs(data=data, times=times, backend='series')
print(ts.history)  # ['created']

filtered = ts.lowpass_filter(cutoff=0.3)
print(filtered.history)  # ['created', 'lowpass_filter']

normalized = filtered.zscale()
print(normalized.history)  # ['created', 'lowpass_filter', 'zscale']
```

#### Manual History Management

```python
# Add custom history entry
ts._add_history("custom_processing_step")

# Clear history
ts.history = []

# Set complete history
ts.history = ['imported', 'validated', 'preprocessed']
```

---

## Performance Considerations

### Memory Usage

The Series backend uses approximately 10-20% more memory than NumPy backend due to:

- Pandas Index objects
- Metadata storage
- Series overhead

#### Memory Optimization

```python
# Use appropriate data types
data = data.astype(np.float32)  # Reduce memory by 50%

# For large datasets, consider chunking
def process_large_series(data, times, chunk_size=100000):
    """Process large time series in chunks."""
    results = []
    
    for i in range(0, len(data), chunk_size):
        chunk_data = data[i:i+chunk_size]
        chunk_times = times[i:i+chunk_size]
        
        chunk_ts = baseTs(data=chunk_data, times=chunk_times, backend='series')
        processed = chunk_ts.lowpass_filter(cutoff=0.3)
        results.append(processed)
    
    return combine_chunks(results)
```

### Computational Performance

#### Operation Performance Comparison

| Operation | NumPy Backend | Series Backend | Notes |
|-----------|---------------|----------------|-------|
| Element access | 1x | 1.2x | Minimal overhead |
| Basic math | 1x | 1.1x | Vectorized operations |
| Filtering | 1x | 1.5x | Additional metadata handling |
| Rolling ops | Manual loop | Optimized | Series often faster |
| Time slicing | Index lookup | Native | Series much faster |
| Statistics | Manual calc | Native | Series faster |

#### Performance Tips

```python
# For pure numerical work, use NumPy backend
signal_processing = baseTs(data=data, times=times, backend='numpy')
filtered = signal_processing.lowpass_filter(cutoff=0.3)

# Convert to Series for time-series analysis
time_analysis = baseTs(
    data=filtered.data, 
    times=pd.date_range('2023-01-01', periods=len(filtered.data), freq='D'),
    backend='series'
)
rolling_avg = time_analysis.rolling_mean(window=30)
```

---

## Integration with Pandas Ecosystem

### DataFrame Integration

#### Converting to DataFrame

```python
# Convert baseTs to DataFrame
ts = baseTs(data=data, times=dates, backend='series')

df = pd.DataFrame({
    'timestamp': ts.times,
    'value': ts.data,
    'signal_name': ts.signal_name
})

# Or directly from Series backend
if ts._backend == 'series':
    df = ts._data.to_frame('value')
    df['signal_name'] = ts.signal_name
```

#### Creating from DataFrame

```python
# Create baseTs from DataFrame
df = pd.read_csv('timeseries.csv', parse_dates=['timestamp'])
ts = baseTs.from_df(df, time_col='timestamp', data_col='value')
```

### Pandas Operations

#### Direct Series Access

```python
# Access underlying Series for pandas operations
ts = baseTs(data=data, times=dates, backend='series')

# Direct pandas operations
series_data = ts._data
resampled = series_data.resample('M').mean()  # Monthly resampling
grouped = series_data.groupby(series_data.index.month).mean()  # By month
```

#### Method Chaining with Pandas

```python
# Combine baseTs and pandas operations
result = (ts
          .lowpass_filter(cutoff=0.3)
          .rolling_mean(window=30)
          ._data  # Access underlying Series
          .resample('W')  # Pandas resampling
          .mean()  # Weekly means
         )

# Convert back to baseTs if needed
weekly_ts = baseTs(
    data=result.values,
    times=result.index,
    backend='series',
    signal_name=f"{ts.signal_name}_weekly"
)
```

### Plotting Integration

#### Matplotlib Integration

```python
import matplotlib.pyplot as plt

# Direct plotting of Series backend
ts = baseTs(data=data, times=dates, backend='series')

fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# Plot original data
ts._data.plot(ax=axes[0], title=f"{ts.signal_name} - Original")

# Plot rolling average
rolling_avg = ts.rolling_mean(window=30)
rolling_avg._data.plot(ax=axes[1], title="30-Day Rolling Average")

plt.tight_layout()
plt.show()
```

#### Plotly Integration

```python
import plotly.express as px
import plotly.graph_objects as go

# Convert to DataFrame for Plotly
df = ts._data.reset_index()
df.columns = ['timestamp', 'value']

# Interactive plot
fig = px.line(df, x='timestamp', y='value', title=ts.signal_name)
fig.show()

# Multiple series comparison
fig = go.Figure()
fig.add_trace(go.Scatter(x=ts.times, y=ts.data, name='Original'))
fig.add_trace(go.Scatter(x=rolling_avg.times, y=rolling_avg.data, name='Rolling Average'))
fig.show()
```

---

## Advanced Usage Patterns

### Custom Series Subclassing

```python
class CustomTimeSeriesData(TimeSeriesData):
    """Custom extension with domain-specific methods."""
    
    @property
    def _constructor(self):
        return CustomTimeSeriesData
    
    def domain_specific_method(self):
        """Add domain-specific functionality."""
        # Custom implementation
        return self._constructor(
            self.values * 2,  # Example transformation
            index=self.index,
            **self._metadata_dict
        )

# Use custom class
custom_ts = CustomTimeSeriesData(data=data, index=dates)
result = custom_ts.domain_specific_method()
```

### Batch Processing

```python
def process_multiple_series(series_list, operations):
    """Process multiple time series with same operations."""
    results = []
    
    for ts_data in series_list:
        ts = baseTs(data=ts_data['data'], times=ts_data['times'], backend='series')
        
        # Apply operations chain
        result = ts
        for operation in operations:
            result = operation(result)
        
        results.append(result)
    
    return results

# Usage
operations = [
    lambda ts: ts.lowpass_filter(cutoff=0.3),
    lambda ts: ts.rolling_mean(window=30),
    lambda ts: ts.zscale()
]

processed_series = process_multiple_series(data_list, operations)
```

This comprehensive API documentation covers all aspects of the Series backend, providing detailed information for advanced users who want to leverage the full power of the pandas integration.