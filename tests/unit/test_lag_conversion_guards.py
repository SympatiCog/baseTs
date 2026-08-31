"""Guards on the two lag-conversion primitives (issue #32).

`time_to_idx` and `idx_to_time` are the single door every lag consumer passes
through: `get_lags` calls one of them, `shift_timeseries` calls `get_lags`, and
`plotting.lag_plot` (hence `baseTs.lag_plot`) calls `shift_timeseries`. Before
this change neither converted value was checked, so a degenerate time base -
duplicate or non-increasing timestamps, giving a NaN derived rate - produced
`ValueError: cannot convert float NaN to integer` in seconds mode and a silent
NaN `lag_secs` in index mode.

That is the failure PR #26's audit set out to remove from `get_peaks`, one
module over; the site was simply missed. `get_peaks` deliberately still accepts
`freq <= 0` because its `max(25, ...)` floor makes the rate irrelevant there.
No such floor exists here - `idx_to_time(5, 0.0)` is a real ZeroDivisionError -
so the full `validate_sampling_freq` guard applies.

The lag itself is checked in the same place: `shift_timeseries` calls
`validate_lag` *after* `get_lags`, so the raw conversion error preempted the
diagnosis that validator exists to give.
"""
import matplotlib
matplotlib.use("Agg")

from decimal import Decimal  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

from baseTs import baseTs  # noqa: E402
from baseTs.plotting import lag_plot  # noqa: E402
from baseTs.utils import (  # noqa: E402
    ValidationError,
    get_lags,
    idx_to_time,
    shift_timeseries,
    time_to_idx,
)


def _signal(n=300):
    return np.sin(np.arange(n) / 10.0)


def _degenerate():
    """Every timestamp identical, so the derived rate is NaN.

    This is the object from #32's reproduction. Nothing about constructing it
    raises: the rate is derived from the index, and a zero duration derives to
    NaN by design.
    """
    return baseTs(_signal(), np.zeros(300))


def _uniform():
    """A well-formed 100 Hz series, rate declared so the arithmetic is exact."""
    return baseTs(_signal(), np.arange(300) / 100.0, freq=100.0)


class TestADegenerateTimeBaseIsDiagnosed:
    """The rate must be rejected where it enters the conversion.

    Each of these fails on main with the raw conversion error, or - worse, in
    index mode - does not fail at all.
    """

    def test_seconds_mode_shift_names_the_time_base(self):
        with pytest.raises(ValueError, match="degenerate"):
            shift_timeseries(_degenerate(), 0.5, "seconds")

    def test_index_mode_shift_no_longer_reports_a_nan_lag_in_seconds(self):
        """The silent half of #32.

        On main this returns successfully with `lag_secs=nan`: the shift itself
        only needs the index, so the nonsense rides along in the result dict
        (and in the plot title) rather than stopping anything.
        """
        with pytest.raises(ValueError, match="degenerate"):
            shift_timeseries(_degenerate(), 5, "index")

    def test_lag_plot_seconds_mode_names_the_time_base(self):
        try:
            with pytest.raises(ValueError, match="degenerate"):
                lag_plot(_degenerate(), 0.5, "seconds")
        finally:
            plt.close("all")

    def test_lag_plot_index_mode_names_the_time_base(self):
        """Index mode is `lag_plot`'s default, and on main it draws a plot
        titled "nan seconds" instead of refusing."""
        try:
            with pytest.raises(ValueError, match="degenerate"):
                lag_plot(_degenerate(), 5, "index")
        finally:
            plt.close("all")

    def test_the_core_method_inherits_the_guard(self):
        """`baseTs.lag_plot` delegates, so it must not need its own check."""
        try:
            with pytest.raises(ValueError, match="degenerate"):
                _degenerate().lag_plot(5)
        finally:
            plt.close("all")

    def test_get_lags_rejects_a_nan_rate_in_both_modes(self):
        for lag, unit in ((0.5, "seconds"), (5, "index")):
            with pytest.raises(ValueError, match="degenerate"):
                get_lags(lag, unit, np.nan)


