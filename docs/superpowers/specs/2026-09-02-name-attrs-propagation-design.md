# Carrying pandas' identity fields across derivation (#35, #39)

Date: 2026-09-02
Issues: #35 (primary), #39 (closed as a consequence)
Branch: `fix/name-attrs-propagation`
Baselines: `main` @ `c82a162`, measured on pandas 3.0.5/numpy 2.5.1,
pandas 2.3.3/numpy 1.26.4 and pandas 2.3.3/numpy 2.2.6

Revision 2, after a `consensus-review` panel round (codex + agy). What that
round changed is recorded in "What the review changed" at the end.

## Problem

A `baseTs` is a `pd.Series`, so it carries three pieces of identity that
pandas itself defines and propagates: the Series `name`, the `attrs` dict,
and `flags`. baseTs drops all three across most derivations. Plain
`pd.Series` drops none of them on the same operations.

Measured on `main`, seeding `ts.name = 'SIG'`, `ts.attrs['unit'] = 'mV'` and
`ts.flags.allows_duplicate_labels = False`. **Measured on pandas 3.0.5**;
the one row that differs by pandas version is called out below the table.

| path | `name` | `attrs` | `flags` |
|---|---|---|---|
| `iloc[:50]`, `rolling(5).mean()` | kept | kept | kept |
| `head()` | **lost** | **lost** | **lost** |
| `dropna()`, `round()`, `sort_values()` | **lost** | kept | kept |
| `ts + 1` and every arithmetic operator | **lost** | **lost** | **lost** |
| `copy(deep=True)`, `copy.deepcopy`, `apply_function` | **lost** | **lost** | **lost** |
| `copy(deep=False)` | **lost** | kept | kept |
| `lowpass_filter`, `bandpass_at`, `zscale`, `detrend`, `sg_filter`, `lowess_detrend`, `filter_outliers`, `interpolate_gaps()` | **lost** | **lost** | **lost** |
| `interpolate_gaps(inplace=True)`, `shift_time(inplace=True)`, `ts.data = x` | **lost** | **lost** | **lost** |
| `baseTs(ts)`, `TimeSeriesData(ts)`, `to_basetseries()` | **lost** | **lost** | **lost** |

**Version divergence, one row only.** `head()` keeps all three on pandas
2.3.3 and loses all three on 3.0.5, because pandas 3.0's `head()` is
`self.iloc[:n].copy()` (`generic.py:5749`) and so reaches our rebuilding
`copy()`, where 2.3.3's does not. Every other row is identical across
2.3.3/numpy 1.26.4, 2.3.3/numpy 2.2.6 and 3.0.5/numpy 2.5.1.

**Pickling produces a broken object.** Stated precisely, because two earlier
attempts at this sentence were wrong: `pickle.dumps` succeeds,
`pickle.loads` succeeds, and the object that comes back is unusable —
`b.name`, `b.iloc[:3]`, `b.head(2)`, `b + 1` and even **`repr(b)`** all raise
`AttributeError: 'baseTs' object has no attribute '_name'`. `b.mean()` still
works. Identical on both pandas majors. This is #39's symptom, and `repr`
raising is worse than #39 describes: you cannot look at the object to see
what is wrong with it.

### The issue text and its correcting comment both undercount

Issue #35 names one site. The correcting comment on it raises that to two.
The real figure is **one missing registry entry plus nine sites**, and the
loss reaches plain pandas calls (`head()`, `dropna()`, `sort_values()`,
arithmetic) that neither document mentions.

### Two independent causes

**Cause A — `_name` is absent from `_metadata`.**
`TimeSeriesData._metadata` *replaces* `pd.Series._metadata`, which is
`['_name']`. Every pandas path that relies on `__finalize__` to carry the
name therefore drops it, and `__setstate__` never restores `_name`, which is
why an unpickled object is broken. This is issue **#39**'s root cause, and it
is not baseTs-specific: a five-line `pd.Series` subclass that replaces
`_metadata` reproduces the `head()`/`dropna()`/`round()` half exactly.

