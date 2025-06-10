# -*- coding: utf-8 -*-
"""
Utility functions for time series analysis and signal processing.
Created on Oct 19 2024
@author: stan@sympaticog.com
"""

from dataclasses import dataclass
from typing import Union, Dict, Tuple, List, Any, Optional #, TYPE_CHECKING
import numpy as np
from numpy.typing import NDArray
from scipy.signal import find_peaks

# if TYPE_CHECKING:
#     from .core import baseTs

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
        ValueError: If the time series is empty or has invalid frequency
    """
    # Input validation
    if len(ts.data) == 0:
        raise ValueError("Time series data is empty")
    if ts.freq <= 0:
        raise ValueError(f"Invalid sampling frequency: {ts.freq} Hz")
    
    data = ts.data.copy()
    
    # Validate data doesn't contain NaN or Inf
    if np.any(np.isnan(data)) or np.any(np.isinf(data)):
        raise ValueError("Time series data contains NaN or Inf values")
    
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
    """
    min_samples = max(25, int(min_dist_secs * ts.freq))
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