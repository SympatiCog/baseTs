"""The three identity fields pandas owns must survive derivation (#35, #39).

A `baseTs` is a `pd.Series`, so it carries three pieces of identity that
pandas defines and propagates itself: the Series `name`, the `attrs` dict and
`flags`. On `main` it drops all three across most derivations, where plain
`pd.Series` drops none of them.

Two independent causes, and these tests are grouped by which one they pin:

* `TimeSeriesData._metadata` *replaced* `pd.Series._metadata` (which is
  `['_name']`), so every `__finalize__` path lost the name and an unpickled
  object was left without a `_name` attribute at all - that is #39, and it is
  why `repr()` on an unpickled baseTs used to raise.
* Nine sites rebuild or re-initialise an object carrying only `_metadata`
  names. `attrs` and `flags` are not in `_metadata`; pandas handles them
  separately inside `__finalize__`, so no site carried them.

The design doc is `docs/superpowers/specs/2026-09-02-name-attrs-propagation-design.md`.

The guard against a tenth site is deliberately *derived* rather than listed:
`test_every_inplace_method_is_classified` discovers baseTs' own `inplace=`
methods by reflection, so adding one without classifying it fails here. An
earlier revision of this file listed the paths by hand, which is exactly how
`interpolate_gaps(inplace=True)` and `shift_time(inplace=True)` went unfound.
"""
import ast
import copy as copy_module
import inspect
import pathlib
import pickle

import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest

from baseTs import baseTs
from baseTs.series import (TimeSeriesData, deepcopy_metadata_value,
                          _carry_identity,
                          _apply_duplicate_label_declaration,
                          _refuse_undeclarable_index)
from baseTs.utils import ValidationError

NAME = "NAMEVAL"
ATTRS = {"unit": "mV"}


def seeded(n: int = 200, rate: float = 40.0) -> baseTs:
    """A baseTs whose three identity fields are all at non-default values.

    Every field must differ from its default or an assertion that it
    "survived" is vacuous - it would pass against an object that had been
    reset. `allows_duplicate_labels` defaults to True, so the seed is False.
    """
    times = np.arange(n) / rate
    data = np.sin(2 * np.pi * 3.0 * times) + 0.05 * np.arange(n)
    ts = baseTs(data, times, signal_name="sig")
    ts.name = NAME
    ts.attrs["unit"] = "mV"
    ts.flags.allows_duplicate_labels = False
    return ts


def identity_of(obj):
    """The three fields as one comparable tuple."""
    return (obj.name, dict(obj.attrs), obj.flags.allows_duplicate_labels)


SEEDED_IDENTITY = (NAME, ATTRS, False)


# --------------------------------------------------------------------------
# Cause A: _name belongs to pandas' own registry
# --------------------------------------------------------------------------

class TestMetadataRegistry:
    """`_metadata` must extend pandas' list rather than replace it."""

    def test_metadata_extends_rather_than_replaces_pandas(self):
        """Every name pandas declares must still be carried.

        Asserted against `pd.Series._metadata` rather than the literal
        `'_name'`, because the defect being fixed is precisely that a list
        pandas owns was hardcoded here. A future pandas that adds a second
        name would reintroduce the bug against a hardcoded assertion while
        passing this one.
        """
        for declared in pd.Series._metadata:
            assert declared in TimeSeriesData._metadata

    def test_name_is_carried_by_the_registry_not_by_a_special_case(self):
        assert '_name' in TimeSeriesData._metadata


class TestUnpickledObjectIsUsable:
    """#39: the round-trip always worked; what came back did not.

    Stated precisely because two earlier attempts at this sentence were
    wrong: `dumps` succeeds and `loads` succeeds on `main` too. The defect is
    that the returned object has no `_name`, so every pandas operation and
    even `repr()` raised AttributeError. Asserting `loads` returned something
    would therefore have passed against the bug.
    """

    def test_round_trip_returns_an_equivalent_object(self):
        back = pickle.loads(pickle.dumps(seeded()))
        assert isinstance(back, baseTs)
        assert len(back) == 200
        np.testing.assert_allclose(back.values, seeded().values)

    def test_unpickled_object_has_the_private_name_slot(self):
        back = pickle.loads(pickle.dumps(seeded()))
        assert hasattr(back, '_name')

    @pytest.mark.parametrize("label, operation", [
        ("name", lambda ts: ts.name),
        ("repr", lambda ts: repr(ts)),
        ("iloc", lambda ts: ts.iloc[:3]),
        ("head", lambda ts: ts.head(2)),
        ("arithmetic", lambda ts: ts + 1),
    ])
    def test_operations_on_an_unpickled_object_do_not_raise(self, label,
                                                            operation):
        """Each of these raised AttributeError: no attribute '_name'.

        Parametrised one operation per case rather than in a loop, so a
        regression names the operation that broke instead of the first one.
        """
        back = pickle.loads(pickle.dumps(seeded()))
        operation(back)

    def test_identity_survives_the_round_trip(self):
        back = pickle.loads(pickle.dumps(seeded()))
        assert identity_of(back) == SEEDED_IDENTITY


