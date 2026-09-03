# Stamping `lowess_fit` and `outlier_indices` with the data they describe (#40)

Date: 2026-09-03
Issue: #40
Branch: `fix/lowess-fit-data-stamp`
Baseline: `main` @ `dbef680`, measured on pandas 3.0.1/numpy 2.5.2,
pandas 2.3.3/numpy 1.26.4 and pandas 2.3.3/numpy 2.2.6

Revision 2, after a `consensus-review` panel round (codex + agy). What that
round changed is recorded in "What the review changed" at the end.

## Problem

`lowess_fit` and `outlier_indices` are valid only for the samples they were
computed from. #20 made them read as `None` when the *index* changes, so a
slice, a `dropna` or a `sort_values` can no longer hand back a fit for
positions that moved. The complement is untouched: an operation that replaces
the *values* on an unchanged index carries the fit onto data it does not
describe, and nothing reads as stale. `qc_plot` then draws the old fit over
the new signal.

Measured on `main`, starting from a 200-sample filtered series that carries a
valid fit and one outlier position:

| operation | values changed | index unchanged | fit kept | indices kept |
|---|---|---|---|---|
| `ts.data = noise` | yes | yes | **kept** | **kept** |
| `ts.iloc[3] = 5.0`, `ts[label] = 9.0` | yes | yes | **kept** | **kept** |
| `ts.values[:] = 0` (pandas 2.x only; raises on 3.x) | yes | yes | **kept** | **kept** |
| `ts += 1.0` | yes | yes | **kept** | **kept** |
| `sg_filter()`, `detrend('linear')`, `lowpass_filter(1.0)`, `zscale()`, `apply_function(np.abs)` | yes | yes | **kept** | **kept** |
| `ts * 2.0`, `rolling(5).mean()` | yes | yes | **kept** | **kept** |
| `ts + 0.0`, `copy()`, `rolling(1).mean()` | no | yes | kept | kept |
| `clip(-1, 1)` on data already inside that range | no | yes | kept | kept |
| `fillna(0, inplace=True)`, `interpolate_gaps()`, `interpolate_gaps(inplace=True)` on data without NaN | no | yes | kept | kept |

Eighteen operations were tried on pandas 3.0.1. Eleven change the values and
keep both fields (the `ts.values[:]` row is a twelfth on pandas 2.3.3, where
that door is open). The issue's table names four. The seven that keep both
*correctly* are the ones whose values happen to come out equal, and they
matter because they are what separates "the data changed" from "a method was
called": the rule below must keep those seven and drop the eleven.

`ts.values[:] = 0` raises `ValueError: assignment destination is read-only`
on pandas 3.0 (copy-on-write), so that door is closed on 3.x by pandas
itself. **Measured open on pandas 2.3.3** with both numpy majors: the write
lands, the data reads back as all zeros, and the fit is still there. It is
the shape of door #20's lesson is about: a write to the block's own array
passes through nothing this package defines, so no write-side hook can see
it.

### Why this is a separate decision from #20, and what the issue left open

#20 invalidates on index change and is structural: every door that changes
the index changes `self.index`, and the getter reads `self.index`. The issue
deliberately left the data case out, for two reasons.

**Producers write data first and the fit second.** `filter_outliers` and
`lowess_detrend` both assign `.data` and then the fit. Any rule keyed on
"the data changed" makes that ordering load-bearing: a producer that set the
fit *before* the data would see it invalidated immediately. That is true of
this design too. What changes is the failure mode: with the rule in place a
mis-ordered producer hands back `None`, which its own test catches on the
first run, instead of a fit that looks fine and describes something else.
The tests in "Testing" pin both producers' ordering by asserting the fit is
readable on their results.

**Is the old fit *wrong*, or a record?** After `lowess_detrend`, the fit is
by construction the trend that was removed - it does not describe the
detrended values, and its docstring says so. The same is true, less
obviously, of `filter_outliers`: its fit was computed from the *unfiltered*
values, then the data is replaced by the filtered values. Neither producer's
fit "describes" the data it sits next to in the sense of being a fit *of*
it. What both fits do describe is the data *as the producer left it*: the
values that were on the object at the moment the fit was assigned, which is
the pairing `qc_plot` draws and the pairing a reader of `outlier_indices`
relies on. That is the definition this design uses, because it is the one
that can be checked mechanically. "Is this transform one whose result the
fit still usefully annotates" cannot be.