`iloc` keeps the name despite this because pandas' fast slice path carries
`_name` through the constructor rather than through `__finalize__` — which is
precisely why the loss looks arbitrary from the outside.

**Cause B — nine sites rebuild or re-initialise an object** and restore only
`_metadata` names. `attrs` and `flags` are not in `_metadata` (pandas handles
them separately inside `__finalize__`), so no site carries them. The nine
split into two groups that need **different mechanisms**, which is the main
thing the review round changed:

**Group 1 — rebuild sites.** A *new* object is constructed and the old one's
metadata copied onto it. `target` and `source` are different objects.

| # | site | file:line | copies |
|---|---|---|---|
| 1 | `baseTs.copy(deep=True)` | core.py:2347 | `_metadata` loop |
| 2 | `baseTs.copy(deep=False)` fallback | core.py:2378 | `_metadata` loop |
| 3 | `baseTs._create_new_with_data` | core.py:424 | **hand-curated list** |
| 4 | `TimeSeriesData.copy` fallback | series.py:773 | `_metadata` loop |
| 5 | `TimeSeriesData.to_basetseries` | series.py:851 | `_metadata` loop |
| 6 | `TimeSeriesData._wrap_result_as_basets` | series.py:1027 | `_metadata` loop |

Site 6 is a rebuild site neither the issue nor its correcting comment names.
Site 3 is the one Cause A cannot reach, because it iterates its own curated
list rather than `_metadata`.

**Group 2 — self-mutating re-initialisation sites.** `super(TimeSeriesData,
self).__init__(...)` is called on `self`. pandas' own `__init__` resets
`name`, `attrs` and `flags` to defaults; `_metadata` fields survive only
because they live in the instance `__dict__`, which `pd.Series.__init__` does
not touch — an accident, not a mechanism.

| # | site | file:line | saves/restores |
|---|---|---|---|
| 7 | `baseTs._update_series_data` (reached by `ts.data = x`) | core.py:382 | `_metadata` only |
| 8 | `baseTs.interpolate_gaps(inplace=True)` | core.py:1758 | **nothing** |
| 9 | `baseTs.shift_time(inplace=True)` | core.py:1824 | **nothing** |

These three are the same three `pd.Series.__init__` doors #20 identified,
where the round that went looking for exactly that pattern guarded two of
three. `ts.times = x` is *not* one: it assigns `self.index` and never
re-initialises, so it touches no identity field.

`baseTs.copy` is not merely a user-facing method: **pandas calls it
internally**. `head()` reaches it at `generic.py:5749` on pandas 3.0 and
`sort_values()` at `series.py:3759`, so a rebuild site sits on ordinary
pandas paths.

## Decisions taken

1. **Fix both causes.** Cause A is #39's fix, so #39 closes here.
2. **`signal_name` and `name` stay independent**, and the docstrings say so.
   `name` is pandas': any hashable, kept verbatim. `signal_name` is baseTs'
   plot label: coerced to an uppercase string by `normalise_label`. Syncing
   them would force one to break the other's contract, and would smuggle in a
   decision that belongs to #56.
3. **`flags` is folded in**, not filed. It is dropped by exactly the same
   sites for exactly the same reason, and this change moves and re-documents
   that exact code. Filing it would guarantee a fourth pass over the same
   loops.

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

- **Every `_metadata` loop starts copying `_name`.** That is the intent at
  sites 1, 2, 4, 5, 7 and in `__finalize__`.
- **Site 6 (`_wrap_result_as_basets`) must carry the *result's* name, not
  `self`'s.** `super().__add__` has already applied pandas' own rule —
  `ts_a + ts_b` with differing names yields `None`, not the left operand's
  name. Copying `self._name` over the top would silently diverge from pandas
  on every two-operand operation. This site therefore takes its identity from
  `result`. Confirmed by the panel against live pandas: `result.name` is
  already pandas-resolved whichever dunder produced it, including the
  reflected ones.

  **As built, the loop is given no `_name` exclusion**, though this document
  previously said it would get one alongside `signal_name`'s. The
  `_carry_identity(new_basets, result)` call that follows overwrites whatever
  the loop set, so the exclusion would be dead code that reads as a
  safeguard. Mutation testing settled it — no test could tell the two
  spellings apart — and the implementation review flagged the stale sentence
  this replaces.
