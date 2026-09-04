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

from decimal import Decimal  # noqa: E402
from fractions import Fraction  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

from baseTs import baseTs  # noqa: E402
from baseTs.plotting import plot_fft_power  # noqa: E402


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def _span_x_extent(patch):
    """The data-space x range of an axvspan patch, on any matplotlib.

    axvspan returned a Polygon before matplotlib 3.10 and returns a Rectangle
    after, and the two disagree on everything convenient: Rectangle has
    get_x()/get_width() and a unit-square path, Polygon has neither and carries
    data coordinates in its vertices. Composing the path with the patch's own
    transform is the one reading that is correct for both, which matters
    because CI runs Python 3.9 through 3.11 and so spans that change.

    Only x is meaningful - axvspan puts y through a blended transform in axes
    coordinates.
    """
    vertices = patch.get_patch_transform().transform(patch.get_path().vertices)
    xs = np.asarray(vertices, float)[:, 0]
    return xs.min(), xs.max()


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


class TestTheDisplayBoundsAreValidatedBeforeDrawing:
    """The frequency bounds reach ax.set_xlim, which rejects NaN and Inf.

    An infinite max_rate passes the frequency mask (the mask is non-empty), so
    it used to reach the draw phase and die inside set_xlim - after setup_plot
    had already minted a figure and titled the caller's axes. That is exactly
    the guarantee this change claims, so the bounds have to be checked in the
    compute phase alongside everything else.

    A non-numeric bound was worse than undocumented: it died on np.isnan with
    "ufunc 'isnan' not supported for the input types", and max_rate=None is a
    call docs/API.md's own legacy section still shows.
    """

    @pytest.mark.parametrize("max_rate", [np.inf, -np.inf])
    def test_a_non_finite_max_rate_leaks_no_figure(self, good_ts, max_rate):
        before = set(plt.get_fignums())
        with pytest.raises(ValueError, match="max_rate"):
            plot_fft_power(good_ts, max_rate=max_rate)
        assert set(plt.get_fignums()) == before

    def test_a_non_finite_max_rate_leaves_a_supplied_axes_untouched(self, good_ts):
        _, ax = plt.subplots()
        with pytest.raises(ValueError, match="max_rate"):
            plot_fft_power(good_ts, max_rate=np.inf, ax=ax)
        assert ax.get_title() == ""
        assert list(ax.get_lines()) == []

    def test_a_non_finite_min_rate_is_rejected(self, good_ts):
        before = set(plt.get_fignums())
        with pytest.raises(ValueError, match="min_rate"):
            plot_fft_power(good_ts, min_rate=np.inf)
        assert set(plt.get_fignums()) == before

    @pytest.mark.parametrize("bad", [None, "abc", "30", True, [1.0, 2.0]])
    def test_a_non_numeric_max_rate_raises_valueerror_not_typeerror(self, good_ts, bad):
        """ValueError, matching every other bound failure in this function.

        '30' and True are rejected rather than coerced, following
        validate_sampling_freq: float('30') succeeds and bool is a Real, so
        both would otherwise slip through a bare float() call.
        """
        with pytest.raises(ValueError, match="max_rate"):
            plot_fft_power(good_ts, max_rate=bad)

    def test_a_nan_max_rate_still_means_nyquist(self, good_ts):
        """NaN is the documented public sentinel for max_rate - not an error."""
        ax = plot_fft_power(good_ts, max_rate=np.nan)
        drawn = np.asarray(ax.get_lines()[0].get_xdata(), float)
        # The top bin, not Nyquist itself: fftfreq's highest positive bin for
        # an even-length series is rate/2 - rate/n, so 4.975 Hz here.
        expected, _ = good_ts.get_frequency_content()
        assert drawn.max() == expected.max()
        assert 4.9 < drawn.max() <= 5.0

    def test_a_nan_min_rate_is_rejected(self, good_ts):
        """min_rate has no sentinel, so NaN is simply invalid there."""
        with pytest.raises(ValueError, match="min_rate"):
            plot_fft_power(good_ts, min_rate=np.nan)

    def test_a_multi_element_array_bound_is_named_as_not_a_scalar(self, good_ts):
        """Pins the shared door's ndarray branch, which mutation testing found bare.

        Deleting that branch leaves the suite green, because float() on a
        multi-element array raises TypeError on numpy 2.x and the shared door
        translates it to ValueError anyway - so only the *message* degrades,
        from "is not a scalar. Pass a single number" to "is not a real number".
        The branch exists precisely because that distinction is what tells a
        caller what to do, and because float() accepts such an array on numpy
        1.x, which would make the accept set differ across the CI matrix.
        """
        with pytest.raises(ValueError, match="is not a scalar"):
            plot_fft_power(good_ts, max_rate=np.array([1.0, 2.0]))

    def test_a_zero_dim_array_bound_is_still_accepted(self, good_ts):
        """The other half of that branch: 0-d arrays convert alike on both majors."""
        ax = plot_fft_power(good_ts, max_rate=np.array(2.0))
        assert ax.get_xlim() == (0.0, 2.0)


