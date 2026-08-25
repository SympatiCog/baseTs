# baseTs API Documentation

## Table of Contents
1. [Core Class](#core-class)
2. [Constructor](#constructor)
3. [Properties](#properties)
4. [Core Methods](#core-methods)
5. [Signal Processing](#signal-processing)
6. [Data Transformation](#data-transformation)
7. [Statistical Analysis](#statistical-analysis)
8. [Enhanced Time-Series Operations](#enhanced-time-series-operations)
9. [Enhanced Frequency Analysis](#enhanced-frequency-analysis)
10. [Utility Functions](#utility-functions)
11. [Legacy Methods](#legacy-methods)

---

## Core Class

### `baseTs`

The main class for time series data analysis built on pandas Series foundation.

```python
class baseTs(TimeSeriesData):
    """
    Time series data container with signal processing capabilities.
    
    Built directly on pandas Series foundation, providing access to 270+
    native pandas methods while maintaining full backward compatibility.
    """
```

---

## Constructor

### `baseTs.__init__(data, times, **kwargs)`

Create a new baseTs object.

**Parameters:**
- `data` (array-like): The signal values (y-axis data)
- `times` (array-like): The time points (x-axis data) 
- `signal_name` (str, optional): Name for the signal
- `freq` (float, optional): Sampling frequency in Hz
- `ts_offset` (float, optional): Time offset in seconds

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

# Create time series with numeric times
data = np.sin(np.linspace(0, 4*np.pi, 1000))
times = np.linspace(0, 10, 1000)
ts = baseTs(data=data, times=times)

# Create time series with datetime index
dates = pd.date_range('2023-01-01', periods=365, freq='D')
ts_series = baseTs(data=np.random.randn(365), times=dates)

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

### Metadata Properties

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
ts = baseTs(data=data, times=times)
filtered = ts.lowpass_filter(cutoff=0.3)

print(f"Length: {ts.len()}")
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

### `detrend(method='linear', inplace=False)`

Remove trend from the signal using various detrending methods.

**Parameters:**
- `method` (str, optional): Detrending method ('linear', 'constant'). Default: 'linear'
  - 'linear': Remove linear trend (best fit line)
  - 'constant': Remove mean (demean the signal)
- `inplace` (bool, optional): If True, modifies existing object. Otherwise returns new object. Default: False

**Returns:**
- `baseTs`: New detrended baseTs object

**Raises:**
- `ValueError`: If method is not supported

**Example:**
```python
# Remove linear trend
detrended = ts.detrend(method='linear')

# Remove mean only (constant detrending)
demeaned = ts.detrend(method='constant')

# In-place detrending
ts.detrend(method='linear', inplace=True)
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

### `interpolate_gaps(method='linear', limit=None, order=None, inplace=False)`

Interpolate missing values (NaN) in the time series with enhanced capabilities.

**Parameters:**
- `method` (str, optional): Interpolation method ('linear', 'time', 'spline', 'polynomial', etc.). Default: 'linear'
- `limit` (int, optional): Maximum number of consecutive NaN values to interpolate
- `order` (int, optional): Order for polynomial/spline interpolation methods
- `inplace` (bool, optional): If True, modifies existing object. Otherwise returns new object

**Returns:**
- `baseTs`: New baseTs object with interpolated data

**Example:**
```python
# Linear interpolation
interpolated = ts.interpolate_gaps(method='linear')

# Polynomial interpolation with order 3
poly_interp = ts.interpolate_gaps(method='polynomial', order=3)

# Spline interpolation with limit
spline_interp = ts.interpolate_gaps(method='spline', order=2, limit=10)

# Time-based interpolation (works with numeric indices)
time_interp = ts.interpolate_gaps(method='time')
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

## Enhanced Time-Series Operations

These methods leverage the pandas Series foundation for optimal performance.

### `rolling_mean(window, center=False)`

Calculate rolling mean.

**Parameters:**
- `window` (int): Window size in number of periods
- `center` (bool, optional): Whether to center the window. Default: False

**Returns:**
- `baseTs`: New baseTs object with rolling mean

**Example:**
```python
ts = baseTs(data=data, times=dates)

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

## Enhanced Frequency Analysis

### `get_frequency_content(window=None)`

Get frequency domain representation using enhanced FFT with optional windowing.

**Parameters:**
- `window` (str, optional): Window function to apply ('hann', 'hamming', 'blackman', None)

**Returns:**
- `Tuple[NDArray, NDArray]`: Tuple of (frequencies, power_spectrum)

**Example:**
```python
# Basic FFT
freqs, power = ts.get_frequency_content()

# With Hann window for reduced spectral leakage
freqs, power = ts.get_frequency_content(window='hann')

# With Blackman window for maximum side-lobe suppression
freqs, power = ts.get_frequency_content(window='blackman')
```

### `get_peak_freq(num_pks=1, window=None, min_freq=None, max_freq=None)`

Get the top peak frequencies using enhanced frequency analysis with windowing.

**Parameters:**
- `num_pks` (int, optional): Number of top peak frequencies to return. Default: 1
- `window` (str, optional): Window function to apply ('hann', 'hamming', 'blackman', None)
- `min_freq` (float, optional): Minimum frequency to consider (Hz, defaults to exclude DC component)
- `max_freq` (float, optional): Maximum frequency to consider (Hz, defaults to Nyquist)

**Returns:**
- `float` or `List[float]`: Single peak frequency if num_pks=1, otherwise list of peak frequencies

**Example:**
```python
# Basic peak frequency (excludes DC component by default)
peak = ts.get_peak_freq()  # Returns: 25.3

# Top 3 peaks with Hanning window
peaks = ts.get_peak_freq(num_pks=3, window='hann')  # Returns: [25.3, 10.1, 45.7]

# Peak in specific frequency range with windowing
peak = ts.get_peak_freq(window='blackman', min_freq=1.0, max_freq=50.0)  # Returns: 15.2

# Include DC component explicitly
peak_with_dc = ts.get_peak_freq(min_freq=0.0)  # May return 0.0 if DC is strongest
```

### `plot_fft_power(max_rate=np.nan, min_rate=0.0, window=None, show=True, ax=None)`

Plot FFT power spectrum with enhanced windowing and frequency range control.

**Parameters:**
- `max_rate` (float, optional): Maximum frequency to display (Hz). Default: Nyquist frequency
- `min_rate` (float, optional): Minimum frequency to display (Hz). Default: 0.0
- `window` (str, optional): Window function to apply ('hann', 'hamming', 'blackman', None)
- `show` (bool, optional): Whether to display the plot. Default: True
- `ax` (matplotlib.axes.Axes, optional): Axes to plot on

**Returns:**
- `matplotlib.axes.Axes`: The plot axes

**Example:**
```python
# Basic FFT plot
ts.plot_fft_power()

# Plot with frequency range and Hann window
ts.plot_fft_power(min_rate=1.0, max_rate=50.0, window='hann')

# Plot with Blackman window for detailed analysis
ts.plot_fft_power(window='blackman', show=False)
```

---

## Legacy Methods

These methods are maintained for backward compatibility.

### Signal Processing (Legacy)

```python
# Legacy bandpass method
def bandpass_at(self, hp_hz, lp_hz, sampling_rate=None):
    """Legacy bandpass filter method."""
    
# Legacy outlier filtering
def set_outlier_filter(self, frac=0.075, z_threshold=7, it=0, delta_frac=0.0):
    """Set up LOWESS outlier filter.

    frac is the LOWESS bandwidth (fraction of points per local window),
    not the fraction of points expected to be outliers.
    """

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

The pandas Series foundation provides:

- **Rolling Operations**: 2-5x faster using native pandas implementations
- **Time Slicing**: Optimized pandas indexing for time-based queries  
- **Memory Efficiency**: Eliminated dual array storage overhead
- **Statistical Operations**: Vectorized pandas computations
- **Resampling**: Native pandas resampling algorithms
- **FFT with Windowing**: Enhanced spectral analysis with reduced leakage

### Optimization Tips

```python
# For large datasets, consider data type optimization
data = data.astype(np.float32)  # Use float32 if precision allows

# Direct pandas Series operations available
ts = baseTs(data=data, times=times)
ts.describe()          # Statistical summary
ts.quantile(0.95)      # 95th percentile
ts.rolling(10).mean()  # Native pandas rolling
ts.resample('1S').max() # Native pandas resampling

# Enhanced frequency analysis with windowing
freqs, power = ts.get_frequency_content(window='hann')
peak = ts.get_peak_freq(window='blackman', min_freq=1.0)
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

# Include enhanced time-series operations
result = (ts
          .lowpass_filter(cutoff=0.3)
          .rolling_mean(window=30)
          .interpolate_gaps(method='spline', order=2)
          .zscale())

# Enhanced frequency analysis in pipeline
peak_freq = (ts
            .bandpass_filter(low_cutoff=0.1, high_cutoff=0.4)
            .get_peak_freq(window='hann', min_freq=1.0))
```

This API documentation provides comprehensive coverage of all baseTs functionality with the pandas Series foundation, offering enhanced performance and capabilities while maintaining full backward compatibility.