- **Half A does nothing for sites 8 and 9**, which have no metadata loop to
  ride. This is why Group 2 needs its own mechanism rather than a wider
  registry.
- **Half A alone does not close #39 either.** It fixes objects pickled *from
  now on*. A blob written before this change carries no `_name` key, because
  `__getstate__` serialised the registry as it stood then, so loading it with
  the fixed code still yields an object whose every operation raises. Closing
  #39 as stated — "unpickled objects are broken" — needs `__setstate__` to
  normalise a missing `_name` to `None` after delegating to pandas. That is
  the same normalise-at-the-door move `_detach_shared_metadata` already makes
  for `history` and `outlier_filter`, applied to the one door that
  reconstitutes an object from bytes.
- **`deepcopy_metadata_value` is reached with `_name`.** A Series name must be
  hashable, so it cannot be a `list`/`dict`/`ndarray` and the isinstance gate
  never matches it. No change needed; asserted by a test rather than left as
  an assumption.
- **#27's `_metadata` census must classify the new field**: `_name` joins
  `PRESERVED_BY_OP`, the quoted counts go `(10, 3)` → `(11, 3)`, and
  `_seeded()` must set a non-default name or
  `test_seeding_leaves_no_metadata_field_vacuous` is toothless on it.

Measured with `_metadata` monkeypatched at runtime: `name` becomes correct on
every path except site 3's, the unpickled object works, and the suite is
**968 passed, 2 failed** — both failures being #27's census guard correctly
demanding the new field be classified. No behavioural breakage. The panel
re-ran this independently and reproduced the same two failures.

### Half B, Group 1 — one door for the identity triple

A module-level helper in `series.py`, beside `_detach_shared_metadata`:

```python
def _carry_identity(target, source):
    """Copy the three identity fields pandas' own __finalize__ carries."""
```

It copies:

- **`name`** — `object.__setattr__(target, '_name', getattr(source, '_name', None))`.
  By the private slot, on the same invariant as #20: assigning through the
  public property runs a setter, and `Series.name`'s setter validates
  hashability, so a name that predates that rule would raise here rather than
  at its origin.

  **Read with `getattr`, never `source.name`.** `NDFrame.__getstate__`
  serialises `{k: getattr(self, k, None) for k in self._metadata}` — the
  registry *as it was at dump time*. A blob pickled before this change
  therefore has no `_name` key, and loading it with the fixed code still
  produces an object without the attribute. Verified: `old.name` and
  `repr(old)` both still raise after the fix. Reading `source.name` in the
  helper would make the fix itself raise on every legacy pickle.
- **`attrs`** — `deepcopy(source.attrs)` when non-empty, else left alone.
  **Verified against pandas' source on both majors, not assumed:**
  `NDFrame.__finalize__` deep-copies attrs, guarded by an `if other.attrs:`
  emptiness check it documents as a 50× performance concern. An earlier draft
  of this design said "shallow copy, matching pandas" and was wrong. Matching
  pandas here means `iloc` and `copy()` isolate nested attrs values
  identically.
