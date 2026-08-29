"""
Unit tests for baseTs.filters parameter validation.
"""
import numpy as np
import pytest

from baseTs import baseTs
from baseTs.filters import InvalidParameterError, bandpass_filter


class TestBandEdgeValidation:
    """Both band edges must be validated, not just max(hp_hz, lp_hz) (#30).

    `bandpass_filter` validated with `max(hp_hz, lp_hz)`, so only one edge was
    ever checked - and which one depended on argument position, because
    `max()` is order-dependent on NaN: `max(0.1, nan)` returns 0.1 and slips
    through, while `max(nan, 0.4)` returns nan and is caught. A negative,
    zero, or NaN lower edge reached scipy and died there, escaping the
    InvalidParameterError contract with a message about `Wn` internals rather
    than about the argument the caller got wrong.
    """

    FS = 10.0

    @classmethod
    def _data(cls):
        return np.sin(np.arange(500) / 10.0)

    @classmethod
    def _ts(cls):
        return baseTs(cls._data(), np.arange(500) / 10.0)

    # (label, hp_hz, lp_hz, expected message fragment)
    #
    # Fragments are deliberately distinctive. On #28 a test matched a
    # substring true of two different messages and so could not tell them
    # apart; "Band edge hp_hz" and "Band edges out of order" cannot collide,
    # and neither can collide with the generic single-cutoff message.
    BAD_BANDS = [
        ("negative lower edge", -1.0, 0.4, "Band edge hp_hz"),
        ("zero lower edge", 0.0, 0.4, "Band edge hp_hz"),
        ("NaN lower edge", np.nan, 0.4, "Band edge hp_hz"),
        ("lower edge at Nyquist", 5.0, 4.0, "Band edge hp_hz"),
        ("lower edge above Nyquist", 6.0, 4.0, "Band edge hp_hz"),
        ("transposed edges", 0.4, 0.1, "Band edges out of order"),
        ("equal edges", 0.2, 0.2, "Band edges out of order"),
    ]

    @pytest.mark.parametrize(
        "label,hp_hz,lp_hz,fragment",
        BAD_BANDS,
        ids=[c[0] for c in BAD_BANDS],
    )
    def test_bad_band_raises_invalid_parameter_error(self, label, hp_hz, lp_hz, fragment):
        """Every one of these reached scipy and raised a bare ValueError."""
        with pytest.raises(InvalidParameterError, match=fragment):
            bandpass_filter(self._data(), hp_hz=hp_hz, lp_hz=lp_hz, sample_Hz=self.FS)

    # A bad *upper* edge is caught by the delegated validate_filter_params
    # call, which runs first and carries the generic single-cutoff message.
    # Pinned rather than left to chance: it is the one place the new
    # band-specific messages do not reach, and a reader of the error would
    # otherwise be surprised.
    BAD_UPPER_EDGES = [
        ("negative upper edge", 0.1, -0.4),
        ("zero upper edge", 0.1, 0.0),
        ("NaN upper edge", 0.1, np.nan),
        ("upper edge above declared Nyquist", 0.1, 6.0),
    ]

    @pytest.mark.parametrize(
        "label,hp_hz,lp_hz",
        BAD_UPPER_EDGES,
        ids=[c[0] for c in BAD_UPPER_EDGES],
    )
    def test_bad_upper_edge_reports_the_generic_cutoff_message(self, label, hp_hz, lp_hz):
        with pytest.raises(InvalidParameterError, match="Cutoff frequency must be positive"):
            bandpass_filter(self._data(), hp_hz=hp_hz, lp_hz=lp_hz, sample_Hz=self.FS)

    def test_bad_band_names_both_values_when_out_of_order(self):
        """A message about ordering is useless without the two values in it."""
        with pytest.raises(InvalidParameterError) as excinfo:
            bandpass_filter(self._data(), hp_hz=0.4, lp_hz=0.1, sample_Hz=self.FS)

        message = str(excinfo.value)
        assert "0.4" in message and "0.1" in message

    def test_nan_upper_edge_is_caught_like_a_nan_lower_edge(self):
        """The asymmetry that made this bug position-dependent.

        `max(0.1, nan)` returns 0.1, so a NaN *upper* edge was discarded and
        the filter ran on it; `max(nan, 0.4)` returns nan, so a NaN *lower*
        edge was caught. Same argument, opposite outcome by position. Both
        must now raise.
        """
        with pytest.raises(InvalidParameterError):
            bandpass_filter(self._data(), hp_hz=0.1, lp_hz=np.nan, sample_Hz=self.FS)

    def test_upper_edge_checked_against_the_rate_the_filter_actually_uses(self):
        """Nyquist must come from the effective rate, not the declared one.

        The filter normalises by `effective_fs = sample_Hz / window_step`, but
        validation compared against `sample_Hz / 2`. At window_step=4 the
        effective Nyquist is 1.25 Hz, so lp_hz=4.0 passed validation and then
        died inside scipy.
        """
        with pytest.raises(InvalidParameterError):
            bandpass_filter(
                self._data(), hp_hz=0.5, lp_hz=4.0, sample_Hz=self.FS, window_step=4
            )

    def test_the_same_band_is_fine_at_window_step_1(self):
        """Pins that the check above is about the effective rate.

        Without this, the previous test would pass just as well if the new
        guard rejected lp_hz=4.0 outright for the wrong reason.
        """
        out = bandpass_filter(self._data(), hp_hz=0.5, lp_hz=4.0, sample_Hz=self.FS)

        assert np.all(np.isfinite(out))

    def test_a_valid_band_still_filters(self):
        """The guard must not disturb an ordinary call."""
        t = np.arange(1500) / 30.0
        data = np.sin(2 * np.pi * 0.2 * t) + np.sin(2 * np.pi * 5.0 * t)

        out = bandpass_filter(data, hp_hz=1.0, lp_hz=10.0, sample_Hz=30.0)

        def amplitude_at(values, hz):
            return abs(2.0 / len(t) * np.sum(values * np.exp(-2j * np.pi * hz * t)))

        assert amplitude_at(out, 5.0) > 0.9 * amplitude_at(data, 5.0)
        assert amplitude_at(out, 0.2) < 0.1 * amplitude_at(data, 0.2)

    def test_a_nan_rate_still_reports_the_rate_not_the_band(self):
        """Check order: a degenerate time base is the more useful complaint."""
        with pytest.raises(InvalidParameterError, match="Invalid sampling frequency"):
            bandpass_filter(self._data(), hp_hz=0.1, lp_hz=0.4, sample_Hz=np.nan)


class TestEveryBandpassEntryPointRejectsABadLowerEdge:
    """The contract must hold on all three names, on the axis it is about.

    #28's equivalent test asserted that four entry points agreed but only ever
    fed them NaN-gappy float data, so it could not see the dtype asymmetry it
    was named for. The axis here is the *lower* edge, since that is the one
    `max(hp_hz, lp_hz)` discarded - feeding these a bad upper edge would test
    the path that already worked.
    """

    @staticmethod
    def _ts():
        return baseTs(np.sin(np.arange(500) / 10.0), np.arange(500) / 10.0)

    def test_bandpass_at(self):
        with pytest.raises(InvalidParameterError, match="Band edge hp_hz"):
            self._ts().bandpass_at(hp_hz=-1.0, lp_hz=0.4)

    def test_bandpass_filter_alias(self):
        with pytest.raises(InvalidParameterError, match="Band edge hp_hz"):
            self._ts().bandpass_filter(-1.0, 0.4)

    def test_butterpass_at(self):
        """Reachable at all only since #27, which was dead before it."""
        with pytest.raises(InvalidParameterError, match="Band edge hp_hz"):
            self._ts().butterpass_at(-1.0, 0.4)