class _ExtendedForPickling(baseTs):
    """A subclass adding a `_metadata` name, defined at module level.

    Module level because pickle resolves a class by qualified name, and one
    defined inside a test function cannot be found on load.
    """

    _metadata = baseTs._metadata + ['extra_field']

    @property
    def _constructor(self):
        return _ExtendedForPickling


class TestPickleWrittenBeforeTheFix:
    """A blob already on disk must load too, and that needs more than #35.

    Adding `_name` to `_metadata` fixes what is pickled *from now on*.
    `__getstate__` writes the registry as it stood at dump time, so a blob
    written by the old code has no `_name` key and pandas' restore loop has
    nothing to set it from - the object comes back missing the attribute and
    raises on every operation, which is #39 unfixed for every pickle that
    already exists. `__setstate__` normalises it.

    Reproduced by deleting the key from a state dict rather than by
    committing a binary fixture: the shape being tested is exactly "this key
    is absent", and a checked-in blob would additionally pin a pickle
    protocol and a pandas version that this test does not mean to assert.
    """

    @staticmethod
    def _restored_without_a_name_key():
        """A state dict shaped like a blob written before `_name` was added.

        Both edits matter, and an earlier version of this fixture made only
        the first. Deleting the `_name` *value* reproduces the missing
        attribute; leaving `state['_metadata']` as the current registry does
        not reproduce a real legacy blob, whose registry predates `_name`.
        pandas installs that stored list as an *instance* attribute, so the
        stale one shadows the class's permanently - and a fixture that keeps
        the current list cannot see it. That gap is exactly why the shadowing
        defect survived a full mutation round here.
        """
        state = dict(seeded().__getstate__())
        assert '_name' in state, (
            "the fixture assumes __getstate__ writes _name; if it stopped, "
            "this test is no longer reproducing a pre-fix blob"
        )
        del state['_name']
        state['_metadata'] = [name for name in state['_metadata']
                              if name != '_name']
        revived = object.__new__(baseTs)
        revived.__setstate__(state)
        return revived

    def test_the_stale_registry_does_not_shadow_the_class(self):
        """The heal must survive the next operation, not just the load.

        Without this, a legacy object came back working and then lost its
        name again the first time anything iterated `self._metadata`.
        """
        revived = self._restored_without_a_name_key()
        assert '_name' in revived._metadata

    def test_a_name_set_after_loading_survives_a_re_pickle(self):
        revived = self._restored_without_a_name_key()
        revived.name = "healed"
        assert pickle.loads(pickle.dumps(revived)).name == "healed"

    def test_a_name_set_after_loading_survives_an_inplace_write(self):
        revived = self._restored_without_a_name_key()
        revived.name = "healed"
        revived.data = np.arange(4.0)
        assert revived.name == "healed"

    def test_a_deliberately_extended_instance_registry_is_kept(self):
        """Only a *stale* shadow is dropped, not any shadow.

        Deleting unconditionally also discarded a registry extended on one
        instance: the extra names' values survived the round-trip, but
        nothing tracked them afterwards, so they were dropped from every
        later derivation. A shadow that still covers what the class declares
        is not the legacy case.
        """
        ts = seeded()
        object.__setattr__(ts, '_metadata', list(ts._metadata) + ['ad_hoc'])
        object.__setattr__(ts, 'ad_hoc', 'kept')

        back = pickle.loads(pickle.dumps(ts))

        # Both, because the registry entry without the value would be a
        # dangling name and the value without the entry is what the
        # unconditional delete produced. Not asserted: that `back.iloc[:3]`
        # also carries it - an instance-level registry never propagated to
        # derived objects, on `main` or here, because __finalize__ reads the
        # *new* object's `_metadata`, which is the class's.
        assert 'ad_hoc' in back._metadata
        assert back.ad_hoc == 'kept'

    def test_a_subclass_that_extends_the_registry_round_trips(self):
        """The class-level case, which must keep working either way."""
        obj = _ExtendedForPickling(np.arange(5.0), np.arange(5) / 10.0)
        obj.name = 'X'
        obj.extra_field = 'kept'

        back = pickle.loads(pickle.dumps(obj))

        assert back.name == 'X'
        assert back.extra_field == 'kept'
        assert 'extra_field' in back._metadata
        # Unlike the instance case above, a class-level entry does reach a
        # derived object, because __finalize__ finds it on the child's class.
        assert back.iloc[:3].extra_field == 'kept'

    def test_a_pre_fix_blob_loads_without_the_key(self):
        assert hasattr(self._restored_without_a_name_key(), '_name')

    @pytest.mark.parametrize("label, operation", [
        ("name", lambda ts: ts.name),
        ("repr", lambda ts: repr(ts)),
        ("iloc", lambda ts: ts.iloc[:3]),
        ("arithmetic", lambda ts: ts + 1),
    ])
    def test_a_pre_fix_blob_is_usable(self, label, operation):
        operation(self._restored_without_a_name_key())

    def test_the_absent_name_comes_back_as_none_not_invented(self):
        """None, because the name genuinely is not in those bytes.

        Healing the object must not mean guessing what it was called -
        `signal_name` is a different field with a different meaning, and
        substituting it here would make an unpickled object disagree with
        every other derivation about what `name` holds.
        """
        assert self._restored_without_a_name_key().name is None


