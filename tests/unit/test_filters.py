"""
Unit tests for baseTs.filters parameter validation.
"""
import numbers
import re
from fractions import Fraction

import numpy as np
import pytest

from baseTs import baseTs
from baseTs.filters import (
    InvalidParameterError,
    bandpass_filter,
    highpass_filter,
    lowpass_filter,
    notch_filter,
    validate_band_params,
    validate_filter_params,
)


@numbers.Real.register
class _UnconvertibleReal:
    """Registers as a Real but cannot become one.

    numbers.Real is a registrable ABC, so membership does not imply a working
    __float__. This class has none at all, which makes float() raise TypeError
    - one of the conversion errors an `except OverflowError` alone let escape
    the InvalidParameterError contract.
    """


@numbers.Real.register
class _DeclaresOneHz:
    """A Real that converts to 1.0 and supports nothing else.

    Registers, coerces, passes every range check - and then has no
    __truediv__, so it used to die in signal.butter past all validation.
    """

    def __float__(self):
        return 1.0


@numbers.Real.register
class _LiesAboutDivision:
    """Converts to 1.0 but divides to something else entirely.

    The nastier half of the same hole: validation saw 1.0, scipy saw a
    near-Nyquist Wn, and the mismatch surfaced as a bare scipy ValueError
    about `Wn` internals - the exact failure mode this whole change exists to
    remove.
    """

    def __float__(self):
        return 1.0

    def __truediv__(self, other):
        return 0.999999


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
        """All of these must raise; four of the seven previously did not.

        The negative, zero, transposed and equal cases reached scipy on main
        and raised a bare ValueError. The other three - NaN lower edge, and a
        lower edge at or above Nyquist - were already InvalidParameterError,
        because `max(hp_hz, lp_hz)` happens to select the offending value in
        each. They are here for coverage of the message, not as evidence of a
        behaviour change; TestTheInvalidParameterContractIsComplete carries the
        per-case classification and is what the CHANGELOG's count comes from.

        An earlier docstring claimed all seven changed. That was the census
        error over again in a place the census does not reach, which is worth
        saying out loud: asserting the count fixed the table, not the prose
        around it.
        """
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