- **`flags.allows_duplicate_labels`** — by plain assignment, for a reason
  that had to be rewritten once the "freshness" premise was tested.

  pandas 2.3.3's `__finalize__` assigns (`self.flags.adl = other.flags.adl`);
  pandas 3.0.5's ANDs (`self.flags.adl = self.flags.adl and other.flags.adl`).
  Revision 2 justified plain assignment by claiming every target is freshly
  constructed, so `True and x == x`. **That premise is false**, and the test
  revision 2 said would pin it asserted end-to-end outcomes rather than the
  premise. Measured: `pd.Series.copy(deep=False)` on a baseTs returns an
  object that is *already* `isinstance(..., baseTs)` with the flag already
  carried by pandas' own `__finalize__`, so `baseTs.copy(deep=False)`'s
  rebuild fallback is not reached at all in normal operation and its target,
  when it is reached, is not fresh.

  Plain assignment is right on its own merits instead: the helper's contract
  is "this object is a derivation of that one", and a derivation takes the
  source's declaration. AND-ing would let a target's incidental default
  override an explicit `False` on the source in one direction and not the
  other. The freshness question is therefore dropped rather than asserted,
  and the divergence from pandas 3.x's AND is documented in the docstring as
  deliberate.

  **Restoring the flag can raise, and that is a behaviour change.** If the
  operation produced a duplicate index while the source declared
  `allows_duplicate_labels=False`, pandas refuses the restore with
  `DuplicateLabelError`. This is reachable today: on a length-1 series
  `_update_series_data` builds its replacement index with
  `np.linspace(start, end, n)` where `start == end`, so `ts.data = [1., 2., 3.]`
  yields the index `[0.0, 0.0, 0.0]`. That call currently succeeds *because*
  the flag is not carried; carrying it makes it raise.

  The flag is still carried, because silently dropping a declaration the
  caller made is the failure mode this whole change exists to fix. But the
  refusal is caught and re-raised as a `ValidationError` naming the
  operation, the duplicate labels and the declaration that forbids them —
  pandas' own message says only "Index has duplicates" and gives the caller
  nothing to act on. The degenerate `linspace` index behind the reachable
  case is a pre-existing defect of its own and is filed, not fixed here.

Called from all six Group 1 sites. Sites 1, 2, 4, 5 and 6 would get `name`
from Half A alone; they call the helper anyway, because a single door
carrying all three is the point and per-site divergence is what produced this
issue.

### Half B, Group 2 — collapse three doors into one

The review's strongest point: `_carry_identity(target, source)` **cannot work
as a post-hoc call** where `target is source`. By the time it could run, the
re-initialisation has already reset the source's own identity fields, so
`_carry_identity(self, self)` is a no-op dressed as a fix.

So Group 2 does not get a call added to it — it gets **deleted as three
separate doors**. A single primitive on `baseTs`:

```python
def _adopt_data_inplace(self, values, index):
    """Re-initialise this object's data and index, keeping everything else."""
```

It snapshots `_metadata` *and* the identity triple, calls
`super(TimeSeriesData, self).__init__(values, index=index)`, then restores
both. Sites 7, 8 and 9 all call it; `_update_series_data` keeps its
index-derivation logic and delegates the re-init, and the two `inplace=True`
branches lose their hand-rolled `super().__init__` calls entirely.

This is the move the repo has made at #15, #20, #38 and #27: when the same
omission appears at N sites, delete the sites rather than instrument them.
One door can be forgotten in one place; three cannot be kept in step. It also
means a future `inplace=True` method that needs to re-initialise has an
obvious thing to call, which is what sites 8 and 9 lacked.

### Making a tenth site fail loudly

The review's other strong point: the census test I first proposed was closed
over the same hand-authored path table it was meant to police. It would fail
if a *listed* path changed group, but could never fail for a path missing
from the table — which is precisely how sites 7–9 went unfound in revision 1.

The guard therefore derives its subjects instead of listing them:

- **Every `inplace=True` branch**, discovered by reflection over `baseTs`'s
  own public methods whose signature has an `inplace` parameter, and asserted
  to equal the set that has been classified. Each classified method is then
  called on a seeded object and asserted to preserve the identity triple.

  Precisely what this buys, since revision 2 overclaimed it: reflection
  cannot invent a valid cutoff frequency, so the *arguments* stay a
  hand-written table. What is derived is the **membership** check — adding a
  method that takes `inplace` fails the suite until someone classifies it.
  It does not exercise a new method for free; it refuses to stay green while
  one is unaccounted for. That is the property sites 8 and 9 needed and a
  hand-written path list could never have.

  Measured while building it: **36 of 53** `inplace`-capable methods lose the
  triple on `main`, and the loss correlates exactly with the method being
  baseTs-defined rather than inherited — every inherited pandas method
  already keeps it. That correlation is what makes the owner-based partition
  a real boundary rather than a convenience.