## Design

### The stamp gains a third element

The positional slot currently holds `(value, index_it_describes)`. It becomes
`(value, index_it_describes, values_it_describes)`, where the third element
is a **copy** of the object's values taken by the setter at assignment time.
The getter returns the value only while *both* the live index equals the
stamped index and the live values equal the stamped values.

This is the mechanism the `_positional_property` docstring already
anticipates ("stamping the data as well removes this wrinkle with it"), and
it is the same shape as `_freq_declaration` and the #20 index stamp: the
metadata carries the thing it was computed against, pandas copies the triple
verbatim like any other `_metadata` entry, and one getter re-checks it on
every read. No write-side hook, for the reason #20 established: there is no
bounded list of places a value can change. `ts.iloc[3] = 5` and
`ts[label] = 9` write into the block manager inside pandas' own indexer;
`ts.values[...] = x` on pandas 2.x writes into the array directly; neither
passes through anything this package defines. The getter reads the live
values, which every one of those doors changes.

### The comparison

Both sides go through `to_numpy()`. The snapshot is
`pd.Index(np.array(self.to_numpy(), copy=True))`, taken by the setter, and
the check is `stamped.equals(pd.Index(self.to_numpy()))`. Three reasons,
each measured on the throwaway spike that chose it, on pandas 3.0.1 and
re-measured on 2.3.3 with both numpy majors (identical results):

- **It cannot be mutated.** `pd.Index` is immutable, so the snapshot cannot
  be written into by a later in-place operation and silently start agreeing
  with whatever the data became. A read-only numpy array was the
  alternative; its `writeable` flag does not survive pickling.
- **Its equality is the right one.** `Index.equals` treats NaN as equal to
  NaN in the same position, so a series with gaps compares equal to itself;
  it compares values rather than dtypes, so `float32` against `float64` of
  the same numbers is equal and `1.0` against `1` is equal; and it handles
  object, complex, tz-aware datetime, boolean and empty values without
  raising. A nullable `Float64` series compares equal to its own snapshot
  because `to_numpy()` materialises both sides the same way (as an object
  array holding `pd.NA`, or a float array holding NaN, depending on the
  pandas version - the same on both sides either way). `Series.equals` is
  dtype-strict, so a `float32` cast would drop the fit; `np.array_equal`
  cannot compare arrays holding `pd.NA` (it raises `TypeError: boolean
  value of NA is ambiguous`).
- **Its cost is the cost of reading the value.** 0.5 ms per read on a
  million samples, 40 µs on two hundred. `Index.equals` on the index is
  already O(n) on a derived object's first read, and hashing the values
  instead was measured at 3-10x slower per read (a digest has to be
  recomputed from the live values on every read, because an in-place write
  leaves nothing cheaper to compare). There is no identity fast path for the
  data as there is for the index, and there cannot be: in-place writes keep
  the array's identity while changing its contents.

`-0.0` equals `0.0` under this comparison and a NaN with a different payload
equals a NaN. Both are values-equal, so both keep the fit, which is right: a
fit of `x` is a fit of `-0.0` where `x` was `0.0`.

The copy is shallow. For an object-dtype series holding mutable elements,
the snapshot and the live values share those elements, and mutating one in
place would leave the check passing. No baseTs series holds such values in
any documented use, and `Index.equals` on object dtype compares by `==`, so
this is noted rather than defended against.

### Order of checks

Index first, values second. The index check has an identity fast path after
the first successful read; the values check does not. An object whose index
changed fails the cheap check and never pays for the expensive one, and a
slice - the common case - fails on length before comparing anything.

### Eager release on derivation

`_drop_stale_positional_metadata`, which runs on every derivation, releases a
slot on a values mismatch as it already does on an index mismatch. It is
still memory, not correctness: without it `filtered.sg_filter()` would pin
the parent's full-length fit *and* its full-length snapshot for as long as
the result lived, with the getter reading `None` the whole time.

