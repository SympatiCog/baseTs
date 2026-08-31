"""Tests for the metadata defaults that must survive a derivation (issue #33).

`history` was made unconditionally a list in PR #26 by normalising in
`_detach_shared_metadata`, the chokepoint `__finalize__` runs. `outlier_filter`
reaches derived objects by the same mechanism but had no such normaliser, so a
`None` propagated forever and every accessor that reads `.config` died on it.

Two routes put the `None` there in the first place, and both are covered:
pandas' `__finalize__`, which copies whatever the parent holds, and
`_copy_metadata_from_basetseries`, whose fallback set every unrecognised name
to `None` outright.
"""
import matplotlib
matplotlib.use("Agg")

import numpy as np
import pytest

from baseTs import baseTs
from baseTs.LowessOutlierFilter import LowessOutlierFilter
from baseTs.series import TimeSeriesData


class _DuckSeries:
    """The shape `TimeSeriesData.__init__` treats as a baseTs to convert from.

    Anything with `.times` and `.data` takes that branch, so a source carrying
    none of the metadata reaches `_copy_metadata_from_basetseries` and every
    name falls through to its default arm.
    """

    def __init__(self):
        self.times = np.arange(10) / 10.0
        self.data = np.arange(10.0)


def _cleared_filter():
    """A series whose filter has been cleared - the state issue #33 reports."""
    ts = baseTs(np.arange(10.0), np.arange(10) / 10.0, signal_name="sig")
    ts.outlier_filter = None
    return ts


class TestOutlierFilterSurvivesDerivation:
    """"outlier_filter is always a filter" must hold on every derived object.

    Without it `get_outlier_filter_params`, `info` and `filter_outliers` all
    raise `AttributeError: 'NoneType' object has no attribute 'config'` on an
    object that never chose to be in that state - it inherited it.
    """

    def test_finalize_restores_a_filter(self):
        """__finalize__ copies the parent's None; the chokepoint must fix it."""
        assert isinstance(_cleared_filter().iloc[:5].outlier_filter,
                          LowessOutlierFilter)

    def test_copy_deep_restores_a_filter(self):
        assert isinstance(_cleared_filter().copy().outlier_filter,
                          LowessOutlierFilter)

    def test_copy_shallow_restores_a_filter(self):
        assert isinstance(_cleared_filter().copy(deep=False).outlier_filter,
                          LowessOutlierFilter)

    def test_create_new_with_data_restores_a_filter(self):
        """zscale() routes through _create_new_with_data, not __finalize__."""
        assert isinstance(_cleared_filter().zscale().outlier_filter,
                          LowessOutlierFilter)

    def test_derived_params_accessor_works(self):
        params = _cleared_filter().iloc[:5].get_outlier_filter_params()
        assert isinstance(params, dict)
        assert "frac" in params

    def test_derived_info_works(self, capsys):
        """info() reads outlier_filter.config to print the filter block."""
        _cleared_filter().iloc[:5].info()
        assert "History:" in capsys.readouterr().out

    def test_derived_filter_outliers_works(self):
        """The filter itself is read off the object, so it died here too.

        Long enough for the default frac to give LOWESS a usable window - a
        short slice raises on the window size before it can reach the filter.
        """
        ts = baseTs(np.sin(np.arange(400) / 20.0), np.arange(400) / 10.0)
        ts.outlier_filter = None
        out = ts.iloc[:200].filter_outliers(inplace=False)
        assert len(out) == 200

    def test_a_hand_cleared_object_is_not_healed_in_place(self):
        """The deliberate boundary of a chokepoint fix, pinned so it is visible.

        _detach_shared_metadata runs on derivation, never on the object you
        mutate, so clearing the attribute yourself leaves that object broken
        until something derives from it. What the fix guarantees is that the
        None stops *propagating* - no object inherits a state it never chose.
        Closing the in-place half would take a normalising property, the shape
        `freq` and `lowess_fit` use.
        """
        with pytest.raises(AttributeError):
            _cleared_filter().get_outlier_filter_params()


