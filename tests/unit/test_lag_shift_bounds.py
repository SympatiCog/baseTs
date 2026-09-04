"""The lag that is applied is the lag that is reported (#51-#54).

Four defects in the same call chain - `get_lags` -> `validate_lag` ->
`shift_timeseries` -> `plotting.lag_plot` - all of which #32 left in place
and filed rather than folded in. Each one let the returned dict, and so the
plot title, describe a shift the function had not performed:

- **#51** `time_to_idx` truncated, so a *derived* rate of 99.99999999999999 Hz
  shifted 49 samples for a requested 0.5 s, and `get_lags` echoed the
  caller's 0.5 back as `lag_secs`. Now the conversion rounds to the nearest
  sample, and `lag_secs` is derived *from* `lag_idx`, so the two halves of
  the result agree by construction.
- **#52** the wrapped head was blanked with `np.nan`, which an integer array
  cannot hold. Now the head is blanked with the dtype's own missing value
  where it has one, and widened to float where it has none - and with
  `drop_nan=True` no sentinel is needed at all, so the dtype survives.
- **#53** nothing bounded the lag by the series length, so a lag of 100
  samples on a 5-sample series returned an empty array labelled `100.0
  seconds`. Now it is refused with both numbers in the message.
- **#54** `lag_unit` was compared against the literal `'seconds'` and
  anything else - `'second'`, `'Seconds'` - fell through to index mode, a
  factor-of-the-rate change in meaning. Now only the two documented units
  are accepted.
"""
import matplotlib
matplotlib.use("Agg")

from decimal import Decimal  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from baseTs import baseTs  # noqa: E402
from baseTs.plotting import lag_plot  # noqa: E402
from baseTs.utils import (  # noqa: E402
    ValidationError,
    get_lags,
    idx_to_time,
    shift_timeseries,
    time_to_idx,
    validate_lag,
)


def _signal(n=300):
    return np.sin(np.arange(n) / 10.0)


def _derived(n=300):
    """A nominal 100 Hz series with the rate *derived*, which is the default.

    The derived rate is 99.99999999999999, not 100.0 - this is #51's
    reproduction, and the case a caller who never declares a rate is in.
    """
    return baseTs(_signal(n), np.arange(n) / 100.0)


def _declared(n=300):
    return baseTs(_signal(n), np.arange(n) / 100.0, freq=100.0)


def _five():
    return baseTs(np.array([1.0, 2, 3, 4, 5]), np.array([0.0, 1, 2, 3, 4]))


def _five_int():
    return baseTs(np.array([1, 2, 3, 4, 5], dtype=np.int64),
                  np.array([0, 1, 2, 3, 4], dtype=np.int64))