### Deep copy and detachment

`deepcopy_metadata_value` deep-copies the payload and carries the index and
the snapshot by reference, both immutable. `_detach_shared_metadata`, which
gives a derived object its own `outlier_indices` list, rebuilds the triple
rather than the pair. `copy(deep=True)` therefore costs one payload copy per
slot, as it does today; the snapshot is shared across every derived object
until one of them is assigned a new fit.

### Pickles written before this change

A blob on disk holds one of three shapes in each slot, and `__setstate__`
completes every one to the triple:

| written | slot holds | completion |
|---|---|---|
| before #20 | the bare fit array or positions list, or `None` | stamped against the unpickled object's index and values |
| #20 to now | `(value, index)` | index kept, stamped against the unpickled object's values |
| from now on | `(value, index, values)` | left alone |

The shape test is on type and length, not on length alone: a two-sample
bare fit array is not a pair. The pre-#20 shape is a pre-existing defect on
its own - the #20 getter unpacks the slot as a pair and raises on a bare
array - and is folded in because the same door and the same rule cover it.

What completion means, stated honestly: a legacy blob carries no evidence
of whether its fit still described its values when it was written. The
completion accepts the pairing the blob holds, so a fit that was stale
under #40's defect at pickling time reads as valid after unpickling, where
the same object kept in memory would read `None`. The alternative is to
drop every legacy fit to fix a defect most of them do not have. The rule
applies from the moment of unpickling: the next change to the values reads
`None` like any other.

The same door already heals `_name` for #39, so this is a second branch in
a method that exists for this purpose, not a new mechanism. The `_metadata`
shadow deletion runs first and the completion after, so both heals read the
class's registry.

### Producers

`filter_outliers` and the constructor assign the slots after the data, so
the stamp records the data they leave behind; neither changes.
`filter_outliers(qcplot=True)` assigns the fit onto a pre-filter copy, so
the QC plot's fit is stamped against the original values it is drawn over -
the one place the pairing is between a fit and the very data it was computed
from.

`lowess_detrend` changes in one line. Its docstring promises that
`outlier_indices` is "left alone: detrending is not filtering", and on
`main` the positions do survive it. Under the rule they would not: it
assigns new values and never re-touches the positions. So it re-asserts
them after assigning the data - a copy of the source's readable positions,
or `None` if the source had none - and its promise stays true. This is what
a producer is for: the rule decides what a *derivation* keeps, and a method
that knows the positions still describe its result says so by stamping
them. `is_outlier_filtered` needs nothing; it is a flag.

The copying discipline from #20 gains a second reason. Copying a slot
through the public name would re-stamp it with the receiving object's index
*and values*, laundering a stale fit on both axes. `_create_new_with_data`
and `_copy_metadata_from_basetseries` copy the private slots, and
`TestTheStampIsNotLaunderable` pins that.

### What is deliberately not done

- **No per-transform judgement on derivations.** `sg_filter`,
  `lowpass_filter` and the rest do not decide whether the parent's fit
  "still applies". They change the values, so the fit reads `None`, whatever
  the transform was. A rule that could be argued per method could not be
  checked. `lowess_detrend` is not an exception to this: it is a producer
  re-stamping a slot, which is the mechanism working, not a carve-out from
  it.
- **`outlier_indices` is not treated differently from `lowess_fit`.** One
  could argue the positions are a record of what was removed and survive a
  values change that the fit does not. Two mechanisms for two fields that
  #20 unified, whose docs say "reading one does not change the other", and
  whose release is joint, is a cost paid for a distinction the issue does
  not draw. A reader who wants the positions after a further transform
  reads them before it, or keeps the filtered object.
- **`is_outlier_filtered` is untouched.** It is a flag, not a description of
  samples, and it already survives everything.
- **`_freq_declaration` is untouched.** Its token is exactly what its
  derivation reads, and its derivation does not read the values.

## Behaviour changes

All are the rule doing what it says; none is incidental.

