# Stamping `lowess_fit` and `outlier_indices` with the data they describe (#40)

Date: 2026-09-03
Issue: #40
Branch: `fix/lowess-fit-data-stamp`
Baseline: `main` @ `dbef680`, measured on pandas 3.0.1/numpy 2.5.2

Revision 1, before the `consensus-review` panel round. What that round
changes will be recorded in "What the review changed" at the end.

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
| `ts += 1.0` | yes | yes | **kept** | **kept** |
| `sg_filter()`, `detrend('linear')`, `lowpass_filter(1.0)`, `zscale()`, `apply_function(np.abs)` | yes | yes | **kept** | **kept** |
| `ts * 2.0`, `rolling(5).mean()` | yes | yes | **kept** | **kept** |
| `ts + 0.0`, `copy()`, `rolling(1).mean()`, `clip(-1, 1)` on data already inside that range, `fillna(0, inplace=True)` on data without NaN | no | yes | kept | kept |

Thirteen of the eighteen operations tried change the values and keep both
fields. The issue's table names four. The five that keep both *correctly*
are the ones whose values happen to come out equal, and they matter because
they are what separates "the data changed" from "a method was called": the
rule below must keep those five and drop the thirteen.

`ts.values[:] = 0` raises `ValueError: assignment destination is read-only`
on pandas 3.0 (copy-on-write), so that door is closed on 3.x by pandas
itself. It is open on pandas 2.x. Either way it is the shape of door #20's
lesson is about: a write to the block's own array passes through nothing
this package defines, so no write-side hook can see it.

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

The snapshot is stored as a `pd.Index` built from a copy of the values, and
the check is `stamped.equals(pd.Index(self.to_numpy()))`. Three reasons,
each measured on the throwaway spike that chose it:

- **It cannot be mutated.** `pd.Index` is immutable, so the snapshot cannot
  be written into by a later in-place operation and silently start agreeing
  with whatever the data became. A read-only numpy array was the
  alternative; its `writeable` flag does not survive pickling and
  `np.array_equal` raises on object dtypes.
- **Its equality is the right one.** `Index.equals` treats NaN as equal to
  NaN in the same position, so a series with gaps compares equal to itself;
  it compares values rather than dtypes, so `float32` against `float64` of
  the same numbers is equal, `1.0` against `1` is equal, and nullable
  `Float64` against `float64` with the NA in the same place is equal; and it
  handles object, complex, datetime and boolean values without raising.
  `Series.equals` is dtype-strict on all three of those; `np.array_equal`
  raises on object dtype and cannot see `pd.NA`.
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

A blob on disk holds two-element pairs. `__setstate__` completes each pair
into a triple by stamping it with the unpickled object's own values. That is
exactly what the setter would have recorded had it existed when the fit was
assigned, and the blob's data and fit were serialised together, so an object
comes back in the state it was pickled in: a fit that was valid then is valid
now, and a fit that was already stale under #40's defect stays exactly as
stale as it was. Dropping the pair instead would silently lose every fit in
every existing pickle to fix a defect most of them do not have.

The same door already heals `_name` for #39, so this is a second branch in a
method that exists for this purpose, not a new mechanism.

### Producers

No change to `filter_outliers`, `lowess_detrend` or the constructor. All
three assign the fit after the data, so the stamp records the data they
leave behind. `filter_outliers(qcplot=True)` assigns the fit onto a
pre-filter copy, so the QC plot's fit is stamped against the original
values it is drawn over - the one place the pairing is between a fit and
the very data it was computed from.

The copying discipline from #20 gains a second reason. Copying a slot
through the public name would re-stamp it with the receiving object's index
*and values*, laundering a stale fit on both axes. `_create_new_with_data`
and `_copy_metadata_from_basetseries` copy the private slots, and
`TestTheStampIsNotLaunderable` pins that.

### What is deliberately not done

- **No per-transform judgement.** `sg_filter`, `lowpass_filter` and the
  rest do not decide whether the parent's fit "still applies". They change
  the values, so the fit reads `None`, whatever the transform was. A rule
  that could be argued per method could not be checked.
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
  `lowess_fit` and `outlier_indices` as `None`.** The thirteen operations in
  the table, and any other. `filter_outliers(inplace=True)` followed by
  `interpolate_gaps(inplace=True)` on data that had pre-existing gaps loses
  both; on data without gaps the interpolation changes nothing and both
  survive. Code that reads either field after a further transform must read
  it before, or from the filtered object.
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
- **Pickles grow** by the snapshot, and pre-existing pickles load with
  their fits intact under the rule above.

## Testing

`tests/unit/test_data_stamp_invalidation.py`, new, mirrors the structure of
#20's file for the values axis:

- **The issue's reproduction** as written: `ts.data = noise` on an unchanged
  index reads both as `None`.
- **Every operation in the table**, parametrised, asserting the thirteen
  drop both and the five keep both. The five are the discriminating half:
  a rule that fired on "a method was called" would fail them.
- **Doors past every hook**: `ts.iloc[3] = x`, `ts[label] = x`,
  `ts.values[...] = x` where pandas allows it (skipped with a reason on
  copy-on-write), `fillna(inplace=True)` on data with gaps, `ts += 1`.
- **The pairing is what the producer left behind**: `filter_outliers` and
  `lowess_detrend` results, both `inplace` values, read a non-`None` fit,
  and `filter_outliers(qcplot=True)` draws the fit trace. Pins the ordering
  the issue was worried about.
- **The stamp is a copy**: mutating the object's values after stamping does
  not mutate the snapshot (`ts._lowess_fit[2]` still equals the original).
- **Reading is pure**: a stale read does not clear the slot; reading one
  field does not change the other; restoring the original values makes the
  fit readable again on the owning object.
- **Values equality semantics**: NaN-in-the-same-place equal; `float32`
  cast of exactly representable values equal; a one-sample change unequal;
  object and nullable dtypes do not raise.
- **Legacy pickles**: a blob built with two-element slots (constructed by
  hand, the way #39's test builds a `_name`-less blob) loads with the fit
  readable and the slot completed to a triple.
- **Laundering, on the values axis**: `_create_new_with_data` carries the
  parent's snapshot object verbatim (`is`), using `copy()` as the
  discriminating derivation - it has its own `Index` object and equal
  values, so it is the case that keeps the fit *and* proves nothing
  re-stamped it. `sg_filter` played that role in #20's test and cannot any
  more, because its result correctly reads `None`.

In `test_derived_lowess_invalidation.py`, eight tests pin the old rule
("values changed, index unchanged, both kept"). They are rewritten, not
deleted: each keeps its purpose - that the *index* rule does not fire on an
unchanged index - and does it with a values-preserving operation
(`+ 0.0`, `rolling(1).mean()`, `clip` inside the data's range, a
same-length assignment of equal values, `+= 0.0`), while its former
values-changing operation moves to the new file as a drop case.

Mutation testing on the getter and on `_drop_stale_positional_metadata`, as
on the previous two branches: delete the values check, invert it, compare
without copying, and confirm a test fails for each.

## Risk register

- **Version matrix.** `Index.equals` semantics for NaN, nullable NA and
  object dtype were measured on pandas 3.0.1 only. `array_equivalent`
  underlies it on both majors and has since 1.x, but the full suite must run
  on pandas 2.3.3 (numpy 1.26 and 2.x) as before, and the `ts.values[...]`
  door must be exercised there, where it is open.
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

To be written after the panel round.
