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

`_freq_declaration` is a plain attribute with no descriptor, so no ordinary
metadata copy can install a value the setter never saw. To be precise about
the limit of that claim: a caller who writes `ts._freq_declaration = (...)`
directly, or who passes a duck-typed object with a `.freq` but no
`._freq_declaration` through `_copy_metadata_from_basetseries`
(`series.py:209-227`), still bypasses validation. That is the same protection
every other `_metadata` attribute on this class has always had, not a gap
specific to `freq` — but "closed" overstates it, and the docstring should say
"single supported door", not "closed".

**Reversing an earlier decision: `freq <= 0` at the constructor.**
`tests/unit/test_utils.py:457-473` asserts that `baseTs(sig, times, freq=0.0)`
constructs and that `get_peaks` still works on it. It passes today, and it
exists because an earlier revision applied `validate_sampling_freq` at that
consumption site and that was judged an unannounced API break. This design
reverses it deliberately. The test's own stated justification is that
`freq <= 0` objects must be tolerated *because* `interpto_hz(0)` mints them —
and Section 4 makes `interpto_hz(0)` raise, so nothing can mint one any more.
With the premise gone, tolerating the value at a production site buys nothing
and costs the chokepoint. The test is rewritten to assert what it actually
cares about — that `get_peaks` never consults the rate — by calling
`get_peaks` directly rather than by constructing an invalid object. Listed as
breaking change 6.

**One deliberate inconsistency.** `baseTs.__init__` uses `freq=np.nan` as its
public "not supplied" sentinel, so `baseTs(data, times, freq=np.nan)` must
keep meaning *unset* and must not raise, while `ts.freq = np.nan` does raise.
The gate at the `baseTs` layer stays `_is_unset`; the gate inside
`TimeSeriesData.__init__` is `freq is not None`; the setter always validates.
Changing the sentinel is a separate breaking change and is out of scope.

### 4. `interpto_hz` (#23)

The grid is rebuilt to have exact spacing:

```python
n = int(np.floor(np.round(duration * new_freq, 9))) + 1
new_ts = t0 + np.arange(n) / new_freq
```

**The rounding is not cosmetic.** A bare `floor(duration * new_freq)` silently
drops a trailing sample on a same-rate round trip, because the product lands
just below the integer:

```python
times = np.arange(1000) / 30.0
float(times[-1] - times[0]) * 30.0   # 998.9999999999999, not 999.0
```

so `interpto_hz(30)` on a 1000-sample 30 Hz series would return 999 samples.
That loss has nothing to do with the grid correction this section is making,
and it must not be shipped as though it did. Rounding to 9 decimal places
absorbs representation error while leaving a genuine fractional product
(998.9999 from real data) to floor as it should. The 30 Hz round trip goes in
the test suite as a regression case.

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

This table was rebuilt against the actual call sites after review; the first
draft was written from memory and was missing two required deletions, one
required *addition*, and mislabelled a method.

| Location | Removed |
|---|---|
| `core.py:343-371` | `index_unchanged` computation, conditional `freq` kwarg, post-construction re-assert in `_create_new_with_data` |
| `core.py:242-244` | the second derive-into-storage branch, `if _is_unset(freq): self.freq = self._calculate_effective_frequency()`, in `baseTs.__init__`. **This one is load-bearing**: left in place it routes a degenerate index's NaN through the validating setter, so `baseTs(data, np.zeros(200))` would raise at construction — contradicting Section 6 and breaking the very test rewrite this spec proposes |
| `core.py:290` | manual `self.freq = self._calculate_effective_frequency()` in the `times` setter |
| `core.py:1189,1199` | both `self.freq = filt.freq` lines in **`filter_outliers`** (not `remove_outliers`, which never touches `.freq` — it routes through `_create_new_with_data`) — redundant once the index drives the rate, and a live hazard once the setter validates, since `filt.freq` can be NaN |
| `core.py:2193-2196`, `core.py:2222` | `freq=self.freq` passed as a constructor kwarg by `copy(deep=True)` and by the shallow-copy `isinstance` fallback. Same fix as `to_basetseries`: carry `_freq_declaration` as metadata rather than round-tripping the rate through a constructor |
| `series.py:401-406` | `to_basetseries` passing `freq=self.freq` as a constructor kwarg — which the validating setter would reject for a degenerate source — together with the `attr not in ['freq', 'signal_name']` special-case that exists to compensate for it. It carries `_freq_declaration` like any other metadata name instead |
| `series.py:583` | the matching `attr not in ['freq', 'signal_name']` special-case in the arithmetic path |
| `series.py:183-184` | the `else` branch of `TimeSeriesData.__init__` that derives a rate into storage. Nothing replaces it: an object with no declaration derives on read |

One **addition** is required, and it is easy to miss because everything else
here is a deletion. `_create_new_with_data` does not iterate `self._metadata`
— it copies a hand-curated `metadata_attrs` list (`core.py:375-378`) that
deliberately excludes `'freq'`. `_freq_declaration` must be added to that
list. Without it, deleting `core.py:343-371` as the table says silently drops
every declaration across index-preserving operations:
`baseTs(..., freq=999.0).zscale().freq` would stop returning 999.0, breaking
this design's own acceptance criterion and the existing
`test_explicit_freq_still_honoured` (`test_core.py:735`). `to_basetseries` and
the arithmetic path iterate the full `_metadata` and need no such edit —
`_create_new_with_data` is the lone outlier.

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
- **A non-numeric index derives NaN rather than raising.**
  `_calculate_effective_frequency` does `float(index[-1] - index[0])`, which
  raises `TypeError: ... not 'Timedelta'` on a `DatetimeIndex`. Today that
  fires at the constructor, because construction derives eagerly. This design
  deletes the eager derivation, so without a guard the object would build
  cleanly and raise later from `.freq`, `info()`, `__repr__` or any spectral
  method — which is #31's own complaint ("the error lands three calls away
  from the mistake") reintroduced by the fix for it. The derivation therefore
  catches `TypeError` and returns NaN, and the existing consumption guards
  produce the error at the point of use. Side effect, listed as breaking
  change 7: `baseTs` becomes constructible from a `DatetimeIndex`.