class TestTheValidatedValueIsTheOneThatGetsFiltered:
    """Validation is worthless if the filter then uses a different value.

    Five review rounds audited validate_band_params' internals. None looked at
    the line that consumes the result: `signal.butter(3, [hp_hz/nyq,
    lp_hz/nyq])` divided the caller's *original* object, because the coerced
    edges were local to the validator and never came back. So an edge could be
    validated as 1.0 and then divide to something else entirely - or fail to
    divide at all - and the call died past every guard, with a bare exception.

    Enumerating the call sites inside a function is not the same as
    enumerating the surface: the escape was one line outside it.
    """

    FS = 10.0

    @classmethod
    def _data(cls):
        return np.sin(np.arange(500) / 10.0)

    def test_an_edge_with_no_truediv_is_still_filtered(self):
        """It declared float() == 1.0, so 1.0 is what the filter must use."""
        out = bandpass_filter(
            self._data(), hp_hz=_DeclaresOneHz(), lp_hz=4.0, sample_Hz=self.FS
        )

        assert np.all(np.isfinite(out))

    def test_a_lying_truediv_cannot_change_the_band(self):
        """The value validated is the value filtered, whatever __truediv__ says."""
        lying = bandpass_filter(
            self._data(), hp_hz=_LiesAboutDivision(), lp_hz=4.0, sample_Hz=self.FS
        )
        honest = bandpass_filter(
            self._data(), hp_hz=1.0, lp_hz=4.0, sample_Hz=self.FS
        )

        np.testing.assert_array_equal(lying, honest)

    def test_an_exact_type_filters_as_its_float(self):
        """Fraction and Decimal are legitimate Reals, not adversarial ones."""
        from decimal import Decimal
        from fractions import Fraction

        expected = bandpass_filter(
            self._data(), hp_hz=0.5, lp_hz=4.0, sample_Hz=self.FS
        )

        for edge in (Fraction(1, 2), Decimal("0.5")):
            out = bandpass_filter(
                self._data(), hp_hz=edge, lp_hz=4.0, sample_Hz=self.FS
            )
            np.testing.assert_array_equal(out, expected)


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

    #: The census is BUILT, not hand-listed.
    #:
    #: Three revisions of this table got the count wrong, and the last miss was
    #: the tell: `window_step=NaN` had a row and `overlap=NaN` did not, though
    #: `max(1, window_step - overlap)` is order-dependent on NaN for either
    #: operand. A hand-maintained list of a symmetric family will keep losing
    #: one half of it. So the symmetric families are generated as products and
    #: only the genuinely one-off cases are written out.
    #:
    #: Each row carries the fragment its own guard produces - specific enough
    #: to pin which check fired, not merely which parameter was at fault - and
    #: a flag for whether this change altered the behaviour. `main` is frozen
    #: history (main = pre-#30), so recording it as data is a fact rather than
    #: a cached value that can go stale.

    #: value -> per-edge (fragment, changed-by-this-fix)
    EDGE_CASES = {
        'negative': (-1.0, {
            'hp_hz': (r"Band edge hp_hz must be positive and less than", True),
            'lp_hz': (r"Cutoff frequency must be positive", True)}),
        'zero': (0.0, {
            'hp_hz': (r"Band edge hp_hz must be positive and less than", True),
            'lp_hz': (r"Cutoff frequency must be positive", True)}),
        # A NaN *lower* edge already raised InvalidParameterError before this
        # change: max(nan, 0.4) returns nan, which the pre-existing NaN-safe
        # cutoff check caught. A NaN *upper* edge did not - max(0.1, nan)
        # returns 0.1. That asymmetry is the whole bug.
        'NaN': (np.nan, {
            'hp_hz': (r"Band edge hp_hz must be positive and less than", False),
            'lp_hz': (r"Cutoff frequency must be positive", True)}),
        'non-scalar': (np.array([0.1, 0.2]), {
            'hp_hz': (r"Band edge hp_hz must be a real number", True),
            'lp_hz': (r"Band edge lp_hz must be a real number", True)}),
        # Already InvalidParameterError on main, where the range check caught
        # it by comparing a big int against a float exactly. Now caught one
        # step earlier by the coercion, so the message changed and the
        # behaviour did not.
        'too large': (10 ** 400, {
            'hp_hz': (r"Band edge hp_hz is too large", False),
            'lp_hz': (r"Band edge lp_hz is too large", False)}),
        # A Real that cannot be coerced. The band edges take the same path the
        # windowing parameters do, so this case has to exist on both.
        'unconvertible': (_UnconvertibleReal(), {
            'hp_hz': (r"Band edge hp_hz could not be converted", True),
            'lp_hz': (r"Band edge lp_hz could not be converted", True)}),
    }

    #: value -> (fragment template, changed-by-this-fix)
    WINDOW_CASES = {
        'NaN': (np.nan, r"{p} must be a real number and finite", True),
        'non-numeric': (None, r"{p} must be a real number, got", True),
        'too large': (10 ** 400, r"{p} is too large", True),
        'unconvertible': (_UnconvertibleReal(), r"{p} could not be converted", True),
    }

    #: Genuinely one-off - no symmetric partner to lose.
    ONE_OFF = [
        ("edges transposed", dict(hp_hz=0.4, lp_hz=0.1),
         r"Band edges out of order", True),
        ("edges equal", dict(hp_hz=0.2, lp_hz=0.2),
         r"Band edges out of order", True),
        ("upper past effective Nyquist",
         dict(hp_hz=0.5, lp_hz=4.0, window_step=4),
         r"Cutoff frequency must be positive", True),
        # Guarded since #24, so unchanged by this fix.
        ("degenerate rate", dict(hp_hz=0.1, lp_hz=0.4, sample_Hz=np.nan),
         r"Invalid sampling frequency", False),
        # An exact type whose value is below Nyquist but whose nearest double
        # is not. A review round read this as a narrowing introduced by the
        # coercion, because comparing the Fraction exactly accepts it. It is
        # not: float(lp) == 500.0 exactly, so scipy computes Wn == 1.0 and
        # dies. On main this passes validation and then raises a bare
        # ValueError from scipy - the very failure this change exists to stop.
        # Rejecting it up front is the guard predicting what the filter does.
        ("upper edge rounds onto Nyquist",
         dict(hp_hz=1.0, lp_hz=Fraction(500) - Fraction(1, 10 ** 16),
              sample_Hz=1000.0),
         r"Cutoff frequency must be positive", True),
    ]

    @staticmethod
    def _build_census():
        cls = TestTheInvalidParameterContractIsComplete
        rows = []
        for case, (value, per_edge) in cls.EDGE_CASES.items():
            for edge, (fragment, changed) in per_edge.items():
                other = 'lp_hz' if edge == 'hp_hz' else 'hp_hz'
                kwargs = {edge: value, other: 0.4 if edge == 'hp_hz' else 0.1}
                rows.append((f"{edge} {case}", kwargs, fragment, changed))
        for param in ('window_step', 'overlap'):
            for case, (value, template, changed) in cls.WINDOW_CASES.items():
                rows.append((f"{param} {case}",
                             dict(hp_hz=0.1, lp_hz=0.4, **{param: value}),
                             template.format(p=param), changed))
        return rows + cls.ONE_OFF

    #: The count quoted in the CHANGELOG entry for #30, asserted below.
    BEHAVIOUR_CHANGES_CLAIMED = 21

    def test_the_contract_holds_for_every_known_bad_input(self):
        """Every known bad input raises, with the message its own guard makes."""
        failures = []
        for label, kwargs, fragment, _changed in self._build_census():
            kwargs = {'sample_Hz': self.FS, **kwargs}
            try:
                bandpass_filter(self._data(), **kwargs)
                failures.append(f"{label}: no exception")
            except InvalidParameterError as exc:
                if not re.search(fragment, str(exc)):
                    failures.append(
                        f"{label}: {str(exc)!r} does not match {fragment!r}")
            except Exception as exc:  # noqa: BLE001 - the point of the test
                failures.append(
                    f"{label}: {type(exc).__name__} escaped the contract: {exc}")

        assert not failures, "\n".join(failures)

    def test_the_breaking_change_count_matches_the_changelog(self):
        """The number in the prose is asserted against the table.

        Adding a case without classifying it, or reclassifying one, now fails
        here instead of quietly making a CHANGELOG paragraph wrong.
        """
        census = self._build_census()
        changed = [c for c in census if c[3]]
        unchanged = [c for c in census if not c[3]]

        assert len(changed) == self.BEHAVIOUR_CHANGES_CLAIMED
        assert sorted(c[0] for c in unchanged) == [
            "degenerate rate", "hp_hz NaN", "hp_hz too large", "lp_hz too large",
        ]

    def test_every_fragment_pins_its_own_case(self):
        """A fragment true of another case's message pins nothing.

        Three fragments were previously too loose - a bare "real number"
        matched the non-scalar *edge* messages as well as the windowing ones.
        Cross-matching every fragment against every message is what found
        that; reading them did not.
        """
        messages = {}
        for label, kwargs, fragment, _ in self._build_census():
            try:
                bandpass_filter(self._data(), **{'sample_Hz': self.FS, **kwargs})
                messages[label] = ("", fragment)
            except InvalidParameterError as exc:
                messages[label] = (str(exc), fragment)

        collisions = {
            label: [other for other, (msg, _) in messages.items()
                    if other != label
                    and messages[other][1] != fragment
                    and re.search(fragment, msg)]
            for label, (_, fragment) in messages.items()
        }
        collisions = {k: v for k, v in collisions.items() if v}

        assert not collisions, f"fragments reaching foreign cases: {collisions}"


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


