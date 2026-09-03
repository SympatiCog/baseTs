"""Tests for #40: lowess_fit and outlier_indices on an object whose values changed.

#20 made both fields read as None when the *index* they were computed against
is no longer the object's index. This is the complement: an operation that
replaces the *values* on an unchanged index carried the fit onto data it does
not describe, and nothing read as stale. The positional slot now holds
`(value, index, values_snapshot)` and the getter checks both.

Same shape as #20's suite, on the other axis. The discriminating tests are
the ones that KEEP the fit: a rule keyed on "a method was called" rather than
"the values changed" would fail them.
"""

import copy as copy_module
import pickle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from baseTs import baseTs  # noqa: E402


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def _spiked(n: int = 200):
    t = np.linspace(0, 10, n)
    d = np.sin(t)
    d[123] += 6.0
    return d, t


@pytest.fixture
def filtered():
    """A filtered series carrying a real fit and a real outlier record."""
    d, t = _spiked()
    ts = baseTs(d, t, signal_name="sig")
    ts.set_outlier_filter(frac=0.2)
    ts.filter_outliers(inplace=True)
    assert ts.lowess_fit is not None and len(ts.lowess_fit) == 200
    assert ts.outlier_indices
    assert not np.isnan(np.asarray(ts.data, float)).any(), (
        "the fixture assumes the filter interpolated its own rejection"
    )
    return ts


@pytest.fixture
def gapped():
    """Filtered, with a pre-existing NaN the filter leaves alone (#36)."""
    d, t = _spiked()
    d[50] = np.nan
    ts = baseTs(d, t, signal_name="sig")
    ts.set_outlier_filter(frac=0.2)
    ts.filter_outliers(inplace=True)
    assert np.isnan(np.asarray(ts.data, float)[50])
    assert ts.lowess_fit is not None
    return ts


def _values(ts):
    return np.asarray(ts.data, dtype=float)


NOISE = np.random.default_rng(0).standard_normal(200)


# --------------------------------------------------------------------------
# The issue's reproduction
# --------------------------------------------------------------------------

class TestTheIssue:

    def test_replacing_the_values_on_an_unchanged_index_drops_both(self, filtered):
        before_index = filtered.index.copy()

        filtered.data = NOISE

        assert filtered.index.equals(before_index), "this is the values rule, not #20's"
        assert filtered.lowess_fit is None
        assert filtered.outlier_indices is None

    def test_the_stale_fit_is_not_drawn(self, filtered):
        """qc_plot gates the fit trace on lowess_fit; a stale one must not appear."""
        from baseTs.plotting import qc_plot

        filtered.data = NOISE
        _, ax = plt.subplots()
        qc_plot(filtered, _values(filtered), ax=ax)
        labels = [line.get_label() for line in ax.get_lines()]
        assert "Lowess Fit" not in labels


# --------------------------------------------------------------------------
# Derivations: the values decide, not the method
# --------------------------------------------------------------------------

VALUE_CHANGING = {
    "sg_filter": lambda ts: ts.sg_filter(),
    "detrend_linear": lambda ts: ts.detrend("linear"),
    "lowpass_filter": lambda ts: ts.lowpass_filter(1.0),
    "zscale": lambda ts: ts.zscale(),
    "apply_function_abs": lambda ts: ts.apply_function(np.abs),
    "times_two": lambda ts: ts * 2.0,
    "rolling_5_mean": lambda ts: ts.rolling(5).mean(),
    "astype_float32": lambda ts: ts.astype(np.float32),
}

VALUE_PRESERVING = {
    "plus_zero": lambda ts: ts + 0.0,
    "copy": lambda ts: ts.copy(),
    "rolling_1_mean": lambda ts: ts.rolling(1).mean(),
    "clip_inside_range": lambda ts: ts.clip(-1.0, 1.0),
    "fillna_without_gaps": lambda ts: ts.fillna(0.0),
    "interpolate_gaps_without_gaps": lambda ts: ts.interpolate_gaps(),
    "apply_function_identity": lambda ts: ts.apply_function(lambda x: x),
}


class TestValueChangingDerivationsDropBoth:

    @pytest.mark.parametrize("derive", VALUE_CHANGING.values(), ids=VALUE_CHANGING.keys())
    def test_drops_both(self, filtered, derive):
        result = derive(filtered)

        assert result.index.equals(filtered.index), "the index rule must not be what fires"
        assert not np.array_equal(_values(result), _values(filtered), equal_nan=True), (
            "this operation must change the values for the test to mean anything"
        )
        assert result.lowess_fit is None
        assert result.outlier_indices is None

    @pytest.mark.parametrize("derive", VALUE_CHANGING.values(), ids=VALUE_CHANGING.keys())
    def test_the_source_is_untouched(self, filtered, derive):
        derive(filtered)
        assert filtered.lowess_fit is not None
        assert filtered.outlier_indices is not None

    def test_the_slot_is_released_not_just_unreadable(self, filtered):
        """Memory: a stale slot would pin the parent's fit and snapshot."""
        assert filtered.sg_filter()._lowess_fit is None
        assert filtered.sg_filter()._outlier_indices is None