## Implementation order

Both external reviewers on the adversarial panel dissented from this design
in favour of two targeted patches, on blast-radius grounds. Neither dissent
identified a flaw in the token argument; both argued from size of change.
The architecture stands, but the objection is answered by shipping it in
three independently revertable commits rather than one:

1. **The property and validation.** Closes #29 and #31. Touches metadata
   only — no method changes the numbers it returns. This is the commit the
   design is really about, and it can be reverted without taking anything
   else with it.
2. **The `interpto_hz` grid fix.** Closes #23. The *only* commit that alters
   numeric output, and independent of the freq mechanism — it would be worth
   doing even if `freq` stayed a stored attribute. Keeping it separate means
   a regression in resampled data can be bisected and reverted without
   losing the metadata fix.
3. **Cleanup.** The `freq=self.freq` constructor kwargs in `copy`,
   `to_basetseries` and the shallow-copy fallback, and the
   `attr not in ['freq', ...]` special-cases. Verified by prototype to be
   *optional*: a NaN `self.freq` is absorbed by `_is_unset` before reaching
   the setter, so these paths are correct as they stand and this commit is
   tidying, not repair. Sequencing it last keeps it out of the risk budget.

A prototype of the property against pandas 3.0.5 confirmed the mechanism
before any of this was committed to: declarations propagate correctly through
slicing, arithmetic, `dropna`, `copy`, `copy(deep=True)`, pickle, `concat`
and `nlargest`, expire correctly on `iloc[::2]` and `sort_values`, and the
setter rejects every invalid rate. Property reads cost 1.4 µs.

**Not yet verified on pandas 2.x.** The prototype ran on 3.0.5; this project
floors at `pandas>=2.0.0` and CI exercises 2.3.3 on Python 3.9/3.10. A
version-matrix divergence in exactly this area produced the `objs` /
`input_objs` bug in PR #25, so commit 1 is not mergeable until CI is green on
the full matrix, not merely on the developer's interpreter.

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
  degenerate source and of an invalid `new_freq`. Includes the same-rate
  round trip `baseTs(data, np.arange(1000)/30.0).interpto_hz(30)` as an
  explicit regression case for the floating-point undershoot in Section 4 —
  it must return 1000 samples, not 999.
- `baseTs(..., freq=999.0).zscale().freq == 999.0`, guarding the
  `_create_new_with_data` metadata-list addition in Section 5. Without that
  one-line addition this test fails, and nothing else in the suite catches it.
- A `DatetimeIndex` series constructs and reads `.freq` as NaN rather than
  raising `TypeError`, and a spectral method on it raises the guard's
  `ValueError` rather than the raw conversion error.

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

Helps with #20, but less than the first draft claimed. `lowess_fit` and
`outlier_indices` have the same "did the index change?" question, and the
token *shape* is reusable for it — invalidate to `None` on mismatch, as
agreed, rather than reslicing. But the equivalence argument that makes the
token airtight here does not carry over: it holds because the token is
exactly what `_calculate_effective_frequency` reads, and those two attributes
are position-indexed, so an interior permutation that leaves the token intact
would still invalidate them. #20 needs a stricter check than this one.

Documentation to update, none of which the first draft mentioned:
`docs/EXAMPLES.md:1064` assigns `ts.freq = sampling_rate`; `docs/API.md` and
`docs/API_SERIES.md` document `freq` as a stored attribute.
`docs/CHANGELOG.md` takes the breaking changes.

Corrected during implementation: this list originally named
`docs/USER_GUIDE.md` too, and that was wrong. Every `freq` reference in that
file is either a constructor kwarg with a positive rate or a read of
`ts.freq`, both of which remain valid — there was no stale claim to fix.
`interpto_hz` turned out to have no prior documentation at all in any of
these files, so its entry is new rather than a rewrite.

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
6. `baseTs(data, times, freq=0.0)` and `freq=-1.0` now raise at construction.
   They were accepted, deliberately, because `interpto_hz(0)` used to mint
   such objects; this release stops it from doing so. See Section 3.
7. `baseTs` constructed on a `DatetimeIndex` no longer raises `TypeError`; it
   builds, and `.freq` reads NaN. See Section 6.
8. Arithmetic between series preserves an explicitly declared rate when the
   result's index is unchanged, where it previously always re-derived.
   Found during implementation, not design. On `main`, a series declaring
   10.0 Hz over a time base measuring 9.9 Hz reported `a.freq == 10.0` but
   `(a + b).freq == 9.9` — the same object answering differently for an
   operation that never touched its index, which is #29's defect living in
   the arithmetic path rather than a separate one. The token makes both
   answers 10.0. This narrows #19's fix, which deliberately made arithmetic
   re-derive; #19's actual failure mode was a stale rate surviving an index
   *change* (`resample` reporting 100 Hz for a 1 Hz series), and that stays
   fixed, because a changed index moves the token.
