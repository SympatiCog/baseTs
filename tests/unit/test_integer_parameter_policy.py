"""
One policy for integer parameters (#78).

#49 gave `order` a strict rule: a non-bool numbers.Integral of at least 1,
coerced to a plain int, otherwise InvalidParameterError. Its siblings did not
follow it. `window_step=4.0` and `2.5` were accepted through the real-number
guard; `sg_filter(window_length=True)` silently returned its input (the
window-length-1 identity) while `window_length=11.0` died with scipy's bare
TypeError; `set_outlier_filter(order=4.7)` stored 4 and `order=True` stored a
bool. Same package, three answers to "what is an integer parameter".

These tests pin the one answer. A parameter that counts something (poles,
samples, iterations, a polynomial degree) is an integer: a numpy integer is
admitted and coerced, a bool is refused by name, an integral-valued float is
refused too - a count is not a measurement - and the floor is stated by the
rule, not by the caller.
"""
import numpy as np
import pytest

from baseTs import baseTs
from baseTs.filters import (
    InvalidParameterError,
    bandpass_filter,
    lowpass_filter,
    sg_filter,
    validate_band_params,
)

FS = 10.0


def _data(n=500):
    return np.sin(np.arange(n) / 10.0)


def _bandpass(**kwargs):
    kwargs = {'hp_hz': 0.1, 'lp_hz': 0.4, 'sample_Hz': FS, **kwargs}
    return bandpass_filter(_data(), **kwargs)


class TestWindowingParametersAreIntegers:
    """`window_step` and `overlap` are annotated int and documented as a step
    and an overlap in samples; they were validated as finite reals."""

    @pytest.mark.parametrize("bad", [4.0, 2.5, True, np.float64(4), "4"],
                             ids=["4.0", "2.5", "True", "np.float64", "'4'"])
    def test_a_non_integer_window_step_is_refused_by_name(self, bad):
        with pytest.raises(InvalidParameterError,
                           match=r"window_step must be a positive integer, got"):
            _bandpass(window_step=bad)

    @pytest.mark.parametrize("bad", [1.0, 0.5, True, np.float64(0), "0"],
                             ids=["1.0", "0.5", "True", "np.float64", "'0'"])
    def test_a_non_integer_overlap_is_refused_by_name(self, bad):
        with pytest.raises(InvalidParameterError,
                           match=r"overlap must be a non-negative integer, got"):
            _bandpass(overlap=bad)

    def test_overlap_may_be_zero_but_not_negative(self):
        """An overlap of zero is the default. A negative one would inflate the
        effective rate above the real one - one of the silent cases #30 named."""
        np.testing.assert_array_equal(_bandpass(overlap=0), _bandpass())
        with pytest.raises(InvalidParameterError,
                           match=r"overlap must be a non-negative integer, got -1"):
            _bandpass(overlap=-1)

    def test_a_zero_window_step_is_refused(self):
        with pytest.raises(InvalidParameterError,
                           match=r"window_step must be a positive integer, got 0"):
            _bandpass(window_step=0)

    def test_a_numpy_integer_is_accepted_and_is_the_same_filter(self):
        expected = _bandpass(window_step=4)
        np.testing.assert_array_equal(_bandpass(window_step=np.int64(4)), expected)
        np.testing.assert_array_equal(
            _bandpass(window_step=np.int64(6), overlap=np.int64(2)), expected)

    def test_the_public_validator_applies_the_same_rule(self):
        """validate_band_params is public and cannot rely on its caller."""
        for bad in (0, -1, 0.5, 4.0, True):
            with pytest.raises(InvalidParameterError,
                               match=r"window_step must be a positive integer"):
                validate_band_params(_data(), FS, 0.1, 0.4, 3, window_step=bad)

    def test_a_window_step_too_large_to_divide_by_stays_in_the_contract(self):
        """10**400 is a positive integer, so the type rule admits it, and
        `sample_Hz / window_step` then raises OverflowError. That was the bare
        error #30 closed; the integer policy must not reopen it."""
        with pytest.raises(InvalidParameterError, match=r"window_step is too large"):
            _bandpass(window_step=10 ** 400)


