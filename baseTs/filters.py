# -*- coding: utf-8 -*-
"""
Created on Oct 19 2024
@author: stan@sympaticog.com
"""

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, firwin, savgol_filter

zscale = lambda x: (x - x.mean()) / x.std()

def sg_filter(data: np.array, window_length: int = 11, polyorder: int = 2):
    """
    Apply a Savitzky-Golay filter to the input data.
    """
    # Adjust window length if necessary
    if window_length >= len(data):
        window_length = len(data) - 1 if len(data) % 2 == 0 else len(data)
    if polyorder >= window_length:
        polyorder = window_length - 1
    if window_length % 2 == 0:
        window_length += 1
        
    return savgol_filter(data, window_length, polyorder)


def highpass_filter(data: np.array, highpass_freq: float, sampling_freq: float, order: int = 5):
    """
    Apply a symmetric highpass filter to the input data.
    """
    nyquist_rate = sampling_freq / 2.0
    high = highpass_freq / nyquist_rate
    b, a = butter(order, high, btype='high')
    filtered_data = filtfilt(b, a, data)
    return filtered_data    

def lowpass_filter(data: np.array, cutoff: float, fs: float, order: int = 5):
    """
    Apply a symmetric lowpass filter to the input data.
    """
    nyq = 0.5 * fs  # Nyquist Frequency
    normal_cutoff = cutoff / nyq
    # Get the filter coefficients
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    filtered_data = filtfilt(b, a, data)
    return filtered_data

def bbf(data: np.array, highpass_freq: float, lowpass_freq: float, sampling_freq: float, order: int = 5):
    """
    Apply a symmetric bandpass Butterworth filter to the input data.

    Parameters:
    - data: Original data vector.
    - highpass_freq: High-pass cutoff frequency in Hz.
    - lowpass_freq: Low-pass cutoff frequency in Hz.
    - sampling_freq: Sampling frequency in Hz.
    - order: Order of the Butterworth filter.

    Returns:
    - filtered_data: The filtered data vector.
    """
    nyquist_rate = sampling_freq / 2.0

    # Convert cutoff frequencies to the Nyquist rate
    low = highpass_freq / nyquist_rate
    high = lowpass_freq / nyquist_rate

    # Design the Butterworth bandpass filter
    b, a = butter(order, [low, high], btype='band')

    # Apply the filter symmetrically (zero-phase filtering)
    filtered_data = filtfilt(b, a, data)

    return filtered_data

def bandpass_filter(data: np.array,
                    hp_hz: float = 0.01,
                    lp_hz: float = 0.1,
                    sample_Hz: float = 30,
                    window_step: int = 1,
                    overlap: int = 0,
                    reset_mean: bool = True):
    """
    Apply a symmetric bandpass filter to the input data.

    Parameters:
    - data: Original data vector.
    - hp_hz: High-pass cutoff frequency in Hz.
    - lp_hz: Low-pass cutoff frequency in Hz.
    - sample_Hz: Sampling frequency in Hz.
    - window_step: Step size for the windowed analysis.
    - overlap: Overlap size for the windowed analysis.
    - reset_mean: Boolean flag to reset the mean of the filtered data
      to the mean of the original data.

    Returns:
    - filtered: The filtered data vector.
    """
    from scipy import signal
    # Effective sampling rate of windowed analysis
    window_step -= overlap
    effective_fs = sample_Hz / window_step
    
    nyq = effective_fs / 2
    b, a = signal.butter(3, [hp_hz/nyq, lp_hz/nyq], btype='band')
    filtered = signal.filtfilt(b, a, data)

    if reset_mean == True:
        delta = data.mean() - filtered.mean()
        filtered += delta
    
    return(filtered)

def interpolate_missing_values(
    ts,
    interpolation_method: str = 'linear',
    order: int = 1,
    inplace: bool = False,
):
    """
    Interpolate missing values in the data.
    """
    data = ts.data
    time_index = ts.times
    
    cleaned_series = pd.Series(data, index=time_index)
    interpolated_series = cleaned_series.interpolate(method=interpolation_method, order=order)
    if interpolated_series.isnull().any():
        interpolated_series = interpolated_series.fillna(method='ffill')
        interpolated_series = interpolated_series.fillna(method='backfill')
        
    if inplace:
        ts.data = interpolated_series.values
        return ts
    else:
        res = ts.copy()
        res.data = interpolated_series.values
        return res