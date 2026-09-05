# -*- coding: utf-8 -*-
"""
Pandas Series subclass for time series analysis.
Created for baseTs pandas migration.
@author: stan@sympaticog.com
"""

from __future__ import annotations
import datetime
from typing import Optional, Union, Any, Dict, List, Tuple
import copy as copy_module
import numpy as np
import pandas as pd
from numpy.typing import NDArray
# pandas' own index normaliser, so _set_axis sees exactly the Index pandas
# would build (a list of tuples stays an object Index there, where
# pd.Index() would make a MultiIndex). Present on pandas 2.2.3 and 3.0.1.
from pandas.core.indexes.base import ensure_index

from .LowessOutlierFilter import LowessOutlierFilter
from .utils import validate_sampling_freq


class _UnsetType:
    """The type of `_UNSET`. Distinct so it can be annotated and matched."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "<unset>"


#: "This keyword was not supplied", as opposed to "it was supplied and its
#: value happens to equal the default".
#:
#: The constructors copy a source object's metadata and then assign their own
#: keyword defaults over the top, which reset eleven of thirteen names on
#: every conversion (#57). Telling the two apart is what makes "assign only
#: what the caller actually passed" expressible: `False` and `""` cannot do
#: it, because they are also values a caller may legitimately mean.
#:
#: `None` cannot serve either. It is already a meaningful argument in places -
#: `baseTs(..., last_process=None)` is documented to produce `""` - so reusing
#: it here would make a supported call mean something new.
#:
#: `np.nan` serves the numeric arguments through `_is_unset`, and stays: it is
#: the constructor's *public* sentinel for `freq`, documented as such.
_UNSET = _UnsetType()


def _carries_metadata(data: Any) -> bool:
    """True if `data` is a source whose metadata a constructor should copy.

    Both constructors need the same answer: `TimeSeriesData.__init__` to know
    whether to copy, and `baseTs.__init__` to know whether an absent `history`
    means "nothing was carried across" or "the source's history is empty".
    Two spellings of the question drifted apart once already.

    A `TimeSeriesData` qualifies even though it has neither `.times` nor
    `.data` - those are baseTs' names, and gating on them alone meant
    converting a TimeSeriesData reset every one of its thirteen names.

    A plain `pd.Series` does not qualify: it carries no metadata to preserve,
    so the defaults are the right starting point for it.
    """
    if isinstance(data, TimeSeriesData):
        return True
    return hasattr(data, 'times') and hasattr(data, 'data')


#: The private slots behind the positional properties, paired with the public
#: names they back. Each holds either None or
#: `(value, index_it_describes, values_it_describes)`.
_POSITION_INDEXED_SLOTS = (('lowess_fit', '_lowess_fit'),
                           ('outlier_indices', '_outlier_indices'))


def _values_stamp(obj) -> pd.Index:
    """Snapshot `obj`'s values for a positional slot to be checked against.

    A `pd.Index` rather than an array, for two properties the check needs
    and an array does not give. It is immutable, so no later in-place write
    to the series can reach into the snapshot and make it agree with
    whatever the data became; a read-only ndarray's `writeable` flag does not
    survive a pickle round trip. And `Index.equals` is the right equality:
    NaN equals NaN in the same position, so a series with gaps compares equal
    to itself; values are compared rather than dtypes, so a `float32` cast of
    representable values still matches; and object, complex, tz-aware and
    boolean values compare without raising. `Series.equals` is dtype-strict
    and `np.array_equal` cannot compare arrays holding `pd.NA`.

    Built from an explicit copy, and that copy is load-bearing on pandas 2.x.
    `to_numpy()` hands back a view of the block's own array on both majors;
    `pd.Index` copies it on pandas 3.0 and aliases it on 2.3.3, so without
    the copy every in-place write on 2.x would land in the snapshot too and
    the check would pass on exactly the doors it exists to close. Measured:
    the mutant that drops the copy survives the suite on 3.0.1 and fails six
    tests on 2.3.3.

    Both sides go through `to_numpy()` - here and in _values_match - so an
    extension dtype is materialised the same way on both sides whatever that
    way is on the running pandas.

    Two limits on object dtype, noted rather than defended against because
    no baseTs series holds such values in any documented use: the copy is
    shallow, so a mutable element mutated in place leaves the check passing;
    and `Index.equals` treats `None` and `NaN` in the same position as equal,
    so swapping one for the other keeps the fit.
    """
    return pd.Index(np.array(obj.to_numpy(), copy=True))


def _values_match(obj, stamp: pd.Index) -> bool:
    """Whether `obj`'s live values are still the ones `stamp` recorded.

    O(n) on every call, and there is no fast path to add: an in-place write
    keeps the array's identity while changing its contents, so nothing
    cheaper than comparing the values can prove they are unchanged. Measured
    at 0.5 ms per million samples, alongside a fit that is itself a million
    floats.
    """
    return stamp.equals(pd.Index(obj.to_numpy()))


def _label_property(public: str, private: str, what: str) -> property:
    """Build a label attribute that is always a string.

    `signal_name` and `last_process` are read by every plot title, axis label
    and legend entry as `signal_name + " " + last_process`. #33 made them
    strings on every derivation path and through both constructors by
    normalising at the chokepoints, and pinned its own boundary: the object
    you *mutate* was not healed, so `ts.signal_name = None` stored `None`
    until the next derivation. That half is what let `lag_plot` fail on
    `.upper()` and fall back to a printed diagnostic and a placeholder label
    (#61). Coercing in the setter closes it the way #33's note said it
    would be closed - the `freq` / `lowess_fit` shape, validate where the
    value enters the object rather than guard every place it is read.

    The public name stays in `_metadata`, deliberately. pandas propagates
    those entries with `object.__setattr__`, which honours data descriptors,
    so `__finalize__`, `copy` and `__setstate__` all run this setter. For the
    positional slots that is laundering (#20); for a label it is the
    normalisation wanted, and it is what turns a legacy pickle carrying
    `None` under the public name into `""` on restore.

    The getter defaults to `""` rather than raising, because pandas can
    build a subclass instance without running `__init__` and finalize it
    later; and this class's own `copy()` loop reads each `_metadata` name
    through `hasattr` first, so a raising getter would silently skip the
    label there. It reads `__dict__` directly rather than `getattr`, because
    a miss in `getattr` falls through to NDFrame.__getattr__, which consults
    the block manager - and on an instance that has none yet (a `__new__`
    without `__init__`) that recursed instead of raising.

    `del ts.signal_name` returns the label to `""` rather than removing it:
    a plain attribute could be deleted and then raise on the next read,
    which is one more way for the label to stop being a string.
    """
    def getter(self):
        return self.__dict__.get(private, "")

    def setter(self, value):
        object.__setattr__(self, private, normalise_label(value))

    def deleter(self):
        self.__dict__.pop(private, None)

    return property(getter, setter, deleter,
                    doc=f"{what} Always a string; see normalise_label.")


def _positional_property(public: str, private: str, what: str) -> property:
    """
    Build a property that hands back `value` only while the index it was
    computed against is still the object's index and the values it was
    computed against are still the object's values.

    `lowess_fit` holds one float per sample and `outlier_indices` holds
    *positions* into that same sample sequence. Neither survives a change of
    index, and neither can be resliced in general: a positional slice has an
    obvious mapping, but resample, dropna and sort_values have none, so a
    reslicing implementation would be right on one path and silently wrong on
    every other.

    **Checked on read, not on write.** The write-side version of this rule
    needed a hook at every place an index can change, and there is no bounded
    list of those. Three review rounds took it from four hooks to seven and a
    fourth hole turned up immediately: `ts.loc[new] = v` and `ts.pop(label)`
    reach past `__finalize__`, `_update_inplace` and index assignment alike to
    swap the block manager directly, and `interpolate_gaps(inplace=True)` was
    one of three `pd.Series.__init__` call sites of which an explicit audit
    for that exact pattern still guarded only two. Reading `self.index` at
    access time cannot be bypassed, because every one of those doors changes
    `self.index` - which is the whole point of the redesign.

    This is the `freq` mechanism from #38 applied to a second kind of
    metadata, with one deliberate difference: `freq` compares a
    `(len, first, last)` token, because those are exactly the three inputs its
    derivation reads. That token is not enough here. An interior permutation
    leaves it untouched while moving every sample these two describe, so the
    check is full `Index.equals`.

    The stored index is a reference, not a copy: `pd.Index` is immutable and
    assignment rebinds rather than mutates, so there is nothing to copy.

    **Reading never destroys.** The getter is a pure function of the stored
    pair and the live index, so what one read returns does not depend on
    whether an earlier read happened. Clearing on a mismatch was tried and is
    worse: release then becomes per-attribute and observation-dependent -
    reading `lowess_fit` while stale would drop it while leaving
    `outlier_indices` recoverable, so an index reverted afterwards would bring
    back exactly the one nobody had looked at.

    **The values are checked too (#40).** The index test is positional: it
    says the samples are still where the fit says they are. It cannot see
    `ts.data = noise`, `ts.iloc[3] = 5`, `sg_filter()` or `ts * 2` - every
    one of which leaves the index alone and replaces what is at those
    positions, so the fit describes samples the object no longer holds and
    `qc_plot` draws it over a signal it was never fitted to. The slot
    therefore carries a third element, a snapshot of the values taken by the
    setter, and the getter compares the live values against it. Same
    argument as for the index: there is no bounded list of places a value
    can change (`ts.iloc[i] = v` writes inside pandas' indexer, and on
    pandas 2.x `ts.values[:] = 0` writes into the array itself), but every
    one of them changes what `to_numpy()` returns, and that is what is read.

    What "the values it describes" means is *the values that were on the
    object when the slot was assigned*. That is deliberately not "the
    values the fit was computed from" - `filter_outliers` computes its fit
    from the unfiltered data and assigns it after replacing the data, and
    `lowess_detrend`'s fit is the trend it removed. A producer writes the
    data first and the slot second, and the stamp records what it left
    behind. That ordering is load-bearing; a producer that stamped first
    would read `None` on its own result, which its test catches.

    Index first, values second: the index check has an identity fast path
    after the first read and fails cheaply on a length change, so an object
    whose index moved never pays for the values comparison.

    Reading does re-stamp with the index it just proved equal. That changes no
    answer - equality is transitive - and buys two things: later reads take
    `Index.equals`' identity fast path instead of an O(n) comparison, and the
    index the value arrived with is released. Both matter because every derived
    object gets a *new* `Index` instance, even from `copy(deep=False)`, so a
    derived object never hits the identity fast path on its first read however
    unchanged its index is. There is no equivalent for the values - see
    _values_match - so a valid read is O(n) every time.
    """

    def getter(self):
        stored = getattr(self, private, None)
        if stored is None:
            return None
        value, described_index, described_values = stored
        try:
            current = self.index
        except AttributeError:
            # Before the block manager exists there is no index to describe.
            return None
        if not current.equals(described_index):
            return None
        if not _values_match(self, described_values):
            return None
        if current is not described_index:
            object.__setattr__(self, private, (value, current, described_values))
        return value

    def setter(self, value):
        if value is None:
            object.__setattr__(self, private, None)
            return
        object.__setattr__(self, private, (value, self.index, _values_stamp(self)))

    getter.__name__ = public
    setter.__name__ = public
    return property(getter, setter, doc=f"{what} Valid only while the index "
                                        f"and the values it was assigned "
                                        f"against are still this object's; "
                                        f"reads as None otherwise (#20, #40).")


#: The private slot names alone, for callers that need to recognise them.
_POSITION_INDEXED_PRIVATE = tuple(private for _public, private in _POSITION_INDEXED_SLOTS)


def deepcopy_metadata_value(name: str, value: Any):
    """
    Deep-copy a `_metadata` entry, reaching inside a positional slot.

    Both `copy()` implementations deep-copy an entry only when it is a list,
    dict or ndarray. A positional slot is a `(value, index)` tuple, so that
    test silently stopped matching when the slots moved behind the properties,
    and `copy(deep=True)` began handing back the parent's own fit array - an
    aliasing bug on the one path whose whole purpose is to prevent it.

    Both stamps are carried over by reference rather than copied: each is a
    `pd.Index`, immutable, so there is nothing to isolate, and copying the
    index stamp would throw away the identity that lets a later read take
    the fast path. No test pins that - a deep-copied index is still
    `equals`-true, so the choice is memory and speed, not behaviour.
    """
    if name in _POSITION_INDEXED_PRIVATE:
        if value is None:
            return None
        payload, described_index, described_values = value
        return (copy_module.deepcopy(payload), described_index, described_values)
    if isinstance(value, (list, dict, np.ndarray)):
        return copy_module.deepcopy(value)
    return value


def _drop_stale_positional_metadata(obj):
    """
    Release a positional slot whose index or values no longer match.

    Runs on derivation only, from _detach_shared_metadata. Without it every
    slice of a filtered series would pin the parent's full-length fit for as
    long as the slice lived, whether or not anyone ever read it - and since
    #40, every `sg_filter()` result would pin the fit and the full-length
    values snapshot beside it.

    It *is* observable, and the rule it enforces is deliberate: a derived
    object whose index never matched is born without the value, so restoring
    an index later cannot hand it one it never had. That differs from the same
    revert on the object that owned the fit, where the value does come back -
    see _positional_property. The two halves are each defensible on their own
    terms, and neither depends on whether anyone read anything.

    The limitation this leaves: an object mutated *in place* to a different
    index or different values keeps the old value in its slot, unread, until
    it is overwritten or the object is collected. Closing that would need a
    hook at every point an index or a value can change, which is the design
    this replaced.

    _positional_property remains the correctness mechanism: this only decides
    when an unreadable value is released, never whether a readable one is.
    """
    for _public, private in _POSITION_INDEXED_SLOTS:
        stored = getattr(obj, private, None)
        if stored is None:
            continue
        _value, described_index, described_values = stored
        try:
            current = obj.index
        except AttributeError:
            continue
        if not current.equals(described_index) or not _values_match(obj, described_values):
            object.__setattr__(obj, private, None)
    return obj


def _complete_positional_slots(obj):
    """
    Bring a positional slot restored from a pickle up to the current shape.

    `__getstate__` writes the slot as it stood at dump time, so a blob on
    disk holds one of three shapes, and each is completed to the triple the
    getter unpacks:

    - written before #20: the bare fit array or positions list. Stamped
      against the unpickled object's own index and values. The #20 getter
      could not even unpack this shape, so it is a pre-existing break folded
      in here because the same door and the same rule cover it.
    - written between #20 and #40: `(value, index)`. The index is kept and
      the values are stamped from the unpickled object.
    - written since #40: `(value, index, values)`. Left alone.

    The test is on shape, not on length: a pair or a triple is a tuple whose
    second element is the `pd.Index` stamp. Nothing checks the third - no
    shape this code has ever written has an Index second and anything but
    one third, so a check there would be a branch no test can reach.
    Length alone misclassifies two legacy payloads - a two-sample bare fit
    array, and a bare *tuple* of positions such as `(3, 7)`, which the
    pre-#20 attribute accepted verbatim and which a length test would read
    as a pair whose "index" is `7`. Both are bare payloads and are stamped
    as such.

    What completing against the unpickled object's values means, stated
    plainly: a legacy blob carries no evidence of whether its fit still
    described its values when it was written, and this accepts the pairing
    the blob holds. A fit that was stale under #40's defect at pickling time
    reads as valid after unpickling, where the same object kept in memory
    would read None. The alternative - dropping every legacy fit to catch
    the few that were stale - loses more than it corrects. From the moment
    of unpickling the rule applies as it does to any other object: the next
    change to the values reads None.

    Runs after the `_metadata` shadow heal in __setstate__, so it iterates
    the class's registry, not a stale instance copy.
    """
    for _public, private in _POSITION_INDEXED_SLOTS:
        stored = getattr(obj, private, None)
        if stored is None:
            continue
        stamped = (isinstance(stored, tuple) and len(stored) in (2, 3)
                   and isinstance(stored[1], pd.Index))
        if stamped and len(stored) == 3:
            continue
        if stamped:
            value, described_index = stored[0], stored[1]
        else:
            value, described_index = stored, obj.index
        object.__setattr__(obj, private, (value, described_index, _values_stamp(obj)))
    return obj


#: The Series `name`, read and written by its private slot.
#:
#: Never `source.name`. `NDFrame.__getstate__` serialises
#: `{k: getattr(self, k, None) for k in self._metadata}` - the registry as it
#: stood when the blob was written - so an object unpickled from a blob
#: predating `_name`'s addition to `_metadata` has no such attribute, and the
#: property raises rather than returning None. Reading through the property
#: would make this helper raise on exactly the objects #39 is about.
_IDENTITY_NAME_SLOT = '_name'


def _carry_identity(target, source):
    """Copy the three identity fields pandas' own __finalize__ carries.

    `name`, `attrs` and `flags` are pandas', not baseTs'. `_metadata` covers
    the first only because pandas declares `_name` there; the other two are
    handled separately inside `__finalize__`, so any code that builds a new
    object and replays `_metadata` onto it carries none of them.

    This is that code's one door. It exists because six sites independently
    rebuilt an object and six times forgot the same fields - see
    `_adopt_data_inplace` for the self-mutating sites, which cannot use this
    helper because their target *is* their source.

    attrs is deep-copied under an emptiness guard, matching
    `NDFrame.__finalize__` exactly rather than approximating it: pandas
    deep-copies (so nested values are isolated, not shared) and skips the work
    when `attrs` is empty, which its own comment justifies as a 50x cost. An
    earlier revision of this helper copied shallowly and would have left two
    objects sharing one nested value while looking correct at the top level.

    `allows_duplicate_labels` is assigned, not AND-ed. pandas 2.x assigns and
    pandas 3.x ANDs with the target's existing value. Stated precisely, since
    an earlier version of this paragraph had the asymmetry backwards: the two
    differ only when the target is already restrictive and the source is
    permissive, where AND keeps the target's False and assignment takes the
    source's True. AND can never let a target override an explicit False - it
    is the other direction that differs. A derivation takes its source's
    declaration, so assignment is what this helper means; the divergence from
    pandas 3.x is deliberate and, because every target here is freshly built
    and therefore permissive, currently unobservable. It is also the one
    field that can refuse - see _apply_duplicate_label_declaration.
    """
    # Read through the public name with a default; write through the slot.
    # One `getattr` covers all three sources this sees, which a slot-only read
    # did not: a Series (`.name` returns `_name`), a duck-typed source that
    # `_copy_metadata_from_basetseries` accepts on `.times`/`.data` alone and
    # which may carry `.name` and no slot - silently dropped before - and an
    # object unpickled from a pre-fix blob, whose property raises
    # AttributeError from inside, exactly what the default swallows. A
    # slot-first version with a `hasattr` guard behaved identically and had a
    # dead branch, which is how mutation testing found it.
    #
    # The *write* stays on the slot: `Series.name`'s setter validates
    # hashability, so assigning through it would raise here rather than at the
    # origin for a name that predates the rule (#20's invariant).
    object.__setattr__(target, _IDENTITY_NAME_SLOT,
                       getattr(source, 'name', None))

    source_attrs = getattr(source, 'attrs', None)
    if source_attrs:
        target.attrs = copy_module.deepcopy(source_attrs)

    # Both getattrs are load-bearing, and for the same reason the name is
    # read by slot: a source here is not always an NDFrame.
    # `_copy_metadata_from_basetseries` accepts anything with `.times` and
    # `.data`, so a duck-typed source has no `flags` at all and reading
    # `source.flags` raised AttributeError on a call that works on `main`.
    # A source that declares nothing declares the permissive default.
    declared = getattr(getattr(source, 'flags', None),
                       'allows_duplicate_labels', True)
    if declared is not target.flags.allows_duplicate_labels:
        _apply_duplicate_label_declaration(target, declared)
    return target


def _refuse_undeclarable_index(declared, index):
    """Reject an index the declaration could not survive, before anything moves.

    Called *before* a re-initialisation commits, not after. Setting
    `allows_duplicate_labels = False` is a validation pandas performs against
    the live index, so restoring a declaration afterwards can fail - and by
    then the new data and index are already in place and the flag has been
    reset to pandas' permissive default. The object was left mutated, with
    the protection it declared silently switched off, by an operation that
    had just reported failure. A caller catching the error has every reason
    to assume nothing changed.

    Checking the prospective index first makes the operation atomic: either
    it raises having touched nothing, or the duplicate-label restore that
    follows cannot fail.

    **Returns the index it checked, and the caller must use that object.**
    Building a `pd.Index` from a one-shot iterable drains it, so a version
    that checked one object and let the caller re-use the original turned a
    working call into `Length of values (3) does not match length of index
    (0)` for any generator index. Materialising once and handing the result
    back means there is exactly one candidate index, never two - the same
    unpack-once rule that a band-edge generator forced on `plot_fft_power`.
    Unconditional, not only on the falsy branch, so the two branches cannot
    hand back different types.
    """
    candidate = index if isinstance(index, pd.Index) else pd.Index(index)
    if not declared and candidate.has_duplicates:
        _raise_duplicate_label_refusal(candidate)
    return candidate


#: How many duplicated labels an error message names before summarising.
_DUPLICATE_LABELS_SHOWN = 5


def _raise_duplicate_label_refusal(index, cause=None):
    """The one wording for both the pre-check and the restore arm.

    The labels are sampled rather than pasted whole. `{duplicated!r}` on the
    full list built an 889,108-character exception from an index of 100,000
    duplicated pairs - the same defect `utils._describe` exists to prevent,
    where a 200k-element list produced a 1.4 MB message that then lands in
    logs and tracebacks. A handful of labels and a count identify the
    mistake; the rest is payload.

    The remedy it names has to be one the reader can actually carry out. An
    earlier wording offered "give the result a unique index", which is not
    available on any path that raises this: `ts.data = ...`,
    `interpolate_gaps` and `shift_time` all *derive* the result's index, and
    none of them takes one from the caller. Clearing the declaration is the
    action that exists, so that is what is offered - and the derived index is
    named as the thing to look at rather than as something to replace.
    """
    from .utils import ValidationError, _describe

    duplicated = index[index.duplicated()].unique().tolist()
    shown = _describe(duplicated[:_DUPLICATE_LABELS_SHOWN])
    if len(duplicated) > _DUPLICATE_LABELS_SHOWN:
        shown += f" and {len(duplicated) - _DUPLICATE_LABELS_SHOWN} more"
    error = ValidationError(
        "this series declares allows_duplicate_labels=False, but the "
        f"operation derived an index with duplicate time labels {shown}, so "
        "that declaration cannot be carried to the result. Clear it with "
        "`ts.flags.allows_duplicate_labels = True` to allow the result, or "
        "avoid the operation that produced the repeated timestamps."
    )
    raise error from cause


def _apply_duplicate_label_declaration(target, declared):
    """Carry `allows_duplicate_labels`, diagnosing pandas' refusal.

    Setting the flag to False is a validation, not a note: pandas checks the
    index there and then. So an operation that produced duplicate labels on
    an object whose owner declared it would have none fails *here*, at the
    moment the declaration is restored, with a message that says only "Index
    has duplicates" and names neither the object nor the declaration.

    Carrying the flag anyway is deliberate. Silently dropping a declaration
    the caller made is the class of failure this whole change exists to fix,
    and a derived object that quietly permits what its parent forbade is
    worse than a loud one. What is added is the diagnosis.

    **Not reachable through the re-initialisation path any more**, and the
    docstring said otherwise until a review pointed at the contradiction.
    `_refuse_undeclarable_index` now rejects a duplicate-bearing index before
    `_adopt_data_inplace` commits anything, with this same wording, so a
    derived duplicate index raises there and never arrives here. (The case
    that used to illustrate this, `ts.data = [1., 2., 3.]` on a single-sample
    series, no longer derives a duplicated index at all: since #65 the setter
    refuses it earlier, for having no span.) What can still reach this arm is
    `_carry_identity`, which
    has no pre-check because its target takes its source's index. The arm is
    kept and unit-tested directly rather than deleted on that reasoning.
    """
    from pandas.errors import DuplicateLabelError

    try:
        target.flags.allows_duplicate_labels = declared
    except DuplicateLabelError as exc:
        # Caught by class. An earlier version matched `type(exc).__name__` and
        # justified it by saying an import would itself become a version
        # dependency - which is false: pandas has exported this from
        # `pandas.errors` since 1.2, well below this project's `pandas>=2.0.0`
        # floor, and it is importable on both majors the CI matrix covers.
        _raise_duplicate_label_refusal(target.index, cause=exc)


def _detach_shared_metadata(obj):
    """
    Give `obj` its own `history` list and its own `outlier_indices` list.

    pandas' default __finalize__ assigns metadata by reference, so a derived
    object would append to the list it inherited - one history for two series.

    `outlier_filter` needs no copy: FilterConfig is frozen and
    set_outlier_filter rebinds the filter rather than mutating it, so sharing
    one is safe by construction.

    `outlier_indices` gets a fresh list because it is neither frozen nor
    rebound-only: it is a plain list, and appending or sorting through any
    object that shares it rewrites the outlier record of every other. Its cost
    is O(number of outliers), not O(number of samples), so copying it on every
    derivation is cheap. `lowess_fit` is left shared: it is one float per
    sample, nothing in the library writes into it, and copying it here would
    turn an O(1) slice into an O(n) walk of the parent's metadata. Whether
    either is still *readable* is decided by _positional_property on access,
    not here; this only stops two objects sharing one mutable list.

    A history that is not a list is normalised rather than left alone. pandas
    propagates metadata from whichever operand carries it, so an operand
    without a history hands None to the derived object; normalising here makes
    "history is always a list" hold for every consumer, instead of asking each
    of the nine call sites that touch it to guard for itself.

    Any non-list history is coerced, not just None: a str, tuple or ndarray is
    just as fatal to .append(). See normalise_history for the coercion rules.

    A `None` outlier_filter is replaced by a default on the same argument, and
    only when it is None - restoring a default is not the same as imposing one,
    and a configured filter must reach the derived object untouched. pandas
    copies whatever the parent holds, so an object that reached this state (see
    _copy_metadata_from_basetseries, or a caller who cleared the attribute)
    handed the None to every object derived from it, where `.config` is read
    unguarded by get_outlier_filter_params, info and filter_outliers alike.

    `signal_name` and `last_process` used to be coerced here too, for the
    same reason: plotting builds every title, axis label and legend entry
    with `signal_name + " " + last_process`. Since #61 they are normalising
    properties, so every assignment - this one included - already coerces,
    and an arm here would be redundant with the setter. See _label_property.
    """
    object.__setattr__(obj, 'history', normalise_history(getattr(obj, 'history', None)))
    if getattr(obj, 'outlier_filter', None) is None:
        object.__setattr__(obj, 'outlier_filter', LowessOutlierFilter())
    stored = getattr(obj, '_outlier_indices', None)
    if stored is not None and isinstance(stored[0], (list, np.ndarray)):
        # ndarray as well as list: the constructor types this parameter as
        # np.array, so a list-only check leaves the documented isolation
        # depending on which shape a caller happened to supply. Either way the
        # cost is the number of outliers, not the number of samples.
        object.__setattr__(obj, '_outlier_indices',
                           (copy_module.copy(stored[0]),) + tuple(stored[1:]))
    return _drop_stale_positional_metadata(obj)


def normalise_history(history: Any) -> list:
    """Coerce any history value to a fresh list.

    The single definition of the "history is always a list" invariant, so the
    __finalize__ path, _create_new_with_data, the constructor kwarg and
    _update_history_and_process cannot drift apart. Always returns a new list,
    never the caller's own object: two series built from one list would
    otherwise cross-contaminate each other's history.

    Only genuine sequences are iterated. Anything else is wrapped as a single
    entry, because iterating it loses data silently where the old
    AttributeError was at least loud:

      - str/bytes: list('note') gives four single-character entries
      - Mapping:   list({'a': 'x'}) gives ['a'] and drops every value
      - set:       order varies with PYTHONHASHSEED
      - iterator:  consumed by the first derivation, empty for every later one

    Wrapping preserves the value so nothing is lost, and the result is still a
    list, so .append() works and the invariant holds.
    """
    if history is None:
        return []
    if isinstance(history, list):
        return list(history)
    if isinstance(history, (tuple, np.ndarray, pd.Series, pd.Index)):
        return list(history)
    # Deliberately not a bare `list(history)` fallback - see the docstring.
    return [history]


def normalise_label(value: Any) -> str:
    """Coerce a label attribute (`signal_name`, `last_process`) to a string.

    The single definition of "the label metadata is always a string", so the
    __finalize__ path and _copy_metadata_from_basetseries cannot drift apart.

    None becomes the empty string, which is what both attributes are born with
    and what every consumer already handles. Anything else is stringified
    rather than blanked: a caller who set a number meant it to appear on the
    plot, and `str(12)` keeps it there where `""` would silently lose it.

    Unlike normalise_history there is no shared-mutable problem to solve here -
    strings are immutable, so this is about type, not about isolation.
    """
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return str(value)


#: Nanoseconds per second, as the int64 the stamp arithmetic below works in.
_NS_PER_SECOND = 1_000_000_000


def _holds_calendar_datetimes(index: pd.Index) -> bool:
    """True if every element of an object index is a calendar datetime.

    The rule is by element type, not by parsing: `datetime.date` and its
    subclasses (`datetime`, `Timestamp`, NaT) and `numpy.datetime64`
    count; a missing value (None, NaN, NaT) is allowed among them; a string
    is not a datetime however it reads, so a text index stays text. An
    index with no datetime in it at all is not one either.
    """
    seen_stamp = False
    for element in index:
        if isinstance(element, (datetime.date, np.datetime64)):
            seen_stamp = seen_stamp or not pd.isna(element)
        elif element is None or (isinstance(element, float) and np.isnan(element)):
            continue
        else:
            return False
    return seen_stamp


def _seconds_since_origin(index: pd.Index) -> Optional[Tuple[pd.Index, Optional[float]]]:
    """Turn a stamped index into the seconds the package reads (#100).

    The package keeps one time base - a float index of seconds - and this is
    where a calendar index joins it. A `DatetimeIndex` becomes seconds since
    its *first* stamp (not its earliest: the numeric path keeps an unsorted
    index as given, and so does this one), and that stamp is the origin,
    returned as epoch seconds. A `TimedeltaIndex` is already durations and
    becomes its own seconds, with no origin. Anything else returns None and
    is left alone, which is what keeps the numeric path untouched.

    A timezone-aware index is an instant, and epoch seconds identify an
    instant exactly, so it converts like a naive one read as UTC; the zone
    name is kept nowhere. `datetimes` gives naive UTC back.

    An empty index has no first stamp and therefore no origin. A NaT
    *first* stamp is refused: every second would be NaN and the origin NaN
    with it, a pair nothing downstream can read. An interior NaT becomes a
    NaN second, which is what the numeric index admits already.

    An object index whose elements are all calendar datetimes - `Timestamp`
    or `datetime` objects pandas could not unify into one DatetimeIndex
    because they carry different zones, or plain `datetime.date` objects -
    is a stamped index too, and goes through `pd.to_datetime(utc=True)`,
    which reads each element as the instant it names (a naive one as UTC,
    a date as its midnight) and lands in the DatetimeIndex arm. Left alone,
    such an index sat as raw objects in a float slot, `times` returned
    Timestamps and nothing raised (review round 1, both panelists).

    Returns:
        `(seconds, origin)` - a float64 Index and the origin in epoch
        seconds, None when the index carries no origin - or None when the
        index is not a stamped one.
    """
    if index.dtype == object and _holds_calendar_datetimes(index):
        index = pd.to_datetime(index, utc=True)
    if isinstance(index, pd.DatetimeIndex):
        if len(index) == 0:
            return pd.Index(np.array([], dtype=float), name=index.name), None
        first = index[0]
        if pd.isna(first):
            raise ValueError(
                "cannot convert this DatetimeIndex to seconds: its first "
                "stamp is NaT, and the first stamp is the origin the seconds "
                "are counted from. Drop or fill it first.")
        seconds = np.asarray((index - first).total_seconds(), dtype=float)
        return pd.Index(seconds, name=index.name), first.value / _NS_PER_SECOND
    if isinstance(index, pd.TimedeltaIndex):
        seconds = np.asarray(index.total_seconds(), dtype=float)
        return pd.Index(seconds, name=index.name), None
    return None


#: Below this many seconds a float64 second still resolves nanoseconds:
#: its ulp is under 1e-9, so the stored value is within half a nanosecond
#: of the true one and rounds back to it. At 2**23 s the ulp becomes
#: 1.86e-9 and microseconds are what the float can vouch for. 2**23 s is
#: 97 days. (A first cut said 2**22, where the ulp merely passes half a
#: nanosecond - one octave early; the glm review round caught the
#: arithmetic and a 1000-consecutive-nanosecond sweep per octave
#: confirmed it: 0 mismatches at 97 days, 463 at 97.1.)
_NANOSECOND_EXACT_BELOW = 2.0 ** 23

#: Seconds whose nanosecond count no longer fits int64: pandas stamps are
#: int64 nanoseconds, so nothing this far from the origin is a stamp.
_STAMP_RANGE_SECONDS = 2.0 ** 63 / 1_000_000_000


def _origin_timestamp(ts_offset: float) -> pd.Timestamp:
    """The origin `ts_offset` names, rebuilt at microsecond resolution.

    A float64 epoch in the 2020s resolves to about 2.4e-7 s, so the
    nanosecond digits of a finer origin were never in the float; rounding
    to the microsecond recovers exactly any origin that lies on one, which
    is every `date_range` start and every stamp at microsecond resolution
    or coarser. A nanosecond origin comes back within half a microsecond.
    The rounding is sound while the float's ulp is under 1e-6, i.e. for
    any origin before 2**33 s - the year 2242.
    """
    return pd.Timestamp(int(round(float(ts_offset) * 1_000_000)), unit='us')


def _stamps_from_seconds(origin: pd.Timestamp, seconds: Any) -> pd.DatetimeIndex:
    """origin + seconds, as a DatetimeIndex, at the precision the float holds.

    A float64 second resolves nanoseconds only below 2**23 s from the
    origin (97 days; its ulp passes 1e-9 there) and microseconds below
    2**33 s (272 years). Each second is therefore rebuilt at the finer of
    those its magnitude allows: split into whole and fraction (the whole
    part is an exact integer; the fraction is below 1 and its product with
    1e9 is within 1.2e-7 ns of exact, which the rounding absorbs -
    `round(seconds * 1e9)` on the whole value loses nanoseconds past
    2**53), then the nanoseconds are rounded to the microsecond beyond
    2**23 s. The rule, measured over a census in
    test_datetime_index_converts_at_the_constructor.py: every stamp at
    microsecond resolution or coarser round-trips exactly at any span, and
    a nanosecond stamp does so within 97 days of the origin and comes
    back rounded to the microsecond beyond that. (Rounding always to the
    nanosecond, an earlier cut, put a microsecond stamp 200 days out 2 ns
    off; the digits were not in the float.)

    A second more than 2**63 ns (292 years) from the origin is refused
    with OverflowError rather than wrapped: the int64 product wrapped
    silently and 9.5e9 s came back as a date in 1686. pandas raises the
    same OverflowError itself when origin + seconds leaves its 1677-2262
    stamp range, so both limits surface the same way.

    The split is `trunc`, not `floor`: for a negative second `x - trunc(x)`
    is exact (Sterbenz - the two are within a factor of two, or trunc is
    zero), while `x - floor(x)` subtracts a value up to twice x and can
    round. Measured: a second of -1.0000000005, whose exact nanosecond
    count is -1000000000.50000004, came back -1000000001 through trunc and
    -1000000000 through floor. Only a numeric index can hold such a second
    (a stamp is already whole nanoseconds), and the pin uses one.

    A NaN or infinite second becomes NaT, as the datetime64 NaT sentinel
    (int64 min) in the view below.
    """
    secs = np.asarray(seconds, dtype=float)
    ns = np.full(secs.shape, np.iinfo(np.int64).min, dtype=np.int64)
    finite = np.isfinite(secs)
    kept = secs[finite]
    if np.any(np.abs(kept) >= _STAMP_RANGE_SECONDS):
        worst = kept[np.argmax(np.abs(kept))]
        raise OverflowError(
            f"cannot place a second {worst!r} from the origin on the calendar: "
            "pandas stamps are int64 nanoseconds, which span 292 years either "
            "side of the origin.")
    whole = np.trunc(kept)
    frac_ns = np.round((kept - whole) * _NS_PER_SECOND)
    beyond = np.abs(kept) >= _NANOSECOND_EXACT_BELOW
    frac_ns[beyond] = np.round(frac_ns[beyond] / 1000.0) * 1000.0
    ns[finite] = whole.astype(np.int64) * _NS_PER_SECOND + frac_ns.astype(np.int64)
    return origin + pd.TimedeltaIndex(ns.view('timedelta64[ns]'))


def _freq_token(index: Any) -> tuple:
    """Fingerprint an index for the purpose of sampling-rate derivation.

    Deliberately exactly the three values _calculate_effective_frequency
    reads - length, first timestamp, last timestamp - and nothing else. That
    is what makes the token trustworthy rather than merely convenient: two
    equal tokens guarantee that re-deriving the rate right now would return
    the number it returned when the token was taken, so a declaration stamped
    against it is as valid as it was on the day it was made.

    It follows that the token is blind to interior reordering. That is
    correct, not a gap - the derivation is blind to it too, and an index
    permutation that leaves length and endpoints alone leaves the mean rate
    alone. It does NOT mean the grid is still uniform; nothing in this class
    has ever claimed that.

    Args:
        index: Any pandas Index or sequence supporting len() and [] access

    Returns:
        A tuple safe to compare with ==; (0,) for an empty index
    """
    n = len(index)
    if n == 0:
        return (0,)
    return (n, index[0], index[-1])


class _FinalizingWindow:
    """
    Wraps a pandas window object (Rolling/Expanding/ExponentialMovingWindow)
    so its aggregations propagate metadata.

    rolling()/expanding()/ewm() build their result via the parent's
    `_constructor` directly and never call `__finalize__` - the type survives
    but history, outlier_filter and everything else in `_metadata` resets to
    constructor defaults. The window object holds the parent as `.obj`; this
    finalizes each aggregation result against it, mirroring what pandas does
    for every other operation.
    """

    def __init__(self, window: Any, parent: "TimeSeriesData", method: str) -> None:
        object.__setattr__(self, '_window', window)
        object.__setattr__(self, '_parent', parent)
        object.__setattr__(self, '_method', method)

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._window, name)
        if not callable(attr):
            return attr

        def finalizing_call(*args, **kwargs):
            result = attr(*args, **kwargs)
            if isinstance(result, pd.Series):
                result = result.__finalize__(self._parent, method=self._method)
            return result

        return finalizing_call

    def __iter__(self):
        """
        Python looks up dunder methods on the type, bypassing __getattr__,
        so this needs an explicit override. The underlying window's own
        iteration already yields correctly-finalized baseTs objects (pandas
        builds each one via the parent's _constructor then __finalize__(s)
        it against the parent internally) - delegate rather than re-wrap.
        """
        return iter(self._window)

    def __repr__(self) -> str:
        return f"_FinalizingWindow({self._window!r})"


class TimeSeriesData(pd.Series):
    """
    Pandas Series subclass optimized for time series analysis.
    
    This class extends pandas Series to provide time-series specific functionality
    while maintaining compatibility with the existing baseTs API.
    
    Attributes:
        freq: Sampling frequency in Hz
        signal_name: Name of the signal
        history: Processing history list
        is_filtered: Whether the data has been filtered
        is_interpolated: Whether at least one value is an interpolated
            estimate rather than a measured sample: set by the regridders,
            by a gap fill that filled a gap, and by filter_outliers when it
            replaced an outlier or filled an input gap; never reset (#90)
        is_uniform_grid: Whether the data is on a uniform time grid
        ts_offset: Timestamp offset in seconds
        has_timestamp_offset: Whether a timestamp offset has been applied
        outlier_indices: Indices of detected outliers
        lowess_fit: LOWESS fit data for outlier filtering
        last_process: Last processing operation performed
    """
    
    # Every attribute pandas should carry across an operation. Anything missing
    # here is silently dropped by slicing, rolling, dropna, etc.
    #
    # 'filtered_indices' used to be listed here but was only ever initialised to
    # None and never written by anything - a half-finished rename. The attribute
    # that actually holds outlier positions is 'outlier_indices', which was
    # absent, so `ts.iloc[:50].outlier_indices` raised AttributeError.
    #
    # '_freq_declaration' replaces 'freq'. What propagates is the declaration
    # plus the index token it was made against, not the rate - so pandas'
    # __finalize__ copying it verbatim is now correct, because the child
    # re-validates it against its own index. Listing the property here instead
    # would be actively wrong: __finalize__ copies with object.__setattr__,
    # which honours data descriptors, so every propagation would run the
    # validating setter.
    #
    # Composed from `pd.Series._metadata` rather than beginning at
    # '_freq_declaration'. This list *replaced* pandas' own, which is
    # ['_name'], so the Series name was carried by nothing: every
    # __finalize__ path dropped it, and __getstate__ - which serialises
    # exactly this registry - never wrote it, leaving unpickled objects
    # without a `_name` attribute at all (#39). Extending rather than
    # hardcoding '_name' keeps a future pandas that declares a second name
    # working, since hardcoding a list pandas owns is the original mistake.
    _metadata = pd.Series._metadata + [
        '_freq_declaration', 'signal_name', 'history', 'is_filtered',
        'is_interpolated', 'is_uniform_grid', 'ts_offset',
        'has_timestamp_offset', '_outlier_indices', '_lowess_fit',
        'last_process', 'is_outlier_filtered', 'outlier_filter',
    ]

    def __setstate__(self, state):
        """Restore from a pickle, healing a blob that predates `_name`.

        Adding '_name' to `_metadata` fixes objects pickled from now on, and
        nothing else: `__getstate__` wrote the registry as it stood at dump
        time, so a blob written before this change carries no `_name` key and
        pandas' restore loop has nothing to set it from. The object would
        come back missing the attribute and raise on `.name`, `repr()`,
        `iloc` and arithmetic - which is #39's symptom, unfixed, for every
        pickle already on disk.

        Normalising here rather than guarding each reader is the same move
        _detach_shared_metadata makes for `history` and `outlier_filter`,
        applied to the one door that rebuilds an object out of bytes.

        The registry shadow has to go first, and healing `_name` without it
        was worse than not healing at all. pandas writes `_metadata` into the
        pickle and its `__setstate__` installs whatever it finds as an
        *instance* attribute, permanently shadowing the class's. Every pickle
        gets that shadow; for one written since this change it is identical to
        the class list and harmless, but a legacy blob carries the old,
        `_name`-less registry - so the object would come back healed, work
        once, and then lose the name again the moment anything iterated
        `self._metadata`: `__getstate__` on the next pickle, or
        `_adopt_data_inplace`'s snapshot on the next `ts.data = x`. Deleting
        the shadow lets the class attribute govern, which is where the
        registry is actually defined.
        """
        super().__setstate__(state)
        # Dropped only when it is *stale*, not whenever it exists. Deleting
        # unconditionally also discarded a registry someone had deliberately
        # extended on one instance - the extra names' values survived, but
        # nothing tracked them afterwards, so they were silently dropped from
        # every later derivation. A shadow that still covers everything the
        # class declares is not the legacy case and is left alone.
        shadow = self.__dict__.get('_metadata')
        if shadow is not None and not set(type(self)._metadata) <= set(shadow):
            object.__delattr__(self, '_metadata')
        if not hasattr(self, _IDENTITY_NAME_SLOT):
            object.__setattr__(self, _IDENTITY_NAME_SLOT, None)
        _complete_positional_slots(self)

    # What propagates is the (value, index, values) triple, not the bare
    # value - so pandas copying it verbatim is correct, because the child
    # re-checks it against its own index and values on read. Listing the
    # public names here instead
    # would be actively wrong for the same reason it is wrong for `freq`:
    # __finalize__ copies with object.__setattr__, which honours data
    # descriptors, so every propagation would run the stamping setter and
    # re-stamp the parent's fit with the child's index - laundering exactly
    # the staleness this exists to catch.
    lowess_fit = _positional_property(
        'lowess_fit', '_lowess_fit',
        "LOWESS fit produced by filter_outliers or lowess_detrend, one value "
        "per sample.")
    signal_name = _label_property(
        'signal_name', '_signal_name', "Name of the signal.")
    last_process = _label_property(
        'last_process', '_last_process',
        "Name of the last processing step applied.")
    outlier_indices = _positional_property(
        'outlier_indices', '_outlier_indices',
        "Positions of the samples filter_outliers rejected.")

    def __init__(self, data=None, index=None, freq: Optional[float] = None,
                 signal_name: Union[str, _UnsetType] = _UNSET,
                 ts_offset: Union[float, _UnsetType] = _UNSET,
                 has_timestamp_offset: Union[bool, _UnsetType] = _UNSET,
                 **kwargs):
        """
        Initialize TimeSeriesData object.

        A `DatetimeIndex` or `TimedeltaIndex` - however spelled: an Index, a
        datetime64 array, a list of Timestamps, or the index of a Series
        passed as `data` - is converted here to the float seconds every
        method reads (#100). See _seconds_since_origin for the rule.

        Args:
            data: Array-like data or baseTs object
            index: Time index values (if data is array-like)
            freq: Sampling frequency in Hz
            signal_name: Name of the signal
            ts_offset: The origin the index's seconds are counted from, in
                epoch seconds. A DatetimeIndex carries its own origin (its
                first stamp) and refuses a second one.
            has_timestamp_offset: Whether an origin applies. False alongside
                a DatetimeIndex keeps the seconds and drops the origin.
            **kwargs: Additional Series initialization parameters
        """
        # Handle different input formats
        if _carries_metadata(data):
            # Conversion from something that already holds metadata. `.times`
            # and `.data` are baseTs' spelling; a TimeSeriesData has neither,
            # so gating on them alone sent the superclass down the plain-pandas
            # arm and reset all thirteen names on the way (#57).
            values = data.data if hasattr(data, 'data') else data.values
            idx = pd.Index(data.times if hasattr(data, 'times')
                           else data.index)
            # An index given alongside a source was silently dropped: this
            # branch takes the source's. `baseTs.__init__` legitimately derives
            # `times` FROM the source when the caller named none, so the test
            # is whether the two disagree, not whether one was passed.
            #
            # Refusing rather than ignoring, because ignoring is how
            # `baseTs(ts_200, times=arange(5))` returned a 200-sample object
            # and said nothing. Before TimeSeriesData counted as a source that
            # case at least reindexed to all-NaN - wrong, but visible - so
            # staying silent would have traded a loud wrong answer for a quiet
            # one, in a change that exists to stop objects misreporting
            # themselves.
            if index is not None and not pd.Index(index).equals(idx):
                raise ValueError(
                    "index/times was given alongside a source that "
                    "carries its own index, and the two differ. The "
                    "source's index is the one a conversion keeps, so "
                    "the argument would be ignored. Reindex the source "
                    "first, or drop the argument.")
            super().__init__(values, index=idx, **kwargs)
            self._copy_metadata_from_basetseries(data)
        elif isinstance(data, np.ndarray) and isinstance(index, np.ndarray):
            # Legacy numpy array initialization
            super().__init__(data, index=pd.Index(index), **kwargs)
            self._initialize_default_metadata()
        else:
            # Standard pandas Series initialization
            super().__init__(data, index=index, **kwargs)
            self._initialize_default_metadata()

        # The index was converted on its way in, by _set_axis - the one door
        # pandas routes every index through, including the ones above. What
        # is left to do here is give the origin it found back to the pair:
        # _initialize_default_metadata and _copy_metadata_from_basetseries
        # both just wrote the pair (defaults, or the source's) over the one
        # _set_axis had set, and an index carries its origin, so the index
        # wins. Before the rate declaration below, whose token reads the
        # index as installed.
        origin_from_index = self._restore_origin_from_index()

        # The offset pair is owned here, where the index is built, so that a
        # DatetimeIndex and an explicit `ts_offset` meet in one place. The
        # order - flag first, then the offset, then the one-way coherence
        # rule - is the order baseTs.__init__ applied before the pair moved
        # here, and the outcomes for every combination of the two keywords
        # are pinned on both the array and the conversion path.
        if not isinstance(has_timestamp_offset, _UnsetType):
            self.has_timestamp_offset = has_timestamp_offset
        if not isinstance(ts_offset, _UnsetType):
            if origin_from_index:
                raise ValueError(
                    "ts_offset was given alongside a DatetimeIndex, which "
                    "carries its own origin (its first stamp). One origin "
                    "or the other: pass seconds or a TimedeltaIndex with "
                    "ts_offset, or the DatetimeIndex alone.")
            self.ts_offset = ts_offset
            self.has_timestamp_offset = True
        elif (not isinstance(has_timestamp_offset, _UnsetType)
              and not has_timestamp_offset):
            # Explicitly cleared, with no offset named. Truthiness, not
            # `is False`: np.False_ is what `arr.any()` and any comparison
            # result give, and it is not the False singleton, so an identity
            # test let through exactly the pair this exists to prevent.
            #
            # One direction only. The reverse - asserting the flag without an
            # offset - is a caller's own assertion, and rejecting it would
            # break a call that works today.
            #
            # "no offset applied, offset 1.5" is a state nothing downstream
            # expects, and __finalize__ copies the pair onward, so an
            # incoherent one would ride into every derived object.
            self.ts_offset = 0

        # Declare the rate only when one was supplied. With no declaration the
        # `freq` property derives from the index on read, so there is nothing
        # to store - the `else` branch that used to derive into an attribute
        # here was the first of the two places that made freq a value able to
        # drift from the index it described.
        if freq is not None:
            self.freq = freq

        # Set signal name, but only when one was given. Assigned
        # unconditionally, this overwrote the name
        # _copy_metadata_from_basetseries had just copied off the source, so
        # TimeSeriesData(ts) returned an unnamed series (#57).
        #
        # Through normalise_label because this is the third door the label
        # metadata arrives by, and the only one that used to call a str method
        # on it: copy(deep=True) and _create_new_with_data both hand the
        # parent's name back to this constructor, so a name that was not a
        # string reached `.upper()` and died there rather than at the
        # assignment that set it.
        if not isinstance(signal_name, _UnsetType):
            self.signal_name = normalise_label(signal_name).upper()
        
        # Initialize or update history
        if not hasattr(self, 'history') or self.history is None:
            self.history = [f"Created TimeSeriesData with {len(self)} samples"]

    def _set_axis(self, axis, labels, *args, **kwargs) -> None:
        """Install an index, converting a stamped one to seconds (#100).

        This is the one door. pandas routes every index through here -
        `Series.__init__` on every spelling of the constructor, the `index`
        property setter, `set_axis`, the constructor `reindex` calls, the
        re-initialisation `_adopt_data_inplace` performs - measured on
        pandas 2.2.3 and 3.0.1, with the same signature on both (`*args,
        **kwargs` ride through in case a later pandas adds one). The first
        cut converted in `__init__` and the `times` setter instead, and
        review round 1 (both panelists) found `ts.index = dates` and
        `set_axis(dates)` leaving a raw DatetimeIndex on the object with a
        stale offset pair, so `datetimes` refused it as having no origin.

        A DatetimeIndex becomes seconds and its first stamp is recorded as
        the origin; a TimedeltaIndex becomes seconds and the pair is left
        alone (durations say nothing about an origin); anything else is
        installed as given. `_origin_from_index` always describes the index
        currently installed: the origin it brought, or None. It is not in
        `_metadata`, so it is neither propagated nor pickled - it is a fact
        about this object's own index, and every copier consults it to
        apply the one rule: an index carries its origin, and a copied pair
        does not overwrite it. See _restore_origin_from_index.

        The pair is set here as well, directly, for the post-construction
        doors. During construction the metadata initialisers overwrite it a
        moment later and `__init__` restores it from `_origin_from_index`.
        """
        index = labels if isinstance(labels, pd.Index) else ensure_index(labels)
        converted = _seconds_since_origin(index)
        origin = None
        if converted is not None:
            index, origin = converted
        super()._set_axis(axis, index, *args, **kwargs)
        object.__setattr__(self, '_origin_from_index', origin)
        if origin is not None:
            object.__setattr__(self, 'ts_offset', origin)
            object.__setattr__(self, 'has_timestamp_offset', True)

    def _restore_origin_from_index(self) -> bool:
        """Give the pair the origin the installed index brought, if any.

        The rule every copier applies: an index carries its origin. A
        derivation that keeps its parent's seconds inherits the parent's
        pair (the index brought no origin, so the copy stands); one whose
        index arrived stamped - `reindex(dates)`, `_create_new_with_data(x,
        dates)`, `TimeSeriesData(duck_with_dates)` - keeps the origin those
        stamps carry, and the parent's or source's pair, copied a moment
        earlier, is put back. Read from `__dict__`, not getattr: an object
        pandas built without `__init__` has no such slot and must read as
        "no origin", not recurse.

        Returns:
            True when the index brought an origin.
        """
        origin = self.__dict__.get('_origin_from_index')
        if origin is None:
            return False
        object.__setattr__(self, 'ts_offset', origin)
        object.__setattr__(self, 'has_timestamp_offset', True)
        return True

    @property
    def datetimes(self) -> pd.DatetimeIndex:
        """The index as calendar stamps: the origin plus each second.

        The index itself is seconds (#100), so this is the one way back to
        the stamps a series was built from, and what pandas' calendar
        conveniences read - `ts.groupby(ts.datetimes.month)`,
        `pd.Series(ts.values, index=ts.datetimes).rolling('1h')`. The stamps
        are naive UTC; an aware index was recorded as its UTC instant.

        Exact for any series built from stamps at microsecond resolution or
        coarser - see _origin_timestamp and _stamps_from_seconds for the two
        limits.

        Raises:
            ValueError: when the series has no origin - built from seconds or
                durations and never given one.
        """
        if not self.has_timestamp_offset:
            raise ValueError(
                "this series has no timestamp origin: its index is seconds "
                "with no calendar attached. Build it from a DatetimeIndex, "
                "or declare the origin with set_timestamp_offset(epoch_seconds).")
        return _stamps_from_seconds(_origin_timestamp(self.ts_offset), self.index)

    def _initialize_default_metadata(self):
        """Initialize default metadata values."""
        self.is_filtered = False
        self.is_interpolated = False
        self.is_uniform_grid = False
        self.ts_offset = 0
        self.has_timestamp_offset = False
        self._outlier_indices = None
        self._lowess_fit = None
        self.last_process = ""
        self.history = []
        # Listed in _metadata, and now that the constructor only assigns a
        # name when one is given, this is where the default comes from for a
        # series built from arrays.
        self.signal_name = ""
        # _metadata declares these two; without them any derived object
        # inherited None and clobbered the default it was born with.
        self.is_outlier_filtered = False
        self.outlier_filter = LowessOutlierFilter()
        # _metadata declares this; test_type_preservation.py asserts every
        # declared name exists on a constructed object.
        self._freq_declaration = None

    def _copy_metadata_from_basetseries(self, base_ts):
        """Copy metadata from a baseTs object, without sharing its mutables."""
        for attr in self._metadata:
            if hasattr(base_ts, attr):
                setattr(self, attr, getattr(base_ts, attr))
            else:
                # Set default if attribute doesn't exist
                if attr == 'history':
                    self.history = [f"Converted from baseTs with {len(self)} samples"]
                elif attr in ['is_filtered', 'is_interpolated', 'is_uniform_grid',
                              'is_outlier_filtered', 'has_timestamp_offset']:
                    # is_outlier_filtered was missing from this list, so the
                    # one boolean flag that names the outlier filter fell to
                    # the bare `else` and landed as None - on the same objects,
                    # and by the same omission, as the filter itself. Nothing
                    # downstream normalises it, so it propagated.
                    setattr(self, attr, False)
                elif attr in ['ts_offset']:
                    setattr(self, attr, 0)
                else:
                    # What reaches here is None-tolerant by design:
                    # _lowess_fit and _outlier_indices carry the index they
                    # describe (#20), and _freq_declaration is absent until
                    # someone declares a rate (#29/#31/#23). signal_name and
                    # last_process are normalising properties (#61), so the
                    # None lands as "" - the arm that used to assign "" for
                    # them was redundant with the setter. outlier_filter is
                    # not None-tolerant - but it needs no arm of its own,
                    # because the _detach_shared_metadata call at the end of
                    # this method restores a default for exactly that name.
                    # An arm here would be unreachable in effect:
                    # neutralising it leaves every test in
                    # test_metadata_defaults.py green.
                    setattr(self, attr, None)

        # attrs and flags are not in _metadata, so the loop above cannot
        # carry them and a conversion arrived without either. `_name` the
        # loop does carry - but only when the source has the attribute, and a
        # duck-typed source or one restored from a pre-#39 pickle does not,
        # which is precisely what this helper's getattr is for.
        _carry_identity(self, base_ts)

        _detach_shared_metadata(self)

    def _calculate_effective_frequency(self) -> float:
        """Derive the sampling frequency from the time index.

        Returns NaN rather than raising for any index this cannot measure -
        too short, zero or negative duration, or a non-numeric dtype. NaN is
        the value the consumption guards (validate_sampling_freq and friends)
        are built to reject with a message naming the degenerate time base;
        a raw TypeError escaping from here would name the subtraction
        instead, some distance from the mistake.

        The TypeError arm covers a non-numeric index - strings, say. A
        DatetimeIndex used to be the case that reached it (its span is a
        Timedelta, which float() refuses); since #100 the constructor
        converts one to seconds before anything derives from it.

        Returns:
            Samples per unit time, or NaN when the index cannot support a rate
        """
        if len(self.index) < 2:
            return np.nan
        try:
            duration = float(self.index[-1] - self.index[0])
        except (TypeError, ValueError):
            return np.nan
        if duration <= 0:
            return np.nan
        # n samples span n-1 intervals. Using len(self) here over-reported the
        # rate by n/(n-1) - 11% at n=10, 25% at n=5 - for every series built
        # from a times array without an explicit freq.
        return (len(self) - 1) / duration

    @property
    def freq(self) -> float:
        """The sampling rate in Hz, derived from the index unless declared.

        An explicitly supplied rate is honoured only while the index still
        matches the token it was declared against - see _freq_token. This is
        what makes every derivation path agree: __finalize__, copy() and
        _create_new_with_data all just carry the declaration, and this one
        property decides whether it still applies.

        Returns:
            The declared rate when its token still matches, otherwise the
            rate derived from the current index (NaN if it cannot support one)
        """
        declaration = getattr(self, '_freq_declaration', None)
        if declaration is not None:
            try:
                if declaration[1] == _freq_token(self.index):
                    return declaration[0]
            except Exception:
                # Any failure to build or compare a token - an exotic index
                # dtype, an object array - falls through to re-deriving.
                # Failing toward derivation is the safe direction: it is what
                # the index actually supports.
                pass
        return self._calculate_effective_frequency()

    @freq.setter
    def freq(self, value: Any) -> None:
        """Declare an explicit sampling rate against the current index.

        The single validating door for a rate entering the object. Issue #31
        is that there was no such door: `freq=` reached __init__ unchecked and
        __finalize__ copied it onward, so a bad rate was reported some
        distance from the mistake, with a diagnosis that could be flatly
        wrong - a NaN blamed the timestamps when the constructor kwarg was
        the problem.

        Args:
            value: A positive finite rate, or None to clear the declaration
                and return the object to deriving from its index

        Raises:
            ValueError: If value is not a positive, finite real scalar
        """
        if value is None:
            self._freq_declaration = None
            return
        self._freq_declaration = (validate_sampling_freq(value),
                                  _freq_token(self.index))

    def __finalize__(self, other, method=None, **kwargs):
        """
        Propagate metadata, detaching what a derived object must not share.

        pandas' default __finalize__ assigns metadata by reference, so a derived
        object would share the parent's `history` list - appending to one would
        silently append to the other.

        `outlier_filter` is deliberately left shared: FilterConfig is frozen
        and set_outlier_filter rebinds rather than mutates it, so a shared
        filter cannot carry a write from one object to another.

        `_lowess_fit` and `_outlier_indices` need nothing special here. They
        carry the index and the values they describe with them, so copying
        the triple verbatim is correct however the derived index or values
        differ - the property re-checks both on read. That is the point of moving the check to read time: this
        method no longer has to be one of the places that knows the rule.

        method == 'concat' is special-cased: nlargest/nsmallest route through
        an internal concat step where `other` is not an NDFrame (a
        SimpleNamespace on pandas >= 3.0, a private _Concatenator on
        pandas 2.x), so pandas' own isinstance(other, NDFrame) branch above
        skips it and metadata is silently dropped. `objs` is the attribute
        both shapes carry; the newer `input_objs` pandas' >= 3.0
        __finalize__ docstring documents does not exist on pandas 2.x and
        using it there silently no-ops this whole block - caught by CI on
        Python 3.9/3.10 (pandas 2.3.3), which this project's own
        `pandas>=2.0.0` floor requires supporting. Recovery only fires when
        exactly one of those objects is non-empty: that is nlargest/
        nsmallest's internal single-real-result-plus-empty-placeholder
        pattern. A genuine multi-operand pd.concat() has more than one
        non-empty operand, and must not have its result's
        freq/signal_name/history overwritten by whichever operand happens to
        be first - the constructor already derived correct values from the
        real merged index.
        """
        super().__finalize__(other, method=method, **kwargs)
        if method == 'concat':
            objs = getattr(other, 'objs', None)
            if objs:
                nonempty = [obj for obj in objs if len(obj) > 0]
                if len(nonempty) == 1:
                    source = nonempty[0]
                    for name in self._metadata:
                        if hasattr(source, name):
                            object.__setattr__(self, name, getattr(source, name))
        # The pair was just copied from `other`; if this object's own index
        # arrived stamped (reindex(dates) builds through the constructor
        # and lands here), that index's origin is the one that holds (#100,
        # review round 1).
        self._restore_origin_from_index()
        return _detach_shared_metadata(self)

    def _finalizing_window(self, method: str, *args, **kwargs) -> _FinalizingWindow:
        """See _FinalizingWindow: rolling()/expanding()/ewm() never call __finalize__."""
        window = getattr(super(), method)(*args, **kwargs)
        return _FinalizingWindow(window, self, method)

    def rolling(self, *args, **kwargs) -> _FinalizingWindow:
        """Rolling window whose aggregations propagate metadata - see _FinalizingWindow."""
        return self._finalizing_window('rolling', *args, **kwargs)

    def expanding(self, *args, **kwargs) -> _FinalizingWindow:
        """Expanding window whose aggregations propagate metadata - see _FinalizingWindow."""
        return self._finalizing_window('expanding', *args, **kwargs)

    def ewm(self, *args, **kwargs) -> _FinalizingWindow:
        """EWM window whose aggregations propagate metadata - see _FinalizingWindow."""
        return self._finalizing_window('ewm', *args, **kwargs)

    @property
    def _constructor(self):
        """Return constructor for pandas operations."""
        return TimeSeriesData

    @property
    def _constructor_sliced(self):
        """Return constructor for sliced operations."""
        return TimeSeriesData

    def copy(self, deep: bool = True) -> "TimeSeriesData":
        """
        Create a copy of the TimeSeriesData object with metadata preservation.
        
        Args:
            deep: Whether to make a deep copy
            
        Returns:
            Copied TimeSeriesData object
        """
        copied = super().copy(deep=deep)
        # Ensure it's the right type
        if not isinstance(copied, TimeSeriesData):
            copied = TimeSeriesData(copied.values, index=copied.index)

        # No _carry_identity call here, deliberately. `super().copy()` runs
        # pandas' __finalize__, which carries attrs and flags, and the
        # _metadata loop below carries `_name` now that the registry declares
        # it - so all three arrive without help at both depths. Measured, not
        # assumed: adding a call changed nothing, and deleting it again broke
        # no test. The rebuild above is pre-existing dead code (`_constructor`
        # guarantees the type), so putting the call inside it would only look
        # load-bearing.
        
        # Copy metadata. The allow-list bounds what gets deep-copied: an
        # unguarded deepcopy turns any non-copyable metadata value into a hard
        # error on routine operations. outlier_filter is not on it, and is
        # shared at both depths - safe, see _detach_shared_metadata.
        for attr in self._metadata:
            if hasattr(self, attr):
                value = getattr(self, attr)
                if deep:
                    # See deepcopy_metadata_value: the positional slots hold a
                    # (value, index) tuple, so an isinstance check against
                    # list/dict/ndarray never matches them and a deep copy
                    # would quietly share the parent's array.
                    value = deepcopy_metadata_value(attr, value)
                setattr(copied, attr, value)

        # Unconditionally, not just when shallow. The loop above re-assigns
        # history by reference, undoing what __finalize__ already detached,
        # and pandas reaches here internally (sort_values calls
        # copy(deep=False)), so a "shallow" copy must not hand back a shared
        # list. The deep branch already deep-copies a list history, but
        # deepcopy(None) is None, so copy(deep=True) was the one derivation
        # path that let a malformed history through - the normalisation has
        # to run on both.
        _detach_shared_metadata(copied)
        return copied

    def duration(self) -> float:
        """
        Calculate the duration of the time series.
        
        Returns:
            Duration in seconds (or time units of the index)
        """
        if len(self.index) == 0:
            return 0.0
        return float(self.index[-1] - self.index[0])

    def len(self) -> int:
        """
        Get the length of the time series (backward compatibility).
        
        Returns:
            Number of data points
        """
        return len(self)

    def _update_history_and_process(self, hist_msg: str, last_process: str):
        """Helper method to update history and last_process.

        Normalises rather than testing `is None`. _detach_shared_metadata only
        runs on *derivation* - copy(), iloc, _create_new_with_data - so it
        never touches the object an in-place method mutates. A str, tuple or
        dict history set on an object and then passed to set_timestamp_offset,
        set_outlier_filter or any inplace=True filter reached .append()
        untouched and raised the very AttributeError this guard exists to
        prevent.
        """
        self.history = normalise_history(getattr(self, 'history', None))
        self.history.append(hist_msg)
        self.last_process = last_process

    def _update_flags(self, **flags):
        """Helper method to update object flags."""
        for flag_name, flag_value in flags.items():
            setattr(self, flag_name, flag_value)

    def to_basetseries(self):
        """
        Convert back to a legacy baseTs object for compatibility.

        Returns:
            baseTs object with equivalent data and metadata
        """
        from .core import baseTs

        # Create baseTs object with numpy arrays. The name is not passed
        # here: it is copied below with the rest of _metadata. Re-minting it
        # through the constructor upper-cased it, so a conversion renamed the
        # series it was converting (#56).
        base_ts = baseTs(
            data=self.values,
            times=self.index.values,
        )

        # Copy metadata. freq is no longer special-cased out: the rate is not
        # in _metadata any more, _freq_declaration is, and the constructed
        # object derives from an index identical to this one. Nor is
        # signal_name: it is a normalising property (#61), so the setattr
        # below coerces a None to "" on its own.
        for attr in self._metadata:
            if hasattr(self, attr):
                setattr(base_ts, attr, getattr(self, attr))

        # A conversion is a copy, so it keeps the source's identity. The loop
        # above would carry `_name` on its own now that the registry declares
        # it; attrs and flags have never been in the registry and still need
        # this call.
        _carry_identity(base_ts, self)

        return _detach_shared_metadata(base_ts)

    def info(self):
        """
        Display information about the time series data.
        """
        from .utils import round_values
        
        data_info = {
            "Length": len(self),
            "Min": np.min(self.values),
            "Max": np.max(self.values),
            "Std": np.std(self.values)
        }
        
        # Round all values except for length
        for key, value in data_info.items():
            data_info[key] = round_values(value)
        
        times_info = {
            "Start": self.index[0] if len(self) > 0 else np.nan,
            "End": self.index[-1] if len(self) > 0 else np.nan,
            "Duration": self.duration(),
            "Effective Frequency": self.freq,
            "Timestamp Offset": getattr(self, 'ts_offset', 0)
        }
        
        for key, value in times_info.items():
            times_info[key] = round_values(value)
        
        print("TimeSeriesData Information:")
        for key, value in data_info.items():
            print(f"  {key}: {value}")
        
        print("\nTime Information:")
        for key, value in times_info.items():
            print(f"  {key}: {value}")
        
        # normalise_history, not a truthiness test: `and self.history` raises
        # on an ndarray and len() raises on a generator, and a bare loop over
        # a str prints one line per character. Kept identical to baseTs.info(),
        # which prints the header unconditionally - the two used to disagree
        # on an empty history.
        print("\nHistory:")
        for entry in normalise_history(getattr(self, 'history', None)):
                print(f"  {entry}")

    def __repr__(self) -> str:
        """String representation of TimeSeriesData."""
        base_repr = super().__repr__()
        additional_info = f"\nFreq: {getattr(self, 'freq', 'Unknown')} Hz"
        if hasattr(self, 'signal_name') and self.signal_name:
            additional_info += f", Signal: {self.signal_name}"
        return base_repr + additional_info

    # Arithmetic operations that should return baseTs objects
    def __add__(self, other):
        """Addition operation returning a baseTs object."""
        result = super().__add__(other)
        return self._wrap_result_as_basets(result, "Addition")

    def __radd__(self, other):
        """Right addition operation returning a baseTs object."""
        result = super().__radd__(other)
        return self._wrap_result_as_basets(result, "Addition")

    def __sub__(self, other):
        """Subtraction operation returning a baseTs object."""
        result = super().__sub__(other)
        return self._wrap_result_as_basets(result, "Subtraction")

    def __rsub__(self, other):
        """Right subtraction operation returning a baseTs object."""
        result = super().__rsub__(other)
        return self._wrap_result_as_basets(result, "Subtraction")

    def __mul__(self, other):
        """Multiplication operation returning a baseTs object."""
        result = super().__mul__(other)
        return self._wrap_result_as_basets(result, "Multiplication")

    def __rmul__(self, other):
        """Right multiplication operation returning a baseTs object."""
        result = super().__rmul__(other)
        return self._wrap_result_as_basets(result, "Multiplication")

    def __truediv__(self, other):
        """Division operation returning a baseTs object."""
        result = super().__truediv__(other)
        return self._wrap_result_as_basets(result, "Division")

    def __rtruediv__(self, other):
        """Right division operation returning a baseTs object."""
        result = super().__rtruediv__(other)
        return self._wrap_result_as_basets(result, "Division")

    def __pow__(self, other):
        """Power operation returning a baseTs object."""
        result = super().__pow__(other)
        return self._wrap_result_as_basets(result, "Power")

    def __rpow__(self, other):
        """Right power operation returning a baseTs object."""
        result = super().__rpow__(other)
        return self._wrap_result_as_basets(result, "Power")

    def _inplace_arith(self, result):
        """
        Adopt an arithmetic result in place, history entry included.

        pandas implements `ts += 1` as __add__ followed by keeping the values
        and discarding the wrapper, so the entry _wrap_result_as_basets
        appended would be thrown away with it - `ts += 1` recorded nothing
        while `ts = ts + 1` recorded an entry.
        """
        if not isinstance(result, TimeSeriesData):
            return result
        history = list(getattr(result, 'history', []) or [])
        last_process = getattr(result, 'last_process', "")
        # reindex_like, as pandas' own _inplace_method does: augmented
        # assignment must not change the length of the object being assigned
        # to, even when the operand carries a different index.
        self._update_inplace(result.reindex_like(self))
        object.__setattr__(self, 'history', history)
        object.__setattr__(self, 'last_process', last_process)
        return self

    def __iadd__(self, other):
        return self._inplace_arith(self + other)

    def __isub__(self, other):
        return self._inplace_arith(self - other)

    def __imul__(self, other):
        return self._inplace_arith(self * other)

    def __itruediv__(self, other):
        return self._inplace_arith(self / other)

    def __ipow__(self, other):
        return self._inplace_arith(self ** other)

    def _wrap_result_as_basets(self, result, operation_name: str):
        """
        Wrap arithmetic operation results as baseTs objects.
        
        Args:
            result: Result from pandas arithmetic operation
            operation_name: Name of the operation for history tracking
            
        Returns:
            baseTs object with the operation result
        """
        # Import here to avoid circular imports
        from .core import baseTs
        
        # Handle scalar results
        if np.isscalar(result):
            # For scalar results, we can't return a baseTs, so return the scalar
            return result
        
        # No freq= kwarg here - it is carried below instead, as
        # _freq_declaration, along with the rest of _metadata. No
        # signal_name= either, for the same reason and one more: through the
        # constructor the operand's name came back upper-cased, so
        # `ts + 1` was titled differently from `ts` (#56). The loop below
        # copies it verbatim; signal_name is a normalising property (#61),
        # so a None operand name still lands as "" at the assignment.
        new_basets = baseTs(
            data=result.values,
            times=result.index.values,
        )

        # Copy relevant metadata. _freq_declaration rides along like any other
        # name: arithmetic between two operands on different time bases
        # produces a union index, whose token will not match the declaration,
        # so the result re-derives. The explicit freq exclusion this loop used
        # to carry is what the token now does properly.
        #
        # `_name` is not excluded here, though it is tempting to: the
        # `_carry_identity` call below supersedes whatever this loop sets, so
        # an exclusion would be dead code that reads like a safeguard.
        # Deleting one confirmed it - no test could tell the two apart.
        for attr in self._metadata:
            if hasattr(self, attr):
                setattr(new_basets, attr, getattr(self, attr))

        # From `result`, not `self`: name, attrs and flags on the operation's
        # own output are what pandas decided they should be, including for the
        # reflected operators, where `self` is the right-hand operand.
        _carry_identity(new_basets, result)

        # Before the history update, not after: the entry appended below would
        # otherwise land in the operand's own history list.
        _detach_shared_metadata(new_basets)

        # Update history
        new_basets._update_history_and_process(
            f"Applied {operation_name} operation",
            f"_{operation_name.lower()}"
        )
        
        return new_basets