- **Every direct re-initialisation**, asserted by a source-level check that
  `super(TimeSeriesData, self).__init__` appears in `core.py` only inside
  `_adopt_data_inplace`. A tenth site re-introducing the pattern fails the
  suite rather than waiting for someone to notice.
- The enumerated derivation-path table is kept as well, in #27's
  `KEEPS_IDENTITY` shape, for the pandas-native paths that reflection cannot
  discover — but it is now the *supplement*, not the mechanism.

## Testing

New `tests/unit/test_identity_propagation.py`:

- the reflection-derived `inplace` sweep and the source-level re-init check;
- the enumerated derivation-path census over `name`, `attrs` and `flags`;
- **a pickle round-trip** — the suite has none at all today, which is why #39
  survived. It must assert the *unpickled object works*: `repr`, `.name`,
  `iloc`, `head` and arithmetic, not merely that `loads` returned;
- attrs isolation: mutating a derived object's `attrs`, including a nested
  value, must not reach the parent;
- the two-operand arithmetic name rule (`a + b` with differing names → `None`,
  matching pandas), the one place Half A could silently diverge;
- the freshness assumption behind the `flags` assignment, per above;
- `deepcopy_metadata_value` leaves a name untouched.

Updated `tests/unit/test_core.py`: #27's census gains `_name`.

TDD: every test above is written and seen to fail before the fix lands. Each
fix is then mutation-tested — delete the line, confirm the test fails —
because reading a test cannot tell you whether it would.

## Deliberately not in scope

- **#56** (`_create_new_with_data` re-upper-cases `signal_name`, so `zscale`
  and `iloc` disagree). It needs a decision about which behaviour is
  intended; decision 2 keeps the two fields separable so #56 stays
  independently fixable.
- **Seeding `name` from `signal_name`** when unset, and `from_df` setting
  `name` from `data_col`. Both are the sync question decision 2 declined.
- **`utils.add_constant` / `diff` / `dediff`** build a bare `baseTs` from
  arrays and copy **no** metadata at all — thirteen fields, not three. A
  different and wider defect. Checked for reachability: `diff` and `dediff`
  are consumed for `.data`/`.times` only inside `diff_ts`/`dediff`,
  `add_constant` has no caller, and none is in `__all__`, so no public API
  returns one. To be filed, not widened into. The panel independently agreed
  none of these exclusions leaves an incoherent state.
- **`interpolate_missing(inplace=True)` is dead.** It passes `inplace=` to
  `interpolate_missing_values`, which returns `None` in that branch, then
  reads `.data` off it — `AttributeError` on both pandas majors, with and
  without NaNs in the data. Dead from introduction, the same shape as #27's
  `butterpass_at`. Found by the reflection sweep, recorded in the test file's
  `INPLACE_KNOWN_BROKEN` so the exclusion is accounted for rather than
  silent, and to be filed.
- **`_update_series_data`'s degenerate replacement index.** When the data
  length changes it rebuilds the index as `np.linspace(start, end, n)`, and
  on a length-1 series `start == end`, so every timestamp is identical. To be
  filed: it is the pre-existing cause behind the `DuplicateLabelError`
  interaction above, and inventing a constant index is wrong independently of
  any flag.

## Risk register

- **Version matrix — partly discharged already.** Verified on pandas 2.3.3
  (numpy 1.26.4 and 2.2.6) as well as 3.0.5: `pd.Series._metadata ==
  ['_name']`; `__finalize__` deep-copies attrs under an emptiness guard; the
  `head()` divergence above; the `flags` AND-vs-assign difference above; and
  the branch baseline suite at **970 passed** in both 2.3.3 venvs. The full
  suite must be re-run in all three combos after implementation.