class TestValuePreservingDerivationsKeepBoth:
    """The discriminating half: same index, same values, a method was called."""

    @pytest.mark.parametrize("derive", VALUE_PRESERVING.values(), ids=VALUE_PRESERVING.keys())
    def test_keeps_both(self, filtered, derive):
        result = derive(filtered)

        assert result.index.equals(filtered.index)
        assert np.array_equal(_values(result), _values(filtered), equal_nan=True)
        assert result.lowess_fit is not None
        assert np.array_equal(result.lowess_fit, filtered.lowess_fit)
        assert result.outlier_indices == filtered.outlier_indices

    def test_a_derivation_of_gapped_data_keeps_both(self, gapped):
        """NaN in the same place compares equal to itself."""
        assert gapped.copy().lowess_fit is not None
        assert (gapped + 0.0).outlier_indices is not None


# --------------------------------------------------------------------------
# Doors that pass through nothing this package defines
# --------------------------------------------------------------------------

class TestInPlaceValueWrites:

    def test_iloc_assignment_drops_both(self, filtered):
        filtered.iloc[3] = 99.0
        assert filtered.lowess_fit is None
        assert filtered.outlier_indices is None

    def test_label_assignment_drops_both(self, filtered):
        filtered[filtered.index[4]] = 99.0
        assert filtered.lowess_fit is None
        assert filtered.outlier_indices is None

    def test_a_write_through_the_values_view_drops_both(self, filtered):
        """Open on pandas 2.x; copy-on-write closes it on 3.x."""
        try:
            filtered.values[:] = 0.0
        except ValueError as exc:
            pytest.skip(f"pandas closed this door itself: {exc}")
        assert filtered.lowess_fit is None
        assert filtered.outlier_indices is None

    def test_augmented_scalar_arithmetic_drops_both(self, filtered):
        filtered += 1.0
        assert filtered.lowess_fit is None
        assert filtered.outlier_indices is None

    def test_augmented_arithmetic_that_changes_nothing_keeps_both(self, filtered):
        filtered += 0.0
        assert filtered.lowess_fit is not None
        assert filtered.outlier_indices is not None

    def test_fillna_inplace_on_gapped_data_drops_both(self, gapped):
        gapped.fillna(0.0, inplace=True)
        assert gapped.lowess_fit is None
        assert gapped.outlier_indices is None

    def test_interpolate_gaps_inplace_on_gapped_data_drops_both(self, gapped):
        gapped.interpolate_gaps(inplace=True)
        assert gapped.lowess_fit is None
        assert gapped.outlier_indices is None

    def test_assigning_equal_values_keeps_both(self, filtered):
        filtered.data = _values(filtered).copy()
        assert filtered.lowess_fit is not None
        assert filtered.outlier_indices is not None


# --------------------------------------------------------------------------
# Producers: the pairing is what they leave behind
# --------------------------------------------------------------------------

class TestProducersLeaveAReadablePairing:
    """Both producers assign the data first and the slot second.

    That ordering is now load-bearing. A producer that stamped before writing
    the data would hand back None; these pin that neither does.
    """

    @pytest.mark.parametrize("inplace", [False, True])
    def test_filter_outliers_leaves_a_readable_fit(self, inplace):
        d, t = _spiked()
        ts = baseTs(d, t)
        ts.set_outlier_filter(frac=0.2)
        out = ts.filter_outliers(inplace=inplace)
        assert out.lowess_fit is not None
        assert out.outlier_indices

    @pytest.mark.parametrize("inplace", [False, True])
    def test_lowess_detrend_leaves_a_readable_fit(self, inplace):
        d, t = _spiked()
        out = baseTs(d, t).lowess_detrend(frac=0.25, inplace=inplace)
        assert out.lowess_fit is not None

    @pytest.mark.parametrize("inplace", [False, True])
    def test_lowess_detrend_keeps_the_outlier_record_it_promises(self, filtered, inplace):
        """Its docstring says outlier_indices is left alone; detrending changes
        the values, so keeping that promise means re-stamping the positions."""
        before = list(filtered.outlier_indices)
        out = filtered.lowess_detrend(frac=0.25, inplace=inplace)
        assert out.outlier_indices == before

    def test_lowess_detrend_does_not_share_the_outlier_list(self, filtered):
        out = filtered.lowess_detrend(frac=0.25, inplace=False)
        out.outlier_indices.append(9999)
        assert 9999 not in filtered.outlier_indices

    def test_lowess_detrend_of_an_unfiltered_source_has_no_positions(self):
        d, t = _spiked()
        assert baseTs(d, t).lowess_detrend(frac=0.25).outlier_indices is None

    def test_the_qc_plot_fit_is_stamped_against_the_data_it_is_drawn_over(self):
        d, t = _spiked()
        ts = baseTs(d, t)
        ts.set_outlier_filter(frac=0.2)
        _, ax = plt.subplots()
        ts.filter_outliers(qcplot=True, inplace=False, ax=ax)
        labels = [line.get_label() for line in ax.get_lines()]
        assert "Lowess Fit" in labels


