# -*- coding: utf-8 -*-
"""
Created on Oct 19 2024
@author: stan@sympaticog.com
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from typing import Union

# local imports
from .utils import shift_timeseries

zscale = lambda x: (x - x.mean()) / x.std()

# TODO: Consider using the general line series plot for this.
def qc_plot(ts,
            filt_data: np.array,
            filt_times: np.array = None,
            ax = None,
            title: str = None,
            xlabel: str = None,
            ylabel: str = None,
            show_lowess: bool = True,
            show: bool = False):
    """
    Plots a quality control plot for a timeseries.
    """
        
    if ax is None:
        ax = plt.gca()
    if title is None:
        title = f"QC Plot for {ts.signal_name}"
    if xlabel is None:
        xlabel = "Time"
    if ylabel is None:
        ylabel = ts.signal_name + " " + ts.last_process
    if filt_times is None:
        filt_times = ts.times

    ax.plot(ts.times, ts.data, label='Original')
    ax.plot(filt_times, filt_data, label='Filtered')
    if np.logical_and(ts.is_outlier_filtered, show_lowess):
        ax.plot(ts.times, ts.lowess_fit, label='Lowess Fit')
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True)
    ax.legend()
    
    if show:
        plt.show()
        
    return ax
    
        
def hist(ts,
         ax = None,
         title: str = None,
         xlabel: str = None,
         show: bool = False,
         bins: int = -1,
         kde: bool = False):
    """
    Plots a histogram of a timeseries.
    """
    if ax is None:
        ax = plt.gca()
    if xlabel is None:
        xlabel = ts.signal_name + " " + ts.last_process
    if bins == -1:
        bins = 'auto'
    if kde:
        density = True
        plotkind = "KDE"
        ylabel = "Density"
    else:
        density = False
        plotkind = "Histogram"
        ylabel = "Frequency"
    if title is None:
        title = f"{plotkind} of {ts.signal_name} {ts.last_process}"
        
    # Plot histogram
    ax.hist(ts.data, bins=bins, density=density, edgecolor='black', label='Histogram', alpha=0.6)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True)
    if kde:
        # Calculate KDE
        kde = gaussian_kde(ts.data)
        x = np.linspace(min(ts.data), max(ts.data), 150)
        y = kde(x)
        # Plot KDE
        ax.plot(x, y, label='KDE')
        ax.legend()
    if show:
        plt.show()
    
    return ax
 
def plot(ts,
         ax = None,
         title: str = None,
         xlabel: str = None,
         ylabel: str = None, 
         show: bool = True,
         lowess: bool = False,
         start_idx: int = 0,
         end_idx: int = -1): 
    """
    Plots a time series.
    """
    
    # Check that ts has baseTs-like structure
    if not hasattr(ts, 'data') or not hasattr(ts, 'times'):
        raise TypeError("ts must have data and times attributes")
    
    if ax is None:
        ax = plt.gca()
    if title is None:
        title = f"{ts.signal_name} by time."
    if xlabel is None:
        xlabel = "Time in seconds."
    if ylabel is None:
        ylabel = ts.signal_name + " " + ts.last_process
        
    ax.plot(ts.times[start_idx:end_idx], ts.data[start_idx:end_idx], label=ts.signal_name+ts.last_process)
    if lowess:
        ax.plot(ts.times[start_idx:end_idx], ts.lowess_fit[start_idx:end_idx], label='Lowess Fit')
        ax.legend()
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True)
    if show:
        plt.show()
    return ax

def plot_series(base_ts,
                series_list: list,
                ax = None,
                title: str = None,
                xlabel: str = None,
                ylabel: str = None, 
                show: bool = True,
                start_idx: int = 0,
                end_idx: int = -1): 
    """
    Plots multiple timeseries on the same plot.

    Args:
        base_ts (baseTs): The base timeseries object that defines the time axis.
        series_list (list): A list of timeseries objects to plot.
        ax (matplotlib.axes.Axes, optional): The axes on which to plot. Defaults to None.
        title (str, optional): The title of the plot. Defaults to None.
        xlabel (str, optional): The label for the x-axis. Defaults to None.
        ylabel (str, optional): The label for the y-axis. Defaults to None.
        show (bool, optional): Whether to display the plot. Defaults to True.

    Returns:
        matplotlib.axes.Axes: The axes with the plot.
    
    Note:
        The time axis is defined by the base_ts and shared between all series.
        Use the .signal_name and .last_process attributes of each timeseries object
        to label the series by default.
    """
    
    # Check that base_ts has baseTs-like structure
    if not hasattr(base_ts, 'data') or not hasattr(base_ts, 'times'):
        raise TypeError("base_ts must have data and times attributes")
    
    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=(12, 5))
    if title is None:
        title = f"{base_ts.signal_name} by time."
    if xlabel is None:
        xlabel = "Time in seconds."
    if ylabel is None:
        ylabel = base_ts.signal_name + " " + base_ts.last_process
        
    ax.plot(base_ts.times[start_idx:end_idx], base_ts.data[start_idx:end_idx], label=base_ts.signal_name)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True)
    for series in series_list:
        ax.plot(series.times[start_idx:end_idx], series.data[start_idx:end_idx], label=f"{series.signal_name} {series.last_process}")
    ax.legend()
    if show:
        plt.show()
    return ax

def plot_fft_power(ts,
                   max_rate: float = np.nan,
                   ax = None,
                   title: str = None,
                   xlabel: str = None,
                   ylabel: str = None, 
                   show: bool = False,
                   demean: bool = True,
                   scale_power: bool = False):
    """
    Plots the power of a timeseries signal using FFT.
    """
    
    # Check that ts has baseTs-like structure
    if not hasattr(ts, 'data') or not hasattr(ts, 'times'):
        raise TypeError("ts must have data and times attributes")
    
    if ax is None:
        ax = plt.gca()
    if title is None:
        title = f"Power Spectrum of {ts.signal_name}{ts.last_process}"
    if xlabel is None:
        xlabel = "Frequency (Hz)"
    if ylabel is None:
        ylabel = "Power"
    if scale_power:
        ylabel = "Scaled " + ylabel
    
    # Compute FFT power using object method
    freqs, power = ts.compute_fft_power(max_rate=max_rate, demean=demean, scale_power=scale_power)

    # Plotting
    ax.plot(freqs, power)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xlim(0, np.max(freqs))
    ax.grid(True)

    if show:
        plt.show()

    return ax

def lag_plot(ts,
            lag: Union[int, float], 
            lag_unit: str = "index",
            ax = None,
            show: bool = False) -> plt.Axes:
    """
    Generate a lag plot for a given timeseries object and lag.
    
    Parameters:
    - timeseries_obj: An object with .data (numpy array), .times, and .freq properties.
    - lag: A lag value, can be either an integer index or a time-based lag in seconds.
    - lag_unit: Specify whether the lag is in 'index' or 'seconds'. Default is 'index'.
    """
    
    res = shift_timeseries(ts, lag, lag_unit, drop_nan=False)
    lagged_data = res['lagged_data']
    lag_secs = res['lag_secs']
    lag_idx = res['lag_idx']
    
    try:
        sig_name = ts.signal_name.upper()
    except:
        sig_name = "Signal"

    # Create lag plot
    if ax is None:
        ax = plt.gca()
    ax.scatter(ts.data[lag_idx:], lagged_data[lag_idx:], s=3)  # Skip the NaN values for plotting
    ax.set_xlabel(f'Original {sig_name} Data')
    ax.set_ylabel(f'{sig_name} Data lagged at {lag_secs}seconds ({lag_idx}items)')
    ax.set_title(f'{sig_name} Lag Plot at {lag_secs} seconds ({lag_idx}items)')
    ax.grid(True)
    if show:
        plt.show()
    return ax