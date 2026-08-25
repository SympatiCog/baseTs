"""
Tests for the hybrid baseTs.plot accessor.

`plot` was a plain alias for plot_line, which shadowed the pandas `.plot`
accessor - an object, not a method - making ts.plot.line(), .bar(), .hist()
and the rest unreachable. The accessor keeps the callable behaviour and
restores attribute access.
"""
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import pytest

from baseTs import baseTs


@pytest.fixture
def ts():
    # Strictly positive so pie/area/kde are all valid
    data = np.abs(np.sin(np.arange(50) / 5.0)) + 0.1
    return baseTs(data, np.arange(50) / 10.0, freq=10.0, signal_name="probe")


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close('all')


class TestCallableBehaviour:
    """The historical spelling must be unchanged."""

    def test_plot_is_callable(self, ts):
        assert isinstance(ts.plot(), plt.Axes)

    def test_plot_matches_plot_line(self, ts):
        assert type(ts.plot()) is type(ts.plot_line())

    @pytest.mark.parametrize("kwargs", [
        {"show": False},
        {"title": "custom"},
        {"lowess": False},
        {"xlabel": "t", "ylabel": "v"},
    ])
    def test_plot_line_kwargs_pass_through(self, ts, kwargs):
        assert isinstance(ts.plot(**kwargs), plt.Axes)

    def test_plot_accepts_an_axes(self, ts):
        _, ax = plt.subplots()
        assert ts.plot(ax=ax) is ax


class TestPandasAccessorRestored:

    @pytest.mark.parametrize("kind", [
        "line", "bar", "barh", "hist", "box", "kde", "density", "area", "pie",
    ])
    def test_pandas_plot_kinds_are_reachable(self, ts, kind):
        assert isinstance(getattr(ts.plot, kind)(), plt.Axes)

    def test_dir_exposes_pandas_kinds(self, ts):
        listed = dir(ts.plot)
        for kind in ("line", "bar", "hist", "box"):
            assert kind in listed

    def test_unknown_attribute_raises(self, ts):
        with pytest.raises(AttributeError):
            ts.plot.definitely_not_a_plot_kind

    def test_repr_is_informative(self, ts):
        assert "plot accessor" in repr(ts.plot)


class TestAccessorSurvivesOperations:

    def test_available_after_pandas_operation(self, ts):
        """The accessor is a property, so it must follow the preserved type."""
        sliced = ts.iloc[0:20]
        assert isinstance(sliced, baseTs)
        assert isinstance(sliced.plot(), plt.Axes)
        assert isinstance(sliced.plot.bar(), plt.Axes)

    def test_accessor_bound_to_its_own_series(self, ts):
        """Each accessor plots its own data, not the parent's."""
        sliced = ts.iloc[0:10]
        ax = sliced.plot.line()
        assert len(ax.lines[0].get_xdata()) == 10
