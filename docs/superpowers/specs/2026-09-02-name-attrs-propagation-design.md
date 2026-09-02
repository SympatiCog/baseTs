# Carrying pandas' identity fields across derivation (#35, #39)

Date: 2026-09-02
Issues: #35 (primary), #39 (closed as a consequence)
Branch: `fix/name-attrs-propagation`
Baseline measured on: `main` @ `c82a162`, pandas 3.0.5, numpy 2.5.1

## Problem

A `baseTs` is a `pd.Series`, so it has three pieces of identity that pandas
itself defines and propagates: the Series `name`, the `attrs` dict, and
`flags`. baseTs drops all three across most derivations. Plain `pd.Series`
drops none of them on the same operations.

Measured on `main`, seeding `ts.name = 'SIG'`, `ts.attrs['unit'] = 'mV'` and
`ts.flags.allows_duplicate_labels = False`:

| path | `name` | `attrs` | `flags` |
|---|---|---|---|
| `iloc[:50]`, `rolling(5).mean()` | kept | kept | kept |
| `head()` | **lost** | **lost** | **lost** |
| `dropna()`, `round()`, `sort_values()` | **lost** | kept | kept |
| `ts + 1` and every arithmetic operator | **lost** | **lost** | **lost** |
| `copy(deep=True)`, `copy.deepcopy`, `apply_function` | **lost** | **lost** | **lost** |
| `copy(deep=False)` | **lost** | kept | kept |
| `lowpass_filter`, `bandpass_at`, `zscale`, `detrend`, `sg_filter`, `lowess_detrend`, `filter_outliers`, `interpolate_gaps`, `interpto_hz` | **lost** | **lost** | **lost** |
| `baseTs(ts)`, `TimeSeriesData(ts)`, `to_basetseries()` | **lost** | **lost** | **lost** |

`pickle.dumps(ts)` raises `AttributeError: 'baseTs' object has no attribute
'_name'` on `main`. Pickling a baseTs does not work at all today.

### The issue text and its correcting comment both undercount

Issue #35 names one site (`copy(deep=True)`). The correcting comment on it
raises that to two (adding `_create_new_with_data`). The real figure is
**one missing registry entry plus six rebuild sites**, and the loss reaches
plain pandas calls (`head()`, `dropna()`, `sort_values()`, arithmetic) that
neither document mentions.

### Two independent causes

**Cause A — `_name` is absent from `_metadata`.**
`TimeSeriesData._metadata` *replaces* `pd.Series._metadata`, which is
`['_name']`. Every pandas path that relies on `__finalize__` to carry the
name therefore drops it, and `__getstate__`/`__setstate__` never round-trip
`_name`, which is why pickling raises. This is issue **#39**'s root cause,
and it is not baseTs-specific: a five-line `pd.Series` subclass that
replaces `_metadata` reproduces the `head()`/`dropna()`/`round()` half
exactly.

`iloc` keeps the name despite this because pandas' fast slice path carries
`_name` through the constructor rather than through `__finalize__` — which
is precisely why the loss looks arbitrary from the outside.

**Cause B — six sites rebuild an object through the constructor** and
restore only `_metadata` names. `attrs` and `flags` are not in `_metadata`
(pandas handles them separately inside `__finalize__`), so no rebuild site
carries them:

| # | site | file:line | copies |
|---|---|---|---|
| 1 | `baseTs.copy(deep=True)` | core.py:2347 | `_metadata` loop |
| 2 | `baseTs.copy(deep=False)` fallback | core.py:2378 | `_metadata` loop |
| 3 | `baseTs._create_new_with_data` | core.py:424 | **hand-curated list** |
| 4 | `baseTs._update_series_data` | core.py:377 | `_metadata` loop |
| 5 | `TimeSeriesData.copy` fallback | series.py:773 | `_metadata` loop |
| 6 | `TimeSeriesData.to_basetseries` | series.py:851 | `_metadata` loop |
| 7 | `TimeSeriesData._wrap_result_as_basets` | series.py:1027 | `_metadata` loop |
| 8 | `TimeSeriesData._copy_metadata_from_basetseries` | series.py:572 | `_metadata` loop |