# --------------------------------------------------------------------------
# Cause B, group 1: the rebuild sites
# --------------------------------------------------------------------------

#: Derivation paths that must hand back an object carrying the seed's
#: identity. Split from the pandas-native paths below only for readability -
#: the requirement is identical.
BASETS_DERIVATIONS = {
    "copy(deep=True)": lambda ts: ts.copy(),
    "copy(deep=False)": lambda ts: ts.copy(deep=False),
    "deepcopy": lambda ts: copy_module.deepcopy(ts),
    "apply_function": lambda ts: ts.apply_function(lambda d: d * 2),
    "lowpass_filter": lambda ts: ts.lowpass_filter(8.0),
    "bandpass_at": lambda ts: ts.bandpass_at(1.0, 8.0),
    "zscale": lambda ts: ts.zscale(),
    "detrend": lambda ts: ts.detrend(),
    "sg_filter": lambda ts: ts.sg_filter(),
    "filter_outliers": lambda ts: ts.filter_outliers(),
    "interpolate_gaps": lambda ts: ts.interpolate_gaps(),
    "interpto_hz": lambda ts: ts.interpto_hz(20.0),
    "shift_time": lambda ts: ts.shift_time(2),
    "baseTs(ts)": lambda ts: baseTs(ts),
    "TimeSeriesData(ts)": lambda ts: TimeSeriesData(ts),
    "to_basetseries": lambda ts: TimeSeriesData(ts).to_basetseries(),
    "arithmetic": lambda ts: ts + 1,
}

#: Paths implemented entirely by pandas. They already worked for `attrs` and
#: `flags`; they are here because `name` did not, and because a change to our
#: `_metadata` or `copy()` can break them - `head()` on pandas 3.0 is
#: `self.iloc[:n].copy()`, so it reaches our rebuild.
PANDAS_NATIVE_DERIVATIONS = {
    "iloc": lambda ts: ts.iloc[:50],
    "head": lambda ts: ts.head(10),
    "dropna": lambda ts: ts.dropna(),
    "round": lambda ts: ts.round(2),
    "sort_values": lambda ts: ts.sort_values(),
    "rolling.mean": lambda ts: ts.rolling(5).mean(),
}

ALL_DERIVATIONS = {**BASETS_DERIVATIONS, **PANDAS_NATIVE_DERIVATIONS}


