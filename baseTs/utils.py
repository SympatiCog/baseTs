# -*- coding: utf-8 -*-
"""
Utility functions for time series analysis and signal processing.
Created on Oct 19 2024
@author: stan@sympaticog.com
"""

import math
import numbers
from dataclasses import dataclass
from typing import Union, Dict, Tuple, List, Any, Optional #, TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray
from scipy.signal import find_peaks

# if TYPE_CHECKING:
#     from .core import baseTs

def coerce_real_scalar(value: Any, description: str) -> float:
    """Coerce a scalar argument to a float, or raise ValueError naming it.

    The type half of validate_sampling_freq, shared rather than copied so a
    second caller with different *range* rules does not carry a second copy of
    the *type* rules. Local copies of a shared check are exactly what let the
    four spectral entry points drift apart before #28, and the reasoning below
    is subtle enough that a copy would drift quietly.

    The returned value may be NaN or infinite: this decides only whether the
    argument is a real scalar at all. Each caller applies its own range rule,
    because they genuinely differ - a sampling rate must be finite and
    positive, a plot's `max_rate` takes NaN as its "use Nyquist" sentinel, and
    a plot's `min_rate` may be zero.

    Args:
        value: The argument to coerce
        description: How to name the argument in the error, e.g.
            "Invalid sampling frequency" or "Invalid max_rate". Used as a
            prefix, so it should read as a noun phrase.

    Returns:
        The value as a plain float, which may be NaN or infinite

    Raises:
        ValueError: If the value is not a real scalar
    """
    # Converted via float() rather than gated on numbers.Real: Fraction, int
    # >= 2**63 and np.timedelta64 are all Real and all satisfy `> 0`, but
    # np.isfinite has no object-dtype loop and raises TypeError on them -
    # which would break the ValueError promise this docstring makes, and
    # escape the `except ValueError` translation in filters. float() accepts
    # everything np.fft.fftfreq can actually use, including 0-d arrays and
    # Decimal, and raises for multi-element arrays.
    #
    # str and bool are excluded first: float("30") succeeds, and a bool is a
    # Real, so True would otherwise be accepted as 1.0 Hz. np.bool_ is listed
    # explicitly because it is NOT a subclass of Python bool, and it is what
    # every numpy comparison yields (`arr.mean() > 0`, `np.any(...)`).
    if isinstance(value, (bool, np.bool_, str, bytes)):
        raise ValueError(f"{description}: {value!r} is not a real number.")
    # A size-1 ndarray is rejected rather than unwrapped: float() accepts it on
    # numpy 1.x (with a DeprecationWarning) and raises on 2.x, so allowing it
    # would make this guard's accept/reject set differ across the CI matrix -
    # the same version-sensitivity that produced the objs/input_objs bug in
    # PR #25. 0-d arrays convert identically on both majors and stay allowed.
    if isinstance(value, np.ndarray) and value.ndim > 0:
        raise ValueError(
            f"{description}: {value!r} is not a scalar. Pass a "
            f"single number, e.g. float(arr[0])."
        )
    try:
        return float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        # OverflowError, not just TypeError/ValueError: float(10**400) raises
        # it, and it is neither - so it would escape both this contract and
        # the `except ValueError` translation in filters.
        raise ValueError(f"{description}: {value!r} is not a real number.") from exc

def validate_sampling_freq(freq: Any) -> float:
    """Reject a sampling rate that cannot produce meaningful frequency bins.

    Written as `not (value > 0)` rather than `value <= 0` because every
    comparison against NaN is False, so the latter lets NaN straight through.
    A NaN rate is reachable whenever the time base is degenerate:
    _calculate_effective_frequency returns NaN for a zero or negative
    duration. Passing that into np.fft.fftfreq(n, d=1/freq) yields NaN
    frequency bins instead of an error, so the caller gets silent nonsense.

    This is now also called from the `freq` property setter - the production
    door, where TimeSeriesData.__init__ and every explicit `ts.freq = ...`
    assignment route through it, so a bad rate is refused at the point it
    enters the object rather than surfacing later from whatever consumes it.
    The consumption-site calls below stay in place as defence in depth: a
    caller that bypasses the setter - writing `ts._freq_declaration` directly,
    or a duck-typed metadata copy - can still land a bad rate on the object,
    and these are what catch it if one does.

    Args:
        freq: The sampling rate to validate, in Hz

    Returns:
        The frequency as a float, when it is usable

    Raises:
        ValueError: If the frequency is not a real scalar, or is NaN,
            infinite, zero, or negative
    """
    # The type rules live in coerce_real_scalar, shared with the plotting
    # bounds; only the range rule below is specific to a sampling rate.
    value = coerce_real_scalar(freq, "Invalid sampling frequency")

    if not (value > 0) or not math.isfinite(value):
        # The degenerate-time-base hint applies to NaN only; a zero, negative
        # or infinite rate is almost always an explicit `freq=` argument, and
        # pointing those at the timestamps sends the reader the wrong way.
        hint = (
            " A NaN rate usually means the time base is degenerate (duplicate "
            "or non-increasing timestamps, giving zero duration)."
            if math.isnan(value) else ""
        )
        raise ValueError(f"Invalid sampling frequency: {freq} Hz.{hint}")
    return value

def _complex_data_message(what: str) -> str:
    """The rejection text for complex sample values (issue #43).

    `what` describes the offending dtype - "dtype 'complex128'", or
    "dtype 'object' holding complex values" - so that the two spellings of
    the same problem do not read as a contradiction.

    Names the reason (one-sided spectra presume real input) and the remedy
    (pick a real projection explicitly), because the obvious fix - taking
    the real part on the caller's behalf - is what relative_band_power used
    to do silently, and is what this rejection exists to stop.
    """
    return (
        f"Time series data is complex: {what}. The spectral functions return "
        f"one-sided spectra, keeping only non-negative frequencies on the "
        f"strength of a symmetry that real input has and complex input does "
        f"not - so the discarded half would be real content, not a mirror. "
        f"Pass the real projection you mean explicitly, e.g. `values.real`, "
        f"`values.imag` or `np.abs(values)`."
    )


def _holds_complex_numbers(arr: Any) -> bool:
    """Whether an object array that failed the float cast is complex numbers.

    Inspects the elements rather than asking whether a complex cast would
    succeed: complex('1+2j') parses where float('1+2j') does not, so a cast
    probe would route a malformed text column to the complex message and
    its `.real`/`.imag` remedies. Only genuine number objects count, and at
    least one must be non-real; a string among them means the data is not
    numeric, which is the more useful thing to say.
    """
    if arr.dtype.kind != "O":
        return False
    numbers_only = all(isinstance(x, numbers.Complex) for x in arr.flat)
    return numbers_only and any(
        not isinstance(x, numbers.Real) for x in arr.flat
    )


