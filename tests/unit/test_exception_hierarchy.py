"""The domain exceptions are also ValueErrors.

Both validating families raise a type of their own - `ValidationError` for a
bad lag, `InvalidParameterError` for a bad filter parameter - while the shared
validators underneath them (`validate_sampling_freq`) raise a bare `ValueError`.
Before this change neither domain type inherited `ValueError`, so no single
except clause covered one call: catching `ValueError` missed the domain error,
catching `TimeSeriesError` missed the rate error, and a caller who wanted "tell
me when my input was rejected" had to name both.

That is not a hypothetical. #30 and #32 each shipped a documented breaking
change of exactly this shape - "code catching ValueError will stop catching
these" - and both were still unreleased. Widening the hierarchy retires both
rather than documenting them.

Widening only: every existing `except ValidationError` / `except FilterError`
keeps working, because the domain identity is kept alongside the new base.
"""
import numpy as np
import pytest

from baseTs import baseTs
from baseTs.filters import FilterError, InvalidParameterError, bandpass_filter
from baseTs.utils import (TimeSeriesError, ValidationError, shift_timeseries,
                          time_to_idx)


def _uniform():
    return baseTs(np.sin(np.arange(300) / 10.0), np.arange(300) / 100.0,
                  freq=100.0)


def _degenerate():
    return baseTs(np.sin(np.arange(300) / 10.0), np.zeros(300))


class TestTheDomainTypesAreAlsoValueErrors:
    """The identity is added, never swapped."""

    def test_validation_error_is_a_value_error(self):
        assert issubclass(ValidationError, ValueError)

    def test_invalid_parameter_error_is_a_value_error(self):
        assert issubclass(InvalidParameterError, ValueError)

    def test_validation_error_keeps_its_domain_identity(self):
        assert issubclass(ValidationError, TimeSeriesError)

    def test_invalid_parameter_error_keeps_its_domain_identity(self):
        assert issubclass(InvalidParameterError, FilterError)

    def test_the_domain_base_is_still_reached_first(self):
        """Order matters for an `except TimeSeriesError` / `except ValueError`
        pair written in that order: the domain clause must win."""
        assert ValidationError.__mro__.index(TimeSeriesError) < \
            ValidationError.__mro__.index(ValueError)


class TestOneExceptClauseNowCoversOneCall:
    """The point of the change, tested through real calls rather than issubclass.

    A single `lag_plot`/`shift_timeseries` call can reject either argument, and
    the two rejections came from different branches of the hierarchy.
    """

    def test_a_bad_rate_and_a_bad_lag_are_caught_by_one_clause(self):
        with pytest.raises(ValueError):
            shift_timeseries(_degenerate(), 0.5, "seconds")   # the rate
        with pytest.raises(ValueError):
            shift_timeseries(_uniform(), np.nan, "seconds")   # the lag

    def test_the_same_holds_for_the_filter_family(self):
        data = np.sin(np.arange(500) / 10.0)

        with pytest.raises(ValueError):
            bandpass_filter(data, hp_hz=0.1, lp_hz=0.4, sample_Hz=np.nan)
        with pytest.raises(ValueError):
            bandpass_filter(data, hp_hz=-1.0, lp_hz=0.4, sample_Hz=10.0)

    def test_catching_the_domain_type_still_works(self):
        """Existing code that names the domain type must be unaffected."""
        with pytest.raises(ValidationError):
            time_to_idx(np.nan, 100.0)
        with pytest.raises(TimeSeriesError):
            time_to_idx(np.nan, 100.0)


class TestNoFallbackPathStartsSwallowingADomainError:
    """The real risk of widening: 14 `except ValueError` sites in the package.

    Each wraps a builtin conversion or a single validator that raises a bare
    ValueError, so none can catch a domain error - but that is an argument, and
    these are the two places where being wrong would be silent.
    """

    def test_the_filter_rate_translation_does_not_double_wrap(self):
        """`except ValueError -> raise InvalidParameterError` in filters now
        has a self-catching shape. Its try block holds only
        validate_sampling_freq, so the message must still be the rate's."""
        with pytest.raises(InvalidParameterError) as excinfo:
            bandpass_filter(np.sin(np.arange(500) / 10.0),
                            hp_hz=0.1, lp_hz=0.4, sample_Hz=np.nan)

        assert "Invalid sampling frequency" in str(excinfo.value)
        assert str(excinfo.value).count("Invalid sampling frequency") == 1

    def test_the_filter_data_translation_does_not_double_wrap(self):
        """#48 added a second translation site of the same shape, around
        validate_finite_data. Same tightness, same pin."""
        data = np.sin(np.arange(500) / 10.0)
        data[100] = np.nan
        with pytest.raises(InvalidParameterError) as excinfo:
            bandpass_filter(data, hp_hz=0.1, lp_hz=0.4, sample_Hz=10.0)

        assert str(excinfo.value).count("NaN or Inf") == 1

    def test_a_degenerate_index_still_derives_rather_than_raising(self):
        """`_calculate_effective_frequency` catches (TypeError, ValueError) to
        fall back to NaN. If a domain error could reach it, a bad rate would
        become a silent NaN instead of a diagnosis."""
        assert np.isnan(_degenerate().freq)
