# -*- coding: utf-8 -*-
"""
Created on Oct 19 2024
@author: stan@sympaticog.com
"""

from __future__ import annotations
from typing import Any, Union, Optional, Literal, TYPE_CHECKING
import numbers
from decimal import Decimal

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, savgol_filter
from dataclasses import dataclass
from scipy import signal

from .utils import validate_finite_data, validate_sampling_freq

if TYPE_CHECKING:
    from .core import baseTs

# Type aliases
ArrayLike = Union[np.ndarray, list]
InterpolationMethod = Literal['linear', 'nearest', 'zero', 'slinear', 'quadratic', 'cubic']

def zscale(x: ArrayLike) -> np.ndarray:
    """Standardize data by removing the mean and scaling to unit variance."""
    return (x - np.mean(x)) / np.std(x)

@dataclass
class FilterConfig:
    """Configuration for filter parameters."""
    order: int = 5
    window_length: int = 11
    polyorder: int = 2
    reset_mean: bool = True

class FilterError(Exception):
    """Base exception for filter-related errors."""
    pass

class InvalidParameterError(FilterError, ValueError):
    """Exception raised for invalid filter parameters.

    Also a ValueError, for the same reason as utils.ValidationError: a rejected
    parameter is an invalid value, and this module translates bare ValueErrors
    from validate_sampling_freq into this type, so the two halves of one call
    were catchable only by naming both.

    Widening only - `except FilterError` and `except InvalidParameterError` are
    unaffected, and FilterError precedes ValueError in the MRO.

    Note the shape this creates in the translation sites below:
    `except ValueError: raise InvalidParameterError(...)` can now catch this
    type. Each try block deliberately holds a single call into utils
    (validate_sampling_freq, or validate_finite_data since #48), which raises
    a bare ValueError and never this one, so nothing double-wraps - pinned by
    a test per site, since the tightness is what makes it safe.
    """
    pass

def _require_real(label: str, value) -> None:
    """
    Reject a parameter that is not a real scalar.

    Membership is tested against numbers.Real rather than by attempting
    float(value). `float(np.array([0.1]))` returns 0.1 on numpy 1.x and raises
    on 2.x, so a float()-based guard would accept a one-element array on one
    CI leg and reject it on another with the suite green either way - the trap
    PR #26 hit with `float(np.array([30.0]))`.

    Decimal is admitted alongside numbers.Real because it is registered under
    numbers.Number only, and rejecting it here would have this module accept a
    Decimal *rate* - validate_sampling_freq does so deliberately - while
    refusing a Decimal *band edge*. One type, two answers, same call.

    bool is excluded explicitly: it is a Real, and `True` as a band edge or a
    window step is a mistake worth naming rather than silently reading as 1.
    Complex is excluded by construction, being neither.
    """
    if isinstance(value, bool) or not isinstance(value, (numbers.Real, Decimal)):
        raise InvalidParameterError(
            f"{label} must be a real number, got {value!r}")


def _as_real_float(label: str, value) -> float:
    """Type-check a parameter and coerce it to a plain float.

    NaN and the infinities pass through: callers that must reject them say so
    with their own check, so the message can name the actual rule broken.

    Coercing matters beyond tidiness. numbers.Real is a registrable ABC, so an
    accepted value can be an object whose comparisons are stateful - two
    textually identical checks need not agree, and reasoning about whether one
    of them is redundant becomes unsound. Every comparison downstream is
    against the float this returns, which removes the question instead of
    answering it.
    """
    _require_real(label, value)

    # A Python int is a Real of unbounded width, so it passes the membership
    # test and then dies in the conversion: float(10**400) raises
    # OverflowError. Unwrapped, that escapes the contract exactly as the bare
    # TypeError this helper exists to prevent - the same class of hole, one
    # step further in.
    #
    # All three conversion errors are caught, matching validate_sampling_freq,
    # which wraps the identical float() call in
    # `except (TypeError, ValueError, OverflowError)`. numbers.Real is a
    # registrable ABC, so a virtual subclass can carry a __float__ that raises
    # anything - or no __float__ at all, which makes float() raise TypeError.
    # An earlier revision caught only OverflowError and was narrower than the
    # sibling guard it was modelled on.
    try:
        number = float(value)
    except OverflowError as exc:
        raise InvalidParameterError(
            f"{label} is too large to convert to a float, got {value!r}") from exc
    except (TypeError, ValueError) as exc:
        raise InvalidParameterError(
            f"{label} could not be converted to a float, got {value!r}") from exc

    return number