def validate_non_empty(data: Any) -> None:
    """Reject a series with no samples before it reaches np.fft.fftfreq.

    The third of the shared spectral guards, alongside validate_sampling_freq
    (the time base) and validate_finite_data (the sample values). This one is
    about the sample *count*: np.fft.fftfreq computes `1.0 / (n * d)`, so an
    empty series raised a bare ZeroDivisionError from inside numpy, outside
    the ValueError contract every spectral entry point documents (issue #62).
    validate_sampling_freq and validate_finite_data both pass an empty series -
    the rate is usable and there is no NaN in nothing - so neither could catch
    it, and until now only compute_fft_power carried a check of its own.

    Emptiness only. A single sample is accepted here: it is not a division by
    zero, and a threshold above zero would not buy a meaningful spectrum either
    (one sample and two samples both yield a DC-only spectrum). compute_fft_power
    documents its own minimum of two, which is its contract and not this
    guard's.

    Args:
        data: The sample values to check, as any array-like

    Raises:
        ValueError: If `data` contains no elements
    """
    # `.size`, not `len()`: a 0-d array holds one value and has no len(), and
    # an (0, k) array has k columns and no samples.
    if np.asarray(data).size == 0:
        raise ValueError(
            "Time series data is empty: a spectrum needs at least one sample."
        )


def validate_finite_data(data: Any, allow_complex: bool = False) -> None:
    """Reject sample values an FFT cannot produce a meaningful spectrum from.

    The companion to validate_sampling_freq: that one rejects a bad time base,
    this one rejects bad samples. A single NaN anywhere in the input makes
    np.fft.fft return an all-NaN spectrum - not a degraded one, an entirely
    meaningless one - and scipy's find_peaks still returns indices over an
    all-NaN array. get_peak_freq therefore reported a confident wrong number
    that was insensitive to how much of the data was bad (issue #28).

    Raising rather than dropping the bad samples is deliberate. Dropping would
    change the sample spacing, so the resulting bins would no longer be the
    frequencies they are labelled with, and the caller would not be told. The
    error names interpolate_gaps() because filling the gaps is the decision
    the caller has to make, and it is theirs to make explicitly.

    This lives in one place because the four spectral entry points had already
    drifted: compute_fft_power and relative_band_power each carried their own
    copy with different wording, and get_frequency_content carried none.

    Args:
        data: The sample values to check, as any array-like
        allow_complex: Accept complex dtypes, applying only the finiteness
            rule to them. The default rejects complex, which is right for
            every spectral consumer (#43). The filter family passes True
            (#48): filtfilt handles complex input correctly, filtering the
            real and imaginary parts independently, so the one-sided-spectrum
            reasoning does not apply there and the NaN rule is the one it
            shares.

    Raises:
        ValueError: If the data contains NaN or Inf, is complex (unless
            `allow_complex`), or is not numeric
    """
    arr = np.asarray(data)

    # Integer and boolean dtypes cannot represent NaN or Inf at all, so they
    # are accepted without inspection. Purely to avoid copying the whole array
    # to float64 on every call - the accept/reject set is identical either
    # way, since a cast integer is still finite.
    if arr.dtype.kind in "bui":
        return

    # datetime64 and timedelta64 are rejected before the float cast below,
    # because that cast SUCCEEDS on them and would wave NaT straight through:
    # NaT is stored as the int64 sentinel -2**63, which converts to a large
    # but perfectly finite float. np.isfinite then reports no problem, and the
    # value reaches np.fft.fft to die there as a DTypePromotionError naming an
    # internal promotion rule instead of the caller's data.
    if arr.dtype.kind in "Mm":
        # No remedy here mentions a cast through int64 or float. That is the
        # obvious suggestion and it is actively wrong: it reinterprets the
        # int64 storage, so NaT comes back as -9.22e18 - a large finite number
        # this guard would then accept, reproducing one level up the exact
        # silent-nonsense failure it exists to prevent. Subtracting or dividing
        # goes through datetime semantics instead and maps NaT to NaN, landing
        # the caller on the gap-filling message above.
        #
        # Split by kind because the two need genuinely different remedies:
        # dividing a datetime64 by a timedelta64 is not merely unhelpful, it
        # raises UFuncTypeError. An earlier revision offered the duration
        # remedy for both and left datetime callers to improvise, which is how
        # they would have found the int64 cast.
        if arr.dtype.kind == "m":
            remedy = (
                "Convert durations to a number of seconds first, e.g. "
                "`values / np.timedelta64(1, 's')`."
            )
        else:
            remedy = (
                "Convert timestamps to elapsed seconds first, e.g. "
                "`(values - values[0]) / np.timedelta64(1, 's')`."
            )
        raise ValueError(
            f"Time series data is not numeric: dtype '{arr.dtype}' holds "
            f"datetimes or durations, not sample values. {remedy} Note that "
            f"casting via `.astype(float)` or `.astype('int64')` will not do: "
            f"it exposes NaT's integer sentinel as a large finite number "
            f"rather than NaN, which this check would then accept."
        )

    # Complex is a dtype rejection, not a value one, so it comes before the
    # finiteness check: a complex array with a NaN in it would otherwise be
    # told to fill its gaps and then be rejected again for its dtype.
    #
    # Every consumer of this guard returns a one-sided spectrum - the
    # non-negative bins only - which is correct for real input because the
    # negative half is its mirror. Complex input has no such symmetry, so the
    # discarded half is genuine content. Before #43 the entry points handled
    # that in two different silent ways: relative_band_power cast to float
    # and kept the real part under a ComplexWarning, while the others fed the
    # complex data to np.fft.fft and threw away the negative half - which,
    # for an analytic signal, is all of it. get_peak_freq reported 0.388 Hz
    # for a 0.05 Hz probe with no warning at all.
    if arr.dtype.kind == "c" and not allow_complex:
        raise ValueError(_complex_data_message(f"dtype '{arr.dtype}'"))

    # Anything not already numeric (object arrays, most often) is converted so
    # np.isfinite has a dtype it can loop over - it raises TypeError on object
    # arrays. A complex array only reaches here when allowed, and np.isfinite
    # handles it directly: a value is finite when both parts are.
    if arr.dtype.kind not in "fc":
        try:
            arr = np.asarray(arr, dtype=float)
        except (TypeError, ValueError) as exc:
            # TypeError translated to ValueError to keep the promise this
            # docstring makes, the same way validate_sampling_freq does.
            # arr is unchanged here - the failed assignment above leaves the
            # original bound, so this reports the caller's dtype, not float.
            #
            # An object array of complex numbers fails the float cast too,
            # and deserves the complex message rather than "not numeric": the
            # caller has complex data, and the remedy is the one above.
            if _holds_complex_numbers(arr):
                # The keyword has to reach this branch too. The first cut
                # consulted it at the dtype check only, so complex hiding in
                # an object array was told to discard its imaginary part -
                # the opposite of what allow_complex promises.
                #
                # The helper has established every element is a number
                # *object* - but numbers.Complex is a registrable ABC, so
                # membership does not imply a working __complex__ any more
                # than numbers.Real implied a working __float__ in filters.
                # The cast is guarded like the float cast above for that
                # reason; a registered impostor is "not numeric", not a crash.
                if allow_complex:
                    try:
                        arr = np.asarray(arr, dtype=complex)
                    except (TypeError, ValueError) as cast_exc:
                        raise ValueError(
                            f"Time series data is not numeric: dtype "
                            f"'{arr.dtype}' cannot be interpreted as complex "
                            f"numbers."
                        ) from cast_exc
                else:
                    raise ValueError(_complex_data_message(
                        f"dtype '{arr.dtype}' holding complex values")) from exc
            else:
                raise ValueError(
                    f"Time series data is not numeric: dtype '{arr.dtype}' cannot "
                    f"be interpreted as real numbers."
                ) from exc

    finite = np.isfinite(arr)
    if not finite.all():
        # No finite sample at all: the remedy below presupposes a valid sample
        # to interpolate from, and the leading-gap hint presupposes a first
        # valid value to extend. Neither exists, so naming either would be a
        # remedy that does not run (review of #77).
        if not finite.any():
            raise ValueError(
                "Time series data contains NaN or Inf values and no finite "
                "ones: there is nothing to interpolate from."
            )
        message = ("Time series data contains NaN or Inf values. Fill gaps "
                   "first, e.g. with interpolate_gaps().")
        # A gap at the *start* is the one case the remedy above does not
        # clear: interpolate_gaps() forwards pandas' default
        # limit_direction='forward', which fills nothing before the first
        # valid sample, so a caller who follows the message lands back on it
        # (#77 - the #28 "remedy reproduces the bug" pattern one level up). A
        # trailing gap is different: under the default method the forward
        # fill extends the last valid value over it, so the plain remedy
        # works there and gets no hint. Keyed on the first sample being NaN,
        # not merely non-finite: interpolate_gaps() does not fill Inf in any
        # direction (#81), so a limit_direction hint would be a second remedy
        # that does not run for a leading-Inf caller. A leading NaN with an
        # Inf elsewhere still gets the hint: it is true of the leading gap
        # and following it clears that gap; what remains is #81's. And only
        # for 1-D input:
        # "starts with" is a claim about a series, and [0] of a 2-D array is
        # a row, not a sample (a 0-d NaN is all-NaN and never gets here, so
        # arr[0] cannot raise). The hint's remedy is scoped to the default
        # method because it is false for most others - measured over every
        # method pandas accepts, on pandas 2.2 and 3.0: the pandas-native
        # ones ('linear', 'time', 'index', 'values') extend the first valid
        # value; every scipy-backed one either fills no edge ('cubic',
        # 'polynomial', 'nearest', 'akima', ...) or extrapolates its fit
        # ('spline', 'pchip', 'cubicspline', 'barycentric'). Stated as the
        # rule rather than a list, because a two-name list missed 'cubic'
        # (review). A `limit` caps the edge fill like any other (docstring,
        # not message: it is the caller's own constraint).
        if arr.ndim == 1 and np.isnan(arr[0]):
            message += (
                " The series starts with a gap, which interpolate_gaps() "
                "leaves in place by default (it fills forward from the first "
                "valid sample): pass limit_direction='both', which with the "
                "default method extends the first valid value back over the "
                "edge - a constant fill, not an interpolation; the "
                "scipy-backed methods ('cubic', 'polynomial', 'spline', ...) "
                "leave an edge unfilled or extrapolate a fit. Alternatively, "
                "drop the samples before the first valid one."
            )
        raise ValueError(message)