Site 7 is a *third* rebuild site that neither the issue nor its correcting
comment names. Site 3 is the one Cause A cannot reach, because it iterates
its own curated list rather than `_metadata`.

`baseTs.copy` is not merely a user-facing method: **pandas calls it
internally**. `head()` reaches it at `generic.py:5749` and `sort_values()` at
`series.py:3759`, so the rebuild sits on ordinary pandas paths.

## Decisions taken

1. **Fix both causes.** Cause A is #39's fix, so #39 closes here.
2. **`signal_name` and `name` stay independent**, and the docstrings say so.
   `name` is pandas': any hashable, kept verbatim. `signal_name` is baseTs'
   plot label: coerced to an uppercase string by `normalise_label`. Syncing
   them would force one to break the other's contract, and it would smuggle
   in a decision that belongs to #56.
3. **`flags` is folded in**, not filed. It is dropped by exactly the same
   sites for exactly the same reason, and this change moves and re-documents
   that exact code. Filing it would guarantee a fourth pass over the same
   eight loops.

## Design

### Half A — `_name` joins `_metadata`

```python
_metadata = pd.Series._metadata + [
    '_freq_declaration', 'signal_name', 'history', ...
]
```

Composed from `pd.Series._metadata` rather than hardcoding `'_name'`, so a
future pandas that adds a fourth entry is carried rather than dropped — the
mistake being fixed is exactly the hardcoding of a list pandas owns.

Consequences, each handled deliberately:

- **All eight `_metadata` loops start copying `_name`.** That is the intent
  at sites 1, 2, 4, 5, 6, 8 and in `__finalize__`.
- **Site 7 (`_wrap_result_as_basets`) must carry the *result's* name, not
  `self`'s.** `super().__add__` has already applied pandas' own rule —
  `ts_a + ts_b` with differing names yields `None`, not the left operand's
  name. Copying `self._name` over the top would silently diverge from pandas
  on every two-operand operation. This site therefore excludes `_name` from
  the loop the way it already excludes `signal_name`, and takes the name from
  `result`.
- **`deepcopy_metadata_value` is reached with `_name`.** A Series name must
  be hashable, so it cannot be a `list`/`dict`/`ndarray` and the isinstance
  gate never matches it. No change needed; asserted by a test rather than
  left as an assumption.
- **#27's `_metadata` census must classify the new field**: `_name` joins
  `PRESERVED_BY_OP`, the quoted counts go `(10, 3)` → `(11, 3)`, and
  `_seeded()` must set a non-default name or
  `test_seeding_leaves_no_metadata_field_vacuous` is toothless on it.

Measured with `_metadata` monkeypatched at runtime: `name` becomes correct on
every path except site 3's, pickling round-trips, and the suite is **968
passed, 2 failed** — both failures being #27's census guard correctly
demanding the new field be classified. No behavioural breakage.

### Half B — one door for the identity triple

A module-level helper in `series.py`, beside `_detach_shared_metadata`:

```python
def _carry_identity(target, source):
    """Copy the three identity fields pandas' own __finalize__ carries."""
```

It copies:

- **`name`** — `object.__setattr__(target, '_name', source.name)`, by the
  private slot. This is the invariant #20 established: assigning through a
  public property runs a setter, and `Series.name`'s setter validates
  hashability, so a name that reached the object before that rule existed
  would raise here rather than at its origin.
- **`attrs`** — `deepcopy(source.attrs)` when non-empty, else left alone.
  **Verified against pandas' source, not assumed:** `NDFrame.__finalize__`
  deep-copies attrs, guarded by an `if other.attrs:` emptiness check it
  documents as a 50× performance concern. An earlier draft of this design
  said "shallow copy, matching pandas" and was wrong. Matching pandas here
  means `iloc` and `copy()` isolate nested attrs values identically.
