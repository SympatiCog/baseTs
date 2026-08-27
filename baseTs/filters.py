# -*- coding: utf-8 -*-
"""
Created on Oct 19 2024
@author: stan@sympaticog.com
"""

from __future__ import annotations
from typing import Union, Optional, Literal, TYPE_CHECKING
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, savgol_filter
from dataclasses import dataclass
from scipy import signal

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

class InvalidParameterError(FilterError):
    """Exception raised for invalid filter parameters."""
    pass

def validate_filter_params(data: ArrayLike, 
                          sampling_freq: float,
                          cutoff_freq: float,
                          order: int) -> None:
    """
    Validate filter parameters.
    
    Args:
        data: Input data array
        sampling_freq: Sampling frequency in Hz
        cutoff_freq: Cutoff frequency in Hz
        order: Filter order
        
    Raises:
        InvalidParameterError: If parameters are invalid
    """
    from .utils import validate_sampling_freq

    if not isinstance(data, (np.ndarray, list)):
        raise InvalidParameterError("Data must be a numpy array or list")

    # `sampling_freq <= 0` is False for NaN, so a degenerate time base used to
    # reach butter()/filtfilt() and come back as an all-NaN array with nothing
    # but a RuntimeWarning. Delegated so there is one definition of a usable
    # rate, but re-raised as InvalidParameterError to keep this module's
    # exception type for callers that catch it.
    try:
        validate_sampling_freq(sampling_freq)
    except ValueError as exc:
        raise InvalidParameterError(str(exc)) from exc

    # Also NaN-blind on its own; ordered after the rate check so a NaN rate
    # reports the degenerate time base rather than a confusing cutoff error.
    if not (cutoff_freq > 0) or cutoff_freq >= sampling_freq/2:
        raise InvalidParameterError("Cutoff frequency must be positive and less than Nyquist frequency")

    if order <= 0:
        raise InvalidParameterError("Filter order must be positive")

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

def notch_filter(data: ArrayLike, 
                 cutoff_hz: float, 
                 fs_hz: float, 
                 order: int = 5) -> np.ndarray:
    """
    Apply a symmetric notch filter to the input data.
    
    Args:
        data: Input data array
        cutoff_hz: Notch frequency in Hz
        fs_hz: Sampling frequency in Hz
        order: Filter order
        
    Returns:
        Filtered data array
        
    Raises:
        InvalidParameterError: If parameters are invalid
    """
    data = np.asarray(data)
    validate_filter_params(data, fs_hz, cutoff_hz, order)
    
    nyquist_rate = fs_hz / 2.0
    notch = cutoff_hz / nyquist_rate
    b, a = butter(order, [notch - 0.01, notch + 0.01], btype='bandstop')
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
    validate_filter_params(data, sampling_freq, highpass_freq, order)
    
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
    validate_filter_params(data, fs, cutoff, order)
    
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
    validate_filter_params(data, sample_Hz, max(hp_hz, lp_hz), 3)
    
    # Effective sampling rate of windowed analysis
    window_step = max(1, window_step - overlap)
    effective_fs = sample_Hz / window_step
    
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