class TestTheConversionPrimitivesGuardThemselves:
    """Both are public utilities, so neither can rely on its caller."""

    def test_time_to_idx_rejects_a_nan_rate(self):
        with pytest.raises(ValueError, match="Invalid sampling frequency"):
            time_to_idx(0.5, np.nan)

    def test_idx_to_time_rejects_a_nan_rate(self):
        with pytest.raises(ValueError, match="Invalid sampling frequency"):
            idx_to_time(5, np.nan)

    def test_a_zero_rate_is_a_diagnosis_not_a_zero_division(self):
        """#32 names this one explicitly: `ZeroDivisionError: float division
        by zero` says nothing about the rate that caused it."""
        with pytest.raises(ValueError, match="Invalid sampling frequency"):
            idx_to_time(5, 0.0)

    def test_a_zero_rate_is_rejected_by_time_to_idx_too(self):
        """It does not divide, so it dies silently instead: `int(0.5 * 0.0)`
        is a perfectly good 0, and `validate_lag` then blames the lag."""
        with pytest.raises(ValueError, match="Invalid sampling frequency"):
            time_to_idx(0.5, 0.0)

    @pytest.mark.parametrize("bad", [np.inf, -np.inf, -100.0, "100", None])
    def test_every_unusable_rate_is_refused_by_both(self, bad):
        with pytest.raises(ValueError, match="Invalid sampling frequency"):
            time_to_idx(0.5, bad)
        with pytest.raises(ValueError, match="Invalid sampling frequency"):
            idx_to_time(5, bad)


class TestANonFiniteLagIsDiagnosed:
    """`validate_lag` never gets to speak, because `get_lags` converts first.

    The rate is fine in all of these; the lag is what cannot be converted.
    """

    @pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
    def test_a_non_finite_lag_in_seconds_is_a_validation_error(self, bad):
        with pytest.raises(ValidationError, match="no corresponding index"):
            shift_timeseries(_uniform(), bad, "seconds")

    @pytest.mark.parametrize("bad", [np.nan, np.inf])
    def test_time_to_idx_refuses_a_non_finite_lag_directly(self, bad):
        with pytest.raises(ValidationError, match="no corresponding index"):
            time_to_idx(bad, 100.0)

    @pytest.mark.parametrize("bad", ["0.5", b"0.5", None, np.array([0.5, 1.0])])
    def test_a_lag_that_is_not_a_real_number_is_refused(self, bad):
        """A string lag dies on main with `can't multiply sequence by
        non-int`. It must not start being *accepted* either: `float("0.5")`
        succeeds, so a coercing guard without a str exclusion would widen what
        the conversion takes."""
        with pytest.raises(ValidationError, match="[Ll]ag"):
            time_to_idx(bad, 100.0)

    def test_the_lag_error_type_matches_the_validator_it_precedes(self):
        """One argument, one exception type. `validate_lag` raises
        ValidationError for every other bad lag; a non-finite one arriving as a
        bare ValueError would mean callers need two excepts for one problem."""
        with pytest.raises(ValidationError):
            shift_timeseries(_uniform(), np.nan, "seconds")

    def test_an_int_too_large_for_a_float_is_refused(self):
        """float(10**400) raises OverflowError, which is neither TypeError nor
        ValueError - so catching only those two lets it escape the
        ValidationError contract, exactly as it escapes int() today."""
        with pytest.raises(ValidationError, match="[Ll]ag"):
            time_to_idx(10 ** 400, 100.0)

    def test_a_non_finite_lag_in_index_mode_still_reaches_validate_lag(self):
        """Unchanged, and deliberately so: `idx_to_time` divides rather than
        truncating, so a NaN index flows through to `validate_lag`, which
        already diagnoses it as a non-integer lag - and does it better, because
        it knows index mode is what the caller asked for."""
        with pytest.raises(ValidationError, match="positive nonzero integer"):
            shift_timeseries(_uniform(), np.nan, "index")