- **`flags.allows_duplicate_labels`** — the one flag pandas' `__finalize__`
  propagates.

Called from all eight sites. Sites 1–2 and 5–8 could get `name` from Half A
alone; they call the helper anyway, because a single door that carries all
three is the point and per-site divergence is what produced this issue.

### Making a ninth site fail loudly

A helper called from eight places is still eight places that can forget. The
repo's own record on this — #15, #20, #38, and #27's `PRESERVED_BY_OP`
frozensets — says the guard has to be a test that fails when a new site
appears, not a comment asking people to remember.

So: a census test in #27's shape. The path table above becomes
`KEEPS_IDENTITY` / `DROPS_IDENTITY` frozensets, asserted against what the
calls actually do, plus an assertion that the two sets exactly cover the
enumerated paths. A derivation path added without classification fails the
suite.

## Testing

New `tests/unit/test_identity_propagation.py`:

- the path census above, over `name`, `attrs` and `flags`;
- **a pickle round-trip** — the suite has none at all today, which is why
  #39 survived; it must cover `dumps`/`loads` and then a derivation off the
  unpickled object, which is #39's stated symptom;
- attrs isolation: mutating a derived object's `attrs`, including a nested
  value, must not reach the parent;
- the two-operand arithmetic name rule (`a + b` with differing names → `None`,
  matching pandas), which is the one place Half A could silently diverge;
- `deepcopy_metadata_value` leaves a name untouched.

Updated `tests/unit/test_core.py`: #27's census gains `_name`.

TDD: every test above is written and seen to fail before the fix lands.
Each fix is then mutation-tested — delete the line, confirm the test fails —
because reading a test cannot tell you whether it would.

## Deliberately not in scope

- **#56** (`_create_new_with_data` re-upper-cases `signal_name`, so `zscale`
  and `iloc` disagree). It needs a decision about which behaviour is
  intended; this change does not touch it, and decision 2 above keeps the two
  fields separable so #56 stays independently fixable.
- **Seeding `name` from `signal_name`** when unset, and `from_df` setting
  `name` from `data_col`. Both are the sync question decision 2 declined.
- **`utils.add_constant` / `diff` / `dediff`** build a bare `baseTs` from
  arrays and copy **no** metadata at all — thirteen fields, not three. That
  is a different and wider defect. Checked for reachability: `diff` and
  `dediff` are consumed for `.data`/`.times` only inside `diff_ts`/`dediff`,
  `add_constant` has no caller, and none is in `__all__`, so no public API
  returns one of these objects. Noted here; to be filed rather than widened
  into.

## Risk register

- **Version matrix.** `_metadata` is version-sensitive machinery and
  `__finalize__`'s attrs handling differs across pandas majors. Everything
  above is measured on pandas 3.0.5 / numpy 2.5.1. Before merging: throwaway
  venvs on pandas 2.3.3 with numpy 1.26 and numpy 2.x, per this project's own
  `pandas>=2.0.0` floor and CI's Python 3.9/3.10 legs. The specific claims to
  re-verify there are `pd.Series._metadata == ['_name']` and that
  `__finalize__` deep-copies attrs under an emptiness guard.
- **`_update_inplace` and `_mgr` surgery.** #20's lesson: pandas mutates
  objects without passing through anything this repo writes. Half A rides
  `_metadata`, which pandas itself consults, so it is not exposed to this;
  Half B's sites are all rebuilds, which are. The census test is what bounds
  the claim.
- **Behaviour change, and it is user-visible.** Derived objects now carry a
  name where they previously handed back `None`. Anything asserting
  `result.name is None` after a filter changes. CHANGELOG entry covers #35
  and #39 with that framing.

## Review gate

`consensus-review` rounds until findings go trivial, every finding verified
against a `main` worktree before acting, then a **different** harness as the
merge gate rather than another round of the same panel — the pattern that
caught what converged panels missed on #20, #28 and #34.