def _require_finite_real(label: str, value) -> float:
    """Coerce, and additionally reject NaN and the infinities.

    Used for parameters that are arithmetic operands rather than comparands.
    NaN survives every `<`/`>=` comparison as False, so a NaN reaching
    `max(1, window_step - overlap)` is silently clamped rather than rejected -
    the same order-dependent `max()` blindness this module had for band edges.
    """
    number = _as_real_float(label, value)
    if not np.isfinite(number):
        raise InvalidParameterError(
            f"{label} must be a real number and finite, got {value!r}")
    return number


def _require_order(order: Any, label: str = "Filter order") -> int:
    """Type-check a filter order and coerce it to a plain int.

    `order <= 0` was the whole check (#49). `True` is an int in Python, so it
    passed and built an order-1 filter; `'4'` died in the comparison with a
    bare TypeError; `3.5` passed and was left to whatever the installed scipy
    does with a float order. numbers.Integral rather than int so numpy
    integers are admitted, and int() so the value handed to scipy is the one
    checked here - the same rule as _as_real_float, one type down.

    An integral-valued float such as 4.0 is rejected too. Admitting it would
    mean choosing between `int(4.0)` and rejecting 4.5 by a second rule, and
    an order is a count of poles, not a measurement.
    """
    if (isinstance(order, bool) or not isinstance(order, numbers.Integral)
            or int(order) <= 0):
        raise InvalidParameterError(
            f"{label} must be a positive integer, got {order!r}")
    return int(order)


def _require_finite_data(data: ArrayLike) -> None:
    """The filter family's data guard, translated into this module's type.

    filtfilt's bidirectional pass propagates a single NaN across the whole
    output, so four bad samples came back as six hundred with no exception
    and no warning (#48). #28 placed the shared guard at the spectral
    family's production site; this is the filter family's. Complex is
    allowed - filtfilt filters the two parts independently, and the
    one-sided-spectrum reasoning behind the guard's default does not apply.

    A helper rather than an inline call because it must run *last*, after
    every parameter check, and two validators need to say so: a bad call is
    a bug in the call, bad data is a property of the input, and the O(n)
    scan should not be what tells the caller about a cutoff they mistyped.
    The try block holds this one call only, for the reason
    InvalidParameterError gives, and is pinned against double-wrapping.
    """
    try:
        validate_finite_data(data, allow_complex=True)
    except ValueError as exc:
        raise InvalidParameterError(str(exc)) from exc


def validate_filter_params(data: ArrayLike,
                           sampling_freq: float,
                           cutoff_freq: float,
                           order: int) -> tuple:
    """
    Validate the parameters and data of a single-cutoff filter.

    The parameter checks, then the data scan, in that order. The band and
    notch validators compose the two halves themselves so that their own
    edge checks can sit between them: see _validate_filter_args.

    Args:
        data: Input data array
        sampling_freq: Sampling frequency in Hz
        cutoff_freq: Cutoff frequency in Hz
        order: Filter order

    Returns:
        `(sampling_freq, cutoff_freq, order)`: the rate and cutoff as plain
        floats, the order as a plain int. Callers must compute with all three
        rather than with their own arguments. validate_sampling_freq accepts
        exact Reals such as Decimal, which pass validation and then die on
        `0.5 * fs` with a raw TypeError outside this function's try/except;
        and a cutoff that is validated here and then divided by the caller
        is only validated if the two objects agree, which a numbers.Real
        virtual subclass need not (#49 - the hole #30 closed for
        bandpass_filter, in the three siblings it left untouched).

    Raises:
        InvalidParameterError: If parameters or data are invalid
    """
    checked = _validate_filter_args(data, sampling_freq, cutoff_freq, order)
    _require_finite_data(data)
    return checked


