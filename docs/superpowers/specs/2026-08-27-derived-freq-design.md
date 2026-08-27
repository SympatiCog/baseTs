# Derived `freq`: closing #29, #31 and #23

Date: 2026-08-27
Issues: #29, #31, #23
Status: approved, awaiting implementation plan

## Problem

`freq` is a stored attribute. Three code paths write it and they disagree.

`_create_new_with_data` re-derives it when the index changes (#19's fix).
`__finalize__` copies it verbatim. `TimeSeriesData.__init__` stores whatever
the caller passed. So the same index change produces two different rates
depending on which path built the object:

```python
ts = baseTs(np.sin(np.arange(100) / 10.0), np.arange(100) / 10.0)  # 10 Hz

ts.trimto_timepoints(0, 5).freq   # 10.0  - re-derived, correct
ts.iloc[::2].freq                 # 10.0  - carried; the true rate is 5.0
ts.sort_values().freq             # 10.0  - carried; the true rate is NaN
```

Nothing validates a rate where it enters the object, so a bad one is accepted
at construction and reported some distance from the mistake:

```python
baseTs(data, times, freq=0.0)     # constructs silently; so does freq='30'
baseTs(np.ones(5), freq=0)        # times become [nan, inf, inf, inf, inf]
baseTs(np.ones(5), freq=-10)      # times run backwards
ts.interpto_hz(0)                 # len 0, freq 0, no error
```

And `interpto_hz` builds a grid whose real rate is short of the requested one
by `(N-1)/N`, hidden today because the requested rate is stored verbatim:

```python
ts.interpto_hz(5)     # 499 samples, stored freq 5, measured rate 4.984985
ts.interpto_hz(100)   # 9990 samples, stored freq 100, measured rate 99.989990
```

All three are the same defect wearing different clothes: `freq` is a value
that can drift from the index it describes, and every fix so far has guarded
where it is *read* rather than where it is *written*. PR #26 added guards to
five consumption sites across five review rounds, and #29 means the original
silent-nonsense output is still reachable through `iloc`.

## Approach

Stop storing the rate. Derive it from the index, and let an explicit rate be a
*declaration* that expires when the index it was made against changes.

This is the same move as #15, where freezing `FilterConfig` deleted the
copying machinery and its three latent bugs instead of patching it a fourth
time. It makes the bug class unreachable rather than guarding a sixth site.

Two approaches were rejected:

- **Patch `__finalize__` and the two constructors** (what #29 and #31
  suggest). Smallest change, but leaves `freq` a stored value that can drift,
  so the next path that writes it is the next bug.
- **Delete the consumption guards** once the setter is the only door. Smallest
  end state, but no defence in depth if a future path bypasses the setter.

## Design

### 1. The `freq` property

`freq` becomes a property on `TimeSeriesData`. One private attribute holds the
declaration:

```python
_freq_declaration = None        # or (value: float, token)
```

The token is the index fingerprint:

```python
token = (len(index), index[0], index[-1])   # (0,) when the index is empty
```

These are *exactly* the three inputs `_calculate_effective_frequency`
consumes. So "the token still matches" means "re-deriving right now would
return the number it returned when the declaration was made" — the declaration
is as valid as it was on the day it was made. Any index change that could move
the rate moves the token.

The getter rebuilds the token from the current index, compares it to the
stored one with `==`, returns the declared value on a match and re-derives
otherwise. It is O(1) and holds no cache, so there are no invalidation hooks
to get wrong.

Measured on a 200 000-sample series: `_calculate_effective_frequency` costs
1.0 µs and does not grow with length, against 30 µs for `iloc[:100]` and
118 µs for `ts * 2`. This answers the cost question #29 left open — the
objection to re-deriving on the hot path does not survive measurement.

### 2. Propagation

`_metadata` swaps `'freq'` for `'_freq_declaration'`.

`__finalize__` is **not** touched. It keeps copying metadata verbatim, and
that becomes correct: what it now copies is a declaration the child
re-validates against its own index. #29 closes without editing the method the
issue is named after.

Removing `'freq'` from `_metadata` also matters mechanically. pandas'
`__finalize__` copies with `object.__setattr__`, which honours data
descriptors — had `freq` stayed in the list, every propagation would have run
the validating setter.

### 3. Validation at production sites (#31)

The setter is the one door, and it runs `validate_sampling_freq`:

- `ts.freq = 0` / `inf` / `'30'` / `True` raises `ValueError`, naming the
  assignment as the mistake.
- `ts.freq = None` clears the declaration, returning the object to derived.
- `TimeSeriesData.__init__` routes `freq=` through the setter, so
  `baseTs(..., freq='30')` raises at the constructor rather than three calls
  later.
- `baseTs.__init__` validates `freq` **before** using it to build an index
  when `times` is omitted, closing the `[nan, inf, inf, ...]` and
  backwards-index cases above.

`_freq_declaration` is a plain attribute with no descriptor, so nothing that
copies metadata can install a value the setter never saw. The class is closed.

**One deliberate inconsistency.** `baseTs.__init__` uses `freq=np.nan` as its
public "not supplied" sentinel, so `baseTs(data, times, freq=np.nan)` must
keep meaning *unset* and must not raise, while `ts.freq = np.nan` does raise.
The gate at the `baseTs` layer stays `_is_unset`; the gate inside
`TimeSeriesData.__init__` is `freq is not None`; the setter always validates.
Changing the sentinel is a separate breaking change and is out of scope.

### 4. `interpto_hz` (#23)

The grid is rebuilt to have exact spacing:

```python
n = int(np.floor(duration * new_freq)) + 1
new_ts = t0 + np.arange(n) / new_freq
```

`new_freq` is validated first. A degenerate source — duration ≤ 0, a
non-monotonic or non-unique source index, or fewer than two resulting samples
— raises, replacing today's silent empty-result-stamped-5-Hz behaviour.

The result also **declares** `new_freq`. Not because the grid needs it: after
the fix the rate derives correctly. It is because the derived value
round-trips through floating point — `(n-1) / ((n-1)/f)` is not bit-exact `f`
— so `ts.interpto_hz(100).freq` could otherwise read `99.99999999999999`.
Declaring makes it exact, and after the grid fix the declaration is *true*
rather than the 0.2 % overstatement it is today. It still expires:
`ts.interpto_hz(5).iloc[::2].freq` reports 2.5.

**This changes `interpto_hz` output.** Sample count shifts by one
(`floor(d*f)+1` rather than `int(d*f)`), timestamps shift, and the last sample
may fall short of `times[-1]` instead of landing on it. That is the point: the
old grid did not have the rate it claimed.

### 5. Deletions

The design pays for itself in removed machinery:

| Location | Removed |
|---|---|
| `core.py:343-371` | `index_unchanged` computation, conditional `freq` kwarg, post-construction re-assert in `_create_new_with_data` — it now just carries `_freq_declaration` in its metadata copy |
| `core.py:290` | manual `self.freq = self._calculate_effective_frequency()` in the `times` setter |
| `core.py:1189,1199` | both `self.freq = filt.freq` lines in `remove_outliers` — redundant once the index drives the rate, and a live hazard once the setter validates, since `filt.freq` can be NaN |
| `series.py:401-406` | `to_basetseries` passing `freq=self.freq` as a constructor kwarg — which the validating setter would reject for a degenerate source — together with the `attr not in ['freq', 'signal_name']` special-case that exists to compensate for it. It carries `_freq_declaration` like any other metadata name instead |
| `series.py:583` | the matching `attr not in ['freq', 'signal_name']` special-case in the arithmetic path |
| `series.py:183-184` | the `else` branch of `TimeSeriesData.__init__` that derives a rate into storage. Nothing replaces it: an object with no declaration derives on read |

### 6. Edge cases

- **Degenerate index** still derives NaN rather than raising. The consumption
  guards are what turn that into an error, and they stay as defence in depth.
- **Token comparison is wrapped.** Any exception building or comparing a token
  (exotic index dtypes, object arrays) is treated as a mismatch, failing
  toward re-deriving.
- **NaN in the index** never equals its own token, so such an object always
  re-derives. Correct, and degenerate regardless.
- **Empty and single-sample indexes.** Token is `(0,)` when empty and
  `(1, idx[0], idx[0])` at length 1; derivation returns NaN below length 2, as
  it does today.
- **`test_type_preservation.py:82`** asserts every `_metadata` name exists on
  a constructed object, so it will enforce that `_freq_declaration` is
  initialised in `_initialize_default_metadata`.

## Testing

New coverage:

- Property contract: a declaration is honoured across an index-preserving
  operation (`zscale`), expires across `iloc[::2]`, `sort_values`, `resample`
  and `dropna`, and `freq = None` returns the object to derived.
- Both derivation paths now agree — `ts.iloc[::2].freq` and
  `ts.trimto_timepoints(...)` .freq give the same answer for the same index
  change. This is #29's acceptance test.
- Setter rejections at assignment and at both constructors, including the
  no-`times` path that builds the index from the rate.
- `interpto_hz` grid exactness across several rates, plus rejection of a
  degenerate source and of an invalid `new_freq`.

Existing tests to rewrite:

- `tests/unit/test_core.py:723` (`TestNanFreqIsNotLaundered`) reaches a NaN
  rate through `ts.freq = np.nan`, which the setter now refuses. It rewrites
  to construct a degenerate index, `baseTs(data, np.zeros(200))` — the only
  route by which a bad rate can still reach a consumption site.
- `tests/unit/test_utils.py:502` plants `np.float32(nan)` and `np.float32(inf)`
  on an object. NaN keeps an end-to-end test via the degenerate index; the
  values that are now unreachable on a constructed object move down to direct
  `get_peaks` and `validate_sampling_freq` calls, which is the level their
  contract actually lives at.

The split principle: keep an end-to-end test for what can still happen, and
test the rest at the function whose contract it is. No test should assert a
state the class can no longer enter.

## Consequences

Closes #29, #31 and #23.

Sets up #20. `lowess_fit` and `outlier_indices` have the same "did the index
change?" question, and the token answers it — invalidate to `None` on
mismatch, as agreed, rather than reslicing.

Breaking changes, for the changelog:

1. A declared rate expires when the index changes.
   `baseTs(..., freq=999).iloc[:50].freq` returns the derived rate, not 999.
2. Assigning an invalid rate raises. `ts.freq = 0`, `ts.freq = np.nan` and
   `ts.freq = '30'` were silent; they now raise `ValueError`.
3. `interpto_hz` returns a different grid — one more sample, exact spacing,
   and a final timestamp that may fall short of the source's last.
4. `interpto_hz` raises on a degenerate source instead of returning an empty
   series stamped with the requested rate.
5. `TimeSeriesData._metadata` no longer contains `'freq'`.