- **`_update_inplace` and `_mgr` surgery.** #20's lesson: pandas mutates
  objects without passing through anything this repo writes. The panel
  checked `_inplace_arith`/`_update_inplace` specifically and found no defect:
  `_update_inplace` swaps `_mgr` and leaves `name`/`attrs`/`flags` untouched,
  so `ts += 1` keeps the target's own values — which is exactly what stock
  `pd.Series` does. Verified, no fix needed, and worth a test so the next
  reviewer does not re-raise it.
- **Behaviour change, and it is user-visible.** Derived objects now carry a
  name where they previously handed back `None`. Anything asserting
  `result.name is None` after a filter changes. CHANGELOG covers #35 and #39
  with that framing.

## What implementation review round 2 changed

Scoped deliberately away from the inventory and onto the round-1 fixes, on
the grounds that this repo's rounds mostly find defects in the previous
round's fix. All three findings were exactly that.

- **The atomicity fix drained a one-shot index.** `_refuse_undeclarable_index`
  built a `pd.Index` from its argument to test it, then let the caller hand
  the *original* to pandas - so a generator index was exhausted by the check
  and `super().__init__` saw an empty one. Fixed by returning the
  materialised index and requiring the caller to use it: exactly one candidate
  index, never two. Not reachable from the three current call sites, all of
  which pass an array or an `Index`, but a trap laid for the next one.
- **The `_metadata` shadow fix deleted too much.** Dropping it
  unconditionally also discarded a registry someone had deliberately extended
  on a single instance; the values survived but nothing tracked them
  afterwards. Now dropped only when it is *stale* - when it no longer covers
  what the class declares.
- **The AST scan's `__init__` skip ignored nesting.** A flat `ast.walk`
  descends into nested scopes, so an ordinary `super().__init__()` inside a
  nested class's own `__init__` was attributed to the enclosing method. The
  scan now yields only calls in a function's own scope.

**Found independently while the round ran:** the refusal message named every
duplicated label, building an 889,108-character exception from an index of
100,000 duplicated pairs. This repo already has `utils._describe` for exactly
that failure, written after a 200k-element list produced a 1.4 MB message; the
new helper now uses it and names a bounded sample plus a count.

Three findings the round raised and dropped on verification, all worth
recording because they were checked rather than assumed: `.has_duplicates`
does not raise on unhashable elements in this pandas; the `if declared:`
truthiness test handles `np.bool_(False)` correctly, so it is *not* a
recurrence of the `is False` bug this repo shipped before; and the
`_metadata` snapshot inside `_adopt_data_inplace` cannot be made to fail by
any of this class's own metadata names.

## What the implementation review changed

A `consensus-review` round against the code (codex ✓, agy ✓), the first not
aimed at the design. Five findings, all reproduced against a `main` worktree
before acting, all fixed in the same branch.

- **`_adopt_data_inplace` was not atomic** (both models). On the refusal path
  it had already committed the new data and index and let the flag fall back
  to pandas' permissive default, so an operation that reported failure left a
  mutated object with its declared protection silently switched off — and the
  CHANGELOG claimed the opposite in the same breath. Fixed by checking the
  prospective index *before* the re-initialisation
  (`_refuse_undeclarable_index`), which makes the method all-or-nothing.
- **A legacy pickle healed once and then re-broke.** pandas writes `_metadata`
  into the blob and installs it as an *instance* attribute, so a pre-fix blob
  permanently shadowed the class registry: the name came back, then vanished
  again on the next re-pickle or `ts.data = x`, because both iterate
  `self._metadata`. `__setstate__` now drops the shadow before healing.
- **The legacy-pickle fixture could not see that**, because it deleted the
  `_name` value but kept the *current* registry in the state dict. A real blob
  carries the old one. This is why a full mutation round missed the defect —
  the fixture was not the shape it claimed to be.
- **`test_a_permissive_flag_is_not_turned_restrictive` was vacuous.** Its
  target went through `.copy()`, which is always freshly constructed and
  therefore permissive, so `_carry_identity`'s guard short-circuited and the
  assign-vs-AND choice was never reached; the test passed with the whole flag
  mechanism deleted. Rewritten against the helper directly.