class TestIdentitySurvivesDerivation:

    @pytest.mark.parametrize("label", sorted(ALL_DERIVATIONS))
    def test_derived_object_carries_the_identity(self, label):
        derived = ALL_DERIVATIONS[label](seeded())
        assert identity_of(derived) == SEEDED_IDENTITY

    def test_plain_pandas_is_the_standard_being_met(self):
        """The bar is pandas' own behaviour, not an invented one.

        If a future pandas stops propagating these on a native path, this
        fails alongside the baseTs case and says which side moved.
        """
        s = pd.Series(np.arange(10.0), name=NAME)
        s.attrs["unit"] = "mV"
        s.flags.allows_duplicate_labels = False
        for derive in (lambda x: x.iloc[:5], lambda x: x.copy(),
                       lambda x: x + 1, lambda x: copy_module.deepcopy(x)):
            assert identity_of(derive(s)) == SEEDED_IDENTITY


class TestAttrsIsolation:
    """attrs must be copied, never shared - pandas deep-copies it."""

    def test_mutating_a_derived_objects_attrs_does_not_reach_the_parent(self):
        parent = seeded()
        child = parent.copy()
        child.attrs["unit"] = "V"
        assert parent.attrs["unit"] == "mV"

    def test_nested_attrs_values_are_isolated_too(self):
        """A shallow dict copy passes the test above and fails this one.

        pandas' `__finalize__` uses `deepcopy`, guarded by an emptiness
        check; matching it shallowly would leave two objects sharing one
        nested value while looking correct at the top level.
        """
        parent = seeded()
        parent.attrs["cal"] = {"gain": 1}
        child = parent.copy()
        child.attrs["cal"]["gain"] = 99
        assert parent.attrs["cal"]["gain"] == 1

    def test_an_empty_attrs_stays_empty(self):
        """The emptiness guard must not invent a dict where none was set."""
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        assert ts.copy().attrs == {}


class TestArithmeticNameFollowsPandas:
    """The one place carrying `_name` could silently diverge from pandas.

    `_wrap_result_as_basets` rebuilds from the result of the pandas
    operation. Copying `self`'s name onto it would look right for `ts + 1`
    and be wrong for two named operands, where pandas resolves the result
    name to None.
    """

    @staticmethod
    def _named(name, values=(1.0, 2.0, 3.0)):
        ts = baseTs(np.array(values), np.arange(len(values)) / 10.0)
        ts.name = name
        return ts

    def test_matching_names_are_kept(self):
        assert (self._named("A") + self._named("A")).name == "A"

    def test_differing_names_resolve_to_none_as_in_pandas(self):
        result = self._named("A") + self._named("B")
        reference = (pd.Series([1.0, 2.0, 3.0], name="A")
                     + pd.Series([1.0, 2.0, 3.0], name="B"))
        assert result.name == reference.name is None

    def test_scalar_operand_keeps_the_series_name(self):
        assert (self._named("A") + 1).name == "A"

    def test_reflected_operators_agree_with_pandas(self):
        """`result.name` is pandas-resolved whichever dunder produced it."""
        assert (1 + self._named("A")).name == "A"


class TestDeepcopyOfAName:
    """`_name` now reaches deepcopy_metadata_value; it must pass through."""

    def test_a_name_is_returned_unchanged(self):
        assert deepcopy_metadata_value('_name', 'SIG') == 'SIG'

    def test_a_name_cannot_be_a_mutable_container(self):
        """Which is why the isinstance gate in that helper never matches it.

        Recorded as a test rather than a comment: it is the reason no deep
        copy is needed, and pandas is what enforces it.
        """
        ts = baseTs(np.arange(5.0), np.arange(5) / 10.0)
        with pytest.raises(TypeError):
            ts.name = ['not', 'hashable']


# --------------------------------------------------------------------------
# Cause B, group 2: the self-mutating re-initialisation sites
# --------------------------------------------------------------------------

#: Arguments for every baseTs-owned method that takes `inplace`. The *set* of
#: methods is discovered by reflection (see
#: test_every_inplace_method_is_classified); only the arguments are written by
#: hand, because no reflection can invent a valid cutoff frequency.
INPLACE_ARGS = {
    'abs': (), 'apply_function': (lambda d: d * 2,), 'bandpass_at': (),
    'bandpass_filter': (1.0, 8.0), 'butterpass_at': (1.0, 8.0), 'center': (),
    'dediff_ts': (), 'detrend': (), 'diff_ts': (), 'filter_outliers': (),
    'gauss_filter': (), 'highpass_at': (1.0,), 'highpass_filter': (1.0,),
    'interp_to_uniform_grid': (), 'interpolate_gaps': (),
    'interpto_hz': (20.0,), 'interpto_samples': (150,), 'lowess_detrend': (),
    'lowpass_at': (8.0,), 'lowpass_filter': (8.0,), 'normalize_range': (),
    'notch_at': (5.0,), 'notch_filter': (5.0,), 'remove_outliers': (),
    'rolling_max': (3,), 'rolling_mean': (3,), 'rolling_median': (3,),
    'rolling_min': (3,), 'rolling_std': (3,), 'scale': (2.0,),
    'set_indices_to_nan_and_interpolate': ([2, 3],), 'sg_filter': (),
    'shift_time': (2,), 'time_slice': (), 'trimto_timepoints': (),
    'zscale': (),
}