# --------------------------------------------------------------------------
# The stamp itself
# --------------------------------------------------------------------------

class TestTheStamp:

    def test_the_slot_is_a_triple_ending_in_an_immutable_snapshot(self, filtered):
        value, index, snapshot = filtered._lowess_fit
        assert index is filtered.index or index.equals(filtered.index)
        assert isinstance(snapshot, pd.Index)
        assert np.array_equal(np.asarray(snapshot, float), _values(filtered), equal_nan=True)

    def test_the_snapshot_is_a_copy_not_a_view(self, filtered):
        original_third = _values(filtered)[3]
        snapshot = filtered._lowess_fit[2]

        filtered.iloc[3] = 99.0

        assert snapshot[3] == original_third

    def test_a_stale_read_does_not_clear_the_slot(self, filtered):
        filtered.data = NOISE
        assert filtered.lowess_fit is None
        assert filtered._lowess_fit is not None

    def test_reading_one_field_does_not_change_the_other(self, filtered):
        filtered.data = NOISE
        assert filtered.lowess_fit is None
        assert filtered._outlier_indices is not None
        assert filtered.outlier_indices is None
        assert filtered._lowess_fit is not None

    def test_restoring_the_values_makes_the_fit_readable_again(self, filtered):
        original = _values(filtered).copy()
        filtered.data = NOISE
        assert filtered.lowess_fit is None

        filtered.data = original

        assert filtered.lowess_fit is not None
        assert filtered.outlier_indices is not None

    def test_restoring_the_index_does_not_resurrect_a_fit_for_other_data(self, filtered):
        """The wrinkle #20 documented and #40 removes."""
        old_times = np.asarray(filtered.times).copy()
        filtered.data = NOISE
        filtered.times = old_times + 100.0
        filtered.times = old_times
        assert filtered.lowess_fit is None

    def test_deepcopy_shares_the_snapshot_and_isolates_the_payload(self, filtered):
        twin = copy_module.deepcopy(filtered)
        assert twin._lowess_fit[2] is filtered._lowess_fit[2]
        assert twin._lowess_fit[0] is not filtered._lowess_fit[0]
        assert twin.lowess_fit is not None


class TestValuesEquality:
    """What 'the same values' means, pinned on hand-stamped slots."""

    @staticmethod
    def _stamped(data, dtype=float):
        n = len(data)
        ts = baseTs(np.asarray(data, dtype=dtype), np.arange(n, dtype=float))
        ts.lowess_fit = np.arange(n, dtype=float)
        ts.outlier_indices = [1]
        return ts

    def test_a_float32_cast_of_representable_values_keeps_both(self):
        ts = self._stamped(np.arange(50.0))
        cast = ts.astype(np.float32)
        assert cast.lowess_fit is not None
        assert cast.outlier_indices == [1]

    def test_a_single_changed_sample_drops_both(self):
        ts = self._stamped(np.arange(50.0))
        ts.iloc[7] = 7.5
        assert ts.lowess_fit is None

    def test_nan_in_the_same_place_is_equal(self):
        data = np.arange(50.0)
        data[9] = np.nan
        ts = self._stamped(data)
        assert ts.lowess_fit is not None
        assert ts.copy().lowess_fit is not None

    def test_a_nullable_float_cast_does_not_raise_and_keeps_both(self):
        ts = self._stamped(np.arange(50.0))
        cast = ts.astype("Float64")
        assert cast.lowess_fit is not None

    def test_an_object_cast_does_not_raise_and_keeps_both(self):
        ts = self._stamped(np.arange(50.0))
        cast = ts.astype(object)
        assert cast.lowess_fit is not None

    def test_negative_zero_equals_zero(self):
        ts = self._stamped(np.zeros(10))
        ts.iloc[2] = -0.0
        assert ts.lowess_fit is not None