class TestTheSingleCutoffFiltersUseTheValidatedValue:
    """#30 closed the validate-one-compute-with-another hole for bandpass_filter
    alone. lowpass_filter, highpass_filter and notch_filter kept dividing the
    caller's original cutoff object after validate_filter_params had
    range-checked it and thrown the checked value away (#49).

    The helpers are the ones #30's tests built: a Real with no __truediv__,
    and one whose __truediv__ disagrees with its __float__.
    """

    FS = 10.0

    @classmethod
    def _data(cls):
        return np.sin(np.arange(500) / 10.0)

    FILTERS = [
        ("lowpass_filter", lambda d, c, fs: lowpass_filter(d, c, fs)),
        ("highpass_filter", lambda d, c, fs: highpass_filter(d, c, fs)),
        ("notch_filter", lambda d, c, fs: notch_filter(d, c, fs)),
    ]

    @pytest.mark.parametrize("name, run", FILTERS, ids=[f[0] for f in FILTERS])
    def test_a_cutoff_with_no_truediv_is_still_filtered(self, name, run):
        out = run(self._data(), _DeclaresOneHz(), self.FS)

        assert np.all(np.isfinite(out))

    @pytest.mark.parametrize("name, run", FILTERS, ids=[f[0] for f in FILTERS])
    def test_a_lying_truediv_cannot_change_the_cutoff(self, name, run):
        lying = run(self._data(), _LiesAboutDivision(), self.FS)
        honest = run(self._data(), 1.0, self.FS)

        np.testing.assert_array_equal(lying, honest)

    @pytest.mark.parametrize("name, run", FILTERS, ids=[f[0] for f in FILTERS])
    def test_an_exact_type_filters_as_its_float(self, name, run):
        from decimal import Decimal

        expected = run(self._data(), 0.5, self.FS)

        for cutoff in (Fraction(1, 2), Decimal("0.5")):
            np.testing.assert_array_equal(run(self._data(), cutoff, self.FS), expected)

    @pytest.mark.parametrize("name, run", FILTERS, ids=[f[0] for f in FILTERS])
    def test_an_unconvertible_cutoff_is_an_invalid_parameter(self, name, run):
        with pytest.raises(InvalidParameterError, match="Cutoff frequency"):
            run(self._data(), _UnconvertibleReal(), self.FS)

    def test_the_validator_returns_what_it_checked(self):
        """Callers can only compute with the checked values if they get them."""
        from decimal import Decimal

        fs, cutoff, order = validate_filter_params(
            self._data(), Decimal("10"), Decimal("0.5"), np.int64(4))

        assert (fs, cutoff, order) == (10.0, 0.5, 4)
        assert type(fs) is float and type(cutoff) is float and type(order) is int