- **Every derivation that changes values on an unchanged index now reads
  `lowess_fit` and `outlier_indices` as `None`.** The eleven operations in
  the table, and any other. `filter_outliers(inplace=True)` followed by
  `interpolate_gaps(inplace=True)` on data that had pre-existing gaps loses
  both; on data without gaps the interpolation changes nothing and both
  survive. Code that reads either field after a further transform must read
  it before, or from the filtered object.
- **`lowess_detrend` keeps `outlier_indices`, as documented**, by
  re-stamping it. Its `lowess_fit` is the trend it removed, as before.
- **Restoring an index no longer resurrects a fit for different data.** The
  wrinkle `_positional_property`'s docstring records - a fit made readable
  again by putting the old index back after the values changed - is gone,
  because the values check fails independently.
- **Reads cost O(n) in the values on every read.** Previously O(n) in the
  index on the first read and O(1) after. Measured at 0.5 ms per million
  samples; the fit itself is a million floats.
- **Memory.** A stamped slot holds one extra copy of the values it was
  stamped against, shared by reference across derived objects. Comparable to
  the fit it validates, which is one float per sample.
- **`copy(deep=True)` is unchanged in cost.** The snapshot is shared, not
  copied.
- **Pickles grow** by the snapshot, and pre-existing pickles of every shape
  load with their fits readable under the completion rule above.

## Documentation

`docs/API_SERIES.md` lines 421-485 document the #20 rule and say that
scalar arithmetic, `sg_filter` and `rolling` keep both fields, which the
new rule reverses for the value-changing cases. That section is rewritten
around the triple; the two "consequences" bullets change (the index-revert
wrinkle is gone; the in-place-mutation limitation remains and now covers
values too). `_positional_property`'s docstring, the comment above the two
property definitions, `__finalize__`'s docstring and the `times` setter's
comment all say "pair" and are updated. `docs/CHANGELOG.md` gains an
Unreleased section naming the behaviour changes and the migration.

## Testing

`tests/unit/test_data_stamp_invalidation.py`, new, mirrors the structure of
#20's file for the values axis:

- **The issue's reproduction** as written: `ts.data = noise` on an unchanged
  index reads both as `None`.
- **Every operation in the table**, parametrised, asserting the eleven
  drop both and the seven keep both. The seven are the discriminating half:
  a rule that fired on "a method was called" would fail them.
- **Doors past every hook**: `ts.iloc[3] = x`, `ts[label] = x`,
  `ts.values[...] = x` where pandas allows it (skipped with a reason on
  copy-on-write), `fillna(inplace=True)` on data with gaps, `ts += 1`.
- **The pairing is what the producer left behind**: `filter_outliers` and
  `lowess_detrend` results, both `inplace` values, read a non-`None` fit;
  `lowess_detrend` on a filtered source keeps `outlier_indices` equal to the
  source's and not the same list; `filter_outliers(qcplot=True)` draws the
  fit trace. Pins the ordering the issue was worried about.
- **The stamp is a copy**: mutating the object's values after stamping does
  not mutate the snapshot (`ts._lowess_fit[2]` still equals the original).
- **Reading is pure**: a stale read does not clear the slot; reading one
  field does not change the other; restoring the original values makes the
  fit readable again on the owning object.
- **Values equality semantics**: NaN-in-the-same-place equal; `float32`
  cast of exactly representable values equal; a one-sample change unequal;
  object and nullable dtypes do not raise.
- **Legacy pickles, all three shapes**: blobs built by hand (the way #39's
  test builds a `_name`-less blob) with a bare array, a pair, and `None` in
  the slot load with the fit readable and the slot completed to a triple;
  a two-sample bare array is completed as a bare array, not unpacked as a
  pair.
- **Laundering, on the values axis**: `_create_new_with_data` carries the
  parent's snapshot object verbatim (`is`), using `copy()` as the
  discriminating derivation - it has its own `Index` object and equal
  values, so it is the case that keeps the fit *and* proves nothing
  re-stamped it. `sg_filter` played that role in #20's test and cannot any
  more, because its result correctly reads `None`.

