# Changelog

All notable changes to the baseTs project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-XX-XX

### 🚀 Major Architecture Update: Pandas Series Foundation

**BREAKING CHANGE**: baseTs now inherits directly from pandas Series, providing native access to 270+ pandas methods while maintaining 100% backward compatibility for existing APIs.

### Added
- **Pandas Series Foundation**: Direct inheritance from pandas Series via TimeSeriesData class
- **Enhanced Frequency Analysis**: 
  - `get_frequency_content(window=None)`: FFT with windowing support ('hann', 'hamming', 'blackman')
  - `get_peak_freq()`: Enhanced peak detection with windowing and frequency range control
  - `plot_fft_power()`: Enhanced plotting with `min_rate` parameter and windowing
- **Advanced Interpolation**:
  - `interpolate_gaps()`: Enhanced with `order` parameter for polynomial/spline interpolation
  - Time interpolation support for numeric indices (not just datetime)
- **Native Pandas Access**: Direct access to all pandas Series methods
- **Windowing Functions**: Spectral leakage reduction for frequency analysis
- **DC Component Control**: Automatic exclusion of DC component in peak frequency detection

### Enhanced  
- **Performance**: 2-5x faster rolling operations using native pandas implementations
- **Memory Efficiency**: Eliminated dual array storage overhead  
- **Time Slicing**: Optimized pandas indexing for time-based queries
- **Statistical Operations**: Vectorized pandas computations
- **Metadata Preservation**: All processing history and filter states maintained through pandas operations
- **Method Signatures**: Enhanced with additional parameters while maintaining backward compatibility

### Fixed
- **Time Interpolation**: Now works correctly with numeric time indices 
- **FFT Edge Cases**: Robust handling of constant signals, NaN/Inf values, and very short signals
- **DC Component Handling**: Consistent behavior between legacy and enhanced FFT methods
- **Power Scaling**: Safe normalization in compute_fft_power() for edge cases

### Documentation
- **Complete API Update**: Removed dual backend references, documented pandas Series foundation
- **Enhanced Examples**: New windowing examples and frequency analysis workflows  
- **Performance Notes**: Updated optimization guidelines for pandas Series architecture
- **Method Chaining**: Enhanced examples with new capabilities

### Testing
- **Comprehensive Coverage**: All 62 tests passing with enhanced functionality
- **Edge Case Validation**: Robust handling of degenerate cases in FFT analysis
- **Backward Compatibility**: 100% API compatibility maintained

### Removed
- **Dual Backend System**: Simplified to single pandas Series backend
- **Backend Parameters**: No longer need to specify `backend='series'`
- **Backend Management**: Eliminated BackendManager and conversion utilities

## [Unreleased] — `freq` becomes a derived property (#29, #31, #23)

### Behavior change — `freq` is now a property, not a stored attribute

`freq` used to be a plain attribute: whatever value was last assigned —by
the constructor, by a filter, by pandas' own metadata propagation— stayed
put even after the time index it described had since changed underneath it.
It is now a property. By default it derives from the time index; setting it
explicitly records a *declaration*, honoured only while the index still
matches the one it was set against, and the declaration expires the moment
an operation changes that index. The setter validates, so a bad rate now
raises immediately instead of surfacing much later as a NaN FFT bin or a
wrong filter cutoff. `interpto_hz` was also rebuilt so the grid it produces
actually measures the rate it reports.

Eight breaking changes fall out of these two fixes:

1. **A declared rate expires when the index changes.**
   `baseTs(..., freq=999).iloc[:50].freq` now returns the rate derived from
   the sliced index, not `999`. **Migrate:** re-declare `.freq` after any
   operation that changes the index if you need the old rate to stick, or
   rely on the derived rate instead.

2. **Assigning an invalid rate raises.** `ts.freq = 0`, `ts.freq = np.nan`
   and `ts.freq = '30'` used to be stored silently; they now raise
   `ValueError`. **Migrate:** validate the rate before assigning, or catch
   `ValueError` around the assignment.

3. **`interpto_hz` returns a different grid** — one more sample, spacing of
   exactly `1/new_freq`, and a final timestamp that may fall short of the
   source's last timestamp rather than landing on it. `ts.interpto_hz(200)`
   on a 10.0 s series now returns 2001 samples, not 2000. **Migrate:**
   update any code or test that asserts a specific `interpto_hz` sample
   count or a specific final timestamp.

4. **`interpto_hz` raises on a degenerate source** — a zero, negative, or
   unmeasurable time span — instead of returning an empty series stamped
   with the requested rate. **Migrate:** wrap the call in
   `try`/`except ValueError` if you were relying on an empty result rather
   than an exception.

