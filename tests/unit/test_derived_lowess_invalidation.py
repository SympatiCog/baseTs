"""Tests for #20: lowess_fit and outlier_indices on derived objects.

`lowess_fit` is an array of one value per sample and `outlier_indices` holds
*positions* into that same sample sequence. Both describe the object they were
computed against and are meaningless against any other sample sequence, so an
object whose index differs from the one they were computed against must not
carry them.

Reslicing is not the fix. It is only definable for a positional slice; resample,
dropna and sort_values have no meaningful mapping, so a reslicing implementation
would be right on one path and silently wrong on every other. Invalidation is
correct everywhere, and makes the `lowess_fit is not None` guard the plotting
code already has do the right thing on its own.
"""
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from baseTs import baseTs
from baseTs.plotting import plot, qc_plot


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


@pytest.fixture
def filtered():
    """A filtered series carrying a real fit and a real outlier record."""
    t = np.linspace(0, 10, 200)
    d = np.sin(t)
    d[123] += 6.0
    ts = baseTs(d, t, signal_name="sig")
    ts.set_outlier_filter(frac=0.2)
    ts.filter_outliers(inplace=True)
    assert ts.lowess_fit is not None and len(ts.lowess_fit) == 200
    assert ts.outlier_indices
    return ts


class TestInvalidationOnDerivation:
    """A different index means neither attribute describes the object."""

    def test_a_slice_drops_the_lowess_fit(self, filtered):
        assert filtered.iloc[:50].lowess_fit is None

    def test_a_slice_drops_the_outlier_indices(self, filtered):
        assert filtered.iloc[:50].outlier_indices is None

    def test_dropna_drops_both(self, filtered):
        filtered.iloc[10] = np.nan
        cleaned = filtered.dropna()
        assert cleaned.lowess_fit is None
        assert cleaned.outlier_indices is None

    def test_an_interior_permutation_drops_both(self, filtered):
        """Stricter than the `freq` token, deliberately.

        `_freq_token` is (len, first, last) and is airtight for `freq` because
        those are exactly the three inputs the rate derivation reads. These two
        attributes are position-indexed, so a permutation that leaves the token
        untouched still moves every sample they describe.
        """
        from baseTs.series import _freq_token

        order = np.arange(200)
        order[1:-1] = order[1:-1][::-1]
        shuffled = filtered.iloc[order]

        assert _freq_token(shuffled.index) == _freq_token(filtered.index), (
            "this test is only meaningful while the token is unchanged"
        )
        assert shuffled.lowess_fit is None
        assert shuffled.outlier_indices is None

    def test_an_unchanged_index_keeps_both(self, filtered):
        """Invalidation is about the index, not about deriving at all.

        `+ 0.0` rather than `* 2.0`: since #40 the values are checked too,
        so the operation has to leave them alone for this to isolate the
        index rule. `* 2.0` is a drop case in test_data_stamp_invalidation.
        """
        same = filtered + 0.0
        assert same.lowess_fit is not None
        assert len(same.lowess_fit) == len(same)
        assert same.outlier_indices == filtered.outlier_indices

    def test_a_head_of_the_whole_series_keeps_both(self, filtered):
        """The rule is index equality, not "was a slicing method called"."""
        whole = filtered.head(len(filtered))
        assert whole.lowess_fit is not None
        assert whole.outlier_indices is not None

    def test_copy_keeps_both(self, filtered):
        copied = filtered.copy()
        assert copied.lowess_fit is not None
        assert np.array_equal(copied.lowess_fit, filtered.lowess_fit)
        assert copied.outlier_indices == filtered.outlier_indices

    def test_a_rolling_aggregation_keeps_both(self, filtered):
        """rolling() routes through _FinalizingWindow, not __finalize__ directly.

        A window of one leaves every value as it was; a wider window changes
        them and is a drop case in test_data_stamp_invalidation (#40).
        """
        rolled = filtered.rolling(1).mean()
        assert rolled.lowess_fit is not None
        assert rolled.outlier_indices is not None


