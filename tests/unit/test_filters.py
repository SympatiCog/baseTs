"""
Unit tests for baseTs.filters parameter validation.
"""
import re

import numpy as np
import pytest

from baseTs import baseTs
from baseTs.filters import (
    InvalidParameterError,
    bandpass_filter,
    validate_band_params,
)


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


class TestWindowingParamsAreGuardedLikeTheBandEdges:
    """`max(1, window_step - overlap)` is the same defect one line down (#30).

    The first version of this fix replaced `max(hp_hz, lp_hz)` while leaving
    `max(1, window_step - overlap)` directly beneath it — and `max()` is
    order-dependent on NaN there for exactly the same reason. A NaN window
    step compared False against 1 and was silently clamped to 1, so the filter
    ran on a rate the caller never asked for. A string or None died on the
    subtraction with a bare TypeError before any validation ran at all.

    Fixing one and shipping the other, in a commit whose message is about this
    defect class, is not a defensible place to stop.
    """

    FS = 10.0

    @classmethod
    def _data(cls):
        return np.sin(np.arange(500) / 10.0)

    BAD_WINDOWING = [
        ("NaN window_step", dict(window_step=np.nan)),
        ("NaN overlap", dict(overlap=np.nan)),
        ("string window_step", dict(window_step="1")),
        ("None window_step", dict(window_step=None)),
        ("string overlap", dict(overlap="0")),
        ("None overlap", dict(overlap=None)),
    ]

    OVERSIZED = [
        ("huge int overlap", dict(overlap=10 ** 400)),
        ("huge int window_step", dict(window_step=10 ** 400)),
    ]

    @pytest.mark.parametrize(
        "label,kwargs", OVERSIZED, ids=[c[0] for c in OVERSIZED]
    )
    def test_an_int_too_large_for_float_is_rejected_not_raised_through(self, label, kwargs):
        """`float(10**400)` raises OverflowError, which is not our contract.

        A Python int is a numbers.Real, so it passes the membership test and
        then dies on the conversion. The first draft of this guard did the
        conversion unwrapped, which turned `overlap=10**400` from silently
        succeeding on main - `max(1, 1 - 10**400)` is fine in int arithmetic -
        into a bare OverflowError. Making a wrong answer into an exception is
        an improvement; making it into an exception outside the contract this
        change exists to restore is not.

        `window_step=10**400` already raised OverflowError on main, through
        `sample_Hz / window_step`. The guard claimed to close that class and
        did not until now.
        """
        with pytest.raises(InvalidParameterError, match="is too large to convert"):
            bandpass_filter(
                self._data(), hp_hz=0.1, lp_hz=0.4, sample_Hz=self.FS, **kwargs
            )

    @pytest.mark.parametrize(
        "label,kwargs", BAD_WINDOWING, ids=[c[0] for c in BAD_WINDOWING]
    )
    def test_bad_windowing_param_raises_invalid_parameter_error(self, label, kwargs):
        with pytest.raises(InvalidParameterError, match="must be a real number"):
            bandpass_filter(
                self._data(), hp_hz=0.1, lp_hz=0.4, sample_Hz=self.FS, **kwargs
            )

    def test_a_nan_window_step_no_longer_runs_silently(self):
        """The worst of them: it produced output rather than an error."""
        with pytest.raises(InvalidParameterError):
            bandpass_filter(
                self._data(), hp_hz=0.1, lp_hz=0.4, sample_Hz=self.FS,
                window_step=np.nan,
            )

    def test_window_step_below_one_is_rejected_when_called_directly(self):
        """validate_band_params is public, so it cannot rely on its caller.

        `bandpass_filter` clamps with max(1, ...) before calling in, but a
        direct caller has no such floor, and a sub-1 step would inflate the
        effective rate above the real one.
        """
        for bad in (0, -1, 0.5):
            with pytest.raises(InvalidParameterError, match="[Ww]indow step"):
                validate_band_params(self._data(), self.FS, 0.1, 0.4, 3,
                                     window_step=bad)


