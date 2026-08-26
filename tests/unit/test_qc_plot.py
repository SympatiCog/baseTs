"""Tests for filter_outliers(qcplot=True).

The QC plot exists to show the filter's effect, so its "Original" trace must be
the pre-filter signal and it must carry the LOWESS fit — under both values of
`inplace`. Before this was fixed, inplace=True plotted the filtered data as
"Original" (the result against itself) and inplace=False silently dropped the
fit trace.
"""
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from baseTs import baseTs


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


@pytest.fixture
def spiked_ts():
    t = np.linspace(0, 10, 300)
    d = np.sin(2 * np.pi * 0.5 * t) + 0.05 * np.random.default_rng(0).standard_normal(300)
    d[100] += 5.0
    d[200] -= 5.0
    ts = baseTs(data=d, times=t, signal_name="sig")
    ts.set_outlier_filter(frac=0.1, z_threshold=5)
    return ts


def _traces(ax):
    return {line.get_label(): np.asarray(line.get_ydata(), float) for line in ax.get_lines()}


@pytest.mark.parametrize("inplace", [False, True])
def test_original_trace_is_the_prefilter_signal(spiked_ts, inplace):
    before = np.asarray(spiked_ts.data, float).copy()
    _, ax = plt.subplots()
    spiked_ts.filter_outliers(qcplot=True, inplace=inplace, ax=ax)

    traces = _traces(ax)
    assert "Original" in traces
    assert np.allclose(traces["Original"], before), (
        "the 'Original' trace must be the signal as it was before filtering"
    )


@pytest.mark.parametrize("inplace", [False, True])
def test_original_and_filtered_are_distinguishable(spiked_ts, inplace):
    _, ax = plt.subplots()
    spiked_ts.filter_outliers(qcplot=True, inplace=inplace, ax=ax)

    traces = _traces(ax)
    assert not np.array_equal(traces["Original"], traces["Filtered"]), (
        "plotting the filtered data against itself makes the QC plot inert"
    )


@pytest.mark.parametrize("inplace", [False, True])
def test_lowess_fit_trace_is_present(spiked_ts, inplace):
    _, ax = plt.subplots()
    spiked_ts.filter_outliers(qcplot=True, inplace=inplace, ax=ax)

    traces = _traces(ax)
    assert "Lowess Fit" in traces, "the fit trace is the point of the QC plot"
    assert np.all(np.isfinite(traces["Lowess Fit"]))


def test_qcplot_does_not_mutate_caller_when_not_inplace(spiked_ts):
    """The plotting path must not become a second route to the #6 bug."""
    before = np.asarray(spiked_ts.data, float).copy()
    before_fit = spiked_ts.lowess_fit
    before_last = spiked_ts.last_process

    _, ax = plt.subplots()
    result = spiked_ts.filter_outliers(qcplot=True, inplace=False, ax=ax)

    assert result is not spiked_ts
    assert np.array_equal(np.asarray(spiked_ts.data, float), before)
    assert spiked_ts.lowess_fit is before_fit
    assert spiked_ts.last_process == before_last


def test_qcplot_false_leaves_no_figure_behind(spiked_ts):
    n_before = len(plt.get_fignums())
    spiked_ts.filter_outliers(qcplot=False, inplace=False)
    assert len(plt.get_fignums()) == n_before


@pytest.mark.parametrize("inplace", [False, True])
def test_return_value_is_unaffected_by_plotting(spiked_ts, inplace):
    """Asking for a plot must not change what the filter returns."""
    import copy as _copy

    plain = _copy.deepcopy(spiked_ts).filter_outliers(qcplot=False, inplace=inplace)
    _, ax = plt.subplots()
    plotted = _copy.deepcopy(spiked_ts).filter_outliers(qcplot=True, inplace=inplace, ax=ax)

    assert np.allclose(np.asarray(plain.data, float), np.asarray(plotted.data, float))
    assert plain.outlier_indices == plotted.outlier_indices