class TestBothModesRefuseANonNumericLagTheSameWay:
    """One argument, one exception type, whichever mode it arrives in.

    Guarding only `time_to_idx` would leave the two modes disagreeing about
    the same bad lag: seconds mode raising ValidationError while index mode
    dies on `"0.5" / 100.0` with a bare TypeError. Both are unusable for the
    same reason, so both are refused in the same terms.

    Finiteness is deliberately *not* symmetric: `int()` cannot take a NaN and
    has to refuse it here, while division can, so a NaN index keeps flowing
    through to `validate_lag`'s better-targeted message above.
    """

    @pytest.mark.parametrize("bad", ["0.5", b"0.5", None])
    def test_index_mode_refuses_it_through_the_shift(self, bad):
        with pytest.raises(ValidationError, match="[Ll]ag"):
            shift_timeseries(_uniform(), bad, "index")

    @pytest.mark.parametrize("bad", ["0.5", b"0.5", None, 10 ** 400])
    def test_idx_to_time_refuses_it_directly(self, bad):
        with pytest.raises(ValidationError, match="[Ll]ag"):
            idx_to_time(bad, 100.0)

    @pytest.mark.parametrize("unit", ["seconds", "index"])
    def test_the_rate_is_named_first_when_both_are_bad(self, unit):
        """Two bad arguments must produce the same first complaint in either
        mode. Left to Python's evaluation order, `_coerce_lag(lag) / rate`
        blames the lag while `int(secs * rate)` blames the rate - the same call
        diagnosed two ways depending on which unit the caller chose.
        """
        with pytest.raises(ValueError, match="degenerate"):
            shift_timeseries(_degenerate(), "0.5", unit)

    def test_a_numeric_but_non_integer_index_is_still_validate_lags_to_judge(self):
        """Coercion must not start *accepting* what validate_lag rejects: a
        Decimal converts cleanly, so the division succeeds and the integer
        rule is applied where it has always lived."""
        from decimal import Decimal

        with pytest.raises(ValidationError, match="positive nonzero integer"):
            shift_timeseries(_uniform(), Decimal("5"), "index")


class TestAFiniteInputCannotProduceANonFiniteResult:
    """Checking the operands is not the same as checking the result.

    Both arguments can pass their own guard and still combine into something
    the conversion cannot express: `1e300 s * 1e300 Hz` is `inf`, so `int()`
    raised a bare OverflowError - the very class of raw-conversion leak this
    module exists to stop, and one the docstring now promises not to emit.
    Division has the mirror case: `10**300 / 1e-300` is `inf`, which nothing
    downstream catches, because `validate_lag` only asks whether the *index*
    is a positive int and never looks at the seconds derived from it.

    Both were reachable on main too. What is new is the promise, so the
    promise is what has to be made true.
    """

    def test_a_product_that_overflows_is_a_diagnosis(self):
        with pytest.raises(ValidationError, match="conversion overflows"):
            time_to_idx(1e300, 1e300)

    def test_a_quotient_that_overflows_is_a_diagnosis(self):
        with pytest.raises(ValidationError, match="conversion overflows"):
            idx_to_time(10 ** 300, 1e-300)

    def test_the_overflowing_seconds_no_longer_reach_the_result(self):
        """`lag_secs=inf` used to ride out into the returned dict and the plot
        title, which is #32's silent failure in a different disguise."""
        tiny_rate = baseTs(_signal(), np.arange(300) / 100.0, freq=1e-300)

        with pytest.raises(ValidationError, match="conversion overflows"):
            shift_timeseries(tiny_rate, 10 ** 300, "index")

    def test_a_non_finite_input_is_still_the_other_guards_business(self):
        """The result check must not swallow the NaN index that validate_lag
        diagnoses better: only a *finite* input is promised a finite result."""
        assert np.isnan(idx_to_time(np.nan, 100.0))

    def test_a_large_but_representable_product_still_converts(self):
        """The check is finiteness, not a magnitude policy. This is absurd
        input, but it has an exact answer and always returned one."""
        assert time_to_idx(1e300, 100.0) == int(1e302)