def _closed(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    finally:
        plt.close("all")


# ---------------------------------------------------------------------------
# #51 - the conversion rounds, and the result reports the lag it applied
# ---------------------------------------------------------------------------


class TestADerivedRateShiftsByTheSampleAsked:
    """`int(0.5 * 99.99999999999999)` is 49. The caller asked for 50."""

    def test_the_reproduction_from_the_issue(self):
        ts = _derived()

        assert repr(ts.freq) == "99.99999999999999"
        assert shift_timeseries(ts, 0.5, "seconds")["lag_idx"] == 50

    def test_the_primitive_rounds_to_the_nearest_sample(self):
        assert time_to_idx(0.5, 99.99999999999999) == 50
        assert time_to_idx(0.4999999999999999, 100.0) == 50
        assert time_to_idx(0.494, 100.0) == 49
        assert time_to_idx(0.506, 100.0) == 51

    def test_the_issues_sweep_no_longer_comes_up_short(self):
        """Every length from 100 to 2000 at a nominal 100 Hz, three lags.

        The issue measured 7% of these one sample short under truncation.
        Under rounding the residue is ~1e-14 relative, far inside half a
        sample, so every case lands on the sample the caller meant.
        """
        short = [
            (n, lag)
            for n in range(100, 2001)
            for lag in (0.5, 1.0, 2.0)
            if time_to_idx(lag, _derived(n).freq) != int(lag * 100)
        ]

        assert short == []

    def test_an_exact_half_sample_rounds_to_even(self):
        """The tie rule is Python's, stated so it is not mistaken for drift.

        A lag that lands exactly between two samples has no nearest sample;
        either neighbour is as honest as the other, and `lag_secs` reports
        whichever was taken. Round-half-to-even is deterministic and does
        not carry the `floor(x + 0.5)` hazard, where 0.49999999999999994 +
        0.5 is 1.0 in floating point.
        """
        assert time_to_idx(2.5, 1.0) == 2
        assert time_to_idx(3.5, 1.0) == 4

    def test_the_returned_index_is_a_plain_int(self):
        """`round()` on a float returns int; `validate_lag` insists on it."""
        assert type(time_to_idx(0.5, 100.0)) is int
        assert type(time_to_idx(1e300, 100.0)) is int

    def test_a_lag_under_half_a_sample_is_still_zero_and_still_refused(self):
        """Rounding must not start inventing a one-sample shift for a lag
        that is nearer to no shift at all."""
        assert time_to_idx(0.004, 100.0) == 0
        with pytest.raises(ValidationError, match="positive nonzero integer"):
            shift_timeseries(_declared(), 0.004, "seconds")


class TestTheResultReportsTheLagItApplied:
    """`lag_secs` was the caller's argument echoed back. Now it is derived
    from `lag_idx`, so it cannot disagree with the shift performed."""

    def test_seconds_mode_reports_the_seconds_of_the_index_it_applied(self):
        ts = _derived()
        res = shift_timeseries(ts, 0.5, "seconds")

        assert res["lag_idx"] == 50
        assert res["lag_secs"] == 50 / ts.freq
        assert res["lag_secs"] == pytest.approx(0.5)
        assert res["lag_secs"] != 0.5           # 0.5000000000000001: the truth

    def test_an_unrepresentable_lag_reports_what_was_taken_not_what_was_asked(self):
        """0.3 s at 7 Hz is 2.1 samples. Rounding alone would make the two
        values agree in the common case but not this one: it applies 2 samples
        and, without the second half of the fix, would still say 0.3 s."""
        secs, idx = get_lags(0.3, "seconds", 7.0)

        assert idx == 2
        assert secs == pytest.approx(2 / 7)
        assert secs != 0.3

    def test_the_two_halves_agree_by_construction_in_seconds_mode(self):
        for lag in (0.013, 0.5, 0.997, 1.0, 2.49):
            secs, idx = get_lags(lag, "seconds", 99.99999999999999)
            assert secs == idx_to_time(idx, 99.99999999999999)

    def test_index_mode_is_unchanged(self):
        secs, idx = get_lags(50, "index", 100.0)

        assert idx == 50
        assert secs == pytest.approx(0.5)

    def test_a_declared_exact_rate_reports_exactly_what_was_asked(self):
        """Nothing changes for the caller who was already getting the right
        answer: 50 / 100.0 is exactly 0.5."""
        res = shift_timeseries(_declared(), 0.5, "seconds")

        assert res["lag_idx"] == 50
        assert res["lag_secs"] == 0.5

    def test_seconds_mode_reports_a_float_whatever_the_caller_passed(self):
        """A Decimal or a bool used to be echoed back as itself."""
        assert type(get_lags(Decimal("0.5"), "seconds", 100.0)[0]) is float
        assert type(get_lags(True, "seconds", 100.0)[0]) is float

    def test_the_plot_title_names_the_lag_that_was_drawn(self):
        """`Lag Plot at 0.5 seconds (49items)` was the issue's example."""
        ax = _closed(lag_plot, _derived(), 0.5, "seconds")

        assert "(50items)" in ax.get_title()
        assert "49" not in ax.get_title()


# ---------------------------------------------------------------------------
# #52 - the wrapped head is blanked in the dtype's own terms
# ---------------------------------------------------------------------------


class TestAnIntegerSeriesCanBeShifted:
    """`lagged_data[:lag_idx] = np.nan` on int64 raised the very message
    #32 is named for, from a different line."""

    def test_the_reproduction_from_the_issue(self):
        res = shift_timeseries(_five_int(), 2, "index")

        np.testing.assert_array_equal(res["lagged_data"], [1, 2, 3])
        np.testing.assert_array_equal(res["lagged_timeseries"], [0, 1, 2])

    def test_dropping_the_head_needs_no_sentinel_so_the_dtype_survives(self):
        """With `drop_nan=True` the blanked samples are sliced off anyway;
        widening to float to hold a NaN nobody will see would change the
        caller's dtype for nothing."""
        res = shift_timeseries(_five_int(), 2, "index")

        assert res["lagged_data"].dtype == np.int64
        assert res["lagged_timeseries"].dtype == np.int64

    def test_keeping_the_head_widens_an_integer_array_to_float(self):
        """The caller asked for NaN placeholders, and NaN is a float. This
        is what `pd.Series([1, 2, 3]).shift(1)` does too."""
        res = shift_timeseries(_five_int(), 2, "index", drop_nan=False)

        assert res["lagged_data"].dtype == np.float64
        assert res["lagged_timeseries"].dtype == np.float64
        np.testing.assert_array_equal(res["lagged_data"], [np.nan, np.nan, 1, 2, 3])
        np.testing.assert_array_equal(res["lagged_timeseries"], [np.nan, np.nan, 0, 1, 2])

    def test_an_integer_series_can_be_lag_plotted(self):
        """`lag_plot` calls with `drop_nan=False`, so it took the raising
        path unconditionally."""
        ax = _closed(lag_plot, _five_int(), 2, "index")

        assert ax.collections
        assert len(ax.collections[0].get_offsets()) == 3

    def test_a_float_series_returns_exactly_what_it_did_before(self):
        """The old code, inlined, so the refactor is pinned against it."""
        ts = _five()
        k = 2
        expected_data = np.roll(ts.data, k)
        expected_data[:k] = np.nan
        expected_times = np.roll(ts.times, k)
        expected_times[:k] = np.nan

        kept = shift_timeseries(ts, k, "index", drop_nan=False)
        np.testing.assert_array_equal(kept["lagged_data"], expected_data)
        np.testing.assert_array_equal(kept["lagged_timeseries"], expected_times)
        assert kept["lagged_data"].dtype == np.float64

        dropped = shift_timeseries(ts, k, "index")
        np.testing.assert_array_equal(dropped["lagged_data"], expected_data[k:])
        np.testing.assert_array_equal(dropped["lagged_timeseries"], expected_times[k:])

    def test_the_result_does_not_alias_the_series(self):
        """`np.roll` always copied. Slicing instead would hand back a view of
        `ts.data`, so a caller who edits the result would edit the series."""
        ts = _five()
        res = shift_timeseries(ts, 2, "index")
        res["lagged_data"][0] = 999.0
        res["lagged_timeseries"][0] = 999.0

        assert ts.data[0] == 1.0
        assert ts.times[0] == 0.0


class TestATimestampArrayIsBlankedWithNaT:
    """A datetime index derives no rate, so these need a declared one to
    reach the shift at all - and then died on `Could not convert object to
    NumPy datetime`. `astype(float)` is not the remedy here: it reinterprets
    the int64 storage, which the issue warns about explicitly."""

    def _stamped(self):
        return baseTs(np.arange(5.0),
                      pd.date_range("2024", periods=5, freq="10ms"),
                      freq=100.0)

    def test_the_head_becomes_nat_and_the_dtype_survives(self):
        res = shift_timeseries(self._stamped(), 2, "index", drop_nan=False)
        times = res["lagged_timeseries"]

        assert times.dtype.kind == "M"
        assert np.isnat(times[:2]).all()
        assert not np.isnat(times[2:]).any()
        np.testing.assert_array_equal(times[2:], self._stamped().times[:3])

    def test_dropping_the_head_keeps_the_timestamps(self):
        res = shift_timeseries(self._stamped(), 2, "index")

        assert res["lagged_timeseries"].dtype.kind == "M"
        np.testing.assert_array_equal(res["lagged_timeseries"],
                                      self._stamped().times[:3])

    def test_a_timedelta_index_is_blanked_the_same_way(self):
        ts = baseTs(np.arange(5.0),
                    pd.timedelta_range(0, periods=5, freq="10ms"),
                    freq=100.0)
        res = shift_timeseries(ts, 2, "index", drop_nan=False)
        times = res["lagged_timeseries"]

        assert times.dtype.kind == "m"
        assert np.isnat(times[:2]).all()
        np.testing.assert_array_equal(times[2:], ts.times[:3])

    def test_a_stamped_series_can_be_lag_plotted(self):
        ax = _closed(lag_plot, self._stamped(), 2, "index")

        assert ax.collections


class TestTheBlankingRuleIsStatedNotListed:
    """The dtype's own missing value where it has one; float64 where it has
    none. Object arrays hold NaN; bool has no missing value and widens."""

    def test_an_object_array_holds_nan_without_widening(self):
        ts = baseTs(np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=object),
                    np.array([0.0, 1, 2, 3, 4]))
        res = shift_timeseries(ts, 2, "index", drop_nan=False)

        assert res["lagged_data"].dtype == object
        assert all(x != x for x in res["lagged_data"][:2])       # NaN is not NaN
        assert list(res["lagged_data"][2:]) == [1.0, 2.0, 3.0]

    def test_a_bool_array_widens_to_float(self):
        ts = baseTs(np.array([True, False, True, True, False]),
                    np.array([0.0, 1, 2, 3, 4]))
        res = shift_timeseries(ts, 2, "index", drop_nan=False)

        assert res["lagged_data"].dtype == np.float64
        np.testing.assert_array_equal(res["lagged_data"], [np.nan, np.nan, 1, 0, 1])

    def test_an_unsigned_array_widens_to_float(self):
        ts = baseTs(np.array([1, 2, 3, 4, 5], dtype=np.uint8),
                    np.array([0.0, 1, 2, 3, 4]))
        res = shift_timeseries(ts, 2, "index", drop_nan=False)

        assert res["lagged_data"].dtype == np.float64
        np.testing.assert_array_equal(res["lagged_data"], [np.nan, np.nan, 1, 2, 3])

    def test_a_complex_array_holds_nan_without_widening(self):
        ts = baseTs(np.array([1 + 1j, 2, 3, 4, 5]), np.array([0.0, 1, 2, 3, 4]))
        res = shift_timeseries(ts, 2, "index", drop_nan=False)

        assert res["lagged_data"].dtype == np.complex128
        assert np.isnan(res["lagged_data"][:2]).all()
        np.testing.assert_array_equal(res["lagged_data"][2:], [1 + 1j, 2, 3])