def _validate_filter_args(data: ArrayLike,
                          sampling_freq: float,
                          cutoff_freq: float,
                          order: int) -> tuple:
    """The parameter half of validate_filter_params: everything but the data
    scan. Returns the same `(sampling_freq, cutoff_freq, order)` triple.

    Split out so validate_band_params can check its lower edge and the
    ordering *before* the O(n) data scan. With the scan inside the delegated
    call, a mistyped hp_hz on gappy data reported the gaps - the parameter
    rule inverted for exactly the entry point that has the most parameters
    (review of #48).
    """
    if not isinstance(data, (np.ndarray, list)):
        raise InvalidParameterError("Data must be a numpy array or list")

    # `sampling_freq <= 0` is False for NaN, so a degenerate time base used to
    # reach butter()/filtfilt() and come back as an all-NaN array with nothing
    # but a RuntimeWarning. Delegated so there is one definition of a usable
    # rate, but re-raised as InvalidParameterError to keep this module's
    # exception type for callers that catch it. The try block holds this one
    # call only: see InvalidParameterError on why that tightness matters.
    try:
        sampling_freq = validate_sampling_freq(sampling_freq)
    except ValueError as exc:
        raise InvalidParameterError(str(exc)) from exc

    # Coerced before it is compared, so the range check below and the
    # division in the caller see the same float. Ordered after the rate check
    # so a NaN rate reports the degenerate time base rather than a confusing
    # cutoff error.
    cutoff_freq = _as_real_float("Cutoff frequency", cutoff_freq)

    # Also NaN-blind on its own. The limit is named, not just the rule. A
    # message stating no number sends the caller round the loop a second time
    # on a value that was never going to work, which is the #28 lesson - a
    # message that implies a remedy has to carry enough for the remedy to be
    # right.
    if not (cutoff_freq > 0) or cutoff_freq >= sampling_freq/2:
        raise InvalidParameterError(
            f"Cutoff frequency must be positive and less than Nyquist frequency "
            f"(cutoff_freq={cutoff_freq!r}, Nyquist={sampling_freq/2} Hz)")

    order = _require_order(order)

    return sampling_freq, cutoff_freq, order


