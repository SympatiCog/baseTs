# -*- coding: utf-8 -*-
"""
Created on Oct 19 2024
@author: stan@sympaticog.com
"""

from __future__ import annotations
import numpy as np
from scipy import interpolate
import matplotlib.pyplot as plt
import copy
import pandas as pd
from scipy.ndimage import gaussian_filter
from typing import Optional, TYPE_CHECKING, Union

# Import modules - now using relative imports
from .filters import bandpass_filter, sg_filter, interpolate_missing_values, lowpass_filter, highpass_filter, notch_filter
from .LowessOutlierFilter import LowessOutlierFilter, TailType
from .utils import find_closest_time, compute_fft_power, find_closest, get_peak_freq, get_peaks, ClosestMatch, diff, dediff
from .compat import BackendManager, ArrayCompatMixin, convert_to_series, validate_time_index
# from .plotting import qc_plot, hist, plot

if TYPE_CHECKING:
    from .plotting import plt

def from_df(df: pd.DataFrame, 
            time_col: str = "time", 
            data_col: str = "value", 
            signal_name: Optional[str] = None,
            freq: Optional[float] = None,
            ts_offset: Optional[float] = None) -> "baseTs":
    """
    Create a baseTs object from a pandas DataFrame.

    Args:
        df: Input DataFrame containing time series data
        time_col: Name of the column containing time values
        data_col: Name of the column containing data values
        signal_name: Name of the signal (defaults to data_col if None)
        freq: Sampling frequency in Hz (optional)
        ts_offset: Timestamp offset in seconds (optional)

    Returns:
        baseTs: A new baseTs object initialized with the DataFrame data

    Raises:
        ValueError: If required columns are missing or data is invalid
        TypeError: If input types are incorrect
    """
    # Input validation
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    
    # Check for required columns
    missing_cols = [col for col in [time_col, data_col] if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Validate data types
    if not np.issubdtype(df[time_col].dtype, np.number):
        raise ValueError(f"Time column '{time_col}' must be numeric")
    if not np.issubdtype(df[data_col].dtype, np.number):
        raise ValueError(f"Data column '{data_col}' must be numeric")
    
    # Check for missing values
    if df[time_col].isnull().any():
        raise ValueError(f"Time column '{time_col}' contains missing values")
    if df[data_col].isnull().any():
        raise ValueError(f"Data column '{data_col}' contains missing values")
    
    # Sort by time if not already sorted
    if not df[time_col].is_monotonic_increasing:
        df = df.sort_values(time_col)
    
    # Create baseTs object
    ts = baseTs(
        data=df[data_col].values,
        times=df[time_col].values,
        signal_name=signal_name if signal_name is not None else data_col,
        freq=freq,
        ts_offset=ts_offset if ts_offset is not None else np.nan
    )
    
    return ts


class baseTs(ArrayCompatMixin):
    """
    Basic data class to hold a timeseries and data.
    
    Now supports dual backends: numpy arrays (legacy) and pandas Series (new).
    
    Args:
        data (np.array): The actual observational data.
        times (np.array): The timestamps corresponding to the data.
        freq (float, optional): The frequency of data collection. Defaults to np.nan.
        use_series (bool, optional): Use pandas Series backend. Defaults to False.
        backend (str, optional): Explicit backend choice ('numpy' or 'series').

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
                 last_process: str = "",
                 use_series: bool = None,
                 backend: str = None,
                 ):
        
        """
        Initialize the baseTs object with dual backend support.
        """
        
        # Determine backend to use
        if backend is not None:
            if backend not in ['numpy', 'series']:
                raise ValueError(f"Invalid backend: {backend}. Must be 'numpy' or 'series'")
            self._backend = backend
        elif use_series is not None:
            self._backend = 'series' if use_series else 'numpy'
        else:
            self._backend = 'series' if BackendManager.should_use_series() else 'numpy'
        
        # Initialize based on backend
        if self._backend == 'series':
            self._init_series_backend(
                data, times, freq, ts_offset, is_filtered, is_interpolated,
                is_uniform_grid, is_outlier_filtered, has_timestamp_offset,
                filtered_indices, lowess_fit, signal_name, history, last_process
            )
        else:
            self._init_numpy_backend(
                data, times, freq, ts_offset, is_filtered, is_interpolated,
                is_uniform_grid, is_outlier_filtered, has_timestamp_offset,
                filtered_indices, lowess_fit, signal_name, history, last_process
            )

    def _init_numpy_backend(self, data, times, freq, ts_offset, is_filtered,
                           is_interpolated, is_uniform_grid, is_outlier_filtered,
                           has_timestamp_offset, filtered_indices, lowess_fit,
                           signal_name, history, last_process):
        """Initialize with legacy numpy backend."""
        self._data = data
        self._times = times
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
                self._times = np.arange(0, len(data)) / freq
            else:
                raise ValueError("You must provide either a times array or a frequency")
        else:
            self._times = times

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
        self.outlier_filter = LowessOutlierFilter()

    def _init_series_backend(self, data, times, freq, ts_offset, is_filtered,
                            is_interpolated, is_uniform_grid, is_outlier_filtered,
                            has_timestamp_offset, filtered_indices, lowess_fit,
                            signal_name, history, last_process):
        """Initialize with pandas Series backend."""
        from .series import TimeSeriesData
        
        # Handle times array
        if times is None:
            if freq is not np.nan:
                times = np.arange(0, len(data)) / freq
            else:
                raise ValueError("You must provide either a times array or a frequency")
        
        # Validate time index
        validate_time_index(times)
        
        # Create TimeSeriesData object
        if history is None:
            history = [f"Created baseTs object with {len(data)} samples"]
        
        self._series = TimeSeriesData(
            data=data,
            index=times,
            freq=freq if freq is not np.nan else None,
            signal_name=signal_name
        )
        
        # Set metadata
        self._series.is_filtered = is_filtered
        self._series.is_interpolated = is_interpolated
        self._series.is_uniform_grid = is_uniform_grid
        self._series.is_outlier_filtered = is_outlier_filtered
        self._series.has_timestamp_offset = has_timestamp_offset
        self._series.filtered_indices = filtered_indices
        self._series.lowess_fit = lowess_fit
        self._series.last_process = last_process
        self._series.history = history
        # self.last_process = last_process

        
        # Handle timestamp offset
        if ts_offset is not np.nan:
            self._series.ts_offset = ts_offset
            self._series.has_timestamp_offset = True
        else:
            self._series.ts_offset = 0
            self._series.has_timestamp_offset = False
        
        # Calculate frequency if not provided
        if freq is np.nan:
            self._series.freq = self._series._calculate_effective_frequency()
        
        # instantiate outlier filter w/ default parameters
        self.outlier_filter = LowessOutlierFilter()

    # Backend Management Properties
    @property
    def backend(self) -> str:
        """Get the current backend type."""
        return self._backend
    
    @property
    def is_series_backend(self) -> bool:
        """Check if using Series backend."""
        return self._backend == 'series'
    
    @property
    def is_numpy_backend(self) -> bool:
        """Check if using numpy backend."""
        return self._backend == 'numpy'

    # Compatibility Properties - Override ArrayCompatMixin for better integration
    @property
    def data(self) -> np.ndarray:
        """
        Get the data values as numpy array (backward compatibility).
        
        Returns:
            Numpy array of data values
        """
        if self._backend == 'series':
            return self._series.values
        else:
            return self._data
    
    @data.setter
    def data(self, value: np.ndarray):
        """
        Set the data values (backward compatibility).
        
        Args:
            value: New data array
        """
        if self._backend == 'series':
            # Check if lengths match
            if len(value) == len(self._series.index):
                # Same length, can preserve index
                old_index = self._series.index
            else:
                # Different length, create new index with same time range
                start_time = self._series.index[0] if len(self._series) > 0 else 0
                end_time = self._series.index[-1] if len(self._series) > 0 else len(value)-1
                old_index = np.linspace(start_time, end_time, len(value))
            
            # Create new Series with new data
            old_metadata = {}
            for attr in self._series._metadata:
                if hasattr(self._series, attr):
                    old_metadata[attr] = getattr(self._series, attr)
            
            self._series = self._series.__class__(
                value, 
                index=old_index, 
                freq=old_metadata.get('freq', self._series.freq),
                signal_name=old_metadata.get('signal_name', self._series.signal_name)
            )
            
            # Restore metadata
            for attr, val in old_metadata.items():
                if attr not in ['freq', 'signal_name']:
                    setattr(self._series, attr, val)
        else:
            self._data = value
    
    @property
    def times(self) -> np.ndarray:
        """
        Get the time values as numpy array (backward compatibility).
        
        Returns:
            Numpy array of time values
        """
        if self._backend == 'series':
            return self._series.index.values
        else:
            return self._times
    
    @times.setter
    def times(self, value: np.ndarray):
        """
        Set the time values (backward compatibility).
        
        Args:
            value: New time array
        """
        if self._backend == 'series':
            # Update the Series with new index, preserving data
            self._series.index = pd.Index(value)
            # Recalculate frequency
            self._series.freq = self._series._calculate_effective_frequency()
        else:
            self._times = value
            # Recalculate frequency
            if len(value) > 1:
                self.freq = len(value) / (value[-1] - value[0])

    # Metadata Properties - Use backend-appropriate storage
    @property
    def signal_name(self) -> str:
        """Get signal name."""
        if self._backend == 'series':
            return self._series.signal_name
        else:
            return getattr(self, '_signal_name', "")
    
    @signal_name.setter
    def signal_name(self, value: str):
        """Set signal name."""
        if self._backend == 'series':
            self._series.signal_name = value.upper()
        else:
            self._signal_name = value.upper()

    @property
    def freq(self) -> float:
        """Get sampling frequency."""
        if self._backend == 'series':
            return self._series.freq
        else:
            return getattr(self, '_freq', np.nan)
    
    @freq.setter
    def freq(self, value: float):
        """Set sampling frequency."""
        if self._backend == 'series':
            self._series.freq = value
        else:
            self._freq = value

    @property
    def history(self) -> list:
        """Get processing history."""
        if self._backend == 'series':
            return self._series.history
        else:
            return getattr(self, '_history', [])
    
    @history.setter
    def history(self, value: list):
        """Set processing history."""
        if self._backend == 'series':
            self._series.history = value
        else:
            self._history = value

    @property
    def last_process(self) -> str:
        """Get last process."""
        if self._backend == 'series':
            return self._series.last_process
        else:
            return getattr(self, '_last_process', "")
        
    @last_process.setter
    def last_process(self, value: str):
        """Set last process."""
        if self._backend == 'series':
            self._series.last_process = value
        else:
            self._last_process = value
            

    def _get_metadata_attr(self, attr_name, default=None):
        """Helper to get metadata attributes from appropriate backend."""
        if self._backend == 'series':
            return getattr(self._series, attr_name, default)
        else:
            return getattr(self, attr_name, default)
    
    def _set_metadata_attr(self, attr_name, value):
        """Helper to set metadata attributes on appropriate backend."""
        if self._backend == 'series':
            setattr(self._series, attr_name, value)
        else:
            setattr(self, attr_name, value)

    def _update_history_and_process(self, hist_msg: str, last_process: str):
        """Helper method to update history and last_process."""
        self.history.append(hist_msg)
        self._set_metadata_attr('last_process', last_process)

    def _update_flags(self, **flags):
        """Helper method to update object flags."""
        for flag_name, flag_value in flags.items():
            self._set_metadata_attr(flag_name, flag_value)

    def _process_inplace(self, func, *args, **kwargs):
        """Helper method to process data in-place."""
        result = func(self.data, *args, **kwargs)
        self.data = result
        return self

    def _process_new(self, func, *args, **kwargs):
        """Helper method to process data and return new object."""
        new_obj = self.copy()
        result = func(new_obj.data, *args, **kwargs)
        new_obj.data = result
        return new_obj

    def _process_with_flags(self, func, hist_msg: str, last_process: str, inplace: bool = False, **flags):
        """Helper method to process data with history and flag updates."""
        if inplace:
            result = self._process_inplace(func)
            self._update_history_and_process(hist_msg, last_process)
            self._update_flags(**flags)
            return self
        else:
            result = self._process_new(func)
            result._update_history_and_process(hist_msg, last_process)
            result._update_flags(**flags)
            return result

    def _create_new_with_data(self, new_data: np.ndarray, new_times: np.ndarray = None, 
                             preserve_metadata: bool = True, **kwargs) -> "baseTs":
        """
        Create a new baseTs object with new data, preserving backend and metadata.
        
        Args:
            new_data: New data array
            new_times: New time array (optional, uses existing if None)
            preserve_metadata: Whether to copy metadata from current object
            **kwargs: Additional parameters for new object
            
        Returns:
            New baseTs object with same backend as current object
        """
        if new_times is None:
            new_times = self.times
            
        # Create new object with same backend
        new_kwargs = {
            'backend': self._backend,
            'freq': self.freq,
            'signal_name': self.signal_name
        }
        new_kwargs.update(kwargs)
        
        new_obj = baseTs(new_data, new_times, **new_kwargs)
        
        if preserve_metadata:
            # Copy metadata
            metadata_attrs = ['is_filtered', 'is_interpolated', 'is_uniform_grid', 
                            'is_outlier_filtered', 'has_timestamp_offset', 'ts_offset',
                            'filtered_indices', 'lowess_fit', 'last_process']
            
            for attr in metadata_attrs:
                if hasattr(self, attr):
                    new_obj._set_metadata_attr(attr, self._get_metadata_attr(attr))
            
            # Copy history (make a copy to avoid reference issues)
            new_obj.history = self.history.copy()
        
        return new_obj

    def _enhanced_process_with_flags(self, func, hist_msg: str, last_process: str, 
                                   inplace: bool = False, modify_times: bool = False, 
                                   **flags) -> "baseTs":
        """
        Enhanced processing method that handles both data and time modifications.
        
        Args:
            func: Function to apply to data (should return data or (data, times) tuple)
            hist_msg: History message
            last_process: Last process identifier
            inplace: Whether to modify in place
            modify_times: Whether the function modifies times
            **flags: Metadata flags to update
            
        Returns:
            Processed baseTs object
        """
        result = func(self.data)
        
        if modify_times:
            if isinstance(result, tuple) and len(result) == 2:
                new_data, new_times = result
            else:
                raise ValueError("Function must return (data, times) tuple when modify_times=True")
        else:
            new_data = result
            new_times = None
        
        if inplace:
            self.data = new_data
            if new_times is not None:
                self.times = new_times
            self._update_history_and_process(hist_msg, last_process)
            self._update_flags(**flags)
            return self
        else:
            new_obj = self._create_new_with_data(new_data, new_times)
            new_obj._update_history_and_process(hist_msg, last_process)
            new_obj._update_flags(**flags)
            return new_obj

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
    
    def zscale(self, inplace: bool = False) -> "baseTs":
        """
        Z-scale the data (zero mean, unit variance).
        
        Args:
            inplace: If True, modifies existing object. Otherwise returns new object.
            
        Returns:
            Z-scaled baseTs object
        """
        def zscale_func(data):
            return (data - data.mean()) / data.std()

        return self._enhanced_process_with_flags(
            func=zscale_func,
            hist_msg="Z-scaled the data",
            last_process="_zscale",
            inplace=inplace
        )

    def normalize_range(self, target_min: float = 0.0, target_max: float = 1.0, 
                       inplace: bool = False) -> "baseTs":
        """
        Normalize the data to a specified range.
        
        Args:
            target_min: Minimum value of target range
            target_max: Maximum value of target range
            inplace: If True, modifies existing object. Otherwise returns new object.
            
        Returns:
            Normalized baseTs object
        """
        def normalize_func(data):
            data_min, data_max = data.min(), data.max()
            data_range = data_max - data_min
            if data_range == 0:
                return np.full_like(data, (target_min + target_max) / 2)
            target_range = target_max - target_min
            return target_min + (data - data_min) * target_range / data_range

        return self._enhanced_process_with_flags(
            func=normalize_func,
            hist_msg=f"Normalized data to range [{target_min}, {target_max}]",
            last_process="_normalize",
            inplace=inplace
        )

    def center(self, inplace: bool = False) -> "baseTs":
        """
        Center the data around zero (remove mean).
        
        Args:
            inplace: If True, modifies existing object. Otherwise returns new object.
            
        Returns:
            Centered baseTs object
        """
        def center_func(data):
            return data - data.mean()

        return self._enhanced_process_with_flags(
            func=center_func,
            hist_msg="Centered data (removed mean)",
            last_process="_center",
            inplace=inplace
        )

    def scale(self, factor: float, inplace: bool = False) -> "baseTs":
        """
        Scale the data by a constant factor.
        
        Args:
            factor: Scaling factor
            inplace: If True, modifies existing object. Otherwise returns new object.
            
        Returns:
            Scaled baseTs object
        """
        def scale_func(data):
            return data * factor

        return self._enhanced_process_with_flags(
            func=scale_func,
            hist_msg=f"Scaled data by factor {factor}",
            last_process=f"_scale_{factor}",
            inplace=inplace
        )

    def abs(self, inplace: bool = False) -> "baseTs":
        """
        Take absolute value of the data.
        
        Args:
            inplace: If True, modifies existing object. Otherwise returns new object.
            
        Returns:
            Absolute value baseTs object
        """
        def abs_func(data):
            return np.abs(data)

        return self._enhanced_process_with_flags(
            func=abs_func,
            hist_msg="Took absolute value of data",
            last_process="_abs",
            inplace=inplace
        )
    
    def interpto_hz(self, new_freq: int, kind: str = 'linear', inplace: bool = False) -> "baseTs":
        """
        Interpolate the times to a new frequency.

        Args:
            new_freq (int): The desired new frequency of the interpolated times.
            kind (str, optional): The type of interpolation to use. Defaults to 'linear'.
            inplace (bool, optional): If True, modifies existing object. Otherwise returns a new object. Defaults to False.

        Returns:
            baseTs: Interpolated data at new frequency
        """
        def interp_func(data):
            new_ts = np.linspace(self.times[0], self.times[-1], int(self.duration() * new_freq))
            f1 = interpolate.interp1d(self.times, data, kind=kind)
            return f1(new_ts), new_ts, new_freq
            
        def process_result(result):
            data, times, freq = result
            if inplace:
                self.data = data
                self.times = times
                self.freq = freq
                self.is_interpolated = True
                self.is_uniform_grid = True
                return self
            else:
                new_obj = self.copy()
                new_obj.data = data
                new_obj.times = times
                new_obj.freq = freq
                new_obj.is_interpolated = True
                new_obj.is_uniform_grid = True
                return new_obj
                
        result = interp_func(self.data)
        processed = process_result(result)
        processed._update_history_and_process(
            hist_msg=f"Interpolated to {new_freq}Hz",
            last_process=f"_interpto_{new_freq}Hz"
        )
        return processed

    def interpto_samples(self, new_len: int, kind: str = 'linear', inplace: bool = False) -> "baseTs":
        """
        Interpolate the times to a new length.

        Args:
            new_len (int): The desired new length of the interpolated times.
            kind (str, optional): The type of interpolation to use. Defaults to 'linear'.
            inplace (bool, optional): If True, modifies existing object. Otherwise returns a new object. Defaults to False.

        Returns:
            baseTs: Interpolated data
        """
        def interp_func(data):
            new_ts = np.linspace(self.times[0], self.times[-1], new_len)
            new_freq = new_len / self.duration()
            f1 = interpolate.interp1d(self.times, data, kind=kind)
            return f1(new_ts), new_ts, new_freq
            
        def process_result(result):
            data, times, freq = result
            if inplace:
                self.data = data
                self.times = times
                self.freq = freq
                self.is_interpolated = True
                self.is_uniform_grid = True
                return self
            else:
                new_obj = self.copy()
                new_obj.data = data
                new_obj.times = times
                new_obj.freq = freq
                new_obj.is_interpolated = True
                new_obj.is_uniform_grid = True
                return new_obj
                
        result = interp_func(self.data)
        processed = process_result(result)
        processed._update_history_and_process(
            hist_msg=f"Interpolated to {new_len} samples",
            last_process=f"_interpto_{new_len}samples"
        )
        return processed

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
        def trim_func(data):
            if start_val != np.nan:
                start_idx = find_closest(start_val, self.times).location
            else:
                start_idx = 0
            if end_val != -1:
                end_idx = find_closest(end_val, self.times).location
            else:
                end_idx = -1
            return data[start_idx:end_idx], self.times[start_idx:end_idx]
            
        def process_result(result):
            data, times = result
            if inplace:
                self.data = data
                self.times = times
                return self
            else:
                new_obj = self.copy()
                new_obj.data = data
                new_obj.times = times
                return new_obj
                
        result = trim_func(self.data)
        processed = process_result(result)
        processed._update_history_and_process(
            hist_msg=f"Trimmed data to [{start_val}:{end_val}]",
            last_process=f"_trimto_[{start_val}:{end_val}]"
        )
        return processed

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
        if inplace is False:
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
        
    
    def notch_at(self, cutoff_hz: float, order: int = 5, inplace: bool = False) -> "baseTs":
        """
        Apply a notch filter at the specified frequency.
        
        Args:
            cutoff_hz: Notch frequency in Hz
            order: Filter order
            inplace: If True, modifies existing object. Otherwise returns new object.
            
        Returns:
            Notch filtered baseTs object
        """
        def notch_func(data):
            return notch_filter(data, cutoff_hz, self.freq, order)
            
        return self._enhanced_process_with_flags(
            func=notch_func,
            hist_msg=f"Notch filtered at {cutoff_hz} Hz",
            last_process=f"_notch_{cutoff_hz}Hz",
            inplace=inplace,
            is_filtered=True
        )
        
    def highpass_at(self, cutoff: float, order: int = 5, inplace: bool = False) -> "baseTs":
        """
        Apply a highpass filter at the specified cutoff frequency.
        
        Args:
            cutoff: Highpass cutoff frequency in Hz
            order: Filter order
            inplace: If True, modifies existing object. Otherwise returns new object.
            
        Returns:
            Highpass filtered baseTs object
        """
        def highpass_func(data):
            return highpass_filter(data, cutoff, self.freq, order)
            
        return self._enhanced_process_with_flags(
            func=highpass_func,
            hist_msg=f"Highpass filtered at {cutoff} Hz",
            last_process=f"_hp_{cutoff}Hz",
            inplace=inplace,
            is_filtered=True
        )
        
    def lowpass_at(self, cutoff: float, order: int = 5, inplace: bool = False) -> "baseTs":
        """
        Apply a lowpass filter at the specified cutoff frequency.
        
        Args:
            cutoff: Lowpass cutoff frequency in Hz
            order: Filter order
            inplace: If True, modifies existing object. Otherwise returns new object.
            
        Returns:
            Lowpass filtered baseTs object
        """
        def lowpass_func(data):
            return lowpass_filter(data, cutoff, self.freq, order)
            
        return self._enhanced_process_with_flags(
            func=lowpass_func,
            hist_msg=f"Lowpass filtered at {cutoff} Hz",
            last_process=f"_lp_{cutoff}Hz",
            inplace=inplace,
            is_filtered=True
        )

    def gauss_filter(self, sigma: float = 1, inplace: bool = False) -> "baseTs":
        """
        Apply a Gaussian filter to the data.
        
        Args:
            sigma: Standard deviation for Gaussian kernel
            inplace: If True, modifies existing object. Otherwise returns new object.
            
        Returns:
            Gaussian filtered baseTs object
        """
        def gauss_func(data):
            return gaussian_filter(data, sigma)
            
        return self._enhanced_process_with_flags(
            func=gauss_func,
            hist_msg=f"Applied Gaussian filter with sigma={sigma}",
            last_process=f"_gauss_{sigma}",
            inplace=inplace,
            is_filtered=True
        )
    
    def bandpass_at(self,
                    hp_hz: float = 0.01,
                    lp_hz: float = 0.1,
                    inplace: bool = False,
                    reset_mean: bool = True) -> "baseTs":
        """
        Apply a bandpass filter to the signal at specified low-pass and high-pass frequencies.

        Args:
            hp_hz: High-pass cutoff frequency in Hz
            lp_hz: Low-pass cutoff frequency in Hz
            inplace: If True, modifies existing object. Otherwise returns new object.
            reset_mean: If True, resets the mean of the filtered data to the mean of the original data

        Returns:
            Bandpass filtered baseTs object
        """
        def bandpass_func(data):
            return bandpass_filter(
                data,
                hp_hz=hp_hz,
                lp_hz=lp_hz,
                sample_Hz=self.freq,
                reset_mean=reset_mean
            )
            
        return self._enhanced_process_with_flags(
            func=bandpass_func,
            hist_msg=f"Bandpass filtered at {lp_hz} Hz and {hp_hz} Hz",
            last_process=f"_bp_{lp_hz}:{hp_hz}Hz",
            inplace=inplace,
            is_filtered=True
        )

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
        filt = bandpass_filter(self.data, highpass_freq=hp_freq, lowpass_freq=lp_freq, sampling_freq=self.freq)
        hist_msg = f"Butterworth pass filtered at {hp_freq} Hz and {lp_freq} Hz"
        last_process = "_btrp_" + str(lp_freq) + ":" + str(hp_freq) + "Hz"
        if inplace is True:
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
                        use_median: bool = True,
                        tails: Union[str, TailType] = TailType.BOTH,
                        num_fits: int = 25) -> "baseTs":
        """
        Set outlier filter parameters.
        
        Parameters
        ----------
        params : dict, optional
            Dictionary of parameter values. If provided, overrides individual parameters.
            Valid keys are: 'z_threshold', 'frac', 'max_iterations', 'interpolation_method',
            'order', 'use_median', 'tails', 'num_fits'
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
        tails : Union[str, TailType], default=TailType.BOTH
            Which tails to process for outlier detection. Can be 'BOTH', 'UPPER', 'LOWER',
            or a TailType enum member.
        num_fits : int, default=25
            Number of LOWESS fits to perform.
        
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
                'use_median': bool,
                'tails': (str, TailType),
                'num_fits': int
            }
            
            # Validate and set parameters from dictionary
            for param_name, param_type in valid_params.items():
                if param_name in params:
                    value = params[param_name]
                    # Type checking
                    if param_name == 'tails':
                        if isinstance(value, str):
                            try:
                                value = TailType[value.upper()]
                            except KeyError:
                                raise ValueError(f"Invalid string value for tails: {value}. Must be 'BOTH', 'UPPER', or 'LOWER'.")
                        elif not isinstance(value, TailType):
                             raise ValueError(f"Invalid type for tails. Expected str or TailType, got {type(value)}.")
                    elif not isinstance(value, param_type):
                        try:
                            value = param_type(value)
                        except ValueError:
                            raise ValueError(f"Invalid type for {param_name}. Expected {param_type.__name__}")
                    setattr(self.outlier_filter.config, param_name, value)
        else:
            # Use individual parameters
            self.outlier_filter.config.z_threshold = z_threshold
            self.outlier_filter.config.max_iterations = max_iterations
            self.outlier_filter.config.frac = frac
            self.outlier_filter.config.interpolation_method = interpolation_method
            self.outlier_filter.config.order = order
            self.outlier_filter.config.use_median = use_median
            if isinstance(tails, str):
                try:
                    self.outlier_filter.config.tails = TailType[tails.upper()]
                except KeyError:
                    raise ValueError(f"Invalid string value for tails: {tails}. Must be 'BOTH', 'UPPER', or 'LOWER'.")
            else: # it's already a TailType enum
                self.outlier_filter.config.tails = tails
            self.outlier_filter.config.num_fits = num_fits
        
        hist_msg = f"Set new outlier filter parameters: {self.outlier_filter.config.__dict__}"
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
        return self.outlier_filter.config.__dict__
        
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
        hist_msg = f"Filtered outliers with lowess: {self.outlier_filter.config.__dict__}"
        last_process = "_outfilt"
                   
        if inplace is True:
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
        
        Args:
            window_length: Length of the filter window (must be odd)
            polyorder: Order of the polynomial fit
            inplace: If True, modifies existing object. Otherwise returns new object.
            
        Returns:
            Savitzky-Golay filtered baseTs object
        """
        def sg_func(data):
            return sg_filter(data, window_length, polyorder)
            
        return self._enhanced_process_with_flags(
            func=sg_func,
            hist_msg=f"Applied Savitzky-Golay filter wl={window_length}, polyorder={polyorder}",
            last_process="_sgFilter",
            inplace=inplace,
            is_filtered=True
        )
        
    def interpolate_missing(self, inplace: bool = False) -> "baseTs":
        """
        Interpolate missing values in the data.
        """
        def interp_func(data):
            return interpolate_missing_values(self, inplace=inplace)
            
        def process_result(result):
            if inplace:
                self.data = result.data
                self.times = result.times
                return self
            else:
                return result
                
        result = interp_func(self.data)
        processed = process_result(result)
        processed._update_history_and_process(
            hist_msg="Interpolated missing values in timeseries",
            last_process="_interp"
        )
        return processed
    
    def diff_ts(self, zeropad: bool = False, inplace: bool = False) -> "baseTs":
        """
        Compute the first difference of the timeseries.
        """
        def diff_func(data):
            result = diff(self, zeropad=zeropad)
            if result is None:
                raise ValueError("Failed to compute first difference of timeseries")
            return result.data, result.times
            
        def process_result(result):
            data, times = result
            if inplace:
                self.data = data
                self.times = times
                return self
            else:
                new_obj = self.copy()
                new_obj.data = data
                new_obj.times = times
                return new_obj
                
        result = diff_func(self)
        processed = process_result(result)
        processed._update_history_and_process(
            hist_msg="Computed first difference of timeseries",
            last_process="_diff"
        )
        return processed

    def dediff_ts(self, inplace: bool = False) -> "baseTs":
        """
        Compute the cumulative sum of the timeseries.
        """
        # Assuming utils.dediff(self) returns a baseTs object
        # containing the dedifferenced data and corresponding times.
        dediffed_result_ts = dediff(self)

        if dediffed_result_ts is None:
            raise ValueError("Failed to compute cumulative sum of timeseries (dediff returned None)")

        hist_msg = "Computed cumulative sum of timeseries"
        last_process = "_dediff"

        if inplace:
            self.data = dediffed_result_ts.data
            self.times = dediffed_result_ts.times
            # If dediff might change frequency or other relevant attributes, update them here.
            # For example:
            # if hasattr(dediffed_result_ts, 'freq'):
            #     self.freq = dediffed_result_ts.freq
            # Add any other attributes from dediffed_result_ts that should be copied.
            
            self._update_history_and_process(hist_msg, last_process)
            # self._update_flags(...) # Call if specific flags need to be set/updated
            return self
        else:
            new_obj = self.copy()  # Start with a copy of the original state
            new_obj.data = dediffed_result_ts.data
            new_obj.times = dediffed_result_ts.times
            # If dediff might change frequency or other relevant attributes, update them here on new_obj.
            # For example:
            # if hasattr(dediffed_result_ts, 'freq'):
            #     new_obj.freq = dediffed_result_ts.freq
            # Add any other attributes from dediffed_result_ts that should be copied to new_obj.

            new_obj._update_history_and_process(hist_msg, last_process)
            # new_obj._update_flags(...) # Call if specific flags need to be set/updated
            return new_obj

    # Enhanced Pandas-Powered Methods
    
    def rolling_mean(self, window: int, center: bool = True, inplace: bool = False) -> "baseTs":
        """
        Apply a rolling mean to the data.
        
        Args:
            window: Size of the rolling window (number of samples)
            center: Whether to center the window
            inplace: If True, modifies existing object. Otherwise returns new object.
            
        Returns:
            Rolling mean baseTs object
        """
        if self._backend == 'series':
            # Use pandas rolling capabilities
            rolling_result = self._series.rolling(window, center=center).mean()
            # Remove NaN values and corresponding times
            valid_mask = ~rolling_result.isna()
            new_data = rolling_result[valid_mask].values
            new_times = rolling_result[valid_mask].index.values
        else:
            # Fallback for numpy backend
            import pandas as pd
            temp_series = pd.Series(self.data)
            rolling_result = temp_series.rolling(window, center=center).mean()
            valid_mask = ~rolling_result.isna()
            new_data = rolling_result[valid_mask].values
            new_times = self.times[valid_mask]
        
        if inplace:
            self.data = new_data
            self.times = new_times
            self._update_history_and_process(
                f"Applied rolling mean with window={window}",
                f"_rolling_mean_{window}"
            )
            return self
        else:
            new_obj = self._create_new_with_data(new_data, new_times)
            new_obj._update_history_and_process(
                f"Applied rolling mean with window={window}",
                f"_rolling_mean_{window}"
            )
            return new_obj

    def rolling_std(self, window: int, center: bool = True, inplace: bool = False) -> "baseTs":
        """
        Apply a rolling standard deviation to the data.
        """
        if self._backend == 'series':
            rolling_result = self._series.rolling(window, center=center).std()
            valid_mask = ~rolling_result.isna()
            new_data = rolling_result[valid_mask].values
            new_times = rolling_result[valid_mask].index.values
        else:
            # Fallback for numpy backend
            import pandas as pd
            temp_series = pd.Series(self.data)
            rolling_result = temp_series.rolling(window, center=center).std()
            valid_mask = ~rolling_result.isna()
            new_data = rolling_result[valid_mask].values
            new_times = self.times[valid_mask]

        if inplace:
            self.data = new_data
            self.times = new_times
            self._update_history_and_process(
                f"Applied rolling standard deviation with window={window}",
                f"_rolling_std_{window}"
            )
            return self
        else:
            new_obj = self._create_new_with_data(new_data, new_times)   
            new_obj._update_history_and_process(
                f"Applied rolling standard deviation with window={window}",
                f"_rolling_std_{window}"
            )
            return new_obj
        
    def rolling_median(self, window: int, center: bool = True, inplace: bool = False) -> "baseTs":
        """
        Apply a rolling median to the data.
        """
        if self._backend == 'series':
            rolling_result = self._series.rolling(window, center=center).median()
            valid_mask = ~rolling_result.isna() 
            new_data = rolling_result[valid_mask].values
            new_times = rolling_result[valid_mask].index.values
        else:
            # Fallback for numpy backend
            import pandas as pd
            temp_series = pd.Series(self.data)  
            rolling_result = temp_series.rolling(window, center=center).median()
            valid_mask = ~rolling_result.isna()
            new_data = rolling_result[valid_mask].values
            new_times = self.times[valid_mask]

        if inplace:
            self.data = new_data
            self.times = new_times
            self._update_history_and_process(
                f"Applied rolling median with window={window}",
                f"_rolling_median_{window}"
            )
            return self
        else:
            new_obj = self._create_new_with_data(new_data, new_times)   
            new_obj._update_history_and_process(
                f"Applied rolling median with window={window}",
                f"_rolling_median_{window}"
            )
            return new_obj
        
    def rolling_max(self, window: int, center: bool = True, inplace: bool = False) -> "baseTs":
        """
        Apply a rolling maximum to the data.
        """
        if self._backend == 'series':
            rolling_result = self._series.rolling(window, center=center).max()
            valid_mask = ~rolling_result.isna() 
            new_data = rolling_result[valid_mask].values
            new_times = rolling_result[valid_mask].index.values
        else:
            # Fallback for numpy backend
            import pandas as pd
            temp_series = pd.Series(self.data)      
            rolling_result = temp_series.rolling(window, center=center).max()
            valid_mask = ~rolling_result.isna()
            new_data = rolling_result[valid_mask].values
            new_times = self.times[valid_mask]

        if inplace: 
            self.data = new_data
            self.times = new_times
            self._update_history_and_process(
                f"Applied rolling maximum with window={window}",
                f"_rolling_max_{window}"
            )   
            return self
        else:
            new_obj = self._create_new_with_data(new_data, new_times)   
            new_obj._update_history_and_process(
                f"Applied rolling maximum with window={window}",
                f"_rolling_max_{window}"
            )
            return new_obj
        
    def rolling_min(self, window: int, center: bool = True, inplace: bool = False) -> "baseTs":
        """
        Apply a rolling minimum to the data.    
        """
        if self._backend == 'series':
            rolling_result = self._series.rolling(window, center=center).min()
            valid_mask = ~rolling_result.isna() 
            new_data = rolling_result[valid_mask].values
            new_times = rolling_result[valid_mask].index.values
        else:
            # Fallback for numpy backend
            import pandas as pd
            temp_series = pd.Series(self.data)      
            rolling_result = temp_series.rolling(window, center=center).min()
            valid_mask = ~rolling_result.isna()
            new_data = rolling_result[valid_mask].values
            new_times = self.times[valid_mask]

        if inplace:
            self.data = new_data
            self.times = new_times
            self._update_history_and_process(
                f"Applied rolling minimum with window={window}",
                f"_rolling_min_{window}"
            )
            return self
        else:
            new_obj = self._create_new_with_data(new_data, new_times)       
            new_obj._update_history_and_process(
                f"Applied rolling minimum with window={window}",
                f"_rolling_min_{window}"
            )
            return new_obj
        
    def time_slice(self, start_time: float = None, end_time: float = None, 
                  inplace: bool = False) -> "baseTs":
        """
        Slice the time series between start and end times.
        
        Args:
            start_time: Start time (if None, uses beginning)
            end_time: End time (if None, uses end)
            inplace: If True, modifies existing object. Otherwise returns new object.
            
        Returns:
            Time-sliced baseTs object
        """
        if self._backend == 'series':
            # Use pandas time-based indexing
            if start_time is None:
                start_time = self._series.index[0]
            if end_time is None:
                end_time = self._series.index[-1]
            
            # Use pandas boolean indexing for time range
            mask = (self._series.index >= start_time) & (self._series.index <= end_time)
            sliced_series = self._series[mask]
            new_data = sliced_series.values
            new_times = sliced_series.index.values
        else:
            # Use numpy indexing
            mask = np.ones(len(self.times), dtype=bool)
            if start_time is not None:
                mask &= (self.times >= start_time)
            if end_time is not None:
                mask &= (self.times <= end_time)
            
            new_data = self.data[mask]
            new_times = self.times[mask]
        
        if inplace:
            self.data = new_data
            self.times = new_times
            self._update_history_and_process(
                f"Time sliced from {start_time} to {end_time}",
                f"_time_slice"
            )
            return self
        else:
            new_obj = self._create_new_with_data(new_data, new_times)
            new_obj._update_history_and_process(
                f"Time sliced from {start_time} to {end_time}",
                f"_time_slice"
            )
            return new_obj

    def get_statistics(self) -> dict:
        """
        Get comprehensive statistics for the time series.
        
        Returns:
            Dictionary containing various statistics
        """
        data = self.data
        
        stats = {
            'count': len(data),
            'mean': np.mean(data),
            'std': np.std(data),
            'min': np.min(data),
            'max': np.max(data),
            'median': np.median(data),
            'q25': np.percentile(data, 25),
            'q75': np.percentile(data, 75),
            'duration': self.duration(),
            'frequency': self.freq,
            'sample_rate': len(data) / self.duration() if self.duration() > 0 else 0
        }
        
        return stats
    
    # Utility functions
    
    def compute_fft_power(self, max_rate: float = np.nan, demean: bool = True, scale_power: bool = True) -> tuple:
        """
        Compute the FFT power of the timeseries.
        """
        return compute_fft_power(self, max_rate=max_rate, demean=demean, scale_power=scale_power)

    def get_closest_time(self, sec: float) -> ClosestMatch:
        """
        Find the closest time in the timeseries to a target time in seconds.
        
        Args:
            sec: Target time in seconds
            
        Returns:
            ClosestMatch object containing:
                - location: the index of the closest time
                - value: the value of the closest time
                - abs_err: the difference between the closest time and the target time in seconds
                - target: the original target time
        """
        return find_closest_time(self, sec)

    def get_peak_freq(self, num_pks: int = 1) -> float:
        """
        Compute the peak frequency of the timeseries.
        Returns the frequency of the peak power.
        """
        pk_freq = get_peak_freq(self, num_pks=num_pks)  
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
             show: bool = False) -> plt.Axes:
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
                    start_idx: int = 0,
                    end_idx: int = -1,
                    show: bool = False) -> plt.Axes:
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
                start_idx=start_idx,
                end_idx=end_idx,
                show=show)

    def plot_hist(self,
                  ax = None,
                  title: str = None,
                  xlabel: str = None,
                  show: bool = False,
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
    
    def lag_plot(self, lag: Union[int, float], lag_unit: str = "index", ax: Optional[plt.Axes] = None, show: bool = False) -> plt.Axes:
        """
        Plot a lag plot of the timeseries.
        """
        # Import plotting here to avoid circular imports
        from .plotting import lag_plot  
        return lag_plot(self, lag=lag, lag_unit=lag_unit, ax=ax, show=show)

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
        from .utils import round_values
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
        df = pd.DataFrame({"times": self.times, "data": self.data})
        if set_index:  # set times as index if desired ;
            df.set_index("times", inplace=True)
        return df

    def lowess_detrend(self, frac: float = 0.25, inplace: bool = False) -> "baseTs":
        """
        Detrend the data using a lowess fit.
        """
        def detrend_func(data):
            lowess_fit = self.set_outlier_filter(frac=frac)
            self.filter_outliers(inplace=True)
            # STANEDIT
            return data - self.lowess_fit, self.lowess_fit
            
        def process_result(result):
            data, lowess_fit = result
            if inplace:
                self.data = data
                self.lowess_fit = lowess_fit
                return self
            else:
                new_obj = self.copy()
                new_obj.data = data
                new_obj.lowess_fit = lowess_fit
                return new_obj
                
        result = detrend_func(self.data)
        processed = process_result(result)
        processed._update_history_and_process(
            hist_msg=f"Detrended with lowess fit frac={frac}",
            last_process="_lowess_detrend"
        )
        return processed