# ---------------------------------------------------------------------------
# #53 - a lag longer than the series is refused, not returned empty
# ---------------------------------------------------------------------------


class TestALagLongerThanTheSeriesIsRefused:
    """`np.roll` wraps modulo the length and the blanking then covered the
    whole array: an empty result with `lag_secs=100.0` on a 4-second series."""

    def test_the_reproduction_from_the_issue(self):
        with pytest.raises(ValidationError, match="5 samples"):
            shift_timeseries(_five(), 100, "index")

    def test_the_kept_head_form_is_refused_too(self):
        """This was five NaNs and no error."""
        with pytest.raises(ValidationError, match="5 samples"):
            shift_timeseries(_five(), 100, "index", drop_nan=False)

    def test_the_message_names_both_numbers(self):
        with pytest.raises(ValidationError) as excinfo:
            shift_timeseries(_five(), 100, "index")

        assert "lag=100" in str(excinfo.value)
        assert "5 samples" in str(excinfo.value)

    def test_seconds_mode_names_the_seconds_the_samples_and_the_length(self):
        """The caller thinks in seconds; the bound is in samples. Both, and
        the rate that connects them, so the arithmetic can be checked."""
        with pytest.raises(ValidationError) as excinfo:
            shift_timeseries(_five(), 100.0, "seconds")

        message = str(excinfo.value)
        assert "lag=100.0s" in message
        assert "lag_idx=100" in message
        assert "5 samples" in message

    def test_a_lag_equal_to_the_length_is_the_boundary(self):
        """`lag_idx == len` blanks every sample; `len - 1` leaves one. The
        one-sample result is degenerate but honest - it is a real shift, and
        the caller can see its length - so it is not refused."""
        with pytest.raises(ValidationError, match="5 samples"):
            shift_timeseries(_five(), 5, "index")

        res = shift_timeseries(_five(), 4, "index")
        np.testing.assert_array_equal(res["lagged_data"], [1.0])
        assert res["lag_idx"] == 4

    def test_lag_plot_refuses_rather_than_drawing_nothing(self):
        with pytest.raises(ValidationError, match="5 samples"):
            _closed(lag_plot, _five(), 100, "index")

    def test_the_core_method_inherits_the_bound(self):
        with pytest.raises(ValidationError, match="5 samples"):
            _closed(_five().lag_plot, 100)

    def test_a_seconds_lag_that_rounds_up_to_the_length_is_refused(self):
        """The bound is applied to the *rounded* index, which is the one
        that will be used: 4.6 s at 1 Hz rounds to 5 samples."""
        with pytest.raises(ValidationError, match="5 samples"):
            shift_timeseries(_five(), 4.6, "seconds")

        assert shift_timeseries(_five(), 4.4, "seconds")["lag_idx"] == 4

    def test_validate_lag_takes_the_length_as_a_keyword(self):
        """The bound lives with the other lag rules. Without the keyword the
        validator is unchanged, so existing callers keep their behaviour."""
        validate_lag(100, 100, "index", 1.0)                     # no length: no bound
        validate_lag(4, 4, "index", 1.0, n_samples=5)

        with pytest.raises(ValidationError, match="5 samples"):
            validate_lag(5, 5, "index", 1.0, n_samples=5)
        with pytest.raises(ValidationError, match="5 samples"):
            validate_lag(5.0, 5, "seconds", 1.0, n_samples=5)

    def test_the_positive_integer_rule_is_still_judged_first(self):
        """A zero lag on a five-sample series is a zero lag, not a bound."""
        with pytest.raises(ValidationError, match="positive nonzero integer"):
            validate_lag(0, 0, "index", 1.0, n_samples=5)