def validate_band_params(data: ArrayLike,
                         sampling_freq: float,
                         hp_hz: float,
                         lp_hz: float,
                         order: int,
                         window_step: int = 1) -> tuple:
    """
    Validate the parameters of a two-edged (band) filter.

    Args:
        data: Input data array
        sampling_freq: Sampling frequency in Hz, before windowing
        hp_hz: High-pass (lower) band edge in Hz
        lp_hz: Low-pass (upper) band edge in Hz
        order: Filter order
        window_step: Step size of the windowed analysis, already net of
            overlap. The band edges are checked against the rate this
            produces, not against `sampling_freq`.

    Returns:
        `(effective_freq, hp_hz, lp_hz)`, all plain floats.

        Callers must use all three, not just the first. The rate is the
        normalised one (see validate_filter_params on why the raw argument is
        unusable) and the rate the band was actually validated against. The
        edges are the coerced values that were validated - which is the point:
        a caller that validates these and then computes with its own originals
        is filtering something other than what was checked. That was a real
        hole, not a hypothetical one: `signal.butter(3, [hp_hz/nyq,
        lp_hz/nyq])` divided the caller's objects, so a numbers.Real whose
        __truediv__ disagreed with its __float__ passed every guard here and
        then produced a bare scipy ValueError about Wn.

    Raises:
        InvalidParameterError: If parameters are invalid

    Notes:
        Callers used to validate with `max(hp_hz, lp_hz)`, which checked one
        edge and picked which one by argument position, since `max()` is
        order-dependent on NaN (#30). Both edges are checked here, along with
        the relation between them.

        Data and order are delegated to validate_filter_params rather than
        re-derived. Local copies of a shared check are what let the spectral
        family drift apart before #28.

        The rate is normalised through the same shared door before any
        arithmetic touches it: a Decimal or string rate would otherwise die on
        the division below with a raw TypeError, outside the
        InvalidParameterError contract.

        The delegated call receives the *effective* rate, not the declared
        one, so its Nyquist figure is the limit the filter will really apply.
        An earlier revision passed the declared rate and reported a limit of
        5.0 Hz where the real one was 1.25, which is worse than reporting no
        limit at all - a caller retrying just under the quoted figure failed
        again.

        The delegated call is what range-checks `lp_hz`, so the check below
        covers `hp_hz` only. An earlier revision tested both edges again
        afterwards; that second `lp_hz` test was unreachable, since the
        delegated call evaluates the same predicate on the same value against
        the same Nyquist and raises first.

        "The same value" is doing real work in that sentence, and is why the
        edges are coerced to float above rather than merely type-checked. A
        `numbers.Real` virtual subclass may answer the identical comparison
        differently on two calls, which would make the removed test reachable
        after all - textually identical predicates are not observationally
        identical over an ABC-registered domain. Comparing coerced floats makes
        the redundancy real rather than assumed.

        One visible asymmetry remains: an out-of-range `lp_hz` is reported with
        the generic cutoff message rather than a band-specific one naming the
        edge. That message carries the offending value and the real limit, so
        it is complete; only its wording differs.

        Edges are checked before their ordering, so a band that is both
        out-of-range and out-of-order reports the out-of-range edge - the more
        specific complaint of the two.
    """
    # The rate first, and through the shared door, so it is a normalised float
    # before it is divided.
    try:
        sampling_freq = validate_sampling_freq(sampling_freq)
    except ValueError as exc:
        raise InvalidParameterError(str(exc)) from exc

    window_step = _require_finite_real('Window step', window_step)
    if not window_step >= 1:
        raise InvalidParameterError(
            f"Window step must be at least 1, got {window_step!r}")

    effective_freq = sampling_freq / window_step

    # Scalar-ness before any comparison: `not (edge > 0)` on an array raises
    # numpy's ambiguity ValueError, which escapes this module's contract.
    # Coerced in the same breath, so every comparison below - and the one
    # inside the delegated call - is against a plain float rather than against
    # an object free to answer the same question twice, differently.
    hp_hz = _as_real_float("Band edge hp_hz", hp_hz)
    lp_hz = _as_real_float("Band edge lp_hz", lp_hz)

    # The coerced upper edge comes back and is what gets returned below. The
    # order is validated but not returned: bandpass_filter passes a literal.
    # The parameter half only: the data scan runs last, below, after the
    # lower edge and the ordering have had their say.
    effective_freq, lp_hz, _ = _validate_filter_args(
        data, effective_freq, lp_hz, order)
    nyquist = effective_freq / 2

    # `not (hp_hz > 0)` rather than `hp_hz <= 0`, which is False for NaN.
    # Only the lower edge: the delegated call above already range-checked
    # lp_hz against this same nyquist.
    if not (hp_hz > 0) or hp_hz >= nyquist:
        raise InvalidParameterError(
            f"Band edge hp_hz must be positive and less than the Nyquist "
            f"frequency ({nyquist} Hz), got {hp_hz!r}")

    if not (hp_hz < lp_hz):
        raise InvalidParameterError(
            f"Band edges out of order: hp_hz={hp_hz!r} must be less than "
            f"lp_hz={lp_hz!r}")

    _require_finite_data(data)

    return effective_freq, hp_hz, lp_hz


