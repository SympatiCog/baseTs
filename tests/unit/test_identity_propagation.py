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
from baseTs.series import TimeSeriesData, deepcopy_metadata_value

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


def basets_owned_inplace_methods():
    """Every public baseTs-defined method taking `inplace`, by reflection.

    Restricted to methods baseTs itself defines. The ones inherited from
    pandas (`dropna`, `fillna`, `sort_values`, ...) route through
    `_update_inplace`, which swaps `_mgr` and leaves the identity fields
    alone - they were measured as already correct, and they are pandas'
    responsibility rather than ours.
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
        if function.__qualname__.split('.')[0] != 'baseTs':
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
        """Every `super(TimeSeriesData, self).__init__` line in core.py.

        `inspect.getsourcefile` rather than `import baseTs.core`: the module
        and the class share the name `baseTs`, so importing the module inside
        a test shadows the class it needs to look at two lines later.
        """
        source = pathlib.Path(inspect.getsourcefile(baseTs)).read_text()
        return [(number, line.strip())
                for number, line in enumerate(source.splitlines(), 1)
                if 'super(TimeSeriesData, self).__init__' in line]

    def test_core_reinitialises_only_inside_the_primitive(self):
        sites = self._reinit_call_sites()
        assert len(sites) == 1, (
            f"re-initialising `self` through pandas resets name/attrs/flags; "
            f"route it through baseTs._adopt_data_inplace. Found: {sites}"
        )

    def test_the_one_site_is_the_primitive(self):
        line_number = self._reinit_call_sites()[0][0]
        source, start = inspect.getsourcelines(baseTs._adopt_data_inplace)
        assert start <= line_number < start + len(source)


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

    def test_a_permissive_flag_is_not_turned_restrictive(self):
        """The direction an AND would silently break."""
        ts = seeded()
        ts.flags.allows_duplicate_labels = True
        assert ts.copy().flags.allows_duplicate_labels is True


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