5. **`TimeSeriesData._metadata` no longer contains `'freq'`.** The
   internal slot it used to name is now `'_freq_declaration'`. **Migrate:**
   code that introspects or iterates `_metadata` looking for `'freq'` needs
   to look for `'_freq_declaration'` instead — or, better, just read and
   write the public `freq` property directly and leave `_metadata` alone.

6. **`baseTs(data, times, freq=0.0)` and `freq=-1.0` now raise at
   construction.** They were accepted before, deliberately, because
   `interpto_hz(0)` used to mint exactly such objects; this release stops
   `interpto_hz` from doing that, so the constructor no longer has to
   tolerate them either. **Migrate:** pass a positive, finite rate, or omit
   `freq` and let it derive from `times`. Note the asymmetry:
   `baseTs(..., freq=np.nan)` still means "not supplied" and does **not**
   raise — `np.nan` is the constructor's own sentinel for that — but
   `ts.freq = np.nan` on an existing object does raise, because there the
   only meaning of assigning `np.nan` is a bad declaration.

7. **A `DatetimeIndex`-backed series now constructs successfully** where it
   used to raise `TypeError`; `.freq` reads `NaN` instead, since a
   `DatetimeIndex` cannot support a numeric rate. **Migrate:** if you were
   catching `TypeError` to detect a `DatetimeIndex` input, check
   `np.isnan(ts.freq)` instead, or resample to a numeric index first.

8. **Arithmetic between two series now preserves an explicitly declared
   rate when the result's index is unchanged**, where it previously always
   re-derived. Found during implementation, not design: a series declaring
   10.0 Hz over a time base measuring 9.9 Hz reported `a.freq == 10.0` but
   `(a + b).freq == 9.9` — the same object answering differently for an
   operation that never touched its index. **Migrate:** code that relied on
   arithmetic always re-deriving `freq`, even when the index didn't change,
   will now see the operand's declared rate instead. See
   `docs/superpowers/specs/2026-08-27-derived-freq-design.md` (Consequences,
   item 8) for the full reasoning.

## [Unreleased] — bounded gap handling in filter_outliers

### Fixed — filter_outliers no longer invents data in pre-existing gaps

**Behaviour change.** `filter_outliers` used to fill every NaN in the series,
without bound, and left nothing to mark which samples were synthetic. On a
600-sample series a 400-sample acquisition gap came back fully populated:

| input | pre-NaN | post-NaN (before) | post-NaN (now) |
|---|---|---|---|
| mid gap, 2 samples | 2 | 0 | 2 |
| mid gap, 100 samples | 100 | 0 | 100 |
| mid gap, 400 of 600 | 400 | 0 | 400 |
| leading gap, 200 samples | 200 | 0 | 200 |
| trailing gap, 200 samples | 200 | 0 | 200 |

Leading and trailing gaps were worse than interpolated: the `ffill().bfill()`
fallback filled them with a **constant**, which reads downstream as genuine
low-variance signal.

Two populations of NaN were being conflated. Samples the filter blanks itself
should be interpolated — that is what the filter is for. NaNs already in the
input are acquisition dropouts, and the filter was never asked to invent them.
By the time the post-processing step ran, the two were indistinguishable. The
input mask is now captured before the iteration loop and restored afterwards.

`lowess_fit` gets the same treatment, so the QC plot no longer draws a
confident fit across a region with no data.

**Migration:** if you relied on receiving a gap-free series, either set
`fill_input_gaps=True` on the filter to restore the old behaviour, or — better
— pipeline `interpolate_gaps(limit=...)` yourself, which lets you bound how
much absence you are willing to interpolate through. The number of samples left
as NaN is now recorded in the history entry.

The filter's *fit* already handled gaps correctly and is unchanged: LOWESS
regresses against real timestamps over the valid mask, so gap duration is
respected and no structure is fabricated in the fit itself.

## [Unreleased] — freq and history guards

### Fixed — degenerate sampling rates are rejected instead of producing NaN output

`compute_fft_power` guarded an unusable rate with `if ts.freq <= 0`. Every
comparison against NaN is False, so a NaN rate passed straight through and the
FFT returned NaN frequency bins rather than raising. A NaN rate is reachable
whenever the time base is degenerate: `_calculate_effective_frequency` returns
NaN for a zero or negative duration.

Three further consumers had the same blind spot, one of them with no rate check
at all:

- `get_frequency_content` builds its own FFT and had **no guard**; it is the
  path `get_peak_freq` and `relative_band_power` both take
- `relative_band_power`'s Nyquist comparison (`high_freq > nan` is False) let a
  NaN rate through to a confusing "too short for band power analysis"
- `filters.validate_filter_params` had the identical `sampling_freq <= 0`
  comparison, so `lowpass_filter` and `highpass_filter` on a degenerate series
  returned **100% NaN data and reported success**. All four filter methods route
  through it.

All now share `utils.validate_sampling_freq`, which rejects NaN, infinities,
zero and negative rates. `filters` re-raises it as `InvalidParameterError` to
keep that module's exception type.

