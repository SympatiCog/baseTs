"""A helper that derives a baseTs from a baseTs carries its metadata (#64, #66).

Two defects of one shape, in the free functions that sit beside the class:

* `utils.add_constant`, `utils.diff`, `utils.dediff` and
  `LowessOutlierFilter.filter` built their result with the bare constructor
  from two arrays, so every `_metadata` field came back at its default -
  the name, the flags, `is_filtered`, and a `ts_offset` that the returned
  timestamps still embodied but the object no longer reported (#66).
* `baseTs.interpolate_missing(inplace=True)` forwarded `inplace` to
  `filters.interpolate_missing_values`, which returns `None` on that path,
  and then read `.data` off the `None` - dead from introduction (#64).

The public wrappers `diff_ts()`, `dediff_ts()` and `filter_outliers()` were
never affected: each starts from a copy and borrows only the arrays. The
helpers are importable all the same, and `LowessOutlierFilter` is exported.
"""
import ast
import inspect
import pathlib

import numpy as np
import pytest

from baseTs import baseTs
import baseTs.LowessOutlierFilter as lowess_module
from baseTs import filters as filters_module
from baseTs import utils as utils_module
from baseTs.LowessOutlierFilter import LowessOutlierFilter
from baseTs.utils import add_constant, dediff, diff

N = 200
RATE = 40.0
#: Declared on the seed; the index derives 40.0, so a carried declaration
#: and a re-derived rate cannot be confused.
DECLARED_RATE = 999.0

#: The `_metadata` fields a derivation copies verbatim. The positional slots
#: (`_lowess_fit`, `_outlier_indices`) are excluded because they are
#: *supposed* to read back as None once the values change (#40), and the
#: rate declaration because `diff` changes the index it was declared against.
CARRIED = ('signal_name', 'is_filtered', 'is_interpolated', 'is_uniform_grid',
           'is_outlier_filtered', 'has_timestamp_offset', 'ts_offset',
           'last_process')


def seeded() -> baseTs:
    """A baseTs with every carried field away from its default.

    Every field has to differ from its default, or a "survived" assertion
    is vacuous against an object that was reset. Both labels are assigned
    after construction in mixed case so that a re-minted one (the
    constructor upper-cases `signal_name`, #56) is distinguishable from a
    carried one. The outlier filter is an instance assigned here, compared
    by identity, so a result that re-minted a default filter would differ.
    The rate is declared at a value no derivation would re-derive.
    """
    times = np.arange(N) / RATE
    data = np.sin(2 * np.pi * 3.0 * times)
    ts = baseTs(data, times)
    ts.signal_name = 'Heart Rate'
    ts.outlier_filter = LowessOutlierFilter()   # this instance, not any default
    ts.set_timestamp_offset(1.5)
    ts.is_filtered = True
    ts.is_interpolated = True
    ts.is_uniform_grid = True
    ts.is_outlier_filtered = True
    ts.last_process = '_seeded'
    ts.name = 'NameVal'
    ts.attrs['unit'] = 'mV'
    ts.flags.allows_duplicate_labels = False
    # Last: a declaration expires when the index changes (#38), and
    # set_timestamp_offset above used to shift it (it only records the
    # origin since #100; the order is kept as the rule).
    ts.freq = DECLARED_RATE
    return ts


def carried_of(ts):
    fields = {field: getattr(ts, field) for field in CARRIED}
    fields['name'] = ts.name
    fields['attrs'] = dict(ts.attrs)
    fields['outlier_filter'] = ts.outlier_filter
    fields['allows_duplicate_labels'] = ts.flags.allows_duplicate_labels
    return fields


def lowess_filtered(ts):
    return LowessOutlierFilter().filter(ts, return_lowess=False)[0]


DERIVATIONS = {
    'add_constant': lambda ts: add_constant(ts, 1.0),
    'diff': lambda ts: diff(ts),
    'diff_zeropad': lambda ts: diff(ts, zeropad=True),
    'dediff': lambda ts: dediff(ts),
    'LowessOutlierFilter.filter': lowess_filtered,
}


# --------------------------------------------------------------------------
# #66: the free helpers
# --------------------------------------------------------------------------