def round_values(x: Any, decimals: int = 4) -> Any:
    """Round a float to a specified number of decimal places,
    or return the value unchanged if not a float."""
    return round(x, decimals) if isinstance(x, float) else x

def add_constant(ts: Any, constant: float = 0, inplace: bool = False) -> Any:
    """Add a constant to a time series."""
    from .core import baseTs
    x = ts.data.copy()
    t = ts.times.copy()
    x = x + constant
    
    if inplace:
        ts.data = x
        ts.times = t
        return ts
    else:
        res = baseTs(data=x, times=t)
        return res

def diff(ts: Any, zeropad: bool = False) -> Any:
    """Diff a time series."""
    from .core import baseTs
    x = ts.data.copy()
    t = ts.times.copy()
    if zeropad:
        d = np.diff(x)
        d = np.insert(d, 0, d[0])
    else:
        d = np.diff(x)
        t = t[1:]
    res = baseTs(data=d, times=t)
    return(res)

def dediff(ts: Any) -> Any:
    """Dediff a time series."""
    from .core import baseTs
    # x = ts.data.copy()
    t = ts.times.copy()
    cs = np.cumsum(ts.data)
    res = baseTs(data=cs, times=t)
    return(res)

class TimeSeriesError(Exception):   
    """Base exception for time series related errors."""
    pass

class ValidationError(TimeSeriesError, ValueError):
    """Exception raised for validation errors.

    Also a ValueError, because a rejected argument *is* an invalid value and
    `except ValueError` is what callers write. Without it no single except
    clause covered one call: the shared validators underneath this one
    (validate_sampling_freq) raise a bare ValueError, so catching ValueError
    missed the lag and catching TimeSeriesError missed the rate.

    Widening only - every `except ValidationError` and `except TimeSeriesError`
    keeps working, and TimeSeriesError precedes ValueError in the MRO, so a
    caller who lists both clauses still reaches the domain one first.
    """
    pass

@dataclass
class ClosestMatch:
    """Data class for storing closest match results."""
    value: float
    location: int
    target: Optional[float] = 0
    abs_err: Optional[float] = 0

@dataclass
class BandPowerResult:
    """
    Detailed breakdown of a relative band power computation.

    Attributes:
        ratio: The relative band power itself (band_sum / total_sum)
        ratio_type: Which convention produced it ('power' or 'amplitude')
        band_sum: Summed power (or amplitude) inside the band
        total_sum: Summed power (or amplitude) over all non-DC bins
        low_freq: Lower band edge in Hz (inclusive)
        high_freq: Upper band edge in Hz (inclusive)
        n_band_bins: Number of FFT bins inside the band
        n_total_bins: Number of non-DC FFT bins in the spectrum
        bin_fraction: n_band_bins / n_total_bins. This is the value both
            conventions converge on for white noise, so it is the reference
            point for "no band-specific structure" - the null is not zero.
        freq_resolution: Spacing between FFT bins in Hz (freq / n_samples)
        nyquist: Nyquist frequency in Hz
    """
    ratio: float
    ratio_type: str
    band_sum: float
    total_sum: float
    low_freq: float
    high_freq: float
    n_band_bins: int
    n_total_bins: int
    bin_fraction: float
    freq_resolution: float
    nyquist: float