- **Both halves of the "derive, don't hand-list" guard had holes.** The
  reflection filter keyed on the literal class name `baseTs`, so a method
  defined on `TimeSeriesData` was invisible to it; and the AST scan required
  the two-argument `super(Cls, self)` form, so a zero-argument
  `super().__init__(...)` in an ordinary method — equivalent at runtime, and
  equally destructive — slipped past. Both widened, and both fixes verified by
  injecting the exact site each used to miss.

Also corrected: this document's claim that `_wrap_result_as_basets` excludes
`_name` from its loop, which the implementation deliberately does not do.

## What review round 2 changed

A second `consensus-review` round (codex ✓, agy ✓), scoped away from the
inventory and onto the two mechanisms revision 2 introduced. Three findings
were raised by both models; all four below were verified independently before
acting.

- **Reading `source.name` breaks on legacy pickles** (both models). Verified
  by pickling with unpatched code and loading with patched code: the object
  still has no `_name`, so the helper would raise inside the fix. Now
  `getattr(source, '_name', None)`, plus the `__setstate__` normalisation
  above — which is what actually closes #39 rather than half of it.
- **The `flags` freshness premise was false** (both models), and revision 2's
  claimed test did not assert it. Verified: `pd.Series.copy(deep=False)`
  returns an already-finalised baseTs, so the fallback target is not fresh.
  Plain assignment is kept, justified on the helper's contract instead, and
  the freshness claim is deleted rather than papered over.
- **The reflection guard was overclaimed** (both models). Corrected above:
  reflection derives membership, not arguments.
- **Carrying `flags` can raise where nothing raises today** (codex; verified
  and reproduced). `ts.data = x` on a length-1 series builds a duplicate
  index, and restoring `allows_duplicate_labels=False` onto it is refused.
  Handled by re-raising as a diagnosable `ValidationError`; the degenerate
  index generator behind it is filed separately.

One finding was dropped: that `_update_series_data`'s explicit `_metadata`
snapshot is redundant because those attributes live in the instance
`__dict__` and survive re-init anyway. True, but it is exactly the accident
this change replaces with a mechanism, so the snapshot stays and the
docstring says why.

## What review round 1 changed

A `consensus-review` panel round (codex ✓, agy ✓; no finding raised by both,
so everything was single-source and independently verified before acting).

**Accepted and folded in:**

- Sites 8 and 9 (`interpolate_gaps(inplace=True)`, `shift_time(inplace=True)`)
  were missing from revision 1's inventory entirely — and Half A cannot reach
  them, so revision 1 would have shipped claiming to close a bug class while
  leaving two reachable public methods exhibiting it.
- `_carry_identity(target, source)` is structurally wrong where
  `target is source`; Group 2 needs a pre-reinit snapshot.
- The census guard was closed over its own table and could not discover an
  unenumerated site. Now reflection-derived.
- The `flags` AND-vs-assignment difference between pandas majors.
- The structural alternative for Group 2 — collapse the re-init sites onto
  one primitive rather than add a call to each.

**Corrected:**

- The panel called sites 8 and 9 "two more sites" and credited
  `_update_series_data` with handling this. It saves and restores `_metadata`
  only, so it loses `name`/`attrs`/`flags` exactly like the other two, and
  `ts.data = x` reaches it. **Three** sites, not two.
- The panel's finding that `pickle.loads(data)` raises is not reproducible on
  either pandas major: `dumps` succeeds, `loads` succeeds, and the *returned
  object* raises on attribute access. Revision 1's own claim (that `dumps`
  raises) was also wrong. The corrected statement is above.

**Dropped:** the panel's own three dropped findings, including agy's
`_inplace_arith` claim, which it verified as incorrect.

## Review gate

`consensus-review` rounds until findings go trivial, every finding verified
against the `main` worktree before acting, then a **different** harness as the
merge gate rather than another round of the same panel — the pattern that
caught what converged panels missed on #20, #28 and #34.