class TestHelperDerivationsCarryMetadata:

    @pytest.mark.parametrize("derive", DERIVATIONS.values(),
                             ids=list(DERIVATIONS))
    def test_every_carried_field_reaches_the_result(self, derive):
        source = seeded()
        expected = carried_of(source)
        assert carried_of(derive(source)) == expected

    @pytest.mark.parametrize("derive", DERIVATIONS.values(),
                             ids=list(DERIVATIONS))
    def test_history_is_copied_not_shared(self, derive):
        """The result starts from the source's history and owns its copy.

        Sharing the list is the defect #15 and #35 kept meeting: the next
        `_update_history_and_process` on either object would then append to
        both.
        """
        source = seeded()
        before = list(source.history)
        result = derive(source)
        assert result.history[:len(before)] == before
        assert result.history is not source.history
        result.history.append('touched the result')
        assert source.history == before

    @pytest.mark.parametrize("derive", DERIVATIONS.values(),
                             ids=list(DERIVATIONS))
    def test_result_is_a_basets(self, derive):
        assert isinstance(derive(seeded()), baseTs)

    def test_add_constant_leaves_the_source_alone(self):
        source = seeded()
        before = source.data.copy()
        add_constant(source, 1.0)
        np.testing.assert_array_equal(source.data, before)

    def test_add_constant_inplace_returns_the_same_object(self):
        source = seeded()
        assert add_constant(source, 1.0, inplace=True) is source

    def test_add_constant_inplace_adds_the_constant(self):
        """Pinned because a mutant that skipped the write survived the rest."""
        source = seeded()
        before = source.data.copy()
        add_constant(source, 1.0, inplace=True)
        np.testing.assert_array_equal(source.data, before + 1.0)

    @pytest.mark.parametrize("derive", DERIVATIONS.values(),
                             ids=list(DERIVATIONS))
    def test_attrs_are_not_shared_with_the_source(self, derive):
        """Round 2 (glm) asked; measured false, and pinned so it stays so."""
        source = seeded()
        result = derive(source)
        result.attrs['unit'] = 'V'
        assert source.attrs['unit'] == 'mV'

    @pytest.mark.parametrize("derive", [DERIVATIONS[k] for k in
                             ('add_constant', 'diff_zeropad', 'dediff',
                              'LowessOutlierFilter.filter')],
                             ids=['add_constant', 'diff_zeropad', 'dediff',
                                  'LowessOutlierFilter.filter'])
    def test_a_declared_rate_is_honoured_where_the_index_is_kept(self, derive):
        """The CHANGELOG says so; round 2 (glm) noted nothing pinned it."""
        assert derive(seeded()).freq == DECLARED_RATE

    def test_a_declared_rate_expires_where_diff_changes_the_index(self):
        assert diff(seeded()).freq == pytest.approx(RATE)

    def test_a_helper_that_changes_no_value_keeps_the_positional_slots(self):
        """The #40 rule, as for `ts + 0.0`: readable while index and values
        are the ones they were stamped against."""
        source = seeded()
        source.lowess_fit = np.full(N, 9.0)
        source.outlier_indices = [3]
        result = add_constant(source, 0.0)
        np.testing.assert_array_equal(result.lowess_fit, np.full(N, 9.0))
        assert result.outlier_indices == [3]

    def test_a_helper_that_changes_the_values_drops_the_positional_slots(self):
        source = seeded()
        source.lowess_fit = np.full(N, 9.0)
        source.outlier_indices = [3]
        for result in (add_constant(source, 1.0), diff(source), dediff(source)):
            assert result.lowess_fit is None
            assert result.outlier_indices is None

    def test_diff_shortens_and_keeps_the_offset_timestamps(self):
        """The returned timestamps embody the offset; the object reports it."""
        source = seeded()
        result = diff(source)
        np.testing.assert_array_equal(result.times, source.times[1:])
        assert result.ts_offset == 1.5


class TestTheFilterResultDoesNotInheritPositionalSlots:
    """`lowess_fit` / `outlier_indices` describe the source's samples, not the result's.

    Review round 1 (codex) found the regression: on already-clean data the
    filter changes no value, so the #40 staleness check - which drops a
    positional slot only when the index or the values differ - let the
    source's own fit and outlier list through unchanged. A caller reading
    them off the returned object would take a fit from some earlier run for
    this one. On `main` the bare constructor left both `None`; the wrapper
    `filter_outliers()` stamps its own on the object it builds, and that
    stays the wrapper's job.
    """

    @staticmethod
    def _clean_source_with_stamped_slots():
        source = seeded()
        source.lowess_fit = np.full(N, 999.0)
        source.outlier_indices = [5, 6, 7]
        assert source.lowess_fit is not None       # the stamp is live
        return source

    def test_lowess_fit_is_not_inherited_when_nothing_changed(self):
        source = self._clean_source_with_stamped_slots()
        result = lowess_filtered(source)
        np.testing.assert_array_equal(result.data, source.data)  # the trap
        assert result.lowess_fit is None

    def test_outlier_indices_are_not_inherited_when_nothing_changed(self):
        source = self._clean_source_with_stamped_slots()
        result = lowess_filtered(source)
        np.testing.assert_array_equal(result.data, source.data)  # the trap
        assert result.outlier_indices is None

    def test_the_source_keeps_its_own_slots(self):
        source = self._clean_source_with_stamped_slots()
        lowess_filtered(source)
        assert source.outlier_indices == [5, 6, 7]