#: Methods that cannot be exercised because they are broken on `main`,
#: independently of this change. Named with their issue so the exclusion is
#: an accounted-for gap rather than a silent skip.
INPLACE_KNOWN_BROKEN = {
    # interpolate_missing(inplace=True) passes inplace= to a helper that
    # returns None, then reads `.data` off it - dead from introduction, on
    # both pandas majors, with and without NaNs in the data.
    'interpolate_missing': 'filed separately: dead inplace branch',
}


#: The classes in this package that may define an `inplace=` method. Both,
#: not just `baseTs`: a filter keyed on the literal name 'baseTs' cannot see a
#: method defined one class up on `TimeSeriesData`, which is the same object
#: with the same re-initialisation hazard. A guard whose whole purpose is to
#: notice a site nobody enumerated must not be scoped by a name someone typed.
OUR_CLASS_NAMES = frozenset({'baseTs', 'TimeSeriesData'})

_NESTED_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def _calls_in_own_scope(node):
    """Yield the `ast.Call` nodes belonging to `node` itself.

    A flat `ast.walk` descends into nested functions and classes, so a
    perfectly ordinary `super().__init__()` inside a nested class's own
    `__init__` was attributed to the *enclosing* method and reported as a
    re-initialisation site. Nothing in this package nests a class inside a
    method today, so the guard would have failed the suite on correct code
    the first time someone did.
    """
    for child in ast.iter_child_nodes(node):
        if isinstance(child, _NESTED_SCOPES):
            continue
        if isinstance(child, ast.Call):
            yield child
        yield from _calls_in_own_scope(child)


def basets_owned_inplace_methods():
    """Every public method this package defines that takes `inplace`.

    Restricted to methods we define. The ones inherited from pandas
    (`dropna`, `fillna`, `sort_values`, ...) route through `_update_inplace`,
    which swaps `_mgr` and leaves the identity fields alone - measured as
    already correct, and pandas' responsibility rather than ours.
    """
    found = {}
    for name, function in inspect.getmembers(baseTs,
                                             predicate=inspect.isfunction):
        if name.startswith('_'):
            continue
        try:
            signature = inspect.signature(function)
        except (ValueError, TypeError):
            continue
        if 'inplace' not in signature.parameters:
            continue
        if function.__qualname__.split('.')[0] not in OUR_CLASS_NAMES:
            continue
        found[name] = function
    return found


class TestInplaceMethodsPreserveIdentity:
    """`inplace=True` mutates the object; it must not reset its identity.

    This is the check that closes the hole revision 1 of the design left:
    the three `pd.Series.__init__` sites re-initialise `self`, and pandas'
    own `__init__` resets `name`, `attrs` and `flags` to defaults. Adding
    `_name` to `_metadata` cannot help here, because these sites run no
    metadata loop at all.
    """

    def test_every_inplace_method_is_classified(self):
        """A new `inplace=` method fails here until someone classifies it.

        The point of deriving the set rather than listing it. A hand-written
        table cannot fail for a path missing from the table, which is
        precisely how `interpolate_gaps(inplace=True)` and
        `shift_time(inplace=True)` survived the first pass over this bug.
        """
        discovered = set(basets_owned_inplace_methods())
        classified = set(INPLACE_ARGS) | set(INPLACE_KNOWN_BROKEN)
        assert discovered == classified, (
            "a baseTs method taking `inplace` was added or removed; give it "
            "arguments in INPLACE_ARGS or record it in INPLACE_KNOWN_BROKEN"
        )

    @pytest.mark.parametrize("method_name", sorted(INPLACE_ARGS))
    def test_inplace_call_preserves_identity(self, method_name):
        ts = seeded()
        getattr(ts, method_name)(*INPLACE_ARGS[method_name], inplace=True)
        assert identity_of(ts) == SEEDED_IDENTITY

    @pytest.mark.parametrize("method_name", sorted(INPLACE_ARGS))
    def test_inplace_call_preserves_the_rest_of_the_metadata(self,
                                                             method_name):
        """The identity fix must not cost what already worked.

        These survived a re-init only because they live in the instance
        __dict__, which `pd.Series.__init__` does not touch. Routing the
        re-init through one primitive that snapshots and restores must keep
        them surviving - by mechanism now rather than by accident.
        """
        ts = seeded()
        ts.is_filtered = True
        getattr(ts, method_name)(*INPLACE_ARGS[method_name], inplace=True)
        assert ts.signal_name == "SIG"
        assert ts.is_filtered is True
        assert isinstance(ts.history, list)