class TestOutlierFilterDefaultAtConstruction:
    """The other route to a None: the metadata-copy fallback in series.py.

    `_copy_metadata_from_basetseries` gives history, the flags and the string
    names real defaults when the source has none, then sets everything else -
    `outlier_filter` included - to None. baseTs' own __init__ re-guards it, so
    only a TimeSeriesData built this way keeps the None, and every object
    derived from it inherits one.
    """

    def test_duck_typed_source_gets_a_filter(self):
        assert isinstance(TimeSeriesData(_DuckSeries()).outlier_filter,
                          LowessOutlierFilter)

    def test_object_derived_from_a_duck_typed_source_gets_a_filter(self):
        derived = TimeSeriesData(_DuckSeries()).iloc[:5]
        assert isinstance(derived.outlier_filter, LowessOutlierFilter)


class TestLabelMetadataSurvivesDerivation:
    """"signal_name and last_process are always strings" - same defect class.

    Issue #33 asks for these two to be reviewed alongside outlier_filter, and
    they have the same hole with a louder symptom: plotting builds its labels
    with `ts.signal_name + " " + ts.last_process`, so a propagated None raises
    TypeError from matplotlib's caller rather than AttributeError.
    """

    @staticmethod
    def _labelled(signal_name, last_process):
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        ts.signal_name = signal_name
        ts.last_process = last_process
        return ts

    DERIVATIONS = [
        pytest.param(lambda ts: ts.iloc[:5], id="finalize"),
        pytest.param(lambda ts: ts.copy(), id="copy_deep"),
        pytest.param(lambda ts: ts.copy(deep=False), id="copy_shallow"),
        pytest.param(lambda ts: ts.zscale(), id="create_new_with_data"),
    ]

    # zscale() records itself in last_process, as every processing method does,
    # so it can say nothing about what the parent's value would have become.
    # It stays in the signal_name cases, where it is the only path that routes
    # the name back through the constructor.
    LAST_PROCESS_DERIVATIONS = DERIVATIONS[:-1]

    @pytest.mark.parametrize("derive", DERIVATIONS)
    def test_none_signal_name_becomes_empty(self, derive):
        assert derive(self._labelled(None, "")).signal_name == ""

    @pytest.mark.parametrize("derive", LAST_PROCESS_DERIVATIONS)
    def test_none_last_process_becomes_empty(self, derive):
        assert derive(self._labelled("sig", None)).last_process == ""

    @pytest.mark.parametrize("derive", DERIVATIONS)
    def test_non_string_signal_name_is_coerced(self, derive):
        """A number is as fatal to `name + " " + process` as a None is.

        On the copy(deep=True) path it was fatal one step earlier: the name
        goes back through the constructor, which called `.upper()` on it.
        """
        assert derive(self._labelled(12, "")).signal_name == "12"

    @pytest.mark.parametrize("derive", LAST_PROCESS_DERIVATIONS)
    def test_non_string_last_process_is_coerced(self, derive):
        assert derive(self._labelled("sig", 3.5)).last_process == "3.5"

    def test_plotting_a_derived_object_does_not_raise(self):
        """The live crash: TypeError: unsupported operand 'NoneType' + 'str'."""
        self._labelled(None, None).iloc[:5].plot()

    @pytest.mark.parametrize("derive", DERIVATIONS)
    def test_a_real_signal_name_reaches_the_derived_object_unchanged(self, derive):
        """Restoring a default must not rewrite a name someone chose.

        Deliberately already upper-case: _create_new_with_data passes the name
        back through the constructor, which upper-cases it, so a mixed-case
        name is changed on that path alone. That is pre-existing and separate
        from this fix - asserting it here would only hide which of the two
        rewrote the name.
        """
        assert derive(self._labelled("HEART RATE", "")).signal_name == "HEART RATE"

    @pytest.mark.parametrize("derive", LAST_PROCESS_DERIVATIONS)
    def test_a_real_last_process_reaches_the_derived_object_unchanged(self, derive):
        assert derive(self._labelled("sig", "_lowpass")).last_process == "_lowpass"


