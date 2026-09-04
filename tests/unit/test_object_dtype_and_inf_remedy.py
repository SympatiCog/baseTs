"""Object-dtype data reaching numeric code, and the Inf half of the NaN remedy.

Three issues of one shape. An object array of ordinary floats passed the
shared data guard - which cast a copy to float to check finiteness and then
threw the cast away - and reached scipy (#75: bare `NotImplementedError`
from every Butterworth filter) or pandas (#80: bare `TypeError` from
`interpolate_gaps()`, the remedy the guard itself names). And the guard's
"NaN or Inf" message named `interpolate_gaps()` for both halves of its own
disjunction when pandas fills NaN only, so an Inf caller followed the remedy
and landed on the same message (#81).

The cast now lives in one place, `utils.coerce_numeric_data`, which the guard
calls and whose result it returns; the filters and `interpolate_gaps` compute
with that result. The message is split by what was found.
"""

import decimal
import numbers
import re

import numpy as np
import pandas as pd
import pytest

from baseTs import baseTs
from baseTs.filters import (InvalidParameterError, bandpass_filter, highpass_filter,
                            lowpass_filter, notch_filter)

FS = 30.0
N = 600


def _sine():
    return np.sin(2 * np.pi * 0.5 * np.arange(N) / FS)


def _as_object(values):
    return np.array(list(values), dtype=object)


FILTERS = [
    ("lowpass_filter", lambda d: lowpass_filter(d, 5.0, FS)),
    ("highpass_filter", lambda d: highpass_filter(d, 0.1, FS)),
    ("notch_filter", lambda d: notch_filter(d, 5.0, FS)),
    ("bandpass_filter", lambda d: bandpass_filter(d, hp_hz=0.1, lp_hz=5.0, sample_Hz=FS)),
]
FILTER_IDS = [f[0] for f in FILTERS]

METHODS = [
    ("lowpass_at", lambda ts: ts.lowpass_at(5.0)),
    ("highpass_at", lambda ts: ts.highpass_at(0.1)),
    ("notch_at", lambda ts: ts.notch_at(5.0)),
    ("bandpass_at", lambda ts: ts.bandpass_at(0.1, 5.0)),
]
METHOD_IDS = [m[0] for m in METHODS]


# --- the shared coercer ------------------------------------------------------