class TestTheHighlightBandIsValidatedBeforeDrawing:
    """`band_low >= band_high` is False for NaN, so a NaN edge passed the guard.

    Pre-existing - the same check let it through on main, just positioned after
    the plot rather than before it. Closed here because this change moves and
    re-documents that check, and shipping "raises if not strictly increasing"
    over a known NaN hole would make the new docstring false.
    """

    @pytest.mark.parametrize(
        "band", [(np.nan, 0.5), (0.1, np.nan), (np.nan, np.nan), (np.inf, 0.5)]
    )
    def test_a_non_finite_band_edge_is_rejected(self, good_ts, band):
        before = set(plt.get_fignums())
        with pytest.raises(ValueError, match="highlight_band"):
            plot_fft_power(good_ts, highlight_band=band)
        assert set(plt.get_fignums()) == before

    @pytest.mark.parametrize("band", [(0.1, 0.2, 0.3), (0.1,), 5, "ab"])
    def test_a_malformed_band_raises_valueerror(self, good_ts, band):
        """One ValueError for every malformed band, from two different doors.

        The 1- and 3-tuples and the non-iterable die on unpacking; "ab" unpacks
        happily to ('a', 'b') and is caught one step later by the string guard
        in the shared door. The point of the parametrization is that the caller
        cannot tell which door fired.
        """
        with pytest.raises(ValueError, match="highlight_band"):
            plot_fft_power(good_ts, highlight_band=band)

    def test_a_non_numeric_band_edge_raises_valueerror(self, good_ts):
        with pytest.raises(ValueError, match="highlight_band"):
            plot_fft_power(good_ts, highlight_band=(None, 0.5))


BAD_INPUTS = [
    ("unknown window", dict(window="bartlett")),
    ("range selects no bins", dict(min_rate=100.0, max_rate=200.0)),
    ("min_rate above max_rate", dict(min_rate=3.0, max_rate=1.0)),
    ("max_rate +Inf", dict(max_rate=np.inf)),
    ("max_rate -Inf", dict(max_rate=-np.inf)),
    ("max_rate None", dict(max_rate=None)),
    ("max_rate 'abc'", dict(max_rate="abc")),
    ("max_rate '30'", dict(max_rate="30")),
    ("max_rate True", dict(max_rate=True)),
    ("max_rate list", dict(max_rate=[1.0, 2.0])),
    ("min_rate Inf", dict(min_rate=np.inf)),
    ("min_rate NaN", dict(min_rate=np.nan)),
    ("min_rate None", dict(min_rate=None)),
    ("min_rate True", dict(min_rate=True)),
    ("band reversed", dict(highlight_band=(0.4, 0.1))),
    ("band equal edges", dict(highlight_band=(0.2, 0.2))),
    ("band (NaN, 0.5)", dict(highlight_band=(np.nan, 0.5))),
    ("band (0.1, NaN)", dict(highlight_band=(0.1, np.nan))),
    ("band (NaN, NaN)", dict(highlight_band=(np.nan, np.nan))),
    ("band (Inf, 0.5)", dict(highlight_band=(np.inf, 0.5))),
    ("band (0.1, Inf)", dict(highlight_band=(0.1, np.inf))),
    ("band (None, 0.5)", dict(highlight_band=(None, 0.5))),
    ("band 3-tuple", dict(highlight_band=(0.1, 0.2, 0.3))),
    ("band 1-tuple", dict(highlight_band=(0.1,))),
    ("band non-iterable", dict(highlight_band=5)),
    ("band string", dict(highlight_band="ab")),
]


@pytest.mark.parametrize("label,kwargs", BAD_INPUTS, ids=[c[0] for c in BAD_INPUTS])
def test_every_rejected_input_raises_valueerror_and_draws_nothing(good_ts, label, kwargs):
    """One contract for the whole function, generated from a census against main.

    Uniform ValueError is the point. Several of these used to escape as
    TypeError - `np.isnan(None)` gave "ufunc 'isnan' not supported for the
    input types", and a malformed band died on tuple unpacking - which the bare
    except then drew as text, so no caller ever saw the type either way.

    Four of them did not even produce error text on main, they produced a
    silently wrong plot: `max_rate=True` and `min_rate=True` were taken as
    1.0 Hz, `highlight_band='ab'` passed the ordering check because 'a' >= 'b'
    is False, and a NaN band edge passed it for the same reason.
    """
    before = set(plt.get_fignums())
    with pytest.raises(ValueError):
        plot_fft_power(good_ts, **kwargs)
    assert set(plt.get_fignums()) == before, "a rejected call minted a figure"


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