# ---------------------------------------------------------------------------
# #54 - only the two documented units are accepted
# ---------------------------------------------------------------------------


class TestAnUnknownUnitIsRefused:
    """`get_lags(5, 'second', 100.0)` returned `(0.05, 5)`: five samples,
    where the caller asked for five seconds."""

    @pytest.mark.parametrize("unit", ["second", "Seconds", "sec", "SECONDS",
                                      "Index", "samples", "", b"seconds",
                                      None, 1])
    def test_get_lags_refuses_it(self, unit):
        with pytest.raises(ValidationError, match="'seconds' or 'index'"):
            get_lags(5, unit, 100.0)

    def test_the_message_names_what_was_passed(self):
        with pytest.raises(ValidationError, match="'second'"):
            get_lags(5, "second", 100.0)

    def test_the_two_documented_units_still_work(self):
        assert get_lags(5, "seconds", 100.0) == (5.0, 500)
        assert get_lags(5, "index", 100.0) == (pytest.approx(0.05), 5)

    def test_shift_timeseries_refuses_it(self):
        with pytest.raises(ValidationError, match="'seconds' or 'index'"):
            shift_timeseries(_declared(), 5, "second")

    def test_lag_plot_refuses_it(self):
        with pytest.raises(ValidationError, match="'seconds' or 'index'"):
            _closed(lag_plot, _declared(), 5, "Seconds")

    def test_validate_lag_shares_the_rule(self):
        """Its else-branch produced the index-mode message for any unknown
        unit - the same assumption, one function over. One rule, one place."""
        with pytest.raises(ValidationError, match="'seconds' or 'index'"):
            validate_lag(5, 5, "second", 100.0)

    def test_the_unit_is_judged_before_the_rate_or_the_lag(self):
        """Without a unit there is no way to know which conversion the lag
        was meant for, so nothing about the lag or the rate can be diagnosed
        in the caller's terms yet."""
        degenerate = baseTs(_signal(), np.zeros(300))

        with pytest.raises(ValidationError, match="'seconds' or 'index'"):
            shift_timeseries(degenerate, "0.5", "second")