class TestSavitzkyGolayParametersAreIntegers:
    """sg_filter passed its parameters to scipy after arithmetic that assumed
    them integral: `True` read as 1 and returned the input unchanged, `11.0`
    died inside savgol_filter with a bare TypeError."""

    def test_a_bool_window_length_no_longer_returns_the_input_unchanged(self):
        with pytest.raises(InvalidParameterError,
                           match=r"window_length must be a positive integer, got True"):
            sg_filter(_data(), window_length=True)

    def test_a_float_window_length_is_refused_here_not_in_scipy(self):
        with pytest.raises(InvalidParameterError,
                           match=r"window_length must be a positive integer, got 11.0"):
            sg_filter(_data(), window_length=11.0)

    def test_a_zero_window_length_is_refused(self):
        with pytest.raises(InvalidParameterError,
                           match=r"window_length must be a positive integer, got 0"):
            sg_filter(_data(), window_length=0)

    @pytest.mark.parametrize("bad", [2.0, True, -1, "2"], ids=["2.0", "True", "-1", "'2'"])
    def test_a_non_integer_polyorder_is_refused_by_name(self, bad):
        with pytest.raises(InvalidParameterError,
                           match=r"polyorder must be a non-negative integer, got"):
            sg_filter(_data(), window_length=11, polyorder=bad)

    def test_polyorder_zero_is_a_moving_average_and_is_accepted(self):
        out = sg_filter(_data(), window_length=5, polyorder=0)
        expected = np.convolve(np.pad(_data(), 2, mode='edge'), np.ones(5) / 5, mode='valid')
        # savgol pads by polynomial extrapolation ('interp' mode); the interior
        # is the plain moving average.
        np.testing.assert_allclose(out[2:-2], expected[2:-2])

    def test_numpy_integers_are_accepted_and_give_the_same_output(self):
        expected = sg_filter(_data(), window_length=11, polyorder=2)
        np.testing.assert_array_equal(
            sg_filter(_data(), window_length=np.int64(11), polyorder=np.int32(2)),
            expected)

    def test_the_method_carries_the_same_rule(self):
        ts = baseTs(_data(), np.arange(500) / FS, freq=FS)
        with pytest.raises(InvalidParameterError,
                           match=r"window_length must be a positive integer"):
            ts.sg_filter(window_length=11.0)

    def test_the_length_and_parity_adjustments_still_run_after_the_check(self):
        """A window longer than the data is still shortened, and an even one
        still made odd - the policy is a type check in front, not a rewrite."""
        short = _data(8)
        assert sg_filter(short, window_length=11, polyorder=2).shape == short.shape
        assert sg_filter(_data(), window_length=10, polyorder=2).shape == (500,)


class TestFilterOrderKeepsItsRule:
    """`order` already had the rule; it keeps its wording."""

    def test_the_order_message_is_unchanged(self):
        with pytest.raises(InvalidParameterError,
                           match=r"Filter order must be a positive integer, got True"):
            lowpass_filter(_data(), 0.5, FS, order=True)


class TestSetOutlierFilterIntegerFields:
    """`max_iterations`, `order` and `it` are the filter config's integer
    fields. `_coerce` used to call int() on anything that was not already an
    int - so 4.7 stored 4 and '5' stored 5 - and let a bool through as an int."""

    @pytest.fixture
    def ts(self):
        return baseTs(_data(), np.arange(500) / FS, freq=FS)

    @pytest.mark.parametrize("field", ["max_iterations", "order"])
    @pytest.mark.parametrize("bad", [4.7, 4.0, True, "4", 0, -1],
                             ids=["4.7", "4.0", "True", "'4'", "0", "-1"])
    def test_a_positive_int_field_refuses_what_the_filters_refuse(self, ts, field, bad):
        with pytest.raises(ValueError, match=rf"{field} must be a positive integer, got"):
            ts.set_outlier_filter(**{field: bad})

    @pytest.mark.parametrize("bad", [1.0, True, "1", -1],
                             ids=["1.0", "True", "'1'", "-1"])
    def test_it_refuses_non_integers_and_negatives(self, ts, bad):
        with pytest.raises(ValueError, match=r"it must be a non-negative integer, got"):
            ts.set_outlier_filter(it=bad)

    def test_it_may_be_zero(self, ts):
        ts.set_outlier_filter(it=0)
        assert ts.get_outlier_filter_params()['it'] == 0

    def test_the_rejection_is_the_filter_module_type_and_a_value_error(self, ts):
        """One exception type across the package; `except ValueError` still
        catches it, as the existing container-argument test relies on."""
        with pytest.raises(InvalidParameterError):
            ts.set_outlier_filter(order=4.7)

    def test_the_params_dict_path_applies_the_same_rule(self, ts):
        with pytest.raises(ValueError, match=r"max_iterations must be a positive integer"):
            ts.set_outlier_filter(params={'frac': 0.1, 'max_iterations': 5.0})

    def test_a_numpy_integer_is_stored_as_a_plain_int(self, ts):
        ts.set_outlier_filter(max_iterations=np.int64(7), order=np.int32(3), it=np.uint8(1))
        params = ts.get_outlier_filter_params()
        assert params['max_iterations'] == 7 and type(params['max_iterations']) is int
        assert params['order'] == 3 and type(params['order']) is int
        assert params['it'] == 1 and type(params['it']) is int

    def test_a_bad_value_leaves_the_configuration_untouched(self, ts):
        ts.set_outlier_filter(max_iterations=7, frac=0.2)
        with pytest.raises(ValueError):
            ts.set_outlier_filter(frac=0.3, order=True)
        params = ts.get_outlier_filter_params()
        assert params['max_iterations'] == 7
        assert params['frac'] == 0.2
        assert params['order'] == 2  # FilterConfig's default, never overwritten
