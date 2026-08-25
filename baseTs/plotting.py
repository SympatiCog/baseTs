# -*- coding: utf-8 -*-
"""
Created on Oct 19 2024
@author: stan@sympaticog.com
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from typing import Union, Optional, Tuple

# local imports
#sys.path.append('/Users/stan/Projects/cpCST_MoBI/baseTs')
from .utils import shift_timeseries

def zscale(x: np.ndarray) -> np.ndarray:
    """Standardize data by removing the mean and scaling to unit variance."""
    return (x - np.mean(x)) / np.std(x)

def setup_plot(ax: Optional[plt.Axes] = None, 
               figsize: Tuple[float, float] = (9, 3),
               title: Optional[str] = None,
               xlabel: Optional[str] = None,
               ylabel: Optional[str] = None,
               show: bool = False) -> Tuple[plt.Figure, plt.Axes]:
    """
    Common setup function for creating and configuring plots.
    
    Args:
        ax: Optional axes to plot on. If None, creates new figure and axes.
        figsize: Tuple of (width, height) in inches.
        title: Optional plot title.
        xlabel: Optional x-axis label.
        ylabel: Optional y-axis label.
        show: Whether to display the plot.
        
    Returns:
        Tuple of (figure, axes)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure
        
    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.grid(True)
    
    if show:
        plt.show()
        
    return fig, ax

def qc_plot(ts,
            filt_data: np.array,
            filt_times: Optional[np.array] = None,
            ax: Optional[plt.Axes] = None,
            title: Optional[str] = None,
            xlabel: Optional[str] = None,
            ylabel: Optional[str] = None,
            show_lowess: bool = True,
            show: bool = False) -> plt.Axes:
    """
    Plots a quality control plot for a timeseries.
    """
    if title is None:
        title = f"QC Plot for {ts.signal_name}"
    if xlabel is None:
        xlabel = "Time"
    if ylabel is None:
        ylabel = ts.signal_name + " " + ts.last_process
    if filt_times is None:
        filt_times = ts.times

    _, ax = setup_plot(ax=ax, title=title, xlabel=xlabel, ylabel=ylabel, show=False)

    ax.plot(ts.times, ts.data, label='Original')
    ax.plot(filt_times, filt_data, label='Filtered')
    # Gate on the fit itself, not on is_outlier_filtered: that flag means "a
    # filter has been configured", so it is True before any fit exists and
    # False after lowess_detrend, which produces a fit without filtering.
    if show_lowess and ts.lowess_fit is not None:
        ax.plot(ts.times, ts.lowess_fit, label='Lowess Fit')
    ax.legend()
    
    if show:
        plt.show()
        
    return ax

def hist(ts,
         ax: Optional[plt.Axes] = None,
         title: Optional[str] = None,
         xlabel: Optional[str] = None,
         show: bool = False,
         bins: int = -1,
         kde: bool = False) -> plt.Axes:
    """
    Plots a histogram of a timeseries.
    """
    if xlabel is None:
        xlabel = ts.signal_name + " " + ts.last_process
    if bins == -1:
        bins = 'auto'
    
    plotkind = "KDE" if kde else "Histogram"
    ylabel = "Density" if kde else "Frequency"
    if title is None:
        title = f"{plotkind} of {ts.signal_name} {ts.last_process}"
        
    _, ax = setup_plot(ax=ax, title=title, xlabel=xlabel, ylabel=ylabel, show=False)
        
    # Plot histogram
    ax.hist(ts.data, bins=bins, density=kde, edgecolor='black', label='Histogram', alpha=0.6)
    
    if kde:
        # Calculate KDE
        kde_obj = gaussian_kde(ts.data)
        x = np.linspace(min(ts.data), max(ts.data), 150)
        y = kde_obj(x)
        # Plot KDE
        ax.plot(x, y, label='KDE')
        ax.legend()
        
    if show:
        plt.show()
        
    return ax

def plot(ts,
         ax: Optional[plt.Axes] = None,
         title: Optional[str] = None,
         xlabel: Optional[str] = None,
         ylabel: Optional[str] = None, 
         show: bool = False,
         lowess: bool = False,
         start_idx: int = 0,
         end_idx: int = -1) -> plt.Axes: 
    """
    Plots a timeseries.
    """
    from baseTs import baseTs  # Import inside the function to avoid circular import
    
    if not isinstance(ts, baseTs):
        raise TypeError("ts must be an instance of baseTs")
    
    if title is None:
        title = f"{ts.signal_name} by time."
    if xlabel is None:
        xlabel = "Time in seconds."
    if ylabel is None:
        ylabel = ts.signal_name + " " + ts.last_process
        
    _, ax = setup_plot(ax=ax, title=title, xlabel=xlabel, ylabel=ylabel, show=False)
        
    ax.plot(ts.times[start_idx:end_idx], ts.data[start_idx:end_idx], 
            label=ts.signal_name + ts.last_process)
    if lowess:
        ax.plot(ts.times[start_idx:end_idx], ts.lowess_fit[start_idx:end_idx], 
                label='Lowess Fit')
        ax.legend()
        
    if show:
        plt.show()
        
    return ax