class TestCoerceNumericData:
    """One function owns the dtype rules the guard used to mix into its scan."""

    def test_an_object_array_of_reals_becomes_float64(self):
        from baseTs.utils import coerce_numeric_data

        out = coerce_numeric_data(_as_object([1.0, 2, np.float32(3.5), True]))

        assert out.dtype == np.float64
        np.testing.assert_array_equal(out, [1.0, 2.0, 3.5, 1.0])

    def test_pandas_missing_markers_count_as_gaps(self):
        """`None` and `pd.NA` are how pandas spells a hole in an object
        column, so they become NaN rather than making the column "not
        numeric". The guard then names the gap remedy, which - now that
        interpolate_gaps() coerces the same way - actually runs."""
        from baseTs.utils import coerce_numeric_data

        out = coerce_numeric_data(_as_object([1.0, None, 3.0, pd.NA]))

        assert out.dtype == np.float64
        np.testing.assert_array_equal(np.isnan(out), [False, True, False, True])

    def test_nan_passes_through_the_coercer(self):
        """The coercer settles the dtype only; finiteness is the guard's job,
        and interpolate_gaps() needs the NaN to reach it."""
        from baseTs.utils import coerce_numeric_data

        out = coerce_numeric_data(_as_object([1.0, np.nan]))
        assert np.isnan(out[1])

    def test_complex_in_object_is_complex128_when_allowed_and_refused_otherwise(self):
        from baseTs.utils import coerce_numeric_data

        obj = _as_object([1 + 2j, 3.0])
        out = coerce_numeric_data(obj, allow_complex=True)
        assert out.dtype == np.complex128
        np.testing.assert_array_equal(out, [1 + 2j, 3 + 0j])

        with pytest.raises(ValueError, match="holding complex values"):
            coerce_numeric_data(obj)

    @pytest.mark.parametrize("bad", [
        _as_object(["1.5", "2"]),          # parses as float; accepted by the old try-cast
        _as_object([decimal.Decimal("1")]),  # a Number, not a numbers.Real
        _as_object([{}, {}]),
        _as_object([1.0, "x"]),
        np.array(["1.5", "2"]),              # fixed-width text
    ], ids=["numeric-text", "Decimal", "dicts", "mixed", "str-dtype"])
    def test_anything_else_is_not_numeric(self, bad):
        """Classified by what the elements *are*, not by whether a float()
        parse would succeed: the old try-cast accepted a column of numeric
        strings and every consumer then died on it (#43's lesson, applied to
        the real branch). Nothing that succeeded before is refused now - no
        object array reached a result through any guarded path."""
        from baseTs.utils import coerce_numeric_data

        with pytest.raises(ValueError, match="not numeric"):
            coerce_numeric_data(bad, allow_complex=True)

    def test_a_registered_impostor_is_not_numeric_not_a_crash(self):
        """numbers.Real is a registrable ABC; membership does not imply a
        working __float__ (#48's lesson for the complex branch)."""
        from baseTs.utils import coerce_numeric_data

        @numbers.Real.register
        class _Impostor:
            pass

        with pytest.raises(ValueError, match="not numeric"):
            coerce_numeric_data(_as_object([_Impostor(), _Impostor()]))

    @pytest.mark.parametrize("arr", [
        np.arange(4), np.array([True, False]), np.array([1.0, np.nan]),
        np.array([1 + 1j]),
    ])
    def test_numeric_dtypes_pass_through_untouched(self, arr):
        from baseTs.utils import coerce_numeric_data

        out = coerce_numeric_data(arr, allow_complex=True)
        assert out.dtype == arr.dtype
        assert out is arr

    def test_the_datetime_rule_is_the_same_one_the_guard_had(self):
        from baseTs.utils import coerce_numeric_data

        with pytest.raises(ValueError, match="holds datetimes or durations"):
            coerce_numeric_data(np.array(["2020-01-01"], dtype="datetime64[s]"))

    def test_shape_survives(self):
        from baseTs.utils import coerce_numeric_data

        out = coerce_numeric_data(np.array([[1.0, 2.0], [3.0, None]], dtype=object))
        assert out.shape == (2, 2)
        assert np.isnan(out[1, 1])


def test_the_guard_returns_the_array_it_checked():
    """The cast the guard threw away is the one every consumer needs (#75)."""
    from baseTs.utils import validate_finite_data

    obj = _as_object([1.0, 2.0])
    out = validate_finite_data(obj)

    assert isinstance(out, np.ndarray)
    assert out.dtype == np.float64
    floats = np.array([1.0, 2.0])
    assert validate_finite_data(floats) is floats


# --- #75: the filters compute with the coerced array -------------------------