class TestNonScalarBandEdgesKeepTheContract:
    """An array edge escaped with numpy's ambiguity error, on main and after.

    `if not (edge > 0)` on an array raises "The truth value of an array with
    more than one element is ambiguous" — a bare ValueError, so the
    InvalidParameterError contract had a hole left in it by a fix whose whole
    subject is that contract.

    Membership is tested with numbers.Real rather than float(), deliberately:
    `float(np.array([0.1]))` returns 0.1 on numpy 1.x and raises on 2.x, so a
    float()-based guard would accept a one-element array on one CI leg and
    reject it on another, with the suite green either way.
    """

    FS = 10.0

    @classmethod
    def _data(cls):
        return np.sin(np.arange(500) / 10.0)

    @pytest.mark.parametrize("edge", [
        np.array([0.1, 0.2]),
        np.array([0.1]),
        [0.1],
        None,
        "0.1",
    ], ids=["2-element array", "1-element array", "list", "None", "string"])
    def test_non_scalar_lower_edge(self, edge):
        with pytest.raises(InvalidParameterError, match="Band edge hp_hz"):
            bandpass_filter(self._data(), hp_hz=edge, lp_hz=0.4, sample_Hz=self.FS)

    @pytest.mark.parametrize("edge", [
        np.array([0.4, 0.5]),
        np.array([0.4]),
        [0.4],
        None,
        "0.4",
    ], ids=["2-element array", "1-element array", "list", "None", "string"])
    def test_non_scalar_upper_edge(self, edge):
        with pytest.raises(InvalidParameterError, match="Band edge lp_hz"):
            bandpass_filter(self._data(), hp_hz=0.1, lp_hz=edge, sample_Hz=self.FS)

    def test_a_numpy_scalar_edge_is_still_accepted(self):
        """The guard must not reject the numeric types callers really pass."""
        out = bandpass_filter(
            self._data(), hp_hz=np.float64(0.1), lp_hz=np.float32(0.4),
            sample_Hz=self.FS,
        )

        assert np.all(np.isfinite(out))


class TestRejectionMessagesNameTheRealLimit:
    """A message that states no number sends the caller round the loop twice.

    At sample_Hz=10 and window_step=4 the effective Nyquist is 1.25 Hz. The
    first version of this fix reported an out-of-range lp_hz with a message
    carrying no number at all, and checked it against the *declared* Nyquist
    of 5.0 — so a caller who reasonably retried at 2.0 failed again, against
    a limit nothing had mentioned.

    This is the #28 lesson generalised: an error message that names a remedy
    is code, so the remedy has to be executed rather than asserted. These
    tests take the limit out of the message and check that a band under it is
    actually accepted.
    """

    FS = 10.0

    @classmethod
    def _data(cls):
        return np.sin(np.arange(500) / 10.0)

    @staticmethod
    def _limit_from(message):
        """Pull the Nyquist figure the message quotes."""
        found = re.findall(r"([0-9]*\.?[0-9]+)\s*Hz", message)
        assert found, f"message quotes no limit in Hz: {message!r}"
        return float(found[-1])

    def test_message_quotes_the_effective_limit_not_the_declared_one(self):
        with pytest.raises(InvalidParameterError) as excinfo:
            bandpass_filter(self._data(), hp_hz=0.5, lp_hz=6.0,
                            sample_Hz=self.FS, window_step=4)

        assert self._limit_from(str(excinfo.value)) == pytest.approx(1.25)

    def test_following_the_message_actually_works(self):
        """Execute the remedy rather than asserting the string."""
        with pytest.raises(InvalidParameterError) as excinfo:
            bandpass_filter(self._data(), hp_hz=0.5, lp_hz=6.0,
                            sample_Hz=self.FS, window_step=4)
        limit = self._limit_from(str(excinfo.value))

        out = bandpass_filter(self._data(), hp_hz=0.1, lp_hz=limit * 0.9,
                              sample_Hz=self.FS, window_step=4)

        assert np.all(np.isfinite(out))

    def test_the_band_edge_message_quotes_its_limit_too(self):
        with pytest.raises(InvalidParameterError) as excinfo:
            bandpass_filter(self._data(), hp_hz=6.0, lp_hz=4.0, sample_Hz=self.FS)

        assert self._limit_from(str(excinfo.value)) == pytest.approx(5.0)