class TestReinitHasOneDoor:
    """`super(TimeSeriesData, self).__init__` may appear in exactly one place.

    A source-level assertion, because the failure mode is someone writing a
    *new* call rather than misusing an existing one - there is no runtime
    moment at which a not-yet-written site can be observed. It is the same
    reasoning as #27's `_metadata` census: pin the shape of the code, not
    just its behaviour.
    """

    @staticmethod
    def _reinit_call_sites():
        """Functions in core.py that re-initialise self through pandas.

        Parsed, not grepped. A substring scan matched this rule's own
        explanatory comment in `_adopt_data_inplace`, reporting the
        docstring that documents the invariant as a violation of it - the
        instrument has to distinguish a call from a mention.

        `inspect.getsourcefile` rather than `import baseTs.core`: the module
        and the class share the name `baseTs`, so importing the module inside
        a test shadows the class it needs.
        """
        tree = ast.parse(pathlib.Path(inspect.getsourcefile(baseTs)).read_text())
        sites = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            # By where the call is, not by how `super` is spelled. An earlier
            # version required the two-argument form, so a zero-argument
            # `super().__init__(...)` in an ordinary method slipped past -
            # and at runtime the two are equivalent, both re-initialising a
            # live object and resetting name, attrs and flags. What actually
            # distinguishes a legitimate call is that it is a constructor
            # chaining to its base, which is to say it sits in `__init__`.
            if node.name == '__init__':
                continue
            for inner in _calls_in_own_scope(node):
                if (isinstance(inner.func, ast.Attribute)
                        and inner.func.attr == '__init__'
                        and isinstance(inner.func.value, ast.Call)
                        and isinstance(inner.func.value.func, ast.Name)
                        and inner.func.value.func.id == 'super'):
                    sites.append((node.name, inner.lineno))
        return sites

    def test_core_reinitialises_only_inside_the_primitive(self):
        sites = self._reinit_call_sites()
        assert [name for name, _ in sites] == ['_adopt_data_inplace'], (
            f"re-initialising `self` through pandas resets name/attrs/flags; "
            f"route it through baseTs._adopt_data_inplace. Found: {sites}"
        )

    def test_a_nested_class_constructor_is_not_a_reinit_site(self):
        """The scan must attribute a call to its *nearest* enclosing function.

        A flat `ast.walk` descends into nested scopes, so an ordinary
        `super().__init__()` in a nested class's own `__init__` was blamed on
        the enclosing method. Nothing in the package nests a class in a method
        today, so the guard would have failed on correct code the first time
        someone did.
        """
        source = (
            "class Foo:\n"
            "    def bar(self):\n"
            "        class Inner:\n"
            "            def __init__(self):\n"
            "                super().__init__()\n"
            "        return Inner()\n"
        )
        tree = ast.parse(source)
        blamed = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name != '__init__'
            for call in _calls_in_own_scope(node)
            if isinstance(call.func, ast.Attribute)
            and call.func.attr == '__init__'
        ]
        assert blamed == []

    def test_the_primitive_is_where_the_scan_says_it_is(self):
        """Guards the scan itself against silently matching nothing.

        An assertion that a list contains only X passes vacuously when the
        list is empty, so a typo in the AST predicate would leave this class
        green while checking nothing at all.
        """
        sites = self._reinit_call_sites()
        assert len(sites) == 1
        source, start = inspect.getsourcelines(baseTs._adopt_data_inplace)
        assert start <= sites[0][1] < start + len(source)