class TestInvalidationOnInPlaceIndexChange:
    """The index can change without any derivation at all."""

    def test_assigning_new_times_drops_both(self, filtered):
        filtered.times = np.linspace(0, 20, 200)
        assert filtered.lowess_fit is None
        assert filtered.outlier_indices is None

    def test_assigning_the_same_times_keeps_both(self, filtered):
        filtered.times = np.asarray(filtered.times)
        assert filtered.lowess_fit is not None
        assert filtered.outlier_indices is not None

    def test_assigning_a_new_index_directly_drops_both(self, filtered):
        """`.index` is pandas' own setter, and `.times` is not the only door."""
        filtered.index = np.linspace(100, 200, len(filtered))
        assert filtered.lowess_fit is None
        assert filtered.outlier_indices is None

    def test_assigning_the_same_index_directly_keeps_both(self, filtered):
        filtered.index = filtered.index.copy()
        assert filtered.lowess_fit is not None
        assert filtered.outlier_indices is not None

    def test_shift_time_inplace_drops_both(self, filtered):
        """The inplace branch calls pd.Series.__init__ directly, bypassing
        _update_series_data, the times setter and __finalize__ alike."""
        filtered.shift_time(periods=5, inplace=True)
        assert len(filtered) < 200, "the shift must actually drop samples"
        assert filtered.lowess_fit is None
        assert filtered.outlier_indices is None

    def test_assigning_shorter_data_drops_both(self, filtered):
        """The data setter rebuilds the index when the length changes."""
        filtered.data = np.zeros(50)
        assert filtered.lowess_fit is None
        assert filtered.outlier_indices is None

    def test_assigning_same_length_data_keeps_both(self, filtered):
        """Same length keeps the index; equal values keep the fit (#40).

        Assigning zeros here would trip the values rule instead, which is a
        drop case in test_data_stamp_invalidation.
        """
        filtered.data = np.asarray(filtered.data, dtype=float).copy()
        assert filtered.lowess_fit is not None
        assert filtered.outlier_indices is not None


class TestInheritedPandasInplaceMethods:
    """`inplace=True` on an inherited pandas method swaps the block manager.

    pandas routes these through NDFrame._update_inplace, which finalizes only
    the *returned* object - the one it then throws away - and never assigns
    `.index`. None of them is overridden in this repo, so nothing baseTs writes
    is on the path at all; the read-time check catches them because each one
    leaves `self.index` different from the one the fit was stamped against.
    """

    def test_dropna_inplace_drops_both(self, filtered):
        """The reported crash, reachable without any baseTs method at all."""
        filtered.iloc[5] = np.nan
        filtered.dropna(inplace=True)
        assert len(filtered) == 199
        assert filtered.lowess_fit is None
        assert filtered.outlier_indices is None

    def test_qc_plot_after_dropna_inplace_does_not_raise(self, filtered):
        filtered.iloc[5] = np.nan
        filtered.dropna(inplace=True)
        _, ax = plt.subplots()
        qc_plot(filtered, np.asarray(filtered.data, float), filtered.times, ax=ax)
        assert "Lowess Fit" not in [line.get_label() for line in ax.get_lines()]

    def test_sort_values_inplace_drops_both(self, filtered):
        """The silent variant: same length, every position moved."""
        filtered.sort_values(inplace=True)
        assert len(filtered) == 200, "sorting must not change the length"
        assert filtered.lowess_fit is None
        assert filtered.outlier_indices is None

    def test_sort_index_inplace_drops_both(self, filtered):
        filtered.sort_index(ascending=False, inplace=True)
        assert filtered.lowess_fit is None
        assert filtered.outlier_indices is None

    def test_drop_inplace_drops_both(self, filtered):
        filtered.drop(filtered.index[:10], inplace=True)
        assert len(filtered) == 190
        assert filtered.lowess_fit is None
        assert filtered.outlier_indices is None

    @pytest.mark.parametrize(
        "call",
        [
            lambda ts: ts.fillna(0.0, inplace=True),
            lambda ts: ts.clip(-1.0, 1.0, inplace=True),
        ],
        ids=["fillna", "clip"],
    )
    def test_index_preserving_inplace_methods_keep_both(self, filtered, call):
        """These keep the positions, so the index rule must not fire.

        On this fixture they also leave every value alone - there is no NaN
        to fill and nothing outside [-1, 1] to clip - so the values rule
        (#40) does not fire either. The gapped and out-of-range variants are
        drop cases in test_data_stamp_invalidation.
        """
        call(filtered)
        assert filtered.lowess_fit is not None
        assert len(filtered.lowess_fit) == len(filtered)
        assert filtered.outlier_indices is not None


