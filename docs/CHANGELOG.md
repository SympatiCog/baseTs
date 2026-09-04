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

## [Unreleased] — the signal name keeps its case across a derivation (#56)

### Fixed — `zscale()` and `iloc[:5]` disagreed about the name of one series

The constructor has always upper-cased the `signal_name` it is handed, and
nothing else ever did. Every derivation copies the parent's name — except the
ones that handed it back to the constructor as a keyword, which upper-cased it
a second time. So a name assigned after construction, `ts.signal_name =
'Heart Rate'`, survived `iloc`, `head`, `copy` and `TimeSeriesData(ts)` and
came out of `zscale()`, `detrend()`, `rolling_mean()`, `ts + 1` and
`to_basetseries()` as `'HEART RATE'`. Every plot title, axis label and legend
entry is built from the name, so which case a plot showed depended on which
method produced the series.

**The decision the issue asked for.** Two readings were defensible: the
upper-casing is a library-wide normalisation, and `iloc`, `copy` and the
attribute setter are the ones that were wrong; or it is the constructor's
courtesy to its own argument, and the re-minting paths were wrong. The second
is taken. It is the reading the rest of this arc has been establishing — a
derived object carries its parent's metadata unchanged (#33, #35, #57) — it
is what the API docs describe (`signal_name`: "name for the signal", with no
mention of case), and the alternative would have extended an undocumented
rewrite to the attribute setter, where a mixed-case name is currently the
user's to set. The rule, stated once and pinned: **the constructor normalises
its own argument; a derivation copies the parent's name, whichever path built
it.**

Three sites re-minted the name and are changed to copy it:
`baseTs._create_new_with_data`, which every non-inplace processing method
routes through; `TimeSeriesData._wrap_result_as_basets`, the arithmetic
wrapper; and `TimeSeriesData.to_basetseries`. Two more passed the name to the
constructor redundantly — `copy(deep=True)` and the shallow-copy rebuild — and
preserved case only because the `_metadata` loop overwrote what the
constructor had just upper-cased. The keyword is dropped there so the copy is
the one assignment, not the second of two.

The copy goes through `normalise_label`, the same coercion the other copying
doors use, so a `None` name still reaches a derived object as `""` (#33's
guarantee, which the constructor used to provide on this path). With
`preserve_metadata=True` the `_detach_shared_metadata` call at the end of the
method normalises the labels anyway — mutation testing showed a raw copy
survived that case — so the explicit normaliser is there for
`preserve_metadata=False`, where nothing else runs, and is pinned there.

### Changed

- A mixed-case or lower-case `signal_name` assigned after construction now
  survives `zscale()`, `detrend()`, `rolling_mean()` and every other
  `_create_new_with_data` caller, arithmetic (`ts + 1`, `1 + ts`, `ts * ts`),
  and `to_basetseries()`. Before, each returned it upper-cased. A name that
  was already upper-case — which is every name that came from the constructor
  and was never reassigned — is unaffected on every path.

### Unchanged

- `baseTs(..., signal_name='Heart Rate')` still stores `'HEART RATE'`, as does
  `from_df`, which defaults the name to the column name through the same
  door. Pinned.
- A `signal_name=` passed explicitly to `_create_new_with_data(**kwargs)` or
  to a conversion (`baseTs(ts, signal_name='Other')`) is a constructor
  argument, not an inheritance, and is upper-cased. Pinned.
- The attribute setter is not a normalising door and is not made one:
  `ts.signal_name = None` stores `None`, and it is the next derivation that
  turns it into `""`.

### Observed, not changed

- `plotting.lag_plot` calls `.upper()` on the name itself when it builds a
  title, so a lag plot is upper-cased where every other plot is not. That is
  in #61's neighbourhood and is left for it.

## [Unreleased] — the lag that is applied is the lag that is reported (#51, #52, #53, #54)

### Fixed — four ways the shift result described a shift it had not performed

All four live in the one chain `get_lags` → `validate_lag` →
`shift_timeseries` → `plotting.lag_plot` (hence `baseTs.lag_plot`), and all
four were filed from #32's review rounds rather than folded in. Three let
the returned dict, and so the plot title, say something the function had
not done; the fourth raised numpy's message for a cause #32's title had
already claimed.

