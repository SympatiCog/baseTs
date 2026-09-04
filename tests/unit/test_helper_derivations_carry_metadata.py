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
from baseTs import LowessOutlierFilter as lowess_module
from baseTs import filters as filters_module
from baseTs import utils as utils_module
from baseTs.LowessOutlierFilter import LowessOutlierFilter
from baseTs.utils import add_constant, dediff, diff

N = 200
RATE = 40.0

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
    is vacuous against an object that was reset. The name is assigned after
    construction in mixed case so that a re-minted name (the constructor
    upper-cases its argument, #56) is distinguishable from a carried one.
    """
    times = np.arange(N) / RATE
    data = np.sin(2 * np.pi * 3.0 * times)
    ts = baseTs(data, times)
    ts.signal_name = 'Heart Rate'
    ts.set_timestamp_offset(1.5)
    ts.is_filtered = True
    ts.is_interpolated = True
    ts.is_uniform_grid = True
    ts.is_outlier_filtered = True
    ts.last_process = '_seeded'
    ts.name = 'NAMEVAL'
    ts.attrs['unit'] = 'mV'
    ts.flags.allows_duplicate_labels = False
    return ts


def carried_of(ts):
    fields = {field: getattr(ts, field) for field in CARRIED}
    fields['name'] = ts.name
    fields['attrs'] = dict(ts.attrs)
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

    def test_diff_shortens_and_keeps_the_offset_timestamps(self):
        """The returned timestamps embody the offset; the object reports it."""
        source = seeded()
        result = diff(source)
        np.testing.assert_array_equal(result.times, source.times[1:])
        assert result.ts_offset == 1.5


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
        calls = [
            node for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == 'baseTs'
        ]
        assert not calls, (
            f"{module.__name__} builds a baseTs with the bare constructor at "
            f"lines {[c.lineno for c in calls]}; derive from the source with "
            "_create_new_with_data so its metadata is carried"
        )


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

    def test_inplace_carries_the_metadata(self):
        ts = gappy()
        expected = carried_of(ts)
        expected['last_process'] = '_interp'
        ts.interpolate_missing(inplace=True)
        assert carried_of(ts) == expected
