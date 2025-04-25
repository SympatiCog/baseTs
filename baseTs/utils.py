# -*- coding: utf-8 -*-
"""
Created on Oct 19 2024
@author: stan@sympaticog.com
"""

import numpy as np
from scipy.signal import find_peaks
from typing import Union, Dict, Tuple, List, Any

def compute_fft_power(ts,
                      demean: bool = True,
                      scale_power: bool = True,
                      max_rate: float = np.nan) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the power of a baseTs signal using FFT.
    """
    data = ts.data.copy()
    if demean:
        data -= data.mean()
    
    # Compute the FFT
    n = len(data)
    fft_result = np.fft.fft(data)
    fft_freqs = np.fft.fftfreq(n, d=1/ts.freq)

    # Compute power spectrum (magnitude squared of the FFT)
    power = np.abs(fft_result)**2 / n  # Normalize by number of samples

    # Since FFT output is symmetric, we take the first half for plotting
    half_n = n // 2
    freqs = fft_freqs[:half_n]
    power = power[:half_n]
    
    if not np.isnan(max_rate):
        idx = find_closest(max_rate, freqs)["location"]
    else:
        idx = len(freqs)  # Use full range if max_rate is not specified

    freqs = freqs[:idx]
    power = power[:idx]
    
    if scale_power:
        power /= np.sum(power)  # Normalize power spectrum

    return freqs, power

def get_peak_freq(ts) -> float:
    """
    Get the peak frequency of the timeseries.
    """
    freq, power = ts.compute_fft_power()
    pk_freq = freq[np.where(power==power.max())][0]
    return pk_freq

def get_peaks(ts, min_dist_secs: float = 1.0, min_height: float = None) -> List[int]:
    """
    Get the peaks in the timeseries.
    """
    # min_samples = int(min_dist_secs * ts.freq)
    min_samples = 25
    peaks = find_peaks(ts.data, distance=min_samples, height=min_height)
    return peaks[0]

def find_closest(val, in_list) -> Dict[str, Any]:
    """
    parameters:
        val:     target numeric value to find in list/array
        in_list: a list/array of numeric values
    returns:
        closest: dict
            'value':    value closest to target within in_list
            'location': index of that value within in_list
    """
    closest = {}
    loc = (np.abs(np.asarray(in_list) - val)).argmin()
    val = in_list[loc]
    closest["value"] = val
    closest["location"] = loc
    return closest

def find_closest_time(ts, sec: float, round_to: int = -1) -> Dict[str, Any]:
    """
    find the closest time in a baseTs object to a target time in seconds
    returns the closest time value and its index in the baseTs data
    parameters:
        ts:       baseTs object
        sec:      target time to find in list/array
        round_to: round float results to round_to places.
                  Note: -1 disables rounding 
    returns:
        closest: dict
            'target':   requested target time
            'value':    closest time value in the baseTs timeseries
            'location': index of the closest time value 
    """
    closest = {}
    loc = (np.abs(ts.times - sec)).argmin()
    val = ts.times[loc]
    abs_err = np.abs(sec-val)
    if round_to > -1:
        val = np.round(val, round_to)
        abs_err = np.round(abs_err, round_to)
        
    closest["target"] = sec
    closest["value"] = val
    closest["abs_err"] = abs_err
    closest["location"] = loc
    return closest

def validate_lag(lag, lag_idx, lag_unit, freq):
    """
    Validate the lag parameters.
    """
    # Ensure that the lag is valid (must be a positive integer)
    if not isinstance(lag_idx, int) or lag_idx <= 0:
        if lag_unit == "seconds":
            raise ValueError(f"lag_idx must be a positive nonzero integer.\n In seconds mode, got lag={lag}s, and freq={freq}, which results in lag_idx={lag_idx}.\nIs your frequency correct?")
        else:  # lag_unit == "index"
            if isinstance(lag, float):
                floatmsg = "Did you mean to use seconds mode? "
            else:
                floatmsg = ""
            raise ValueError(f"lag must be a positive nonzero integer.\n In index mode, got lag={lag}. {floatmsg}")

def idx_to_time(lag_idx, freq):
    """
    Convert an index to a time value.
    """
    sample_interval = 1/float(freq)  # Extract the number part of the frequency
    lag_secs = lag_idx * sample_interval  # Convert seconds to the nearest integer index lag
    return lag_secs

def time_to_idx(lag_secs, freq):
    """
    Convert a time value to an index.
    """
    sample_interval = 1/float(freq)  # Extract the number part of the frequency
    lag_idx = int(lag_secs / sample_interval)  # Convert seconds to the nearest integer index lag
    return lag_idx

def get_lags(lag, lag_unit, freq):
    """
    Get the lag values in both seconds and indices.
    """
    if lag_unit == 'seconds':
        lag_secs = lag
        lag_idx = time_to_idx(lag_secs, freq)
    else:
        lag_idx = lag
        lag_secs = idx_to_time(lag_idx, freq)
    return lag_secs, lag_idx

def shift_timeseries(ts,
                     lag: Union[int, float] = 0, 
                     lag_unit: str = "index",
                     drop_nan: bool = True) -> Dict[str, Any]:
    """
    Shift a timeseries by a lag value.
    """
    data = ts.data  
    freq = ts.freq 
    
    lag_secs, lag_idx = get_lags(lag, lag_unit, freq)
    validate_lag(lag, lag_idx, lag_unit, freq)

    # Shift the data manually by lagging the values
    lagged_data = np.roll(data, lag_idx)
    
    # Since the data has been "rolled", we'll manually set the first lag_idx 
    # elements to NaN to avoid using wrapped values
    lagged_data[:lag_idx] = np.nan
    lagged_times = np.roll(ts.times, lag_idx)
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