def sg_filter(data: ArrayLike,
              window_length: int = 11, 
              polyorder: int = 2) -> np.ndarray:
    """
    Apply a Savitzky-Golay filter to the input data.
    
    Args:
        data: Input data array
        window_length: Length of the filter window (must be odd)
        polyorder: Order of the polynomial fit
        
    Returns:
        Filtered data array
        
    Raises:
        InvalidParameterError: If parameters are invalid
    """
    data = np.asarray(data)
    
    # Adjust window length if necessary
    if window_length >= len(data):
        window_length = len(data) - 1 if len(data) % 2 == 0 else len(data)
    if polyorder >= window_length:
        polyorder = window_length - 1
    if window_length % 2 == 0:
        window_length += 1
        
    return savgol_filter(data, window_length, polyorder)


NOTCH_HALF_WIDTH = 0.01
"""Half-width of the band notch_filter stops, as a fraction of Nyquist.

The stopped band is `cutoff_hz +/- NOTCH_HALF_WIDTH * nyquist`, so in Hz it
widens with the sampling rate: 0.05 Hz each side at 10 Hz, 5 Hz each side at
1 kHz. That is the rule the function has always applied (in normalised units,
`cutoff/nyquist +/- 0.01`); it is named here so validate_notch_params can
check the same band `butter` receives, and so a change to a Hz- or Q-based
width is a decision rather than a drift.
"""


def validate_notch_params(data: ArrayLike,
                          sampling_freq: float,
                          cutoff_hz: float,
                          order: int) -> tuple:
    """
    Validate the parameters and data of a notch filter.

    Args:
        data: Input data array
        sampling_freq: Sampling frequency in Hz
        cutoff_hz: Notch frequency in Hz
        order: Filter order

    Returns:
        `(sampling_freq, low, high, order)`: the rate as a plain float, the
        two edges of the stopped band in *normalised* units (fractions of
        Nyquist, what `butter` takes as `Wn`), and the order as a plain int.
        Callers must filter with the returned edges, not rebuild them: these
        are the two floats that were range-checked.

    Raises:
        InvalidParameterError: If parameters or data are invalid

    Notes:
        notch_filter used to validate `cutoff_hz` against (0, Nyquist) and
        then stop the band `cutoff/nyquist +/- 0.01` - two derived edges the
        validator never saw, so a cutoff within 1% of Nyquist of either end
        passed and died in scipy with a bare ValueError about `Wn` (#76).
        The #49 shape, reached by a different route: the value filtered was
        derived from the value validated by a rule the validator did not
        know. The band is now built here and checked as built.

        The notch range check runs before the delegated single-cutoff check
        rather than after it, so *every* out-of-range cutoff - zero, negative,
        NaN, at or above Nyquist, or merely inside the half-width - gets the
        one message that quotes the limits a retry has to meet. Delegating
        first would have reported `less than Nyquist (5.0 Hz)` for a cutoff
        of 5.0, and a caller who retried at 4.99 on that advice was refused
        again. That makes the delegated call's own cutoff range check
        unreachable from here (the notch range is strictly inside it); it is
        still called for the data type, the order, and one definition of a
        usable rate.

        Parameters before the O(n) data scan, as in validate_band_params: a
        mistyped notch on gappy data names the notch, not the gaps.

        Precedence among the parameters is the siblings': the cutoff range
        is judged before the order, as `_validate_filter_args` judges it.
        A cutoff in the newly refused margin combined with a bad order
        therefore reports the cutoff where `main` reported the order - a
        consequence of the tighter range, not of a reordering. Only the
        data-container check moves behind the range check, and it is
        unreachable from notch_filter, which `asarray`s first.
    """
    # The rate first, and through the shared door, so it is a normalised
    # float before it is divided.
    try:
        sampling_freq = validate_sampling_freq(sampling_freq)
    except ValueError as exc:
        raise InvalidParameterError(str(exc)) from exc

    nyquist = sampling_freq / 2.0

    # The shared rate check admits any positive finite float, and halving the
    # smallest of them (5e-324) underflows to exactly 0.0. The siblings only
    # compare against it; this validator divides by it, so the division
    # needs its own guard or a bare ZeroDivisionError escapes the contract.
    if not (nyquist > 0):
        raise InvalidParameterError(
            f"Sampling frequency {sampling_freq!r} Hz is too small: its "
            f"Nyquist frequency underflows to 0 Hz")

    # Coerced before it is divided, so the edges below and the ones butter
    # receives are computed from the same float.
    # Labelled "Cutoff frequency", the parameter's name in the siblings, so the
    # type and conversion messages stay byte-identical to theirs; only the
    # range rule below is notch-specific and says "Notch frequency".
    cutoff_hz = _as_real_float("Cutoff frequency", cutoff_hz)
    notch = cutoff_hz / nyquist
    low, high = notch - NOTCH_HALF_WIDTH, notch + NOTCH_HALF_WIDTH

    # scipy requires 0 < Wn < 1 for every edge. `not (low > 0)` rather than
    # `low <= 0`, which is False for NaN. Checked on the derived edges, not on
    # the cutoff against a pre-computed range, so the predicate is the one
    # scipy applies to the numbers scipy gets - at the exact boundary the two
    # spellings can disagree by an ulp.
    if not (low > 0) or not (high < 1):
        half_width_hz = NOTCH_HALF_WIDTH * nyquist
        raise InvalidParameterError(
            f"Notch frequency must be more than {half_width_hz} Hz "
            f"({NOTCH_HALF_WIDTH:.0%} of Nyquist) from both 0 Hz and the "
            f"Nyquist frequency ({nyquist} Hz), because the stopped band is "
            f"the notch frequency +/- {half_width_hz} Hz: "
            f"{half_width_hz} < cutoff_hz < {nyquist - half_width_hz} Hz; "
            f"got cutoff_hz={cutoff_hz!r}")

    # The data type, the order, and the rate again through the same door.
    # Its cutoff range check cannot fire: the notch check above is strictly
    # tighter on the same float.
    sampling_freq, _, order = _validate_filter_args(
        data, sampling_freq, cutoff_hz, order)

    _require_finite_data(data)

    return sampling_freq, low, high, order