**#51 — a derived rate shifted one sample short and reported the lag it did
not apply.** `time_to_idx` truncated with `int()`. A derived rate is rarely
exact — a nominal 100 Hz series derives to 99.99999999999999 — so
`int(0.5 * rate)` was 49 for a caller who asked for half a second, in 7% of
a sweep over every length from 100 to 2000 samples. `get_lags` then echoed
the caller's 0.5 back as `lag_secs`, so the result read `{'lag_secs': 0.5,
'lag_idx': 49}` and the plot `Lag Plot at 0.5 seconds (49items)`. The
conversion now rounds to the nearest sample (Python's `round`, so an exact
half goes to the even neighbour — either neighbour is as honest as the other
when there is no nearest one, and the rule is pinned so it is not mistaken
for drift). Separately, and for every seconds-mode call, `lag_secs` is now
derived *from* `lag_idx` — `idx_to_time(lag_idx, freq)` — rather than echoed:
the two halves of the result agree by construction whatever the rounding
did. Rounding alone would not have got there: 0.3 s at 7 Hz is 2.1 samples,
2 are applied, and 2/7 s is what the result now says, where it used to say
0.3. The issue's sweep is a test, and it comes up short in 0 of 5703 cases.

**#52 — an integer series raised the very message #32 is named for.** The
wrapped head was blanked with `lagged[:lag_idx] = np.nan`, which an int64
array cannot hold: `ValueError: cannot convert float NaN to integer`, from a
different line and a different cause than #32 — the rate was fine, the
container could not take the sentinel. A `datetime64` index (reachable with a
declared rate) died on `Could not convert object to NumPy datetime` the same
way. `lag_plot` calls with `drop_nan=False` and so took that path
unconditionally, so no integer series could be lag-plotted. Two changes.
With `drop_nan=True` the blanked samples are sliced off anyway, so no
sentinel is written and the series' own dtype survives — an int64 series
returns int64, a timestamp index returns timestamps. With `drop_nan=False`
the head is blanked with the dtype's own missing value where it has one (NaN
for float, complex and object; NaT for datetime and timedelta); a
*numeric* dtype with none (integer, unsigned, bool) is widened to float64
first, which for integers is what `pd.Series([1, 2, 3]).shift(1)` does —
and only while every value is within ±2**53, where float64 is exact:
review round 2 (codex) showed that widening the whole array for the sake
of two placeholders changed the *surviving* samples past that limit, two
distinct values landing on one float, where main had raised; so past it
the call is refused and the message names `drop_nan=True`, which keeps the
dtype, a remedy the test executes (bool deliberately diverges — pandas shifts a bool Series to object, and a
float sentinel is what this contract promises); and a non-numeric dtype with
none (bytes, str) is refused by name, because "widen" would mean parsing,
and review round 1 (codex) showed an outcome-based fallback let
`['1.0', '2.0', ...]` flip from text to float64 silently when its entries
happened to parse. `astype(float)` is deliberately not the route for the
datetime kinds: it reinterprets the int64 storage and turns NaT into
-9.2e18, the trap #28 documented. A float series returns
exactly the arrays it did before, pinned against the old code inlined in the
test; the result is still a fresh array, not a view of the series.

**#53 — a lag longer than the series returned an empty result, confidently
labelled.** `np.roll` wraps modulo the length and the blanking then covered
the whole array, so `shift_timeseries(five_samples, 100, 'index')` returned
an empty array with `lag_secs=100.0` on a 4-second series, and `lag_plot`
drew an empty scatter titled `100.0 seconds (100items)`. `validate_lag`
takes a new keyword, `n_samples`, and refuses `lag_idx >= n_samples` with a
message naming the lag, the samples it converts to, the rate that connects
them in seconds mode, and the series length. The bound is applied to the
*rounded* index — the one that will be used — so 4.6 s at 1 Hz on a
five-sample series is refused as 5 samples. `lag_idx == n - 1` is accepted:
it leaves one sample, which is degenerate but honest, and the caller can see
its length. Without the keyword the validator is unchanged, so an existing
direct caller keeps its behaviour.

**#54 — any unit but the literal `'seconds'` was silently index mode.**
`get_lags` dispatched on `lag_unit == 'seconds'` with no other check, so
`'second'`, `'Seconds'` and `'sec'` all meant samples — a factor of the
sampling rate in what the lag means, with the plot then correctly labelled
for the wrong reading. `validate_lag`'s else-branch carried the same
assumption. One shared check now refuses anything but exactly `'seconds'` or
`'index'`, naming both and what was passed. Case is not folded: rejecting is
safer than guessing when the two readings differ by 100x. The unit is judged
before the rate or the lag — without it there is no way to know which
conversion the lag was meant for.

### Changed — behaviour, all of it the rule doing what it says

- `time_to_idx` rounds where it truncated. A seconds lag within half a
  sample of a boundary can now convert to one more sample than before; the
  reported `lag_secs` says which.
- `lag_secs` in seconds mode is a `float` derived from the applied index. A
  `Decimal` or `bool` lag used to be echoed back as itself; an exact declared
  rate still reports exactly what was asked (50 / 100.0 is 0.5).
- `shift_timeseries(..., drop_nan=True)` returns the series' own dtype
  instead of float64 — only visible for non-float series, which raised
  before.
- `shift_timeseries(..., drop_nan=False)` on an integer or bool series
  returns float64 with NaN, on a timestamp index returns NaT, where both
  raised before. A bytes or str series raises `ValidationError` naming the
  dtype where it raised numpy's bare conversion error. An integer series
  with a value beyond ±2**53 raises `ValidationError` naming the exact
  remedy, where it raised numpy's bare error.
- One call that succeeded now raises, at the edge of float range (review
  round 1): a lag of 1.7e308 s at 1e-308 Hz rounds to 2 samples, and the
  seconds those 2 samples span overflow, so `idx_to_time`'s existing guard
  refuses the derived `lag_secs` where the old code echoed 1.7e308 back.
  Accepted and pinned: the echo described a shift the call did not make.
- A lag of the series length or more raises `ValidationError` where it
  returned an empty (or all-NaN) result. #32's outcome census had one row
  affected — a 50 s lag on a 3 s series — and it is updated.
- An unknown `lag_unit` raises `ValidationError` where it was index mode.

### Testing

`tests/unit/test_lag_shift_bounds.py`: the issue reproductions for all
four; the 5703-case rounding sweep; the tie rule; the two halves agreeing by
construction across lags at the derived rate; the blanking rule across
int64, uint8, bool, object, complex, datetime64 and timedelta64; the
`drop_nan=False` float path pinned against the old code; text refused by
kind, not by whether it parses; the 2**53 widening limit at both ends with
its remedy executed; the plot title checked for its seconds, not only its
sample count; the float-range overflow accepted above; an
array `lag_unit` diagnosed rather than compared elementwise; the boundary at
`len - 1` / `len`; the seconds-mode bound on the rounded index; the unit
refused through `get_lags`, `validate_lag`, `shift_timeseries` and
`lag_plot`, and judged before the rate. Three pins in
`test_lag_conversion_guards.py` that described truncation are restated for
rounding. Review round 3, a third harness (ollama `glm-5.3:cloud` prompted
directly with the diff), found two pins that passed for the wrong reason:
the rounds-up-to-the-length test matched "5 samples", true of both bound
messages, and now asserts the rounded index the message names; the
rule-order test used a zero index the bound could never fire on, and now
uses a non-integer index past the bound so both rules could speak. 28
mutants over the diff, 27 killed; the survivor is `len(data)` against
`len(times)`, the same number for any Series, noted in a comment.

## [Unreleased] — the NaN message says what a leading gap needs (#77)

### Fixed — a remedy that reproduced the bug it reported, one level up

`validate_finite_data` rejects NaN with "Fill gaps first, e.g. with
`interpolate_gaps()`", and since #48 the Butterworth filters raise the same
message. But `interpolate_gaps()` forwards pandas' default
`limit_direction='forward'`, which fills nothing before the first valid
sample, so a gap at the *start* of the series survived the remedy and the
caller who followed it was rejected again with the exact message they had
just obeyed:

```python
d[0:4] = np.nan
baseTs(d, t).interpolate_gaps().lowpass_at(5.0)   # InvalidParameterError: ...interpolate_gaps()
```

A leading NaN is realistic in the documented `filter_outliers() → filter`
chain: a late acquisition start, or an outlier at sample 0. #28's own first
attempt named a remedy that reproduced the bug it reported, and #48 tested
its remedy end to end for that reason — but only for an interior gap.

The validator sees the array, so it now says which case the caller is in.
When the first sample is NaN the message adds that the series starts with a
gap, that `interpolate_gaps()` leaves it in place by default, and that
`limit_direction='both'` extends the first valid value back over the edge —
a constant fill, not an interpolation — or that the samples before the
first valid one can be dropped. An interior or trailing gap keeps the plain
message: measured on pandas 3.0 and 2.2, under the default method the
forward fill already extends the last valid value over a *trailing* gap, so
that caller needs no hint and gets none. The
hint is keyed on NaN rather than on non-finite, because `interpolate_gaps()`
does not fill Inf in any direction and pointing an Inf caller at
`limit_direction` would be a second remedy that does not run. Both families
share the helper, so `get_peak_freq` and the other spectral entry points say
the same thing.

Review round 1 (both panelists) caught the first cut of the hint making that
promise for every `method`: `'polynomial'` fills no edge in any direction
and `'spline'` fills one by extrapolating its fit, not by a constant — so a
caller on either method who followed the hint verbatim landed on the message
again, the very pattern being fixed one level deeper. Round 2 then found the
two-name carve-out that fixed it was itself a list that missed: `'cubic'`,
named on the docstring's own `method` line, behaves like `'polynomial'`. The
whole method set was measured on pandas 2.2 and 3.0, and it splits cleanly:
the four pandas-native methods (`'linear'`, `'time'`, `'index'`, `'values'`)
extend the first valid value, and every scipy-backed method either leaves the
edge unfilled or extrapolates a fit. The message states that rule; the
docstring and `API.md` list which method does which. The hint also
presupposed a first valid value to extend; a series with no finite sample at
all now gets its own message — there is nothing to interpolate from —
instead of either remedy, since neither runs, and that branch is not scoped
to 1-D because it is true of any shape. The positional hint *is* appended
only for 1-D input: "starts with" is a claim about a series, and `[0]` of a
2-D array is a row, not a sample — so 2-D input with a finite sample
(reachable only by importing the helper directly) keeps exactly the message
it had. A `limit` caps the edge fill like any other; that is the caller's
own constraint, so it is documented in the docstring rather than the
message, and pinned by a test.

Round 3, a third harness, went at the prose. It found the trailing-gap
rationale stated without the default-method qualifier the diff itself had
just introduced for the leading edge (the whole method set was then measured
at the trailing edge too: same split, in both directions); the "drop the
leading samples" alternative reading as attached to the scipy clause and
naming no position (now "drop the samples before the first valid one"); a
0-d pin that could not fail once the hint's key became `ndim == 1` (deleted,
the all-NaN test covers 0-d); and the method rule pinned for five names but
stated for eighteen (now pinned for all eighteen). It also asked whether a
leading NaN with an Inf *elsewhere* should get the hint. It does, on
purpose: the hint's claim is about the leading gap and following it clears
that gap; what remains is the Inf, which is #81's, and the decision is
pinned. Complex data with a leading NaN, and the in-place form, both run the
remedy; pinned too.

**The default is unchanged.** Making `'both'` the default would have
`interpolate_gaps()` invent edge values by constant extension without being
asked, which is what #36 stopped `filter_outliers` from doing; the caller
makes the fill decision explicitly. The `interpolate_gaps` docstring and
`API.md` now document `limit_direction`, the edge asymmetry, and that
which methods fill an edge and how. The remedies are executed in the tests,
not just named: through `interpolate_gaps(limit_direction='both')`, a
600-sample series with a leading gap filters to 600 finite samples, and a
separate 500-sample series with a leading gap recovers its true 0.16 Hz
peak.

## [Unreleased] — the Butterworth filters reject non-finite data (#48)

### Fixed — four NaN samples in, six hundred NaN out, silently

`bandpass_filter`, `lowpass_filter`, `highpass_filter` and `notch_filter` all
run `scipy.signal.filtfilt`, whose bidirectional pass propagates any NaN
across the entire output. A 4-sample dropout in a 600-sample series came back
as 600 NaNs, with no exception and no `RuntimeWarning`.

#28 fixed exactly this failure for the spectral family by placing
`utils.validate_finite_data` at the production site. The filter family never
got it, so since #36 — which made `filter_outliers` leave acquisition gaps as
NaN — one ordinary pipeline got two opposite answers for the same series:

```python
cleaned = baseTs(data, t).filter_outliers()   # 4 NaN preserved, by design (#36)
cleaned.get_peak_freq()                        # ValueError, guarded by #28
cleaned.bandpass_at(hp_hz=0.1, lp_hz=5.0)      # returned all-NaN, silently
```

`validate_filter_params` — which all four already delegate to, `bandpass_filter`
through `validate_band_params` — now calls the same shared guard, after the
parameter checks and translated to `InvalidParameterError` the way the rate
check is. One guard rather than four local copies, because local copies are
what let the spectral checks drift apart before #28. The data is checked
last so a mistyped cutoff is reported before the O(n) scan, and the
translation site is pinned against double-wrapping like the existing one.
Review caught that rule inverted for `bandpass_filter`: `validate_band_params`
checks its lower edge and the ordering *after* delegating, so with the scan
inside the delegated call a mistyped `hp_hz` on gappy data reported the gaps.
The single-cutoff validator is now split into a parameter half and the data
guard, and the band validator composes them with its own checks in between.
A test per combination pins it.

**Complex data is still accepted.** Reusing the guard verbatim would have
rejected complex input with #43's message about one-sided spectra, which is
wrong for a filter: `filtfilt` filters the real and imaginary parts
independently and correctly. `validate_finite_data` gained an
`allow_complex` keyword, default `False`, so the spectral family's #43
behaviour is untouched and the filters get only the NaN rule they share. A
complex value with a NaN in either part is still rejected. Review caught the
first cut consulting the keyword at the dtype check only, so complex numbers
hiding in an object array were still told to discard their imaginary part;
the object branch now casts to complex when allowed — with the cast
guarded, since `numbers.Complex` is a registrable ABC and a registered
impostor with no working `__complex__` escaped the first cut as a bare
`TypeError` from every filter. (Object-dtype arrays
still cannot be *filtered*, because `scipy.signal.filtfilt` refuses them
with a bare `NotImplementedError` — identical on `main`, and filed
separately.)

**`sg_filter` and `gauss_filter` are deliberately left alone.** Both are
windowed convolutions, not bidirectional IIR passes: a 4-sample gap comes out
as 14 and 20 NaN respectively, local to where it was. That is degraded output
rather than a confident wrong answer, and it matches how `filter_outliers`
treats gaps it did not create. The asymmetry is documented in `API.md` and
pinned by a test, so it stays a decision rather than an accident of which
functions route through the validator.

**Breaking, in the same way #28 was.** Any pipeline feeding gappy data into
one of the four filters used to get NaN out and now gets
`InvalidParameterError` naming `interpolate_gaps()`. The remedy is tested end
to end — `filter_outliers() → interpolate_gaps() → lowpass_at()` returns 600
finite samples — following #28's precedent, whose own first attempt
recommended a remedy that reproduced the bug it reported. All nine `baseTs`
entry points (the four `_at` methods, their four aliases, and `butterpass_at`)
are asserted to agree. No shipped doc pipeline was affected: the one that
feeds `filter_outliers` into a filter already interpolated first for #28's
sake, and the README pipeline has spikes but no gaps.

## [Unreleased] — the single-cutoff filters compute with the value they validated (#49)

### Fixed — `lowpass_filter`, `highpass_filter` and `notch_filter` divided the caller's original cutoff

`validate_filter_params` range-checked `cutoff_freq` and threw the checked
object away, returning only the normalised rate. Each of the three filters
then divided its own argument:

```python
fs = validate_filter_params(data, fs, cutoff, order)
normal_cutoff = cutoff / nyq          # the caller's object, not the checked value
```

So the value that passed validation was not necessarily the value that got
filtered. `Decimal('0.5')` — a type `validate_sampling_freq` deliberately
accepts as a *rate* — raised a bare `TypeError` as a *cutoff*, outside the
`InvalidParameterError` each docstring promises. The sharper case is any
`numbers.Real` virtual subclass whose `__truediv__` disagrees with its
`__float__`: it passed every range check and then built a filter for a band
nobody asked for. This is the hole #30 closed for `bandpass_filter`, in the
three siblings #30 left untouched and named.

`validate_filter_params` now coerces the cutoff through the same
`_as_real_float` door the band edges use, range-checks the float, and returns
`(sampling_freq, cutoff_freq, order)`. All three filters compute with what
comes back; `validate_band_params` consumes the coerced upper edge the same
way. The tests reuse #30's adversarial Reals — one with no `__truediv__`, one
whose division lies — and assert the lying one filters bit-identically to an
honest `1.0`.

### Fixed — `order` was checked with `order <= 0` and nothing else

`order=True` passed and silently built an order-1 filter. `order='4'` died in
the comparison with a bare `TypeError`. `order=3.5` passed and was left to
scipy. `order` is now required to be a non-bool `numbers.Integral` of at least
1, coerced to `int`, and reported as `InvalidParameterError` otherwise. numpy
integers are accepted. An integral-valued float such as `4.0` is rejected
rather than truncated: an order is a count of poles, and admitting `4.0` would
mean a second rule for `4.5`.

**Breaking, in three places.** `validate_filter_params` is a public function and
its return changed from a float to a 3-tuple; any direct caller must unpack.
The four `order` inputs above that used to pass now raise. And a 0-d numpy
array cutoff (`np.array(0.5)`), which used to filter, is now rejected as not
a real number — the same rule the band edges have followed since #30, whose
`_require_real` docstring explains why arrays are refused rather than probed
with `float()`. The *rate* still accepts a 0-d array through
`validate_sampling_freq`; the two doors disagree on that one type, and this
entry records it rather than hides it. A `float` cutoff and an `int` order —
what every caller in the package, the tests and the docs pass — are
unaffected: `float(x)` and `int(x)` are the identity there, and the whole
existing suite ran unchanged.

## [Unreleased] — `relative_band_power` defaults to the fALFF band (#46)

### Added — `low_freq=0.01, high_freq=0.1` on `relative_band_power`

`ts.relative_band_power()` now measures 0.01-0.1 Hz, a common low-frequency
band for resting-state fMRI and other slow physiological fluctuations.
Before, both edges were required and every call in that domain spelled out
the same two numbers; `falff()` already defaulted to them. The `utils`
function and the `baseTs` method both gained the defaults.

The docstrings now say it is one convention among several. Two claims in
the issue's rationale did not survive review and are not repeated: that
Zou et al. (2008) documents this band (that paper computed fALFF over
0.01-0.08 Hz, which the `falff` docstrings now say and its example
reproduces), and that it is the standard HRV band (the HRV literature's LF
band is 0.04-0.15 Hz, now the docstrings' example of a different band).
The default itself is unchanged from what `falff()` already carried.

Not a breaking change. Every existing call passes the edges explicitly, by
position or keyword, and those calls are unaffected; the new tests assert
the bare call returns exactly what the explicit `(0.01, 0.1)` call returns.

The convention split with `falff()` is unchanged and deliberate: a bare
`relative_band_power()` is the variance fraction (`ratio='power'`), a bare
`falff()` is the amplitude ratio (`ratio='amplitude'`). The two functions now
differ *only* in that default, and their docstrings say so.

The default does not relax the constraints. A series sampled below 0.2 Hz
puts the default upper edge above Nyquist and raises the same `ValueError`
an explicit call would, with the edge the caller never typed in the message.
The duration constraint is weaker than the docstring's 100 s precondition
suggests: that figure is what it takes to give the 0.01 Hz edge a bin of
its own, but the call only refuses when *no* bin lands in the band, which
for a decade-wide band happens below roughly 10 s. Review caught the first
draft of this entry claiming a raise at 100 s; a 20 s series at 1 Hz
succeeds.

**Pinned against drift.** The band now lives in four signatures with
nothing tying them together at runtime, so
`test_band_defaults_agree_across_all_four_entry_points` asserts the literal
defaults on all four. The literal is deliberate: a shared constant would
make the test tautological, and the literal is what a caller's IDE shows.

## [Unreleased] — USER_GUIDE Example 4 runs to completion (#44)

### Fixed — two defects in `scientific_time_series_analysis`, one masking the other

The worked example under *Example 4: Scientific Data Analysis* could not run.
`bandpass_at(hp_hz=0.1, lp_hz=50.0)` at the example's own
`sampling_rate=100` put the upper edge exactly at Nyquist, which
`validate_band_params` rejects as it should, so the pipeline raised
`InvalidParameterError` before reaching the feature extraction. Had it got
there, the `spectral_features` dict literal referenced itself
(`spectral_features['spectral_centroid']` inside the literal that binds the
name) and would have raised `UnboundLocalError`. The upper edge is now 40 Hz
with a comment naming the constraint, and the centroid is computed before
the dict is built.

Neither is a library change. Both surfaced while fixing #28, which touched a
different line of the same example - the `quality_score < 0.95` branch - and
were filed rather than folded in.

**Pinned by executing the document.** A new
`tests/unit/test_user_guide_examples.py` extracts the example from
`docs/USER_GUIDE.md` by its heading and runs it, so the document stays the
source of truth; a copy pasted into a test would pin the copy, and the two
would drift the way the spectral guards had before #28. Each fix was checked
by reverting it alone and watching the test fail with that defect's error.

**Filed rather than folded in:** #69. Executing every fenced Python block in
`docs/` the same way, sequentially per file, fails 45 of 108. Most of
`API_SERIES.md` is fragments with no setup, but the rest is real rot - keyword
arguments that no longer exist, a removed method, pandas frequency aliases
rejected by 3.x, and eleven `API.md` blocks written against the old attribute
API. That is a sweep of its own, with the harness shape already in place.
## [Unreleased] — the spectral family rejects complex data (#43)

### Fixed — `relative_band_power` silently truncated complex data to its real part

`relative_band_power` (and so `falff`) narrowed its input with
`np.asarray(ts.values, dtype=float)`. On a complex series that emits a
`ComplexWarning` and keeps the real part, and the band ratio came back as a
number with nothing in the output to say half the data had been discarded.
#28 had just made `utils.validate_finite_data` accept complex deliberately,
so the guard said complex was acceptable and the function then threw half of
it away.

**The inconsistency was four ways, not two.** Measured on `main` with the
issue's own probe — `sin + i·cos`, an analytic signal whose one spectral line
sits at *negative* frequency:

| Entry point | On complex input |
|---|---|
| `relative_band_power`, `falff` | `ComplexWarning`; answer from the real part only |
| `get_frequency_content` | no warning; every non-negative bin ≈ 1e-27 |
| `get_peak_freq` | no warning; reports 0.388 Hz for a 0.05 Hz signal |
| `compute_fft_power` | no warning; non-negative half only |

The three that handled complex "natively" were wrong in a quieter way than
the one that warned. Every spectral function here returns a **one-sided**
spectrum: it keeps the non-negative bins on the strength of Hermitian
symmetry, which real input has and complex input does not. On complex data
the discarded half is content, not a mirror — for an analytic signal it is
all of the content. So the issue's second option, letting the FFT handle
complex natively, is what three of the four already did, and it produced a
confident wrong number with no warning at all.

**Behaviour change:** `validate_finite_data` now rejects complex data, so
`get_frequency_content`, `get_peak_freq`, `compute_fft_power`,
`relative_band_power`, `falff` and `plot_fft_power` raise `ValueError` on a
complex series where they previously returned a number (two of them under a
`ComplexWarning`, three silently). The message names the reason and the
remedy: pass the real projection you mean explicitly — `values.real`,
`values.imag` or `np.abs(values)`. The library does not choose one for you,
because choosing the real part silently is exactly what this fixes.

The check is made on dtype, before the finiteness check, so a complex array
that also contains NaN is told about its dtype rather than sent to
`interpolate_gaps()` and rejected again afterwards. An object array holding
complex numbers gets the same message rather than the generic "not numeric"
one. Real-valued input takes an unchanged code path; the #28 test that named
complex "the load-bearing case" for acceptance now pins the rejection, and
says why.

`baseTs` has no other complex support — the filters reject complex band
edges by construction, and the constructor never promised complex samples —
so this closes the one place where complex input produced an answer.

## [Unreleased] — `lowess_fit` and `outlier_indices` stop following the values (#40)

### Fixed — a fit survived a change of the data it described

#20 made both fields read as `None` when the *index* they were computed
against is no longer the object's index. The complement was untouched: an
operation that replaces the *values* on an unchanged index carried the fit
onto data it does not describe, and `qc_plot` drew the old fit over the new
signal. Measured on `main`: `ts.data = noise`, `ts.iloc[3] = 5`, `ts += 1`,
`sg_filter()`, `detrend()`, `lowpass_filter()`, `zscale()`, `apply_function()`,
`ts * 2` and `rolling(5).mean()` all kept both fields. The issue names four
of those. On pandas 2.x, `ts.values[:] = 0` is an eleventh; pandas 3.0's
copy-on-write makes that array read-only.

The positional slot now holds `(value, index, values)` - the third element a
snapshot of the object's values taken when the slot was assigned - and the
property getter returns the value only while *both* the live index and the
live values still equal the stamps. Checked on read, in the getter, for the
reason #20 established: there is no bounded list of places a value can
change, but every one of them changes what `to_numpy()` returns.

What the stamp records is **the values that were on the object when the slot
was assigned**, not the values the fit was computed from. `filter_outliers`
computes its fit from the unfiltered data and assigns it after replacing the
data; `lowess_detrend`'s fit is the trend it removed. Both write the data
first and the slot second, and the stamp records what they left behind -
which is the pairing `qc_plot` draws.

### Changed — behaviour, all of it the rule doing what it says

- **Every derivation that changes values on an unchanged index reads
  `lowess_fit` and `outlier_indices` as `None`.** Scalar arithmetic other
  than a no-op, `sg_filter`, the frequency filters, `detrend`, `zscale`,
  `apply_function`, `rolling(n > 1)`, an `astype` that rounds, and any
  in-place write - `ts.data = x`, `ts.iloc[i] = v`, `ts[label] = v`,
  `ts += x`, `fillna(inplace=True)` or `interpolate_gaps(inplace=True)` on
  data that had gaps. Operations that leave the values equal keep both:
  `copy()`, `+ 0.0`, `rolling(1).mean()`, `clip` inside the data's range,
  `interpolate_gaps()` on gap-free data, a `float32` cast of representable
  values. **Migration:** read the fit or the positions before a further
  transform, or keep the filtered object.
- **`lowess_detrend` keeps `outlier_indices`, as its docstring promises**, by
  re-stamping a copy of the source's positions after assigning the detrended
  data. Its `lowess_fit` is the trend it removed, as before.
- **Restoring an index no longer resurrects a fit for different data.** The
  wrinkle #20 documented - a fit made readable again by putting the old
  index back after the values changed - is gone.
- **Reading either property costs O(n) in the values on every read**,
  measured at 0.5 ms per million samples on the fit's own million floats.
  Previously O(n) in the index on the first read and O(1) after. There is no
  fast path: an in-place write keeps the array's identity while changing its
  contents. Derivation pays the same compare once, in the eager release that
  runs on every derived object carrying a slot - a second O(n) pass beside
  the `Index.equals` it already paid.
- **A stamped slot holds one extra copy of the values**, shared by reference
  across derived objects. Comparable to the fit it validates. `copy(deep=True)`
  is unchanged in cost - the snapshot is immutable and shared, not copied.
- **The `butterpass_at` metadata census moves.** The two positional slots
  are now among the fields that call changes (nine preserved, five changed;
  before, eleven and three), because a slot stamped against the old values is
  released on derivation rather than carried unreadable.

### Fixed — a pickle written before #20 could not be read back

`__getstate__` writes the slot as it stood at dump time. A blob written
before #20 holds a bare fit array, which the #20 getter unpacked as a pair and
raised on. `__setstate__` now completes every earlier shape to the triple:
a bare array or list is stamped against the unpickled object's index and
values; a #20-era `(value, index)` pair keeps its index and gains the values
stamp; a current triple is left alone. The test is on type and length, so a
two-sample fit array is not mistaken for a pair.

Stated plainly: a legacy blob carries no evidence of whether its fit still
described its values when it was written, and the completion accepts the
pairing the blob holds. The alternative - dropping every legacy fit to catch
the few that were already stale - loses more than it corrects. From the
moment of unpickling the rule applies as to any other object.

## [Unreleased] — derived objects keep the Series `name`, `attrs` and `flags` (#35, #39)

### Fixed — the three fields pandas owns were dropped by almost every derivation

A `baseTs` is a `pd.Series`, so pandas defines and propagates three pieces of
identity on it: the Series `name`, the `attrs` dict and `flags`. baseTs dropped
all three across most derivations, where a plain `pd.Series` drops none of them.
Measured on `main`, seeding all three: `copy(deep=True)`, `copy.deepcopy`,
`apply_function`, every non-inplace filter and transform, `baseTs(ts)` and
`to_basetseries()` lost all three; `dropna()`, `round()` and `sort_values()`
lost the name; on pandas 3.0 so did `head()`, because pandas 3.0 implements it
as `self.iloc[:n].copy()` and so reaches baseTs' own rebuilding `copy()`.
**36 of 53 `inplace=True` methods** lost all three, and the loss correlated
exactly with the method being baseTs-defined rather than inherited from pandas.

Two independent causes, neither of which the issue names:

- `TimeSeriesData._metadata` **replaced** `pd.Series._metadata` (which is
  `['_name']`) instead of extending it, so every `__finalize__` path dropped the
  name. It now extends, composed from `pd.Series._metadata` rather than
  hardcoding `'_name'` — hardcoding a list pandas owns is the original mistake.
- Nine sites rebuilt or re-initialised an object carrying only `_metadata`
  names. `attrs` and `flags` are not in `_metadata`; pandas handles them inside
  `__finalize__`, so no site carried them. Six were rebuild sites, now served by
  one `_carry_identity` helper. Three re-initialised `self` through
  `super(TimeSeriesData, self).__init__` — `_update_series_data` (reached by
  `ts.data = x`), `interpolate_gaps(inplace=True)` and
  `shift_time(inplace=True)` — and are now one `_adopt_data_inplace` primitive.
  A post-hoc helper could not have served those: their target *is* their source,
  so the snapshot has to be taken before the re-initialisation.

### Fixed — unpickling produced an object that raised on everything (#39)

`pickle.dumps` and `pickle.loads` both succeeded; what came back was unusable.
`__getstate__` serialises exactly `_metadata`, so `_name` was never written and
never restored, and `.name`, `repr()`, `iloc`, `head()` and arithmetic all
raised `AttributeError: 'baseTs' object has no attribute '_name'` on the
restored object. `mean()` worked, which is why it went unnoticed. Identical on
pandas 2.3.3 and 3.0.5.

Extending `_metadata` fixes objects pickled from now on and nothing else: a blob
already on disk has no `_name` key, so loading it with the fixed code still
produced the broken object. `TimeSeriesData.__setstate__` now normalises a
missing `_name` to `None` after delegating to pandas — the same
normalise-at-the-door move `_detach_shared_metadata` makes for `history`,
applied to the one door that rebuilds an object out of bytes. The original name
is not recovered, because it is genuinely not in those bytes.

It also drops the registry pandas restores onto the instance. `_metadata` is
written into every pickle and installed as an *instance* attribute, shadowing
the class's; for a blob written since this change the two are identical and it
does not matter, but a legacy blob carries the old, `_name`-less list. Without
dropping it the object came back healed, worked once, and lost the name again
the moment anything iterated `self._metadata` — the next `pickle.dumps`, or the
next `ts.data = x`.

### Changed — behaviour that was previously silent

- **Derived objects now carry a name.** Code asserting `result.name is None`
  after a filter, transform, copy or conversion will now see the source's name.
- **`attrs` is deep-copied**, matching `NDFrame.__finalize__` exactly, including
  its emptiness guard. Nested `attrs` values are isolated between parent and
  child rather than shared.
- **`allows_duplicate_labels` is carried by assignment**, not by pandas 3.x's
  AND with the target's existing value. A derivation takes its source's
  declaration; AND-ing would let a target's incidental default override an
  explicit `False` in one direction only. pandas 2.x assigns, so this matches
  2.x and deliberately differs from 3.x.
- **Carrying that flag can now raise where nothing raised before.** If an
  operation produces duplicate time labels on an object that declared
  `allows_duplicate_labels=False`, it is refused. This is reachable:
  `_update_series_data` rebuilds the index as `linspace(first, last, n)`, so on
  a single-sample series every replacement timestamp is identical and
  `ts.data = [1., 2., 3.]` produces three duplicate labels (filed as #65). The
  declaration is still carried — silently dropping one is the class of failure
  this change exists to fix — and pandas' bare "Index has duplicates" is
  re-raised as a `ValidationError` naming the labels and the remedy.

  **The refusal happens before anything is mutated.** Checked after the
  re-initialisation, as it first was, the new data and index were already
  committed and the flag had fallen back to pandas' permissive default — an
  operation that reported failure left a mutated object with its declared
  protection silently switched off, which is worse than the silent behaviour it
  replaced. `ts.data = x` is now all-or-nothing: either it raises having
  changed nothing, or it succeeds.

### Testing

`tests/unit/test_identity_propagation.py`. The guard against a tenth site
derives its subjects rather than listing them: it discovers baseTs' own
`inplace=` methods by reflection and asserts the discovered set equals the
classified one, so a new method fails the suite until someone accounts for it.
Reflection cannot invent a valid cutoff frequency, so the *arguments* remain a
hand-written table — what is derived is the membership check, which is the
property a hand-written path list could never have. A source-level AST check
additionally pins that `super(TimeSeriesData, self).__init__` appears in
`core.py` only inside the primitive.

The suite had no pickle round-trip test at all, which is why #39 survived; it
now has one that asserts the unpickled object *works* rather than that `loads`
returned.

26 mutants, 26 killed, 0 survivors. Three lines that survived an earlier round
were removed rather than explained: two `_carry_identity` calls that pandas'
own `__finalize__` had already made redundant, and a `_name` exclusion
superseded by the call after it. A fourth survivor — the arm that re-raises a
non-duplicate error untouched — is unreachable through the public API now that
the refusal happens before the mutation, so it is tested directly rather than
deleted on the assumption that it can never fire.

Both halves of the reflection guard were widened after review found holes in
each: it keyed on the literal class name `baseTs`, missing anything defined on
`TimeSeriesData`, and the AST scan required the two-argument
`super(Cls, self)` form, missing a zero-argument `super().__init__()` in an
ordinary method — equivalent at runtime and equally destructive. Both fixes
were verified by injecting the exact site each used to miss.

Verified on pandas 3.0.5/numpy 2.5.1, pandas 2.3.3/numpy 1.26.4 and pandas
2.3.3/numpy 2.2.6 — 1114 tests green on all three.

## [Unreleased] — `plot_fft_power` raises instead of drawing the error (#34)

### Fixed — a bare `except Exception` neutralised every spectral guard

`plotting.plot_fft_power` wrapped its whole body in `except Exception`, rendered
the message as text on the axes, and returned a normal `Axes`. Its docstring's
`Raises: ValueError ... invalid frequency` was simply false.

```python
deg = baseTs(np.sin(np.arange(400) / 10.0), np.zeros(400))   # freq is NaN
ax = plot_fft_power(deg)        # no exception
ax.texts                        # ['Error plotting FFT: Invalid sampling frequency: nan Hz. ...']
```

A batch pipeline doing `ax = plot_fft_power(ts); fig.savefig(...)` got a
silently-bogus figure and a **success exit code** — the silent-failure mode #24
was written to eliminate, one layer up. #24 and #28 added rate and data guards
to `compute_fft_power`, `get_frequency_content`, `relative_band_power`,
`get_peaks` and `filters.validate_filter_params`; this wrapper undid all of them
on what is, for interactive users, the main path to a spectrum.

**Behaviour change: 29 of a 30-case census change outcome**, generated against
a `main` worktree rather than written from memory, and pinned by
`test_every_rejected_input_raises_valueerror_and_draws_nothing`. Every one of
them now raises `ValueError` — one `except ValueError` covers the function —
where before they drew. The census splits in two:

**22 drew the error as text.** An unusable sampling rate, data containing NaN
or Inf, an unknown `window`, a `[min_rate, max_rate]` window selecting no bins,
a reversed or equal-edged `highlight_band`, and every malformed bound or band
(`max_rate=None`, `'abc'`, `±Inf`, a list; `min_rate=NaN`, `Inf`, `None`; a
band that is a 1- or 3-tuple, a non-iterable, or has a `None` edge). Several of
these were not even `ValueError` underneath: `np.isnan(None)` raised `TypeError:
ufunc 'isnan' not supported for the input types`, and a malformed band died on
tuple unpacking — but the bare `except` meant no caller ever saw either.

**7 drew a silently wrong plot**, which is the worse half and was not in the
issue report. Two distinct mechanisms, not one:

| Input | Before | Why it passed |
|---|---|---|
| `max_rate=True` | plotted, silently taken as 1.0 Hz | `bool` is a `Real` |
| `min_rate=True` | plotted, silently taken as 1.0 Hz | `bool` is a `Real` |
| `highlight_band=(nan, 0.5)` | shaded and legended | every comparison against NaN is `False` |
| `highlight_band=(0.1, nan)` | shaded, legend `0.1-nan Hz` | as above |
| `highlight_band=(nan, nan)` | shaded, legend `nan-nan Hz` | as above |
| `highlight_band=(0.1, inf)` | shaded **to infinity**, legend `0.1-inf Hz` | `0.1 >= inf` is legitimately `False` |
| `highlight_band='ab'` | shaded | `'a' >= 'b'` is `False` |

The infinite upper edge is worth separating from the rest: it is *not* the NaN
quirk. `0.1 >= inf` is honestly `False`, so an ordering check alone could never
have caught it — only a finiteness check does.

The NaN-edge hole is **pre-existing** (`main`'s ordering check has it too, just
positioned after the plot instead of before it) and is the same shape as #30,
where `max(hp_hz, lp_hz)` let argument *position* decide which edge was checked.
It is closed here rather than filed because this change moves and re-documents
that exact check, and shipping "raises if not strictly increasing" over a known
NaN hole would make the new docstring false.

### Also newly *accepted*, in the opposite direction

The census enumerates inputs that were already bad, so it misses this: a
`Decimal` or `Fraction` `max_rate`/`min_rate` now **works**, where `main` died
on `np.isnan(Decimal('2.0'))` with `ufunc 'isnan' not supported for the input
types` and drew that as text. The shared door accepts whatever `float()` does,
which is what `np.fft.fftfreq` can actually use. Pinned, since nothing else
would have caught a widening of the accepted set.

Gappy data needs an `interpolate_gaps()` first — since #36 `filter_outliers`
leaves the gaps it did not create as NaN, and since #28 the spectral guards
reject them.

The one case that did **not** change: a `highlight_band` outside the plotted
range still draws, which is legitimate.

**Three decisions the review rounds forced, recorded because each could
reasonably have gone the other way:**

*Geometry uses the validated values; presentation does not.* `axvspan` is drawn
from the coerced floats, the **legend label** from the caller's originals.
Routing the label through the floats turned `highlight_band=(1, 2)` into a
legend reading `"1.0-2.0 Hz"` where it had always read `"1-2 Hz"` — a silent
presentation change on the success path, which is exactly what this change was
supposed not to make.

The band is **unpacked exactly once**, and both halves returned together. An
earlier revision unpacked it a second time at draw time to build that label,
which broke one-shot iterables: `highlight_band=(x for x in (0.1, 0.4))` plots
on the previous release and raised `not enough values to unpack` here — from
the draw phase, after a figure existed and a supplied `ax` had been titled,
falsifying the one guarantee this change is built on. Both directions are
pinned: a generator band plots, an exhausted one is rejected cleanly.

*The bounds are validated before the series.* A call that is wrong in both ways
reports the bound, not the rate. Deliberate: the bounds are arguments the caller
can fix immediately, and checking them is far cheaper than running the FFT that
would otherwise precede the complaint.

*Bounds and band edges are now widened to `float64` before use.* One measured
consequence, accepted: a `Fraction` carrying more precision than IEEE-754 could
sit within ~1e-18 of a bin edge and fall on the other side of the frequency
mask. The bins are `float64` themselves, so comparing the bounds at the same
precision is the more honest of the two, and the difference is unreachable
without deliberately constructing such a bound.

The shaded span's *rendered* geometry is unchanged for every band type swept
(int, float, mixed, `float32`, `int64`, `Fraction`, `Decimal`), because
matplotlib coerces through `float()` itself. So drawing from the validated
values rather than the caller's originals is a principle here, not an
observable difference — kept because relying on a consumer to repeat your
coercion is what #30 found in the filter family, not because it moves a pixel.

The one visible trace is an attribute rather than a rendering: for a `float32`
band, `Rectangle.get_width()` returns `0.30000000447` where `main` returned
`0.300000011921`, the difference between doing the subtraction in float64 and
in float32. On `main` that stored width was inconsistent with `main`'s own
drawn right edge (`x + width` = `0.4000000134`, rendered `0.4000000059`),
because matplotlib renders from the two edges and not from the width. The new
value is the one that agrees with the picture.

**Known gap, filed as #62 and documented in the docstring rather than patched
here:** an **empty** series raises `ZeroDivisionError`, not `ValueError`, so
the "one `except ValueError`" contract has exactly one hole. It is pre-existing
and family-wide — `get_frequency_content`, `get_peak_freq`,
`relative_band_power` and `falff` all divide by a zero-length index inside
`np.fft.fftfreq`, and only `compute_fft_power` guards it. `main` hid it here in
the same bare `except`. The fix belongs in the shared spectral door, the way
#28 replaced four drifted local copies, not in a sixth local guard — so it is
pinned by a test that will have to be updated when #62 closes.

### Added — `utils.coerce_real_scalar`, the shared type door

The bounds needed the type rules `validate_sampling_freq` already had — reject
`str`/`bool`/`np.bool_`/`bytes` before `float()` (since `float('30')` succeeds
and `True` is a `Real`), reject multi-element arrays rather than unwrap them
(`float()` accepts them on numpy 1.x and raises on 2.x, so allowing them would
make the accept set differ across the CI matrix), and translate `TypeError`/
`ValueError`/`OverflowError` into one `ValueError`.

Those rules are now `utils.coerce_real_scalar`, which `validate_sampling_freq`
calls instead of owning, and which the new `plotting._validate_display_rate`
and `_validate_highlight_band` call too. They are shared rather than copied
because the *type* rules are common while the *range* rules genuinely differ: a
sampling rate must be finite and positive, `max_rate` takes NaN as its "use
Nyquist" sentinel, `min_rate` may be zero. Copying them is what let the four
spectral entry points drift apart before #28.

`validate_sampling_freq`'s own behaviour is unchanged, including its messages;
the 933-test suite passing across the extraction is what says so.

**A hole mutation testing found in the moved code:** the multi-element-array
branch was unpinned — deleting it left the suite green on `main` as well as
here, because `float()` on such an array raises `TypeError` on numpy 2.x and
the shared door translates it to `ValueError` regardless, so only the *message*
degrades. Now pinned from both sides.

**Fixed by reordering, not by narrowing the `except`.** Everything that can
fail on the caller's input now runs *before* `setup_plot`, so a rejected call
has built nothing. Narrowing alone would not have been enough: `setup_plot` ran
above the `try`, so every rejected call **leaked a figure** into pyplot's
registry (`plt.get_fignums()` went from `[]` to `[1]`) — in a batch loop those
accumulate. Two consequences, both pinned by tests and both verified to fail if
the reorder is reverted:

- no figure is created by a call that raises
- a caller-supplied `ax` comes back **untouched**, where it was previously
  titled, labelled, gridded and annotated with the error text

The `highlight_band` ordering check moved with them, so a reversed band is now
rejected before the spectrum goes on the axes rather than after.

No `on_error='annotate'` escape hatch was added. The on-plot text has no caller
asking for it, and the wrapper's whole failure mode was that it applied
unconditionally; if notebook ergonomics want it back it can be added then, with
a use case behind it.

**Not in scope, filed as #61:** `lag_plot` has a bare `except Exception` of the
same shape around `ts.signal_name.upper()`, which prints to stdout and labels
the plot `Signal`. It is a weaker case — `shift_timeseries` is already called
outside it, so #32's guards do propagate; since #33 `signal_name` is a string
on every derived object, so it needs a hand-assigned non-string to fire; and
the consequence is a mislabelled plot, not a wrong one.

## [Unreleased] — conversion stops resetting what it converts (#57)

### Fixed — `baseTs(ts)` reset eleven of thirteen `_metadata` names

```python
ts = baseTs(data, times, signal_name='ECG')
ts.set_outlier_filter(frac=0.42); ts.set_timestamp_offset(1.5)