**Behaviour change:** these five entry points now raise `ValueError` (or
`InvalidParameterError`) where they previously returned NaN-filled output. Code
relying on the silent-NaN behaviour will need to guard the rate itself.
`get_peaks` is deliberately *not* included — its `max(25, ...)` floor makes a
zero or negative rate harmless there, so only non-finite rates are rejected.

`validate_sampling_freq` rejects a size-1 ndarray rather than unwrapping it:
`float(np.array([30.0]))` succeeds on numpy 1.x and raises on 2.x, so accepting
it would make the guard's behaviour differ across the supported matrix. 0-d
arrays convert identically on both majors and remain accepted.

### Fixed — a None history no longer crashes the next operation

`__finalize__` propagates metadata from whichever operand carries it, so an
operand without a history handed `None` to the derived object and the next
operation died on `None.append`. `_update_history_and_process` guarded with
`hasattr`, which is True for a `None` history, so both implementations were
affected.

`history` is now normalised to a list at every derivation path —
`__finalize__`, `copy()` at both depths, and `_create_new_with_data` — through
one shared `normalise_history`. Non-list values (str, tuple, ndarray) are
coerced rather than left to fail later; a str is wrapped rather than exploded
into characters. The eight sites that appended to `history` directly now route
through the guarded helper.

### Known limitations

- `freq` is still copied verbatim by `__finalize__`, so a pandas-derived object
  (`iloc`, `sort_values`) keeps its parent's rate even when the index changed.
  `_create_new_with_data` re-derives correctly, so the two paths disagree. See
  the follow-up issue; this predates the guards above and is why they do not
  fire on those paths.