def notch_filter(data: ArrayLike, 
                 cutoff_hz: float, 
                 fs_hz: float, 
                 order: int = 5) -> np.ndarray:
    """
    Apply a symmetric notch filter to the input data.

    The stopped band is `cutoff_hz +/- 1% of Nyquist` (NOTCH_HALF_WIDTH), so
    the notch must sit more than that half-width from both 0 Hz and Nyquist.
    
    Args:
        data: Input data array
        cutoff_hz: Notch frequency in Hz
        fs_hz: Sampling frequency in Hz
        order: Filter order
        
    Returns:
        Filtered data array
        
    Raises:
        InvalidParameterError: If parameters are invalid, the notch lies
            within the half-width of either end, or the data has gaps
    """
    data = np.asarray(data)
    fs_hz, low, high, order = validate_notch_params(data, fs_hz, cutoff_hz, order)

    b, a = butter(order, [low, high], btype='bandstop')
    return filtfilt(b, a, data)
    
def highpass_filter(data: ArrayLike, 
                    highpass_freq: float, 
                    sampling_freq: float, 
                    order: int = 5) -> np.ndarray:
    """
    Apply a symmetric highpass filter to the input data.
    
    Args:
        data: Input data array
        highpass_freq: Highpass cutoff frequency in Hz
        sampling_freq: Sampling frequency in Hz
        order: Filter order
        
    Returns:
        Filtered data array
        
    Raises:
        InvalidParameterError: If parameters are invalid
    """
    data = np.asarray(data)
    sampling_freq, highpass_freq, order = validate_filter_params(
        data, sampling_freq, highpass_freq, order)

    nyquist_rate = sampling_freq / 2.0
    high = highpass_freq / nyquist_rate
    b, a = butter(order, high, btype='high')
    return filtfilt(b, a, data)