def compute_fft_power(
    ts: Any,  # TODO: Replace with proper baseTs type
    demean: bool = True,
    scale_power: bool = True,
    max_rate: Optional[float] = None
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """
    Compute the power spectrum of a time series using FFT.

    Args:
        ts: Time series object with data and freq attributes
        demean: Whether to remove the mean before FFT
        scale_power: Whether to normalize the power spectrum
        max_rate: Maximum frequency to include in the output

    Returns:
        Tuple of (frequencies, power_spectrum)

    Raises:
        ValueError: If the time series is empty, has an invalid frequency, is
            complex, or contains NaN or Inf values
    """
    # Input validation. The empty check was a local copy until #62 replaced
    # it with the shared door, so this function and get_frequency_content
    # cannot drift apart on it the way they had on the NaN check (#28).
    validate_non_empty(ts.data)
    validate_sampling_freq(ts.freq)

    data = ts.data.copy()

    validate_finite_data(data)

    if demean:
        data_mean = data.mean()
        if not np.isfinite(data_mean):
            raise ValueError("Cannot compute mean: data contains invalid values")
        data -= data_mean
    
    n = len(data)
    
    # Check for degenerate cases
    if n < 2:
        raise ValueError("Time series too short for FFT analysis (minimum 2 points required)")
    
    # Check if data is effectively constant (after demeaning)
    data_std = np.std(data)
    if data_std < 1e-15:  # Effectively zero variance
        # For constant data, return zeros except for DC component
        freqs = np.fft.fftfreq(n, d=1/ts.freq)[:n//2]
        power = np.zeros_like(freqs)
        if not demean and len(freqs) > 0:
            power[0] = np.mean(ts.data)**2  # DC power for constant signal
    else:
        # Normal FFT computation
        fft_result = np.fft.fft(data)
        fft_freqs = np.fft.fftfreq(n, d=1/ts.freq)

        power = np.abs(fft_result)**2 / n
        half_n = n // 2
        freqs = fft_freqs[:half_n]
        power = power[:half_n]
    
    # Handle max_rate parameter
    if max_rate is not None and not np.isnan(max_rate):
        if max_rate <= 0:
            raise ValueError(f"Invalid max_rate: {max_rate} Hz")
        if max_rate > ts.freq/2:
            raise ValueError(f"max_rate ({max_rate} Hz) exceeds Nyquist frequency ({ts.freq/2} Hz)")
        idx = find_closest(max_rate, freqs).location
        freqs = freqs[:idx+1]  # Include the frequency at max_rate
        power = power[:idx+1]
    
    # Ensure we have non-empty arrays
    if len(freqs) == 0 or len(power) == 0:
        raise ValueError("FFT computation resulted in empty frequency or power arrays")
    
    # Handle power scaling
    if scale_power:
        power_sum = np.sum(power)
        if power_sum > 0:
            power = power / power_sum
        else:
            # If all power is zero, scaling doesn't change anything
            pass

    return freqs, power

def get_peak_freq(ts: Any, num_pks: int = 1, window: str = None,
                  min_freq: float = None, max_freq: float = None) -> Union[float, List[float]]:
    """
    Get the top peak frequencies of the time series using enhanced frequency analysis.

    Args:
        ts: Time series object with get_frequency_content method
        num_pks: Number of top peak frequencies to return
        window: Window function to apply ('hann', 'hamming', 'blackman', None)
        min_freq: Minimum frequency to consider (Hz, defaults to exclude DC component)
        max_freq: Maximum frequency to consider (Hz, defaults to Nyquist)

    Returns:
        Single peak frequency (float) if num_pks=1, otherwise list of peak frequencies

    Raises:
        ValueError: If the series is empty, if the sampling frequency is not
            usable, if the data is complex, or if it contains NaN or Inf. All
            are raised by get_frequency_content below, so this function
            carries no guard of its own.

    Examples:
        # Basic peak frequency (returns float, excludes DC)
        peak = get_peak_freq(ts)  # 25.3
        
        # Top 3 peaks with Hanning window (returns list)
        peaks = get_peak_freq(ts, num_pks=3, window='hann')  # [25.3, 10.1, 45.7]
        
        # Peak in frequency range with windowing (returns float)
        peak = get_peak_freq(ts, window='blackman', min_freq=1.0, max_freq=50.0)  # 15.2
        
        # Include DC component explicitly
        peak_with_dc = get_peak_freq(ts, min_freq=0.0)  # May return 0.0 if DC is strongest
    """
    # Use enhanced get_frequency_content method instead of compute_fft_power
    freq, power = ts.get_frequency_content(window=window)
    
    # Apply frequency range filtering
    if max_freq is None:
        max_freq = np.max(freq)  # Use Nyquist frequency as default
    
    # Default to excluding DC component (0 Hz) for typical peak frequency analysis
    # This maintains backward compatibility with the expected behavior
    if min_freq is None:
        # Find the smallest non-zero frequency to exclude DC
        non_zero_freqs = freq[freq > 0]
        min_freq = non_zero_freqs[0] if len(non_zero_freqs) > 0 else 0.0
    
    # Create frequency mask for the specified range
    freq_mask = (freq >= min_freq) & (freq <= max_freq)
    freq_filtered = freq[freq_mask]
    power_filtered = power[freq_mask]
    
    if len(freq_filtered) == 0:
        raise ValueError(f"No frequencies found in range [{min_freq}, {max_freq}] Hz")
    
    # Find peak indices in the filtered data
    peak_indices = np.argsort(power_filtered)[-num_pks:][::-1]  # Get indices of top num_pks peaks
    
    # Return the actual frequencies corresponding to these peaks
    peak_frequencies = freq_filtered[peak_indices].tolist()
    
    # Return single value for backward compatibility when num_pks=1
    if num_pks == 1:
        return peak_frequencies[0]
    else:
        return peak_frequencies

def relative_band_power(
    ts: Any,  # TODO: Replace with proper baseTs type
    low_freq: float = 0.01,
    high_freq: float = 0.1,
    ratio: str = 'power',
    window: Optional[str] = None,
    details: bool = False
) -> Union[float, BandPowerResult]:
    """
    Compute the relative power (or amplitude) in a frequency band.

    This is the quantity behind fractional amplitude of low-frequency
    fluctuations (fALFF) and its EEG/HRV cousin, relative band power.

    The band defaults to 0.01-0.1 Hz, a common low-frequency band for
    resting-state fMRI and other slow physiological fluctuations. It is one
    convention among several: Zou et al. (2008) computed fALFF over
    0.01-0.08 Hz, and the HRV literature's LF band is 0.04-0.15 Hz. Pass
    both edges to measure a different band. The default changes nothing about the
    constraints below: the upper edge still has to sit at or below Nyquist,
    so a series sampled below 0.2 Hz raises the same ValueError an explicit
    (0.01, 0.1) would, and at least one FFT bin still has to fall inside
    the band.

    The two conventions answer different questions and are not
    interchangeable:

    - ratio='power' sums |X(f)|^2 and yields the *fraction of the signal's
      variance* in the band. Parseval makes this exact and comparable across
      recordings with different sampling rates.
    - ratio='amplitude' sums |X(f)| and reproduces classic fALFF (Zou et al.,
      2008). Because the square root compresses peaks, its denominator scales
      with the number of noise bins, so values are not comparable across
      acquisitions with different bandwidth.

    The DC (0 Hz) bin is always excluded from both the numerator and the
    denominator. get_frequency_content() does not demean, so on a signal with
    a non-zero mean the DC bin holds the overwhelming majority of raw power
    and would otherwise drive the ratio toward zero. Excluding it makes the
    result robust to whether the caller detrended upstream.

    Preconditions:
        - Detrend first for meaningful results on trending data:
          ts.detrend('linear'). This function deliberately does not detrend on
          your behalf - that belongs in your processing pipeline.
        - Resample to a uniform grid first if the series is irregular, since
          ts.freq is an effective sampling frequency.
        - The series must be long enough to resolve the band. Frequency
          resolution is freq / n_samples, i.e. 1 / duration, so a 0.01 Hz
          lower edge needs at least 100 s of data for a single bin.

    Args:
        ts: Time series object with a get_frequency_content method
        low_freq: Lower band edge in Hz (inclusive). Defaults to 0.01.
        high_freq: Upper band edge in Hz (inclusive). Defaults to 0.1.
        ratio: 'power' (variance fraction, default) or 'amplitude' (fALFF)
        window: Window function passed through to get_frequency_content
            ('hann', 'hamming', 'blackman', or None)
        details: If True, return a BandPowerResult with the full breakdown
            instead of a bare float

    Returns:
        The relative band power as a float, or a BandPowerResult if
        details=True

    Raises:
        ValueError: If the band is invalid, exceeds Nyquist, is narrower than
            the frequency resolution, if the series is empty, if the data is
            complex or contains NaN/Inf, or if the signal has no spectral
            power outside DC

    Examples:
        # Fraction of variance in the default 0.01-0.1 Hz band
        ts.detrend('linear').relative_band_power()

        # A different band, here the HRV low-frequency band
        ts.relative_band_power(0.04, 0.15)

        # Classic fALFF convention (or use falff(), which defaults to it)
        ts.relative_band_power(ratio='amplitude')

        # Full breakdown, including the white-noise null to compare against
        res = ts.relative_band_power(details=True)
        print(res.ratio, res.bin_fraction)
    """
    if ratio not in ('power', 'amplitude'):
        raise ValueError(
            f"Unknown ratio convention: {ratio!r}. Use 'power' for the "
            f"variance fraction or 'amplitude' for classic fALFF."
        )

    if low_freq < 0:
        raise ValueError(f"low_freq cannot be negative: {low_freq} Hz")

    if low_freq >= high_freq:
        raise ValueError(
            f"low_freq ({low_freq} Hz) must be less than high_freq "
            f"({high_freq} Hz)"
        )

    # ts.get_frequency_content() below validates both the rate and the data,
    # raising the same ValueErrors, so this function carries no check of its
    # own. Two of the checks that follow are NaN-blind - `high_freq > nan` is
    # False, and np.std of data containing NaN is NaN, so `< 1e-15` is False
    # too - but that only means they decline to reject; the error still
    # arrives, with the same message, from the call at the end of this
    # function. A local *copy* of either check is what let the four spectral
    # entry points drift apart in the first place (issue #28).
    nyquist = ts.freq / 2
    if high_freq > nyquist:
        raise ValueError(
            f"high_freq ({high_freq} Hz) exceeds Nyquist frequency "
            f"({nyquist} Hz)"
        )

    # Called here, not left to get_frequency_content, because the cast on the
    # next line runs first and raises TypeError of its own on an object array
    # of non-numbers - so the "all four raise the same ValueError" contract
    # held for NaN data but not for this dtype class. Calling the shared
    # helper is not the drifting local copy the comment above warns about:
    # there is one definition, so it cannot say something different.
    validate_finite_data(ts.values)
    # And this one for the same reason, one line further on: np.std of an
    # empty array warns "Degrees of freedom <= 0" before get_frequency_content
    # would have raised, so the diagnosis arrived with a RuntimeWarning
    # attached (issue #62).
    validate_non_empty(ts.values)
    data = np.asarray(ts.values, dtype=float)

    # Effectively constant data has no oscillatory content, so any ratio would
    # be pure floating-point roundoff. Same threshold used by compute_fft_power.
    if np.std(data) < 1e-15:
        raise ValueError(
            "Signal has no spectral power outside the DC component "
            "(the data is effectively constant)."
        )

    freqs, power = ts.get_frequency_content(window=window)

    # Always drop DC - see the note in the docstring
    non_dc = freqs > 0
    freqs, power = freqs[non_dc], power[non_dc]

    n_total_bins = len(freqs)
    if n_total_bins == 0:
        raise ValueError(
            "Spectrum contains no non-DC frequency bins; the series is too "
            "short for band power analysis."
        )

    freq_resolution = ts.freq / len(data)

    band_mask = (freqs >= low_freq) & (freqs <= high_freq)
    n_band_bins = int(np.count_nonzero(band_mask))
    if n_band_bins == 0:
        needed = 1.0 / max(high_freq - low_freq, np.finfo(float).tiny)
        raise ValueError(
            f"No frequency bins fall in [{low_freq}, {high_freq}] Hz. The "
            f"frequency resolution is {freq_resolution:.6g} Hz "
            f"({len(data)} samples at {ts.freq} Hz); resolving a band this "
            f"narrow needs at least {needed:.6g} s of data."
        )

    spectrum = power if ratio == 'power' else np.sqrt(power)

    total_sum = float(np.sum(spectrum))
    if total_sum <= 0:
        raise ValueError(
            "Signal has no spectral power outside the DC component "
            "(the data is effectively constant)."
        )

    band_sum = float(np.sum(spectrum[band_mask]))
    band_ratio = float(band_sum / total_sum)

    if not details:
        return band_ratio

    return BandPowerResult(
        ratio=band_ratio,
        ratio_type=ratio,
        band_sum=band_sum,
        total_sum=total_sum,
        low_freq=low_freq,
        high_freq=high_freq,
        n_band_bins=n_band_bins,
        n_total_bins=n_total_bins,
        bin_fraction=float(n_band_bins / n_total_bins),
        freq_resolution=float(freq_resolution),
        nyquist=float(nyquist),
    )


def falff(
    ts: Any,  # TODO: Replace with proper baseTs type
    low_freq: float = 0.01,
    high_freq: float = 0.1,
    ratio: str = 'amplitude',
    **kwargs: Any
) -> Union[float, BandPowerResult]:
    """
    Fractional amplitude of low-frequency fluctuations (fALFF).

    Convenience wrapper around relative_band_power() with the convention
    from Zou et al. (2008), "An improved approach to detection of amplitude
    of low-frequency fluctuation (ALFF) for resting-state fMRI", J Neurosci
    Methods 172(1):137-141. Both functions default to the same 0.01-0.1 Hz
    band, which is wider than the 0.01-0.08 Hz that paper used; pass
    (0.01, 0.08) to reproduce it.

    What differs is the convention, and the split is deliberate:
    relative_band_power() defaults to ratio='power' because the variance
    fraction is the better-behaved general-purpose measure, while this
    function defaults to ratio='amplitude' so it reproduces published fALFF
    values.

    Caveat: because the amplitude convention's denominator grows with the
    number of noise bins, fALFF values are not comparable across acquisitions
    with different sampling rates or bandwidth. Use ratio='power' if you need
    that comparability.

    Args:
        ts: Time series object with a get_frequency_content method
        low_freq: Lower band edge in Hz. Defaults to 0.01.
        high_freq: Upper band edge in Hz. Defaults to 0.1.
        ratio: 'amplitude' (default, classic fALFF) or 'power'
        **kwargs: Passed through to relative_band_power (window, details)

    Returns:
        The fALFF value as a float, or a BandPowerResult if details=True

    Raises:
        ValueError: Everything relative_band_power raises, including an
            empty series; this is a thin wrapper over it.

    Examples:
        # Classic fALFF on a detrended signal
        ts.detrend('linear').falff()

        # The band Zou et al. (2008) used
        ts.falff(0.01, 0.08)
    """
    return relative_band_power(ts, low_freq, high_freq, ratio=ratio, **kwargs)


def get_peaks(
    ts: Any,
    min_dist_secs: float = 1.0,
    min_height: Optional[float] = None
) -> List[int]:
    """
    Find peaks in the time series.

    Args:
        ts: Time series object with data attribute
        min_dist_secs: Minimum distance between peaks in seconds
        min_height: Minimum height of peaks

    Returns:
        List of peak indices

    Raises:
        ValueError: If the sampling frequency is NaN or infinite
    """
    # Deliberately narrower than validate_sampling_freq: only non-finite
    # rates are rejected, not `freq <= 0`. int(min_dist_secs * 0.0) is 0 and
    # the max(25, ...) floor absorbs it, so a zero or negative rate provably
    # produced correct peaks before and must keep doing so - rejecting it
    # here would be an API break for input that worked. NaN is different: it
    # reaches int() and dies with "cannot convert float NaN to integer",
    # naming the conversion rather than the degenerate time base.
    #
    # Converted, not isinstance-gated: np.float32/np.float16/np.longdouble are
    # not float subclasses, so an allowlist silently skipped exactly the numpy
    # scalar types a freq is most likely to arrive as, letting the raw
    # conversion error through - and OverflowError, for a float32 infinity.
    try:
        rate = float(ts.freq)
    except (TypeError, ValueError, OverflowError):
        rate = validate_sampling_freq(ts.freq)   # always raises here
    if not math.isfinite(rate):
        validate_sampling_freq(ts.freq)

    min_samples = max(25, int(min_dist_secs * rate))
    peaks, _ = find_peaks(ts.data, distance=min_samples, height=min_height)
    return peaks.tolist()

def find_closest(val: float, in_list: Union[List[float], NDArray[np.float64]]) -> ClosestMatch:
    """
    Find the closest value in a list/array to a target value.

    Args:
        val: Target value to find
        in_list: List or array of values to search in

    Returns:
        ClosestMatch object containing the closest value and its location
    """
    in_array = np.asarray(in_list)
    loc = np.abs(in_array - val).argmin()
    return ClosestMatch(value=in_array[loc], location=loc, abs_err=np.abs(val - in_array[loc]), target=val)

def find_closest_time(
    ts: Any,
    sec: float,
    round_to: int = -1
) -> ClosestMatch:
    """
    Find the closest time in a time series to a target time.

    Args:
        ts: Time series object with times attribute
        sec: Target time in seconds
        round_to: Number of decimal places to round to (-1 for no rounding)

    Returns:
        ClosestMatch object with target time, closest value, and error
    """
    loc = np.abs(ts.times - sec).argmin()
    val = ts.times[loc]
    abs_err = np.abs(sec - val)
    
    if round_to > -1:
        val = np.round(val, round_to)
        abs_err = np.round(abs_err, round_to)
    
    return ClosestMatch(
        target=sec,
        value=val,
        location=loc,
        abs_err=abs_err
    )

LAG_UNITS = ("seconds", "index")

# The largest magnitude at which every integer is exactly a float64.
EXACT_INT_LIMIT = 2 ** 53


def _validate_lag_unit(lag_unit: Any) -> None:
    """Refuse any lag unit but the two documented ones (issue #54).

    `get_lags` used to dispatch on `lag_unit == 'seconds'` with no other
    check, so `'second'`, `'Seconds'` and `'sec'` all fell through to index
    mode - a factor-of-the-sampling-rate change in what the lag means, with
    the plot then correctly labelled for the wrong reading. `validate_lag`
    had the same assumption in its else-branch. One rule, shared, so the two
    cannot disagree.

    Case is not folded: rejecting is safer than guessing when the two
    readings differ by 100x, and the accepted set is two words long.

    Args:
        lag_unit: The unit as the caller passed it

    Raises:
        ValidationError: If it is not exactly 'seconds' or 'index'
    """
    if not isinstance(lag_unit, str) or lag_unit not in LAG_UNITS:
        raise ValidationError(
            f"lag_unit must be 'seconds' or 'index', not {_describe(lag_unit)}."
        )


def validate_lag(
    lag: Union[int, float],
    lag_idx: int,
    lag_unit: str,
    freq: float,
    n_samples: Optional[int] = None,
) -> None:
    """
    Validate lag parameters.

    Args:
        lag: Lag value
        lag_idx: Lag index
        lag_unit: Unit of lag ('seconds' or 'index')
        freq: Sampling frequency
        n_samples: Length of the series the lag will be applied to. When
            given, a lag of that many samples or more is refused (issue #53):
            `np.roll` wraps modulo the length, so such a lag blanked every
            sample and returned an empty result labelled with a lag longer
            than the whole series. Omitted, the bound is not applied, which
            is what every caller before #53 got.

    Raises:
        ValidationError: If the unit is not 'seconds' or 'index', if the
            index is not a positive integer, or if it does not fit the series
    """
    _validate_lag_unit(lag_unit)
    if not isinstance(lag_idx, int) or lag_idx <= 0:
        if lag_unit == "seconds":
            raise ValidationError(
                f"lag_idx must be a positive nonzero integer. "
                f"In seconds mode, got lag={lag}s, and freq={freq}, "
                f"which results in lag_idx={lag_idx}. Is your frequency correct?"
            )
        else:
            floatmsg = "Did you mean to use seconds mode? " if isinstance(lag, float) else ""
            raise ValidationError(
                f"lag must be a positive nonzero integer. "
                f"In index mode, got lag={lag}. {floatmsg}"
            )
    if n_samples is not None and lag_idx >= n_samples:
        # Strictly less: lag_idx == n_samples blanks every sample, and
        # n_samples - 1 leaves one. A one-sample result is degenerate but
        # honest - it is the shift that was asked for, and its length is
        # visible - so the line is drawn at "nothing survives".
        if lag_unit == "seconds":
            raise ValidationError(
                f"lag must be shorter than the series. In seconds mode, got "
                f"lag={lag}s at freq={freq} Hz, which is lag_idx={lag_idx} "
                f"samples, but the series has only {n_samples} samples."
            )
        raise ValidationError(
            f"lag must be shorter than the series. In index mode, got "
            f"lag={lag} samples, but the series has only {n_samples} samples."
        )

def _describe(value: Any) -> str:
    """Render a rejected value for an error message, without pasting it whole.

    `{value!r}` on a large object builds an unusably long exception - a
    200k-element list produced a 1.4 MB message, and 10**400 a 400-digit one -
    which then lands in logs and tracebacks. The type and a prefix are what
    identify the mistake; the contents are not.

    Args:
        value: The rejected value

    Returns:
        Its repr, truncated with the type name appended when it is long
    """
    text = repr(value)
    if len(text) <= 60:
        return text
    return f"{text[:57]}... ({type(value).__name__})"

def _coerce_lag(lag: Any) -> float:
    """Convert a lag to a float, or say which argument is wrong.

    validate_lag is the diagnosis for a bad lag, but shift_timeseries calls it
    *after* get_lags has already converted, so an unconvertible lag died in the
    conversion - `int(nan * rate)`, `"0.5" / rate` - naming the operation
    rather than the argument. This runs first so the caller is told what is
    actually wrong, and runs for both modes so they cannot disagree about the
    same bad value.

    Non-finite values are deliberately allowed through: division handles them,
    so an index-mode NaN reaches validate_lag, which diagnoses it better
    because it knows index mode is what the caller asked for. time_to_idx adds
    its own finiteness check, since int() has no such tolerance.

    Coerced via float() rather than gated on numbers.Real, matching
    validate_sampling_freq: a registrable virtual subclass can satisfy an
    isinstance test and still have no working __float__. This narrows what the
    conversion takes, deliberately - an object with a working __mul__ and no
    __float__ used to multiply through and now does not, which is the point,
    since #30 was about validating one value and computing with another.
    0-d arrays and Decimal still convert.

    str and bytes are both excluded first, and both are load-bearing:
    float("0.5") and float(b"0.5") each return 0.5, so without the exclusion
    this would *widen* what the conversion accepts, where today either raises.
    bytes is easy to mistake for redundant here - float() refuses most
    non-numerics, but not that one.

    bool is deliberately not excluded: float(True) is 1.0 and `True * rate`
    already produced exactly that, so rejecting it would break input that
    worked.

    Args:
        lag: The lag to convert, in seconds or in samples

    Returns:
        The lag as a float, when it is convertible

    Raises:
        ValidationError: If the lag is not a real scalar, or is a real number
            too large for a float
    """
    if isinstance(lag, (str, bytes)):
        raise ValidationError(f"lag must be a real number, not {_describe(lag)}.")
    try:
        return float(lag)
    except OverflowError as exc:
        # Separated from the other two: 10**400 *is* a real number, it is just
        # outside float's range. Folding it into the "not a real number"
        # message tells the caller something false about their value and sends
        # them looking for a type error they do not have.
        raise ValidationError(
            f"lag is too large to convert to a float: {_describe(lag)}."
        ) from exc
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            f"lag must be a real number, not {_describe(lag)}."
        ) from exc

def idx_to_time(lag_idx: int, freq: float) -> float:
    """
    Convert an index to a time value.

    Args:
        lag_idx: Index to convert
        freq: Sampling frequency

    Returns:
        Time value in seconds

    Raises:
        ValueError: If the sampling frequency is not a usable rate (issue #32).
            A degenerate time base derives to NaN, which propagated silently
            into the returned seconds; a zero rate raised ZeroDivisionError,
            naming the division rather than the rate.
        ValidationError: If the lag is not a real scalar

    Note:
        A non-finite index is *not* rejected here. It divides to NaN and
        reaches validate_lag, whose message names index mode and the integer
        rule - a better diagnosis than this function can give.
    """
    # Sequenced rather than written as one expression: `_coerce_lag(lag) /
    # validate_sampling_freq(freq)` evaluates the left operand first, so a call
    # with both arguments bad would blame the lag here and the rate in
    # time_to_idx - the same mistake diagnosed two ways depending on the unit.
    rate = validate_sampling_freq(freq)
    samples = _coerce_lag(lag_idx)
    seconds = samples / rate

    if math.isfinite(samples) and not math.isfinite(seconds):
        # Checking the operands is not the same as checking the result: both
        # can pass their own guard and still divide to inf. Nothing downstream
        # catches that - validate_lag only asks whether the index is a positive
        # int - so an infinite lag_secs rode out into the returned dict and the
        # plot title. Guarded on a finite *input* so a NaN index still reaches
        # validate_lag, which names index mode and the integer rule.
        raise ValidationError(
            f"lag index {lag_idx} at {freq} Hz has no finite duration: the "
            f"conversion overflows."
        )
    return seconds

def time_to_idx(lag_secs: float, freq: float) -> int:
    """
    Convert a time value to the nearest whole number of samples.

    Args:
        lag_secs: Time in seconds
        freq: Sampling frequency

    Returns:
        Index value: `lag_secs * freq` rounded to the nearest integer, with
        an exact half going to the even neighbour (Python's `round`)

    Raises:
        ValueError: If the sampling frequency is not a usable rate (issue #32)
        ValidationError: If the lag is not a real scalar, or is NaN or infinite

    Note:
        Rounded rather than truncated (issue #51). A derived rate is rarely
        exact - a nominal 100 Hz series derives to 99.99999999999999 - so
        `int(0.5 * rate)` was 49 for a caller who asked for half a second,
        in 7% of a 5703-case sweep. The residue is ~1e-14 relative, far
        inside half a sample, so rounding lands on the sample meant every
        time. A lag that falls exactly between two samples has no nearest
        one; either neighbour is as honest as the other, and `get_lags`
        reports whichever was taken.

        Both values are coerced by their validators and the *coerced* values
        are what get multiplied. Validating one object and computing with
        another is how a value validated as 1.0 got filtered as something else
        in issue #30.
    """
    rate = validate_sampling_freq(freq)
    secs = _coerce_lag(lag_secs)
    if not math.isfinite(secs):
        # Unlike the division in idx_to_time, int() cannot carry a NaN or an
        # infinity forward to validate_lag - it raises ValueError and
        # OverflowError respectively, naming neither the lag nor the mode.
        #
        # Redundant for *coverage* and kept for the *message*: the rate is
        # finite and positive by now - guaranteed by validate_sampling_freq's
        # `not (value > 0) or not math.isfinite(value)`, not by anything here -
        # so a non-finite lag cannot produce a finite product either, and the
        # check below would catch every case this one does. It would report an overflow, though, which is the
        # wrong diagnosis for an argument that arrived as NaN. Both messages
        # are pinned by tests that match the distinguishing wording - matching
        # a substring common to both is how this check went undetected as
        # deletable through a whole mutation round.
        raise ValidationError(
            f"lag must be a finite number of seconds. Got lag={lag_secs}, "
            f"which has no corresponding index."
        )

    samples = secs * rate
    if not math.isfinite(samples):
        # Two individually finite values can still multiply to inf, and int()
        # then leaks the bare OverflowError this function promises not to
        # emit. The operands were checked; the product was not.
        raise ValidationError(
            f"lag={lag_secs} at {freq} Hz has no finite index: the conversion "
            f"overflows."
        )
    return round(samples)

def get_lags(
    lag: Union[int, float],
    lag_unit: str,
    freq: float
) -> Tuple[float, int]:
    """
    Get lag values in both seconds and indices.

    Args:
        lag: Lag value
        lag_unit: Unit of lag ('seconds' or 'index')
        freq: Sampling frequency

    Returns:
        Tuple of (lag_seconds, lag_index). In seconds mode the seconds are
        those of the *index that will be applied* - `lag_index / freq` - not
        the caller's argument echoed back (issue #51). A 0.3 s lag at 7 Hz is
        2.1 samples: 2 are applied, and 2/7 s is what this reports, so the
        two halves agree by construction whatever the rounding rule did.

    Raises:
        ValidationError: If the unit is not 'seconds' or 'index' (issue #54),
            or the lag cannot be converted
        ValueError: If the sampling frequency is not a usable rate
    """
    # The unit is judged first: without it there is no way to know which
    # conversion the lag was meant for, so nothing about the lag or the rate
    # can be diagnosed in the caller's terms yet.
    _validate_lag_unit(lag_unit)
    if lag_unit == 'seconds':
        lag_idx = time_to_idx(lag, freq)
        return idx_to_time(lag_idx, freq), lag_idx
    return idx_to_time(lag, freq), lag

def _blank_head(arr: NDArray[Any], k: int) -> NDArray[Any]:
    """Return a copy of `arr` whose first `k` entries are the dtype's missing value.

    `lagged[:k] = np.nan` was the whole of this before #52, and it raised
    `ValueError: cannot convert float NaN to integer` on an int64 series -
    the identical message #32 is named for, from a different cause: the rate
    was fine, the container could not hold the sentinel. A datetime64 index
    died on `Could not convert object to NumPy datetime` the same way.

    The rule, by dtype kind: a dtype with a missing value of its own gets it
    - NaN for float and complex, NaT for datetime and timedelta, NaN into an
    object slot; a *numeric* dtype with none (integer, unsigned, bool) is
    widened to float64 first, an integer one only while every value is
    within +/-2**53 so the widening is exact; and a non-numeric dtype with
    none (bytes, str, void) is refused, because "widen" would mean parsing,
    and a bytes array whose entries happen to read as numbers would flip
    dtype silently.
    Integer widening is what `pd.Series([1, 2, 3]).shift(1)` does; bool
    deliberately diverges from pandas, which shifts a bool Series to object,
    because a float sentinel is what this function's contract promises.
    `astype(float)` is deliberately not applied to the datetime kinds: it
    reinterprets the int64 storage and turns NaT into -9.2e18.

    Args:
        arr: The array to blank, not modified
        k: How many leading entries to blank

    Returns:
        A new array of the same length

    Raises:
        ValidationError: If the dtype has no missing value and is not numeric
    """
    kind = arr.dtype.kind
    if kind in "mM":
        out = arr.copy()
        out[:k] = np.array("NaT", dtype=arr.dtype)
        return out
    if kind in "fcO":
        out = arr.copy()
    elif kind == "b":
        out = arr.astype(float)
    elif kind in "iu":
        # Widening is only honest while it is exact. float64 holds every
        # integer up to 2**53; past that, values the shift never touched
        # come back changed, and two distinct samples can land on one
        # float (review round 2, codex). On main this raised, so returning
        # a quietly imprecise array would trade a loud failure for the
        # confident-wrong-number class this module guards against.
        if arr.size and (arr.min() < -EXACT_INT_LIMIT or arr.max() > EXACT_INT_LIMIT):
            raise ValidationError(
                f"cannot blank the shifted-out samples of a {arr.dtype} array "
                f"whose values exceed 2**53: widening to float64 would change "
                f"them. Use drop_nan=True, which drops the shifted-out samples "
                f"and keeps the dtype."
            )
        out = arr.astype(float)
    else:
        raise ValidationError(
            f"cannot blank the shifted-out samples of a {arr.dtype} array: "
            f"the dtype has no missing value and is not numeric."
        )
    out[:k] = np.nan
    return out

def shift_timeseries(
    ts: Any,
    lag: Union[int, float] = 0,
    lag_unit: str = "index",
    drop_nan: bool = True
) -> Dict[str, Any]:
    """
    Shift a time series by a lag value.

    Args:
        ts: Time series object with data and times attributes
        lag: Lag value
        lag_unit: Unit of lag ('seconds' or 'index')
        drop_nan: Whether to drop the samples the shift moves out of range.
            True returns the `len - lag_idx` samples that survive, in the
            series' own dtype. False returns the full length with the first
            `lag_idx` entries blanked - NaN, or NaT for a timestamp index -
            which widens an integer or bool array to float64, as pandas'
            `shift` does for integers (issue #52).

    Returns:
        Dictionary containing lagged data, times, and lag information.
        `lag_secs` is the duration of `lag_idx` samples at the series' rate,
        so it describes the shift performed (issue #51).

    Raises:
        ValidationError: If the unit is unknown (#54), the lag is not a
            positive whole number of samples, or the lag is not shorter than
            the series (#53) - a longer one wrapped around and blanked every
            sample, returning an empty result labelled with a lag longer
            than the whole series
        ValueError: If the sampling frequency is not a usable rate (#32)
    """
    data = ts.data
    times = ts.times
    freq = ts.freq

    lag_secs, lag_idx = get_lags(lag, lag_unit, freq)
    # len(data) and len(times) are the same number for a Series, whose index
    # and values cannot differ in length; data is named as the one bounded.
    validate_lag(lag, lag_idx, lag_unit, freq, n_samples=len(data))

    if drop_nan:
        # The blanked head is sliced off anyway, so no sentinel is needed and
        # the dtype survives. Copied: np.roll always returned a fresh array,
        # and a view would let a caller edit the series through the result.
        lagged_data = data[:len(data) - lag_idx].copy()
        lagged_times = times[:len(times) - lag_idx].copy()
    else:
        lagged_data = _blank_head(np.roll(data, lag_idx), lag_idx)
        lagged_times = _blank_head(np.roll(times, lag_idx), lag_idx)

    return {
        'lagged_data': lagged_data,
        'lagged_timeseries': lagged_times,
        'lag_secs': lag_secs,
        'lag_idx': lag_idx
    }