class TestIndexMutationsWithNoHookAtAll:
    """The doors that defeated the write-side design.

    These reach past `__finalize__`, `_update_inplace` and index assignment
    alike - pandas swaps the block manager directly. No write-side hook saw
    them, and no audit of baseTs' own methods could have: `pop` and `del` are
    not overridden here, and enlargement happens inside pandas' indexer.

    Checking on read closes them for free, because each one changes
    `self.index` and the property reads `self.index`.
    """

    def test_setitem_enlargement_drops_both(self, filtered):
        filtered[99.0] = 1.0
        assert len(filtered) == 201
        assert filtered.lowess_fit is None
        assert filtered.outlier_indices is None

    def test_loc_enlargement_drops_both(self, filtered):
        filtered.loc[88.0] = 1.0
        assert len(filtered) == 201
        assert filtered.lowess_fit is None
        assert filtered.outlier_indices is None

    def test_at_enlargement_drops_both(self, filtered):
        filtered.at[77.0] = 1.0
        assert len(filtered) == 201
        assert filtered.lowess_fit is None
        assert filtered.outlier_indices is None

    def test_pop_drops_both(self, filtered):
        filtered.pop(filtered.index[0])
        assert len(filtered) == 199
        assert filtered.lowess_fit is None
        assert filtered.outlier_indices is None

    def test_del_drops_both(self, filtered):
        del filtered[filtered.index[0]]
        assert len(filtered) == 199
        assert filtered.lowess_fit is None
        assert filtered.outlier_indices is None

    def test_interpolate_gaps_time_inplace_drops_both(self):
        """The third `pd.Series.__init__` site, and the one an explicit audit
        for that exact pattern still missed.

        `method='time'` round-trips the float index through a nanosecond
        Timedelta, which is not bit-exact. The drift is sub-microsecond, so the
        length is unchanged and nothing raises - the silent failure mode.
        """
        rng = np.random.default_rng(0)
        t = 1_700_000_000.0 + np.sort(rng.uniform(0, 200, 200))
        d = np.sin(np.linspace(0, 10, 200))
        d[123] += 6.0
        ts = baseTs(d, t)
        ts.set_outlier_filter(frac=0.2)
        ts.filter_outliers(inplace=True)
        before = ts.index.copy()

        ts.interpolate_gaps(method="time", inplace=True)

        assert not ts.index.equals(before), "this test needs the index to drift"
        assert len(ts) == 200, "and needs the length to stay the same"
        assert ts.lowess_fit is None
        assert ts.outlier_indices is None


class TestReadIsPureAndDerivationReleases:
    """Two halves of one contract, neither depending on who read what.

    Reading is a pure function of (stored pair, live index): what a read
    returns never depends on whether an earlier read happened. Clearing on a
    stale read was tried and is worse - release becomes per-attribute and
    observation-dependent, so reading `lowess_fit` while stale drops it and
    leaves `outlier_indices` recoverable, and a later revert brings back
    exactly the one nobody looked at.

    Derivation is the one place a value is destroyed, because a derived object
    whose index never matched never had one.
    """

    def _shifted_away(self, filtered):
        original = filtered.index.copy()
        filtered.times = np.asarray(original) + 100.0
        return original

    def test_both_attributes_read_none_while_the_index_differs(self, filtered):
        self._shifted_away(filtered)
        assert filtered.lowess_fit is None
        assert filtered.outlier_indices is None

    def test_reading_one_attribute_does_not_change_the_other(self, filtered):
        """The asymmetry that clearing-on-read introduced."""
        original = self._shifted_away(filtered)
        assert filtered.lowess_fit is None          # read only one of the two
        filtered.times = np.asarray(original)

        assert (filtered.lowess_fit is None) == (filtered.outlier_indices is None), (
            "both must answer the same way; a read must not privilege one"
        )

    def test_restoring_the_index_makes_the_fit_readable_again(self, filtered):
        """Specified, not accidental.

        Within this property's scope - do the samples still sit where the fit
        says - a restored index is genuinely valid again. It is misleading only
        if the data changed meanwhile, which is #40.
        """
        expected = np.asarray(filtered.lowess_fit).copy()
        original = self._shifted_away(filtered)
        assert filtered.lowess_fit is None

        filtered.times = np.asarray(original)

        assert filtered.index.equals(original), "the revert must actually match"
        assert np.array_equal(filtered.lowess_fit, expected)

    def test_a_derived_object_never_regains_what_it_never_had(self, filtered):
        """The other half: derivation destroys, so a revert cannot undo it."""
        original = self._shifted_away(filtered)
        child = filtered.copy()
        assert child._lowess_fit is None, "derivation must release outright"

        child.times = np.asarray(original)

        assert child.lowess_fit is None
        assert child.outlier_indices is None

    def test_a_stale_slot_is_released_on_derivation(self, filtered):
        """Memory: a slice must not pin the parent's full-length array."""
        assert filtered.iloc[:50]._lowess_fit is None

    def test_a_valid_read_restamps_so_later_reads_are_cheap(self, filtered):
        """Every derived object gets a new Index, so a first read is O(n).

        Re-stamping with the index just proved equal changes no answer and
        lets later reads take Index.equals' identity fast path.
        """
        derived = filtered.copy()
        assert derived.index is not filtered.index, "test needs a distinct Index"

        assert derived.lowess_fit is not None
        assert derived._lowess_fit[1] is derived.index


