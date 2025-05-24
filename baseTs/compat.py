# -*- coding: utf-8 -*-
"""
Compatibility layer for baseTs numpy to pandas migration.
Created for baseTs pandas migration.
@author: stan@sympaticog.com
"""

from __future__ import annotations
from typing import Union, TYPE_CHECKING
import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from .core import baseTs
    from .series import TimeSeriesData


class ArrayCompatMixin:
    """
    Mixin class providing backward compatibility for numpy array access.
    
    This allows Series-based objects to maintain the same API as numpy-based objects
    by providing `data` and `times` properties that return numpy arrays.
    """
    
    @property
    def data(self) -> np.ndarray:
        """
        Backward compatibility property for data access.
        
        Returns:
            Numpy array of data values
        """
        if hasattr(self, '_series'):
            return self._series.values
        elif hasattr(self, 'values'):
            return self.values
        else:
            raise AttributeError("No data available")
    
    @property 
    def times(self) -> np.ndarray:
        """
        Backward compatibility property for time access.
        
        Returns:
            Numpy array of time values
        """
        if hasattr(self, '_series'):
            return self._series.index.values
        elif hasattr(self, 'index'):
            return self.index.values
        else:
            raise AttributeError("No times available")


def convert_to_series(obj: Union["baseTs", np.ndarray, pd.Series], 
                     times: np.ndarray = None,
                     **kwargs) -> "TimeSeriesData":
    """
    Convert various input types to TimeSeriesData.
    
    Args:
        obj: Object to convert (baseTs, numpy array, or pandas Series)
        times: Time array (required if obj is numpy array)
        **kwargs: Additional arguments for TimeSeriesData constructor
        
    Returns:
        TimeSeriesData object
        
    Raises:
        ValueError: If conversion is not possible
    """
    from .series import TimeSeriesData
    
    if hasattr(obj, '_series') and hasattr(obj._series, 'values'):
        # Already a Series-backed object
        return obj._series
    elif hasattr(obj, 'data') and hasattr(obj, 'times'):
        # baseTs object
        return TimeSeriesData(obj.data, index=obj.times, **kwargs)
    elif isinstance(obj, pd.Series):
        # pandas Series
        return TimeSeriesData(obj.values, index=obj.index, **kwargs)
    elif isinstance(obj, np.ndarray):
        # numpy array
        if times is None:
            raise ValueError("times array required for numpy array input")
        return TimeSeriesData(obj, index=times, **kwargs)
    else:
        raise ValueError(f"Cannot convert {type(obj)} to TimeSeriesData")


def convert_to_basetseries(obj: Union["TimeSeriesData", pd.Series]) -> "baseTs":
    """
    Convert TimeSeriesData or pandas Series back to baseTs object.
    
    Args:
        obj: TimeSeriesData or pandas Series to convert
        
    Returns:
        baseTs object
    """
    from .core import baseTs
    
    if hasattr(obj, 'to_basetseries'):
        return obj.to_basetseries()
    elif isinstance(obj, pd.Series):
        return baseTs(data=obj.values, times=obj.index.values)
    else:
        raise ValueError(f"Cannot convert {type(obj)} to baseTs")


def ensure_numpy_compatibility(func):
    """
    Decorator to ensure function works with both numpy and Series backends.
    
    This decorator can be used to wrap functions that need to work with both
    the legacy numpy-based baseTs objects and the new Series-based objects.
    """
    def wrapper(self, *args, **kwargs):
        # Store original backend state
        is_series_backend = hasattr(self, '_backend') and self._backend == 'series'
        
        try:
            result = func(self, *args, **kwargs)
            return result
        except Exception as e:
            # If Series backend fails, try falling back to numpy
            if is_series_backend:
                # Convert to numpy temporarily
                old_backend = self._backend
                self._backend = 'numpy'
                try:
                    result = func(self, *args, **kwargs)
                    return result
                finally:
                    self._backend = old_backend
            else:
                raise e
    
    return wrapper


class BackendManager:
    """
    Manages the backend selection and switching for baseTs objects.
    """
    
    DEFAULT_BACKEND = 'numpy'  # Will change to 'series' in future versions
    
    @classmethod
    def get_default_backend(cls) -> str:
        """Get the default backend for new objects."""
        return cls.DEFAULT_BACKEND
    
    @classmethod
    def set_default_backend(cls, backend: str):
        """
        Set the default backend for new objects.
        
        Args:
            backend: 'numpy' or 'series'
            
        Raises:
            ValueError: If backend is not supported
        """
        if backend not in ['numpy', 'series']:
            raise ValueError(f"Unsupported backend: {backend}")
        cls.DEFAULT_BACKEND = backend
    
    @classmethod
    def should_use_series(cls, use_series: bool = None) -> bool:
        """
        Determine if Series backend should be used.
        
        Args:
            use_series: Explicit backend choice (overrides default)
            
        Returns:
            True if Series backend should be used
        """
        if use_series is not None:
            return use_series
        return cls.DEFAULT_BACKEND == 'series'


def validate_time_index(times: np.ndarray) -> None:
    """
    Validate time index for Series creation.
    
    Args:
        times: Time array to validate
        
    Raises:
        ValueError: If time index is invalid
    """
    if len(times) == 0:
        raise ValueError("Time index cannot be empty")
    
    if not np.issubdtype(times.dtype, np.number):
        raise ValueError("Time index must be numeric")
    
    if np.any(np.isnan(times)):
        raise ValueError("Time index cannot contain NaN values")
    
    if not np.all(np.diff(times) >= 0):
        raise ValueError("Time index must be non-decreasing")


def create_time_index(data_length: int, freq: float = None, 
                     start_time: float = 0.0) -> np.ndarray:
    """
    Create a uniform time index for data.
    
    Args:
        data_length: Number of data points
        freq: Sampling frequency in Hz (if None, use index-based times)
        start_time: Starting time value
        
    Returns:
        Time index array
    """
    if freq is not None and freq > 0:
        return np.arange(data_length) / freq + start_time
    else:
        return np.arange(data_length, dtype=float) + start_time