class TestTheInvalidParameterContractIsComplete:
    """Every known bad input raises InvalidParameterError, enumerated.

    The CHANGELOG entry for #30 quotes this list. An earlier draft of it named
    a case that was never breaking, omitted three that were, and gave a count
    matching neither - written from recall rather than from measurement, which
    is the failure #27 ended by asserting its census instead of describing it.
    The same move here: the enumeration lives in the suite, so a case that
    stops holding the contract fails a test rather than quietly making a
    paragraph wrong.
    """

    FS = 10.0

    @classmethod
    def _data(cls):
        return np.sin(np.arange(500) / 10.0)

    #: (label, kwargs, message fragment, changed by this fix)
    #:
    #: The fourth field is what makes this a census rather than a list. An
    #: earlier revision asserted only that each case raises, which stays green
    #: however the breaking-change enumeration drifts - it could not tell a
    #: case this fix changed from one that already behaved. The `main` column
    #: is frozen history (main = pre-#30), so recording it as data is a fact,
    #: not a cached value that can go stale.
    #:
    #: The fragment is what makes each case pin its own check. Type-only
    #: assertions cannot tell the intended guard firing from some other guard
    #: that also raises InvalidParameterError.
    BAD_INPUTS = [
        ("lower: negative", dict(hp_hz=-1.0, lp_hz=0.4), "Band edge hp_hz", True),
        ("lower: zero", dict(hp_hz=0.0, lp_hz=0.4), "Band edge hp_hz", True),
        # Already InvalidParameterError before this fix: max(nan, 0.4) returns
        # nan, which the pre-existing NaN-safe cutoff check caught.
        ("lower: NaN", dict(hp_hz=np.nan, lp_hz=0.4), "Band edge hp_hz", False),
        ("lower: non-scalar", dict(hp_hz=np.array([0.1, 0.2]), lp_hz=0.4),
         "Band edge hp_hz", True),
        ("upper: negative", dict(hp_hz=0.1, lp_hz=-0.4), "Cutoff frequency", True),
        ("upper: zero", dict(hp_hz=0.1, lp_hz=0.0), "Cutoff frequency", True),
        ("upper: NaN", dict(hp_hz=0.1, lp_hz=np.nan), "Cutoff frequency", True),
        ("upper: non-scalar", dict(hp_hz=0.1, lp_hz=np.array([0.4, 0.5])),
         "Band edge lp_hz", True),
        ("edges transposed", dict(hp_hz=0.4, lp_hz=0.1),
         "Band edges out of order", True),
        ("edges equal", dict(hp_hz=0.2, lp_hz=0.2),
         "Band edges out of order", True),
        ("upper past effective Nyquist", dict(hp_hz=0.5, lp_hz=4.0, window_step=4),
         "Cutoff frequency", True),
        ("window_step NaN", dict(hp_hz=0.1, lp_hz=0.4, window_step=np.nan),
         "window_step must be a real number", True),
        ("window_step non-numeric", dict(hp_hz=0.1, lp_hz=0.4, window_step="1"),
         "window_step must be a real number", True),
        ("overlap non-numeric", dict(hp_hz=0.1, lp_hz=0.4, overlap=None),
         "overlap must be a real number", True),
        ("overlap too large", dict(hp_hz=0.1, lp_hz=0.4, overlap=10 ** 400),
         "overlap is too large", True),
        ("window_step too large", dict(hp_hz=0.1, lp_hz=0.4, window_step=10 ** 400),
         "window_step is too large", True),
        # Already InvalidParameterError before this fix, via the pre-existing
        # rate guard from #24.
        ("degenerate rate", dict(hp_hz=0.1, lp_hz=0.4, sample_Hz=np.nan),
         "Invalid sampling frequency", False),
    ]

    #: The count quoted in the CHANGELOG entry for #30, asserted below.
    BEHAVIOUR_CHANGES_CLAIMED = 15

    @pytest.mark.parametrize(
        "label,kwargs,fragment,changed",
        BAD_INPUTS,
        ids=[c[0] for c in BAD_INPUTS],
    )
    def test_the_contract_holds_for_every_known_bad_input(
        self, label, kwargs, fragment, changed
    ):
        kwargs = {'sample_Hz': self.FS, **kwargs}

        with pytest.raises(InvalidParameterError, match=fragment):
            bandpass_filter(self._data(), **kwargs)

    def test_the_breaking_change_count_matches_the_changelog(self):
        """The number in the prose is asserted against the table.

        Adding a case without classifying it, or reclassifying one, now fails
        here instead of quietly making a CHANGELOG paragraph wrong.
        """
        changed = [c for c in self.BAD_INPUTS if c[3]]
        unchanged = [c for c in self.BAD_INPUTS if not c[3]]

        assert len(changed) == self.BEHAVIOUR_CHANGES_CLAIMED
        assert [c[0] for c in unchanged] == ["lower: NaN", "degenerate rate"]


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
