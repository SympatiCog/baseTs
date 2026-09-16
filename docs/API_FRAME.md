# baseDf API Documentation

## Table of Contents
1. [Core Class](#core-class)
2. [Constructor](#constructor)
3. [Properties](#properties)
4. [Indexing and Selection](#indexing-and-selection)
5. [Broadcast Transforms](#broadcast-transforms)
6. [Measurements](#measurements)
7. [Correlation](#correlation)
8. [Averaging](#averaging)
9. [Other Methods](#other-methods)

---

## Core Class

### `baseDf`

A set of `baseTs` time series sharing one index — channels, ROIs, or
electrodes laid out as columns of one table.

```python no-run
class baseDf:
    """A set of time series sharing one index."""
```

`baseDf` holds exactly three pieces of state:

- `_df` — a plain `pd.DataFrame`: the values, indexed by seconds-since-origin,
  one column per channel/ROI/label.
- `_col_meta` — a `pd.DataFrame`, one row per column, holding the nine
  per-column fields every `baseTs` carries (`signal_name`, `history`,
  `is_filtered`, `is_interpolated`, `is_outlier_filtered`, `last_process`,
  `outlier_indices`, `lowess_fit`, `outlier_filter`) plus any user attributes
  supplied at construction (`network`, `hemisphere`, `bad`, `condition`, ...).
- `_index_meta` — four scalars describing the shared index: the declared
  sampling rate, `ts_offset`, `has_timestamp_offset`, and `is_uniform_grid`.
  These are properties of the index alone, so every column shares them by
  definition; a frame does not (and cannot) hold a different declared rate
  per column.

**Why DataFrame-*backed*, not DataFrame-*subclassed*.** `baseDf` deliberately
does not inherit from `pd.DataFrame`. A `pd.DataFrame` subclass exposes a
block manager, `_constructor_sliced` firing on every column access, and more
`__finalize__` entry points than `pd.Series` — and the metadata plumbing
`TimeSeriesData` already pays for on the `Series` side exists precisely
because pandas calls *into* subclass metadata at moments that have to be
discovered one bug at a time. A non-subclass has no such moments: the
metadata contract here is code written in `baseTs/frame.py`, called only
where this file calls it. The cost accepted for that safety is that
`frame.rolling(...)` and the other 270+ pandas methods available on
`baseTs` are **not** inherited by `baseDf` — `.df` is the escape hatch, and
every pandas method a caller needs beyond it is a deliberate, explicit
forward. See
`docs/superpowers/specs/2026-09-13-basedf-multichannel-design.md` ("Decision
1") for the full reasoning.

---

## Constructor

### `baseDf.__init__(data, times=None, freq=np.nan, ts_offset=np.nan, col_meta=None)`

Build a frame directly from a DataFrame, a 2-D array, or a mapping.

**Parameters:**
- `data` (`pd.DataFrame | np.ndarray | dict`): A DataFrame, a 2-D array, or a
  mapping of column label to column values.
- `times` (array-like, optional): The shared index in seconds. Defaults to
  `data`'s own index when it has one, otherwise to sample numbers.
- `freq` (float): Declared sampling rate in Hz. Left undeclared (`np.nan`) by
  default, in which case each column derives its own rate from the index —
  the same rule `baseTs.freq` uses.
- `ts_offset` (float): The origin the index seconds are counted from, in
  epoch seconds. Supplying a value sets `has_timestamp_offset=True`.
- `col_meta` (`pd.DataFrame`, optional): Per-column user attributes, indexed
  by column label.

**Returns:**
- `baseDf`: The frame.

**Raises:**
- `ValidationError`: On duplicate column labels, non-numeric columns, a
  `times` length mismatch, `col_meta` naming a reserved field (one of the
  nine maintained fields above), or `col_meta` describing a column not
  present in the data.

```python
import numpy as np
import pandas as pd
from baseTs import baseDf

n = 200
times = np.arange(n) / 100.0
frame = baseDf(
    {"Cz": np.sin(times), "Pz": np.cos(times)},
    times=times,
    freq=100.0,
    col_meta=pd.DataFrame({"network": ["DMN", "DMN"]}, index=["Cz", "Pz"]),
)
```

### `baseDf.from_df(df, time_col="time", value_cols=None, freq=np.nan, ts_offset=np.nan, col_meta=None)`

Build a frame from a wide table: one time column, many value columns.

**Parameters:**
- `df` (`pd.DataFrame`): The wide table.
- `time_col` (str): Column holding the time values, in seconds. Default:
  `"time"`.
- `value_cols` (sequence, optional): Columns to take. Defaults to every
  numeric column except `time_col`.
- `freq` (float): Declared sampling rate in Hz.
- `ts_offset` (float): Origin the index seconds are counted from.
- `col_meta` (`pd.DataFrame`, optional): Per-column user attributes.

**Returns:**
- `baseDf`: The frame. Rows are sorted by `time_col` first if the table
  wasn't already in time order.

**Raises:**
- `ValidationError`: If `time_col` is absent from `df`, a requested
  `value_cols` entry is absent, or (when `value_cols` is not given) any
  non-`time_col` column is non-numeric — named explicitly rather than
  silently dropped.

A long table (one row per timepoint-and-label) has no per-column shape to
hand `from_df` directly — pivot it to wide first:

```python
import numpy as np
import pandas as pd
from baseTs import baseDf

n_time, n_roi = 50, 3
times = np.arange(n_time) * 2.0
long = pd.DataFrame({
    "time": np.repeat(times, n_roi),
    "roi": np.tile([f"roi{i}" for i in range(n_roi)], n_time),
    "value": np.random.randn(n_time * n_roi),
})
wide = long.pivot(index="time", columns="roi", values="value").reset_index()
frame = baseDf.from_df(wide, time_col="time", freq=0.5)
```

### `baseDf.from_csv(path, time_col="time", value_cols=None, freq=np.nan, ts_offset=np.nan, col_meta=None, **read_csv_kwargs)`

Build a frame from a wide CSV file: one time column, many value columns.
Thin wrapper: `pd.read_csv(path, **read_csv_kwargs)` then `from_df` above —
same parameters, returns, and raises.

```python
frame = baseDf.from_csv("channels.csv", time_col="time", freq=0.5)
```

### `baseDf.from_parquet(path, time_col="time", value_cols=None, freq=np.nan, ts_offset=np.nan, col_meta=None, **read_parquet_kwargs)`

Build a frame from a wide Parquet file: one time column, many value columns.
Thin wrapper: `pd.read_parquet(path, **read_parquet_kwargs)` then `from_df`
above — same parameters, returns, and raises. Requires a parquet engine
(`pyarrow` or `fastparquet`) — install with the `parquet` extra:
`pip install "baseTs[parquet]"`.

```python
frame = baseDf.from_parquet("channels.parquet", time_col="time", freq=0.5)
```

### `baseDf.from_series(series, labels=None)`

Build a frame from existing `baseTs` objects that already share one index.
Each series' own metadata becomes its `col_meta` row, so nothing is lost on
the way in — this is the bridge from a today's-workflow list of `baseTs`
objects into a frame.

**Parameters:**
- `series` (sequence of `baseTs`): The series, all on the same index.
- `labels` (sequence, optional): Column labels. Defaults to each series'
  `signal_name`, falling back to its position (`"c0"`, `"c1"`, ...).

**Returns:**
- `baseDf`: The frame.

**Raises:**
- `ValidationError`: On an empty `series`, indices that don't match exactly
  across the series (points at `baseTs.align_with()` to fix), or conflicting
  `freq`/`ts_offset` declarations between series.

```python
import numpy as np
from baseTs import baseTs, baseDf

times = np.arange(200) / 100.0
a = baseTs(np.sin(times), times, freq=100.0, signal_name="Cz")
b = baseTs(np.cos(times), times, freq=100.0, signal_name="Pz")
frame = baseDf.from_series([a, b])
```

---

## Properties

- `df` (`pd.DataFrame`) — the values, as a plain DataFrame. The escape hatch
  to full pandas: `frame.df.rolling(...)`, `frame.df.to_csv(...)`, etc.
- `col_meta` (`pd.DataFrame`) — one row of metadata per column.
- `columns` (`pd.Index`) — the column labels.
- `index` (`pd.Index`) — the shared index, in seconds.
- `shape` (`Tuple[int, int]`) — `(samples, columns)`.
- `freq` (float) — sampling rate in Hz: the declaration if one was made at
  construction, else derived from the index (via the same logic
  `baseTs.freq` uses, so the two never disagree).
- `ts_offset` (float) — origin the index seconds are counted from, in epoch
  seconds.
- `len(frame)` — number of samples.
- `repr(frame)` — e.g. `baseDf(2 columns x 200 samples, 100 Hz)`.

---

## Indexing and Selection

`baseDf.__getitem__` mirrors pandas' own `__getitem__` contract deliberately
— the one place this class returns two different types from a single call,
because it is the convention users' hands already know:

- `frame[label]` — one column, hydrated as a real `baseTs` carrying every
  metadata field the frame was holding for it.
- `frame[[label1, label2]]` — several labels, or `frame[mask]` with a
  boolean mask the length of `columns` — returns a `baseDf` holding just
  those columns (metadata included).

```python
one = frame["Cz"]          # -> baseTs
subset = frame[["Cz"]]     # -> baseDf, one column
```

### `select(where=None, select=None)`

The named form of the same operation, useful when both a query and an
explicit label list are awkward to spell as `__getitem__`.

**Parameters:**
- `where` (str, optional): A pandas query string evaluated against
  `col_meta`, e.g. `"network == 'DMN' and not bad"`.
- `select`: Labels, or a boolean mask the length of `columns`.

**Returns:**
- `baseDf`: A frame holding the chosen columns, in frame order for a query
  and in the caller's order for an explicit label list.

**Raises:**
- `ValidationError`: If the selection matches no columns, an explicit label
  is unknown, or a boolean mask's length doesn't match `columns`.

---

## Broadcast Transforms

Every `baseTs` method annotated as returning `"baseTs"` — except `copy`
(the frame has its own) and `remove_outliers` — is generated onto `baseDf`
as a method that runs the same call on every column and reassembles the
frame. `baseDf.TRANSFORMS` lists all 38 of them:

```
abs, apply_function, bandpass_at, bandpass_filter, butterpass_at, center,
dediff_ts, detrend, diff_ts, filter_outliers, gauss_filter, highpass_at,
highpass_filter, interp_to_uniform_grid, interpolate_gaps,
interpolate_missing, interpto_hz, interpto_samples, lowess_detrend,
lowpass_at, lowpass_filter, normalize_range, notch_at, notch_filter,
resample, rolling_max, rolling_mean, rolling_median, rolling_min,
rolling_std, scale, set_indices_to_nan_and_interpolate, set_outlier_filter,
sg_filter, shift_time, time_slice, trimto_timepoints, zscale
```

Each broadcast method has the same shape:

```python no-run
def <name>(self, *args, inplace: bool = False, **kwargs) -> "baseDf":
    """Broadcast baseTs.<name> over every column."""
```

Calling `frame.lowpass_at(2.0)` calls `frame["c0"].lowpass_at(2.0)`,
`frame["c1"].lowpass_at(2.0)`, etc., and reassembles the results into a new
frame. Each column's `history` records the operation individually, and
`last_process`/`is_filtered` update per column, exactly as they would on a
`baseTs` called directly. `inplace=True` replaces this frame's contents
instead of returning a new one.

**Raises:**
- `ValidationError`: If the underlying transform returns a different index
  length or values for different columns. `baseDf` requires every column to
  share one index, so a transform whose output index depends on its input
  *values* (rather than only its input index) cannot be broadcast safely.

**Why `remove_outliers` is excluded and `filter_outliers`/`set_outlier_filter`
are not.** `remove_outliers` *drops* the samples it flags as outliers, and
which samples are flagged is a function of each column's own data values —
two columns sharing an index but differing only in *where* their outlier
sits come back with genuinely different indices (one drops the sample at
2.5 s, the other at 12.5 s). Broadcasting it would trip the index-mismatch
refusal above on almost any real multichannel dataset, since channels
rarely spike at the same sample. `filter_outliers` and `set_outlier_filter`
are LOWESS-based and *interpolate* rather than drop, so every column stays
on the shared index regardless of where its own outliers fall — measured
frame-safe, and the two supported ways to handle outliers in a frame:

```python
cleaned = frame.filter_outliers()          # interpolates each column's own outliers in place on the shared index
frame["Cz"].set_outlier_filter(frac=0.5)   # tune one column's filter before broadcasting filter_outliers()
```

`copy` is excluded from the generated list because `baseDf` has its own:
copying a frame's state (`_df`, `_col_meta`, `_index_meta`) directly is a
different, cheaper operation than calling `baseTs.copy()` on every column
and reassembling them.

```python
frame.copy()          # deep=True (default): independent values and col_meta
frame.copy(deep=False)  # shares the underlying DataFrames, pandas' own contract
```

---

## Measurements

### `measure(name, *args, **kwargs)`

Run one `baseTs` measurement on every column and collect the results into
one pandas object, rather than a per-column loop the caller writes by hand.

**Parameters:**
- `name` (str): The `baseTs` method to call. Must be a key of
  `MEASURE_KINDS`.
- `*args`, `**kwargs`: Forwarded to each column's call.

**Returns:** Depends on the measurement's kind (see the table below).

**Raises:**
- `ValidationError`: If `name` is not a known frame measurement, or (for a
  `falff`/`relative_band_power` call) `details=True` is passed — that
  returns a `BandPowerResult` object per column, which cannot fill a numeric
  `pd.Series`; call `frame[label].falff(details=True)` on one column at a
  time instead. Also raised if a `shared_axis` measurement disagrees
  between columns (see below).

`MEASURE_KINDS` — how each measurement's per-column result is collapsed:

| Kind | Meaning | Result shape |
|---|---|---|
| `scalar` | one number per column | `pd.Series`, indexed by column |
| `mapping` | one dict of named values per column | `pd.DataFrame`, columns as rows, dict keys as columns |
| `per_sample` | one array the length of the index per column | `pd.DataFrame`, frame index x columns |
| `object` | a non-numeric result (e.g. a list) per column | `pd.Series` of objects, indexed by column |
| `shared_axis` | a `(axis, values)` 2-tuple whose axis every column must agree on | `(axis, pd.DataFrame)`, `DataFrame` indexed by axis, columns as columns |

```python no-run
MEASURE_KINDS = {
    "falff": "scalar",
    "relative_band_power": "scalar",
    "get_statistics": "mapping",
    "detect_outliers": "per_sample",
    "get_peaks": "object",
    "get_peak_freq": "object",
    "compute_fft_power": "shared_axis",
    "get_frequency_content": "shared_axis",
}
```

Each entry also has a named wrapper method, so `measure()` itself is rarely
called directly:

- `falff(*args, **kwargs) -> pd.Series`
- `relative_band_power(*args, **kwargs) -> pd.Series`
- `get_statistics(*args, **kwargs) -> pd.DataFrame`
- `detect_outliers(*args, **kwargs) -> pd.DataFrame`
- `get_peaks(*args, **kwargs) -> pd.Series`
- `get_peak_freq(*args, **kwargs) -> pd.Series`
- `compute_fft_power(*args, **kwargs) -> Tuple[np.ndarray, pd.DataFrame]`
- `get_frequency_content(*args, **kwargs) -> Tuple[np.ndarray, pd.DataFrame]`

```python
scores = frame.falff(low_freq=0.01, high_freq=0.1)   # pd.Series, one per column
stats = frame.get_statistics()                       # pd.DataFrame, columns x stat names
freqs, power = frame.compute_fft_power()             # shared axis, then a DataFrame over it
```

For anything not in `MEASURE_KINDS`, pull the column out and call it there:
`frame["Cz"].some_other_measurement(...)`.

### `duration()`

**Returns:**
- `float`: The span of the shared index in seconds (`index[-1] - index[0]`,
  or `0.0` for an empty frame). A property of the index, so it is the same
  for every column.

---

## Correlation

Two methods, not one dispatching on the type of `other` — a function whose
return *type* depends on its arguments is a trap this API avoids throughout.

### `correlation_with(other, method="pearson")` — the default

Correlate one `baseTs` against every column. This is the seed case: a
continuous behavioural regressor against a per-electrode measure, or a seed
timeseries against each fMRI ROI.

**Parameters:**
- `other` (`baseTs`): The series to correlate every column against.
- `method` (str): `"pearson"`, `"kendall"`, or `"spearman"`.

**Returns:**
- `pd.Series`: One coefficient per column, keyed by column label. Identical
  to calling `frame[label].correlation_with(other, method=method)` for each
  label — including that method's inner-join alignment, which is harmless
  here because the results are scalars.

**Raises:**
- `ValidationError`: If `other` is a `baseDf` — use `correlation_matrix`
  instead, named explicitly below.

### `correlation_matrix(other=None, method="pearson")` — never implicit

Correlate every column of this frame against every column of another frame
(or, with `other=None`, against itself — the within-frame connectivity
matrix, a common fMRI/EEG use).

This is **not** the default and does not share a name with
`correlation_with`, on purpose: an all-pairs matrix costs `O(k*m)` pairs
where the seed case costs `O(k)`, and it answers a genuinely different
question — "how does everything relate to everything" rather than "how does
everything relate to this one thing." Collapsing the two into one method
that guesses which is meant from the type of `other` would make the O(k*m)
cost invisible at the call site; giving it its own name makes the cost a
choice.

**Parameters:**
- `other` (`baseDf`, optional): The right-hand frame. `None` means this
  frame against itself.
- `method` (str): `"pearson"`, `"kendall"`, or `"spearman"`.

**Returns:**
- `pd.DataFrame`: This frame's columns as rows, `other`'s columns as
  columns.

**Raises:**
- `ValidationError`: If `other` is not a `baseDf` (points at
  `correlation_with` for a single series), or the two frames share no
  timepoints.

```python
seed_corr = frame.correlation_with(seed_ts)     # pd.Series: one number per column
conn = frame.correlation_matrix()               # pd.DataFrame: within-frame connectivity
cross = roi_frame.correlation_matrix(other=other_frame, method="spearman")
```

---

## Averaging

Two methods, not one overloaded method, for the same reason as the
correlation pair: a return type that depends on the arguments is a trap.

### `average(select=None, where=None, skipna=False, min_count=None, name=None)`

Average a selection of columns into one `baseTs`.

**Parameters:**
- `select`: Labels, or a boolean mask the length of `columns`.
- `where` (str, optional): A query against `col_meta`, e.g.
  `"network == 'DMN'"`.
- `skipna` (bool): See "NaN default is propagate" below. Default `False`.
- `min_count` (int, optional): Minimum contributors for a timepoint to be
  kept. Only meaningful with `skipna=True`.
- `name` (str, optional): Signal name for the result. Defaults to a name
  derived from the selection, e.g. `"mean(network == 'DMN')"`.

**Returns:**
- `baseTs`: The averaged series, on the frame's index.

**Raises:**
- `ValidationError`: If the selection matches no columns, or `min_count` is
  given together with `skipna=False`.

### `average_by(by, select=None, where=None, skipna=False, min_count=None)`

Average columns within each group, giving one column per group — e.g.
ROI→network is `frame.average_by("network")`.

**Parameters:**
- `by` (str or sequence of str): Column name(s) in `col_meta` to group on.
- `select`, `where`: Restrict the *input* columns before grouping, same
  semantics as `average`.
- `skipna`, `min_count`: As for `average`, applied independently within each
  group.

**Returns:**
- `baseDf`: One column per group, on the frame's index. A group of one
  column is legal, and its history says so rather than looking like an
  untouched column.

**Raises:**
- `ValidationError`: If a grouping column is absent from `col_meta`, or the
  selection matches no columns.

```python
network_means = frame.average_by("network")            # -> baseDf, one column per network
dmn = frame.average(where="network == 'DMN' and not bad")  # -> baseTs
```

### The rules an average is entitled to claim

Quoted, in substance, from the design spec's "Flag propagation" and "NaN
default is propagate" sections
(`docs/superpowers/specs/2026-09-13-basedf-multichannel-design.md`):

**Flag propagation: contamination ORs, treatment ANDs.**
`is_interpolated` means *some values here were not measured*. It is a
property of the data, so it propagates if **any** contributor carries it,
and is never reset. `is_filtered` and `is_outlier_filtered` mean *this
series has been treated*, a claim about the whole series, so they hold only
if **every** contributor was treated. Averaging 17 ROIs of which 3 were
outlier-filtered yields `is_filtered=False`, with the divergence recorded in
history.

**History is the common prefix, then a summary.** Claiming "bandpassed
1-10 Hz" is honest only if every input was bandpassed. The result's history
is the common prefix of the contributors' histories, then one entry naming
the selection, `n`, and the NaN policy; divergence beyond the prefix is
summarised (`inputs diverged after step 4; 3 of 17 additionally
outlier-filtered`).

**A history entry is "operation; outcome", and steps compare by operation.**
Everything before the first `"; "` names what was done and with which
parameters (`Interpolated to uniform grid of n=400 @ 50.0Hz, fill_value=nan,
max_gap=0.5s`); everything after it is what happened to this one series
(`; 150 grid point(s) outside the data padded with nan`). Ten trials padded
by different amounts therefore share that step, and the prefix keeps it as
the head plus `; per-input details differ` rather than reporting a
divergence. Two trials regridded with different `max_gap` values differ in
the head and diverge for real. The constructor's own entry follows the same
rule (`Created baseTs object; 200 samples`), so trials of different lengths
share step 0. The rule is `frame_average.operation_head`; a new history
message should put its parameters before the separator and its counts after. `outlier_indices`, `lowess_fit`, and `outlier_filter` are
per-column artifacts with no meaning for a mean — dropped, and history says
so. `signal_name` is `name` if given, else derived from the selection.

**NaN default is propagate, not skip: `skipna=False`.** A specparam fit that
failed on channel 17 at window 40 means `skipna=True` would average a
*different set of channels* at that window than everywhere else, silently
changing the estimator mid-series — the failure this default guards
against. `skipna=True` is explicit and records in history how many
timepoints ran at reduced `n`; `min_count` guards the floor. The full
per-timepoint contributor count is always available directly as
`frame.df.notna().sum(axis=1)`, so no new slot is invented for it.

**`min_count` is refused alongside `skipna=False`.** With the default
`skipna=False` a single NaN already propagates, so a floor on the
contributor count has nothing to act on; passing `min_count` without
`skipna=True` raises `ValidationError` rather than silently ignoring it.

**What `average_by` writes per group.** One row per group in the result's
`col_meta`. `signal_name` is the group label; `history` is that group's own
common prefix plus its summary entry; the flag rules above apply within
each group independently. Group membership and `n` are recorded in each
row's history.

---

## Other Methods

See [Broadcast Transforms](#broadcast-transforms) above for why `copy` is
reserved rather than broadcast, and [there](#broadcast-transforms) for its
own signature.