class TestTheOutcomeCensusIsComplete:
    """The CHANGELOG's census, asserted rather than described.

    Every earlier branch in this arc that wrote a behaviour census in prose got
    it wrong at least once, and #30 ended by generating the table and asserting
    it instead. This is that table: every lag shape, both units, both time
    bases. A new lag shape has to be classified here or `test_every_lag_is
    _classified` fails, which is the point.
    """

    LAG_SHAPES = {
        "seconds_float": 0.5,
        "whole_number": 50,
        "nan": np.nan,
        "inf": np.inf,
        "negative_inf": -np.inf,
        "str": "0.5",
        "bytes": b"0.5",
        "none": None,
        "array": np.array([0.5, 1.0]),
        "array_0d": np.array(0.5),
        "int_beyond_float": 10 ** 400,
        "decimal": Decimal("0.5"),
        "bool": True,
        "zero": 0,
        "negative": -5,
    }

    # None means the call succeeds.
    CENSUS = {
        ("seconds", "uniform"): {
            "seconds_float": None, "whole_number": None, "array_0d": None,
            "decimal": None, "bool": None,
            "nan": ValidationError, "inf": ValidationError,
            "negative_inf": ValidationError, "str": ValidationError,
            "bytes": ValidationError, "none": ValidationError,
            "array": ValidationError, "int_beyond_float": ValidationError,
            "zero": ValidationError, "negative": ValidationError,
        },
        ("index", "uniform"): {
            "whole_number": None, "bool": None,
            "seconds_float": ValidationError, "nan": ValidationError,
            "inf": ValidationError, "negative_inf": ValidationError,
            "str": ValidationError, "bytes": ValidationError,
            "none": ValidationError, "array": ValidationError,
            "array_0d": ValidationError, "int_beyond_float": ValidationError,
            "decimal": ValidationError, "zero": ValidationError,
            "negative": ValidationError,
        },
        # A degenerate time base is refused before the lag is judged at all,
        # in both units - so both rows are uniform, and deliberately so.
        ("seconds", "degenerate"): dict.fromkeys(LAG_SHAPES, ValueError),
        ("index", "degenerate"): dict.fromkeys(LAG_SHAPES, ValueError),
    }

    @pytest.mark.parametrize("unit,base", list(CENSUS))
    @pytest.mark.parametrize("shape", list(LAG_SHAPES))
    def test_the_census_row_holds(self, unit, base, shape):
        ts = _uniform() if base == "uniform" else _degenerate()
        lag = self.LAG_SHAPES[shape]
        expected = self.CENSUS[(unit, base)][shape]

        if expected is None:
            assert shift_timeseries(ts, lag, unit)["lag_idx"] is not None
        else:
            with pytest.raises(expected):
                shift_timeseries(ts, lag, unit)

    @pytest.mark.parametrize("row", list(CENSUS))
    def test_every_lag_shape_is_classified(self, row):
        assert set(self.CENSUS[row]) == set(self.LAG_SHAPES)

    def test_a_degenerate_time_base_always_names_the_rate(self):
        """The whole of #32 in one assertion: no lag, and no choice of unit,
        gets a degenerate series past the rate check."""
        degenerate_rows = [
            outcome
            for (unit, base), row in self.CENSUS.items() if base == "degenerate"
            for outcome in row.values()
        ]

        assert degenerate_rows == [ValueError] * 30

    def test_the_two_calls_that_stop_succeeding_are_the_ones_documented(self):
        """Index mode on a degenerate base with a usable integer lag. Both
        returned `lag_secs=nan` before; nothing else regresses from a success.
        """
        newly_refused = [
            (unit, shape)
            for (unit, base), row in self.CENSUS.items() if base == "degenerate"
            for shape, outcome in row.items()
            if unit == "index" and shape in ("whole_number", "bool")
        ]

        assert sorted(newly_refused) == [("index", "bool"),
                                         ("index", "whole_number")]
        for _, shape in newly_refused:
            with pytest.raises(ValueError, match="degenerate"):
                shift_timeseries(_degenerate(), self.LAG_SHAPES[shape], "index")


