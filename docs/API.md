# baseTs API Documentation

## Table of Contents
1. [Core Class](#core-class)
2. [Constructor](#constructor)
3. [Properties](#properties)
4. [Core Methods](#core-methods)
5. [Signal Processing](#signal-processing)
6. [Data Transformation](#data-transformation)
7. [Statistical Analysis](#statistical-analysis)
8. [Time-Series Operations (Series Backend)](#time-series-operations-series-backend)
9. [Utility Functions](#utility-functions)
10. [Backend Management](#backend-management)
11. [Legacy Methods](#legacy-methods)

---

## Core Class

### `baseTs`

The main class for time series data analysis with dual backend support.

```python
class baseTs(ArrayCompatMixin):
    """
    Time series data container with signal processing capabilities.
    
    Supports both NumPy array and Pandas Series backends for enhanced
    time-series functionality while maintaining backward compatibility.
    """
```

---

## Constructor

### `baseTs.__init__(data, times, backend='numpy', **kwargs)`

Create a new baseTs object.

**Parameters:**
- `data` (array-like): The signal values (y-axis data)
- `times` (array-like): The time points (x-axis data) 
- `backend` (str, optional): Backend to use ('numpy' or 'series'). Default: 'numpy'
- `signal_name` (str, optional): Name for the signal
- `freq` (float, optional): Sampling frequency in Hz
- `ts_offset` (float, optional): Time offset in seconds
- `use_series` (bool, optional): Deprecated, use `backend` parameter instead

**Returns:**
- `baseTs`: New baseTs instance

**Raises:**
- `ValueError`: If data and times have different lengths
- `TypeError`: If data or times are not array-like

**Examples:**

```python
import numpy as np
import pandas as pd
from baseTs import baseTs

# NumPy backend (default)
data = np.sin(np.linspace(0, 4*np.pi, 1000))
times = np.linspace(0, 10, 1000)
ts = baseTs(data=data, times=times)

# Series backend
dates = pd.date_range('2023-01-01', periods=365, freq='D')
ts_series = baseTs(data=np.random.randn(365), times=dates, backend='series')

# With metadata
ts_named = baseTs(data=data, times=times, 
                  signal_name="Test Signal", freq=100.0)
```

### `from_df(df, time_col='time', data_col='value', **kwargs)`

Create baseTs object from pandas DataFrame.

**Parameters:**
- `df` (pd.DataFrame): Input DataFrame
- `time_col` (str): Column name for time values. Default: 'time'
- `data_col` (str): Column name for data values. Default: 'value'
- `signal_name` (str, optional): Signal name
- `freq` (float, optional): Sampling frequency
- `ts_offset` (float, optional): Time offset

**Returns:**
- `baseTs`: New baseTs instance

**Example:**
```python
df = pd.DataFrame({
    'timestamp': pd.date_range('2023-01-01', periods=100, freq='H'),
    'sensor_value': np.random.randn(100)
})
ts = baseTs.from_df(df, time_col='timestamp', data_col='sensor_value')
```

---

## Properties

### Core Properties

#### `data`
```python
@property
def data(self) -> np.ndarray:
    """Access the underlying data array."""
```

#### `times`
```python
@property  
def times(self) -> np.ndarray:
    """Access the underlying time array."""
```

#### `len()`
```python
def len(self) -> int:
    """Get the length of the time series."""
```

### Backend Properties

#### `backend`
```python
@property
def backend(self) -> str:
    """Get current backend ('numpy' or 'series')."""
```

### Metadata Properties (Series Backend)

#### `signal_name`
```python
@property
def signal_name(self) -> Optional[str]:
    """Signal name identifier."""
```

#### `freq`
```python
@property
def freq(self) -> Optional[float]:
    """Sampling frequency in Hz."""
```

#### `is_filtered`
```python
@property
def is_filtered(self) -> bool:
    """Whether the signal has been filtered."""
```

#### `history`
```python
@property
def history(self) -> List[str]:
    """Processing history list."""
```

#### `last_process`
```python
@property
def last_process(self) -> Optional[str]:
    """Most recent processing operation."""
```

**Example:**
```python
ts = baseTs(data=data, times=times, backend='series')
filtered = ts.lowpass_filter(cutoff=0.3)

print(f"Length: {ts.len()}")
print(f"Backend: {ts.backend}")
print(f"Is filtered: {filtered.is_filtered}")
print(f"History: {filtered.history}")
```

---

## Core Methods

### `copy()`
```python
def copy(self) -> 'baseTs':
    """Create a deep copy of the baseTs object."""
```

**Returns:**
- `baseTs`: Deep copy of the current object

**Example:**
```python
ts_copy = ts.copy()
ts_copy.data[0] = 999  # Doesn't affect original ts
```

---

## Signal Processing

### `lowpass_filter(cutoff, order=4)`

Apply low-pass Butterworth filter.

**Parameters:**
- `cutoff` (float): Normalized cutoff frequency (0 < cutoff < 1)
- `order` (int, optional): Filter order. Default: 4

**Returns:**
- `baseTs`: New filtered baseTs object

**Raises:**
- `ValueError`: If cutoff is not between 0 and 1

**Example:**
```python
# Remove high-frequency noise
filtered = ts.lowpass_filter(cutoff=0.3)

# Aggressive filtering
heavily_filtered = ts.lowpass_filter(cutoff=0.1, order=6)
```

### `highpass_filter(cutoff, order=4)`

Apply high-pass Butterworth filter.

**Parameters:**
- `cutoff` (float): Normalized cutoff frequency (0 < cutoff < 1)
- `order` (int, optional): Filter order. Default: 4

**Returns:**
- `baseTs`: New filtered baseTs object

**Example:**
```python
# Remove low-frequency trends
detrended = ts.highpass_filter(cutoff=0.05)
```

### `bandpass_filter(low_cutoff, high_cutoff, order=4)`

Apply band-pass Butterworth filter.

**Parameters:**
- `low_cutoff` (float): Low cutoff frequency (0 < low_cutoff < 1)
- `high_cutoff` (float): High cutoff frequency (low_cutoff < high_cutoff < 1)
- `order` (int, optional): Filter order. Default: 4

**Returns:**
- `baseTs`: New filtered baseTs object

**Example:**
```python
# Extract specific frequency band
bandpassed = ts.bandpass_filter(low_cutoff=0.1, high_cutoff=0.4)
```

### `notch_filter(freq, quality=30)`

Apply notch filter to remove specific frequency.

**Parameters:**
- `freq` (float): Frequency to remove (Hz)
- `quality` (float, optional): Quality factor. Default: 30

**Returns:**
- `baseTs`: New filtered baseTs object

**Example:**
```python
# Remove 60 Hz power line noise
denoised = ts.notch_filter(freq=60)
```

---

## Data Transformation

### `zscale()`

Z-score normalization (mean=0, std=1).

**Returns:**
- `baseTs`: New normalized baseTs object

**Raises:**
- `ValueError`: If standard deviation is zero (constant signal)

**Example:**
```python
normalized = ts.zscale()
print(f"Mean: {np.mean(normalized.data):.6f}")  # ~0.0
print(f"Std: {np.std(normalized.data):.6f}")    # ~1.0
```

### `normalize_range(new_min=0, new_max=1)`

Range normalization to specified bounds.

**Parameters:**
- `new_min` (float, optional): New minimum value. Default: 0
- `new_max` (float, optional): New maximum value. Default: 1

**Returns:**
- `baseTs`: New normalized baseTs object

**Raises:**
- `ValueError`: If new_min >= new_max or if data range is zero

**Example:**
```python
# Normalize to [0, 1]
norm_01 = ts.normalize_range()

# Normalize to [-1, 1] 
norm_11 = ts.normalize_range(new_min=-1, new_max=1)

# Custom range
custom = ts.normalize_range(new_min=10, new_max=20)
```

### `apply_function(func)`

Apply arbitrary function to data.

**Parameters:**
- `func` (callable): Function to apply to data array

**Returns:**
- `baseTs`: New baseTs object with transformed data

**Example:**
```python
# Square the signal
squared = ts.apply_function(lambda x: x**2)

# Apply numpy functions
rectified = ts.apply_function(lambda x: np.maximum(x, 0))  # ReLU
log_transformed = ts.apply_function(lambda x: np.log(np.abs(x) + 1e-10))

# Custom function
def custom_transform(x):
    return np.where(x > 0, np.sqrt(x), -np.sqrt(np.abs(x)))

transformed = ts.apply_function(custom_transform)
```

### `detrend(method='linear')`

Remove trend from signal.

**Parameters:**
- `method` (str, optional): Detrending method ('linear', 'constant'). Default: 'linear'

**Returns:**
- `baseTs`: New detrended baseTs object

**Example:**
```python
# Remove linear trend
detrended = ts.detrend(method='linear')

# Remove mean only
demeaned = ts.detrend(method='constant')
```

---

## Statistical Analysis

### `outlier_indices(method='iqr', **kwargs)`

Detect outlier indices using various methods.

**Parameters:**
- `method` (str): Detection method ('iqr', 'zscore', 'modified_zscore')
- `**kwargs`: Method-specific parameters

**Method-specific parameters:**
- `iqr`: `factor` (float, default=1.5) - IQR multiplier
- `zscore`: `threshold` (float, default=3) - Z-score threshold  
- `modified_zscore`: `threshold` (float, default=3.5) - Modified Z-score threshold

**Returns:**
- `np.ndarray`: Array of outlier indices

**Example:**
```python
# IQR method (default)
outliers_iqr = ts.outlier_indices(method='iqr', factor=1.5)

# Z-score method
outliers_z = ts.outlier_indices(method='zscore', threshold=3)

# Modified Z-score method
outliers_mod = ts.outlier_indices(method='modified_zscore', threshold=3.5)

print(f"Found {len(outliers_iqr)} outliers using IQR method")
```

### `remove_outliers(method='iqr', **kwargs)`

Remove outliers from the time series.

**Parameters:**
- `method` (str): Detection method ('iqr', 'zscore', 'modified_zscore')
- `**kwargs`: Method-specific parameters (see `outlier_indices`)

**Returns:**
- `baseTs`: New baseTs object with outliers removed

**Example:**
```python
# Remove outliers using IQR method
cleaned = ts.remove_outliers(method='iqr', factor=2.0)

print(f"Original length: {ts.len()}")
print(f"Cleaned length: {cleaned.len()}")
print(f"Removed {ts.len() - cleaned.len()} outliers")
```

### `interpolate(method='linear')`

Interpolate missing or removed values.

**Parameters:**
- `method` (str, optional): Interpolation method ('linear', 'cubic', 'nearest'). Default: 'linear'

**Returns:**
- `baseTs`: New baseTs object with interpolated data

**Example:**
```python
# Linear interpolation
interpolated = ts.interpolate(method='linear')

# Cubic interpolation
cubic_interp = ts.interpolate(method='cubic')
```

### `resample(factor)`

Resample the time series.

**Parameters:**
- `factor` (float): Resampling factor (>1 for upsampling, <1 for downsampling)

**Returns:**
- `baseTs`: New resampled baseTs object

**Example:**
```python
# Upsample by factor of 2
upsampled = ts.resample(factor=2)

# Downsample by factor of 2
downsampled = ts.resample(factor=0.5)
```

---

## Time-Series Operations (Series Backend)

These methods are available when using `backend='series'`.

### `rolling_mean(window, center=False)`

Calculate rolling mean.

**Parameters:**
- `window` (int): Window size in number of periods
- `center` (bool, optional): Whether to center the window. Default: False

**Returns:**
- `baseTs`: New baseTs object with rolling mean

**Example:**
```python
ts = baseTs(data=data, times=dates, backend='series')

# 7-day rolling average
weekly_avg = ts.rolling_mean(window=7)

# Centered 30-day rolling average  
monthly_avg = ts.rolling_mean(window=30, center=True)
```

### `rolling_std(window, center=False)`

Calculate rolling standard deviation.

**Parameters:**
- `window` (int): Window size in number of periods
- `center` (bool, optional): Whether to center the window. Default: False

**Returns:**
- `baseTs`: New baseTs object with rolling standard deviation

**Example:**
```python
# 7-day rolling volatility
volatility = ts.rolling_std(window=7)
```

### `rolling_max(window, center=False)`

Calculate rolling maximum.

**Parameters:**
- `window` (int): Window size in number of periods
- `center` (bool, optional): Whether to center the window. Default: False

**Returns:**
- `baseTs`: New baseTs object with rolling maximum

### `rolling_min(window, center=False)`

Calculate rolling minimum.

**Parameters:**
- `window` (int): Window size in number of periods  
- `center` (bool, optional): Whether to center the window. Default: False

**Returns:**
- `baseTs`: New baseTs object with rolling minimum

**Example:**
```python
# Rolling statistics
rolling_max = ts.rolling_max(window=30)
rolling_min = ts.rolling_min(window=30)
rolling_range = rolling_max - rolling_min  # Custom calculation
```

### `time_slice(start=None, end=None)`

Extract time series slice by time/date range.

**Parameters:**
- `start` (str or datetime-like, optional): Start time/date
- `end` (str or datetime-like, optional): End time/date

**Returns:**
- `baseTs`: New baseTs object with sliced data

**Raises:**
- `ValueError`: If start >= end or if times are not datetime-indexed

**Example:**
```python
# Date strings (automatically parsed)
january = ts.time_slice(start='2023-01-01', end='2023-01-31')

# Specific time ranges
morning = ts.time_slice(start='2023-01-01 06:00', end='2023-01-01 12:00')

# Open-ended slices
recent = ts.time_slice(start='2023-06-01')  # From June onwards
early = ts.time_slice(end='2023-03-31')     # Until March
```

### `get_statistics()`

Get comprehensive statistical summary.

**Returns:**
- `dict`: Dictionary containing statistical measures

**Keys returned:**
- `mean`: Mean value
- `std`: Standard deviation
- `min`: Minimum value
- `max`: Maximum value
- `median`: Median value
- `skew`: Skewness
- `kurtosis`: Kurtosis
- `count`: Number of observations

**Example:**
```python
stats = ts.get_statistics()

print(f"Mean: {stats['mean']:.4f}")
print(f"Std Dev: {stats['std']:.4f}")
print(f"Skewness: {stats['skew']:.4f}")
print(f"Kurtosis: {stats['kurtosis']:.4f}")
print(f"Range: {stats['min']:.4f} to {stats['max']:.4f}")
```

---

## Utility Functions

### `diff()`

Calculate first differences.

**Returns:**
- `baseTs`: New baseTs object with first differences

**Example:**
```python
# Calculate first differences (useful for returns, velocities, etc.)
differences = ts.diff()
print(f"Original length: {ts.len()}, Diff length: {differences.len()}")
```

### `dediff()`

Reverse first differences (cumulative sum).

**Returns:**
- `baseTs`: New baseTs object with cumulative sum

**Example:**
```python
# Calculate cumulative sum (reverse of diff)
cumulative = ts.dediff()
```

---

## Backend Management

### `BackendManager`

Utility class for managing backend preferences.

#### `BackendManager.set_default_backend(backend)`

Set the default backend for new baseTs objects.

**Parameters:**
- `backend` (str): Backend name ('numpy' or 'series')

**Example:**
```python
from baseTs.compat import BackendManager

# Set Series as default for new objects
BackendManager.set_default_backend('series')

# Now all new baseTs objects use Series backend by default
ts = baseTs(data=data, times=times)  # Uses 'series' backend
```

#### `BackendManager.get_default_backend()`

Get the current default backend.

**Returns:**
- `str`: Current default backend

#### `BackendManager.should_use_series()`

Check if Series backend should be used based on configuration.

**Returns:**
- `bool`: True if Series backend should be used

### Backend Conversion

#### `convert_to_series(data, times, **metadata)`

Convert numpy arrays to pandas Series with metadata.

**Parameters:**
- `data` (array-like): Data values
- `times` (array-like): Time values
- `**metadata`: Metadata to preserve

**Returns:**
- `TimeSeriesData`: Pandas Series subclass with metadata

---

## Legacy Methods

These methods are maintained for backward compatibility.

### Signal Processing (Legacy)

```python
# Legacy bandpass method
def bandpass_at(self, hp_hz, lp_hz, sampling_rate=None):
    """Legacy bandpass filter method."""
    
# Legacy outlier filtering
def set_outlier_filter(self, frac=0.1, z_threshold=2.5):
    """Set up LOWESS outlier filter."""

def filter_outliers(self):
    """Apply LOWESS outlier filtering."""
```

### Plotting (Legacy)

```python
def plot(self, show=True, ax=None, **kwargs):
    """Plot the time series."""

def plot_fft_power(self, max_rate=None, show=True, ax=None):
    """Plot FFT power spectrum."""
```

---

## Error Handling

### Common Exceptions

- **`ValueError`**: Invalid parameter values, mismatched array lengths
- **`TypeError`**: Incorrect data types  
- **`AttributeError`**: Method not available for current backend
- **`RuntimeError`**: Processing failures (e.g., filtering errors)

### Error Handling Example

```python
try:
    # This might fail if cutoff is invalid
    filtered = ts.lowpass_filter(cutoff=1.5)  # Invalid: > 1.0
except ValueError as e:
    print(f"Filter error: {e}")
    # Use a valid cutoff
    filtered = ts.lowpass_filter(cutoff=0.3)

try:
    # This might fail with constant data
    normalized = ts.zscale()
except ValueError as e:
    print(f"Normalization failed: {e}")
    # Use range normalization instead
    normalized = ts.normalize_range()
```

---

## Performance Notes

### NumPy Backend Performance
- Fastest for pure numerical operations
- Minimal memory overhead
- Best for high-frequency processing

### Series Backend Performance  
- 1-5x overhead for basic operations
- Optimized rolling operations (often faster than manual implementation)
- Enhanced functionality worth the overhead for time-series analysis

### Optimization Tips

```python
# For large datasets, consider data type optimization
data = data.astype(np.float32)  # Use float32 if precision allows

# Use NumPy backend for pure signal processing
signal_proc = baseTs(data=data, times=times, backend='numpy')
filtered = signal_proc.lowpass_filter(cutoff=0.3)

# Switch to Series backend for time-series analysis
ts_analysis = baseTs(data=filtered.data, times=dates, backend='series')
rolling_avg = ts_analysis.rolling_mean(window=30)
```

---

## Method Chaining

All methods return new baseTs objects, enabling method chaining:

```python
# Chain multiple operations
result = (ts
          .lowpass_filter(cutoff=0.3)
          .remove_outliers(method='iqr', factor=2.0)
          .zscale()
          .apply_function(np.abs))

# With Series backend, include rolling operations
result = (ts
          .lowpass_filter(cutoff=0.3)
          .rolling_mean(window=30)
          .zscale())
```

This API documentation provides comprehensive coverage of all baseTs functionality across both backends.