class TestFlagsAssignmentAssumption:
    """Why `_carry_identity` may assign the flag rather than AND it.

    pandas 2.3.3's `__finalize__` assigns; 3.0.5's ANDs with the target's
    existing value. The two agree only while every target is freshly
    constructed, because a fresh target's flag is True. That is an
    assumption about call sites, so it is asserted rather than trusted.
    """

    def test_a_fresh_basets_allows_duplicate_labels(self):
        fresh = baseTs(np.arange(5.0), np.arange(5) / 10.0)
        assert fresh.flags.allows_duplicate_labels is True

    def test_a_restrictive_flag_reaches_a_derived_object(self):
        assert seeded().copy().flags.allows_duplicate_labels is False

    def test_a_duck_typed_source_still_has_its_name_carried(self):
        """`_copy_metadata_from_basetseries` accepts anything with
        `.times`/`.data`, so a source can carry `.name` without the private
        slot. Reading the slot alone dropped such a name silently, where
        pandas' `__finalize__` - the model this follows - reads `name`.
        """
        class _Duck:
            times = np.arange(3) / 10.0
            data = np.arange(3.0)
            name = 'DUCKNAME'
            attrs = {'unit': 'mV'}

        target = baseTs(np.arange(3.0), np.arange(3) / 10.0)

        _carry_identity(target, _Duck())

        assert target.name == 'DUCKNAME'

    def test_a_permissive_source_relaxes_a_restrictive_target(self):
        """Assignment, not AND - the direction only a direct call can reach.

        Written against `_carry_identity` itself rather than through
        `.copy()`. Every real target is freshly constructed and therefore
        permissive, so the guard short-circuits and the assign-vs-AND choice
        is never exercised: the version of this test that went through
        `.copy()` passed with the whole flag mechanism deleted. Pinning a
        helper's contract needs the helper.
        """
        target = seeded()
        target.flags.allows_duplicate_labels = False
        source = seeded()
        source.flags.allows_duplicate_labels = True

        _carry_identity(target, source)

        assert target.flags.allows_duplicate_labels is True

    def test_the_declaration_is_refused_before_anything_is_mutated(self):
        """An operation that cannot keep the declaration must change nothing.

        Checked after the fact, the re-initialisation had already committed
        the new data and index and reset the flag to pandas' default, so a
        caught error left a mutated object with its protection silently off.
        """
        ts = baseTs(np.array([1.0]), times=np.array([0.0]))
        ts.flags.allows_duplicate_labels = False
        before = (ts.values.tolist(), ts.index.tolist(),
                  ts.flags.allows_duplicate_labels)

        with pytest.raises(ValidationError, match="duplicate time labels"):
            ts.data = np.array([1.0, 2.0, 3.0])

        assert (ts.values.tolist(), ts.index.tolist(),
                ts.flags.allows_duplicate_labels) == before


