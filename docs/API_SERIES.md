# Enhanced Pandas Series API Documentation

This document describes the new pandas-powered methods available in baseTs, built on the pandas Series foundation.

## Overview

baseTs now inherits directly from pandas Series via the TimeSeriesData class, providing access to:
- 270+ native pandas Series methods
- Enhanced time-series specific operations
- Optimized rolling, resampling, and statistical functions
- Native pandas integration for time-based operations

The examples below share one setup: a 100 Hz sine with a little noise
over 10 seconds, and a second series on the same time base.

```python
import numpy as np
import pandas as pd
from baseTs import baseTs

times = np.arange(1000) / 100.0          # 10 s at exactly 100 Hz
data = np.sin(2 * np.pi * 0.5 * times) + 0.1 * np.random.randn(1000)
ts = baseTs(data, times, freq=100.0, signal_name="sensor")
ts1 = ts
ts2 = baseTs(np.cos(2 * np.pi * 0.5 * times), times, freq=100.0, signal_name="reference")
```

## Enhanced Time-Series Methods

### Resampling and Frequency Conversion

#### `resample(freq, method='mean', **kwargs)`

Resample time series to a different frequency using pandas resampling.

**Parameters:**
- `freq` (str): Target frequency string (e.g., '1s', '100ms', '0.1s')
- `method` (str): Aggregation method ('mean', 'median', 'sum', 'min', 'max', 'std')
- `**kwargs`: Additional arguments passed to pandas resample

**Returns:** New baseTs object with resampled data

**Examples:**
```python
# Downsample to 1Hz
ts_1hz = ts.resample('1s', method='mean')

# Upsample to 100Hz  
ts_100hz = ts.resample('10ms', method='mean')

# Resample with custom aggregation
ts_max = ts.resample('5s', method='max')
```

### Gap Filling and Interpolation