class TestFilterOrderIsValidated:
    """`order <= 0` was the whole check. `True` passed it and built an order-1
    filter; `'4'` died in the comparison with a bare TypeError; `3.5` passed
    and was left to scipy (#49). bandpass_filter is immune only because it
    hardcodes 3.
    """

    FS = 10.0

    @classmethod
    def _data(cls):
        return np.sin(np.arange(500) / 10.0)

    @pytest.mark.parametrize("bad", [True, "4", 3.5, 0, -1, np.nan, 4.0],
                             ids=["bool", "str", "fractional", "zero", "negative",
                                  "nan", "integral float"])
    def test_a_non_positive_integer_order_is_rejected(self, bad):
        with pytest.raises(InvalidParameterError, match="Filter order"):
            lowpass_filter(self._data(), 0.5, self.FS, order=bad)

    def test_a_numpy_integer_order_is_accepted(self):
        out = lowpass_filter(self._data(), 0.5, self.FS, order=np.int64(4))

        np.testing.assert_array_equal(
            out, lowpass_filter(self._data(), 0.5, self.FS, order=4))

    def test_the_band_validator_rejects_a_bad_order_too(self):
        with pytest.raises(InvalidParameterError, match="Filter order"):
            validate_band_params(self._data(), self.FS, 0.1, 0.4, order=True)


