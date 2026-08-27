# -*- coding: utf-8 -*-
"""
Pandas Series subclass for time series analysis.
Created for baseTs pandas migration.
@author: stan@sympaticog.com
"""

from __future__ import annotations
from typing import Optional, Union, Any, Dict, List
import copy as copy_module
import numpy as np
import pandas as pd
from numpy.typing import NDArray

from .LowessOutlierFilter import LowessOutlierFilter


def _detach_shared_metadata(obj):
    """
    Give `obj` its own `history` list.

    pandas' default __finalize__ assigns metadata by reference, so a derived
    object would append to the list it inherited - one history for two series.

    `outlier_filter` needs no copy: FilterConfig is frozen and
    set_outlier_filter rebinds the filter rather than mutating it, so sharing
    one is safe by construction. `lowess_fit` and `outlier_indices` are left
    shared, unchanged from before - see #20.

    A None history is normalised to [] rather than left alone. pandas
    propagates metadata from whichever operand carries it, so an operand
    without a history hands None to the derived object; normalising here makes
    "history is always a list" hold for every consumer, instead of asking each
    of the nine call sites that touch it to guard for itself.
    """
    history = getattr(obj, 'history', None)
    if isinstance(history, list):
        object.__setattr__(obj, 'history', list(history))
    elif history is None:
        object.__setattr__(obj, 'history', [])
    return obj


