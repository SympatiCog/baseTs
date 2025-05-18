# -*- coding: utf-8 -*-
"""
Utility functions for time series analysis and signal processing.
Created on Oct 19 2024
@author: stan@sympaticog.com
"""

from dataclasses import dataclass
from typing import Union, Dict, Tuple, List, Any, Optional
import numpy as np
from numpy.typing import NDArray
from scipy.signal import find_peaks

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
    target: Optional[float] = None
    abs_err: Optional[float] = None

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
    if demean:
        data -= data.mean()
    
    n = len(data)
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
    
    if scale_power:
        power /= np.sum(power)

    return freqs, power

def get_peak_freq(ts: Any) -> float:
    """
    Get the peak frequency of the time series.

    Args:
        ts: Time series object with data and freq attributes

    Returns:
        Peak frequency in Hz
    """
    freq, power = compute_fft_power(ts)
    return freq[np.argmax(power)]

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
    return ClosestMatch(value=in_array[loc], location=loc)

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