class TestFiltfiltFiltersRejectNonFiniteData:
    """Four NaN samples in, six hundred NaN out, silently (#48).

    filtfilt's bidirectional pass propagates any NaN across the whole output.
    #28 put `utils.validate_finite_data` at the spectral family's production
    site for exactly this failure; the filter family never got it, so
    `filter_outliers() -> get_peak_freq()` raised while
    `filter_outliers() -> bandpass_at()` returned 600 NaNs and said nothing.
    """

    FS = 30.0

    @classmethod
    def _gappy(cls):
        d = np.sin(2 * np.pi * 0.5 * np.arange(600) / cls.FS)
        d[300:304] = np.nan
        return d

    FILTERS = [
        ("bandpass_filter", lambda d, fs: bandpass_filter(d, hp_hz=0.1, lp_hz=5.0, sample_Hz=fs)),
        ("lowpass_filter", lambda d, fs: lowpass_filter(d, 5.0, fs)),
        ("highpass_filter", lambda d, fs: highpass_filter(d, 0.1, fs)),
        ("notch_filter", lambda d, fs: notch_filter(d, 5.0, fs)),
    ]
    IDS = [f[0] for f in FILTERS]

    @pytest.mark.parametrize("name, run", FILTERS, ids=IDS)
    def test_a_single_interior_nan_is_rejected_with_the_remedy(self, name, run):
        with pytest.raises(InvalidParameterError, match="interpolate_gaps"):
            run(self._gappy(), self.FS)

    @pytest.mark.parametrize("name, run", FILTERS, ids=IDS)
    def test_an_inf_is_rejected_the_same_way(self, name, run):
        d = self._gappy()
        d[300:304] = np.inf
        with pytest.raises(InvalidParameterError, match="NaN or Inf"):
            run(d, self.FS)

    @pytest.mark.parametrize("name, run", FILTERS, ids=IDS)
    def test_complex_data_still_filters(self, name, run):
        """filtfilt handles complex input correctly - it filters the real and
        imaginary parts independently - so the #43 complex rejection, which is
        about one-sided spectra, does not apply here."""
        d = np.exp(2j * np.pi * 0.5 * np.arange(600) / self.FS)

        out = run(d, self.FS)

        assert out.dtype.kind == "c"
        assert np.all(np.isfinite(out))

    def test_a_bad_parameter_is_reported_before_the_data_is_scanned(self):
        """A bad call is a bug in the call; bad data is a property of the
        input. The cheap check comes first, so the caller fixes the call
        before being told about the gaps."""
        with pytest.raises(InvalidParameterError, match="Cutoff frequency"):
            lowpass_filter(self._gappy(), 20.0, self.FS)

    @pytest.mark.parametrize("band, message", [
        (dict(hp_hz=-1.0, lp_hz=5.0), "Band edge hp_hz"),
        (dict(hp_hz=5.0, lp_hz=1.0), "out of order"),
        (dict(hp_hz=0.1, lp_hz=20.0), "Cutoff frequency"),
    ], ids=["bad hp_hz", "out of order", "bad lp_hz"])
    def test_the_band_validator_also_reports_parameters_before_data(self, band, message):
        """validate_band_params checks hp_hz and the ordering *after* the
        delegated single-cutoff call, which in the first cut ended with the
        O(n) data scan - so a mistyped lower edge on gappy data reported the
        gaps, inverting the rule the line above states (review)."""
        with pytest.raises(InvalidParameterError, match=message):
            bandpass_filter(self._gappy(), sample_Hz=self.FS, **band)

    def test_the_remedy_works_end_to_end(self):
        """Executed, not just named: #28's first attempt recommended a remedy
        that reproduced the bug it reported."""
        t = np.arange(600) / self.FS
        ts = baseTs(self._gappy(), t)
        cleaned = ts.filter_outliers()               # keeps the 4 NaN (#36)

        with pytest.raises(InvalidParameterError, match="interpolate_gaps"):
            cleaned.lowpass_at(5.0)

        out = cleaned.interpolate_gaps().lowpass_at(5.0)

        assert np.all(np.isfinite(out.values))
        assert len(out) == 600

    @pytest.mark.parametrize("call", [
        lambda ts: ts.lowpass_at(5.0),
        lambda ts: ts.lowpass_filter(5.0),
        lambda ts: ts.highpass_at(0.1),
        lambda ts: ts.highpass_filter(0.1),
        lambda ts: ts.notch_at(5.0),
        lambda ts: ts.notch_filter(5.0),
        lambda ts: ts.bandpass_at(0.1, 5.0),
        lambda ts: ts.bandpass_filter(0.1, 5.0),
        lambda ts: ts.butterpass_at(0.1, 5.0),
    ], ids=["lowpass_at", "lowpass_filter", "highpass_at", "highpass_filter",
            "notch_at", "notch_filter", "bandpass_at", "bandpass_filter",
            "butterpass_at"])
    def test_every_baseTs_entry_point_agrees(self, call):
        ts = baseTs(self._gappy(), np.arange(600) / self.FS)
        with pytest.raises(InvalidParameterError, match="interpolate_gaps"):
            call(ts)

    def test_the_windowed_filters_keep_their_local_damage(self):
        """sg_filter and gauss_filter are convolutions, not bidirectional IIR
        passes: a gap stays a gap, only wider. That is degraded output rather
        than a confident wrong answer, and it matches how filter_outliers
        treats gaps it did not create (#36), so they are left alone - a
        decision, recorded here, rather than an accident of which functions
        route through validate_filter_params."""
        ts = baseTs(self._gappy(), np.arange(600) / self.FS)

        for out in (ts.sg_filter().values, ts.gauss_filter(sigma=2).values):
            bad = np.isnan(out)
            assert 4 <= bad.sum() < 60           # wider than the gap, not the series
            assert not bad[:250].any() and not bad[350:].any()