`is_interpolated` means one thing across the package (#90): at least one value
in the series is an interpolated estimate rather than a measured sample. The
regridders (`interpto_hz`, `interpto_samples`, `interp_to_uniform_grid`)
always set it, since every value is re-estimated; `interpolate_gaps` and
`interpolate_missing` set it when they filled a gap; `filter_outliers` sets it
when it replaced an outlier or filled an input gap. A call that estimated
nothing leaves the flag as it found it, and nothing resets it: a series
derived from interpolated values is still built on estimates.

#### `interp_to_uniform_grid(new_grid=None, kind='linear', inplace=True, fill_value=None, max_gap=None)`

Interpolate onto a uniform grid, by default the series' own span at its
effective rate. Two keywords control what happens where there is no data to
interpolate between:

**Parameters:**
- `new_grid` (np.array, optional): The target grid. Must be monotonically increasing.
- `kind` (str): scipy `interp1d` kind ('linear', 'cubic', ...).
- `inplace` (bool): If True, modifies existing object. Otherwise returns new object.
- `fill_value` (float, optional): Value for grid points outside
  `[times[0], times[-1]]`. Default `None` raises `ValueError` on such a point.
  `np.nan` pads a short trial out to a longer common grid, which is how ragged
  trials get onto one index for `baseDf.from_series`.
- `max_gap` (float, optional): Widest interval between consecutive source
  samples, in seconds, that may be bridged. Grid points strictly inside a wider
  interval are left as NaN; a point landing exactly on a sample keeps it.
  Default `None` bridges every interval, however wide.

**Returns:** baseTs on the new grid, `is_interpolated` and `is_uniform_grid`
set. The history entry counts padded and blanked points when either is non-zero.

**Raises:** `ValidationError` for a non-numeric `fill_value` or a non-positive
`max_gap`; `ValueError` for a bad grid.

`max_gap` is the opposite of `interpolate_gaps()`: that fills holes, this
refuses to draw a line across one. Use it when the hole is a real absence of
recording, such as the post-crash period in a cpCST trial, and the average
across trials should report fewer contributors there rather than a fabricated
ramp. The padded or blanked series carries NaN, and the filters refuse gapped
data, so trim to the covered span before filtering an average built this way.

```python
import numpy as np
from baseTs import baseTs, baseDf

grid = np.arange(0, 3.0, 0.1)
trials = []
for n in (10, 20, 30):                      # trials of different lengths
    t = np.arange(n) * 0.1
    trials.append(baseTs(np.sin(t), t))
stacked = [tr.interp_to_uniform_grid(grid, fill_value=np.nan, max_gap=0.5,
                                     inplace=False) for tr in trials]
frame = baseDf.from_series(stacked, labels=["t0", "t1", "t2"])
mean = frame.average(skipna=True, min_count=2)   # NaN past the second-longest trial
```

#### `interpolate_gaps(method='linear', limit=None, inplace=False)`

Interpolate missing values (NaN) in the time series.

**Parameters:**
- `method` (str): Interpolation method ('linear', 'time', 'spline', 'polynomial', etc.)
- `limit` (int, optional): Maximum number of consecutive NaN values to interpolate
- `inplace` (bool): If True, modifies existing object. Otherwise returns new object.

**Returns:** Interpolated baseTs object

**Examples:**
```python
# Linear interpolation
ts_filled = ts.interpolate_gaps(method='linear')

# Spline interpolation with limit
ts_spline = ts.interpolate_gaps(method='spline', limit=10)

# Time-based interpolation
ts_time = ts.interpolate_gaps(method='time')
```

### Time Series Alignment

#### `align_with(other, method='outer')`

Align two time series on a common time index.

**Parameters:**
- `other` (baseTs): Another baseTs object to align with
- `method` (str): Join method ('outer', 'inner', 'left', 'right')

**Returns:** Tuple of (aligned_self, aligned_other) as baseTs objects

**Examples:**
```python
# Outer join alignment (union of time indices)
aligned1, aligned2 = ts1.align_with(ts2, method='outer')

# Inner join alignment (intersection of time indices)
aligned1, aligned2 = ts1.align_with(ts2, method='inner')
```

### Time Shifting

#### `shift_time(periods, inplace=False)`

Shift the time series by a number of periods.

**Parameters:**
- `periods` (int): Number of periods to shift (positive = forward, negative = backward)
- `inplace` (bool): If True, modifies existing object. Otherwise returns new object.

**Returns:** Time-shifted baseTs object

**Examples:**
```python
# Shift forward by 10 periods
ts_forward = ts.shift_time(periods=10)

# Shift backward by 5 periods
ts_backward = ts.shift_time(periods=-5)
```

### Correlation Analysis

#### `correlation_with(other, method='pearson')`

Calculate correlation with another time series.

**Parameters:**
- `other` (baseTs): Another baseTs object
- `method` (str): Correlation method ('pearson', 'kendall', 'spearman')

**Returns:** Correlation coefficient (float)

**Examples:**
```python
# Pearson correlation
pearson_corr = ts1.correlation_with(ts2, method='pearson')

# Spearman rank correlation
spearman_corr = ts1.correlation_with(ts2, method='spearman')
```

### Outlier Detection

#### `detect_outliers(method='zscore', threshold=3.0)`

Detect outliers using statistical methods.

**Parameters:**
- `method` (str): Detection method ('zscore', 'iqr', 'modified_zscore')
- `threshold` (float): Threshold for outlier detection

**Returns:** Boolean array indicating outlier positions

**Examples:**
```python
# Z-score based outlier detection
outliers_z = ts.detect_outliers(method='zscore', threshold=2.5)

# Interquartile range (IQR) method
outliers_iqr = ts.detect_outliers(method='iqr', threshold=1.5)

# Modified z-score method
outliers_mod = ts.detect_outliers(method='modified_zscore', threshold=3.5)
```

### Frequency Analysis

#### `get_frequency_content(window=None)`

Get frequency domain representation using pandas-optimized FFT.

**Parameters:**
- `window` (str, optional): Window function to apply ('hann', 'hamming', 'blackman', None)

**Returns:** Tuple of (frequencies, power_spectrum)

**Raises:** `ValueError` on an unusable sampling frequency, an unknown window function, or NaN/Inf
in the data. An FFT over data containing NaN returns an all-NaN spectrum, so fill gaps first with
`interpolate_gaps()`. That fills NaN only: an Inf needs `ts.replace([np.inf, -np.inf], np.nan)`
before it, and the error says which it found.

**Examples:**
```python
# Basic FFT
freqs, power = ts.get_frequency_content()

# With Hann window
freqs, power = ts.get_frequency_content(window='hann')

# With Blackman window
freqs, power = ts.get_frequency_content(window='blackman')
```

## Enhanced Rolling Operations

All rolling operations now use native pandas implementations for optimal performance:

#### `rolling_mean(window, center=True, inplace=False)`
#### `rolling_std(window, center=True, inplace=False)`  
#### `rolling_median(window, center=True, inplace=False)`
#### `rolling_max(window, center=True, inplace=False)`
#### `rolling_min(window, center=True, inplace=False)`

**Parameters:**
- `window` (int): Size of the rolling window (number of samples)
- `center` (bool): Whether to center the window
- `inplace` (bool): If True, modifies existing object. Otherwise returns new object.

**Examples:**
```python
# Rolling mean with 50-sample window
ts_smooth = ts.rolling_mean(window=50, center=True)

# Rolling standard deviation
ts_std = ts.rolling_std(window=20)

# Rolling maximum
ts_max = ts.rolling_max(window=10)
```

## Enhanced Time Slicing

#### `time_slice(start_time=None, end_time=None, inplace=False)`

Enhanced time-based slicing using pandas indexing.

**Parameters:**
- `start_time` (float, optional): Start time (if None, uses beginning)
- `end_time` (float, optional): End time (if None, uses end)
- `inplace` (bool): If True, modifies existing object. Otherwise returns new object.

**Examples:**
```python
# Extract specific time range
segment = ts.time_slice(start_time=10.0, end_time=50.0)

# Extract from start to specific time
beginning = ts.time_slice(end_time=25.0)

# Extract from specific time to end
ending = ts.time_slice(start_time=75.0)
```

## Enhanced Statistics

#### `get_statistics()`

Get comprehensive statistics using pandas describe() for efficient calculation.

**Returns:** Dictionary containing statistical measures

**Example:**
```python
stats = ts.get_statistics()
# Returns: {
#     'count': 1000,
#     'mean': 0.123,
#     'std': 0.456, 
#     'min': -2.1,
#     'max': 2.3,
#     'median': 0.098,
#     'q25': -0.234,
#     'q75': 0.567,
#     'duration': 10.0,
#     'frequency': 100.0,
#     'sample_rate': 100.0
# }
```

## Native Pandas Series Access

Since baseTs now inherits from pandas Series, you have direct access to all pandas methods:

```python
# Native pandas operations
ts.describe()          # Statistical summary
ts.quantile(0.95)      # 95th percentile
ts.rolling(10).mean()  # Pandas rolling mean
ts.resample('1s', method='max')  # baseTs override, not pandas resample
ts.interpolate()       # Pandas interpolation
ts.dropna()            # Remove NaN values
ts.fillna(0)           # Fill NaN with 0
ts.plot()              # Pandas plotting
```

## Backward Compatibility

All existing baseTs methods work unchanged:

```python
# Legacy methods still work exactly the same
ts.lowpass_at(cutoff=2.0)
ts.bandpass_at(hp_hz=0.1, lp_hz=5.0)  
ts.filter_outliers()
ts.zscale()
ts.normalize_range()
```

## Performance Notes

The new pandas-based implementation provides:

- **Rolling Operations**: 2-5x faster using native pandas implementations
- **Time Slicing**: Optimized pandas indexing for time-based queries
- **Memory Efficiency**: Eliminated dual array storage overhead
- **Statistical Operations**: Vectorized pandas computations
- **Resampling**: Native pandas resampling algorithms

## Integration Examples

### Complete Workflow

```python
import numpy as np
from baseTs import baseTs

# Create time series
times = np.arange(10000) / 100.0         # 100 s at exactly 100 Hz
data = np.sin(2*np.pi*0.5*times) + 0.1*np.random.randn(10000)
ts = baseTs(data, times, freq=100.0, signal_name="example")

# Apply traditional processing
ts_filtered = ts.bandpass_at(hp_hz=0.1, lp_hz=2.0)
# interpolate_gaps because filter_outliers leaves pre-existing gaps as NaN,
# and get_frequency_content below rejects NaN input.
ts_clean = ts_filtered.filter_outliers().interpolate_gaps()

# Apply new enhanced processing  
ts_smooth = ts_clean.rolling_mean(window=50)
ts_resampled = ts_smooth.resample('1s', method='mean')
outliers = ts_resampled.detect_outliers(method='iqr')

# Analysis
stats = ts_resampled.get_statistics()
freqs, power = ts_resampled.get_frequency_content(window='hann')

print(f"Processed {len(ts)} → {len(ts_resampled)} samples")
print(f"Found {np.sum(outliers)} outliers")
print(f"Peak frequency: {freqs[np.argmax(power)]:.2f} Hz")
```

### Advanced Analysis Workflow

```python
# Cross-correlation analysis
ts1 = baseTs(np.sin(2*np.pi*0.5*times), times, freq=100.0, signal_name="signal1")
ts2 = baseTs(np.cos(2*np.pi*0.5*times), times, freq=100.0, signal_name="signal2")

correlation = ts1.correlation_with(ts2, method='pearson')
aligned_ts1, aligned_ts2 = ts1.align_with(ts2, method='inner')

# Frequency analysis with windowing
freqs, power = ts.get_frequency_content(window='hann')
peak_freq = ts.get_peak_freq()

# Gap filling and interpolation
ts_with_gaps = ts.copy()
# Introduce gaps. Note: ts.data returns a read-only view under pandas
# Copy-on-Write, so `ts.data[100:110] = np.nan` raises ValueError. Assign
# through .iloc, or use set_indices_to_nan_and_interpolate() to do both
# steps at once.
ts_with_gaps.iloc[100:110] = np.nan
ts_filled = ts_with_gaps.interpolate_gaps(method='spline')

# Or, in a single step:
ts_filled = ts.set_indices_to_nan_and_interpolate(list(range(100, 110)))

print(f"Correlation: {correlation:.3f}")
print(f"Peak frequency: {peak_freq} Hz")
```

### Pandas Integration

```python
# Direct access to pandas functionality, on a daily series built from a DatetimeIndex.
# The constructor converts the dates to seconds since the first one (#100), so
# the index is numeric and every baseTs method reads it; the dates themselves
# are the `datetimes` accessor
dates = pd.date_range('2023-01-01', periods=365, freq='D')
daily = baseTs(np.random.randn(365), times=dates, signal_name="sensor_data")
assert daily.times[1] == 86400.0 and daily.datetimes[1] == dates[1]

# Use pandas methods directly, keyed on the dates
monthly_stats = daily.groupby(daily.datetimes.month).agg(['mean', 'std', 'min', 'max'])
quantiles = daily.quantile([0.1, 0.25, 0.5, 0.75, 0.9])

# Fixed-length bins resample from the origin and stay a baseTs
weekly_means = daily.resample('7D')

# Convert to DataFrame for complex analysis
df = daily.to_frame('value')
df['month'] = daily.datetimes.month
df['day_of_week'] = daily.datetimes.dayofweek

# A calendar-anchored bin ('W', 'ME') needs a DatetimeIndex: pandas' own
# resample, on a frame or Series over the dates
calendar_weeks = df.set_index(daily.datetimes)['value'].resample('W').mean()

# Seasonal decomposition using pandas
seasonal_means = df.groupby('month')['value'].mean()
weekly_patterns = df.groupby('day_of_week')['value'].mean()
```

## TimeSeriesData Class Reference

### `freq` Property

**`freq`** *(property, float)* — the sampling rate in Hz. Derived from the
time index unless you set one explicitly. An explicitly set rate is honoured
only while the index still matches the one it was set against; any operation
that changes the index (`iloc`, `sort_values`, `resample`, `dropna`) re-derives.
Setting a non-positive, non-finite or non-numeric rate raises `ValueError`.
Reads as `NaN` when the index cannot support a rate — fewer than two samples,
a zero or negative span, or a non-numeric index (an object index of strings;
a `DatetimeIndex` is converted to seconds at the constructor, #100, and
derives normally).

### `datetimes` Property

**`datetimes`** *(property, `pd.DatetimeIndex`)* — the index as calendar
stamps. The index itself is always seconds; a series built from a
`DatetimeIndex` counts them from its first stamp and records that stamp as
`ts_offset` (epoch seconds), and this property is the way back:
`ts.groupby(ts.datetimes.month)`, `pd.Series(ts.values,
index=ts.datetimes).rolling('1h')`. Raises `ValueError` on a series with no
origin — one built from seconds or a `TimedeltaIndex` and never given one via
`set_timestamp_offset`. Naive UTC: a timezone-aware index is recorded as its
UTC instant.

### Metadata Attributes

The TimeSeriesData class preserves metadata through pandas' `_metadata` attribute:

```python
_metadata = [
    '_freq_declaration',      # An explicitly set sampling rate, plus the
                               # index token it was set against (internal;
                               # read/write the public `freq` property instead)
    'signal_name',            # Name of the signal
    'history',                # Processing history list
    'is_filtered',            # Whether the data has been filtered
    'is_interpolated',        # Whether at least one value is an interpolated
                               # estimate rather than a measured sample (#90)
    'is_uniform_grid',        # Whether the data is on a uniform time grid
    'ts_offset',              # The origin the index's seconds are counted
                               # from, in epoch seconds (#100)
    'has_timestamp_offset',   # Whether an origin applies (`datetimes` reads it)
    '_origin_index',          # The index the origin was declared against;
                               # `datetimes` refuses an index not drawn from it
    'outlier_indices',        # Positions of the samples filtered as outliers
    'lowess_fit',             # LOWESS fit data (if applicable)  — one value
                               # per sample; both are positional, see below
    'last_process',           # Last processing operation performed
    'is_outlier_filtered',    # Whether filter_outliers has been applied
    'outlier_filter',         # The LowessOutlierFilter instance used to filter outliers
]
```

`freq` is no longer one of these entries — see [`freq` Property](#freq-property)
above. `__finalize__`, `copy()` and arithmetic all just carry
`_freq_declaration` along like any other metadata entry; it is the `freq`
property getter that re-checks it against the live index on every read and
decides whether it still applies.

`outlier_indices` and `lowess_fit` are the two entries that do *not* simply
travel. They describe the samples by position, so they are dropped to `None` on
any object whose index is not the one they were computed against (#20) — a
slice, a `dropna`, a `resample`, a `sort_values`, arithmetic against a series
on a different index, or an in-place `ts.times = ...`, `ts.index = ...` or
`shift_time(inplace=True)`. They are also dropped on any object whose
**values** are not the ones they were assigned against (#40) — `ts.data = x`,
`ts.iloc[i] = v`, `ts += 1`, `sg_filter`, the frequency filters, `detrend`,
`zscale`, `apply_function`, `ts * 2`, `rolling(n > 1)`. Operations that leave
both the index and the values alone — `copy`, `+ 0.0`, `rolling(1).mean()`,
`clip` inside the data's range, `interpolate_gaps()` on gap-free data — keep
both, and `outlier_indices` is copied rather than shared so appending through
a derived object cannot rewrite the parent's record. Unlike `freq` they cannot
be re-derived on read, which is why the index check is full index equality
rather than the cheaper `(len, first, last)` token: an interior permutation
leaves that token intact while moving every sample they describe.

What "the values they were assigned against" means: the values on the object
at the moment the slot was set, not the values the fit was computed from.
`filter_outliers` computes its fit from the unfiltered data and assigns it
after replacing the data; `lowess_detrend`'s fit is the trend it removed, and
it re-asserts `outlier_indices` after detrending because its docstring
promises they survive. A producer writes the data first and the slot second,
and the stamp records what it left behind — the pairing `qc_plot` draws.

The rule is enforced **on read, in one place** — the properties themselves —
rather than at every point an index or a value can change. `_metadata`
therefore carries the private slots `_lowess_fit` and `_outlier_indices`, each
holding `(value, index_it_describes, values_it_describes)`; pandas copies that
triple verbatim like any other metadata entry, and the property getter
re-checks it against the live index and the live values on every access. The
values stamp is an immutable `pd.Index` built from a copy of the values, so no
in-place write can reach into it, and `Index.equals` gives the right equality:
NaN equals NaN in the same place, `float32` against `float64` of the same
numbers is equal, and object or nullable values compare without raising.
This is the same shape as `_freq_declaration`, with one difference: `freq`
compares a `(len, first, last)` token because those are exactly the three
inputs its derivation reads, while these two are positional, so an interior
permutation must invalidate them and the check is full `Index.equals`.

A valid read costs O(n) in the values every time — 0.5 ms per million samples,
measured — because an in-place write keeps the array's identity while changing
its contents, so nothing cheaper can prove the values unchanged. The index
half has an identity fast path after the first read and is checked first.

Read-time was not the first design. The write-side version needed a hook
wherever an index could change, and that list would not close: it went from
four to seven across three review rounds, and still missed `ts.loc[new] = v`,
`ts.pop(label)`, `del ts[label]` — which swap the block manager inside pandas'
own indexer, past `__finalize__`, `_update_inplace` and `.index` assignment
alike — and `interpolate_gaps(inplace=True)`, one of three
`pd.Series.__init__` call sites of which an explicit audit for that pattern
still guarded only two. Every one of those doors changes `self.index`, and the
getter reads `self.index`, so checking there closes all of them at once and
cannot be bypassed by a path nobody thought of.

**One invariant this depends on:** any code that copies metadata must copy the
private slots, never the public names. Assigning through `lowess_fit` or
`outlier_indices` runs the stamping setter, which re-stamps with the receiving
object's index *and values* and launders a stale fit into a valid-looking one.
`_create_new_with_data` had exactly that shape and names the private slots for
this reason, as it already did for `_freq_declaration`.

Two consequences of checking on read rather than destroying on write:

- **Restoring the index and the values makes the fit readable again, on the
  object that owned it.** Both stamps match again, so the samples the fit
  describes are back where it says. Restoring only the index after the values
  changed does not — that was the wrinkle #20 left and
  [#40](https://github.com/SympatiCog/baseTs/issues/40) closed. A *derived*
  object behaves differently and deliberately: derivation releases a value
  that never described it, so no later revert can hand it one it never had.
  Reading never destroys, so which of the two you get never depends on
  whether anyone looked first.
- **An object mutated in place to a different index or different values keeps
  the old value in its slot**, unread, until it is overwritten or the object
  is collected. Only derivation releases eagerly — which is the case that
  matters, since it is what stops a slice, or since #40 a `sg_filter()`
  result, pinning the parent's full-length fit and values snapshot. Closing
  the in-place case too would need a hook at every point an index or a value
  can change, which is the design this replaced.

Pickles written before #40 hold the older slot shapes — a bare array from
before #20, a `(value, index)` pair from between — and `__setstate__`
completes each to the triple, stamped against the unpickled object's own
index and values. A legacy blob carries no evidence of whether its fit still
described its values when written; the completion accepts the pairing it
holds, and the rule applies from then on.

### Constructor

#### `TimeSeriesData.__init__(data, index=None, **metadata)`

Create a new TimeSeriesData object.

**Parameters:**
- `data` (array-like): The signal values
- `index` (array-like, optional): The time index (becomes pandas Index)
- `**metadata`: Additional metadata to preserve

### Core Methods

#### `copy(deep=True)`

Create a copy with metadata preservation.

#### `duration()`

Calculate the duration of the time series.

#### `len()`

Get the length of the time series (backward compatibility).

## Architecture Notes

### Direct Inheritance Benefits

- **Simplified Codebase**: No dual backend complexity
- **Native Performance**: Direct access to pandas optimizations
- **Enhanced Methods**: 8+ new pandas-powered analysis methods
- **Backward Compatibility**: 100% API compatibility maintained
- **Memory Efficiency**: Eliminated dual array storage overhead

### Migration Path

The migration is completely transparent:

```python
# Old code works exactly the same
ts = baseTs(data=data, times=times)
filtered = ts.lowpass_at(cutoff=0.3)

# New enhanced features automatically available
resampled = ts.resample('100ms', method='mean')
correlation = ts1.correlation_with(ts2)
```

This enhanced API provides a powerful foundation for advanced time-series analysis while maintaining full backward compatibility and adding significant new capabilities through the pandas Series foundation.