# -*- coding: utf-8 -*-
"""
Utility functions for time series analysis and signal processing.
Created on Oct 19 2024
@author: stan@sympaticog.com
"""

import math
from dataclasses import dataclass
from typing import Union, Dict, Tuple, List, Any, Optional #, TYPE_CHECKING
import numpy as np
from numpy.typing import NDArray
from scipy.signal import find_peaks

# if TYPE_CHECKING:
#     from .core import baseTs

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
    if isinstance(freq, (bool, np.bool_, str, bytes)):
        raise ValueError(
            f"Invalid sampling frequency: {freq!r} is not a real number."
        )
    # A size-1 ndarray is rejected rather than unwrapped: float() accepts it on
    # numpy 1.x (with a DeprecationWarning) and raises on 2.x, so allowing it
    # would make this guard's accept/reject set differ across the CI matrix -
    # the same version-sensitivity that produced the objs/input_objs bug in
    # PR #25. 0-d arrays convert identically on both majors and stay allowed.
    if isinstance(freq, np.ndarray) and freq.ndim > 0:
        raise ValueError(
            f"Invalid sampling frequency: {freq!r} is not a scalar. Pass a "
            f"single number, e.g. float(arr[0])."
        )
    try:
        value = float(freq)
    except (TypeError, ValueError, OverflowError) as exc:
        # OverflowError, not just TypeError/ValueError: float(10**400) raises
        # it, and it is neither - so it would escape both this contract and
        # the `except ValueError` translation in filters.
        raise ValueError(
            f"Invalid sampling frequency: {freq!r} is not a real number."
        ) from exc

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

def validate_finite_data(data: Any) -> None:
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

    Raises:
        ValueError: If the data contains NaN or Inf, or is not numeric
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

    # Anything not already numeric (object arrays, most often) is converted so
    # np.isfinite has a dtype it can loop over - it raises TypeError on object
    # arrays. Complex is left alone deliberately: np.isfinite handles it, and
    # a float cast would reject it outright, which would be a behaviour change
    # rather than the guard this function exists to add.
    if arr.dtype.kind not in "fc":
        try:
            arr = np.asarray(arr, dtype=float)
        except (TypeError, ValueError) as exc:
            # TypeError translated to ValueError to keep the promise this
            # docstring makes, the same way validate_sampling_freq does.
            # arr is unchanged here - the failed assignment above leaves the
            # original bound, so this reports the caller's dtype, not float.
            raise ValueError(
                f"Time series data is not numeric: dtype '{arr.dtype}' cannot "
                f"be interpreted as real numbers."
            ) from exc

    if not np.all(np.isfinite(arr)):
        raise ValueError(
            "Time series data contains NaN or Inf values. Fill gaps first, "
            "e.g. with interpolate_gaps()."
        )


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

class ValidationError(TimeSeriesError):
    """Exception raised for validation errors."""
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
        ValueError: If the time series is empty, has an invalid frequency, or
            contains NaN or Inf values
    """
    # Input validation
    if len(ts.data) == 0:
        raise ValueError("Time series data is empty")
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
        ValueError: If the sampling frequency is not usable, or if the data
            contains NaN or Inf. Both are raised by get_frequency_content
            below, so this function carries no guard of its own.

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
    low_freq: float,
    high_freq: float,
    ratio: str = 'power',
    window: Optional[str] = None,
    details: bool = False
) -> Union[float, BandPowerResult]:
    """
    Compute the relative power (or amplitude) in a frequency band.

    This is the quantity behind fractional amplitude of low-frequency
    fluctuations (fALFF, 0.01-0.1 Hz) and its EEG/HRV cousin, relative band
    power. See falff() for the classic parameterization.

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
        low_freq: Lower band edge in Hz (inclusive)
        high_freq: Upper band edge in Hz (inclusive)
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
            the frequency resolution, if the data contains NaN/Inf, or if the
            signal has no spectral power outside DC

    Examples:
        # Fraction of variance between 0.01 and 0.1 Hz
        ts.detrend('linear').relative_band_power(0.01, 0.1)

        # Classic fALFF convention
        ts.relative_band_power(0.01, 0.1, ratio='amplitude')

        # Full breakdown, including the white-noise null to compare against
        res = ts.relative_band_power(0.01, 0.1, details=True)
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
    # raising the same ValueErrors, so this function needs no guard of its
    # own. Two of the checks that follow are NaN-blind - `high_freq > nan` is
    # False, and np.std of data containing NaN is NaN, so `< 1e-15` is False
    # too - but that only means they decline to reject; the error still
    # arrives, with the same message, from the call at the end of this
    # function. A local copy of either guard is what let the four spectral
    # entry points drift apart in the first place (issue #28).
    nyquist = ts.freq / 2
    if high_freq > nyquist:
        raise ValueError(
            f"high_freq ({high_freq} Hz) exceeds Nyquist frequency "
            f"({nyquist} Hz)"
        )

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

    Convenience wrapper around relative_band_power() with the band and
    convention from Zou et al. (2008), "An improved approach to detection of
    amplitude of low-frequency fluctuation (ALFF) for resting-state fMRI",
    J Neurosci Methods 172(1):137-141.

    Note the deliberate default split: relative_band_power() defaults to
    ratio='power' because the variance fraction is the better-behaved
    general-purpose measure, while this function defaults to
    ratio='amplitude' so it reproduces published fALFF values.

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

    Examples:
        # Classic fALFF on a detrended signal
        ts.detrend('linear').falff()

        # Custom band
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

def validate_lag(lag: Union[int, float], lag_idx: int, lag_unit: str, freq: float) -> None:
    """
    Validate lag parameters.

    Args:
        lag: Lag value
        lag_idx: Lag index
        lag_unit: Unit of lag ('seconds' or 'index')
        freq: Sampling frequency

    Raises:
        ValidationError: If lag parameters are invalid
    """
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

def idx_to_time(lag_idx: int, freq: float) -> float:
    """
    Convert an index to a time value.

    Args:
        lag_idx: Index to convert
        freq: Sampling frequency

    Returns:
        Time value in seconds
    """
    return lag_idx / float(freq)

def time_to_idx(lag_secs: float, freq: float) -> int:
    """
    Convert a time value to an index.

    Args:
        lag_secs: Time in seconds
        freq: Sampling frequency

    Returns:
        Index value
    """
    return int(lag_secs * float(freq))

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
        Tuple of (lag_seconds, lag_index)
    """
    if lag_unit == 'seconds':
        return lag, time_to_idx(lag, freq)
    return idx_to_time(lag, freq), lag

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
        drop_nan: Whether to drop NaN values from the result

    Returns:
        Dictionary containing lagged data, times, and lag information
    """
    data = ts.data
    freq = ts.freq
    
    lag_secs, lag_idx = get_lags(lag, lag_unit, freq)
    validate_lag(lag, lag_idx, lag_unit, freq)

    lagged_data = np.roll(data, lag_idx)
    lagged_times = np.roll(ts.times, lag_idx)
    
    lagged_data[:lag_idx] = np.nan
    lagged_times[:lag_idx] = np.nan
    
    if drop_nan:
        lagged_data = lagged_data[lag_idx:]
        lagged_times = lagged_times[lag_idx:]

    return {
        'lagged_data': lagged_data,
        'lagged_timeseries': lagged_times,
        'lag_secs': lag_secs,
        'lag_idx': lag_idx
    }