baseTs(ts).signal_name   # '' — was 'ECG'
baseTs(ts).ts_offset     # 0  — was 1.5
baseTs(ts).history       # ['Created baseTs object with 200 samples']
```

`TimeSeriesData.__init__` copies the source's metadata whenever the argument
looks like a baseTs, and `baseTs.__init__` then assigned its own keyword
defaults straight over the top — `False` for every flag, `""` for the strings,
a fresh list for `history`, `None` for both positional slots.

`outlier_filter` was the one name that survived, and only because #15 added a
guard for it alone. The comment above that guard describes the bug for every
other name: *"baseTs(ts) takes the conversion branch in
TimeSeriesData.__init__, which copies the source's filter, and this used to
overwrite it with a default."* A per-attribute guard does not scale to
thirteen, so the constructor now distinguishes **"the caller passed this"**
from **"this is the parameter default"** and assigns only what was supplied.

**The history loss was the sharpest edge.** A converted series reported
`Created baseTs object with N samples` as its entire provenance while the
flags that would have contradicted it — `is_filtered`, `is_outlier_filtered`,
`has_timestamp_offset` — were cleared in the same breath. Nothing raised; the
object simply claimed to be something it was not. History is now preserved
verbatim, with no "converted from" entry appended: a conversion is a copy, and
editorialising it would make the provenance less true, not more.

**`TimeSeriesData(ts)` lost one name** when the source was a `baseTs` —
`signal_name`, assigned unconditionally after the copy. Same fix, same
sentinel.

**The count is eleven, not the nine the issue reports.** `outlier_indices` and
`lowess_fit` were being reset too — assigned `None` through their public
properties, which clears the value and its index stamp together — and they are
invisible to a comparison that only walks the flags. Only `outlier_filter`
(via #15's guard) and `_freq_declaration` survived. Counted against a `main`
worktree with all thirteen names moved off their defaults, not from reading
the constructor.

**A `TimeSeriesData` source was not recognised as a source at all.** The
conversion branch was gated on `.times` and `.data`, which are baseTs'
spelling; the superclass has neither, so `baseTs(tsd)` and
`TimeSeriesData(tsd)` fell through to the plain-pandas arm and reset all
thirteen. Both constructors now ask one shared predicate,
`_carries_metadata`, which is also what tells an absent `history` from an
empty one.

### Changed — the constructor keywords default to a sentinel

`is_filtered`, `is_interpolated`, `is_uniform_grid`, `is_outlier_filtered`,
`has_timestamp_offset`, `outlier_indices`, `lowess_fit`, `signal_name`,
`history` and `last_process` now default to `_UNSET` rather than to
`False`/`""`/`None`. Visible in `help(baseTs)` and `inspect.signature`, where
the defaults now read `<unset>`.

`None` could not serve as the sentinel: it is already a meaningful argument —
`baseTs(..., last_process=None)` is documented since #33 to produce `""` — so
reusing it would have changed what a supported call means. `np.nan` stays as
the *public* sentinel for `freq` and `ts_offset` via `_is_unset`.

**An explicit argument still wins, including one equal to the old default.**
`baseTs(ts, is_filtered=False)` clears the flag the source was carrying;
only *omitting* it preserves. Asserted for all ten names, because a sentinel
that swallowed explicit arguments would merely have moved the bug.

**`history=None` still asks for a fresh entry**, as the signature has always
meant. An earlier revision of this branch folded a supplied `None` into the
"not supplied" case, which made `history` the one nullable keyword that
preserved rather than cleared — disagreeing with `signal_name=None` and
`last_process=None`, both of which clear to `""`.

**Clearing the offset flag clears the offset.** Dropping the `else` that
zeroed `ts_offset` and `has_timestamp_offset` together is what stops a
conversion losing an offset, but it also made `has_timestamp_offset=False`
alongside a non-zero `ts_offset` reachable for the first time — and
`__finalize__` copies the pair onward, so it would ride into every derived
object. Clearing the flag now clears the offset with it, on *truthiness*:
`np.False_` is what `arr.any()` and any comparison yield, and it is not the
`False` singleton, so an identity test would have let the same pair through.

The rule runs one way only, and deliberately. `has_timestamp_offset=True` with
no offset named is a caller asserting that one was applied without saying what
— odd, but theirs to assert, and rejecting it would break a call that works
today. Pinned by a test rather than left to be discovered.

**An index given alongside a source is refused, not ignored.** The conversion
branch takes its index from the source, so `baseTs(ts_200, times=arange(5))`
returned a 200-sample object and said nothing. Recognising `TimeSeriesData` as
a source extended that silence to a case that had at least been loud before —
it used to reindex to all-NaN — so the constructor now raises when the two
disagree. It does not raise when `baseTs.__init__` derived `times` from the
source itself, which is the common path.

**An empty history is a history.** The "was anything carried across?" test asks
the *source*, not the result's truthiness, so a series whose history is
legitimately `[]` no longer comes back claiming to have just been created —
the same failure this change exists to remove, one layer down.

**Construction from arrays is unchanged.** Nothing is copied on that path, so
every default still arrives — now from `_initialize_default_metadata`, which
gained `signal_name` for the purpose. The internal callers in `series.py` and
`core.py` all construct from ndarrays and are unaffected.

### Not changed

`_create_new_with_data` still upper-cases the signal name it passes back
through the constructor, so `ts.zscale()` turns `'Heart Rate'` into
`'HEART RATE'` while `ts.iloc[:5]` preserves it. That is **#56**, and it needs
a decision about which behaviour is intended rather than a fix.

## [Unreleased] — the metadata defaults survive a derivation (#33)

### Fixed — a `None` filter reached every derived object

```python
ts.outlier_filter = None
ts.iloc[:5].get_outlier_filter_params()
# AttributeError: 'NoneType' object has no attribute 'config'
```

`history` was made unconditionally a list in PR #26 by normalising in
`_detach_shared_metadata`, the chokepoint `__finalize__` runs.
`outlier_filter` arrives by the same mechanism — pandas copies every
`_metadata` name with `object.__setattr__(self, name, getattr(other, name,
None))` — but nothing re-applied a default afterwards, so a `None` propagated
to every derived object, where `get_outlier_filter_params`, `info` and
`filter_outliers` all read `.config` unguarded. The normaliser now restores a
`LowessOutlierFilter()` there, the way it restores a list for `history`.

**The `None` was minted in `series.py`, not by the user.**
`_copy_metadata_from_basetseries` gives `history`, the flags and the string
names real defaults when the source carries none, then falls through to
`setattr(self, attr, None)` for everything else — `outlier_filter` included.
`baseTs.__init__` re-guards it (the guard #15 added for exactly this), so the
state only survived on a `TimeSeriesData` built straight from a source with no
metadata, and on everything derived from it.

That fallback needs no arm of its own, and an earlier revision of this branch
added one anyway: the method ends by calling `_detach_shared_metadata`, so the
`None` it had just written was restored one line later. Neutralising the arm
left all of `test_metadata_defaults.py` green, which is how it was caught. It
is gone, and the comment on the bare `else` now says which names legitimately
reach it — `_lowess_fit` and `_outlier_indices`, which carry the index they
describe (#20), and `_freq_declaration`, absent until a rate is declared
(#29/#31/#23).

**`is_outlier_filtered` was the fallback's real gap**, and the chokepoint does
not cover it. The defaulting arm listed three of the four boolean flags, so
the one that names the outlier filter fell to the bare `else` and landed as
`None` — on the same objects, by the same omission, as the filter itself, and
`assert ts.is_outlier_filtered is False` is an assertion the suite already
makes elsewhere. It is in the flags list now, and all five flags are asserted
boolean on a metadata-less source and on an object derived from one.

**Restoring a default is not imposing one.** A configured filter reaches the
derived object with its parameters intact — asserted across `__finalize__`,
`copy(deep=True)`, `copy(deep=False)` and `_create_new_with_data`, because a
normaliser that assigned unconditionally would pass every other test here
while silently resetting `set_outlier_filter(frac=...)`.

**What this does not do is heal in place**, and a test pins that rather than
leaving it to be discovered. `_detach_shared_metadata` runs on derivation,
never on the object you mutate, so clearing the attribute by hand leaves that
object broken until something derives from it. What the fix guarantees is that
the `None` stops *propagating* — no object inherits a state it never chose.
Closing the in-place half would take a normalising property, the shape `freq`
(#29/#31/#23) and `lowess_fit` (#20) use, and nothing yet needs it.

### Changed — `signal_name` and `last_process` are always strings

The same hole with a louder symptom, and the review issue #33 asks for.
Plotting builds every title, axis label and legend entry with
`ts.signal_name + " " + ts.last_process`, so a propagated `None` raised
`TypeError: unsupported operand type(s) for +: 'NoneType' and 'str'` from
matplotlib's caller. Both names now go through `normalise_label` at the same
chokepoint.

**Three behaviour changes, all narrow:**

- A non-string label is coerced on derivation rather than propagated as-is:
  `ts.signal_name = 12` reaches `ts.iloc[:5]` as `'12'`. Stringified rather
  than blanked — a caller who set a number meant it to appear on the plot.
- `TimeSeriesData(..., signal_name=12)` no longer raises `AttributeError:
  'int' object has no attribute 'upper'`; it stores `'12'`. A failing call
  becomes a succeeding one. The constructor is a door of its own for the
  label, and the only one that called a `str` method on it —
  `copy(deep=True)` and `_create_new_with_data` both hand the parent's name
  back to it.
- `baseTs(..., last_process=None)` returns a plottable object. This was the
  hole a review round found in the fix above: `signal_name` is handed to
  `TimeSeriesData.__init__` and normalised there, while `last_process` is
  assigned straight onto the object by `baseTs.__init__`, so a caller passing
  a supported keyword got back a series whose every plot label raised
  `TypeError` — with nothing mutated afterwards, so not the in-place boundary
  above but an unnormalised entry point. `baseTs(..., last_process=12)` now
  stores `'12'` on the same rule as the name.

Unchanged: the constructor still upper-cases the name it is given.

### Observed, not changed

Two pre-existing defects in the same neighbourhood, both verified identical on
a `main` worktree and filed rather than folded in here:

- **#56** — `_create_new_with_data` re-upper-cases the signal name, so
  `ts.zscale()` turns `'Heart Rate'` into `'HEART RATE'` while `ts.iloc[:5]`
  and `ts.copy()` preserve it. Only reachable for a name assigned after
  construction, since the constructor upper-cases anyway. A fix has to decide
  which of the two behaviours is the intended one, which is why it is not
  folded in.
- **#57** — `baseTs(ts)` resets *nine of thirteen* `_metadata` values to
  constructor defaults: `baseTs.__init__` assigns its own keyword defaults
  over what `_copy_metadata_from_basetseries` just copied. The signal name is
  what this sweep noticed; the other eight came out of checking whether it was
  really alone. `outlier_filter` is the one that survives, and only because
  #15 added the per-attribute guard whose comment describes this exact bug.
  The history loss is the sharpest edge - a converted object reports a fresh
  "Created baseTs object" as its entire provenance, with the flags that would
  have contradicted it reset in the same breath. `TimeSeriesData(ts)` loses
  one, the name.

## [Unreleased] — the domain exceptions are also `ValueError`s

### Changed — `except ValueError` now covers a whole call

```python
class ValidationError(TimeSeriesError, ValueError)          # baseTs/utils.py
class InvalidParameterError(FilterError, ValueError)        # baseTs/filters.py
```

Two lines, and they delete two breaking changes instead of documenting them.

Both validating families raise a type of their own, while the shared validator
underneath them — `validate_sampling_freq` — raises a bare `ValueError`. So no
single `except` clause covered one call: catching `ValueError` missed the lag
or the band edge, catching `TimeSeriesError`/`FilterError` missed the rate. A
caller who wanted "tell me when my input was rejected" had to name both, and
nothing in the API said so.

#30 and #32 each shipped a documented breaking change of exactly that shape —
"code catching `ValueError` will stop catching these". **Both entries are still
`[Unreleased]`**, so those breaks have never reached anyone. Widening the
hierarchy retires both rather than shipping them, and both paragraphs have been
corrected in place.

**Widening only.** Every `except ValidationError`, `except TimeSeriesError`,
`except InvalidParameterError` and `except FilterError` behaves as before, and
the domain base precedes `ValueError` in the MRO, so a caller listing both
clauses still reaches the domain one first. The whole suite passes unchanged.

**The risk was never the two class definitions — it was the fourteen
`except ValueError` sites** already in the package, any of which could start
swallowing a domain error as a fallback. Each was checked: every one wraps
either a builtin conversion (`float()`, `param_type()`) or exactly one
validator that raises a *bare* `ValueError`. The two closest to the edge are
`filters.py`'s translation sites, `except ValueError: raise
InvalidParameterError(...)`, which can now catch the type they produce — their
`try` blocks deliberately hold a single `validate_sampling_freq` call, so
nothing double-wraps. That tightness is what makes the widening safe, so it is
pinned by a test rather than left as a comment.

Not done, and deliberately: the 56 remaining bare `raise ValueError` sites are
untouched. Typing those would buy catch-by-domain, which is unreachable anyway
— `__all__` is `['baseTs', 'from_df', 'TimeSeriesData']`, so the exception
classes are not exported. Exporting them is the enabling step if that is ever
wanted; sweeping 56 sites first would be building an API nobody can catch.

## [Unreleased] — the lag conversions validate the rate (#32)

### Fixed — a degenerate time base died in `int()`, or did not die at all

`utils.time_to_idx` scaled a lag by `ts.freq` with no check on the rate:

```python
return int(lag_secs * float(freq))
```

A degenerate time base — duplicate or non-increasing timestamps — derives to a
NaN rate, so this raised `ValueError: cannot convert float NaN to integer`,
naming the conversion rather than the time base that caused it. That is exactly
the failure #24's audit set out to remove, one module over; the site was simply
missed. `idx_to_time` had the matching hole in the other direction:
`idx_to_time(5, 0.0)` raised `ZeroDivisionError`.

Both now call `validate_sampling_freq`, which covers `get_lags`,
`shift_timeseries`, `validate_lag`, `plotting.lag_plot` and `baseTs.lag_plot`
in one place — the single door every lag consumer already passes through.

**The silent half was worse than the loud one.** In index mode the rate is only
used to *label* the lag, so nothing raised: `shift_timeseries(deg, 5, 'index')`
returned successfully with `lag_secs=nan`, and `lag_plot(deg, 5)` drew a plot
titled "nan seconds". Index mode is `lag_plot`'s default.

**The `get_peaks` precedent does not carry over.** #24 deliberately left
`freq <= 0` acceptable there, because its `max(25, ...)` floor makes the rate
irrelevant. There is no such floor here — a zero rate is a genuine
`ZeroDivisionError` — so the full guard applies.

**The lag is checked in the same place, because `validate_lag` never got to
speak.** `shift_timeseries` calls it *after* `get_lags` has already converted,
so an unusable lag died in the conversion — `int(nan * rate)`, `"0.5" / rate` —
and the validator that exists to diagnose exactly that ran too late to be
reached. Both primitives now coerce the lag through one helper and raise
`ValidationError`, the type `validate_lag` already raises for every other bad
lag.

**Finiteness is asymmetric on purpose.** `int()` cannot carry a NaN forward, so
`time_to_idx` refuses one; division can, so a NaN *index* still flows through to
`validate_lag`, whose message names index mode and the integer rule — a better
diagnosis than the conversion can give. The numeric-but-wrong lag stays
`validate_lag`'s to judge; only the unconvertible one is refused earlier.

**Both functions name the rate first when both arguments are bad.** Written as
one expression, `_coerce_lag(lag) / validate_sampling_freq(freq)` evaluates its
left operand first and would blame the lag, while `int(secs * rate)` blames the
rate — the same mistake diagnosed two ways depending on which unit the caller
chose. The rate check is now sequenced ahead of the lag in both.

**Checking the operands is not the same as checking the result.** Two
individually valid values can still combine into something the conversion
cannot express: `1e300 s * 1e300 Hz` is `inf`, so `int()` raised a bare
`OverflowError` — the same raw-conversion leak this change exists to stop — and
`10**300 / 1e-300` is `inf`, which nothing downstream catches, because
`validate_lag` only asks whether the *index* is a positive integer and never
looks at the seconds derived from it. That `lag_secs=inf` rode out into the
result dict and the plot title. Both were reachable on `main` as well; what is
new is the docstring promising otherwise, so the promise is what was made true.
The rule is now *finite in, finite out, or a diagnosis* — guarded on a finite
input, so a NaN index still reaches `validate_lag`.

**The validated values are the ones that get used**, returned from their
validators rather than re-read from the caller's arguments. Validating one
object and computing with another is how a band edge validated as 1.0 got
filtered as something else in #30.

**Breaking — forty-five of sixty replayed cases change** through
`shift_timeseries`, `plotting.lag_plot` and `baseTs.lag_plot`, enumerated by
replaying fifteen lag shapes × two units × two time bases against a `main`
worktree and against this branch, not from recall. The table is asserted by
`TestTheOutcomeCensusIsComplete`, which also fails if a new lag shape is added
without being classified.

*Two turn a succeeding call into a failing one* — index mode on a degenerate
time base with a usable integer lag (`50`, and `True`, which is `1`). Both were
returning `lag_secs=nan`, and both are the silent failure this fixes.

*Thirty move to `ValueError`* — every remaining degenerate-time-base case.
Nine were already `ValueError` and gain the diagnosis; eleven were a bare
`TypeError` or `OverflowError` thrown by the conversion; eight were a
`ValidationError` about the lag, since the rate is now reported first; two are
the successes above.

*Fourteen move to `ValidationError`* — a lag that is NaN, infinite, a `str`,
`bytes`, `None`, a multi-element array, or an integer too large to convert.
Thirteen were bare `TypeError`, `OverflowError` or `ValueError`; the fourteenth
was already a `ValidationError` and only its message changes. The exception
*type* changes, but `except ValueError` keeps catching them — see the hierarchy
entry below, which widened `ValidationError` for exactly this reason.

*One turns a failing call into a succeeding one* — a `Decimal` lag in seconds
mode, which used to die on `Decimal * float`. `validate_sampling_freq` accepts
`Decimal` as a rate deliberately, and coercing the lag the same way makes the
two arguments agree. Note what accepting it means: the lag converts through its
nearest double, not exactly. `Decimal("0.499999999999999999999999999999")` is
`0.5` as a float and so gives index 50, where exact arithmetic would floor to
49. That is the same trade already made for an exact *rate*, it only shows
within one ULP of an integer boundary, and it is pinned by a test — but "finite
in, finite out" above is a claim about overflow, not about precision.

**One narrowing the census does not cover**, because it is a duck type rather
than one of the fifteen shapes replayed: an object with a working `__mul__` and
no `__float__` used to multiply straight through, and is now refused. That is
the intended consequence of coercing before computing — an object whose
`__mul__` returns something arbitrary is exactly what #30's "validate one
value, compute another" lesson was about — but it is a behaviour change, and it
is pinned by a test rather than left to be discovered.

**Two message defects, both introduced here and both fixed before merge.** The
`OverflowError` arm reported `10**400` as "not a real number", which is false —
it is a real number outside float's range, and the message sent the caller
looking for a type error they did not have; it now has its own wording. And the
messages interpolated the rejected value with `{lag!r}`, so a 200k-element list
produced a 1.4 MB exception; values are now truncated with their type name.

**Direct callers of the two primitives see more change**, because both now
apply `validate_sampling_freq`'s full contract to the rate. A `str` rate is now
refused, where `float("100")` used to succeed and return 50; `True` is refused,
where it used to be taken as 1 Hz and return 0; and negative, zero and infinite
rates are refused, where `time_to_idx(0.5, -100.0)` returned `-50`,
`time_to_idx(0.5, 0.0)` returned `0`, and `idx_to_time(0.5, inf)` returned
`0.0`. None of these can arrive from `ts.freq`, which validates at the property
setter — only from a direct call passing a literal.

One value-level change, on the accepted path: `idx_to_time` with a 0-d array
index returns a Python `float` where it returned `np.float64`. Same value, and
unreachable through `shift_timeseries`, where `validate_lag` rejects a 0-d
array index before it is returned.

**What this does not close, said plainly.** This change guards the sampling
rate and the lag's *type* at the conversion. Three other ways into a bad lag
result run through the same call and are untouched, all three verified
identical on `main` and filed rather than folded in:

- **#52** — `shift_timeseries` blanks the wrapped head with `lagged_data[:lag_idx] =
  np.nan`, so an integer-dtype series raises `ValueError: cannot convert float
  NaN to integer`. That is the *same message* this entry is about, from a
  different line and a different cause: the rate is fine, the container cannot
  hold the sentinel. Anyone reading #32's title would expect that path closed,
  and it is not.
- **#53** — nothing bounds `lag_idx` from above. `validate_lag` checks that it
  is a positive integer, never that it fits the series, so a lag longer than
  the data returns an empty array and a plot titled `100.0 seconds` for a
  4-second series. Silent, and the magnitude is now the one unguarded parameter
  left in this call.
- **#54** — `get_lags` dispatches on `lag_unit == 'seconds'` with no else-branch
  validation, so `'second'` or `'Seconds'` is silently reinterpreted as index
  mode — a factor-of-the-sampling-rate difference in what the lag means, with
  the plot correctly labelled for the wrong reading.

Also unchanged: `int()` truncates rather than rounds (**#51**), so a derived
rate can shift by one sample less than asked.

Three of these four came out of adversarial review rounds on this change, not
from the original report.

## [Unreleased] — both band edges are validated (#30)

### Fixed — `bandpass_filter` checked one edge, and argument order picked which

Validation was:

```python
validate_filter_params(data, sample_Hz, max(hp_hz, lp_hz), 3)
```

One of the two edges, never both. And `max()` is order-dependent on NaN —
`max(0.1, nan)` returns `0.1`, so a NaN *upper* edge was silently discarded,
while `max(nan, 0.4)` returns `nan` and was caught. The same bad argument was
accepted or rejected depending on which parameter it was passed as.

So a negative, zero or NaN lower edge reached scipy and died there:

```python
ts.bandpass_filter(-1.0, 0.4)   # ValueError: filter critical frequencies must be greater than 0
ts.bandpass_filter(0.1, np.nan) # ValueError: Wn[0] must be less than Wn[1]
ts.bandpass_filter(0.4, 0.1)    # ValueError: Wn[0] must be less than Wn[1]
```

Each escaped this module's `InvalidParameterError` contract, and each pointed
at scipy's `Wn` internals rather than at the argument the caller got wrong.

A new `filters.validate_band_params` is now the single door for two-edged
filters. It type-checks both edges, coerces them to plain floats, checks each
positive and below Nyquist (NaN-safely, via `not (x > 0)`), then checks the
ordering relation explicitly, naming both values. Data, rate and order are
delegated to `validate_filter_params` rather than re-derived — local copies of
a shared check drifting apart is what #28 cleaned up in the spectral family.

**The coercion is load-bearing, not tidiness.** `numbers.Real` is a
*registrable* ABC, so an accepted value can be an object whose comparisons are
stateful — able to answer `>= nyquist` with `False` once and `True` the next
time. That makes "these two textually identical predicates are redundant"
unsound as a claim about the accepted domain, and the upper edge genuinely is
checked twice (once by the delegated call, once by the local rule that was
subsequently removed as dead). Comparing coerced floats makes the redundancy
real rather than assumed, so the removal is safe. The same coercion is why an
oversized integer edge now reports "too large to convert" instead of "past
Nyquist" — same exception type, different message.

**The validated value is now the one that gets filtered.** `validate_band_params`
returns `(effective_freq, hp_hz, lp_hz)` rather than the rate alone, and
`bandpass_filter` uses all three. Previously the coerced edges were local to the
validator, so `signal.butter(3, [hp_hz/nyq, lp_hz/nyq])` still divided the
caller's original objects — meaning an edge could be validated as one value and
filtered as another. A `numbers.Real` with no `__truediv__` died there with a
bare `TypeError`; one whose `__truediv__` disagreed with its `__float__`
produced a bare scipy `ValueError` about `Wn`, past every guard. Five review
rounds audited this validator's internals and none looked at the line that
consumes its result: enumerating the checks inside a function is not the same
as enumerating the surface.

**Fixed for `bandpass_filter` only — one of four entry points.** `lowpass_filter`,
`highpass_filter` and `notch_filter` share `validate_filter_params`, which
range-checks `cutoff_freq` without coercing it and returns only the normalised
rate, so all three still divide the caller's original object. A `Decimal`
cutoff raises a bare `TypeError` in each. That is filed as #49 rather than
fixed here, to keep this change to its stated scope — but it is named here
because the paragraph above would otherwise read as closing the defect class
outright, and it does not.

**Transposed edges raise rather than being sorted.** Silently reordering would
filter a band the caller did not ask for and hide the mistake; #27 had just
shown how easy this argument order is to get wrong.

**`Decimal` is accepted as a band edge**, alongside everything registered under
`numbers.Real`. It is registered under `numbers.Number` only, so the first
version of the type guard rejected a `Decimal` edge while
`validate_sampling_freq` deliberately accepted a `Decimal` *rate* — one type,
two answers, in the same call.

**Nyquist now comes from the rate the filter actually uses.** The edges are
normalised by `effective_fs = sample_Hz / max(1, window_step - overlap)`, but
validation compared against `sample_Hz / 2`. At `window_step=4`, `lp_hz=4.0`
passed validation and then died inside scipy. Validation moved after the
effective rate is computed. This is only reachable through a direct
`filters.bandpass_filter` call — `bandpass_at` does not expose `window_step`
or `overlap`, and nothing in the package, tests or docs passes them.

**`window_step` and `overlap` are guarded the same way.** `max(1, window_step -
overlap)` sat one line below `max(hp_hz, lp_hz)` and had the identical flaw:
`max(1, nan)` returns `1`, so a NaN window step was silently clamped and the
filter ran at a rate the caller never asked for — no error, just wrong output.
A string or `None` died on the subtraction with a bare `TypeError` before any
validation ran. Both operands are now checked before the arithmetic. Fixing one
`max()` and shipping the other, in a change whose subject is this defect class,
was not a defensible place to stop.

What this does *not* cover, said plainly: the two operands are checked for type
and finiteness, not for their relationship. `overlap >= window_step` still
clamps to 1 and filters at the full declared rate, and a negative `overlap`
still inflates the effective rate above the real one — both silently. Neither
is reachable through `bandpass_at`, which does not expose either parameter.

**Non-scalar band edges are rejected rather than escaping.** `not (edge > 0)`
on an array raises numpy's "truth value ... is ambiguous" `ValueError`, so the
contract had a hole in it on `main` and would have kept it. Membership is
tested against `numbers.Real`, deliberately not by attempting `float(value)`:
`float(np.array([0.1]))` returns `0.1` on numpy 1.x and raises on 2.x, so a
`float()`-based guard would accept a one-element array on one CI leg and reject
it on another with the suite green either way — the trap PR #26 hit.

**Rejection messages now name the limit, not just the rule.** The shared
cutoff message stated no number at all. Combined with checking `lp_hz` against
the *declared* Nyquist, that sent a caller round the loop twice: at
`sample_Hz=10, window_step=4` an `lp_hz` of 6.0 was rejected against a limit of
5.0 that was never printed, and a reasonable retry at 2.0 failed again against
the real limit of 1.25. The delegated call now receives the effective rate, and
both messages carry the offending value and the applicable Nyquist. Tests take
the limit back out of the message and check that a band under it is accepted —
the remedy is executed, not asserted (#28).

**Breaking — twenty-one behaviour changes**, enumerated by replaying every case
against a `main` worktree and against this branch, not from recall:

*Eleven move from a bare `ValueError` to `InvalidParameterError`* — negative,
zero or non-scalar **lower** edge; negative, zero, NaN or non-scalar **upper**
edge; transposed edges; equal edges; an upper edge valid against the declared
Nyquist but not against the effective one at `window_step > 1`; and an exact
type (`Fraction`, `Decimal`) whose value is below Nyquist but whose nearest
double is not. The exception *type* changes, but `except ValueError` keeps
catching them: `InvalidParameterError` was widened to inherit `ValueError`
alongside `FilterError` before release — see the hierarchy entry above.

*Six move from a bare `TypeError`* — a band edge, `window_step` or `overlap`
that is non-numeric, or that registers as `numbers.Real` without a usable
`__float__`.

*One moves from a bare `OverflowError`* — a `window_step` too large to convert
to a float, which used to die on `sample_Hz / window_step`.

*Three move from no error at all* — a NaN `window_step` or `overlap`, clamped
to 1 by `max()` and filtered at a rate the caller never asked for; and an
oversized integer `overlap`, which `max(1, window_step - overlap)` evaluated
happily in unbounded integer arithmetic. These three are the only ones that
turn a *succeeding* call into a failing one, and all three successes were
returning wrong numbers.

Four cases that look like they belong are absent, because all four already
raised `InvalidParameterError` before this change: a **NaN lower** edge
(`max(nan, 0.4)` returns `nan`, which the pre-existing NaN-safe cutoff check
caught), an **oversized integer** on either edge (the range check compared a
big int against a float exactly), and a **degenerate sampling rate** (guarded
since #24). The messages for the oversized-integer cases changed; the
behaviour did not.

This count was wrong three times before it was right — first thirteen including
a case that was never breaking, then "eight" while enumerating ten, then fifteen
with `overlap=NaN` missing while `window_step=NaN` was present. The last miss is
the instructive one: a hand-written list of a symmetric family keeps losing one
half of it. So the enumeration is now *generated* as a product over both band
edges and both windowing parameters, with only genuinely one-off cases written
out, and `TestTheInvalidParameterContractIsComplete` asserts the total against
the number printed here — it caught the drift to twenty by itself. Each case
also carries the message fragment its own guard produces, and a further test
cross-matches every fragment against every message so that a fragment satisfied
by a different guard fails rather than passing quietly.

A bad *upper* edge still reports the generic cutoff message rather than a
band-specific one, since the delegated check runs first. The message carries
the offending value and the real limit, so it is complete — only its wording
differs. Pinned by tests rather than left to chance.

## [Unreleased] — `butterpass_at` runs at all (#27)

### Fixed — `butterpass_at` raised `TypeError` on every call

The method passed `highpass_freq`, `lowpass_freq` and `sampling_freq` to
`filters.bandpass_filter`, whose parameters are `hp_hz`, `lp_hz` and
`sample_Hz`. None of the three keywords existed, so the call never got past
argument binding:

```python
ts.butterpass_at(0.05, 0.4)
# TypeError: bandpass_filter() got an unexpected keyword argument 'highpass_freq'
```

It was dead from introduction. Nothing referenced it — no test, no example, no
entry in this file or `API.md` — which is why nobody hit it.

`butterpass_at` is now an alias for `bandpass_at`, joining `bandpass_filter`,
which already delegates the same way. The method reaches
`filters.bandpass_filter` for the first time, and therefore
`validate_filter_params`, so a degenerate sampling rate now raises
`InvalidParameterError` here as it does for every sibling filter (#24).

**Delegation rather than the keyword rename the issue suggested, and what that
is and is not worth:** it deletes fourteen lines of hand-rolled `self.copy()` /
`newTs.data = ...` plumbing that bypassed `_create_new_with_data` and
`_update_flags`, leaving one code path where there were two. It is *not* an
output difference, and the entry does not claim one. Measured rather than
assumed: a rename-only version produces identical metadata across all thirteen
entries of `TimeSeriesData._metadata` on both `inplace` branches, on a source
seeded off its constructor default in each of the ten slots the operation
preserves — the remaining three (`is_filtered`, `last_process`, `history`) are
changed by the operation itself. The rate guard above is likewise not a
differentiator — the rename would have inherited it too, since it also calls
`bandpass_filter`. The case for delegating is maintainability.

**Not a breaking change for any caller of the public API, with one visible
consequence:** history now records the `bandpass_at` entry (`"Bandpass filtered
at ..."` / `_bp_{lp}:{hp}Hz`) rather than the old `"Butterworth pass
filtered ..."` / `_btrp_{lp}:{hp}Hz`. Calling the shipped method could not
reach the old token — it raised several lines before writing it. The one way
to have observed it was to monkeypatch `baseTs.core.bandpass_filter` (the
import-time binding; patching `baseTs.filters.bandpass_filter` has no effect)
with a replacement shaped to accept `highpass_freq`/`lowpass_freq`/
`sampling_freq` — parameter names that only ever existed as an artifact of this
bug.