def plot_series(base_ts,
                series_list: list,
                ax: Optional[plt.Axes] = None,
                title: Optional[str] = None,
                xlabel: Optional[str] = None,
                ylabel: Optional[str] = None, 
                show: bool = False,
                start_idx: int = 0,
                end_idx: int = -1) -> plt.Axes: 
    """
    Plots multiple timeseries on the same plot.
    """
    from baseTs import baseTs  # Import inside the function to avoid circular import
    
    if not isinstance(base_ts, baseTs):
        raise TypeError("base_ts must be an instance of baseTs")
    
    if title is None:
        title = f"{base_ts.signal_name} by time."
    if xlabel is None:
        xlabel = "Time in seconds."
    if ylabel is None:
        ylabel = base_ts.signal_name + " " + base_ts.last_process
        
    _, ax = setup_plot(ax=ax, title=title, xlabel=xlabel, ylabel=ylabel, show=False)
        
    ax.plot(base_ts.times[start_idx:end_idx], base_ts.data[start_idx:end_idx], 
            label=base_ts.signal_name)
    
    for series in series_list:
        ax.plot(series.times[start_idx:end_idx], series.data[start_idx:end_idx], 
                label=f"{series.signal_name} {series.last_process}")
    ax.legend()
    
    if show:
        plt.show()
        
    return ax

def plot_fft_power(ts,
                   max_rate: float = np.nan,
                   min_rate: float = 0.0,
                   window: str = None,
                   ax: Optional[plt.Axes] = None,
                   title: Optional[str] = None,
                   xlabel: Optional[str] = None,
                   ylabel: Optional[str] = None, 
                   show: bool = False,
                   scale_power: bool = False,
                   highlight_band: Optional[Tuple[float, float]] = None) -> plt.Axes:
    """
    Plots the power spectrum of a timeseries signal using enhanced FFT with windowing.

    Args:
        ts: Time series object
        max_rate: Maximum frequency to display (defaults to Nyquist frequency)
        min_rate: Minimum frequency to display (defaults to 0.0)
        window: Window function to apply ('hann', 'hamming', 'blackman', None)
        ax: Matplotlib axes to plot on
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        show: Whether to show the plot
        scale_power: Whether to normalize power spectrum
        highlight_band: Optional (low_freq, high_freq) tuple in Hz to shade,
            e.g. (0.01, 0.1) to mark the fALFF band alongside
            ts.relative_band_power(0.01, 0.1)

    Returns:
        Matplotlib axes object

    Raises:
        ValueError: If the time series is empty or has invalid frequency
    """
    from baseTs import baseTs  # Import inside the function to avoid circular import
    
    if not isinstance(ts, baseTs):
        raise TypeError("ts must be an instance of baseTs")
    
    # Set up title with window information
    window_str = f" ({window} window)" if window else ""
    if title is None:
        title = f"Power Spectrum of {ts.signal_name}{ts.last_process}{window_str}"
    if xlabel is None:
        xlabel = "Frequency (Hz)"
    if ylabel is None:
        ylabel = "Power"
    if scale_power:
        ylabel = "Scaled " + ylabel
    
    _, ax = setup_plot(ax=ax, title=title, xlabel=xlabel, ylabel=ylabel, show=False)
    
    try:
        # Use the enhanced get_frequency_content method
        freqs, power = ts.get_frequency_content(window=window)
        
        if len(freqs) == 0 or len(power) == 0:
            raise ValueError("FFT computation resulted in empty frequency or power arrays")
        
        # Apply frequency range filtering
        if np.isnan(max_rate):
            max_rate = np.max(freqs)  # Use Nyquist frequency as default
        
        # Create frequency mask for the specified range
        freq_mask = (freqs >= min_rate) & (freqs <= max_rate)
        freqs_filtered = freqs[freq_mask]
        power_filtered = power[freq_mask]
        
        if len(freqs_filtered) == 0:
            raise ValueError(f"No frequencies found in range [{min_rate}, {max_rate}] Hz")
        
        # Apply power scaling if requested
        if scale_power:
            power_max = np.max(power_filtered)
            if power_max > 0:
                power_filtered = power_filtered / power_max
            
        # Plotting
        ax.plot(freqs_filtered, power_filtered, linewidth=1.2)
        ax.set_xlim(min_rate, max_rate)

        # Shade the band of interest, if requested
        if highlight_band is not None:
            band_low, band_high = highlight_band
            if band_low >= band_high:
                raise ValueError(
                    f"highlight_band low ({band_low} Hz) must be less than "
                    f"high ({band_high} Hz)"
                )
            ax.axvspan(band_low, band_high, alpha=0.15, color='tab:orange',
                       label=f"{band_low}-{band_high} Hz")
            ax.legend()
        
        # Add grid for better readability
        ax.grid(True, alpha=0.3)
        
        # Set y-axis to start at 0 for power spectra
        ax.set_ylim(bottom=0)
        
        if show:
            plt.show()
            
    except Exception as e:
        ax.text(0.5, 0.5, f"Error plotting FFT: {str(e)}", 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes)
        if show:
            plt.show()
    
    return ax

def lag_plot(ts,
            lag: Union[int, float], 
            lag_unit: str = "index",
            ax: Optional[plt.Axes] = None,
            show: bool = False) -> plt.Axes:
    """
    Generate a lag plot for a given timeseries object and lag.
    """
    res = shift_timeseries(ts, lag, lag_unit, drop_nan=False)
    lagged_data = res['lagged_data']
    lag_secs = res['lag_secs']
    lag_idx = res['lag_idx']
    
    try:
        sig_name = ts.signal_name.upper()
    except Exception as e:
        print(f"An error occurred: {e}")
        sig_name = "Signal"

    title = f'{sig_name} Lag Plot at {lag_secs} seconds ({lag_idx}items)'
    xlabel = f'Original {sig_name} Data'
    ylabel = f'{sig_name} Data lagged at {lag_secs}second ({lag_idx}items)'
    
    _, ax = setup_plot(ax=ax, title=title, xlabel=xlabel, ylabel=ylabel, show=False)
    
    ax.scatter(ts.data[lag_idx:], lagged_data[lag_idx:], s=3)  # Skip the NaN values for plotting
    
    if show:
        plt.show()
        
    return ax
