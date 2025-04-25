# -*- coding: utf-8 -*-
"""
Created on Oct 19 2024
@author: stan@sympaticog.com
"""

import numpy as np
from scipy import interpolate
import matplotlib.pyplot as plt
import copy
import pandas as pd
from scipy.ndimage import gaussian_filter

# Import modules - now using relative imports
from .filters import bbf, bandpass_filter, sg_filter, interpolate_missing_values, lowpass_filter, highpass_filter
from .lowess_filter import lowess_outlier_filter
from .utils import find_closest_time, compute_fft_power, find_closest, get_peak_freq, get_peaks


def from_df(df: pd.DataFrame, time_col: str = "time", data_col: str = "value", signal_name: str = None) -> "baseTs":
    """
    Create a baseTs object from a pandas DataFrame.
    """
    if signal_name is None:
        signal_name = data_col
    return baseTs(df[data_col].values, df[time_col].values, signal_name=signal_name)


class baseTs(object):
    """
    Basic data class to hold a timeseries and data.

    Args:
        data (np.array): The actual observational data.
        times (np.array): The timestamps corresponding to the data.
        freq (float, optional): The frequency of data collection. Defaults to np.nan.

    """

    def __init__(self,
                 data: np.array,
                 times: np.array=None,
                 freq: float = np.nan,
                 ts_offset: float = np.nan,
                 is_filtered: bool = False,
                 is_interpolated: bool = False,
                 is_uniform_grid: bool = False,
                 is_outlier_filtered: bool = False,
                 has_timestamp_offset: bool = False,
                 filtered_indices: np.array = None,
                 lowess_fit: np.array = None,
                 signal_name: str = "",
                 history: list = None,
                 last_process: str = ""):
        
        """
        Initialize the baseTs object.
        """
        
        self.data = data
        self.times = times
        self.is_filtered = is_filtered
        self.is_interpolated = is_interpolated
        self.is_uniform_grid = is_uniform_grid
        self.is_outlier_filtered = is_outlier_filtered
        self.has_timestamp_offset = has_timestamp_offset
        self.filtered_indices = filtered_indices
        self.lowess_fit = lowess_fit
        
        if ts_offset is not np.nan:  # if ts_offset is provided, set it and flag as having offset
            self.ts_offset = ts_offset
            self.has_timestamp_offset = True
        else:  # if no ts_offset is provided, set it to 0 to avoid errors and flag as not having offset
            self.ts_offset = 0
            self.has_timestamp_offset = False
            
        if times is None:
            if freq is not np.nan:
                self.times = np.arange(0, len(data)) / freq
            else:
                raise ValueError("You must provide either a times array or a frequency")
        else:
            self.times = times

        if history is None:
            self.history = [f"Created baseTs object with {self.len()} samples"]
        else:   
            self.history = history
        self.signal_name = signal_name.upper()
        self.last_process = last_process
        
        if freq is not np.nan:
            self.freq = freq
        else:
            # Use effective sample rate
            self.freq = self.len() / self.duration()

        # instantiate outlier filter w/ default parameters
        self.outlier_filter = lowess_outlier_filter()

    def duration(self) -> float:
        """
        Calculates the duration of the times.

        Returns:
            float: Duration of the times
        """
        return float(self.times[-1] - self.times[0])
    
    def len(self) -> int:
        """
        Calculates the length of the data.

        Returns:
            int: Length of the data
        """
        return len(self.data)

    def interpto_samples(self, new_len: int, kind: str = 'linear', inplace: bool = False) -> "baseTs":
        """
        Interpolate the times to a new length.

        Args:
            new_len (int): The desired new length of the interpolated times.
            kind (str, optional): The type of interpolation to use. Defaults to 'quadratic'.
            inplace (bool, optional): If True, modifies existing object. Otherwise returns a new object. Defaults to False.

        Returns:
            baseTs: Interpolated data
        """
        new_ts = np.linspace(self.times[0], self.times[-1], new_len)
        new_freq = new_len / self.duration()
        f1 = interpolate.interp1d(self.times, self.data, kind=kind)
        transfer = f1(new_ts)
        last_process = "_interpto_" + str(new_len) + "samples"
        hist_msg = f"Interpolated to {new_len} samples"
        if inplace == False:
            newTs = self.copy()  # Create a new deep copy of the baseTs object
            newTs.data = transfer
            newTs.times = new_ts
            newTs.is_interpolated = True
            newTs.freq = new_freq
            newTs.history.append(hist_msg)
            newTs.last_process = last_process
            newTs.is_interpolated = True
            newTs.is_uniform_grid = True
            return newTs
        else:
            self.data = transfer
            self.times = new_ts
            self.is_interpolated = True
            self.freq = new_freq
            self.history.append(hist_msg)
            self.last_process = last_process
            self.is_interpolated = True
            self.is_uniform_grid = True
            return self
            
    def interp_to_uniform_grid(self, new_grid: np.array = None, kind: str = 'linear', inplace: bool = True) -> "baseTs":
        """
        Interpolate data to a uniform sampling grid.
        If new_grid is not specified, use the existing info to create a new uniform grid
        of the same duration at the average effective sample rate.

        Args:
            new_grid (np.array, optional): The desired new sampling grid. Defaults to None.
            kind (str, optional): The type of interpolation to use. Defaults to 'linear'.
            inplace (bool, optional): If True, modifies existing object. Otherwise returns a new object. Defaults to True.

        Returns:
            new_ts: baseTs object with uniform sampling grid
                    Note: freq is recalculated to match the new grid.
        """
        if new_grid is None:
            # create new evenly spaced grid at the effective sample rate
            new_grid = np.linspace(self.times[0], self.times[-1], len(self.data))
        else:
            if not np.all(np.diff(new_grid) > 0):
                raise ValueError("new_grid must be monotonically increasing.")
            
        f1 = interpolate.interp1d(self.times, self.data, kind=kind)
        new_freq = len(new_grid) / self.duration()
        
        hist_msg = f"Interpolated to uniform grid of n={len(new_grid)} @ {new_freq}Hz"
        last_process = "_unigrid"
        transfer = f1(new_grid)
        if inplace == False:
            newTs = self.copy()
            newTs.data = transfer
            newTs.times = new_grid
            newTs.is_uniform_grid = True
            newTs.freq = new_freq
            newTs.history.append(hist_msg)
            newTs.last_process = last_process
            newTs.is_interpolated = True
            newTs.is_uniform_grid = True
            return newTs
        else:
            self.data = transfer
            self.times = new_grid
            self.freq = new_freq
            self.is_uniform_grid = True
            self.history.append(hist_msg)
            self.last_process = last_process
            self.is_interpolated = True
            self.is_uniform_grid = True
            return self
        
    def zscale(self, inplace: bool = False) -> "baseTs":
        """
        Z-scale the data.
        """
        if inplace:
            self.data = (self.data - self.data.mean()) / self.data.std()
            return self
        else:
            new_ts = self.copy()
            new_ts.data = (new_ts.data - new_ts.data.mean()) / new_ts.data.std()
            return new_ts
    
    def normalize_range(self, inplace: bool = False) -> "baseTs":
        """
        Normalize the data to the range 0-1.
        """
        if inplace:
            self.data = (self.data - self.data.min()) / (self.data.max() - self.data.min())
            return self
        else:
            new_ts = self.copy()
            new_ts.data = (new_ts.data - new_ts.data.min()) / (new_ts.data.max() - new_ts.data.min())
            return new_ts
    
    def interpto_hz(self, new_freq: int, kind: str = 'linear', inplace: bool = False) -> "baseTs":
        """
        Interpolate the times to a new frequency.

        Args:
            new_freq (int): The desired new frequency of the interpolated times.
            kind (str, optional): The type of interpolation to use. Defaults to 'quadratic'.
            inplace (bool, optional): If True, modifies existing object. Otherwise returns a new object. Defaults to False.

        Returns:
            baseTs: Interpolated data at new frequency
        """
        new_ts = np.linspace(self.times[0], self.times[-1], int(self.duration() * new_freq))
        f1 = interpolate.interp1d(self.times, self.data, kind=kind)
        transfer = f1(new_ts)
        hist_msg = f"Interpolated to {new_freq}Hz"
        last_process = "_interpto_" + str(new_freq) + "Hz"
        if inplace == False:
            newTs = self.copy()
            newTs.data = transfer   
            newTs.times = new_ts
            newTs.freq = new_freq
            newTs.is_interpolated = True
            newTs.history.append(hist_msg)
            newTs.last_process = last_process
            newTs.is_interpolated = True
            newTs.is_uniform_grid = True
            return newTs
        
        else:
            self.freq = new_freq
            self.data = transfer
            self.times = new_ts
            self.is_interpolated = True
            self.is_uniform_grid = True
            self.history.append(hist_msg)
            self.last_process = last_process
            return self
        
    def trimto_timepoints(self, start_val: float = np.nan, end_val: float = -1, inplace: bool = False) -> "baseTs":
        """
        Trims the data between specified timepoints.

        Args:
            start_val (float, optional): Start value for trimming. Defaults to np.nan (start of series).
            end_val (float, optional): End value for trimming. Defaults to -1 (end of series).
            inplace (bool, optional): If True, modifies existing object. Otherwise returns a new object. Defaults to False.

        Returns:
            baseTs: Trimmed data
        """
        if start_val != np.nan:
            start_idx = find_closest(start_val, self.times)["location"]
        else:
            start_idx = 0
        if end_val != -1:
            end_idx = find_closest(end_val, self.times)["location"]
        else:
            end_idx = -1

        new_data = self.data[start_idx:end_idx]
        new_ts = self.times[start_idx:end_idx]
        hist_msg = f"Trimmed to {start_idx} to {end_idx}"
        last_process = "_trimto_[" + str(start_idx) + ":" + str(end_idx) + "]"
        if inplace == False:
            newTs = self.copy()
            newTs.data = new_data
            newTs.times = new_ts
            newTs.freq = self.freq
            newTs.history.append(hist_msg)
            newTs.last_process = last_process
            return newTs
        else:
            self.data = new_data
            self.times = new_ts
            self.history.append(hist_msg)
            self.last_process = last_process
            return self

    def lowess_detrend(self, frac: float = 0.25, inplace: bool = False) -> "baseTs":
        """
        Detrend the data using a lowess fit.
        """
        if inplace:
            self.lowess_fit = self.set_outlier_filter(frac=frac)
            self.filter_outliers(inplace=True)
            self.data = self.data - self.lowess_fit
            self.history.append(f"Detrended with lowess fit frac={frac}")
            self.last_process = "_lowess_detrend"
            return self
        else:
            newTs = self.copy()
            newTs.lowess_fit = self.set_outlier_filter(frac=frac)
            newTs.filter_outliers(inplace=True)
            newTs.data = newTs.data - newTs.lowess_fit
            newTs.history.append(f"Detrended with lowess fit frac={frac}")
            newTs.last_process = "_lowess_detrend"
            return newTs
        
    def highpass_at(self, cutoff, order: int = 5, inplace: bool = False) -> "baseTs":
        nyq = 0.5 * self.freq  # Nyquist Frequency
        normal_cutoff = cutoff / nyq
        filt = highpass_filter(self.data, cutoff, self.freq, order)
        hist_msg = f"Highpass filtered at {cutoff} Hz"
        last_process = "_hp_" + str(cutoff) + "Hz"
        if inplace == True:
            self.data = filt
            self.is_filtered = True
            self.history.append(hist_msg)
            self.last_process = last_process
            return self
        else:
            newTs = self.copy()
            newTs.data = filt
            newTs.is_filtered = True
            newTs.history.append(hist_msg)
            newTs.last_process = last_process
            return newTs
        
    def lowpass_at(self, cutoff, order: int = 5, inplace: bool = False) -> "baseTs":
        nyq = 0.5 * self.freq  # Nyquist Frequency
        normal_cutoff = cutoff / nyq
        filt = lowpass_filter(self.data, cutoff, self.freq, order)
        hist_msg = f"Lowpass filtered at {cutoff} Hz"
        last_process = "_lp_" + str(cutoff) + "Hz"
        if inplace == True:
            self.data = filt
            self.is_filtered = True
            self.history.append(hist_msg)
            self.last_process = last_process
            return self
        else:
            newTs = self.copy()
            newTs.data = filt
            newTs.is_filtered = True
            newTs.history.append(hist_msg)
            newTs.last_process = last_process
            return newTs


    def gauss_filter(self, sigma: float = 1, inplace: bool = False) -> "baseTs":
        """
        Apply a Gaussian filter to the data.

        Returns:
            baseTs: The filtered data.
        """
        filt = gaussian_filter(self.data, sigma)
        hist_msg = f"Applied Gaussian filter with sigma={sigma}"
        last_process = "_gauss_" + str(sigma)
        if inplace == True:
            self.data = filt
            self.history.append(hist_msg)
            self.last_process = last_process
            return self
        else:
            newTs = self.copy()
            newTs.data = filt
            return newTs
    
    def bandpass_at(self,
                    hp_hz: float = 0.01,
                    lp_hz: float = 0.1,
                    inplace: bool = False,
                    reset_mean: bool = True) -> "baseTs":
        """
        Apply a bandpass filter to the signal at specified low-pass and high-pass frequencies.

        Args:
            hp_hz (float): High-pass cutoff frequency in Hz.
            lp_hz (float): Low-pass cutoff frequency in Hz.
            inplace (bool, optional): If True, modifies existing object.
                    Otherwise returns a new filtered data.
                    Defaults to False.
            reset_mean (bool, optional): If True, resets the mean of the
                    filtered data to the mean of the original data.
                    Defaults to True.

        Returns:
            baseTs: Bandpass filtered data
        """
        filt = bandpass_filter(self.data,
                               hp_hz=hp_hz,
                               lp_hz=lp_hz,
                               sample_Hz=self.freq,
                               reset_mean=reset_mean)
        hist_msg = f"Bandpass filtered at {lp_hz} Hz and {hp_hz} Hz"
        last_process = "_bp_" + str(lp_hz) + ":" + str(hp_hz) + "Hz"
        if inplace == True:
            self.data = filt
            self.is_filtered = True
            self.history.append(hist_msg)
            self.last_process = last_process
            return self
        else:
            newTs = self.copy()
            newTs.data = filt
            newTs.is_filtered = True
            newTs.history.append(hist_msg)
            newTs.last_process = last_process
            return newTs

    def butterpass_at(self, hp_freq: float, lp_freq: float, inplace: bool = False) -> "baseTs":
        """
        Apply a Butterworth pass filter to the signal at specified low-pass and high-pass frequencies.

        Args:
            hp_freq (float): High-pass frequency.
            lp_freq (float): Low-pass frequency.
            inplace (bool, optional): If True, modifies existing object. Otherwise returns a new filtered data. Defaults to False.

        Returns:
            baseTs: Butterworth pass filtered data
        """
        filt = bbf(self.data, highpass_freq=hp_freq, lowpass_freq=lp_freq, sampling_freq=self.freq)
        hist_msg = f"Butterworth pass filtered at {hp_freq} Hz and {lp_freq} Hz"
        last_process = "_btrp_" + str(lp_freq) + ":" + str(hp_freq) + "Hz"
        if inplace == True:
            self.data = filt
            self.is_filtered = True
            self.history.append(hist_msg)
            self.last_process = last_process
            return self
        else:
            newTs = self.copy()
            newTs.data = filt
            newTs.is_filtered = True
            newTs.history.append(hist_msg)
            newTs.last_process = last_process   
            return newTs
        
    def set_outlier_filter(self, 
                        params: dict = None,
                        z_threshold: float = 7,
                        frac: float = 0.075,
                        max_iterations: int = 10,
                        interpolation_method: str = 'linear',
                        order: int = 2,
                        use_median: bool = True) -> "baseTs":
        """
        Set outlier filter parameters.
        
        Parameters
        ----------
        params : dict, optional
            Dictionary of parameter values. If provided, overrides individual parameters.
            Valid keys are: 'z_threshold', 'frac', 'max_iterations', 'interpolation_method',
            'order', 'use_median'
        z_threshold : float, default=7
            Z-score threshold for outlier detection
        frac : float, default=0.075
            Fraction of points to consider as outliers
        max_iterations : int, default=100
            Maximum number of iterations for outlier detection
        interpolation_method : str, default='linear'
            Interpolation method for replacing outliers
        order : int, default=2
            Order of the interpolation
        use_median : bool, default=True
            Whether to use median instead of mean for calculations
        
        Returns
        -------
        self
            Returns the instance for method chaining
        
        Notes
        -----
        This overwrites the default parameters.
        You must re-run filter_outliers to use the new parameters.
        """
        # If params dictionary is provided, use it to update parameters
        if params is not None:
            valid_params = {
                'z_threshold': float,
                'frac': float,
                'max_iterations': int,
                'interpolation_method': str,
                'order': int,
                'use_median': bool
            }
            
            # Validate and set parameters from dictionary
            for param_name, param_type in valid_params.items():
                if param_name in params:
                    value = params[param_name]
                    # Type checking
                    if not isinstance(value, param_type):
                        try:
                            value = param_type(value)
                        except ValueError:
                            raise ValueError(f"Invalid type for {param_name}. Expected {param_type.__name__}")
                    setattr(self.outlier_filter, param_name, value)
        else:
            # Use individual parameters
            self.outlier_filter.z_threshold = z_threshold
            self.outlier_filter.max_iterations = max_iterations
            self.outlier_filter.frac = frac
            self.outlier_filter.interpolation_method = interpolation_method
            self.outlier_filter.order = order
            self.outlier_filter.use_median = use_median
        
        hist_msg = f"Set new outlier filter parameters: {self.outlier_filter.__dict__}"
        last_process = "_outfilt_params"
        
        self.is_outlier_filtered = True
        self.history.append(hist_msg)
        self.last_process = last_process
    
        return self

    def get_outlier_filter_params(self) -> dict:
        """
        Get outlier filter parameters.
            returns a dictionary of the parameters.
        """
        return self.outlier_filter.__dict__
        
    def filter_outliers(self,
                        inplace: bool = False,
                        qcplot: bool = False,
                        show_plot: bool = False,
                        ax = None) -> "baseTs":
        """
        Apply the outlier filter to the signal.
        Args:
            inplace (bool, optional): If True, modifies existing object. Otherwise returns a new filtered data. Defaults to False.
            qc_plot (bool, optional): If True, generates a QC plot using the current data as the base_ts and the outlier-filtered data as the filtered_data. Defaults to False.
            return_lowess:bool=False,
            show_plot:bool=False,
            ax=None,
        Returns:
            baseTs: filtered data
        """
        # Import plotting here to avoid circular imports
        from .plotting import qc_plot
        
        filt, idx, lowess_fit = self.outlier_filter.filter(self, return_lowess=True)
        hist_msg = f"Filtered outliers with lowess: {self.outlier_filter.__dict__}"
        last_process = "_outfilt"
                   
        if inplace == True:
            self.data = filt.data
            self.times = filt.times
            self.freq = filt.freq
            self.is_outlier_filtered = True
            self.history.append(hist_msg)
            self.last_process = last_process
            self.lowess_fit = lowess_fit
            self.filtered_indices = idx
            result = self 
        else:
            newTs = self.copy()
            newTs.data = filt.data
            newTs.times = filt.times
            newTs.freq = filt.freq
            newTs.history.append(hist_msg)
            newTs.last_process = last_process
            newTs.is_outlier_filtered = True
            newTs.lowess_fit = lowess_fit
            newTs.filtered_indices = idx
            result = newTs
        
        if qcplot:
            # Generate QC plot, optionally display on user-provided axis,
            # and optionally show plot to user.
            _ = qc_plot(self, filt.data, filt.times, show=show_plot, ax=ax)
        
        return result
            
    def sg_filter(self, window_length: int = 11, polyorder: int = 2, inplace: bool = False) -> "baseTs":
        """
        Apply a Savitzky-Golay filter to the signal.
        """
        filt = sg_filter(self.data, window_length, polyorder)
        hist_msg = f"Applied Savitzky-Golay filter wl={window_length}, polyorder={polyorder}"
        last_process = "_sgFilter"
        if inplace == True:
            self.data = filt    
            self.is_filtered = True
            self.history.append(hist_msg)
            self.last_process = last_process
            self.is_filtered = True
            return self
        else:
            newTs = self.copy()
            newTs.data = filt
            newTs.is_filtered = True
            newTs.history.append(hist_msg)
            newTs.last_process = last_process   
            newTs.is_filtered = True
            return newTs
        
    def interpolate_missing(self, inplace: bool = False) -> "baseTs":
        """
        Interpolate missing values in the data.
        """
        return interpolate_missing_values(self, inplace=inplace)
    
    # Utility functions
    
    def compute_fft_power(self, max_rate: float = np.nan, demean: bool = True, scale_power: bool = True) -> tuple:
        """
        Compute the FFT power of the timeseries.
        """
        return compute_fft_power(self, max_rate=max_rate, demean=demean, scale_power=scale_power)

    def get_closest_time(self, sec: float) -> dict:
        """
        Find the closest time in the timeseries to a target time in seconds.
        Returns a dictionary with the following keys:
            "location": the index of the closest time
            "time": the value of the closest time
            "distance": the difference between the closest time and the target time
                        in seconds. Useful for QC/debugging.
        """
        return find_closest_time(self, sec)

    def get_peak_freq(self) -> float:
        """
        Compute the peak frequency of the timeseries.
        Returns the frequency of the peak power.
        """
        pk_freq = get_peak_freq(self)  
        return pk_freq

    def get_peaks(self, min_dist_secs: float = 1.0, min_height: float = None) -> list:
        """
        Get the peaks in the timeseries.
        Returns a list of the indices of the peaks.
        """
        return get_peaks(self, min_dist_secs=min_dist_secs, min_height=min_height)

    # Plotting functions
    
    def plot_line(self,
             ax = None,
             title: str = None,
             xlabel: str = None,
             ylabel: str = None,
             lowess: bool = False,
             show: bool = True) -> plt.Axes:
        """
        Plot the timeseries as a line plot.
        Quick and dirty visualization.
        """
        # Import plotting here to avoid circular imports
        from .plotting import plot
        
        return plot(self,
                ax=ax,
                title=title,
                xlabel=xlabel,
                ylabel=ylabel, 
                lowess=lowess,
                show=show)

    # Alias for plot_line to maintain backward compatibility
    # Will be altered in future versions.
    # TODO: Deprecate in future versions.
    # TODO: Replace with generic plot() function that maps
    #       to all available plotting functions.
    #       e.g. plot_hist would be plot("hist", bins=10, kde=True, etc...)
    plot = plot_line
    
    def plot_series(self,
                    series_list: list,
                    ax = None,
                    title: str = None,
                    xlabel: str = None,
                    ylabel: str = None, 
                    show: bool = True) -> plt.Axes:
        """
        Plot this timeseries against one or more other timeseries.
        e.g. for QC, comparing filtering methods, or multiple participants.
        """
        # Import plotting here to avoid circular imports
        from .plotting import plot_series
        
        return plot_series(self,
                series_list=series_list,
                ax=ax,
                title=title,
                xlabel=xlabel,
                ylabel=ylabel, 
                show=show)

    def plot_hist(self,
                  ax = None,
                  title: str = None,
                  xlabel: str = None,
                  show: bool = True,
                  bins: int = -1,
                  kde: bool = False) -> plt.Axes:
        """
        Plot a histogram of the timeseries.
        """
        # Import plotting here to avoid circular imports
        from .plotting import hist
        
        return hist(self,
                    ax=ax,
                    title=title,
                    xlabel=xlabel,
                    show=show,
                    bins=bins,
                    kde=kde)

    def plot_fft_power(self,
                            max_rate: float = np.nan,
                            ax = None,
                            title: str = None,
                            xlabel: str = None,
                            ylabel: str = None, 
                            show: bool = False,
                            demean: bool = True,
                            scale_power: bool = False) -> plt.Axes:
        """
        Plot the power spectrum of the timeseries.

        Args:
            max_rate (float, optional): Maximum frequency rate to display. Defaults to np.nan.
            ax (matplotlib.axes.Axes, optional): Matplotlib Axes object to plot on. Defaults to None.
            title (str, optional): Title of the plot. Defaults to None.
            xlabel (str, optional): Label for the x-axis. Defaults to None.
            ylabel (str, optional): Label for the y-axis. Defaults to None.
            show (bool, optional): Whether to display the plot. Defaults to False.
            demean (bool, optional): Whether to demean the data before computing FFT. Defaults to True.
            scale_power (bool, optional): Whether to scale the power spectrum. Defaults to False.

        Returns:
            matplotlib.axes.Axes: The Axes object with the plot.
        """
        # Import plotting here to avoid circular imports
        from .plotting import plot_fft_power
        
        return plot_fft_power(self,
                        max_rate=max_rate,
                        ax=ax,
                        title=title,
                        xlabel=xlabel,
                        ylabel=ylabel,  
                        show=show,
                        demean=demean,
                        scale_power=scale_power)

    def copy(self) -> "baseTs":
        """
        Create a deep copy of the baseTs object.

        Returns:
            baseTs: A new instance of baseTs with the same data.
        """
        return copy.deepcopy(self)

    def apply(self, func, *args, inplace=False, **kwargs) -> "baseTs":
        """
        Applies a user-provided function to the data vector.
        Note: the times vector is not modified.
        """
           
        if inplace:
            # Modify the data in-place
            self.data = func(self.data, *args, **kwargs)
            return self  # Return self for chaining
        else:
            # Return a new object with modified data
            new_obj = copy.deepcopy(self)
            new_obj.data = func(new_obj.data, *args, **kwargs)
            return new_obj

    def info(self):
        """
        Display information about the data, times, outlier
        filter parameters, and history.
        """
        round_values = lambda x: round(x, 4) if isinstance(x, float) else x
        
        data_info = {
            "Length": len(self.data),
            "Min": np.min(self.data),
            "Max": np.max(self.data),
            "Std": np.std(self.data)
        }
        
        # Round all values except for length
        for key, value in data_info.items():
            data_info[key] = round_values(value)
        
        times_info = {
            "Start": self.times[0],
            "End": self.times[-1],
            "Duration": self.duration(),
            "Effective Frequency": self.freq,
            "Timestamp Offset": self.ts_offset
        }
        
        for key, value in times_info.items():
            times_info[key] = round_values(value)
        
        outlier_filter_params = self.get_outlier_filter_params()
        
        print("Data Information:")
        for key, value in data_info.items():
            print(f"  {key}: {value}")
        
        print("\nTime Information:")
        for key, value in times_info.items():
            print(f"  {key}: {value}")
        
        print("\nOutlier Filter Parameters:")
        for key, value in outlier_filter_params.items():
            print(f"  {key}: {value}")
        
        print("\nHistory:")
        for entry in self.history:
            print(f"  {entry}")
            
    def set_timestamp_offset(self, ts_offset: float):
        """
        Set or updates the timestamp offset.
        """
        self.ts_offset = ts_offset
        self.times = self.times + ts_offset
        self.history.append(f"Set timestamp offset to {ts_offset}")
        self.last_process = "_tso" + str(ts_offset)
        self.has_timestamp_offset = True

    def to_dataframe(self, set_index: bool = False) -> pd.DataFrame:
        """
        Convert the timeseries to a pandas DataFrame.

        Args:
            set_index (bool): If True, set the 'times' column as the index of the DataFrame.
                              Defaults to False. You can always set the index afterwards using
                              the 'set_index' method.
        Returns:
            pd.DataFrame: A DataFrame containing the times, data, and timestamps.
        """
        if self.has_timestamp_offset:
            timestamps = self.times + self.ts_offset
        else:
            timestamps = self.times * np.nan
        df = pd.DataFrame({"times": self.times, "data": self.data, "timestamps": timestamps})
        if set_index:  # set times as index if desired ;
            df.set_index("times", inplace=True)
        return df


def gauss_filter(data, sigma):
    """
    Apply a Gaussian filter to the data.

    Args:
        data (np.array): The input data to be filtered.
        sigma (float): The standard deviation for Gaussian kernel.

    Returns:
        np.array: The filtered data.
    """
    return gaussian_filter(data, sigma)