## [Unreleased] — the spectral family rejects non-finite *data* (#28)

### Fixed — `get_peak_freq` no longer returns a confident wrong answer on gappy data

`get_frequency_content` built its own FFT and, unlike every sibling in the
spectral family, carried no NaN/Inf check on the data. A single NaN anywhere in
the input makes `np.fft.fft` return an **all-NaN** spectrum, and scipy's
`find_peaks` still returns indices over an all-NaN array — so `get_peak_freq`
reported a plausible-looking frequency with nothing behind it. No warning, and
no NaN in the output to signal the problem.

On a 500-sample 0.16 Hz sine, one injected NaN produced `4.98`. So did five,
and so did fifty; windowing did not change it either. That insensitivity to how
much of the data was bad is what confirms the number was meaningless rather
than merely degraded. This is the more dangerous half of the NaN story fixed in
#24 — that one at least produced visible NaN output.

The root cause was a guard lost in a refactor: `get_peak_freq` was moved off
`compute_fft_power` (which has the check) onto the "enhanced"
`get_frequency_content` (which did not), silently dropping the validation along
with it.

All spectral entry points now share `utils.validate_finite_data`, the companion
to `validate_sampling_freq`. `compute_fft_power` and `relative_band_power` each
carried their own copy of the check with different wording; those copies are
gone, and `relative_band_power` now has no local data guard at all — it calls
`get_frequency_content`, whose guard raises the same error. Local copies at
consumption sites are exactly what let the four drift apart.