class TestFiltersAcceptObjectDtype:

    @pytest.mark.parametrize("name, run", FILTERS, ids=FILTER_IDS)
    def test_an_object_array_of_floats_filters_like_the_float_array(self, name, run):
        expected = run(_sine())
        out = run(_as_object(_sine()))

        assert out.dtype == np.float64
        np.testing.assert_array_equal(out, expected)

    @pytest.mark.parametrize("name, run", FILTERS, ids=FILTER_IDS)
    def test_complex_hiding_in_object_filters_as_complex(self, name, run):
        z = np.exp(2j * np.pi * 0.5 * np.arange(N) / FS)

        out = run(_as_object(z))

        assert out.dtype == np.complex128
        np.testing.assert_array_equal(out, run(z))

    @pytest.mark.parametrize("name, run", FILTERS, ids=FILTER_IDS)
    def test_non_numeric_object_data_is_an_invalid_parameter(self, name, run):
        with pytest.raises(InvalidParameterError, match="not numeric"):
            run(_as_object(["1.5"] * N))

    def test_a_bad_call_is_still_reported_before_bad_data(self):
        """#48's precedence: the O(n) look at the data does not get to speak
        before a cutoff the caller mistyped. The coercion therefore runs
        after validation, on an array the guard has already proved coercible."""
        with pytest.raises(InvalidParameterError, match="Cutoff"):
            lowpass_filter(_as_object(["1.5"] * N), -1.0, FS)

    @pytest.mark.parametrize("name, run", METHODS, ids=METHOD_IDS)
    def test_the_basets_methods_reach_the_same_fix(self, name, run):
        t = np.arange(N) / FS
        expected = run(baseTs(_sine(), t, freq=FS))
        out = run(baseTs(_as_object(_sine()), t, freq=FS))

        assert out.dtype == np.float64
        np.testing.assert_array_equal(out.values, expected.values)


# --- #80: interpolate_gaps() coerces the same way ----------------------------

class TestInterpolateGapsOnObjectDtype:

    @staticmethod
    def _gappy(n_bad=slice(100, 104), marker=np.nan):
        d = _as_object(_sine())
        d[n_bad] = marker
        return baseTs(d, np.arange(N) / FS, freq=FS)

    def test_an_object_series_of_floats_is_filled_as_float64(self):
        ts = self._gappy()
        assert ts.dtype == object                      # the constructor keeps it

        out = ts.interpolate_gaps()

        assert out.dtype == np.float64
        assert not np.isnan(out.values).any()
        floats = _sine()
        floats[100:104] = np.nan
        reference = baseTs(floats, np.arange(N) / FS, freq=FS)
        np.testing.assert_array_equal(out.values, reference.interpolate_gaps().values)

    def test_none_is_a_gap_here_too(self):
        out = self._gappy(marker=None).interpolate_gaps()
        assert out.dtype == np.float64
        assert not np.isnan(out.values).any()

    def test_the_time_method_branch_is_covered(self):
        out = self._gappy().interpolate_gaps(method='time')
        assert out.dtype == np.float64
        assert not np.isnan(out.values).any()

    def test_inplace_too(self):
        ts = self._gappy()
        ret = ts.interpolate_gaps(inplace=True)
        assert ret is ts
        assert ts.dtype == np.float64
        assert not np.isnan(ts.values).any()

    def test_a_non_numeric_object_series_raises_the_guards_message(self):
        ts = baseTs(_as_object(["a"] * 6), np.arange(6) / 10.0)
        with pytest.raises(ValueError, match="not numeric"):
            ts.interpolate_gaps()

    def test_the_remedy_the_guard_names_runs_end_to_end(self):
        """The issue's chain: guard rejects, names interpolate_gaps(), and
        following it now reaches a filtered series instead of pandas' bare
        TypeError."""
        ts = self._gappy()
        with pytest.raises(InvalidParameterError, match="interpolate_gaps"):
            ts.lowpass_at(5.0)

        out = ts.interpolate_gaps().lowpass_at(5.0)
        assert out.dtype == np.float64
        assert np.isfinite(out.values).all()


# --- #81: the message is split by what was found -----------------------------

NAN_MESSAGE = ("Time series data contains NaN or Inf values. Fill gaps first, "
               "e.g. with interpolate_gaps().")
REPLACE_STEP = "replace([np.inf, -np.inf], np.nan)"