@pytest.mark.parametrize(
    "band,expected",
    [((1, 2), "1-2 Hz"),
     ((0.01, 0.1), "0.01-0.1 Hz"),
     ((0.5, 1), "0.5-1 Hz")],
)
def test_the_legend_label_keeps_the_callers_own_formatting(good_ts, band, expected):
    """Validation coerces to float; the label must not inherit that.

    Routing the label through the validated floats turned an integer band's
    legend from "1-2 Hz" into "1.0-2.0 Hz" - a silent presentation change on
    the success path, which is exactly the kind the reorder was supposed not
    to make. The span itself is still drawn from the validated values.
    """
    ax = plot_fft_power(good_ts, max_rate=3.0, highlight_band=band)
    assert [t.get_text() for t in ax.get_legend().get_texts()] == [expected]
    low, high = _span_x_extent(ax.patches[0])
    assert low == pytest.approx(float(band[0]))
    assert high == pytest.approx(float(band[1]))


def test_a_one_shot_iterable_band_is_unpacked_exactly_once(good_ts):
    """A generator band worked before; unpacking it twice broke it.

    An earlier revision validated the band, then re-unpacked the caller's
    original object at draw time to build the legend label. For a generator or
    iter([...]) the second unpack sees an exhausted object, so a band that
    plots fine on the previous release raised "not enough values to unpack" -
    and did so from the draw phase, after a figure existed and a supplied ax
    had been titled, which is the one guarantee this whole change is built on.
    """
    _, ax = plt.subplots()
    before = set(plt.get_fignums())
    plot_fft_power(good_ts, max_rate=3.0, ax=ax,
                   highlight_band=(edge for edge in (0.1, 0.4)))
    assert set(plt.get_fignums()) == before
    assert [t.get_text() for t in ax.get_legend().get_texts()] == ["0.1-0.4 Hz"]
    assert _span_x_extent(ax.patches[0]) == pytest.approx((0.1, 0.4))


def test_an_exhausted_iterable_band_is_still_rejected_cleanly(good_ts):
    """The other side of unpacking once: a genuinely empty iterable still raises."""
    spent = iter([])
    with pytest.raises(ValueError, match="highlight_band"):
        plot_fft_power(good_ts, highlight_band=spent)


@pytest.mark.parametrize("bound", [Decimal("2.0"), Fraction(2, 1)])
def test_high_precision_bounds_are_now_accepted(good_ts, bound):
    """Newly accepted, in the opposite direction to the rest of the census.

    On main these died on `np.isnan(Decimal(...))` with "ufunc 'isnan' not
    supported for the input types" and were drawn as error text. The shared
    door accepts anything float() can take, which is what np.fft.fftfreq can
    actually use, so they now plot. Pinned because the census enumerates only
    inputs that were already bad and would not have caught this direction.
    """
    ax = plot_fft_power(good_ts, max_rate=bound)
    assert ax.get_xlim() == (0.0, 2.0)


def test_a_value_error_from_a_custom_float_is_translated_not_leaked():
    """Pins coerce_real_scalar's ValueError arm, which mutation testing found bare.

    float() raises TypeError for most bad types, so the ValueError entry in the
    except tuple needs an object whose __float__ itself fails that way - the
    same shape of unpinned branch as the multi-element-array case above, and
    the same fix.
    """
    class Awkward:
        def __float__(self):
            raise ValueError("no float for you")

    t = np.arange(400) / 10.0
    ts = baseTs(np.sin(t), t, freq=10.0)
    with pytest.raises(ValueError, match="is not a real number"):
        plot_fft_power(ts, max_rate=Awkward())


def test_an_empty_series_is_a_valueerror_like_everything_else():
    """The hole #34 documented in the "all ValueError" contract is closed.

    It was a ZeroDivisionError from inside np.fft.fftfreq, family-wide, and
    this test pinned it as the one documented exception so that closing #62
    would have to come back here. #62 put the check in the shared spectral
    door (utils.validate_non_empty), so the contract now has no exceptions.
    The family-wide pins live in test_spectral_empty_series.py; this one
    keeps the plotting half: the failure happens in the compute phase, before
    setup_plot, so the draws-nothing guarantee holds for it too.
    """
    empty = baseTs(np.array([]), np.array([]), freq=10.0)
    before = set(plt.get_fignums())
    with pytest.raises(ValueError, match="a spectrum needs at least one sample"):
        plot_fft_power(empty)
    assert set(plt.get_fignums()) == before


def test_scale_power_still_normalises(good_ts):
    ax = plot_fft_power(good_ts, max_rate=2.0, scale_power=True)
    power = np.asarray(ax.get_lines()[0].get_ydata(), float)
    assert np.isclose(power.max(), 1.0)
    assert ax.get_ylabel() == "Scaled Power"
