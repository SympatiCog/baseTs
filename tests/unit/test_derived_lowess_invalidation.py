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
        """Invalidation is about the index, not about deriving at all."""
        doubled = filtered * 2.0
        assert doubled.lowess_fit is not None
        assert len(doubled.lowess_fit) == len(doubled)
        assert doubled.outlier_indices == filtered.outlier_indices

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
        """rolling() routes through _FinalizingWindow, not __finalize__ directly."""
        rolled = filtered.rolling(5).mean()
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
        filtered.data = np.zeros(200)
        assert filtered.lowess_fit is not None
        assert filtered.outlier_indices is not None


class TestInvalidationThroughCreateNewWithData:
    """_create_new_with_data copies both attributes by name, outside __finalize__.

    Every non-inplace baseTs method routes through it, so it needs the same
    index rule - a second implementation is how _create_new_with_data and
    __finalize__ came to disagree about `freq` in #29.
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

    def test_sg_filter_keeps_both(self, filtered):
        """Same index, so both still describe the result."""
        smoothed = filtered.sg_filter()
        assert smoothed.index.equals(filtered.index)
        assert smoothed.lowess_fit is not None
        assert smoothed.outlier_indices == filtered.outlier_indices


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
        """A scalar cannot change the index, so nothing should be dropped."""
        result = filtered * 2.0
        assert result.lowess_fit is not None
        assert result.outlier_indices == filtered.outlier_indices

    def test_an_operand_on_the_same_index_keeps_both(self, filtered):
        twin = baseTs(np.zeros(len(filtered)), np.asarray(filtered.times))
        result = filtered + twin
        assert result.index.equals(filtered.index)
        assert result.lowess_fit is not None


class TestNoWriteThrough:
    """outlier_indices is a mutable list; two objects must not share one."""

    def test_appending_through_a_derived_object_leaves_the_parent_alone(self, filtered):
        before = list(filtered.outlier_indices)
        derived = filtered * 2.0
        derived.outlier_indices.append(9999)
        assert filtered.outlier_indices == before

    def test_appending_through_a_copy_leaves_the_parent_alone(self, filtered):
        before = list(filtered.outlier_indices)
        filtered.copy().outlier_indices.append(9999)
        assert filtered.outlier_indices == before

    def test_appending_through_a_create_new_with_data_result(self, filtered):
        """sg_filter keeps the index, so the list survives - it must not be shared."""
        before = list(filtered.outlier_indices)
        filtered.sg_filter().outlier_indices.append(9999)
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
