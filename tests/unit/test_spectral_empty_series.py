"""An empty series is rejected by every spectral entry point, from one door (#62).

Before this, `compute_fft_power` was the only one of five that checked for an
empty series. The other four - `get_frequency_content`, `get_peak_freq`,
`relative_band_power`, `falff` - and `plot_fft_power` on top of them, let the
zero-length index reach `np.fft.fftfreq`, which divides by `n * d` and raised a
bare `ZeroDivisionError`. That escaped the family's documented contract that
one `except ValueError` catches every rejected input (#32 made
`ValidationError` a `ValueError` for exactly that promise).

Same shape as #28: a guard that one sibling had and the others lacked, because
nobody owned it. The fix is `utils.validate_non_empty`, called at the two
places the family actually computes a spectrum - `get_frequency_content` and
`compute_fft_power` - plus `relative_band_power`, which takes a standard
deviation before it reaches either and would otherwise warn on the way to the
error. `compute_fft_power`'s local copy is gone, so there is one definition and
one message.

The 1-sample decision is pinned here too, so it is a rule rather than an
accident: only the *empty* series is rejected by the door. A single sample
still produces a DC-only spectrum from `get_frequency_content`, and
`compute_fft_power` keeps its own, separately documented, minimum of two.
"""
import warnings

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from baseTs import baseTs  # noqa: E402
from baseTs import utils  # noqa: E402
from baseTs.plotting import plot_fft_power  # noqa: E402


def _empty():
    return baseTs(np.array([]), np.array([]), freq=10.0)


# The whole message, not its first clause. compute_fft_power's pre-#62 local
# check said exactly "Time series data is empty", so a `match` on that prefix
# was satisfied by the old copy and the new door alike.
SHARED_MESSAGE = r"Time series data is empty: a spectrum needs at least one sample\."


def _one_sample():
    return baseTs(np.array([1.0]), np.array([0.0]), freq=10.0)


# Every public route to a spectrum. `falff` reaches `relative_band_power`,
# which reaches `get_frequency_content`; `get_peak_freq` reaches
# `get_frequency_content`; `plot_fft_power` does too. Listing them all rather
# than the two that carry the call is the point: the contract is about what a
# caller sees, not about where the check lives.
ENTRY_POINTS = {
    "get_frequency_content": lambda ts: ts.get_frequency_content(),
    "get_frequency_content(window='hann')": lambda ts: ts.get_frequency_content(window="hann"),
    "compute_fft_power": lambda ts: ts.compute_fft_power(),
    "get_peak_freq": lambda ts: ts.get_peak_freq(),
    "relative_band_power": lambda ts: ts.relative_band_power(),
    "falff": lambda ts: ts.falff(),
    "plot_fft_power": lambda ts: plot_fft_power(ts),
    "utils.compute_fft_power": lambda ts: utils.compute_fft_power(ts),
    "utils.get_peak_freq": lambda ts: utils.get_peak_freq(ts),
    "utils.relative_band_power": lambda ts: utils.relative_band_power(ts),
    "utils.falff": lambda ts: utils.falff(ts),
}


@pytest.mark.parametrize("name", list(ENTRY_POINTS))
def test_an_empty_series_is_a_valueerror_everywhere(name):
    """The whole family, not just the one sibling that already checked.

    `match` pins the shared message by the words the old local copy in
    compute_fft_power never had. Its message, "Time series data is empty",
    is a prefix of the shared one, so matching on that prefix could not tell
    the door from the copy for the two compute_fft_power routes (review
    round 1, agy). A sixth local copy with its own wording fails here too.
    """
    with pytest.raises(ValueError, match=SHARED_MESSAGE):
        ENTRY_POINTS[name](_empty())


@pytest.mark.parametrize("name", list(ENTRY_POINTS))
def test_an_empty_series_raises_without_warning(name):
    """No RuntimeWarning on the way to the error.

    `relative_band_power` takes `np.std` of the data before it reaches the
    FFT, and numpy warns "Degrees of freedom <= 0" on an empty array. A
    diagnosis that arrives with a warning attached reads as two problems.
    Every entry point is checked, not only the one known to warn, so a
    reordering elsewhere cannot reintroduce it quietly.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(ValueError, match=SHARED_MESSAGE):
            ENTRY_POINTS[name](_empty())


def test_plot_fft_power_draws_nothing_for_an_empty_series():
    """The #34 draws-nothing guarantee holds for the rejection this adds."""
    empty = _empty()
    before = set(plt.get_fignums())
    with pytest.raises(ValueError, match=SHARED_MESSAGE):
        plot_fft_power(empty)
    assert set(plt.get_fignums()) == before


class TestTheSharedDoor:
    """`utils.validate_non_empty` is the one definition."""

    @pytest.mark.parametrize("data", [
        [],
        np.array([]),
        np.array([], dtype=int),
        np.empty((0, 3)),
        (),
    ], ids=["list", "float64", "int64", "2d-zero-rows", "tuple"])
    def test_rejects_anything_with_no_elements(self, data):
        with pytest.raises(ValueError, match=SHARED_MESSAGE):
            utils.validate_non_empty(data)

    @pytest.mark.parametrize("data", [
        [0.0],
        np.array([1.0, 2.0]),
        np.array(5.0),
        np.array([np.nan]),
    ], ids=["one-element-list", "two-floats", "0-d", "one-nan"])
    def test_accepts_anything_with_at_least_one_element(self, data):
        """Emptiness only: a NaN is `validate_finite_data`'s to reject, and a
        0-d array holds one value."""
        assert utils.validate_non_empty(data) is None


class TestTheOneSampleDecision:
    """Only the empty series is rejected by the door. One sample is not.

    A 1-sample spectrum is one DC bin and arguably meaningless, but it is not
    a division by zero, and rejecting it would turn two currently-succeeding
    calls into failures on a threshold that does not buy a meaningful
    spectrum anyway (two samples also yield a DC-only spectrum). The decision
    is recorded here so that changing it is a deliberate edit to a rule, not
    a drift.
    """

    def test_get_frequency_content_returns_the_dc_bin(self):
        freqs, power = _one_sample().get_frequency_content()
        assert freqs.tolist() == [0.0]
        assert len(power) == 1

    def test_compute_fft_power_keeps_its_own_minimum_of_two(self):
        """Its threshold is its own contract and is not the door's."""
        with pytest.raises(ValueError, match="minimum 2 points"):
            _one_sample().compute_fft_power()