class TestDeepCopyIndependence:
    """`copy(deep=True)` must hand back arrays the parent does not share.

    Both copy implementations deep-copy a metadata entry only when it is a
    list, dict or ndarray. Moving the slots into `(value, index)` tuples made
    that test fail silently for these two, so a deep copy shared the parent's
    fit - an aliasing bug on the one path whose entire purpose is to avoid it,
    and a regression against the behaviour on main.
    """

    def test_deep_copy_gives_an_independent_lowess_fit(self, filtered):
        copied = filtered.copy(deep=True)
        assert copied.lowess_fit is not filtered.lowess_fit

        copied.lowess_fit[0] = 999.0

        assert filtered.lowess_fit[0] != 999.0

    def test_deep_copy_gives_an_independent_outlier_record(self, filtered):
        copied = filtered.copy(deep=True)
        copied.outlier_indices.append(9999)
        assert 9999 not in filtered.outlier_indices

    def test_deep_copy_keeps_the_values_equal(self, filtered):
        copied = filtered.copy(deep=True)
        assert np.array_equal(copied.lowess_fit, filtered.lowess_fit)
        assert copied.outlier_indices == filtered.outlier_indices

    def test_an_array_valued_outlier_record_is_detached_too(self, filtered):
        """The constructor types this as np.array, so a list check is not enough."""
        filtered.outlier_indices = np.array([3, 4, 5])
        derived = filtered + 0.0
        assert derived.outlier_indices is not filtered.outlier_indices

        derived.outlier_indices[0] = 999

        assert filtered.outlier_indices[0] == 3


class TestTheStampIsNotLaunderable:
    """A copy must move the (value, index) pair, never re-stamp it.

    Any path that copies metadata through the *public* names runs the property
    setter, which stamps with the receiving object's index - turning a stale
    fit into a fresh-looking one. `_create_new_with_data` had exactly that
    shape and had to be switched to the private slots, the same way
    `_freq_declaration` already was. These pin the invariant so a future
    metadata-copying loop cannot quietly reintroduce it.
    """

    def test_metadata_declares_the_private_slots(self):
        from baseTs.series import TimeSeriesData

        assert "_lowess_fit" in TimeSeriesData._metadata
        assert "_outlier_indices" in TimeSeriesData._metadata
        assert "lowess_fit" not in TimeSeriesData._metadata, (
            "declaring the public name makes __finalize__ run the stamping "
            "setter, which re-stamps the parent's fit with the child's index"
        )
        assert "outlier_indices" not in TimeSeriesData._metadata

    def test_a_derived_object_carries_the_parents_stamp_verbatim(self, filtered):
        """The discriminating case for laundering.

        interpolate_gaps routes through _create_new_with_data, which builds a
        *new* Index object for the result, and on gap-free data leaves every
        value alone. If the copy went through the public name, the setter
        would stamp with that new index and the fit would look valid by
        construction. Carrying the parent's own index object is the proof it
        did not. sg_filter played this role before #40; it cannot now, because
        its result changes the values and correctly reads None.
        """
        parent_stamp = filtered._lowess_fit[1]
        derived = filtered.interpolate_gaps()

        assert derived.index is not filtered.index, (
            "this test is only meaningful while the result has its own Index"
        )
        assert derived._lowess_fit[1] is parent_stamp
        assert derived.lowess_fit is not None, "and the fit is still valid here"

    def test_a_stale_slot_is_released_on_derivation(self, filtered):
        """Memory, not correctness: the getter already reads a slice as None.

        Without this the parent's full-length fit would stay alive for as long
        as any slice of it did.
        """
        assert filtered.iloc[:50]._lowess_fit is None

    def test_a_derivation_off_a_valid_fit_onto_a_new_index_reads_none(self, filtered):
        """The behavioural form of the laundering check.

        Starting from a *valid* fit is what makes this discriminating: the
        derived object has a different index, so a copy that went through the
        public name would re-stamp and hand back a fit that looks valid. A
        source that is already stale cannot detect that, because copying None
        onto the target is indistinguishable from doing the right thing.
        """
        assert filtered.lowess_fit is not None, "the source must start valid"
        assert filtered.remove_outliers(method="zscore", threshold=2.0).lowess_fit is None
        assert filtered.shift_time(periods=5).lowess_fit is None