def lowpass_filter(data: ArrayLike, 
                   cutoff: float, 
                   fs: float, 
                   order: int = 5) -> np.ndarray:
    """
    Apply a symmetric lowpass filter to the input data.
    
    Args:
        data: Input data array
        cutoff: Cutoff frequency in Hz
        fs: Sampling frequency in Hz
        order: Filter order
        
    Returns:
        Filtered data array
        
    Raises:
        InvalidParameterError: If parameters are invalid
    """
    data = np.asarray(data)
    fs, cutoff, order = validate_filter_params(data, fs, cutoff, order)

    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return filtfilt(b, a, data)

def bandpass_filter(data: ArrayLike,
                   hp_hz: float = 0.01,
                   lp_hz: float = 0.1,
                   sample_Hz: float = 30,
                   window_step: int = 1,
                   overlap: int = 0,
                   reset_mean: bool = True) -> np.ndarray:
    """
    Apply a symmetric bandpass filter to the input data.
    
    Args:
        data: Input data array
        hp_hz: High-pass cutoff frequency in Hz
        lp_hz: Low-pass cutoff frequency in Hz
        sample_Hz: Sampling frequency in Hz
        window_step: Step size for windowed analysis
        overlap: Overlap size for windowed analysis
        reset_mean: Whether to reset the mean of filtered data to original mean
        
    Returns:
        Filtered data array
        
    Raises:
        InvalidParameterError: If parameters are invalid
    """
    data = np.asarray(data)

    # Effective sampling rate of windowed analysis, computed before validation
    # rather than after it: this is the rate the band edges are normalised by
    # below, so it is the rate they have to be validated against (#30).
    #
    # Both operands are checked before the subtraction, which is eager enough
    # to raise a bare TypeError on a string or None, and before the max(),
    # which is order-dependent on NaN exactly as `max(hp_hz, lp_hz)` was:
    # `max(1, nan)` returns 1, so a NaN step used to be silently clamped and
    # the filter ran at a rate the caller never asked for.
    window_step = _require_finite_real('window_step', window_step)
    overlap = _require_finite_real('overlap', overlap)
    window_step = max(1, window_step - overlap)
    # The coerced edges come back and are what gets filtered. Validating one
    # value and computing with another is not validation (#30).
    effective_fs, hp_hz, lp_hz = validate_band_params(
        data, sample_Hz, hp_hz, lp_hz, 3, window_step=window_step)

    nyq = effective_fs / 2
    b, a = signal.butter(3, [hp_hz/nyq, lp_hz/nyq], btype='band')
    filtered = signal.filtfilt(b, a, data)

    if reset_mean:
        filtered += (data.mean() - filtered.mean())
    
    return filtered

def interpolate_missing_values(ts: baseTs,
                             interpolation_method: str = 'linear',
                             order: int = 1,
                             inplace: bool = False) -> Optional[baseTs]:
    """
    Interpolate missing values in a time series.

    Args:
        ts: Time series object
        interpolation_method: Method of interpolation ('linear', 'cubic', etc.)
        order: Order of interpolation (for spline methods)
        inplace: Whether to modify the existing object or return a new one

    Returns:
        Optional[baseTs]: New time series with interpolated values if inplace=False,
                         None if inplace=True
    """
    if interpolation_method not in ['linear', 'nearest', 'zero', 'slinear', 'quadratic', 'cubic']:
        raise ValueError(f"Invalid interpolation method: {interpolation_method}")
        
    data = ts.data
    time_index = ts.times
    
    cleaned_series = pd.Series(data, index=time_index)
    interpolated_series = cleaned_series.interpolate(
        method=interpolation_method, 
        order=order
    )
    
    # Handle any remaining NaN values
    if interpolated_series.isnull().any():
        interpolated_series = interpolated_series.ffill().bfill()
        
    if inplace:
        ts.data = interpolated_series.values
        return None
    
    res = ts.copy()
    res.data = interpolated_series.values
    return res
