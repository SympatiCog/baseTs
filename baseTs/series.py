# -*- coding: utf-8 -*-
"""
Pandas Series subclass for time series analysis.
Created for baseTs pandas migration.
@author: stan@sympaticog.com
"""

from __future__ import annotations
from typing import Optional, Union, Any, Dict, List
import numpy as np
import pandas as pd
from numpy.typing import NDArray


class TimeSeriesData(pd.Series):
    """
    Pandas Series subclass optimized for time series analysis.
    
    This class extends pandas Series to provide time-series specific functionality
    while maintaining compatibility with the existing baseTs API.
    
    Attributes:
        freq: Sampling frequency in Hz
        signal_name: Name of the signal
        history: Processing history list
        is_filtered: Whether the data has been filtered
        is_interpolated: Whether the data has been interpolated
        is_uniform_grid: Whether the data is on a uniform time grid
        ts_offset: Timestamp offset in seconds
        has_timestamp_offset: Whether a timestamp offset has been applied
        filtered_indices: Indices of filtered outliers
        lowess_fit: LOWESS fit data for outlier filtering
        last_process: Last processing operation performed
    """
    
    _metadata = [
        'freq', 'signal_name', 'history', 'is_filtered', 
        'is_interpolated', 'is_uniform_grid', 'ts_offset',
        'has_timestamp_offset', 'filtered_indices', 'lowess_fit', 
        'last_process'
    ]
    
    def __init__(self, data=None, index=None, freq: Optional[float] = None, 
                 signal_name: str = "", **kwargs):
        """
        Initialize TimeSeriesData object.
        
        Args:
            data: Array-like data or baseTs object
            index: Time index values (if data is array-like)
            freq: Sampling frequency in Hz
            signal_name: Name of the signal
            **kwargs: Additional Series initialization parameters
        """
        # Handle different input formats
        if hasattr(data, 'times') and hasattr(data, 'data'):
            # baseTs object conversion
            super().__init__(data.data, index=pd.Index(data.times), **kwargs)
            self._copy_metadata_from_basetseries(data)
        elif isinstance(data, np.ndarray) and isinstance(index, np.ndarray):
            # Legacy numpy array initialization
            super().__init__(data, index=pd.Index(index), **kwargs)
            self._initialize_default_metadata()
        else:
            # Standard pandas Series initialization
            super().__init__(data, index=index, **kwargs)
            self._initialize_default_metadata()
            
        # Set or calculate frequency
        if freq is not None:
            self.freq = freq
        else:
            self.freq = self._calculate_effective_frequency()
            
        # Set signal name
        self.signal_name = signal_name.upper() if signal_name else ""
        
        # Initialize or update history
        if not hasattr(self, 'history') or self.history is None:
            self.history = [f"Created TimeSeriesData with {len(self)} samples"]

    def _initialize_default_metadata(self):
        """Initialize default metadata values."""
        self.is_filtered = False
        self.is_interpolated = False
        self.is_uniform_grid = False
        self.ts_offset = 0
        self.has_timestamp_offset = False
        self.filtered_indices = None
        self.lowess_fit = None
        self.last_process = ""
        self.history = []

    def _copy_metadata_from_basetseries(self, base_ts):
        """Copy metadata from a baseTs object."""
        for attr in self._metadata:
            if hasattr(base_ts, attr):
                setattr(self, attr, getattr(base_ts, attr))
            else:
                # Set default if attribute doesn't exist
                if attr == 'history':
                    self.history = [f"Converted from baseTs with {len(self)} samples"]
                elif attr in ['is_filtered', 'is_interpolated', 'is_uniform_grid', 'has_timestamp_offset']:
                    setattr(self, attr, False)
                elif attr in ['ts_offset']:
                    setattr(self, attr, 0)
                elif attr in ['signal_name', 'last_process']:
                    setattr(self, attr, "")
                else:
                    setattr(self, attr, None)

    def _calculate_effective_frequency(self) -> float:
        """Calculate effective sampling frequency from time index."""
        if len(self.index) < 2:
            return np.nan
        duration = float(self.index[-1] - self.index[0])
        if duration <= 0:
            return np.nan
        return len(self) / duration

    @property
    def _constructor(self):
        """Return constructor for pandas operations."""
        return TimeSeriesData

    def _constructor_sliced(self):
        """Return constructor for sliced operations."""
        return TimeSeriesData

    def copy(self, deep: bool = True) -> "TimeSeriesData":
        """
        Create a copy of the TimeSeriesData object with metadata preservation.
        
        Args:
            deep: Whether to make a deep copy
            
        Returns:
            Copied TimeSeriesData object
        """
        copied = super().copy(deep=deep)
        # Ensure it's the right type
        if not isinstance(copied, TimeSeriesData):
            copied = TimeSeriesData(copied.values, index=copied.index)
        
        # Copy metadata
        for attr in self._metadata:
            if hasattr(self, attr):
                value = getattr(self, attr)
                if deep and isinstance(value, (list, dict, np.ndarray)):
                    import copy as copy_module
                    value = copy_module.deepcopy(value)
                setattr(copied, attr, value)
        
        return copied

    def duration(self) -> float:
        """
        Calculate the duration of the time series.
        
        Returns:
            Duration in seconds (or time units of the index)
        """
        if len(self.index) == 0:
            return 0.0
        return float(self.index[-1] - self.index[0])

    def len(self) -> int:
        """
        Get the length of the time series (backward compatibility).
        
        Returns:
            Number of data points
        """
        return len(self)

    def _update_history_and_process(self, hist_msg: str, last_process: str):
        """Helper method to update history and last_process."""
        if not hasattr(self, 'history'):
            self.history = []
        self.history.append(hist_msg)
        self.last_process = last_process

    def _update_flags(self, **flags):
        """Helper method to update object flags."""
        for flag_name, flag_value in flags.items():
            setattr(self, flag_name, flag_value)

    def to_basetseries(self):
        """
        Convert back to a legacy baseTs object for compatibility.
        
        Returns:
            baseTs object with equivalent data and metadata
        """
        from .core import baseTs
        
        # Create baseTs object with numpy arrays
        base_ts = baseTs(
            data=self.values,
            times=self.index.values,
            freq=self.freq,
            signal_name=self.signal_name
        )
        
        # Copy metadata
        for attr in self._metadata:
            if hasattr(self, attr) and attr not in ['freq', 'signal_name']:
                setattr(base_ts, attr, getattr(self, attr))
        
        return base_ts

    def info(self):
        """
        Display information about the time series data.
        """
        from .utils import round_values
        
        data_info = {
            "Length": len(self),
            "Min": np.min(self.values),
            "Max": np.max(self.values),
            "Std": np.std(self.values)
        }
        
        # Round all values except for length
        for key, value in data_info.items():
            data_info[key] = round_values(value)
        
        times_info = {
            "Start": self.index[0] if len(self) > 0 else np.nan,
            "End": self.index[-1] if len(self) > 0 else np.nan,
            "Duration": self.duration(),
            "Effective Frequency": self.freq,
            "Timestamp Offset": getattr(self, 'ts_offset', 0)
        }
        
        for key, value in times_info.items():
            times_info[key] = round_values(value)
        
        print("TimeSeriesData Information:")
        for key, value in data_info.items():
            print(f"  {key}: {value}")
        
        print("\nTime Information:")
        for key, value in times_info.items():
            print(f"  {key}: {value}")
        
        if hasattr(self, 'history') and self.history:
            print("\nHistory:")
            for entry in self.history:
                print(f"  {entry}")

    def __repr__(self) -> str:
        """String representation of TimeSeriesData."""
        base_repr = super().__repr__()
        additional_info = f"\nFreq: {getattr(self, 'freq', 'Unknown')} Hz"
        if hasattr(self, 'signal_name') and self.signal_name:
            additional_info += f", Signal: {self.signal_name}"
        return base_repr + additional_info

    # Arithmetic operations that should return baseTs objects
    def __add__(self, other):
        """Addition operation returning a baseTs object."""
        result = super().__add__(other)
        return self._wrap_result_as_basets(result, "Addition")

    def __radd__(self, other):
        """Right addition operation returning a baseTs object."""
        result = super().__radd__(other)
        return self._wrap_result_as_basets(result, "Addition")

    def __sub__(self, other):
        """Subtraction operation returning a baseTs object."""
        result = super().__sub__(other)
        return self._wrap_result_as_basets(result, "Subtraction")

    def __rsub__(self, other):
        """Right subtraction operation returning a baseTs object."""
        result = super().__rsub__(other)
        return self._wrap_result_as_basets(result, "Subtraction")

    def __mul__(self, other):
        """Multiplication operation returning a baseTs object."""
        result = super().__mul__(other)
        return self._wrap_result_as_basets(result, "Multiplication")

    def __rmul__(self, other):
        """Right multiplication operation returning a baseTs object."""
        result = super().__rmul__(other)
        return self._wrap_result_as_basets(result, "Multiplication")

    def __truediv__(self, other):
        """Division operation returning a baseTs object."""
        result = super().__truediv__(other)
        return self._wrap_result_as_basets(result, "Division")

    def __rtruediv__(self, other):
        """Right division operation returning a baseTs object."""
        result = super().__rtruediv__(other)
        return self._wrap_result_as_basets(result, "Division")

    def __pow__(self, other):
        """Power operation returning a baseTs object."""
        result = super().__pow__(other)
        return self._wrap_result_as_basets(result, "Power")

    def __rpow__(self, other):
        """Right power operation returning a baseTs object."""
        result = super().__rpow__(other)
        return self._wrap_result_as_basets(result, "Power")

    def _wrap_result_as_basets(self, result, operation_name: str):
        """
        Wrap arithmetic operation results as baseTs objects.
        
        Args:
            result: Result from pandas arithmetic operation
            operation_name: Name of the operation for history tracking
            
        Returns:
            baseTs object with the operation result
        """
        # Import here to avoid circular imports
        from .core import baseTs
        
        # Handle scalar results
        if np.isscalar(result):
            # For scalar results, we can't return a baseTs, so return the scalar
            return result
        
        # Create new baseTs object with the result
        new_basets = baseTs(
            data=result.values,
            times=result.index.values,
            freq=self.freq,
            signal_name=self.signal_name
        )
        
        # Copy relevant metadata
        for attr in self._metadata:
            if hasattr(self, attr) and attr not in ['freq', 'signal_name']:
                setattr(new_basets, attr, getattr(self, attr))
        
        # Update history
        new_basets._update_history_and_process(
            f"Applied {operation_name} operation",
            f"_{operation_name.lower()}"
        )
        
        return new_basets