class TestLabelMetadataAtConstruction:
    """The constructor kwargs are a door of their own, and one was left open.

    `signal_name` reaches TimeSeriesData.__init__ and is normalised there.
    `last_process` is assigned straight onto the object by baseTs.__init__,
    so a caller who passed a supported keyword got back an object that could
    not be plotted - nothing was mutated afterwards, so this is not the
    "does not heal in place" boundary, it is an unnormalised entry point.
    """

    @staticmethod
    def _constructed(**kwargs):
        return baseTs(np.arange(10.0), np.arange(10) / 10.0, **kwargs)

    def test_none_last_process_kwarg_becomes_empty(self):
        assert self._constructed(last_process=None).last_process == ""

    def test_non_string_last_process_kwarg_is_coerced(self):
        assert self._constructed(last_process=12).last_process == "12"

    def test_plotting_what_the_constructor_returned_does_not_raise(self):
        """TypeError: can only concatenate str (not "NoneType") to str."""
        self._constructed(signal_name="hr", last_process=None).plot()

    def test_none_signal_name_kwarg_becomes_empty(self):
        """The sibling door, already closed - here so the pair stays closed."""
        assert self._constructed(signal_name=None).signal_name == ""

    def test_a_real_last_process_kwarg_is_kept(self):
        assert self._constructed(last_process="_lowpass").last_process == "_lowpass"


class TestFlagDefaultsAtConstruction:
    """`is_outlier_filtered` is a flag, and the fallback left it None.

    The defaulting arm in _copy_metadata_from_basetseries lists three of the
    four boolean flags, so this one fell through to the bare `else` and landed
    as None on a source carrying no metadata - then propagated, since nothing
    downstream normalises it. `assert ts.is_outlier_filtered is False` is an
    assertion the suite already makes elsewhere.
    """

    BOOLEAN_FLAGS = ['is_filtered', 'is_interpolated', 'is_uniform_grid',
                     'is_outlier_filtered', 'has_timestamp_offset']

    @pytest.mark.parametrize("flag", BOOLEAN_FLAGS)
    def test_duck_typed_source_gets_a_boolean(self, flag):
        assert getattr(TimeSeriesData(_DuckSeries()), flag) is False

    @pytest.mark.parametrize("flag", BOOLEAN_FLAGS)
    def test_derived_object_inherits_a_boolean(self, flag):
        assert getattr(TimeSeriesData(_DuckSeries()).iloc[:5], flag) is False


class TestAConfiguredFilterIsNotReplaced:
    """The normaliser must restore a default, never impose one.

    A fix that assigned unconditionally would pass every test above while
    silently resetting the parameters of anyone who had set them.

    This class passes on `main` as well, and that is not a defect in it: a
    configured filter always survived a derivation, because pandas passed the
    reference through untouched. It is here as the guard on the *new* code -
    drop the `is None` from `_detach_shared_metadata` and these four are the
    only tests in this file that fail. Read it as a mutation guard, never as
    evidence that the branch enabled anything.
    """

    @staticmethod
    def _configured():
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        ts.set_outlier_filter(frac=0.42)
        return ts

    @pytest.mark.parametrize("derive", [
        pytest.param(lambda ts: ts.iloc[:5], id="finalize"),
        pytest.param(lambda ts: ts.copy(), id="copy_deep"),
        pytest.param(lambda ts: ts.copy(deep=False), id="copy_shallow"),
        pytest.param(lambda ts: ts.zscale(), id="create_new_with_data"),
    ])
    def test_configured_parameters_survive(self, derive):
        assert derive(self._configured()).get_outlier_filter_params()["frac"] == 0.42