# --------------------------------------------------------------------------
# Laundering, on the values axis
# --------------------------------------------------------------------------

class TestTheStampIsNotLaunderable:
    """A copy must move the triple, never re-stamp it.

    The discriminating derivation is one that keeps the fit AND has its own
    Index and its own values array: interpolate_gaps() on gap-free data goes
    through _create_new_with_data and does both. sg_filter played this role
    in #20's test and cannot any more - its result correctly reads None.
    """

    def test_a_derived_object_carries_the_parents_snapshot_verbatim(self, filtered):
        parent_index, parent_snapshot = filtered._lowess_fit[1], filtered._lowess_fit[2]
        derived = filtered.interpolate_gaps()

        assert derived.index is not filtered.index, "needs its own Index to mean anything"
        # Identity before any read: a valid read re-stamps the index with the
        # one it just proved equal (see _positional_property), which is
        # correct and would hide a laundered copy here.
        assert derived._lowess_fit[1] is parent_index
        assert derived._lowess_fit[2] is parent_snapshot
        assert derived.lowess_fit is not None, "and the fit is still valid here"

    def test_conversion_carries_the_snapshot_verbatim(self, filtered):
        parent_snapshot = filtered._lowess_fit[2]
        converted = baseTs(filtered)
        assert converted._lowess_fit[2] is parent_snapshot
        assert converted.lowess_fit is not None

    def test_a_valid_fit_derived_onto_new_values_reads_none(self, filtered):
        """The behavioural form: a re-stamping copy would look valid here."""
        assert filtered.lowess_fit is not None
        assert filtered.sg_filter().lowess_fit is None
        assert (filtered * 2.0).lowess_fit is None


# --------------------------------------------------------------------------
# Pickles written before this change
# --------------------------------------------------------------------------

class TestLegacyPickles:
    """Every earlier slot shape loads with the fit readable.

    Built by editing a state dict rather than from a committed blob, as #39's
    tests do: the shape under test is "what the slot holds", and a binary
    fixture would also pin a pickle protocol and a pandas version.
    """

    @staticmethod
    def _revived_with(slot_value, n=200, positions=None):
        d, t = _spiked(n) if n == 200 else (np.arange(n, dtype=float), np.arange(n, dtype=float))
        ts = baseTs(d, t)
        state = dict(ts.__getstate__())
        state['_lowess_fit'] = slot_value
        state['_outlier_indices'] = positions
        revived = object.__new__(baseTs)
        revived.__setstate__(state)
        return revived, ts

    def test_a_pre_20_bare_array_is_completed(self):
        fit = np.arange(200.0)
        revived, source = self._revived_with(fit, positions=[3, 7])

        assert np.array_equal(revived.lowess_fit, fit)
        assert revived.outlier_indices == [3, 7]
        assert len(revived._lowess_fit) == 3
        assert isinstance(revived._lowess_fit[2], pd.Index)

    def test_a_two_sample_bare_array_is_not_mistaken_for_a_pair(self):
        fit = np.array([1.5, 2.5])
        revived, _ = self._revived_with(fit, n=2)
        assert np.array_equal(revived.lowess_fit, fit)

    def test_a_20_era_pair_is_completed_keeping_its_index(self):
        fit = np.arange(200.0)
        _, source = self._revived_with(None)
        revived, _ = self._revived_with((fit, source.index), positions=([3, 7], source.index))

        assert np.array_equal(revived.lowess_fit, fit)
        assert revived.outlier_indices == [3, 7]
        assert revived._lowess_fit[1].equals(source.index)
        assert len(revived._lowess_fit) == 3

    def test_a_20_era_pair_whose_index_does_not_match_stays_unreadable(self):
        fit = np.arange(200.0)
        revived, _ = self._revived_with((fit, pd.Index(np.arange(200.0) + 1.0)))
        assert revived.lowess_fit is None

    def test_none_stays_none(self):
        revived, _ = self._revived_with(None)
        assert revived._lowess_fit is None
        assert revived.lowess_fit is None

    def test_a_completed_fit_obeys_the_rule_from_then_on(self):
        revived, _ = self._revived_with(np.arange(200.0), positions=[3])
        revived.data = NOISE
        assert revived.lowess_fit is None
        assert revived.outlier_indices is None

    def test_a_current_pickle_round_trips_readable(self, filtered):
        back = pickle.loads(pickle.dumps(filtered))
        assert back.lowess_fit is not None
        assert back.outlier_indices == filtered.outlier_indices
        assert len(back._lowess_fit) == 3