class _FinalizingWindow:
    """
    Wraps a pandas window object (Rolling/Expanding/ExponentialMovingWindow)
    so its aggregations propagate metadata.

    rolling()/expanding()/ewm() build their result via the parent's
    `_constructor` directly and never call `__finalize__` - the type survives
    but history, outlier_filter and everything else in `_metadata` resets to
    constructor defaults. The window object holds the parent as `.obj`; this
    finalizes each aggregation result against it, mirroring what pandas does
    for every other operation.
    """

    def __init__(self, window: Any, parent: "TimeSeriesData", method: str) -> None:
        object.__setattr__(self, '_window', window)
        object.__setattr__(self, '_parent', parent)
        object.__setattr__(self, '_method', method)

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._window, name)
        if not callable(attr):
            return attr

        def finalizing_call(*args, **kwargs):
            result = attr(*args, **kwargs)
            if isinstance(result, pd.Series):
                result = result.__finalize__(self._parent, method=self._method)
            return result

        return finalizing_call

    def __iter__(self):
        """
        Python looks up dunder methods on the type, bypassing __getattr__,
        so this needs an explicit override. The underlying window's own
        iteration already yields correctly-finalized baseTs objects (pandas
        builds each one via the parent's _constructor then __finalize__(s)
        it against the parent internally) - delegate rather than re-wrap.
        """
        return iter(self._window)

    def __repr__(self) -> str:
        return f"_FinalizingWindow({self._window!r})"


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
        outlier_indices: Indices of detected outliers
        lowess_fit: LOWESS fit data for outlier filtering
        last_process: Last processing operation performed
    """
    
    # Every attribute pandas should carry across an operation. Anything missing
    # here is silently dropped by slicing, rolling, dropna, etc.
    #
    # 'filtered_indices' used to be listed here but was only ever initialised to
    # None and never written by anything - a half-finished rename. The attribute
    # that actually holds outlier positions is 'outlier_indices', which was
    # absent, so `ts.iloc[:50].outlier_indices` raised AttributeError.
    _metadata = [
        'freq', 'signal_name', 'history', 'is_filtered',
        'is_interpolated', 'is_uniform_grid', 'ts_offset',
        'has_timestamp_offset', 'outlier_indices', 'lowess_fit',
        'last_process', 'is_outlier_filtered', 'outlier_filter',
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
        self.outlier_indices = None
        self.lowess_fit = None
        self.last_process = ""
        self.history = []
        # _metadata declares these two; without them any derived object
        # inherited None and clobbered the default it was born with.
        self.is_outlier_filtered = False
        self.outlier_filter = LowessOutlierFilter()

    def _copy_metadata_from_basetseries(self, base_ts):
        """Copy metadata from a baseTs object, without sharing its mutables."""
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

        _detach_shared_metadata(self)

    def _calculate_effective_frequency(self) -> float:
        """Calculate effective sampling frequency from time index."""
        if len(self.index) < 2:
            return np.nan
        duration = float(self.index[-1] - self.index[0])
        if duration <= 0:
            return np.nan
        # n samples span n-1 intervals. Using len(self) here over-reported the
        # rate by n/(n-1) - 11% at n=10, 25% at n=5 - for every series built
        # from a times array without an explicit freq.
        return (len(self) - 1) / duration

    def __finalize__(self, other, method=None, **kwargs):
        """
        Propagate metadata, detaching what a derived object must not share.

        pandas' default __finalize__ assigns metadata by reference, so a derived
        object would share the parent's `history` list - appending to one would
        silently append to the other.

        `outlier_filter` is deliberately left shared: FilterConfig is frozen
        and set_outlier_filter rebinds rather than mutates it, so a shared
        filter cannot carry a write from one object to another. `lowess_fit`
        and `outlier_indices` stay shared too - see _detach_shared_metadata.

        method == 'concat' is special-cased: nlargest/nsmallest route through
        an internal concat step where `other` is not an NDFrame (a
        SimpleNamespace on pandas >= 3.0, a private _Concatenator on
        pandas 2.x), so pandas' own isinstance(other, NDFrame) branch above
        skips it and metadata is silently dropped. `objs` is the attribute
        both shapes carry; the newer `input_objs` pandas' >= 3.0
        __finalize__ docstring documents does not exist on pandas 2.x and
        using it there silently no-ops this whole block - caught by CI on
        Python 3.9/3.10 (pandas 2.3.3), which this project's own
        `pandas>=2.0.0` floor requires supporting. Recovery only fires when
        exactly one of those objects is non-empty: that is nlargest/
        nsmallest's internal single-real-result-plus-empty-placeholder
        pattern. A genuine multi-operand pd.concat() has more than one
        non-empty operand, and must not have its result's
        freq/signal_name/history overwritten by whichever operand happens to
        be first - the constructor already derived correct values from the
        real merged index.
        """
        super().__finalize__(other, method=method, **kwargs)
        if method == 'concat':
            objs = getattr(other, 'objs', None)
            if objs:
                nonempty = [obj for obj in objs if len(obj) > 0]
                if len(nonempty) == 1:
                    source = nonempty[0]
                    for name in self._metadata:
                        if hasattr(source, name):
                            object.__setattr__(self, name, getattr(source, name))
        return _detach_shared_metadata(self)

    def _finalizing_window(self, method: str, *args, **kwargs) -> _FinalizingWindow:
        """See _FinalizingWindow: rolling()/expanding()/ewm() never call __finalize__."""
        window = getattr(super(), method)(*args, **kwargs)
        return _FinalizingWindow(window, self, method)

    def rolling(self, *args, **kwargs) -> _FinalizingWindow:
        """Rolling window whose aggregations propagate metadata - see _FinalizingWindow."""
        return self._finalizing_window('rolling', *args, **kwargs)

    def expanding(self, *args, **kwargs) -> _FinalizingWindow:
        """Expanding window whose aggregations propagate metadata - see _FinalizingWindow."""
        return self._finalizing_window('expanding', *args, **kwargs)

    def ewm(self, *args, **kwargs) -> _FinalizingWindow:
        """EWM window whose aggregations propagate metadata - see _FinalizingWindow."""
        return self._finalizing_window('ewm', *args, **kwargs)

    @property
    def _constructor(self):
        """Return constructor for pandas operations."""
        return TimeSeriesData

    @property
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
        
        # Copy metadata. The allow-list bounds what gets deep-copied: an
        # unguarded deepcopy turns any non-copyable metadata value into a hard
        # error on routine operations. outlier_filter is not on it, and is
        # shared at both depths - safe, see _detach_shared_metadata.
        for attr in self._metadata:
            if hasattr(self, attr):
                value = getattr(self, attr)
                if deep and isinstance(value, (list, dict, np.ndarray)):
                    value = copy_module.deepcopy(value)
                setattr(copied, attr, value)

        if not deep:
            # The loop above re-assigns history by reference, undoing what
            # __finalize__ already detached. pandas reaches here internally
            # (sort_values calls copy(deep=False)), so a "shallow" copy must
            # still not hand back a shared history list. The deep branch
            # deep-copies it in the loop above.
            _detach_shared_metadata(copied)
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
        """Helper method to update history and last_process.

        The guard tests for None as well as absence: hasattr alone is True for
        a history that __finalize__ propagated as None, which then dies on
        None.append.
        """
        if getattr(self, 'history', None) is None:
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

        return _detach_shared_metadata(base_ts)

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

    def _inplace_arith(self, result):
        """
        Adopt an arithmetic result in place, history entry included.

        pandas implements `ts += 1` as __add__ followed by keeping the values
        and discarding the wrapper, so the entry _wrap_result_as_basets
        appended would be thrown away with it - `ts += 1` recorded nothing
        while `ts = ts + 1` recorded an entry.
        """
        if not isinstance(result, TimeSeriesData):
            return result
        history = list(getattr(result, 'history', []) or [])
        last_process = getattr(result, 'last_process', "")
        # reindex_like, as pandas' own _inplace_method does: augmented
        # assignment must not change the length of the object being assigned
        # to, even when the operand carries a different index.
        self._update_inplace(result.reindex_like(self))
        object.__setattr__(self, 'history', history)
        object.__setattr__(self, 'last_process', last_process)
        return self

    def __iadd__(self, other):
        return self._inplace_arith(self + other)

    def __isub__(self, other):
        return self._inplace_arith(self - other)

    def __imul__(self, other):
        return self._inplace_arith(self * other)

    def __itruediv__(self, other):
        return self._inplace_arith(self / other)

    def __ipow__(self, other):
        return self._inplace_arith(self ** other)

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
        
        # Create new baseTs object with the result. freq is left unset so
        # baseTs derives it from the result index - arithmetic between two
        # operands on different time bases produces a union index, and the
        # left operand's freq no longer describes it.
        new_basets = baseTs(
            data=result.values,
            times=result.index.values,
            signal_name=self.signal_name
        )
        
        # Copy relevant metadata
        for attr in self._metadata:
            if hasattr(self, attr) and attr not in ['freq', 'signal_name']:
                setattr(new_basets, attr, getattr(self, attr))

        # Before the history update, not after: the entry appended below would
        # otherwise land in the operand's own history list.
        _detach_shared_metadata(new_basets)

        # Update history
        new_basets._update_history_and_process(
            f"Applied {operation_name} operation",
            f"_{operation_name.lower()}"
        )
        
        return new_basets