class TestDuplicateLabelRefusal:
    """The restore arm, exercised directly.

    Since the pre-commit check landed, no path through the public API reaches
    this arm: `_adopt_data_inplace` refuses before mutating, and every
    `_carry_identity` target takes its source's index. Mutation testing said
    so plainly - neutering the arm left the whole suite green. An arm nothing
    pins is one a later reader will trust wrongly, so it is tested where it
    lives rather than deleted on the assumption that it can never fire.
    """

    class _RefusingTarget:
        """A stand-in whose flag setter raises what the caller chooses."""

        class _Flags:
            def __init__(self, error):
                self._error = error
                self.allows_duplicate_labels = True

            def __setattr__(self, name, value):
                if name == 'allows_duplicate_labels' and self.__dict__.get(
                        '_error') is not None and value is False:
                    raise self.__dict__['_error']
                object.__setattr__(self, name, value)

        def __init__(self, error, index):
            self.flags = self._Flags(error)
            self.index = index

    def test_a_duplicate_refusal_becomes_a_diagnosable_error(self):
        """Raising pandas' real class, not a look-alike.

        An earlier version of this test synthesised a class merely *named*
        `DuplicateLabelError`, which passed only while the production code
        matched on `type(exc).__name__`. Once that became a real `except`
        clause the impostor sailed straight through - the test had been
        pinning the string, not the behaviour.
        """
        from pandas.errors import DuplicateLabelError

        error = DuplicateLabelError("Index has duplicates.")
        target = self._RefusingTarget(error, pd.Index([5.0, 5.0, 6.0]))

        with pytest.raises(ValidationError) as caught:
            _apply_duplicate_label_declaration(target, False)

        # The labels, so a caller can act; pandas' own message names none.
        assert "[5.0]" in str(caught.value)
        assert caught.value.__cause__ is error

    def test_the_remedy_the_message_names_actually_works(self):
        """An error that names a remedy is code; the remedy must run.

        This repo shipped an error once whose advised cast reproduced the bug
        it reported. Two halves, and the first is what stops this being
        vacuous: assert the message *names* the remedy, then carry it out and
        assert the operation succeeds. Without the first half the test passes
        against any wording at all - including the earlier one that advised
        giving the result a unique index, which no path here accepts.
        """
        ts = baseTs(np.array([1.0]), times=np.array([0.0]))
        ts.flags.allows_duplicate_labels = False

        with pytest.raises(ValidationError) as caught:
            ts.data = np.array([1.0, 2.0, 3.0])
        assert "ts.flags.allows_duplicate_labels = True" in str(caught.value)

        ts.flags.allows_duplicate_labels = True   # exactly what it says
        ts.data = np.array([1.0, 2.0, 3.0])

        assert len(ts) == 3

    def test_the_message_does_not_offer_an_index_the_caller_cannot_give(self):
        """The remedy that was there before, and why it was wrong.

        `ts.data = ...`, `interpolate_gaps` and `shift_time` all derive the
        result's index; none takes one from the caller. Advice to "give the
        result a unique index" therefore named an action with no parameter
        behind it.
        """
        ts = baseTs(np.array([1.0]), times=np.array([0.0]))
        ts.flags.allows_duplicate_labels = False

        with pytest.raises(ValidationError) as caught:
            ts.data = np.array([1.0, 2.0, 3.0])

        assert "unique index" not in str(caught.value)

    def test_the_message_stays_bounded_for_a_large_index(self):
        """A diagnosis must not become the payload.

        Naming every duplicated label built an 889,108-character exception
        from 100,000 duplicated pairs. This repo already has `_describe` for
        exactly that failure, after a 200k-element list produced a 1.4 MB
        message.
        """
        index = pd.Index(np.repeat(np.arange(50_000.0), 2))

        with pytest.raises(ValidationError) as caught:
            _refuse_undeclarable_index(False, index)

        assert len(str(caught.value)) < 500
        assert "more" in str(caught.value)

    def test_a_small_index_still_names_its_labels(self):
        """Bounding the message must not stop it being useful."""
        with pytest.raises(ValidationError) as caught:
            _refuse_undeclarable_index(False, pd.Index([7.0, 7.0, 8.0]))

        assert "7.0" in str(caught.value)
        assert "more" not in str(caught.value)

    def test_a_one_shot_index_is_not_consumed_by_the_check(self):
        """The check must hand back what it built, not drain the caller's.

        Building a `pd.Index` from a generator exhausts it, so a version that
        checked one object and let the caller reuse the original turned a
        working call into "Length of values (3) does not match length of
        index (0)".
        """
        ts = seeded(n=3, rate=1.0)
        ts.flags.allows_duplicate_labels = False

        ts._adopt_data_inplace(np.array([1.0, 2.0, 3.0]),
                               iter([10.0, 11.0, 12.0]))

        assert ts.index.tolist() == [10.0, 11.0, 12.0]
        assert identity_of(ts) == SEEDED_IDENTITY

    def test_any_other_error_propagates_unchanged(self):
        """Not everything the setter can raise is a duplicate-label refusal.

        Converting every exception into "your index has duplicates" would
        report a wrong diagnosis with total confidence, which is worse than
        the bare error it replaces.
        """
        error = RuntimeError("something else entirely")
        target = self._RefusingTarget(error, pd.Index([1.0, 2.0]))

        with pytest.raises(RuntimeError, match="something else entirely"):
            _apply_duplicate_label_declaration(target, False)


class TestInplaceArithmeticIsUnaffected:
    """`ts += 1` keeps the target's own identity, as stock pandas does.

    Pinned because a reviewer raised `_update_inplace` as a suspected gap and
    it was verified not to be one; without a test the next reviewer re-raises
    it.
    """

    def test_augmented_assignment_keeps_identity(self):
        ts = seeded()
        ts += 1
        assert identity_of(ts) == SEEDED_IDENTITY

    def test_matching_stock_pandas(self):
        s = pd.Series([1.0, 2.0], name="A")
        s += 1
        assert s.name == "A"