In `test_derived_lowess_invalidation.py`, eleven tests pin the old rule
("values changed, index unchanged, both kept"), at lines 82, 101, 146, 343,
384, 417, 477, 525, 532, 565 and 576 on `main`. Three of them
(`test_appending_through_a_derived_object_leaves_the_parent_alone`,
`test_appending_through_a_create_new_with_data_result`,
`test_an_array_valued_outlier_record_is_detached_too`) would not fail an
assertion but raise, because they call `.append()` or index-assign on a
result that now reads `None`. All eleven are rewritten, not deleted: each
keeps its purpose - that the *index* rule does not fire on an unchanged
index, or that a surviving list is not shared - and does it with a
values-preserving operation (`+ 0.0`, `rolling(1).mean()`, `clip` inside
the data's range, a same-length assignment of equal values, `+= 0.0`,
`copy()`), while its former values-changing operation moves to the new file
as a drop case.

Mutation testing on the getter, on `_drop_stale_positional_metadata` and on
`__setstate__`'s completion, as on the previous two branches: delete the
values check, invert it, compare without copying, complete a pair without
the values, and confirm a test fails for each.

## Risk register

- **Version matrix - partly discharged.** `Index.equals` semantics for NaN,
  nullable NA, object, complex, tz-aware datetime, bool and empty values
  were measured identical on pandas 3.0.1, 2.3.3/numpy 1.26.4 and
  2.3.3/numpy 2.2.6, and the `ts.values[...]` door was measured open on
  both 2.3.3 environments. The full suite (1114 passed on all three at the
  branch baseline) must run on all three after implementation.
- **Read cost in tight loops.** A caller reading `lowess_fit` per iteration
  over a large series pays O(n) per read. No such loop exists in the package
  or its docs; `qc_plot` and `plot` read once. Noted in the CHANGELOG.
- **`to_numpy()` on extension arrays.** For a nullable-dtype series it
  materialises an object array per read. Correct and measured not to raise;
  slower than the numpy-backed path. baseTs series are float64 in every
  documented use.
- **A producer that sets the fit before the data.** None exists. If one is
  added, its own result test reads `None` on the first run.
- **The pickled `_metadata` shadow.** #39's heal deletes a stale instance
  registry; the slot completion here runs after that and reads the class's
  registry, so a legacy blob is healed on both counts in one pass.

## What the review changed

The panel (codex + agy) returned seven findings; all seven were verified
against `main` and all seven changed this document. None changed the
mechanism.

- **Both models: legacy pickles have three shapes.** Revision 1 completed
  "the pair" and never said what a pre-#20 blob holds, which is a bare
  array the #20 getter cannot even unpack. Now a table of all three shapes,
  a type-and-length test, and the pre-#20 shape folded in as pre-existing.
- **Both models: three of the affected tests raise rather than fail.**
  Revision 1 said the old-rule tests would be "rewritten"; it did not say
  that `.append()` on a `None` is an `AttributeError`. Named now.
- **codex: the "stays exactly as stale" claim was false.** Completing a
  legacy pair against the unpickled object's live values makes *every*
  legacy fit read valid, including one that was stale at pickling time.
  The decision stands - dropping every legacy fit is worse - but the text
  now says what the completion actually does and why.
- **codex: `lowess_detrend` promises to leave `outlier_indices` alone.**
  Revision 1 did not check that method against the rule; on `main` the
  positions survive detrending and the docstring says they must. It now
  re-stamps them after assigning the data, and the spec explains why that is
  the mechanism rather than an exception to it.
- **codex: the operation count did not match the table.** "Thirteen of
  eighteen" was wrong; the table now lists all eighteen and the counts are
  eleven and seven.
- **codex: the nullable `Float64` claim was wrong as written.**
  `pd.Index(Float64 array).equals(pd.Index(float64 array))` is `False`; the
  mechanism holds only because both sides go through `to_numpy()`, which
  the text now says. The `np.array_equal` claim was likewise narrowed to
  what was measured.
- **codex: eleven old-rule tests, not eight.** Three were missed on manual
  inspection (`rolling(5).mean()`, the same-length zeros assignment, the
  array-valued detachment test). Listed by line now.
- **codex, minor:** the `API_SERIES.md` rewrite was missing from the plan
  (now a section), and the shallow-copy caveat for object dtype is stated.