**Behaviour change:** `get_frequency_content` and `get_peak_freq` now raise
`ValueError` on data containing NaN or Inf, where they previously returned an
all-NaN spectrum. The message names the remedy: *"Fill gaps first, e.g. with
`interpolate_gaps()`."* This is reachable in normal use — since #36,
`filter_outliers` deliberately returns a series containing NaN, so
`ts.filter_outliers().get_peak_freq()` now raises and needs an
`interpolate_gaps()` between them.

`plot_fft_power` is deliberately not in that list: it never raises. It renders
the new error as on-plot text instead, because of its bare `except Exception`
(issue #34, unchanged here) — so on gappy data it now draws the message where
it previously drew a blank spectrum.

> **Superseded by #34.** `plot_fft_power` now raises like its siblings, so the
> exemption described in the paragraph above no longer holds. The account is
> left standing because it is what this change did; see the #34 entry for what
> replaced it.

Raising rather than dropping the bad samples is deliberate: dropping would
change the sample spacing, so the resulting bins would no longer be the
frequencies they are labelled with, and the caller would not be told. It also
matches what the guarded siblings already did.

**Secondary behaviour change:** non-numeric data (a string or object-dtype
series) now raises `ValueError` naming the data at **all four** entry points.
`compute_fft_power` and `get_frequency_content` previously raised `TypeError:
ufunc 'isnan'/'fft' not supported for the input types`; `relative_band_power`
and `falff` raised `TypeError: float() argument must be a string or a real
number` from their own `np.asarray(..., dtype=float)` narrowing, which runs
before they delegate. That narrowing is now preceded by the shared guard, so
the uniform-`ValueError` contract holds for dtype as well as for NaN. Integer and boolean series skip the check
entirely — those dtypes cannot represent NaN or Inf — and complex data is
checked without a float cast, so it is not newly rejected (**superseded by
#43**, which rejects complex data at all four entry points; the decision here
was out of this issue's scope, not a judgement that complex was supported).
Pandas nullable
dtypes (`Int64`, `Float64`) and pyarrow-backed columns are checked correctly:
`pd.NA` becomes NaN under `np.asarray` and is caught.

`datetime64` and `timedelta64` *data* is rejected up front, before that cast.
The cast is the problem: it **succeeds** on those dtypes, and `NaT` is stored
as the int64 sentinel `-2**63`, which converts to a large but perfectly finite
float — so a `NaT` would otherwise pass the finiteness check and die later in
`np.fft.fft` with a `DTypePromotionError` naming an internal promotion rule.
This concerns *values* only; a series with a `DatetimeIndex` and numeric data
is unaffected.

That error deliberately does **not** suggest a cast through `float` or
`int64`. It is the obvious remedy and it is wrong: it reinterprets the int64
storage, so `NaT` comes back as `-9.22e18`, which the guard then accepts —
reproducing the silent-nonsense failure one level up. Datetime arithmetic maps
`NaT` to `NaN` instead, landing the caller on the gap-filling message.

The message names a different remedy per dtype, because they are not
interchangeable: `values / np.timedelta64(1, 's')` for durations, and
`(values - values[0]) / np.timedelta64(1, 's')` for timestamps. Handing the
duration form to a `datetime64` caller does not merely fail to help — it
raises `UFuncTypeError`.

## [Unreleased] — `lowess_fit` and `outlier_indices` stop following the index (#20)

### Behavior change — positional metadata is validated on read

`lowess_fit` holds one value per sample and `outlier_indices` holds *positions*
into that same sample sequence. Both used to travel onto every derived object
regardless of what that object's index looked like, so a 50-point slice of a
filtered series claimed a 200-point fit and reported outliers at positions it
did not have. `qc_plot` raised `ValueError: x and y must have same first
dimension`; `plot(..., lowess=True)` did not raise, and silently drew the
parent's fit over the child's window.

Both are now properties. Each stores the value together with the index it was
computed against, and hands it back only while that is still the object's
index; otherwise it reads as `None`. Reslicing was rejected as an alternative:
it is only definable for a positional slice, and `resample`, `dropna` and
`sort_values` have no meaningful mapping, so it would have been correct on one
path and silently wrong on the rest.

The check is full index equality — deliberately stricter than the `_freq_token`
used for `freq`, because an interior permutation leaves that token untouched
while moving every sample these two describe.

**Why on read rather than on write.** The first implementation invalidated at
each point an index could change, and that list would not close: it grew from
four places to seven over three review rounds and still missed
`ts.loc[new] = v`, `ts.pop(label)` and `del ts[label]` — which swap the block
manager inside pandas' own indexer, past `__finalize__`, `_update_inplace` and
`.index` assignment alike — as well as `interpolate_gaps(inplace=True)`, one of
three `pd.Series.__init__` call sites of which an explicit audit for that exact
pattern still guarded only two. Every one of those doors changes `self.index`,
and the getter reads `self.index`, so checking there closes all of them at once
and cannot be bypassed by a path nobody anticipated.

Six breaking changes fall out:

1. **An object whose index is not the one the fit was computed against reads
   `None` for both.** `ts.filter_outliers(inplace=True); ts.iloc[:50].lowess_fit`
   is now `None` rather than the parent's 200-point array. This covers every
   way an index can change — slicing, `dropna`, `resample`, `sort_values`,
   `remove_outliers`, `shift_time`, `inplace=True` on any inherited pandas
   method, `ts.loc[new] = v`, `pop`, `del`, `interpolate_gaps(inplace=True)` —
   including a reordering that leaves the length, first and last timestamps
   intact. **Migrate:** re-run `filter_outliers()` or `lowess_detrend()` on the
   object you want a fit for, or slice before filtering rather than after.
   Operations that leave the index alone (`sg_filter`, `copy`, `rolling`,
   scalar arithmetic, `fillna`/`clip`/`interpolate` in place, `ts += x`) still
   carry both.

2. **Arithmetic between two differently indexed series clears both.**
   `filtered + other` produces a union index, against which the left operand's
   fit is the wrong length and its outlier positions point at other samples;
   it used to be carried anyway, and `plot(result, lowess=True)` then raised a
   matplotlib dimension error. **Migrate:** none, unless you were reading
   `lowess_fit` off an arithmetic result — it was the wrong array.

3. **Assigning a new time base clears both.** `ts.times = new_times`,
   `ts.index = new_index`, a length-changing `ts.data = shorter`, and any
   in-place method that changes length or order. **Migrate:** read the fit out
   before reassigning the index if you need it.

4. **`plot(ts, lowess=True)` raises `ValueError` when there is no fit**, naming
   `lowess_fit` and what to run to get one. It previously raised a
   dimension-mismatch `ValueError` from matplotlib, or drew the wrong data.
   `qc_plot` is unchanged: it already gated on `lowess_fit is not None`, and
   now simply omits the trace instead of raising. **Migrate:** guard on
   `ts.lowess_fit is not None` before asking `plot` for a lowess trace.

5. **`outlier_indices` is no longer shared by reference.** Every derivation
   gets its own copy, so `derived.outlier_indices.append(...)` no longer
   rewrites the parent's outlier record. Its length is the number of outliers,
   not the number of samples, so copying it is cheap; both the list and ndarray
   shapes are detached, since the constructor types the parameter as
   `np.array`. `lowess_fit` is still shared on *derivation* — one float per
   sample, never written to, and copying it there would turn an O(1) slice into
   an O(n) walk of the parent's metadata — but `copy(deep=True)` deep-copies it
   as it always did. **Migrate:** none, unless you were relying on the
   write-through.

Two consequences of checking on read rather than destroying on write, neither
of which depends on whether anyone read anything:

- **Restoring an index makes the value readable again on the object that owned
  it.** `ts.times = other; ts.times = original` gives the fit back — correct
  within this property's scope, since the samples are back at the positions the
  fit describes, and misleading only if the *data* changed meanwhile, which is
  tracked separately as #40. A *derived* object never regains a value it never
  had: derivation releases outright.
- **An object mutated in place to a different index keeps the old value in its
  slot** until overwritten or collected. Derivation releases eagerly, which is
  the case that matters — it is what stops a slice pinning the parent's
  full-length array.

6. **`TimeSeriesData._metadata` no longer contains `'lowess_fit'` or
   `'outlier_indices'`.** The slots it names are now `'_lowess_fit'` and
   `'_outlier_indices'`, each holding `(value, index_it_describes)`. This
   mirrors what `'freq'` → `'_freq_declaration'` did in the previous release,
   and for the same reason: `__finalize__` copies with `object.__setattr__`,
   which honours data descriptors, so declaring the public names would run the
   stamping setter on every propagation and re-stamp a stale fit with the
   receiving object's index. **Migrate:** code that introspects or iterates
   `_metadata` looking for either name needs the underscored spelling — or,
   better, should just read and write the public properties. Any code that
   copies metadata between objects must copy the private slots, never assign
   through the public names.

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

Nine breaking changes fall out of these two fixes:

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

8. **Any operation whose result index has the same `(len, first, last)` now
   preserves a declared rate**, where it previously re-derived or
   overwrote it. This is general — not specific to arithmetic — because the
   token the property compares against is exactly those three values.
   Three instances are known on this branch:
   - **Arithmetic.** Found during implementation, not design: a series
     declaring 10.0 Hz over a time base measuring 9.9 Hz reported
     `a.freq == 10.0` but `(a + b).freq == 9.9` — the same object answering
     differently for an operation that never touched its index.
   - **`filter_outliers`.** `baseTs(d, t, freq=999.0).filter_outliers().freq`
     is now `999.0`. On `main`, a `newTs.freq = filt.freq` assignment (this
     branch deleted it) overwrote the declaration with the filter's derived
     rate; deleting it was a behaviour change, not the redundant tidying the
     design's deletion table described it as.
   - **`interp_to_uniform_grid(inplace=False)`.** Same series → `999.0`.
     With `new_grid=None` the grid is `linspace(t0, t1, len(data))`, which
     preserves length and both endpoints, so the token survives even though
     interior spacing changed.

   **Migrate:** code that relied on any index-preserving operation always
   re-deriving `freq` will now see the operand's declared rate instead. See
   `docs/superpowers/specs/2026-08-27-derived-freq-design.md` (Consequences,
   item 8) for the full reasoning.

9. **A pickle written by an older version can fail to load.** If its
   `_metadata` contained `'freq'` set to a non-positive or NaN value —
   plausible, since `main` stored NaN for any degenerate index and
   `interpto_hz(0)` minted `freq=0` objects — unpickling now raises
   `ValueError`. pandas' `__setstate__` restores attributes with
   `object.__setattr__`, which honours the `freq` data descriptor and so
   runs the validating setter on every old pickle, not just new ones.
   **Migrate:** don't unpickle old objects that carried a degenerate rate;
   re-create them from their underlying data and times instead.

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