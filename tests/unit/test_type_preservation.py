"""
Tests that pandas operations preserve the baseTs type and its metadata.

Before this, TimeSeriesData._constructor was inherited unchanged, so every
native pandas operation returned a TimeSeriesData and silently dropped all
baseTs methods - meaning the documented method chaining did not actually work.
"""
import numpy as np
import pytest

from baseTs import baseTs
from baseTs.series import TimeSeriesData


PANDAS_OPS = [
    "iloc[0:10]", "loc[0.0:1.0]", "head(5)", "tail(5)", "dropna()", "abs()",
    "cumsum()", "diff()", "rolling(3).mean()", "shift(1)", "round(2)",
    "clip(0, 10)", "fillna(0)", "sort_values()", "astype(float)",
    "interpolate()", "ffill()", "bfill()", "expanding().mean()",
    "pct_change()", "rank()", "nlargest(3)", "copy()",
]


@pytest.fixture
def ts():
    return baseTs(np.arange(50, dtype=float), np.arange(50) / 10.0,
                  freq=10.0, signal_name="probe")


class TestTypePreservation:

    @pytest.mark.parametrize("op", PANDAS_OPS)
    def test_operation_returns_basets(self, ts, op):
        result = eval(f"ts.{op}")
        assert isinstance(result, baseTs), f"ts.{op} downgraded to {type(result).__name__}"

    @pytest.mark.parametrize("op", PANDAS_OPS)
    def test_result_keeps_basets_methods(self, ts, op):
        """The point of preserving the type is keeping the domain methods."""
        result = eval(f"ts.{op}")
        for method in ("lowpass_at", "detect_outliers", "get_frequency_content"):
            assert hasattr(result, method), f"ts.{op} lost .{method}()"

    def test_chaining_pandas_into_basets(self, ts):
        """The documented pattern: a pandas op followed by a baseTs op."""
        result = ts.iloc[0:40].lowpass_at(1.0).zscale()
        assert isinstance(result, baseTs)
        assert len(result) == 40

    def test_constructor_accepts_pandas_convention(self):
        """pandas builds subclasses as _constructor(values, index=...)."""
        obj = baseTs(np.arange(5, dtype=float), index=np.arange(5) / 10.0)
        assert isinstance(obj, baseTs)
        assert np.allclose(obj.times, np.arange(5) / 10.0)

    def test_constructor_sliced_is_a_property(self):
        """pandas looks this up on the class; a plain method breaks that."""
        assert isinstance(
            type(TimeSeriesData.__dict__['_constructor_sliced']), type(property)
        ) or isinstance(TimeSeriesData.__dict__['_constructor_sliced'], property)


class TestMetadataPropagation:

    def test_outlier_indices_survives_slicing(self, ts):
        """
        outlier_indices was absent from _metadata, so this raised
        AttributeError after any pandas operation.
        """
        ts.outlier_indices = np.array([3, 4, 5])
        assert np.array_equal(ts.iloc[0:20].outlier_indices, np.array([3, 4, 5]))

    def test_declared_metadata_is_actually_reachable(self, ts):
        """Every name in _metadata must exist on a constructed object."""
        for name in TimeSeriesData._metadata:
            assert hasattr(ts, name), f"_metadata declares {name!r} but it is unset"

    def test_signal_name_and_flags_survive(self, ts):
        ts.is_filtered = True
        sliced = ts.iloc[0:20]
        assert sliced.signal_name == ts.signal_name
        assert sliced.is_filtered is True

    def test_history_is_copied_not_shared(self, ts):
        """
        pandas' default __finalize__ assigns metadata by reference, so parent
        and child would share one history list.
        """
        child = ts.iloc[0:20]
        assert child.history is not ts.history

        child.history.append("child-only")
        assert "child-only" not in ts.history