- `get_frequency_content` still has no NaN/**data** check, so gappy data yields
  a fabricated peak frequency. Tracked separately.

## [0.3.0] - 2026-08-25

### Changed — LOWESS backend moved from moepy to statsmodels

`moepy` has not been released since 2021 and was a hard runtime dependency for a
three-call surface, all inside `LowessOutlierFilter._apply_lowess`. That call now
routes through `statsmodels.nonparametric.smoothers_lowess.lowess`.

**Behavior change — outlier counts shift.** The two smoothers are not
interchangeable and no `frac` reconciles them, and neither the size nor the
direction of the change is constant: it depends on the signal. On slowly-varying
`lambda_val` series statsmodels flags fewer points and its flagged set is *not* a
subset of moepy's; on noisier `irt` series it flags **more**. Measured across the
121 real cpCST `lambda_val` series where the filter is operative (see below), at
`frac=0.075, z_threshold=3`:

```
series                                    n    moepy       sm   flagged by sm only
sub-M10902507_ses-MOBI1A_task-CPTC     6214     5617     3197                  180
sub-M10907283_ses-MOBI1A_task-CPTC     7371     6820     4997                  277
sub-M10920486_ses-MOBI1A_task-CPTC     6641     5893     3819                  161
sub-M10920975_ses-MOBI2B_task-CPTC     4751     3619     2605                  459
```

statsmodels flagged fewer in 131/131 of *those* series, but in roughly half of
them it flagged points moepy did not. Do not assume the new backend only removes
detections — and do not generalise the direction. On the 131 `irt` series at
`frac=0.1, z_threshold=6` the comparison inverts: statsmodels flags **more**
(38,417 vs 35,461; 2.48% vs 2.35% median rate).

**Downstream effects are not negligible.** Running an unchanged analysis
(detrend, filter, `relative_band_power`) over 131 `irt` series, per-file outputs
move by a median of 0.67% but by up to 39% in the tail, with 52/131 files
differing by more than 1%. Test-retest ICC2 over the 32 subjects with two
sessions moves by more than that suggests:

```
              moepy              statsmodels        delta
power       0.4393 [0.11,0.68]   0.5078 [0.19,0.73]  +0.069
amplitude   0.4908 [0.18,0.71]   0.5908 [0.31,0.78]  +0.100
```

The confidence intervals overlap heavily, so this is well inside sampling noise
at that n and is *not* evidence that either backend is more correct. It does mean
results computed under the two backends should not be pooled, and any derived
table built with moepy should be regenerated rather than reused.

Default `frac`, `z_threshold` and `max_iterations` values are unchanged;
retuning detection is a separate decision from swapping the backend.

Runtime on the largest real series (n=17,972) is 0.46s vs moepy's 0.15s, since
statsmodels fits every point where moepy fitted 25 anchors. Set `delta_frac` if
that matters — at `delta_frac=0.001` the same series takes 0.03s.

### Added
- `FilterConfig.it` — robustifying iterations performed *inside* the LOWESS fit,
  default `0`. moepy's `fit()` defaulted to `robust_iters=3` and the old code
  never overrode it, so this is a deliberate departure. `0` keeps the robustness
  in one place: this class already runs its own MAD-based loop.
- `FilterConfig.delta_frac` — fits at points separated by `delta_frac * ptp(x)`
  and interpolates between them, trading accuracy for speed on long series.
  Default `0.0` (fit every point). Successor to `num_fits`.
- Warning when the residual scale collapses to the floor (see Fixed).
- `MIN_WINDOW_POINTS` — the smallest local window (`int(frac * n)`) that yields a
  fit rather than an exact interpolation of the data. Measured at 4, independent
  of series length.
- `notch_filter`, `highpass_filter` and `bandpass_filter` — aliases for
  `notch_at`, `highpass_at` and `bandpass_at`, which the docs already referred
  to by those names. `bandpass_filter` accepts an `order` argument for signature
  compatibility only; the underlying filter has no order parameter and ignores it.
- `remove_outliers(method, threshold)` — the statistical counterpart to
  `filter_outliers`: it drops the points `detect_outliers` flags, rather than
  interpolating over them via the LOWESS workflow.

### Changed — `lowess_detrend` no longer filters outliers

`lowess_detrend` previously called `self.filter_outliers(inplace=True)` while
computing the trend. Three consequences, all now gone:

- It mutated the caller even with `inplace=False` (issue #6), so the original
  object came back with its outliers interpolated away.
- It overwrote whatever outlier filter the caller had configured, via a
  `set_outlier_filter` call on `self`.
- The returned data had outliers removed as a side effect of detrending.

The result is now the *original* data minus the LOWESS trend: **outliers are
preserved, not interpolated away.** Pipe through `filter_outliers` first if you
want them gone. The trend is still fitted robustly, so spikes do not drag it
toward themselves, and the fit now uses a throwaway holder so the caller's
filter config and `is_outlier_filtered`/`outlier_indices` are left untouched.

Anyone relying on the old side effect will see outliers survive a detrend that
used to silently remove them.

### Deprecated
- `set_outlier_filter(num_fits=...)` is ignored and raises `DeprecationWarning`,
  from both the keyword and the `params` dict. It was moepy's anchor-fit count;
  statsmodels has no equivalent. Use `delta_frac`. `num_fits` keeps its ninth
  positional slot, and `it`/`delta_frac` are keyword-only, so positional callers
  cannot silently land a `num_fits` value on `it`.

### Fixed
- `_compute_robust_statistics` silently clamped the residual scale to `1e-6`,
  which made `z_threshold` inoperative rather than merely guarding against
  division by zero. It now warns when the clamp engages.

  **This is not hypothetical: 141 of 262 real cpCST series hit the floor at the
  default settings**, under *both* backends. `lambda_val` is a staircase signal
  that LOWESS fits almost exactly, so residual MAD lands around 2e-16 and every
  z-score is divided by the floor. In that regime the flagged set is numerical
  noise — for the floored series it is a contiguous run from index 0, a
  leading-edge fitting artifact rather than detected outliers. Pre-existing and
  unchanged in behavior here; the warning only makes it visible.
- `set_outlier_filter` docstring described `frac` as "Fraction of points to
  consider as outliers". It is the LOWESS bandwidth — the fraction of points in
  each local regression window. Also documented `max_iterations` as `100` when
  the signature says `10`.
- `docs/USER_GUIDE.md` showed `ts.set_outlier_filter(z_threshold=3.0,
  lowess_frac=0.1)`; there is no `lowess_frac` parameter and that line raised
  `TypeError`.
- `docs/API.md` listed `set_outlier_filter(frac=0.1, z_threshold=2.5)`; the real
  defaults are `frac=0.075, z_threshold=7`.
- `LowessOutlierFilter` silently returned a degenerate fit when the local window
  came to three points or fewer (issue #12). Tricube weighting zeroes the window's
  edge points, so at `k = int(frac * n) <= 3` the line is set by at most one
  effectively-weighted point and passes exactly through the data. The "fit" was
  then the input, every residual zero, the MAD scale pinned to `SCALE_FLOOR` and
  `z_threshold` inoperative — a filter that detects nothing looks exactly like a
  clean signal.

  `filter` now raises `ValueError` up front, naming `frac`, the series length,
  the resulting window and a `frac` that would work. The check is on the window,
  not on `frac`: `frac=0.001` is fine on a long series and degenerate on a short
  one, so no bound on `frac` alone catches this. Both `filter_outliers` and
  `lowess_detrend` are covered, since both route through `filter`.

  Masking outliers also shrinks the usable series mid-loop — a run starting at
  exactly `k == 4` drops to `k == 3` after a single removal — so the loop now
  stops when the window would become degenerate and keeps the last sound fit,
  rather than overwriting it with an interpolation of the survivors.
- The `SCALE_FLOOR` notice is now a `RuntimeWarning` rather than a `logging`
  call. It reports that the caller's result is meaningless, so it must surface
  under default configuration rather than only when handlers are attached.
- `filter_outliers(qcplot=True)` produced a QC plot that could not show what it
  claimed, under either value of `inplace` (issue #7):

  - with `inplace=True` the "Original" trace was byte-identical to "Filtered",
    because `self` had already been overwritten with the filtered data before
    being handed to `qc_plot` — the plot compared the result against itself;
  - with `inplace=False` the "Lowess Fit" trace was missing entirely, because
    the fit is assigned to the returned copy and `self.lowess_fit` stays `None`.

  `filter_outliers` now snapshots the pre-filter state before either branch runs
  and carries the new fit on that snapshot, so both traces are correct either
  way. The snapshot is taken only when `qcplot=True`, keeping the copy off the
  normal filtering path. The `ValueError` this used to raise with
  `inplace=False` was already resolved when `qc_plot` moved its guard onto
  `lowess_fit`; this closes the remaining half.

## [0.2.0] - 2026-08-25

### Fixed — `ts.plot` no longer shadows the pandas plotting accessor

`plot` was a plain alias for `plot_line`. Because `pandas.Series.plot` is an
accessor *object* rather than a method, that alias made all eleven pandas plot
kinds unreachable — `ts.plot.line()`, `.bar()`, `.hist()`, `.kde()` and the rest
raised `AttributeError: 'function' object has no attribute 'line'`.

`ts.plot` is now a hybrid accessor: calling it is unchanged (`ts.plot()` still
draws the baseTs line plot and accepts every `plot_line` keyword), while
attribute access delegates to the pandas accessor. Both spellings work.

### Fixed — documentation corrections

- **`resample`**: `docs/API.md` documented a `resample(factor)` signature that
  does not exist. The real signature is `resample(freq: str, method='mean')`.
  Several examples also showed `ts.resample('1s').max()`, which reads as
  pandas-style chaining but resamples with the default `mean` and then takes a
  scalar max over those means; the aggregation belongs in `method=`. Uppercase
  offset aliases (`'1S'`, `'H'`) were updated, and the non-fixed offsets `'W'`
  and `'M'` — which raise on a timedelta index — were replaced.

  Note this override is necessary, not accidental: a baseTs carries a numeric
  float index, and `pandas.Series.resample` requires a `DatetimeIndex`,
  `TimedeltaIndex` or `PeriodIndex`, so pandas' own version raises `TypeError`.

- **`ts.data[...] = ...`**: documented in four places, but `.data` returns a
  read-only view under pandas Copy-on-Write, so item assignment raises
  `ValueError`. This is the correct behaviour — a writable copy would make the
  assignment silently do nothing — so the docs now use `ts.iloc[...] = ...`, the
  `ts.data = array` setter, or `set_indices_to_nan_and_interpolate()`, which had
  been documented nowhere despite being the natural fit.

### Fixed — pandas operations no longer downgrade the object

`TimeSeriesData._constructor` returned `TimeSeriesData`, and `baseTs` inherited
it, so every native pandas operation silently dropped all 62 baseTs methods:

```
ts.rolling(10).mean()  ->  TimeSeriesData    lowpass_at: False
ts.iloc[0:10]          ->  TimeSeriesData    lowpass_at: False
```

This contradicted "All methods return new baseTs objects, enabling method
chaining" and the "270+ pandas methods" claim. All 26 operations tested now
return `baseTs`.

pandas builds subclasses as `_constructor(values, index=...)`, which
`baseTs.__init__` rejected — it took `times`. The constructor now accepts
`index` as an alias (prefer `times` in your own code).

Metadata repairs, without which the preserved type still lost state:

- `_metadata` omitted `outlier_indices`, `is_outlier_filtered` and
  `outlier_filter`, so `ts.iloc[:50].outlier_indices` raised `AttributeError`
  even after `filter_outliers()` had populated it.
- `_metadata` listed `filtered_indices`, which was only ever initialised to
  `None` and never written — a half-finished rename. Retired.
- `_constructor_sliced` was a plain method where pandas expects a property.
- `__finalize__` assigned metadata by reference, so a derived object shared the
  parent's `history` list. Mutable metadata is now copied.

### Behavior change — effective sampling frequency

`_calculate_effective_frequency` computed `len(self) / duration`, but *n*
samples span *n−1* intervals. It over-reported by `n/(n-1)`:

| n | true | reported | error |
|---|---|---|---|
| 5 | 2.0 Hz | 2.500000 | +25.00% |
| 10 | 10.0 Hz | 11.111111 | +11.11% |
| 1000 | 100.0 Hz | 100.100100 | +0.10% |

`freq` feeds `np.fft.fftfreq`, every filter cutoff normalisation, and the
Nyquist check, so the error propagated into reported frequencies and filter
behaviour. **Any code relying on a derived `freq` now gets a slightly lower,
correct value**, and a cutoff that previously sat just under the inflated
Nyquist may now be rejected as at-or-above the real one.

### Fixed — pandas 2.x/3.x compatibility

The package did not run correctly on pandas 2.0 or later. `setup.py` declared
`pandas>=1.1.0`, which was not true; the floor is now `>=2.0.0`.

- **`interpolate_missing()` crashed on leading or trailing NaN.** `filters.py`
  used `fillna(method='ffill')`, removed in pandas 3.0, raising
  `TypeError: NDFrame.fillna() got an unexpected keyword argument 'method'`.
  `Series.interpolate()` does not fill leading/trailing NaN, so this path was
  reached by ordinary input. Now uses `.ffill().bfill()`.
- **`detect_outliers(method='modified_zscore')` crashed.** It called
  `Series.mad()`, removed in pandas 2.0. See the behavior change below.
- **`duration()` and `get_statistics()` raised `IndexError` on an empty
  series.** `baseTs.duration()` shadowed the guarded `TimeSeriesData.duration()`
  and dropped its zero-length check. The redundant override was removed.
- **`freq=float('nan')` silently produced an all-NaN time index.** The
  constructor tested `freq is np.nan`, which only matches that one object.
  `float('nan')`, `np.float64('nan')`, and `None` are now all recognised as
  "not provided" and raise the intended error.
- **Uppercase offset aliases** (`'1S'`) in `resample` docstrings updated to
  lowercase; pandas 3.0 removed the uppercase forms.
- `setup.py` version (0.1.0) and `baseTs/version.py` (0.1.1) disagreed; both
  are now 0.2.0.

### Behavior change — `detect_outliers(method='modified_zscore')`

This is not a like-for-like restoration and it changes results.

`pandas.Series.mad()` returned the **mean** absolute deviation about the
**mean**, not the median absolute deviation about the median, despite the call
site's comment. The 0.6745 constant is calibrated for MAD, so on pandas <= 1.5
this method was mis-scaled by roughly 1.18x: a requested `threshold=3.0`
behaved as approximately 3.55 sigma, under-reporting outliers.

It now computes a true MAD (`np.nanmedian(|x - median|)`), so **the same call
with the same threshold flags more outliers than it did on pandas 1.x**. Code
tuned against the old behaviour may need its threshold revisited.

Two further corrections while restoring it:

- `np.nanmedian`, not `np.median`. `Series.median()` skips NaN, so pairing it
  with a NaN-propagating denominator returned an all-False mask - reporting no
  outliers - whenever the input contained a single NaN.
- When MAD is zero (over half the values identical), the Iglewicz-Hoaglin
  mean-absolute-deviation fallback is used rather than raising or returning
  all-False, both of which would miss a genuine outlier in e.g.
  `[1, 1, 1, 1, 1, 100]`. A truly constant series warns and returns all-False.

### Testing

- New `tests/unit/test_pandas_compat.py`: 17 regression tests covering every
  item above, including NaN-present, zero-MAD, and constant-series inputs.
- `test_get_peaks` seeded and its exact-count assertion relaxed to a
  contains-check under default parameters. It added unseeded noise and asserted
  an exact peak count, so it passed or failed based on preceding global random
  state.

## [Unreleased] — earlier, unreleased notes

### Added
- **Relative Band Power / fALFF**:
  - `relative_band_power(low_freq, high_freq, ratio='power', window=None, details=False)`:
    Relative power or amplitude in a frequency band. Defaults to `ratio='power'`, the fraction
    of signal variance in the band; `ratio='amplitude'` reproduces classic fALFF
    (Zou et al., 2008).
  - `falff(low_freq=0.01, high_freq=0.1, ratio='amplitude')`: Convenience wrapper using the
    literature band and convention.
  - `BandPowerResult` dataclass returned by `details=True`, carrying `band_sum`, `total_sum`,
    bin counts, frequency resolution, and `bin_fraction` — the white-noise null both conventions
    converge on, so a ratio can be interpreted against a baseline.
  - The DC (0 Hz) bin is always excluded from both numerator and denominator. Since
    `get_frequency_content()` does not demean, DC would otherwise dominate the denominator on any
    signal with a non-zero mean and drive the ratio toward zero.
  - Validation for bands above Nyquist, bands narrower than the frequency resolution (with the
    required recording duration in the message), NaN/Inf data, and effectively constant signals.
- **Plotting**: `plot_fft_power(..., highlight_band=(low, high))` shades a frequency band on the
  power spectrum.

### Fixed
- **Derived objects no longer share the outlier filter.** `outlier_filter` was
  propagated by reference on every path that produces a new object, so
  `set_outlier_filter` on a copy, a slice or an arithmetic result reached back
  and retuned the object it came from.

  `FilterConfig` is now frozen and `set_outlier_filter` rebinds the filter
  instead of mutating it in place, which makes sharing safe by construction —
  configuring one object cannot be observed by any other, and no defensive
  copying runs on the hot path.

- **`set_outlier_filter` no longer resets the parameters you did not name.**
  Every parameter defaulted to a real value, so `set_outlier_filter(frac=0.1)`
  quietly also set `z_threshold=7` and `max_iterations=10` — values the caller
  never chose, and different from `FilterConfig`'s own defaults of `3.0` and
  `5`. Unnamed parameters are now left alone.

- **Non-inplace methods no longer reset the outlier filter to defaults.**
  `_create_new_with_data` omitted `outlier_filter` from the metadata it carried,
  so `zscale()`, `detrend()`, `rolling_mean()`, `lowpass_at()` and every other
  method routing through it returned an object configured with `FilterConfig`'s
  defaults. A configured filter silently reverting changes which points are
  treated as outliers.

- **`ts += 1` records its history entry again.** pandas implements augmented
  assignment as `__add__` followed by keeping the values and discarding the
  wrapper, so the entry was appended to an object that was then thrown away.

- **`TimeSeriesData` now has a real outlier filter.** It declared
  `outlier_filter` and `is_outlier_filtered` in `_metadata` but never set them,
  so `to_basetseries()` produced an object carrying `None` and the next
  `filter_outliers()` raised `AttributeError`.

- **`baseTs(..., history=[...])` no longer stores the caller's list.** Two
  series built from one list cross-contaminated each other's history.

- **`freq` is now derived rather than carried across operations that change
  the time base (#19).** `_create_new_with_data` hard-carried `self.freq`
  into every object it built, so `resample()`, `remove_outliers(inplace=False)`
  and every other non-inplace method routing through it reported the *old*
  sampling rate. `interpto_samples` and `interp_to_uniform_grid` computed
  `freq` as `n / duration`, then assigned that over the correct derivation —
  the same `n`-vs-`n-1` error already fixed once for
  `_calculate_effective_frequency`. `get_statistics()`'s `sample_rate` had the
  identical error and is fixed too. An explicitly supplied `freq` is still
  carried across operations that leave the index untouched — see the behavior
  change below.

- **`rolling()`, `expanding()`, and `ewm()` results now carry their parent's
  metadata (#14).** These build their result directly via the constructor and
  never call `__finalize__`, so `history`, `outlier_filter`, `signal_name` and
  everything else in `_metadata` silently reset to constructor defaults.
  `rolling()`/`expanding()` now return a thin finalizing wrapper rather than
  pandas' own window object; `for w in ts.rolling(3): ...` still works
  (delegated straight to the underlying window's own iteration, which already
  finalized correctly on its own) - caught by adversarial review of this fix.

- **`nlargest()`/`nsmallest()` results now carry their parent's metadata
  (#14).** They do call `__finalize__`, but lose it at an internal `concat`
  step where pandas passes a bare `SimpleNamespace` rather than an `NDFrame` —
  pandas' own default only copies `_metadata` from an `NDFrame`. Recovered by
  reading it off the first concatenated object instead, the pattern pandas'
  own subclassing guide documents. The recovery only fires when the
  `SimpleNamespace`'s `input_objs` has exactly one non-empty object -
  nlargest/nsmallest's own internal pattern - so a genuine `pd.concat([a, b])`
  is unaffected and still derives `freq` from the real merged index rather
  than inheriting whichever operand concat saw first. An earlier version of
  this fix matched on any `concat` call and was caught doing exactly that by
  adversarial review before merge.

### Changed
- `copy(deep=False)` hands back its own `history` while still sharing the data
  buffer. pandas reaches this path internally — `sort_values()` is implemented
  as `copy(deep=False)` on sorted input — so a shallow copy the caller never
  asked for was leaking a shared list.

### Behavior change — outlier counts move on chained calls

Because a configured filter now survives into derived objects, code of the form

```python
ts.set_outlier_filter(frac=0.1)
ts.zscale().filter_outliers()
```

filters at the `frac` you set rather than at `FilterConfig`'s default. On a
400-sample test signal this moved the number of points removed from 88 to 50.
The previous numbers came from a config the caller never asked for, but if you
have tuned around them, re-check your thresholds.

`lowess_detrend` is unaffected: it now names `z_threshold` and
`max_iterations` explicitly, so its trend is bit-identical to before.

### Behavior change — freq on arithmetic between different time bases

`_wrap_result_as_basets` took `freq` from the left operand:

```python
x = baseTs(np.arange(10.), np.arange(10) / 10.0,  freq=10.0)
y = baseTs(np.arange(10.), np.arange(10) / 100.0, freq=100.0)
c = x + y
# 19 samples spanning the union of both time bases at a true 20.0 Hz,
# c.freq reported 10.0 - x's rate, regardless of what the result actually is
```

It now derives `freq` from the result's own index instead, unconditionally —
unlike `_create_new_with_data`, this site does not carry an explicitly
supplied `freq` even when the operands share one index, since arithmetic
between two series is exactly the case where the index most needs re-checking
rather than assumed. Code that relied on an arithmetic result reporting an
operand's declared (rather than derived) rate will see a different `freq`
after this change.

### Planned
- Additional windowing functions for spectral analysis
- Enhanced plotting integration with matplotlib
- Export functionality to various formats

## [1.0.0] - 2023-XX-XX (Previous Release)

### Features
- Core baseTs class with NumPy backend
- Basic filtering operations (`lowpass_filter`)
- Normalization methods (`zscale`, `normalize_range`)
- Function application (`apply_function`)
- Outlier detection and removal
- Basic interpolation and resampling

### Core Methods
- `lowpass_filter(cutoff)`: Low-pass filtering with Butterworth filter
- `zscale()`: Z-score normalization (mean=0, std=1)
- `normalize_range()`: Range normalization (min=0, max=1)
- `apply_function(func)`: Apply arbitrary function to data
- `remove_outliers()`: Remove statistical outliers
- `interpolate()`: Linear interpolation of missing values
- `resample(factor)`: Resample to different time resolution

### Properties
- `data`: Access to underlying data array
- `times`: Access to time points array
- `len()`: Get length of time series

## Migration Notes

### From 1.0.0 to Current

#### Breaking Changes
- **None**: This release maintains 100% backward compatibility

#### Migration from 1.0.0 to 2.0.0
```python
# Before (1.0.0 - still works exactly the same)
ts = baseTs(data=data, times=times)
filtered = ts.lowpass_filter(cutoff=0.3)

# After (2.0.0 - same API, enhanced capabilities)
ts = baseTs(data=data, times=times)  # Now pandas Series-based
filtered = ts.lowpass_filter(cutoff=0.3)  # Same method, better performance

# New enhanced features available automatically
freqs, power = ts.get_frequency_content(window='hann')  # Enhanced FFT
peak = ts.get_peak_freq(window='blackman', min_freq=1.0)  # Windowed peak detection
ts.plot_fft_power(min_rate=1.0, max_rate=50.0, window='hann')  # Enhanced plotting
```

#### Automatic Benefits in 2.0.0
- **No Code Changes Required**: All existing code works unchanged
- **Enhanced Performance**: Automatic 2-5x speedup in rolling operations
- **Memory Efficiency**: Reduced memory usage vs. previous dual backend system
- **Native Pandas Access**: Use any pandas Series method directly (e.g., `ts.describe()`, `ts.quantile(0.95)`)

## Future Roadmap

### Version 2.1.0 (Planned - 3 months)
- **Additional Windowing Functions**: Kaiser, Tukey, and custom window support
- **Enhanced Plotting**: Integration with plotly for interactive plots
- **Export Functionality**: Easy export to pandas DataFrame, CSV, HDF5, Parquet
- **Performance Optimizations**: Further improvements for large datasets

### Version 2.2.0 (Planned - 6 months)
- **Seasonal Decomposition**: Trend, seasonal, and residual analysis
- **Advanced Analytics**: Cross-correlation, coherence analysis
- **Multi-resolution Analysis**: Wavelet transforms and time-frequency analysis
- **Batch Processing**: Tools for processing multiple time series

### Version 3.0.0 (Planned - 12 months)
- **Multi-dimensional Support**: Support for multi-channel time series
- **Machine Learning Integration**: Built-in feature extraction and anomaly detection
- **Advanced Resampling**: Non-uniform resampling and gap-filling algorithms
- **Streaming Support**: Real-time time series processing capabilities

## Development Process

### Versioning Strategy
- **Major versions**: Breaking changes, architecture changes
- **Minor versions**: New features, non-breaking enhancements
- **Patch versions**: Bug fixes, documentation updates

### Release Process
1. Feature development and testing
2. Beta release for testing
3. Release candidate with final testing
4. Stable release with documentation
5. Post-release monitoring and hotfixes

### Compatibility Promise
- **Backward compatibility**: Maintained within major versions
- **Deprecation notice**: 12 months minimum before removing features
- **Migration tools**: Provided for major version transitions
- **Legacy support**: Previous major version supported for 24 months

## Credits

### Contributors
- Core development team
- Community contributors
- Beta testers and early adopters

### Dependencies
- **NumPy**: Core numerical operations and array handling
- **SciPy**: Signal processing algorithms and filters  
- **Pandas**: Series foundation and enhanced time-series operations (required)
- **Matplotlib**: Plotting functionality (optional)

### Acknowledgments
- Scientific Python community for best practices
- Pandas team for time-series inspiration
- NumPy team for foundational array operations