class TestInvalidationThroughCreateNewWithData:
    """_create_new_with_data copies the metadata slots outside pandas' machinery.

    Every non-inplace baseTs method routes through it. It needs no rule of its
    own any more - only the discipline of copying the private slots rather than
    assigning through the properties, which TestTheStampIsNotLaunderable pins.
    """

    def test_remove_outliers_drops_both(self, filtered):
        thinned = filtered.remove_outliers(method="zscore", threshold=2.0)
        assert len(thinned) < len(filtered), "this test needs samples to be dropped"
        assert thinned.lowess_fit is None
        assert thinned.outlier_indices is None

    def test_shift_time_drops_both(self, filtered):
        shifted = filtered.shift_time(periods=5)
        assert not shifted.index.equals(filtered.index)
        assert shifted.lowess_fit is None
        assert shifted.outlier_indices is None

    def test_a_value_preserving_rebuild_keeps_both(self, filtered):
        """Same index and same values, so both still describe the result.

        sg_filter was the operation here before #40; its result now reads
        None because it changes the values, and that is a drop case in
        test_data_stamp_invalidation.
        """
        rebuilt = filtered.interpolate_gaps()
        assert rebuilt.index.equals(filtered.index)
        assert rebuilt.lowess_fit is not None
        assert rebuilt.outlier_indices == filtered.outlier_indices


class TestArithmeticOperators:
    """The operator dunders do not route through __finalize__.

    `__add__` and friends are overridden on TimeSeriesData: they call pandas'
    operator, then throw the finalized result away and rebuild it through
    _wrap_result_as_basets, which copies _metadata by name. So the operators
    need the rule applied explicitly, exactly like _create_new_with_data - and
    they must agree with the flex methods (`.add()`, `.mul()`), which do route
    through __finalize__.
    """

    @pytest.fixture
    def other(self):
        return baseTs(np.cos(np.linspace(0, 10, 80)), np.linspace(0, 10, 80))

    def test_adding_a_differently_indexed_series_drops_both(self, filtered, other):
        result = filtered + other
        assert len(result) > len(filtered), "the union index must actually differ"
        assert result.lowess_fit is None
        assert result.outlier_indices is None

    def test_the_operator_agrees_with_the_flex_method(self, filtered, other):
        assert (filtered + other).lowess_fit is (filtered.add(other)).lowess_fit

    @pytest.mark.parametrize(
        "op",
        [
            lambda a, b: a + b,
            lambda a, b: a - b,
            lambda a, b: a * b,
            lambda a, b: a / b,
            lambda a, b: a ** b,
        ],
        ids=["add", "sub", "mul", "truediv", "pow"],
    )
    def test_every_operator_drops_both(self, filtered, other, op):
        result = op(filtered, other)
        assert result.lowess_fit is None
        assert result.outlier_indices is None

    def test_a_scalar_operand_keeps_both(self, filtered):
        """A scalar cannot change the index, so the index rule must not fire.

        Zero, so the values rule (#40) does not fire either; `* 2.0` is a
        drop case in test_data_stamp_invalidation.
        """
        result = filtered + 0.0
        assert result.lowess_fit is not None
        assert result.outlier_indices == filtered.outlier_indices

    @pytest.mark.parametrize(
        "rhs, values_change",
        [("scalar_zero", False), ("different_index", True), ("same_index_zeros", False)],
    )
    def test_augmented_assignment_never_changes_the_index(self, filtered, other, rhs,
                                                          values_change):
        """`ts += x` cannot change ts's index, so the index rule never fires.

        _inplace_arith reindex_like's the result back onto the original index
        before adopting it, exactly as pandas' own _inplace_method does, so
        even an operand on a different time base leaves the length and labels
        alone. This pins that boundary. Whether the fit survives is then the
        values rule's call (#40): adding zero keeps it, and an operand on a
        different time base writes NaN wherever the two do not align, which
        changes the values and drops it.
        """
        operand = {
            "scalar_zero": 0.0,
            "different_index": other,
            "same_index_zeros": baseTs(np.zeros(len(filtered)), np.asarray(filtered.times)),
        }[rhs]
        before_index = filtered.index.copy()
        before_values = np.asarray(filtered.data, dtype=float).copy()

        filtered += operand

        assert filtered.index.equals(before_index)
        changed = not np.array_equal(np.asarray(filtered.data, dtype=float),
                                     before_values, equal_nan=True)
        assert changed is values_change, "the case is not exercising what it claims"
        if values_change:
            assert filtered.lowess_fit is None
            assert filtered.outlier_indices is None
        else:
            assert filtered.lowess_fit is not None
            assert len(filtered.lowess_fit) == len(filtered)
            assert filtered.outlier_indices is not None

    def test_an_operand_on_the_same_index_keeps_both(self, filtered):
        twin = baseTs(np.zeros(len(filtered)), np.asarray(filtered.times))
        result = filtered + twin
        assert result.index.equals(filtered.index)
        assert result.lowess_fit is not None