class TestTheInfHalfOfTheRemedy:

    def test_a_nan_only_message_is_unchanged(self):
        from baseTs.utils import validate_finite_data

        with pytest.raises(ValueError) as exc:
            validate_finite_data(np.array([1.0, np.nan, 3.0]))
        assert str(exc.value) == NAN_MESSAGE

    def test_an_inf_is_told_it_is_not_a_gap_and_given_the_replace_step(self):
        from baseTs.utils import validate_finite_data

        with pytest.raises(ValueError) as exc:
            validate_finite_data(np.array([1.0, np.inf, 3.0]))
        text = str(exc.value)

        assert text.startswith("Time series data contains Inf values.")
        assert "NaN or Inf" not in text
        assert "Inf is not a gap" in text
        assert REPLACE_STEP in text
        assert text.index(REPLACE_STEP) < text.index("interpolate_gaps()")

    def test_both_present_names_both_and_orders_the_two_steps(self):
        from baseTs.utils import validate_finite_data

        with pytest.raises(ValueError) as exc:
            validate_finite_data(np.array([np.nan, 1.0, -np.inf, 3.0][::-1]))
        text = str(exc.value)

        assert text.startswith("Time series data contains NaN and Inf values.")
        assert REPLACE_STEP in text
        assert text.index(REPLACE_STEP) < text.index("interpolate_gaps()")

    def test_a_complex_inf_gets_the_inf_message(self):
        from baseTs.utils import validate_finite_data

        with pytest.raises(ValueError, match="Inf is not a gap"):
            validate_finite_data(np.array([1 + 2j, complex(0, np.inf)]), allow_complex=True)

    def test_a_leading_inf_gets_the_edge_hint_worded_for_after_the_replace(self):
        """#77 keyed the hint on a leading NaN so as not to name a second
        remedy that does not run for Inf. With the replace step in the
        message, the leading gap it will leave is real, and the hint applies
        to it - said as a consequence of the replace, not a present fact."""
        from baseTs.utils import validate_finite_data

        with pytest.raises(ValueError) as exc:
            validate_finite_data(np.array([np.inf, 1.0, 2.0]))
        text = str(exc.value)
        assert "limit_direction='both'" in text
        assert "will then start with a gap" in text
        assert "The series starts with a gap" not in text

        with pytest.raises(ValueError) as nan_led:
            validate_finite_data(np.array([np.nan, 1.0, 2.0]))
        assert "The series starts with a gap" in str(nan_led.value)

        with pytest.raises(ValueError, match="Inf is not a gap") as interior:
            validate_finite_data(np.array([1.0, np.inf, 2.0]))
        assert "limit_direction" not in str(interior.value)

    def test_an_all_non_finite_series_keeps_the_nothing_to_interpolate_message(self):
        from baseTs.utils import validate_finite_data

        for arr in (np.array([np.inf, -np.inf]), np.array([np.nan, np.inf])):
            with pytest.raises(ValueError, match="nothing to interpolate from"):
                validate_finite_data(arr)

    def test_the_filters_carry_the_inf_message(self):
        d = _sine()
        d[300:304] = np.inf
        for name, run in FILTERS:
            with pytest.raises(InvalidParameterError, match="Inf is not a gap"):
                run(d)

    def test_the_issues_chain_runs_when_the_steps_are_followed(self):
        """Executed, not just named: the issue's own example, then the
        leading-Inf variant that needs the hint as well."""
        t = np.arange(N) / FS
        d = _sine()
        d[300:304] = np.inf
        ts = baseTs(d, t, freq=FS)

        with pytest.raises(InvalidParameterError, match=re.escape(REPLACE_STEP)):
            ts.interpolate_gaps().lowpass_at(5.0)         # the old remedy, still a no-op
        out = ts.replace([np.inf, -np.inf], np.nan).interpolate_gaps().lowpass_at(5.0)
        assert np.isfinite(out.values).all()
        assert out.freq == FS

        d[0] = -np.inf
        led = baseTs(d, t, freq=FS)
        with pytest.raises(InvalidParameterError, match="will then start with a gap"):
            led.lowpass_at(5.0)
        out = (led.replace([np.inf, -np.inf], np.nan)
                  .interpolate_gaps(limit_direction='both').lowpass_at(5.0))
        assert np.isfinite(out.values).all()