def bare_constructor_calls(source: str):
    """Line numbers of every `baseTs(...)` / `<anything>.baseTs(...)` call.

    An aliased import (`from .core import baseTs as B`) or a call through a
    variable is not seen, and cannot be in general; where a helper module
    imports the class it does so under its own name (`utils.py` no longer
    imports it at all), and the pin is calibrated to that. The rule it
    states is "no direct constructor call", not "no way to reach the
    constructor".
    """
    calls = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == 'baseTs':
            calls.append(node.lineno)
        elif isinstance(func, ast.Attribute) and func.attr == 'baseTs':
            calls.append(node.lineno)
    return calls


class TestNoHelperUsesTheBareConstructor:
    """A helper module derives through `_create_new_with_data`, never `baseTs(...)`.

    The rule, pinned at the source rather than as a list of the four sites
    this change fixed: a fifth helper written the old way fails here before
    anyone calls it. Parsed rather than grepped so that a docstring
    mentioning `baseTs(` (the API docs quote several) is not a violation.
    """

    @pytest.mark.parametrize("module", [utils_module, filters_module,
                                        lowess_module],
                             ids=['utils', 'filters', 'LowessOutlierFilter'])
    def test_no_direct_constructor_call(self, module):
        source = pathlib.Path(inspect.getsourcefile(module)).read_text()
        calls = bare_constructor_calls(source)
        assert not calls, (
            f"{module.__name__} builds a baseTs with the bare constructor at "
            f"lines {calls}; derive from the source with "
            "_create_new_with_data so its metadata is carried"
        )

    @pytest.mark.parametrize("snippet", [
        "res = baseTs(x, t)",
        "res = core.baseTs(x, t)",
        "res = baseTs.baseTs(data=x, times=t)",
        "def f(ts):\n    from .core import baseTs\n    return baseTs(ts.data, ts.times)",
    ], ids=['bare', 'module-qualified', 'package-qualified', 'local-import'])
    def test_the_detector_sees_each_direct_spelling(self, snippet):
        """Round 1 (codex + agy): a `Name`-only match missed `core.baseTs(...)`."""
        assert bare_constructor_calls(snippet) == [snippet.count("\n") + 1]

    @pytest.mark.parametrize("snippet", [
        "res = ts._create_new_with_data(x, t)",
        "res = isinstance(data, baseTs)",
        "res = ts.copy()",
    ], ids=['derivation', 'isinstance', 'copy'])
    def test_the_detector_ignores_what_is_not_a_constructor_call(self, snippet):
        assert bare_constructor_calls(snippet) == []


# --------------------------------------------------------------------------
# #64: interpolate_missing(inplace=True)
# --------------------------------------------------------------------------

def gappy() -> baseTs:
    ts = seeded()
    data = ts.data.copy()
    data[[10, 11, 50]] = np.nan
    ts.data = data
    return ts


class TestInterpolateMissingInplace:

    def test_inplace_fills_the_gaps_on_the_object_itself(self):
        ts = gappy()
        ts.interpolate_missing(inplace=True)
        assert not np.isnan(ts.data).any()

    def test_inplace_returns_self(self):
        ts = gappy()
        assert ts.interpolate_missing(inplace=True) is ts

    def test_inplace_and_copy_agree_on_the_values(self):
        ts = gappy()
        copied = ts.interpolate_missing()
        ts.interpolate_missing(inplace=True)
        np.testing.assert_array_equal(ts.data, copied.data)

    def test_inplace_keeps_the_index(self):
        ts = gappy()
        before = ts.times.copy()
        ts.interpolate_missing(inplace=True)
        np.testing.assert_array_equal(ts.times, before)

    def test_inplace_records_the_step(self):
        ts = gappy()
        n_before = len(ts.history)
        ts.interpolate_missing(inplace=True)
        assert ts.last_process == '_interp'
        assert len(ts.history) == n_before + 1

    def test_copy_leaves_the_source_gappy(self):
        ts = gappy()
        ts.interpolate_missing()
        assert np.isnan(ts.data).sum() == 3

    def test_leading_and_trailing_gaps_are_filled_from_the_nearest_sample(self):
        """The docstring's claim; round 2 (glm) noted the tests were interior-only."""
        ts = seeded()
        data = ts.data.copy()
        data[[0, 1, N - 1]] = np.nan
        ts.data = data
        ts.interpolate_missing(inplace=True)
        assert ts.data[0] == ts.data[1] == ts.data[2]
        assert ts.data[N - 1] == ts.data[N - 2]

    def test_inplace_carries_the_metadata(self):
        ts = gappy()
        expected = carried_of(ts)
        expected['last_process'] = '_interp'
        ts.interpolate_missing(inplace=True)
        assert carried_of(ts) == expected