class TestTheNaNRemedyClearsAnEdgeGap:
    """#77: the NaN message names `interpolate_gaps()`, which forwards pandas'
    default `limit_direction='forward'` - so a gap at the *start* of the series
    survives it, and a caller who follows the remedy is rejected again with the
    exact message they just obeyed. The #28 pattern (a remedy that reproduces
    the bug it reports) one level up: #48 tested the remedy end to end, but only
    for an interior gap.

    A leading NaN is realistic in the documented filter_outliers() -> filter
    chain: a late acquisition start, or an outlier at sample 0.
    """

    FS = 30.0

    @classmethod
    def _with_gap(cls, where):
        d = np.sin(2 * np.pi * 0.5 * np.arange(600) / cls.FS)
        d[where] = np.nan
        return baseTs(d, np.arange(600) / cls.FS)

    def test_a_leading_gap_survives_the_named_remedy_and_the_message_says_what_it_needs(self):
        cleaned = self._with_gap(slice(0, 4)).filter_outliers()     # keeps the 4 NaN (#36)
        followed = cleaned.interpolate_gaps()                        # the remedy, as named

        assert np.isnan(followed.values[:4]).all()                   # ...which did not clear it

        with pytest.raises(InvalidParameterError, match=r"limit_direction='both'") as exc:
            followed.lowpass_at(5.0)
        assert "starts with" in str(exc.value)
        assert "NaN or Inf" in str(exc.value)          # the hint is appended, not substituted
        assert "constant fill, not an interpolation" in str(exc.value)

    def test_the_edge_remedy_the_message_names_works_end_to_end(self):
        """Executed, not just named - the whole point of #77."""
        cleaned = self._with_gap(slice(0, 4)).filter_outliers()

        filled = cleaned.interpolate_gaps(limit_direction='both')
        out = filled.lowpass_at(5.0)

        assert np.all(np.isfinite(out.values))
        assert len(out) == 600
        # The caveat the message states, measured: the edge fill is the first
        # valid value extended back, not a value interpolated towards anything.
        assert np.all(filled.values[:4] == filled.values[4])
        assert filled.values[4] == cleaned.values[4]

    def test_a_trailing_gap_is_cleared_by_the_plain_remedy(self):
        """The asymmetry the hint is built on, pinned: pandas' forward fill
        extends the last valid value over a trailing gap, so the plain remedy
        works there and the message must not send that caller to
        limit_direction - a hint that is not needed is noise the next caller
        learns to ignore."""
        ts = self._with_gap(slice(596, 600))

        with pytest.raises(InvalidParameterError, match="interpolate_gaps") as exc:
            ts.lowpass_at(5.0)
        assert "limit_direction" not in str(exc.value)

        out = ts.interpolate_gaps().lowpass_at(5.0)
        assert np.all(np.isfinite(out.values))

    def test_an_interior_gap_keeps_the_plain_message(self):
        with pytest.raises(InvalidParameterError, match="interpolate_gaps") as exc:
            self._with_gap(slice(300, 304)).lowpass_at(5.0)
        assert "limit_direction" not in str(exc.value)

    @pytest.mark.parametrize("call", [
        lambda ts: ts.lowpass_at(5.0),
        lambda ts: ts.highpass_filter(0.1),
        lambda ts: ts.notch_at(5.0),
        lambda ts: ts.bandpass_filter(0.1, 5.0),
        lambda ts: ts.butterpass_at(0.1, 5.0),
    ], ids=["lowpass_at", "highpass_filter", "notch_at", "bandpass_filter", "butterpass_at"])
    def test_the_hint_survives_the_InvalidParameterError_wrap_at_every_entry_point(self, call):
        with pytest.raises(InvalidParameterError, match=r"limit_direction='both'"):
            call(self._with_gap(slice(0, 4)))
