"""`lag_plot` labels the plot with the name the series has, and nothing else (#61).

It used to wrap `ts.signal_name.upper()` in a bare `except Exception`, print
the failure to stdout, and label the title and both axes `Signal` as if that
were the name. The same shape #34 removed from `plot_fft_power`, one function
down - weaker, because `shift_timeseries` was already outside the `try`, so no
guard was swallowed; but a mislabelled plot from a diagnostic nobody sees.

Two things closed it. The `try` is gone, along with the print and the
`.upper()`: the title is built from the name verbatim, which is what the
other seven plot titles in plotting.py already did (#56 settled that a
derivation carries the name unchanged; the lag plot was the last place that
re-cased it). And the failure it caught can no longer happen: `signal_name`
is a normalising property since #61, so there is no non-string to call a
method on - see test_label_normalising_property.py.
"""
import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from baseTs import baseTs  # noqa: E402


@pytest.fixture
def ts():
    t = np.arange(400) / 10.0
    return baseTs(np.sin(t), t, freq=10.0, signal_name="ecg")


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def _labels(ax):
    return ax.get_title(), ax.get_xlabel(), ax.get_ylabel()


def test_a_none_name_is_not_labelled_signal_and_prints_nothing(ts, capsys):
    """The issue's reproduction, both halves: stdout stays empty, and the
    placeholder is gone from every label."""
    ts.signal_name = None
    ax = ts.lag_plot(5)
    assert capsys.readouterr().out == ""
    for label in _labels(ax):
        assert "Signal" not in label
    assert ax.get_title() == " Lag Plot at 0.5 seconds (5items)"


def test_a_numeric_name_appears_as_itself(ts, capsys):
    """`normalise_label`'s rule: a caller who set a number meant it to show."""
    ts.signal_name = 12
    ax = ts.lag_plot(5)
    assert capsys.readouterr().out == ""
    assert ax.get_title().startswith("12 Lag Plot")
    assert ax.get_xlabel() == "Original 12 Data"


def test_a_mixed_case_name_is_used_verbatim_like_every_other_plot(ts):
    """The last re-casing site. `plot()` titles "Heart Rate by time."; the lag
    plot titled "HEART RATE Lag Plot" for the same object."""
    ts.signal_name = "Heart Rate"
    ax = ts.lag_plot(5)
    assert ax.get_title() == "Heart Rate Lag Plot at 0.5 seconds (5items)"
    assert ax.get_xlabel() == "Original Heart Rate Data"
    assert ax.get_ylabel() == "Heart Rate Data lagged at 0.5second (5items)"
    assert ts.plot().get_title() == "Heart Rate by time."


def test_a_constructor_name_still_reads_upper_case(ts):
    """Unchanged for the common path: the constructor upper-cases its own
    argument (#56), so a lag plot of a series named at construction looks
    exactly as it did."""
    assert ts.lag_plot(5).get_title() == "ECG Lag Plot at 0.5 seconds (5items)"


def test_lag_plot_has_no_try_and_no_print():
    """The mechanism, pinned at the source: no `try` statement and no call to
    `print` anywhere in lag_plot, so the shape cannot quietly come back.
    Read from the AST, not the text - the comment that explains the removal
    mentions both words."""
    import ast
    import inspect
    import textwrap
    from baseTs import plotting
    tree = ast.parse(textwrap.dedent(inspect.getsource(plotting.lag_plot)))
    assert not [n for n in ast.walk(tree) if isinstance(n, ast.Try)]
    calls = [n.func.id for n in ast.walk(tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
    assert "print" not in calls
