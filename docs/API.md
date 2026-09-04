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
- `freq` (float, optional): Sampling frequency in Hz. Declares an explicit
  rate rather than deriving one from `times`; see the [`freq`](#freq)
  property for how long the declaration is honoured. Defaults to `np.nan`,
  the sentinel meaning "not supplied" — `np.nan` is accepted here without
  raising, but assigning `ts.freq = np.nan` after construction does raise.
- `ts_offset` (float, optional): Time offset in seconds

**Returns:**
- `baseTs`: New baseTs instance

**Raises:**
- `ValueError`: If data and times have different lengths, or if `freq` is
  explicitly given a non-positive, non-finite (other than `NaN`), or
  non-numeric value — e.g. `freq=0.0` or `freq=-1.0`
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
- `freq` (float, optional): Sampling frequency. Passed through to the
  constructor; see [`freq`](#freq) above for how an explicit rate is
  validated and how long it is honoured.
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

Assigning `ts.data = x` replaces the values. With the same length the index is
kept. With a different length the index is resampled over the existing span
(`linspace(first, last, len(x))`, the grid `interpto_samples` builds) — which
needs a span, so growing a series of fewer than two samples raises
`ValidationError` naming the remedy: build a new object with
`baseTs(x, times=...)` or `baseTs(x, freq=...)` (#65). Shrinking to empty is
allowed. To change both values and timestamps, assign `data` first and
`times` second; the `times` setter alone rejects a length mismatch.

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

The constructor upper-cases the `signal_name` keyword it is given, so
`baseTs(..., signal_name="Heart Rate").signal_name` is `"HEART RATE"`. A name
assigned afterwards keeps its case, and every object derived from the
series — a slice, a copy, a processing method, an arithmetic result, a
conversion such as `baseTs(ts)` — carries the source's name as it was. The
keyword is normalised; an inherited name is copied.

`signal_name` and `last_process` are always strings. Assigning `None` stores
`""` and assigning anything else stores its `str`, on the object itself and at
the moment of assignment (they are normalising properties); `del` returns the
label to `""`. Every plot title, axis label and legend entry is built from the
two, so there is no value they can hold that a plot cannot render.

#### `freq`
```python
@property
def freq(self) -> float:
    """Sampling rate in Hz."""
```

Derived from the time index unless you set one explicitly. An explicitly
set rate is honoured only while the index still matches the one it was set
against; any operation that changes the index (`iloc`, `sort_values`,
`resample`, `dropna`) re-derives. Setting a non-positive, non-finite or
non-numeric rate raises `ValueError`. Reads as `NaN` when the index cannot
support a rate — fewer than two samples, a zero or negative span, or a
non-numeric index such as a `DatetimeIndex`.

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
ts_copy.iloc[0] = 999  # Doesn't affect original ts

# NB: ts.data returns a read-only view under pandas Copy-on-Write, so
# `ts_copy.data[0] = 999` raises ValueError. Assign through .iloc, or
# replace the whole array with the setter: `ts_copy.data = new_array`.
```

---

## Signal Processing

**Preconditions shared by the Butterworth filters** (`lowpass_filter`, `highpass_filter`,
`bandpass_filter`, `notch_filter` and their `_at` forms):

- **The data must be gap-free.** These run `scipy.signal.filtfilt`, whose bidirectional pass
  propagates a single NaN across the *entire* output, so four bad samples used to come back as an
  all-NaN series with no warning. Since #48 they raise `InvalidParameterError` instead. Fill gaps
  first with `interpolate_gaps()`. Note that `filter_outliers()` deliberately leaves pre-existing
  gaps as NaN, so a `filter_outliers()` → `lowpass_filter()` chain needs an `interpolate_gaps()`
  between them. A gap at the *start* of the series needs
  `interpolate_gaps(limit_direction='both')`: the default fills forward only, and the error says
  so when that is the case (#77). That holds for the pandas-native methods (`'linear'`, `'time'`,
  `'index'`, `'values'`); the scipy-backed methods (`'cubic'`, `'polynomial'`, `'spline'`, ...)
  leave an edge unfilled or extrapolate a fit. Complex data is accepted: the real and imaginary
  parts are filtered independently.
- `sg_filter()` and `gauss_filter()` are windowed convolutions rather than bidirectional passes, so
  they do **not** raise on NaN: a gap stays a gap, widened by the window. That asymmetry is
  deliberate and pinned by a test.
- Cutoffs must be positive and below Nyquist. For the three single-cutoff filters, `order` must be
  a positive integer (`True`, `4.0` and `'4'` are rejected); `bandpass_filter`'s `order` argument is
  accepted and unused, as its own entry says. Parameter and data rejections raise
  `InvalidParameterError`, which is also a `ValueError`.

### `lowpass_filter(cutoff, order=4)`

Apply low-pass Butterworth filter. Alias for `lowpass_at()`.

**Parameters:**
- `cutoff` (float): Cutoff frequency in Hz (0 < cutoff < Nyquist)
- `order` (int, optional): Filter order. Default: 4

**Returns:**
- `baseTs`: New filtered baseTs object

**Raises:**
- `InvalidParameterError`: If the cutoff is not between 0 and Nyquist, the order is not a positive
  integer, or the data contains NaN or Inf

**Example:**
```python
# Remove high-frequency noise
filtered = ts.lowpass_filter(cutoff=0.3)

# Aggressive filtering
heavily_filtered = ts.lowpass_filter(cutoff=0.1, order=6)
```

### `highpass_filter(cutoff, order=4)`

Apply high-pass Butterworth filter. Alias for `highpass_at()`.

**Parameters:**
- `cutoff` (float): Cutoff frequency in Hz
- `order` (int, optional): Filter order. Default: 4

**Returns:**
- `baseTs`: New filtered baseTs object

**Example:**
```python
# Remove low-frequency trends
detrended = ts.highpass_filter(cutoff=0.05)
```

### `bandpass_filter(low_cutoff, high_cutoff, order=4)`

Apply band-pass Butterworth filter. Alias for `bandpass_at()`.

**Parameters:**
- `low_cutoff` (float): High-pass cutoff frequency in Hz (passed to `bandpass_at` as `hp_hz`)
- `high_cutoff` (float): Low-pass cutoff frequency in Hz (passed to `bandpass_at` as `lp_hz`)
- `order` (int, optional): Accepted for signature compatibility only - the underlying
  bandpass implementation has no order parameter, so this is currently unused.

**Returns:**
- `baseTs`: New filtered baseTs object

**Raises:**
- `InvalidParameterError`: If either band edge is not positive and below the Nyquist
  frequency, or if `low_cutoff` is not strictly less than `high_cutoff`. Both edges are
  checked; before the #30 fix only one was, and which one depended on argument order.

**Example:**
```python
# Extract specific frequency band
bandpassed = ts.bandpass_filter(low_cutoff=0.1, high_cutoff=0.4)
```

### `butterpass_at(hp_freq, lp_freq, inplace=False)`

Apply a band-pass Butterworth filter. Alias for `bandpass_at()`.

**Parameters:**
- `hp_freq` (float): High-pass cutoff frequency in Hz (passed to `bandpass_at` as `hp_hz`)
- `lp_freq` (float): Low-pass cutoff frequency in Hz (passed to `bandpass_at` as `lp_hz`)
- `inplace` (bool, optional): If True, modifies the existing object. Default: False

**Returns:**
- `baseTs`: New filtered baseTs object

**Example:**
```python
# Keep 1-10 Hz
banded = ts.butterpass_at(hp_freq=1.0, lp_freq=10.0)
```

**Note:** Prior to the #27 fix this method raised `TypeError` on every call, so
it has no legacy behavior to preserve. History records the `bandpass_at` entry.

### `notch_filter(freq, order=4)`

Apply notch filter to remove specific frequency. Alias for `notch_at()`.

**Parameters:**
- `freq` (float): Frequency to remove, in Hz
- `order` (int, optional): Filter order. Default: 4

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

### `detect_outliers(method='zscore', threshold=3.0)`

Detect outliers using statistical methods.

Note: this is a separate, stateless statistical outlier detector distinct from the
LOWESS-based workflow (`set_outlier_filter()` + `filter_outliers()`, see above).
Neither calls the other - pick whichever suits your data. There is no
`outlier_indices()` method despite the name similarity; this method returns a
boolean mask, not an index array.

**Parameters:**
- `method` (str): Detection method ('zscore', 'iqr', 'modified_zscore'). Default: 'zscore'
- `threshold` (float): Threshold for outlier detection (IQR multiplier for `'iqr'`,
  z-score/modified z-score threshold otherwise). Default: 3.0

**Returns:**
- `np.ndarray`: Boolean array the same length as the series - `True` where a point
  is an outlier

**Example:**
```python
# Z-score method (default)
outlier_mask = ts.detect_outliers(method='zscore', threshold=3)

# IQR method
outlier_mask = ts.detect_outliers(method='iqr', threshold=1.5)

# Modified Z-score method
outlier_mask = ts.detect_outliers(method='modified_zscore', threshold=3.5)

print(f"Found {outlier_mask.sum()} outliers")
```

### `remove_outliers(method='zscore', threshold=3.0, inplace=False)`

Remove points flagged by `detect_outliers()` from the time series.

**Parameters:**
- `method` (str): Detection method passed to `detect_outliers` ('zscore', 'iqr', 'modified_zscore')
- `threshold` (float): Threshold passed to `detect_outliers`
- `inplace` (bool, optional): If True, modifies existing object. Otherwise returns new object.

**Returns:**
- `baseTs`: New baseTs object with outliers removed

**Example:**
```python
# Remove outliers using the z-score method
cleaned = ts.remove_outliers(method='zscore', threshold=3)

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
- `**kwargs`: Passed to `pandas.Series.interpolate`. The one to know about is `limit_direction`:
  pandas' default `'forward'` fills nothing before the first valid sample, so **a gap at the start
  of the series survives the default call** and the spectral and filter guards reject the result
  with the same message that named this method (#77). Pass `limit_direction='both'` to extend the
  first valid value back over the edge. That is a constant extension, not an interpolation, which
  is why it is not the default. A trailing gap is already extended by the default. These hold for
  the pandas-native methods (`'linear'`, `'time'`, `'index'`, `'values'`). The scipy-backed
  methods differ at an edge in either direction: `'cubic'`, `'quadratic'`, `'slinear'`, `'zero'`,
  `'nearest'`, `'polynomial'`, `'krogh'`, `'piecewise_polynomial'`, `'akima'` and
  `'from_derivatives'` leave it unfilled, while `'spline'`, `'pchip'`, `'cubicspline'` and
  `'barycentric'` extrapolate their fit over it. A `limit` caps the edge fill like any other. A
  series with no valid sample cannot be filled at all, and the guards say so instead of naming
  this method.

**Returns:**
- `baseTs`: New baseTs object with interpolated data

**Example:**
```python
# Linear interpolation
interpolated = ts.interpolate_gaps(method='linear')

# A gap at the start of the series needs the edge fill (constant, not interpolated)
edge_filled = ts.interpolate_gaps(limit_direction='both')

# Polynomial interpolation with order 3
poly_interp = ts.interpolate_gaps(method='polynomial', order=3)

# Spline interpolation with limit
spline_interp = ts.interpolate_gaps(method='spline', order=2, limit=10)

# Time-based interpolation (works with numeric indices)
time_interp = ts.interpolate_gaps(method='time')
```

### `resample(freq, method='mean', **kwargs)`

Resample the time series to a different sampling rate.

This overrides `pandas.Series.resample`, and has to: a baseTs carries a plain
numeric (float seconds) index, and pandas' `resample` requires a `DatetimeIndex`,
`TimedeltaIndex` or `PeriodIndex`. Calling pandas' version directly would raise
`TypeError`. This method converts the numeric index to a timedelta, resamples,
aggregates, and converts back.

**Parameters:**
- `freq` (str): Target interval as a pandas offset string — `'1s'`, `'100ms'`,
  `'0.5s'`, `'1min'`, `'h'`, `'D'`. Must be a **fixed** frequency; non-fixed
  offsets such as `'W'` or `'M'` raise `ValueError`, because the underlying index
  is a timedelta rather than a calendar.
- `method` (str, optional): Aggregation applied to each bin — `'mean'`,
  `'median'`, `'sum'`, `'min'`, `'max'`, `'std'`. Default: `'mean'`
- `**kwargs`: Passed through to the pandas aggregation

**Returns:**
- `baseTs`: New resampled baseTs object

**Aggregate with `method=`, not by chaining.** The aggregation happens *inside*
this call, so `ts.resample('1s').max()` does not mean "max per one-second bin" —
it resamples using the default `mean`, then takes a single scalar max over those
means. Pass the aggregation you want:

```python
# Downsample to 1 Hz, averaging each bin
ts_1hz = ts.resample('1s')                    # method='mean' by default

# Maximum within each one-second bin
ts_peaks = ts.resample('1s', method='max')    # returns a baseTs

# NOT this - returns a single float, not a series
wrong = ts.resample('1s').max()

# Upsample to 100 Hz
ts_100hz = ts.resample('10ms')
```

### `interpto_hz(new_freq, kind='linear', inplace=False)`

Resample onto a grid with exactly `1/new_freq` spacing, starting at the
source's first timestamp. The final sample may fall short of the source's
last timestamp rather than landing on it.

**Parameters:**
- `new_freq` (float): The desired sampling rate in Hz. Must be positive and finite.
- `kind` (str, optional): Interpolation type passed to `scipy.interpolate.interp1d`. Default: `'linear'`
- `inplace` (bool, optional): If True, modifies existing object. Otherwise returns new object

**Returns:**
- `baseTs`: Interpolated data on an exact `new_freq` grid

**Raises:**
- `ValueError`: If `new_freq` is not a positive finite rate, if the source
  time base is degenerate, or if the requested rate yields fewer than two samples

**Example:**
```python
ts_200hz = ts.interpto_hz(200)   # a 10.0 s series returns 2001 samples, not 2000
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

**Raises:**
- `ValueError`: Unusable sampling frequency, unknown window function, or NaN/Inf in the data

**Preconditions:**
- **The data must be gap-free.** An FFT over data containing NaN returns an *all-NaN* spectrum, not
  a degraded one, so this raises rather than handing back nonsense. Fill gaps first with
  `interpolate_gaps()`. Note that `filter_outliers()` deliberately leaves pre-existing gaps as NaN,
  so a `filter_outliers()` → `get_frequency_content()` chain needs an `interpolate_gaps()` between
  them. A gap at the *start* of the series needs `interpolate_gaps(limit_direction='both')`: the
  default fills forward only, and the error says so when that is the case (#77). That holds for
  the pandas-native methods (`'linear'`, `'time'`, `'index'`, `'values'`); the scipy-backed
  methods (`'cubic'`, `'polynomial'`, `'spline'`, ...) leave an edge unfilled or extrapolate a fit.

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

**Raises:**
- `ValueError`: Unusable sampling frequency, or NaN/Inf in the data

Both come from `get_frequency_content()`, which this calls. The data check matters here in
particular: `find_peaks` returns indices over an all-NaN spectrum quite happily, so before this
guard existed a single NaN produced a confident, entirely meaningless frequency.

**Example:**
```python
# Basic peak frequency (excludes DC component by default)
peak = ts.get_peak_freq()  # Returns: 25.3

# Gappy data must be filled first - this raises otherwise
peak = ts.interpolate_gaps().get_peak_freq()

# Top 3 peaks with Hanning window
peaks = ts.get_peak_freq(num_pks=3, window='hann')  # Returns: [25.3, 10.1, 45.7]

# Peak in specific frequency range with windowing
peak = ts.get_peak_freq(window='blackman', min_freq=1.0, max_freq=50.0)  # Returns: 15.2

# Include DC component explicitly
peak_with_dc = ts.get_peak_freq(min_freq=0.0)  # May return 0.0 if DC is strongest
```

### `relative_band_power(low_freq=0.01, high_freq=0.1, ratio='power', window=None, details=False)`

Compute the relative power (or amplitude) in a frequency band — the quantity behind fractional
amplitude of low-frequency fluctuations (fALFF) and relative band power in EEG/HRV work.

The band defaults to 0.01–0.1 Hz, a common low-frequency band for resting-state fMRI and other slow
physiological fluctuations, so the common case is a bare call. It is one convention among several:
Zou et al. (2008) computed fALFF over 0.01–0.08 Hz, and the HRV literature's LF band is
0.04–0.15 Hz. Pass both edges to measure a different band. The default does not relax the preconditions below: the upper
edge still has to sit at or below Nyquist, so a series sampled below 0.2 Hz raises, and at least
one FFT bin still has to fall inside the band.

**Parameters:**
- `low_freq` (float, optional): Lower band edge in Hz (inclusive). Default: 0.01
- `high_freq` (float, optional): Upper band edge in Hz (inclusive). Default: 0.1
- `ratio` (str, optional): `'power'` (variance fraction, default) or `'amplitude'` (classic fALFF)
- `window` (str, optional): Window function to apply ('hann', 'hamming', 'blackman', None)
- `details` (bool, optional): If True, return a `BandPowerResult` breakdown. Default: False

**Returns:**
- `float`: The relative band power, or a `BandPowerResult` if `details=True`

**Choosing a convention.** The two are different measurements, not stylistic variants:

| | `ratio='power'` | `ratio='amplitude'` |
|---|---|---|
| Sums | `\|X(f)\|²` | `\|X(f)\|` |
| Means | Fraction of signal *variance* in band (Parseval-exact) | Classic fALFF (Zou et al., 2008) |
| Across sampling rates | Roughly stable | Falls sharply — denominator grows with the noise-bin count |
| Use when | You want a variance decomposition comparable across recordings | You need to reproduce published fALFF values |

For a fixed 0.05 Hz signal in noise, the amplitude ratio drops roughly tenfold between fs = 0.5 Hz
and fs = 10 Hz while the power ratio barely moves. This is the standard caveat on comparing fALFF
across acquisitions with different TR or bandwidth.

**The null is not zero.** For white noise both conventions converge on `n_band_bins / n_total_bins`.
Use `details=True` and compare `ratio` against `bin_fraction` to judge whether a value reflects real
band-specific structure.

**DC handling.** The 0 Hz bin is always excluded from both numerator and denominator.
`get_frequency_content()` does not demean, so on a signal with a non-zero mean the DC bin holds the
overwhelming majority of raw power — excluding it keeps the result meaningful even if you have not
detrended upstream.

**Preconditions:**
- **Detrend first** on trending data: `ts.detrend('linear')`. This method does not detrend for you.
- **Resample to a uniform grid first** if the series is irregular, since `freq` is an *effective*
  sampling frequency.
- **The series must be long enough.** Frequency resolution is `1 / duration`, so a 0.01 Hz lower
  edge needs at least 100 s of data for a single bin. A band narrower than the resolution raises
  `ValueError`.

**Raises:**
- `ValueError`: Invalid band, band above Nyquist, band narrower than the frequency resolution,
  NaN/Inf in the data, or an effectively constant signal

**Example:**
```python
# Fraction of variance in the default 0.01-0.1 Hz band
ratio = ts.detrend('linear').relative_band_power()  # Returns: 0.717

# A different band, here the HRV low-frequency band
ratio = ts.relative_band_power(0.04, 0.15)

# Classic fALFF convention (or use falff(), which defaults to it)
falff = ts.relative_band_power(ratio='amplitude')  # Returns: 0.147

# Full breakdown, including the white-noise null
res = ts.relative_band_power(details=True)
print(res.ratio, res.bin_fraction)  # 0.717 0.092  -> well above the null
```

### `falff(low_freq=0.01, high_freq=0.1, ratio='amplitude', window=None, details=False)`

Fractional amplitude of low-frequency fluctuations. Convenience wrapper around
`relative_band_power()` using the convention from Zou et al. (2008),
*J Neurosci Methods* 172(1):137-141. Both default to the same 0.01–0.1 Hz band, which is wider
than the 0.01–0.08 Hz that paper used; pass `(0.01, 0.08)` to reproduce it.

What differs is the convention, and the split is deliberate: `relative_band_power()` defaults to
`ratio='power'` as the better-behaved general-purpose measure, while `falff()` defaults to
`ratio='amplitude'` so it reproduces published values.

**Parameters:**
- `low_freq` (float, optional): Lower band edge in Hz. Default: 0.01
- `high_freq` (float, optional): Upper band edge in Hz. Default: 0.1
- `ratio` (str, optional): `'amplitude'` (default) or `'power'`
- `window` (str, optional): Window function to apply ('hann', 'hamming', 'blackman', None)
- `details` (bool, optional): If True, return a `BandPowerResult` breakdown. Default: False

**Returns:**
- `float`: The fALFF value, or a `BandPowerResult` if `details=True`

**Example:**
```python
# Classic fALFF on a detrended signal
value = ts.detrend('linear').falff()  # Returns: 0.147

# The band Zou et al. (2008) used
value = ts.falff(0.01, 0.08)
```
### `plot` — line plot, or the pandas plotting accessor

`ts.plot` is a hybrid: **calling** it draws the baseTs line plot (it is an alias
for `plot_line`), and **attribute access** falls through to the pandas `.plot`
accessor.

It works this way because `pandas.Series.plot` is an *object*, not a method.
Aliasing `plot` to a plain method used to shadow it, making `ts.plot.line()`,
`.bar()`, `.hist()` and the other pandas plot kinds unreachable.

```python
# Calling it: unchanged baseTs behaviour
ts.plot()
ts.plot(lowess=True, title="Signal", ax=ax)

# Attribute access: the pandas plot kinds
ts.plot.bar()
ts.plot.hist(bins=30)
ts.plot.kde()
```

Available pandas kinds: `line`, `bar`, `barh`, `hist`, `box`, `kde`, `density`,
`area`, `pie`, `scatter`, `hexbin`.

`lowess=True` requires a fit on *this* object and raises `ValueError` if there
is none. A fit comes from `filter_outliers()` or `lowess_detrend()`, and does
not survive an operation that changes the index — a slice of a filtered series
has no fit of its own (#20). Run the filter on the slice, or slice after
plotting.

### `plot_fft_power(max_rate=np.nan, min_rate=0.0, window=None, show=True, ax=None)`

Plot FFT power spectrum with enhanced windowing and frequency range control.

**Parameters:**
- `max_rate` (float, optional): Maximum frequency to display (Hz). Default: Nyquist frequency
- `min_rate` (float, optional): Minimum frequency to display (Hz). Default: 0.0
- `window` (str, optional): Window function to apply ('hann', 'hamming', 'blackman', None)
- `show` (bool, optional): Whether to display the plot. Default: True
- `ax` (matplotlib.axes.Axes, optional): Axes to plot on
- `highlight_band` (tuple, optional): `(low_freq, high_freq)` in Hz to shade on the plot, e.g.
  `(0.01, 0.1)` to mark the default `relative_band_power()` band

**Returns:**
- `matplotlib.axes.Axes`: The plot axes

**Raises:**
- `ValueError`: If the sampling rate is unusable (NaN, zero or negative), if the data contains
  NaN or Inf, if `window` names an unknown window function, if `min_rate` or `max_rate` is not a
  real finite scalar (`max_rate` also accepts `np.nan`, its "use Nyquist" sentinel), if
  `[min_rate, max_rate]` selects no frequency bins, or if `highlight_band` is not a strictly
  increasing pair of real finite frequencies

Every rejected input raises `ValueError`, so one `except ValueError` covers the function.

A rejected call draws nothing — no figure is created, and a caller-supplied `ax` is returned
untouched. Until #34 these errors were swallowed and drawn as text on the axes, so a failing call
returned a normal `Axes` and a batch pipeline saved a bogus figure with a success exit code.

Gappy data needs an `interpolate_gaps()` first: since #36 `filter_outliers` leaves the gaps it did
not create as NaN, and since #28 the spectral guards reject them.

```python
ts.filter_outliers().interpolate_gaps().plot_fft_power()
```

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

def plot_fft_power(self, max_rate=np.nan, show=False, ax=None):
    """Plot FFT power spectrum."""
```

> The `max_rate=None` default shown here previously was never the real
> signature, and since #34 that call raises: `np.nan` is the sentinel for "use
> Nyquist". See the current entry above for the full parameter list.

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
ts.resample('1s', method='max')  # baseTs resampling; see resample() above

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
          .remove_outliers(method='zscore', threshold=3)
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