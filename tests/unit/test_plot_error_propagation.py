"""Tests for issue #34: plot_fft_power must raise, not draw the error.

`plot_fft_power` wrapped its whole body in a bare `except Exception` and
rendered the message as text on the axes, so every guard added by #24 and #28
was neutralised on what is, for interactive users, the main path to a spectrum.
A batch pipeline doing `ax = plot_fft_power(ts); fig.savefig(...)` got a
silently-bogus figure and a success exit code.

The fix is structural rather than a narrower `except`: everything that can fail
on the caller's input now runs *before* `setup_plot`, so a rejected call has
built nothing to clean up. That is what the no-leaked-figure and
untouched-axes tests below pin - narrowing the `except` alone would leave both
of those broken, because the figure is already created by the time the guard
runs.
"""
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

from baseTs import baseTs  # noqa: E402
from baseTs.plotting import plot_fft_power  # noqa: E402


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


@pytest.fixture
def good_ts():
    """A series with a usable rate and finite data."""
    t = np.arange(400) / 10.0
    return baseTs(np.sin(2 * np.pi * 0.5 * t), t, freq=10.0, signal_name="sig")


@pytest.fixture
def bad_rate_ts():
    """The issue's own reproduction: every timestamp identical, so freq is NaN."""
    return baseTs(np.sin(np.arange(400) / 10.0), np.zeros(400))


@pytest.fixture
def nan_data_ts():
    """A usable rate carrying gaps - the #28 guard's input."""
    t = np.arange(400) / 10.0
    d = np.sin(2 * np.pi * 0.5 * t)
    d[100:104] = np.nan
    return baseTs(d, t, freq=10.0, signal_name="sig")


def test_a_bad_rate_raises_rather_than_drawing_the_error(bad_rate_ts):
    """The issue's reproduction. The docstring's `Raises:` becomes true."""
    with pytest.raises(ValueError, match="sampling frequency"):
        plot_fft_power(bad_rate_ts)


def test_nan_data_raises_rather_than_drawing_the_error(nan_data_ts):
    """#28's guard reaches the caller instead of becoming on-plot text."""
    with pytest.raises(ValueError):
        plot_fft_power(nan_data_ts)


def test_an_unknown_window_raises(good_ts):
    with pytest.raises(ValueError, match="[Ww]indow"):
        plot_fft_power(good_ts, window="bartlett")


def test_a_range_selecting_no_bins_raises(good_ts):
    """Above Nyquist, so the frequency mask is empty."""
    with pytest.raises(ValueError, match="No frequencies found"):
        plot_fft_power(good_ts, min_rate=100.0, max_rate=200.0)


def test_a_reversed_highlight_band_raises(good_ts):
    with pytest.raises(ValueError, match="highlight_band"):
        plot_fft_power(good_ts, highlight_band=(0.4, 0.1))


def test_the_wrapper_on_the_object_raises_too(bad_rate_ts):
    """ts.plot_fft_power() is the path users actually call."""
    with pytest.raises(ValueError, match="sampling frequency"):
        bad_rate_ts.plot_fft_power()


def test_a_rejected_call_leaks_no_figure(bad_rate_ts):
    """setup_plot used to run before the guard, so every failure left a figure.

    In a batch loop those accumulate. This fails against a merely-narrowed
    `except`, which still creates the figure before raising.
    """
    before = set(plt.get_fignums())
    with pytest.raises(ValueError):
        plot_fft_power(bad_rate_ts)
    assert set(plt.get_fignums()) == before


def test_a_rejected_call_leaves_a_supplied_axes_untouched(bad_rate_ts):
    """A caller passing ax= gets it back as they left it, not titled and annotated."""
    _, ax = plt.subplots()
    with pytest.raises(ValueError):
        plot_fft_power(bad_rate_ts, ax=ax)
    assert ax.get_title() == ""
    assert ax.get_xlabel() == ""
    assert ax.get_ylabel() == ""
    assert list(ax.texts) == []
    assert list(ax.get_lines()) == []


def test_a_reversed_highlight_band_is_rejected_before_anything_is_drawn(good_ts):
    """The band check ran after the spectrum was already plotted.

    Ordering matters for a valid series with an invalid band: the guard must
    fire before the line goes on, or a rejected call still mutates the axes.
    """
    _, ax = plt.subplots()
    with pytest.raises(ValueError, match="highlight_band"):
        plot_fft_power(good_ts, ax=ax, highlight_band=(0.4, 0.1))
    assert list(ax.get_lines()) == []
    assert ax.get_title() == ""


def test_the_filter_outliers_path_raises_and_interpolate_gaps_is_the_remedy():
    """The consequence users actually meet, and the fix the docs name.

    Since #36 filter_outliers preserves the NaNs it did not create, and since
    #28 the spectral guards reject them - so this chain used to draw the error
    message where a caller expected a spectrum. Pinned because it is the one
    reachable-in-normal-use break this change introduces.
    """
    t = np.arange(600) / 10.0
    d = np.sin(2 * np.pi * 0.5 * t)
    d[[100, 200, 300]] += 8.0    # spikes, which the filter blanks and fills
    d[400:404] = np.nan          # an acquisition dropout, which it preserves
    ts = baseTs(d, t, freq=10.0, signal_name="sig")
    ts.set_outlier_filter(frac=0.07, z_threshold=3)
    filtered = ts.filter_outliers()

    assert np.isnan(np.asarray(filtered, float)).any(), "fixture no longer gappy"
    with pytest.raises(ValueError, match="NaN or Inf"):
        filtered.plot_fft_power()

    ax = filtered.interpolate_gaps().plot_fft_power()
    assert len(ax.get_lines()) == 1


def test_the_happy_path_still_draws(good_ts):
    """Pins that moving the computation above setup_plot did not break it."""
    ax = plot_fft_power(good_ts, window="hann", max_rate=2.0)
    lines = ax.get_lines()
    assert len(lines) == 1
    freqs = np.asarray(lines[0].get_xdata(), float)
    assert freqs.min() >= 0.0
    assert freqs.max() <= 2.0
    assert ax.get_title().startswith("Power Spectrum of SIG")
    assert ax.get_xlabel() == "Frequency (Hz)"
    assert ax.get_ylabel() == "Power"
    assert ax.get_xlim() == (0.0, 2.0)


def test_the_happy_path_still_shades_a_highlight_band(good_ts):
    ax = plot_fft_power(good_ts, max_rate=2.0, highlight_band=(0.1, 0.4))
    assert len(ax.patches) == 1
    assert ax.get_legend() is not None


def test_scale_power_still_normalises(good_ts):
    ax = plot_fft_power(good_ts, max_rate=2.0, scale_power=True)
    power = np.asarray(ax.get_lines()[0].get_ydata(), float)
    assert np.isclose(power.max(), 1.0)
    assert ax.get_ylabel() == "Scaled Power"