class TestTheGuardsAreInertOnValidInput:
    """Pinned so a future guard cannot quietly change what a good call returns.

    The numbers come from a declared 100 Hz rate: a derived one is
    99.99999999999999, and `int()` truncates that 0.5 s lag to 49 rather than
    50 - a reminder that these two modes are not exact inverses.
    """

    def test_seconds_mode_converts_as_before(self):
        res = shift_timeseries(_uniform(), 0.5, "seconds")

        assert res["lag_idx"] == 50
        assert res["lag_secs"] == 0.5
        assert res["lagged_data"].shape == (250,)

    def test_index_mode_converts_as_before(self):
        res = shift_timeseries(_uniform(), 50, "index")

        assert res["lag_idx"] == 50
        assert res["lag_secs"] == pytest.approx(0.5)
        assert res["lagged_data"].shape == (250,)

    def test_the_primitives_round_trip_on_a_clean_rate(self):
        assert time_to_idx(0.5, 100.0) == 50
        assert idx_to_time(50, 100.0) == pytest.approx(0.5)

    def test_a_derived_rate_still_truncates_rather_than_rounds(self):
        """99.99999999999999 Hz gives 49, not 50. Guarding the rate must not
        be mistaken for normalising it."""
        derived = baseTs(_signal(), np.arange(300) / 100.0)

        assert shift_timeseries(derived, 0.5, "seconds")["lag_idx"] == 49

    def test_an_exact_non_float_rate_is_still_accepted(self):
        """`validate_sampling_freq` takes Decimal and Fraction deliberately;
        adding it here must not narrow that."""
        from decimal import Decimal
        from fractions import Fraction

        assert time_to_idx(0.5, Decimal("100")) == 50
        assert idx_to_time(50, Fraction(100, 1)) == pytest.approx(0.5)

    def test_the_validated_lag_is_the_one_that_multiplies(self):
        """#30's escape, one module over: validating a coerced value and then
        computing with the caller's original object.

        `Decimal("0.5") * 100.0` raises TypeError, so a conversion that keeps
        the original would reject a lag its own validator just accepted.
        """
        from decimal import Decimal

        assert time_to_idx(Decimal("0.5"), 100.0) == 50

    def test_an_exact_lag_converts_through_its_float_not_exactly(self):
        """Documented, not overlooked: coercion happens before the multiply.

        Exact arithmetic on this Decimal gives 49.99...9, which floors to 49.
        `float()` rounds it to 0.5 first, so the answer is 50. Accepting exact
        types means accepting their nearest double - the same trade
        `validate_sampling_freq` already makes for an exact *rate*. It only
        shows within one ULP of an integer boundary, and the nearest float lag
        below the boundary still gives 49.
        """
        boundary = Decimal("0.499999999999999999999999999999")

        assert float(boundary) == 0.5
        assert time_to_idx(boundary, 100.0) == 50
        assert time_to_idx(0.4999999999999999, 100.0) == 49

    def test_a_lag_whose_multiplication_lies_cannot_change_the_index(self):
        """float() declared 0.5 s, so 0.5 s is what must be converted."""
        class _LiesAboutMultiplication:
            def __float__(self):
                return 0.5

            def __mul__(self, other):
                return 999.0

            __rmul__ = __mul__

        assert time_to_idx(_LiesAboutMultiplication(), 100.0) == 50

    def test_a_valid_lag_plot_still_draws(self):
        try:
            ax = lag_plot(_uniform(), 0.5, "seconds")
            assert ax.collections
        finally:
            plt.close("all")