class TestNoWriteThrough:
    """outlier_indices is a mutable list; two objects must not share one."""

    def test_appending_through_a_derived_object_leaves_the_parent_alone(self, filtered):
        before = list(filtered.outlier_indices)
        derived = filtered + 0.0
        derived.outlier_indices.append(9999)
        assert filtered.outlier_indices == before

    def test_appending_through_a_copy_leaves_the_parent_alone(self, filtered):
        before = list(filtered.outlier_indices)
        filtered.copy().outlier_indices.append(9999)
        assert filtered.outlier_indices == before

    def test_appending_through_a_create_new_with_data_result(self, filtered):
        """interpolate_gaps keeps the index and, on gap-free data, the values,
        so the list survives - it must not be shared."""
        before = list(filtered.outlier_indices)
        filtered.interpolate_gaps().outlier_indices.append(9999)
        assert filtered.outlier_indices == before


class TestProducersStillSetTheFit:
    """Invalidation must not disturb the methods whose job is to produce a fit."""

    def test_filter_outliers_not_inplace_returns_a_fit(self):
        t = np.linspace(0, 10, 200)
        d = np.sin(t)
        d[123] += 6.0
        ts = baseTs(d, t)
        ts.set_outlier_filter(frac=0.2)

        out = ts.filter_outliers(inplace=False)
        assert out.lowess_fit is not None
        assert len(out.lowess_fit) == len(out)
        assert out.outlier_indices

    def test_lowess_detrend_not_inplace_returns_a_fit(self):
        t = np.linspace(0, 10, 200)
        ts = baseTs(np.sin(t) + t * 0.1, t)

        out = ts.lowess_detrend(frac=0.3)
        assert out.lowess_fit is not None
        assert len(out.lowess_fit) == len(out)


class TestPlotting:
    """The reported symptom, and the one plotting path with no guard."""

    def test_qc_plot_on_a_slice_does_not_raise(self, filtered):
        """plotting.py:87 raised ValueError on mismatched first dimensions."""
        sl = filtered.iloc[:50]
        _, ax = plt.subplots()
        qc_plot(sl, np.asarray(sl.data, float), sl.times, ax=ax)

        labels = [line.get_label() for line in ax.get_lines()]
        assert "Lowess Fit" not in labels, (
            "a slice has no fit of its own, so no fit trace should be drawn"
        )

    def test_qc_plot_still_draws_a_fit_when_there_is_one(self, filtered):
        _, ax = plt.subplots()
        qc_plot(filtered, np.asarray(filtered.data, float), filtered.times, ax=ax)
        assert "Lowess Fit" in [line.get_label() for line in ax.get_lines()]

    def test_plot_lowess_on_an_object_without_a_fit_says_so(self, filtered):
        """The caller asked for a fit explicitly; silence would be worse."""
        sl = filtered.iloc[:50]
        _, ax = plt.subplots()
        with pytest.raises(ValueError, match="lowess_fit"):
            plot(sl, lowess=True, ax=ax)

    def test_plot_lowess_still_works_when_there_is_a_fit(self, filtered):
        _, ax = plt.subplots()
        plot(filtered, lowess=True, ax=ax)
        assert "Lowess Fit" in [line.get_label() for line in ax.get_lines()]
