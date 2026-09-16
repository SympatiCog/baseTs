# -*- coding: utf-8 -*-
"""
Created on Oct 19 2024
@author: stan@sympaticog.com
"""

from __future__ import annotations
import math
import numbers
import warnings

import numpy as np
from scipy import interpolate
import matplotlib.pyplot as plt
from pandas.plotting import PlotAccessor
import copy
import pandas as pd
from scipy.ndimage import gaussian_filter
from typing import Optional, TYPE_CHECKING, Union, List, Tuple

# Import modules - now using relative imports
from .filters import (bandpass_filter, sg_filter, interpolate_missing_values, lowpass_filter,
                      highpass_filter, notch_filter, _require_int)
from .LowessOutlierFilter import LowessOutlierFilter, TailType, FilterConfig
from dataclasses import replace
from .utils import (coerce_numeric_data,
                    find_closest_time, compute_fft_power, find_closest, get_peak_freq,
                    get_peaks, ClosestMatch, diff, dediff, relative_band_power, falff,
                    BandPowerResult, validate_sampling_freq,
                    validate_finite_data, validate_non_empty, ValidationError)
from .series import (TimeSeriesData, _detach_shared_metadata,
                     deepcopy_metadata_value, normalise_history,
                     _UNSET, _UnsetType,
                     _carries_metadata, _carry_identity,
                     _apply_duplicate_label_declaration,
                     _refuse_undeclarable_index, _origin_timestamp,
                     _origin_problem)
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
        time_col: Name of the column containing time values: seconds, or a
            datetime or timedelta column
        data_col: Name of the column containing data values
        signal_name: Name of the signal (defaults to data_col if None)
        freq: Sampling frequency in Hz (optional)
        ts_offset: The origin the time column's seconds are counted from,
            in epoch seconds (optional; refused alongside a datetime column,
            which carries its own)

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
    
    # Validate data types. A datetime or timedelta column is accepted since
    # #100: the constructor converts it to seconds (a datetime column sets
    # the origin, so `ts_offset` alongside one is refused there). The
    # pandas tests go first because a timezone-aware column's dtype is not
    # a numpy dtype and np.issubdtype raises on it.
    # The numpy test is guarded the same way: a pandas extension dtype (a
    # string column on pandas 3) made np.issubdtype raise TypeError where
    # the ValueError below was documented.
    time_dtype = df[time_col].dtype
    stamped = (pd.api.types.is_datetime64_any_dtype(time_dtype)
               or pd.api.types.is_timedelta64_dtype(time_dtype))
    numeric = isinstance(time_dtype, np.dtype) and np.issubdtype(time_dtype, np.number)
    if not stamped and not numeric:
        raise ValueError(f"Time column '{time_col}' must be numeric, datetime or timedelta")
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


def from_csv(path,
             time_col: str = "time",
             data_col: str = "value",
             signal_name: Optional[str] = None,
             freq: Optional[float] = None,
             ts_offset: Optional[float] = None,
             **read_csv_kwargs) -> "baseTs":
    """
    Create a baseTs object from a CSV file.

    Thin wrapper: ``pd.read_csv(path, **read_csv_kwargs)`` then :func:`from_df`.

    Args:
        path: Path (or any object ``pandas.read_csv`` accepts) to the CSV file
        time_col: Name of the column containing time values: seconds, or a
            datetime or timedelta column
        data_col: Name of the column containing data values
        signal_name: Name of the signal (defaults to data_col if None)
        freq: Sampling frequency in Hz (optional)
        ts_offset: The origin the time column's seconds are counted from,
            in epoch seconds (optional; refused alongside a datetime column,
            which carries its own)
        **read_csv_kwargs: Forwarded to ``pandas.read_csv`` (e.g. ``sep``,
            ``parse_dates``)

    Returns:
        baseTs: A new baseTs object initialized with the file's data
    """
    return from_df(pd.read_csv(path, **read_csv_kwargs),
                   time_col=time_col, data_col=data_col,
                   signal_name=signal_name, freq=freq, ts_offset=ts_offset)


def from_parquet(path,
                  time_col: str = "time",
                  data_col: str = "value",
                  signal_name: Optional[str] = None,
                  freq: Optional[float] = None,
                  ts_offset: Optional[float] = None,
                  **read_parquet_kwargs) -> "baseTs":
    """
    Create a baseTs object from a Parquet file.

    Thin wrapper: ``pd.read_parquet(path, **read_parquet_kwargs)`` then
    :func:`from_df`. Requires a parquet engine (``pyarrow`` or
    ``fastparquet``) to be installed.

    Args:
        path: Path (or any object ``pandas.read_parquet`` accepts) to the
            Parquet file
        time_col: Name of the column containing time values: seconds, or a
            datetime or timedelta column
        data_col: Name of the column containing data values
        signal_name: Name of the signal (defaults to data_col if None)
        freq: Sampling frequency in Hz (optional)
        ts_offset: The origin the time column's seconds are counted from,
            in epoch seconds (optional; refused alongside a datetime column,
            which carries its own)
        **read_parquet_kwargs: Forwarded to ``pandas.read_parquet`` (e.g.
            ``columns``, ``engine``)

    Returns:
        baseTs: A new baseTs object initialized with the file's data
    """
    return from_df(pd.read_parquet(path, **read_parquet_kwargs),
                   time_col=time_col, data_col=data_col,
                   signal_name=signal_name, freq=freq, ts_offset=ts_offset)


def _is_unset(value) -> bool:
    """
    True if a numeric argument was not supplied.

    The constructor uses np.nan as its "not provided" sentinel, but `value is
    np.nan` only matches that one object - a user passing float('nan') or
    np.float64('nan') fell through and silently produced an all-NaN time index.
    """
    if value is None:
        return True
    try:
        return math.isnan(float(value))
    except (TypeError, ValueError):
        return False

class _PlotAccessor:
    """
    Callable proxy backing ``baseTs.plot``.

    ``plot`` used to be a plain alias for :meth:`baseTs.plot_line`. That shadowed
    the pandas ``.plot`` accessor - which is an object, not a method - so
    ``ts.plot.line()``, ``.bar()``, ``.hist()`` and the other eleven sub-methods
    were unreachable.

    This keeps ``ts.plot()`` drawing the baseTs line plot, and delegates every
    attribute lookup to the pandas accessor, so both spellings work:

        ts.plot()                 # baseTs line plot, as before
        ts.plot(lowess=True)      # baseTs plot_line keyword arguments
        ts.plot.bar()             # pandas PlotAccessor
    """

    __slots__ = ("_ts",)

    def __init__(self, ts: "baseTs"):
        object.__setattr__(self, "_ts", ts)

    def __call__(self, *args, **kwargs):
        return self._ts.plot_line(*args, **kwargs)

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(PlotAccessor(self._ts), name)

    def __dir__(self):
        return sorted(set(dir(PlotAccessor(self._ts))))

    def __repr__(self) -> str:
        name = getattr(self._ts, "signal_name", "") or "unnamed"
        return f"<baseTs plot accessor for {name!r}>"


class baseTs(TimeSeriesData):
    """
    Basic data class to hold a timeseries and data.
    
    Built on pandas Series foundation for optimal time-series analysis.
    
    Args:
        data (np.array): The actual observational data.
        times (np.array): The timestamps corresponding to the data.
        freq (float, optional): The frequency of data collection. Defaults to np.nan.

    """

    def __init__(self,
                 data: np.array,
                 times: np.array = None,
                 freq: float = np.nan,
                 ts_offset: float = np.nan,
                 is_filtered: Union[bool, _UnsetType] = _UNSET,
                 is_interpolated: Union[bool, _UnsetType] = _UNSET,
                 is_uniform_grid: Union[bool, _UnsetType] = _UNSET,
                 is_outlier_filtered: Union[bool, _UnsetType] = _UNSET,
                 has_timestamp_offset: Union[bool, _UnsetType] = _UNSET,
                 outlier_indices: Union[np.ndarray, None, _UnsetType] = _UNSET,
                 lowess_fit: Union[np.ndarray, None, _UnsetType] = _UNSET,
                 signal_name: Union[str, _UnsetType] = _UNSET,
                 history: Union[list, None, _UnsetType] = _UNSET,
                 last_process: Union[str, _UnsetType] = _UNSET,
                 index: np.array = None,
                 **pandas_kwargs):
        """
        Initialize baseTs object as pandas Series with time-series metadata.

        Args:
            index: Alias for `times`. pandas constructs subclass instances as
                _constructor(values, index=...), so accepting `index` is what
                lets baseTs survive native pandas operations - see
                baseTs._constructor. Prefer `times` in user code.
            **pandas_kwargs: Passed through to the pandas Series layer (name,
                copy, dtype). Present for the same reason.
        """

        # pandas calls the constructor with index=; user code passes times=.
        if times is None:
            if index is not None:
                times = index
            elif isinstance(data, pd.Series):
                times = data.index

        # Handle times array - create if not provided
        if times is None:
            if not _is_unset(freq):
                # Validated before use, not after: this builds the index FROM
                # the rate, so freq=0 produced times [nan, inf, inf, ...],
                # freq=-10 ran the index backwards, and freq=inf collapsed it
                # to all-zeros - each of them a silently degenerate object
                # whose real complaint surfaced much later.
                freq = validate_sampling_freq(freq)
                times = np.arange(0, len(data)) / freq
            else:
                raise ValueError("You must provide either a times array or a frequency")
        
        # Initialize as TimeSeriesData (pandas Series subclass)
        # The offset pair rides through too, translated from this class's
        # public NaN/None sentinel to the superclass's. TimeSeriesData owns
        # the pair since #100, because that is where a DatetimeIndex is
        # converted to seconds and where an explicit `ts_offset` alongside
        # one has to be refused.
        super().__init__(
            data=data,
            index=times,
            freq=None if _is_unset(freq) else freq,
            signal_name=signal_name,   # the sentinel rides through
            ts_offset=_UNSET if _is_unset(ts_offset) else ts_offset,
            has_timestamp_offset=has_timestamp_offset,
            **pandas_kwargs
        )
        
        # Set metadata attributes - only the ones the caller actually named.
        #
        # Assigned unconditionally, these overwrote whatever
        # _copy_metadata_from_basetseries had just copied off the source, so
        # baseTs(ts) reset eleven of thirteen names to parameter
        # defaults, and a converted series reported itself as freshly
        # created (#57). #15 fixed
        # exactly this for `outlier_filter` with a per-attribute guard, which
        # is why that one name survived; the guard does not scale to thirteen,
        # so the constructor tells "supplied" from "defaulted" instead.
        #
        # Nothing is copied when the data is an array, so the defaults still
        # arrive there - from _initialize_default_metadata, which is where
        # they belong.
        for _name, _value in (('is_filtered', is_filtered),
                              ('is_interpolated', is_interpolated),
                              ('is_uniform_grid', is_uniform_grid),
                              ('is_outlier_filtered', is_outlier_filtered),
                              ('outlier_indices', outlier_indices),
                              ('lowess_fit', lowess_fit)):
            if not isinstance(_value, _UnsetType):
                setattr(self, _name, _value)
        # The one label door that does not pass through
        # TimeSeriesData.__init__: signal_name is handed to the superclass,
        # while this is assigned straight onto the object. It used to need
        # its own normalise_label call - without it baseTs(...,
        # last_process=None) returned an object whose every plot label raised
        # TypeError, from a supported keyword. Since #61 the assignment
        # itself normalises (last_process is a property), pinned in
        # test_metadata_defaults.py.
        if not isinstance(last_process, _UnsetType):
            self.last_process = last_process

        # The timestamp offset pair (`ts_offset`, `has_timestamp_offset`) is
        # handled by TimeSeriesData.__init__ now - see the super() call
        # above. The block that lived here kept the same rules: untouched
        # unless given (that is what stopped a conversion losing an offset
        # it was carrying), an explicit offset sets the flag, and clearing
        # the flag without an offset zeroes the offset, one direction only.

        # Initialize history. Only when the caller named one, or when nothing
        # was carried across - a conversion keeps the source's history
        # verbatim, where this used to replace it with a single "Created"
        # entry and leave the object claiming to be new.
        if isinstance(history, _UnsetType):
            # Not supplied. Keep whatever was carried across, and mint the
            # creation entry only when there was no source to carry from -
            # asked of the data, not of the result, because a source whose
            # history is legitimately empty is indistinguishable from an
            # absent one by falsiness alone.
            if not _carries_metadata(data):
                self.history = [
                    f"Created baseTs object; {len(self)} samples"]
        elif history is None:
            # Supplied as None: the documented request for a fresh entry.
            # Folded into the branch above, it became the one nullable
            # keyword that preserved rather than cleared, disagreeing with
            # the signature and with every sibling argument.
            self.history = [
                f"Created baseTs object; {len(self)} samples"]
        else:
            # normalise_history, not a bare list(): this is the first place a
            # history enters the system, and list('note') would explode a str
            # into four single-character entries that then persist through
            # every derivation. Also returns a new list rather than the
            # caller's own object, so two series built from one list do not
            # cross-contaminate each other's history.
            self.history = normalise_history(history)

        # Only if the superclass did not already carry one across: baseTs(ts)
        # takes the conversion branch in TimeSeriesData.__init__, which copies
        # the source's filter, and this used to overwrite it with a default.
        if getattr(self, 'outlier_filter', None) is None:
            self.outlier_filter = LowessOutlierFilter()


    @property
    def _constructor(self):
        """
        Keep pandas operations returning baseTs rather than downgrading.

        Without this, TimeSeriesData._constructor is inherited and every native
        pandas operation (slicing, rolling, dropna, ...) returned a
        TimeSeriesData, silently dropping all baseTs methods - so the documented
        method chaining did not actually work.

        pandas calls this as _constructor(values, index=...), which __init__
        accepts via its `index` alias.
        """
        return baseTs

    # Backward compatibility properties
    @property
    def data(self) -> np.ndarray:
        """Get the data values as numpy array (backward compatibility)."""
        return self.values
    
    @data.setter
    def data(self, value: np.ndarray):
        """Set the data values (backward compatibility)."""
        # Update the Series values while preserving metadata
        self._update_series_data(value)
    
    @property
    def times(self) -> np.ndarray:
        """Get the time values as numpy array (backward compatibility)."""
        return self.index.values
    
    @times.setter
    def times(self, value: np.ndarray):
        """Set the time values (backward compatibility).

        The assignment reaches TimeSeriesData._set_axis, the one door every
        index arrives by (#100): a DatetimeIndex becomes seconds since its
        first stamp and sets the origin, a TimedeltaIndex becomes seconds
        and leaves the origin alone, and seconds are taken as given - the
        same rule as the constructor, `ts.index = ...` and `set_axis`.

        One difference from pandas' `ts.index = ...`: seconds assigned here
        are declared to be seconds in this series' time base, so the
        origin, if there is one, describes the new index. pandas' door
        makes no such declaration - `reset_index(inplace=True)` uses it to
        install positions - so seconds arriving there must still be drawn
        from the ones the origin was declared against.
        """
        self.index = pd.Index(value)
        if self.has_timestamp_offset and self.__dict__.get('_origin_from_index') is None:
            self._origin_index = self.index
        # No freq recalculation. The property derives from the index, so a new
        # index re-derives on the next read - and any declaration made against
        # the old index stops matching its token, which is the correct
        # outcome rather than a side effect to remember to trigger here.
        #
        # No lowess_fit/outlier_indices handling either, and for a stronger
        # reason than freq's: they are checked against the live index and the
        # live values when they are *read* (#20, #40), so there is no moment
        # at which this setter, or any other writer, has to remember anything.
    
    def _adopt_data_inplace(self, new_data: np.ndarray, new_index):
        """Re-initialise this object's data and index, keeping everything else.

        The single door for re-initialising `self` through pandas. Three
        methods used to call `super(TimeSeriesData, self).__init__` directly -
        this one, `interpolate_gaps(inplace=True)` and
        `shift_time(inplace=True)` - and pandas' `__init__` resets `name`,
        `attrs` and `flags` to defaults on the way past. Two of the three
        restored nothing at all, and the third restored `_metadata` only, so
        every `inplace=True` method silently stripped the object's identity.

        Collapsing them is deliberate, and not the same as adding a call to
        each. `_carry_identity` cannot serve here: its target *is* its source,
        and by the time any post-reinit call could run, the values it would
        copy have already been reset. The snapshot has to be taken *before*
        the re-initialisation, which only a wrapper around it can guarantee.

        The `_metadata` snapshot is load-bearing, and an earlier version of
        this docstring wrongly called it redundant on the grounds that those
        attributes live in the instance `__dict__` which `pd.Series.__init__`
        does not touch. That is true of baseTs' own names and false of the one
        that matters most: `_name` is in `_metadata` and pandas *does* reset
        it here. Deleting the restore loop fails 40 tests.
        """
        # Split by who owns the field, with no overlap. `_name` is in
        # `_metadata`, so the loop below restores it and these locals must
        # not - two mechanisms restoring one field means neither is pinned by
        # a test, which is what mutation testing showed when both did.
        attrs = dict(getattr(self, 'attrs', {}) or {})
        allows_duplicates = self.flags.allows_duplicate_labels

        # Before the re-initialisation, so this method is all-or-nothing.
        # Checked afterwards, a refused declaration left the object holding
        # the new data and index with its duplicate-label protection reset to
        # pandas' permissive default - a failure report over a mutated,
        # silently unprotected object.
        #
        # The returned index is the one used below, deliberately. Checking a
        # `pd.Index` built from the argument and then handing the *argument*
        # to pandas means two objects where there should be one, and drains a
        # one-shot iterable before pandas ever sees it.
        new_index = _refuse_undeclarable_index(allows_duplicates, new_index)

        preserved = {attr: getattr(self, attr)
                     for attr in self._metadata if hasattr(self, attr)}

        super(TimeSeriesData, self).__init__(new_data, index=new_index)

        for attr, value in preserved.items():
            setattr(self, attr, value)
        # The re-initialisation went through _set_axis; if the new index
        # arrived stamped its origin holds over the preserved pair (#100).
        # No package path hands a stamped index here - every caller derives
        # it from the numeric one - so this is pinned directly.
        if not self._restore_origin_from_index() and self.has_timestamp_offset:
            # Re-initialised in this series' own time base: the preserved
            # pair describes the index just installed, not the old one.
            self._origin_index = self.index

        if attrs:
            self.attrs = attrs
        if allows_duplicates is not self.flags.allows_duplicate_labels:
            _apply_duplicate_label_declaration(self, allows_duplicates)
        return self

    def _update_series_data(self, new_data: np.ndarray):
        """Replace the values, keeping the index where the length allows.

        A same-length assignment keeps the index. A length-changing one
        resamples over the existing span: the index becomes
        `linspace(first, last, n)`, the grid `interpto_samples` builds. Every
        length-changing method in the package assigns `data` first and
        `times` second (the `times` setter alone rejects a length mismatch,
        so that two-step is the only route), which makes this grid a
        transient those methods overwrite; it is kept only by a caller who
        changes the length and supplies no times.

        Resampling needs a measurable span, and an index has none when it
        is empty, holds one sample, has coinciding first and last
        timestamps, or has a NaN at either end. Such an index cannot
        *grow*: it used to (#65), and every added sample landed on a label
        the index could not separate - on a single sample `first == last`,
        so the object silently acquired a fully duplicated index and a
        `freq` derived from a zero-duration grid; on an empty series it
        minted `0, 1, ..., n-1`, a 1 Hz grid nobody asked for; with a NaN
        endpoint, `linspace` invented NaN labels. Growth refuses now, before
        anything is mutated. A no-span index can still *shrink*, keeping
        the first n of the labels it already has - they are all the same
        label, or the same NaN - so `diff_ts` on two samples at one
        timestamp behaves as it always did. Shrinking to empty places
        nothing and needs no span either.

        The first cut of this fix keyed on sample count, and review found
        in turn a two-sample index at one timestamp growing into the same
        duplicated grid, a NaN endpoint passing an equality test, and a
        shrink refused that `main` had handled. The rule is the span; the
        count was its proxy.

        A package method that *grows* the length takes the two-step route
        (`data` then `times`) and must check the span itself first, in its
        own words: this refusal describes an assignment and offers remedies
        for one, which is wrong advice for a caller of `interpto_samples`.
        That method checks; a new one has to. Methods that only shrink
        (`diff_ts`, `remove_outliers`, `trimto_timepoints`, ...) never
        reach the refusal.

        Raises:
            ValidationError: if the length grows on a series whose index
                has no measurable span.
        """
        n_new = len(new_data)
        n_old = len(self.index)
        if n_old == 0:
            no_span, why = True, "an empty series has no span to resample over"
        elif pd.isna(self.index[0]) or pd.isna(self.index[-1]):
            no_span, why = True, ("an endpoint of its index is not a number "
                                  "(it holds a NaN), so its span is unmeasurable")
        elif n_old == 1:
            no_span, why = True, "a single sample has no span to resample over"
        elif self.index[0] == self.index[-1]:
            no_span, why = True, (f"its first and last timestamps coincide at "
                                  f"{self.index[0]!r}, so it has no span to "
                                  "resample over")
        else:
            no_span, why = False, ""

        if n_new == n_old:
            new_index = self.index
        elif no_span and n_new > n_old:
            raise ValidationError(
                f"cannot place {n_new} samples on a series of {n_old}: a "
                "length-changing `ts.data = ...` resamples the new values "
                f"over the existing time span, and {why}. Build a new "
                "object instead: `baseTs(new_data, times=...)` or "
                "`baseTs(new_data, freq=...)`."
            )
        elif no_span or n_new == 0:
            # A shrink of a no-span index keeps labels it already has; an
            # empty result places nothing. Sliced rather than rebuilt so the
            # index keeps its dtype (a DatetimeIndex used to fail in numpy
            # here; since #100 none reaches this, but an object index still
            # would).
            new_index = self.index[:n_new]
        else:
            new_index = np.linspace(self.index[0], self.index[-1], n_new)

        self._adopt_data_inplace(new_data, new_index)

    # _update_history_and_process is inherited from TimeSeriesData. The
    # override that used to sit here was byte-for-byte identical to it once
    # both grew the same None guard, so it is gone rather than left to drift.

    def _update_flags(self, **flags):
        """Helper method to update object flags."""
        for flag_name, flag_value in flags.items():
            setattr(self, flag_name, flag_value)

    def _create_new_with_data(self, new_data: np.ndarray, new_times: np.ndarray = None, 
                             preserve_metadata: bool = True, **kwargs) -> "baseTs":
        """
        Create a new baseTs object with new data, preserving metadata.
        
        Args:
            new_data: New data array
            new_times: New time array (optional, uses existing if None)
            preserve_metadata: Whether to copy metadata from current object
            **kwargs: Additional parameters for new object
            
        Returns:
            New baseTs object
        """
        if new_times is None:
            new_times = self.times

        # No freq handling here any more. The `freq` property derives from the
        # index, and an explicit declaration travels as _freq_declaration in
        # the metadata copy below - where the property re-validates it against
        # this object's own index. The index_unchanged test and the
        # post-construction re-assert that used to live here were a second
        # implementation of the "did the index change?" rule, which is
        # precisely how it came to disagree with __finalize__ (#29).
        new_obj = baseTs(new_data, new_times, **kwargs)

        # The name is inherited, not re-minted. Handing it back to the
        # constructor as a keyword ran it through the constructor's
        # upper-casing a second time, so zscale() and iloc[:5] disagreed about
        # the name of one series (#56). The rule: the constructor normalises
        # its own argument, and a derivation copies the parent's - so a name
        # the caller passes in kwargs is a constructor argument and keeps the
        # constructor's rule, while the parent's is copied verbatim. The
        # assignment normalises on its own since #61 (signal_name is a
        # property), so a None still lands as "" without an explicit call;
        # #56 pinned that on the preserve_metadata=False path, where nothing
        # else runs. Outside the preserve_metadata block because the name
        # never was part of what that flag withholds.
        if 'signal_name' not in kwargs:
            new_obj.signal_name = self.signal_name

        if preserve_metadata:
            # Copy metadata
            metadata_attrs = ['is_filtered', 'is_interpolated', 'is_uniform_grid',
                            'is_outlier_filtered',
                            '_outlier_indices', '_lowess_fit', 'last_process',
                            'outlier_filter']

            # The offset pair is copied only when the new index brought no
            # origin of its own. An index carries its origin (#100): handed
            # a DatetimeIndex as `new_times`, the constructor above recorded
            # its first stamp, and copying the parent's pair over it
            # relabelled 2024 dates as 2023 (review round 1, both
            # panelists). Same shape as the _freq_declaration rule below: a
            # value the new object derived from its own arguments is not
            # overwritten by the parent's.
            if new_obj.__dict__.get('_origin_from_index') is None:
                metadata_attrs += ['has_timestamp_offset', 'ts_offset']
                # And the pair then describes the new index, whatever grid
                # it is: every caller builds `new_times` in this series'
                # time base (a slice, a resampled grid, the same index).
                # Not `_origin_index` from the parent - a copied stamp would
                # refuse the grid resample just built.
                if self.has_timestamp_offset:
                    new_obj._origin_index = new_obj.index

            # Not iterating self._metadata: this list is deliberately curated
            # and excludes signal_name and history, which are handled above
            # and below. _freq_declaration must be added by name, and is skipped
            # when the caller declared a rate explicitly - otherwise this copy
            # would silently overwrite their kwarg with the parent's.
            if 'freq' not in kwargs:
                metadata_attrs.append('_freq_declaration')

            for attr in metadata_attrs:
                if hasattr(self, attr):
                    setattr(new_obj, attr, getattr(self, attr))

            # Copy history (make a copy to avoid reference issues). Shares one
            # normaliser with __finalize__: every non-inplace method routes
            # through here, so a history that arrived as None would otherwise
            # die on .copy() before reaching any of the guarded append paths,
            # and a bare list() would explode a str into characters.
            new_obj.history = normalise_history(self.history)

            # The private slots, not the public names. Assigning through the
            # properties would run their stamping setter and re-stamp the
            # parent's fit with the *new* object's index - laundering the very
            # staleness the properties exist to catch. Same reason
            # _freq_declaration is copied by its private name.
            _detach_shared_metadata(new_obj)

            # The curated list above is the one metadata copy in the package
            # that does not iterate _metadata, so declaring `_name` there
            # reaches every other site but not this one - and this is the site
            # every non-inplace filter and transform goes through. attrs and
            # flags are in no list at all.
            _carry_identity(new_obj, self)

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

    def len(self) -> int:
        """
        Calculates the length of the data.

        Returns:
            int: Length of the data
        """
        return len(self.data)
    
    def __len__(self) -> int:
        """
        Python's built-in len() function support.

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
            mean = data.mean()
            std = data.std()
            if std == 0:
                # For constant data, return zeros (centered around mean)
                return np.zeros_like(data)
            return (data - mean) / std

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
    
    def interpto_hz(self, new_freq: float, kind: str = 'linear',
                    inplace: bool = False) -> "baseTs":
        """
        Resample onto a uniform grid at exactly new_freq.

        The grid is built from the rate rather than by subdividing the
        duration. np.linspace(t0, t1, int(duration * new_freq)) spreads N
        points across the whole span, so the spacing is duration/(N-1) and the
        real rate falls short by (N-1)/N - interpto_hz(5) produced a grid
        measuring 4.984985 Hz while reporting 5. Building from the rate makes
        the reported and produced rates the same number.

        Args:
            new_freq: The desired sampling rate in Hz. Must be positive and
                finite; it is validated here rather than at the point the
                result is consumed.
            kind: Interpolation type passed to scipy.interpolate.interp1d
            inplace: If True, modifies existing object. Otherwise returns a
                new object. Defaults to False.

        Returns:
            baseTs: Interpolated data on an exact new_freq grid

        Raises:
            ValueError: If new_freq is not a positive finite rate, if the
                source time base is degenerate, or if the requested rate is
                too low to produce at least two samples
        """
        new_freq = validate_sampling_freq(new_freq)

        duration = self._resampling_duration(
            f"Cannot interpolate to {new_freq} Hz",
            "has no rate to resample from, and stamping the requested rate "
            "on the empty result would report a healthy number for a series "
            "that has none.")

        # Rounded before flooring. The product lands just below the integer
        # for an exact-rate source - (np.arange(1000)/30.0) spans
        # 998.9999999999999 * 30, not 999.0 - so a bare floor silently drops
        # a trailing sample on a same-rate round trip. Nine places absorbs
        # representation error while leaving a genuine fractional product
        # (998.9999 from real data) to floor as it should.
        n_samples = int(np.floor(np.round(duration * new_freq, 9))) + 1
        if n_samples < 2:
            raise ValueError(
                f"Cannot interpolate to {new_freq} Hz: a {duration}s series "
                f"yields {n_samples} sample(s), and at least two samples are "
                f"needed to carry a rate."
            )

        # Clipped defensively, not to fix an observed bug: n-1 <= duration *
        # new_freq holds by construction, so the last point cannot exceed t1
        # mathematically, and a 200,000-case sweep across rates, lengths and
        # offsets found no overshoot. But np.round above can nudge the product
        # up past its true value, and interp1d rejects anything above its
        # range outright - a one-line clamp against a hard error that would
        # only ever appear on a user's data.
        new_times = self.times[0] + np.arange(n_samples) / new_freq
        new_times[-1] = min(new_times[-1], self.times[-1])

        interpolator = interpolate.interp1d(self.times, self.data, kind=kind)
        new_data = interpolator(new_times)

        if inplace:
            target = self
        else:
            target = self.copy()

        target.data = new_data
        target.times = new_times
        # Declared, not left to derive. After the grid fix the derived rate is
        # correct, but it round-trips through floating point -
        # (n-1) / ((n-1)/f) is not bit-exact f - so .freq could read
        # 99.99999999999999. The declaration is now true rather than the
        # (N-1)/N overstatement it used to be, and it expires on an index
        # change like any other.
        target.freq = new_freq
        target.is_interpolated = True
        target.is_uniform_grid = True

        target._update_history_and_process(
            hist_msg=f"Interpolated to {new_freq}Hz",
            last_process=f"_interpto_{new_freq}Hz"
        )
        return target

    def _resampling_duration(self, what: str, consequence: str) -> float:
        """The source span the two resamplers spread their grid across.

        Shared by `interpto_hz` and `interpto_samples`, which both build
        `linspace(first, last, n)` and both have nothing to build it over
        when the span is zero, negative or unmeasurable. `interpto_hz` has
        checked since #38; `interpto_samples` did not, and on a one-sample
        source returned n copies of one value at n copies of one timestamp
        - then, once the `data` setter refused a length change on such a
        source (#65), failed there instead, with a message about an
        assignment the caller never wrote (review round 1). One check, two
        wordings: `what` names the request, `consequence` says why the
        degenerate span defeats it.

        `duration()` is `float(index[-1] - index[0])`, which raises
        TypeError on a non-numeric index (a DatetimeIndex used to reach it
        and yield a Timedelta; since #100 the constructor converts one to
        seconds, and an object index of strings is what remains). Caught so
        both methods keep the ValueError contract
        their docstrings promise rather than leaking a conversion error
        from two frames down.
        """
        try:
            duration = self.duration()
        except (TypeError, ValueError):
            duration = np.nan
        if not np.isfinite(duration) or duration <= 0:
            raise ValueError(
                f"{what}: the source time base is degenerate (duration "
                f"{duration}). A zero, negative or unmeasurable span "
                f"{consequence}"
            )
        return duration

    def interpto_samples(self, new_len: int, kind: str = 'linear', inplace: bool = False) -> "baseTs":
        """
        Interpolate the times to a new length.

        Args:
            new_len (int): The desired new length of the interpolated times.
            kind (str, optional): The type of interpolation to use. Defaults to 'linear'.
            inplace (bool, optional): If True, modifies existing object. Otherwise returns a new object. Defaults to False.

        Returns:
            baseTs: Interpolated data

        Raises:
            ValueError: if the source spans no positive, finite duration
                (empty, a single sample, first and last timestamps
                coinciding, reversed, or a non-numeric index) - there is
                nothing to spread the new grid across, whatever `new_len`.
        """
        self._resampling_duration(
            f"Cannot interpolate to {new_len} samples",
            "has nothing to spread the new grid across.")

        def interp_func(data):
            new_ts = np.linspace(self.times[0], self.times[-1], new_len)
            f1 = interpolate.interp1d(self.times, data, kind=kind)
            return f1(new_ts), new_ts

        def process_result(result):
            data, times = result
            if inplace:
                self.data = data
                # The times setter recomputes freq via
                # _calculate_effective_frequency - do not overwrite it with
                # new_len / duration(), which over-reports by n/(n-1).
                self.times = times
                self.is_interpolated = True
                self.is_uniform_grid = True
                return self
            else:
                new_obj = self.copy()
                new_obj.data = data
                new_obj.times = times
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

    def interp_to_uniform_grid(
        self,
        new_grid: np.array = None,
        kind: str = 'linear',
        inplace: bool = True,
        fill_value: Optional[float] = None,
        max_gap: Optional[float] = None,
    ) -> "baseTs":
        """
        Interpolate data to a uniform sampling grid.
        If new_grid is not specified, use the existing info to create a new uniform grid
        of the same duration at the average effective sample rate.

        Interpolation bridges every interval between consecutive samples,
        however wide. That is right for jitter and wrong for a hole in the
        recording: pass ``max_gap`` to leave grid points that fall inside an
        interval wider than that as NaN instead. This is not
        ``interpolate_gaps()``, which fills holes; this refuses to.

        Args:
            new_grid (np.array, optional): The desired new sampling grid. Defaults to None.
            kind (str, optional): The type of interpolation to use. Defaults to 'linear'.
            inplace (bool, optional): If True, modifies existing object. Otherwise returns a new object. Defaults to True.
            fill_value (float, optional): Value for grid points outside
                ``[times[0], times[-1]]``. ``np.nan`` pads a short trial out
                to a longer common grid so that ``baseDf.from_series`` can
                stack ragged trials and ``average(skipna=True, min_count=k)``
                can count contributors per timepoint. Default None: a grid
                point outside the data raises ``ValueError``, as before.
            max_gap (float, optional): Widest interval between consecutive
                source samples, in seconds, that may be bridged. Grid points
                strictly inside a wider interval are left as NaN; a grid point
                landing exactly on a sample keeps that sample's value.
                Default None: every interval is bridged, as before.

        Returns:
            new_ts: baseTs object with uniform sampling grid
                    Note: freq is recalculated to match the new grid, unless
                    a declared rate survives the change - see breaking
                    change 8. With new_grid=None the new grid is
                    linspace(t0, t1, len(data)), which preserves
                    (len, first, last), so a declaration on the source
                    carries over even though interior spacing changed.

        Raises:
            ValidationError: If ``fill_value`` is not a number, or ``max_gap``
                is not a positive finite number.
            ValueError: If ``new_grid`` is not monotonically increasing, or
                reaches outside the data with ``fill_value=None``.

        Note:
            The padded or blanked result carries NaN, and the filters refuse
            gapped data; trim to the covered span before filtering an average
            built this way.
        """
        if fill_value is not None and (
            isinstance(fill_value, bool) or not isinstance(fill_value, numbers.Real)
        ):
            raise ValidationError(
                f"fill_value must be a number (np.nan to pad with NaN) or None to "
                f"raise on grid points outside the data; got {fill_value!r}. "
                f"scipy's 'extrapolate' is deliberately not accepted: extrapolated "
                f"samples would be indistinguishable from measured ones."
            )
        if max_gap is not None and (
            isinstance(max_gap, bool)
            or not isinstance(max_gap, numbers.Real)
            or not math.isfinite(max_gap)
            or max_gap <= 0
        ):
            raise ValidationError(
                f"max_gap must be a positive finite number of seconds, or None to "
                f"bridge every interval; got {max_gap!r}."
            )
        if new_grid is None:
            # create new evenly spaced grid at the effective sample rate
            new_grid = np.linspace(self.times[0], self.times[-1], len(self.data))
        else:
            if not np.all(np.diff(new_grid) > 0):
                raise ValueError("new_grid must be monotonically increasing.")

        if fill_value is None:
            f1 = interpolate.interp1d(self.times, self.data, kind=kind)
        else:
            f1 = interpolate.interp1d(self.times, self.data, kind=kind,
                                      bounds_error=False, fill_value=fill_value)
        last_process = "_unigrid"
        transfer = np.asarray(f1(new_grid), dtype=float)
        n_padded = 0
        if fill_value is not None:
            n_padded = int(np.count_nonzero(
                (new_grid < self.times[0]) | (new_grid > self.times[-1])))
        n_blanked = 0
        if max_gap is not None:
            n_blanked = self._blank_wide_gaps(new_grid, transfer, max_gap)
        # Parameters go in the operation head, before the first "; ", and the
        # per-series counts after it: baseDf.average compares histories by
        # head (frame_average.operation_head), so the same call on trials
        # padded by different amounts is one shared step rather than a
        # divergence, while a different max_gap is a real one.
        params = ""
        if fill_value is not None:
            params += f", fill_value={fill_value}"
        if max_gap is not None:
            params += f", max_gap={max_gap}s"
        extra = ""
        if n_padded:
            extra += f"; {n_padded} grid point(s) outside the data padded with {fill_value}"
        if n_blanked:
            extra += (f"; {n_blanked} grid point(s) inside gap(s) wider than "
                      f"max_gap left as NaN")
        # freq is not assigned here - it is read, not computed, whenever the
        # property is accessed below. A surviving declaration is honoured (see
        # breaking change 8: this grid preserves (len, first, last) when
        # new_grid is None); otherwise the getter derives via
        # _calculate_effective_frequency, which does not over-report by
        # n/(n-1) the way len(new_grid) / self.duration() did.
        # The rate is rounded in the message: a derived rate carries float
        # noise from the grid spacing (9.999999999999998) while a surviving
        # declaration on a same-shape trial reads 10.0, and printing both at
        # full precision split otherwise identical steps when averaging.
        if inplace is False:
            newTs = self.copy()
            newTs.data = transfer
            newTs.times = new_grid
            newTs.is_uniform_grid = True
            hist_msg = (f"Interpolated to uniform grid of n={len(new_grid)} @ "
                        f"{round(newTs.freq, 6)}Hz{params}{extra}")
            newTs._update_history_and_process(hist_msg, last_process)
            newTs.is_interpolated = True
            newTs.is_uniform_grid = True
            return newTs
        else:
            self.data = transfer
            self.times = new_grid
            self.is_uniform_grid = True
            hist_msg = (f"Interpolated to uniform grid of n={len(new_grid)} @ "
                        f"{round(self.freq, 6)}Hz{params}{extra}")
            self._update_history_and_process(hist_msg, last_process)
            self.is_interpolated = True
            self.is_uniform_grid = True
            return self

    def _blank_wide_gaps(self, new_grid: np.ndarray, values: np.ndarray,
                         max_gap: float) -> int:
        """Set to NaN, in place, the grid points bridging a gap wider than max_gap.

        A grid point strictly between two consecutive source samples more
        than ``max_gap`` apart is a bridge, not data. Points at or outside
        the data's ends are left alone: they are the ``fill_value`` case.

        Args:
            new_grid: The grid the data was interpolated onto.
            values: The interpolated values, modified in place.
            max_gap: Widest bridgeable interval in seconds.

        Returns:
            int: How many points were blanked.
        """
        times = np.asarray(self.times, dtype=float)
        if len(times) < 2:
            return 0
        widths = np.diff(times)
        # Index of the source interval each grid point sits in: searchsorted
        # with side='right' puts an exact hit on times[i] into interval i,
        # whose left edge is the hit itself, so we must test strictness
        # separately rather than trust the interval alone.
        idx = np.searchsorted(times, new_grid, side="right") - 1
        interior = (idx >= 0) & (idx < len(widths))
        safe_idx = np.clip(idx, 0, len(widths) - 1)
        strictly_inside = interior & (new_grid > times[safe_idx])
        blank = strictly_inside & (widths[safe_idx] > max_gap)
        values[blank] = np.nan
        return int(np.count_nonzero(blank))

    def notch_at(self, cutoff_hz: float, order: int = 5, inplace: bool = False) -> "baseTs":
        """
        Apply a notch filter at the specified frequency.

        The stopped band is `cutoff_hz +/- 1% of Nyquist`
        (`filters.NOTCH_HALF_WIDTH`), so the notch must sit more than that
        half-width from both 0 Hz and Nyquist.
        
        Args:
            cutoff_hz: Notch frequency in Hz
            order: Filter order
            inplace: If True, modifies existing object. Otherwise returns new object.
            
        Returns:
            Notch filtered baseTs object

        Raises:
            InvalidParameterError: If the notch lies within the half-width of
                either end, the rate is unusable, or the data has gaps (#76).
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

    def notch_filter(self, freq: float, order: int = 4, inplace: bool = False) -> "baseTs":
        """
        Apply a notch filter at the specified frequency (alias for notch_at).

        Args:
            freq: Notch frequency in Hz
            order: Filter order
            inplace: If True, modifies existing object. Otherwise returns new object.

        Returns:
            Notch filtered baseTs object
        """
        return self.notch_at(freq, order, inplace)

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

    def highpass_filter(self, cutoff: float, order: int = 4, inplace: bool = False) -> "baseTs":
        """
        Apply a highpass filter at the specified cutoff frequency (alias for highpass_at).

        Args:
            cutoff: Highpass cutoff frequency in Hz
            order: Filter order
            inplace: If True, modifies existing object. Otherwise returns new object.

        Returns:
            Highpass filtered baseTs object
        """
        return self.highpass_at(cutoff, order, inplace)

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

    def lowpass_filter(self, cutoff: float, order: int = 5, inplace: bool = False) -> "baseTs":
        """
        Apply a lowpass filter to the data.
        
        Args:
            cutoff: Lowpass cutoff frequency in Hz
            order: Filter order
            inplace: If True, modifies existing object. Otherwise returns new object.
            
        Returns:
            Lowpass filtered baseTs object
        """
        
        return self.lowpass_at(cutoff, order, inplace)
        


    def gauss_filter(self, sigma: float = 1, inplace: bool = False) -> "baseTs":
        """
        Apply a Gaussian filter to the data.
        
        Args:
            sigma: Standard deviation for Gaussian kernel
            inplace: If True, modifies existing object. Otherwise returns new object.
            
        Returns:
            Gaussian filtered baseTs object. An object-dtype series of reals
            comes back as float64 and one holding complex as complex128; a
            numeric series is passed to scipy as it is and keeps its dtype
            (integers in, integers out).

        Raises:
            ValueError: If the data is not numeric (text, `Decimal`, ...) or
                holds datetimes or durations - the shared data guard's
                messages. NaN is not an error here: a windowed convolution
                widens a gap rather than poisoning the output (see the
                sg_filter/gauss_filter note in API.md).
            RuntimeError: scipy's own, for a numeric dtype ndimage does not
                take - float16 is the one in practice. Cast to float32 or
                float64 first.
        """
        def gauss_func(data):
            # The dtype half of the shared guard only (#93): gaussian_filter
            # refuses an object array with a bare RuntimeError, and this
            # method never called the guard because the guard's finiteness
            # rule is deliberately not this method's. Complex is allowed -
            # gaussian_filter handles it part by part, as filtfilt does for
            # the Butterworth family (#75).
            return gaussian_filter(coerce_numeric_data(data, allow_complex=True), sigma)
            
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

    def bandpass_filter(self, low_cutoff: float, high_cutoff: float, order: int = 4,
                         inplace: bool = False) -> "baseTs":
        """
        Apply a bandpass filter between two cutoff frequencies (alias for bandpass_at).

        Args:
            low_cutoff: High-pass cutoff frequency in Hz (maps to bandpass_at's hp_hz)
            high_cutoff: Low-pass cutoff frequency in Hz (maps to bandpass_at's lp_hz)
            order: Accepted for signature compatibility; the underlying filter has no
                order parameter, so this is currently unused.
            inplace: If True, modifies existing object. Otherwise returns new object.

        Returns:
            Bandpass filtered baseTs object
        """
        return self.bandpass_at(hp_hz=low_cutoff, lp_hz=high_cutoff, inplace=inplace)

    def butterpass_at(self, hp_freq: float, lp_freq: float, inplace: bool = False) -> "baseTs":
        """
        Apply a Butterworth bandpass filter (alias for bandpass_at).

        Args:
            hp_freq: High-pass cutoff frequency in Hz (maps to bandpass_at's hp_hz)
            lp_freq: Low-pass cutoff frequency in Hz (maps to bandpass_at's lp_hz)
            inplace: If True, modifies existing object. Otherwise returns new object.

        Returns:
            Bandpass filtered baseTs object

        Notes:
            This delegated body replaces one that passed keyword arguments
            filters.bandpass_filter does not accept, so every call raised
            TypeError (#27). History therefore records the bandpass_at entry:
            calling the shipped method could not reach the old "_btrp_" token,
            and the sibling bandpass_filter alias already records itself this
            way. See docs/CHANGELOG.md for the one contrived way the old token
            was reachable.
        """
        return self.bandpass_at(hp_hz=hp_freq, lp_hz=lp_freq, inplace=inplace)

    def set_outlier_filter(self,
                        params: dict = None,
                        z_threshold: Optional[float] = None,
                        frac: Optional[float] = None,
                        max_iterations: Optional[int] = None,
                        interpolation_method: Optional[str] = None,
                        order: Optional[int] = None,
                        use_median: Optional[bool] = None,
                        tails: Union[str, TailType, None] = None,
                        num_fits: Optional[int] = None,
                        *,
                        it: Optional[int] = None,
                        delta_frac: Optional[float] = None,
                        fill_input_gaps: Optional[bool] = None) -> "baseTs":
        """
        Set outlier filter parameters.

        Parameters
        ----------
        params : dict, optional
            Dictionary of parameter values. If provided, overrides individual parameters.
            Valid keys are: 'z_threshold', 'frac', 'max_iterations', 'interpolation_method',
            'order', 'use_median', 'tails', 'it', 'delta_frac'
        z_threshold : float, optional
            Z-score threshold for outlier detection
        frac : float, optional
            LOWESS bandwidth: the fraction of points included in each local
            regression window. This is *not* the fraction of points expected to
            be outliers.
        max_iterations : int, optional
            Maximum number of iterations for outlier detection
        interpolation_method : str, optional
            Interpolation method for replacing outliers
        order : int, optional
            Order of the interpolation
        use_median : bool, optional
            Whether to use median instead of mean for calculations
        tails : Union[str, TailType], optional
            Which tails to process for outlier detection. Can be 'BOTH', 'UPPER', 'LOWER',
            or a TailType enum member.
        it : int, optional, keyword-only
            Robustifying iterations performed inside the LOWESS fit. Leave at 0
            unless you know why you want otherwise; see FilterConfig.
            Keyword-only so that it cannot occupy num_fits' old positional slot.
        delta_frac : float, optional, keyword-only
            Speed/accuracy tradeoff for long series. See FilterConfig.
        fill_input_gaps : bool, optional, keyword-only
            Whether to also interpolate NaNs that were already in the input.
            Defaults to False - see FilterConfig. Samples this filter blanks
            itself are always interpolated regardless.
        num_fits : int, optional
            Deprecated and ignored. Was the number of LOWESS anchor fits under the
            moepy backend, which has been replaced by statsmodels. Use
            ``delta_frac`` for the equivalent speed/accuracy tradeoff.

        Returns
        -------
        self
            Returns the instance for method chaining
        
        Notes
        -----
        Only the parameters you name are changed; the rest keep their current
        values. An unconfigured object starts at FilterConfig's defaults
        (z_threshold=3.0, max_iterations=5, frac=0.075). Calling this with no
        arguments therefore changes nothing - it is not a way to reset.

        You must re-run filter_outliers to use the new parameters.
        """
        if num_fits is not None or (params is not None and 'num_fits' in params):
            warnings.warn(
                "num_fits is deprecated and ignored: the LOWESS backend moved from "
                "moepy to statsmodels, which has no equivalent parameter. Use "
                "delta_frac for the same speed/accuracy tradeoff.",
                DeprecationWarning,
                stacklevel=2,
            )

        valid_params = {
            'z_threshold': float,
            'frac': float,
            'max_iterations': int,
            'interpolation_method': str,
            'order': int,
            'use_median': bool,
            'tails': (str, TailType),
            'it': int,
            'delta_frac': float,
            'fill_input_gaps': bool
        }

        # The floor each integer field's rule states (#78). A pass count and
        # an interpolation order must exist; the robustifying iterations
        # inside the LOWESS fit default to 0 and may stay there.
        int_floors = {'max_iterations': 1, 'order': 1, 'it': 0}

        def _coerce(param_name, value):
            """Validate one parameter, converting where the type allows."""
            param_type = valid_params[param_name]
            # The integer fields follow the filters' policy rather than the
            # generic int() branch below, which stored 4 for 4.7 and 5 for
            # '5', and passed a bool through as the int it is (#78). The
            # rejection is InvalidParameterError, which is a ValueError, so
            # the contract this method has always made still holds.
            if param_type is int:
                return _require_int(param_name, value, minimum=int_floors[param_name])
            if param_name == 'tails':
                if isinstance(value, str):
                    try:
                        return TailType[value.upper()]
                    except KeyError:
                        raise ValueError(
                            f"Invalid string value for tails: {value}. "
                            "Must be 'BOTH', 'UPPER', or 'LOWER'.")
                if not isinstance(value, TailType):
                    raise ValueError(
                        "Invalid type for tails. Expected str or TailType, "
                        f"got {type(value)}.")
                return value
            # bool before the generic branch: bool("False") is True, because
            # every non-empty string is truthy. That silently inverts a flag
            # supplied from JSON, a CLI or an env var - and for
            # fill_input_gaps it would reinstate exactly the data-inventing
            # behaviour the caller was trying to switch off.
            if param_type is bool and not isinstance(value, bool):
                if isinstance(value, str):
                    if value.strip().lower() in ('true', '1', 'yes'):
                        return True
                    if value.strip().lower() in ('false', '0', 'no'):
                        return False
                    raise ValueError(
                        f"Invalid value for {param_name}: {value!r}. "
                        f"Expected a bool, or one of 'true'/'false'.")
                if isinstance(value, (int, np.integer)) and value in (0, 1):
                    return bool(value)
                raise ValueError(
                    f"Invalid type for {param_name}. Expected bool, "
                    f"got {type(value).__name__}")

            if not isinstance(value, param_type):
                try:
                    return param_type(value)
                except (TypeError, ValueError):
                    raise ValueError(
                        f"Invalid type for {param_name}. "
                        f"Expected {param_type.__name__}")
            return value

        # Only the parameters actually named by the caller are changed. They
        # used to carry real defaults, so set_outlier_filter(frac=...) quietly
        # reset z_threshold to 7 and max_iterations to 10 as well.
        if params is not None:
            updates = {name: _coerce(name, params[name])
                       for name in valid_params if name in params}
        else:
            supplied = {
                'z_threshold': z_threshold, 'frac': frac,
                'max_iterations': max_iterations,
                'interpolation_method': interpolation_method,
                'order': order, 'use_median': use_median, 'tails': tails,
                'it': it, 'delta_frac': delta_frac,
                'fill_input_gaps': fill_input_gaps,
            }
            updates = {name: _coerce(name, value)
                       for name, value in supplied.items() if value is not None}

        # Rebind rather than mutate. FilterConfig is frozen and the filter is
        # rebuilt, so derived objects can share a filter safely: configuring
        # one of them cannot be seen by the others.
        current = getattr(self, 'outlier_filter', None)
        base_config = current.config if current is not None else FilterConfig()
        self.outlier_filter = LowessOutlierFilter(replace(base_config, **updates))

        hist_msg = f"Set new outlier filter parameters: {self.outlier_filter.config.__dict__}"
        last_process = "_outfilt_params"
        
        self.is_outlier_filtered = True
        self._update_history_and_process(hist_msg, last_process)
    
        return self

    def get_outlier_filter_params(self) -> dict:
        """
        Get outlier filter parameters as a plain dict.

        A snapshot, not the live config. Objects derived from one another share
        a filter - that is safe only because nothing mutates a config in place,
        and handing out the real ``__dict__`` would have made a write through
        this dict reach every one of them. frozen=True does not stop that:
        it blocks setattr, not __dict__ assignment.

        Feed it back through ``set_outlier_filter(params=...)``, which is where
        the values get validated.
        """
        return dict(self.outlier_filter.config.__dict__)
        
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
        
        # Counted here, not stashed on the filter: copy() deliberately shares
        # outlier_filter by reference, so an attribute written during filter()
        # would be visible to - and overwritten by - every object sharing that
        # filter. The count belongs to this call, not to the filter.
        n_gaps = int(np.count_nonzero(np.isnan(np.asarray(self.data, dtype=float))))

        filt, idx, lowess_fit = self.outlier_filter.filter(self, return_lowess=True)
        hist_msg = f"Filtered outliers with lowess: {self.outlier_filter.config.__dict__}"
        # Say what was left alone, not just what was configured. Silently
        # returning a series that is part synthetic is the failure #36 is
        # about, and the history is where a reader looks to find out.
        if n_gaps:
            if self.outlier_filter.config.fill_input_gaps:
                hist_msg += f"; interpolated {n_gaps} pre-existing gap sample(s)"
            else:
                hist_msg += f"; left {n_gaps} pre-existing gap sample(s) as NaN"
        last_process = "_outfilt"

        # Snapshot the pre-filter state before either branch below mutates self.
        # qc_plot draws ts.data as "Original", so passing self after an inplace
        # filter plotted the result against itself. Taken only when a plot was
        # asked for, so the copy stays off the normal filtering path.
        qc_base = self.copy() if qcplot else None

        if inplace is True:
            self.data = filt.data
            self.times = filt.times
            self.is_outlier_filtered = True
            self._update_history_and_process(hist_msg, last_process)
            self.lowess_fit = lowess_fit
            self.outlier_indices = idx
            result = self 
        else:
            newTs = self.copy()
            newTs.data = filt.data
            newTs.times = filt.times
            newTs._update_history_and_process(hist_msg, last_process)
            newTs.is_outlier_filtered = True
            newTs.lowess_fit = lowess_fit
            newTs.outlier_indices = idx
            result = newTs

        # is_interpolated is set by the filter on the series it returns,
        # exactly when it replaced an outlier or filled an input gap (#90).
        # This wrapper borrows only the arrays from `filt`, so the flag is
        # carried over here rather than re-derived.
        if filt.is_interpolated:
            result.is_interpolated = True

        if qcplot:
            # Carry the new fit and label on the snapshot, not on self: with
            # inplace=False the caller's object must come back untouched, and
            # qc_plot gates its "Lowess Fit" trace on lowess_fit being set.
            qc_base.lowess_fit = lowess_fit
            qc_base.last_process = last_process
            _ = qc_plot(qc_base, filt.data, filt.times, show=show_plot, ax=ax)
        
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

        Linear interpolation across every NaN, with any leading or trailing
        gap filled from the nearest valid sample. The index is unchanged.

        Args:
            inplace: If True, modifies existing object. Otherwise returns a new object.

        Returns:
            Processed baseTs object
        """
        # `interpolate_missing_values(inplace=True)` mutates its argument and
        # returns None, the pandas convention. This method used to forward
        # `inplace` and then read `.data` off the return value, so the
        # inplace branch raised on every call from the day it was written
        # (#64). The helper's contract is kept; the branch that knows the
        # answer is None does not ask for it.
        # is_interpolated is set by the helper, on the producer, exactly when
        # it filled a gap (#90); this wrapper adds only the history line.
        if inplace:
            interpolate_missing_values(self, inplace=True)
            processed = self
        else:
            processed = interpolate_missing_values(self, inplace=False)
        processed._update_history_and_process(
            hist_msg="Interpolated missing values in timeseries",
            last_process="_interp"
        )
        return processed
    
    def diff_ts(self, zeropad: bool = False, inplace: bool = False) -> "baseTs":
        """
        Compute the first difference of the timeseries.

        Args:
            zeropad: If True, the first difference is repeated at the front so
                the result keeps this series' length and index. Otherwise the
                result is one sample shorter and starts at the second timestamp.
            inplace: If True, modifies existing object. Otherwise returns new object.

        Raises:
            ValidationError: If the series has fewer than two samples (#89).
                A `ValueError`; the series is left unchanged.
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
        # Use pandas rolling capabilities directly
        rolling_result = self.rolling(window, center=center).mean()
        # Remove NaN values and corresponding times
        valid_mask = ~rolling_result.isna()
        new_data = rolling_result[valid_mask].values
        new_times = rolling_result[valid_mask].index.values
        
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
        # Use pandas rolling capabilities directly
        rolling_result = self.rolling(window, center=center).std()
        valid_mask = ~rolling_result.isna()
        new_data = rolling_result[valid_mask].values
        new_times = rolling_result[valid_mask].index.values

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
        # Use pandas rolling capabilities directly
        rolling_result = self.rolling(window, center=center).median()
        valid_mask = ~rolling_result.isna() 
        new_data = rolling_result[valid_mask].values
        new_times = rolling_result[valid_mask].index.values

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
        # Use pandas rolling capabilities directly
        rolling_result = self.rolling(window, center=center).max()
        valid_mask = ~rolling_result.isna() 
        new_data = rolling_result[valid_mask].values
        new_times = rolling_result[valid_mask].index.values

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
        # Use pandas rolling capabilities directly
        rolling_result = self.rolling(window, center=center).min()
        valid_mask = ~rolling_result.isna() 
        new_data = rolling_result[valid_mask].values
        new_times = rolling_result[valid_mask].index.values

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
        
    def _bound_in_seconds(self, bound, which: str):
        """A time_slice bound as seconds on the index.

        A number is seconds on the index, as it always was - `numbers.Number`,
        not `numbers.Real`: `Decimal` registers under the former only, and
        the first cut's `Real` test sent a `Decimal` bound that `main`
        compared fine down the calendar branch, to a "no timestamp origin"
        error (review round 1, codex; the #30 lesson again). Anything else
        is a calendar bound - a date string, a datetime, a date, a
        numpy datetime64, a Timestamp - parsed by `pd.Timestamp`, and placed
        against the origin the way the index's own seconds were: as integer
        nanoseconds divided by 1e9, so a bound that names a sample lands on
        that sample exactly. Two conversions have to agree for that: the
        index's seconds come from the *vectorised*
        `TimedeltaIndex.total_seconds()`, which is nanosecond-exact, while
        the scalar `Timedelta.total_seconds()` a bound would naturally use
        rounds to the microsecond (`Timedelta('500ns').total_seconds()` is
        0.0 on pandas 2.2.3, 2.3.3 and 3.0.1). They give the same float for
        the same stamp on all three legs, pinned across a 10 ms, a
        microsecond and a nanosecond grid. An aware bound is an instant,
        like an aware index.

        Raises:
            TypeError: a calendar bound on a series that cannot place one -
                no origin, or an index the recorded origin no longer
                describes. The message is `_origin_problem`'s.
            ValueError: a string `pd.Timestamp` cannot parse.
        """
        if bound is None or isinstance(bound, numbers.Number):
            return bound
        # Before parsing: on a series with no origin the mistake is the kind
        # of bound, whatever the string says, and that is the message owed.
        # The same helper `datetimes` reads decides whether the origin
        # applies to the index the series holds now.
        problem = _origin_problem(self)
        if problem is not None:
            raise TypeError(
                f"time_slice got a calendar bound for {which} ({bound!r}), but "
                f"{problem} Pass seconds instead.")
        stamp = pd.Timestamp(bound)
        if stamp.tz is not None:
            stamp = stamp.tz_convert(None)
        return (stamp - _origin_timestamp(self.ts_offset)).value / 1e9

    def time_slice(self, start_time=None, end_time=None,
                   inplace: bool = False) -> "baseTs":
        """
        Slice the time series between start and end times, inclusive.

        Args:
            start_time: Start bound: seconds on the index, or - on a series
                with a timestamp origin - a date string or datetime-like,
                converted through the origin. None means the beginning.
            end_time: End bound, same rule. None means the end.
            inplace: If True, modifies existing object. Otherwise returns new object.

        Returns:
            Time-sliced baseTs object

        Raises:
            TypeError: a date string or datetime-like bound on a series with
                no timestamp origin (one built from seconds and never given
                one). A `start_time` after `end_time` is not rejected; it
                returns an empty series.
        """
        start_secs = self._bound_in_seconds(start_time, "start_time")
        end_secs = self._bound_in_seconds(end_time, "end_time")
        if start_secs is None:
            start_secs = self.index[0]
        if end_secs is None:
            end_secs = self.index[-1]

        # Use pandas boolean indexing for time range
        mask = (self.index >= start_secs) & (self.index <= end_secs)
        sliced_series = self[mask]
        new_data = sliced_series.values
        new_times = sliced_series.index.values
        
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
        # Use pandas describe() for efficient statistics calculation
        stats_series = self.describe()
        
        stats = {
            'count': int(stats_series['count']),
            'mean': stats_series['mean'],
            'std': stats_series['std'],
            'min': stats_series['min'],
            'max': stats_series['max'],
            'median': stats_series['50%'],
            'q25': stats_series['25%'],
            'q75': stats_series['75%'],
            'duration': self.duration(),
            'frequency': self.freq,
            # n samples span n-1 intervals - see _calculate_effective_frequency.
            'sample_rate': (len(self) - 1) / self.duration() if self.duration() > 0 else 0
        }
        
        return stats
    
    # Enhanced Pandas Time-Series Methods
    
    def resample(self, freq: str, method: str = 'mean', **kwargs) -> "baseTs":
        """
        Resample time series to a different frequency using pandas resampling.
        
        Args:
            freq: Target frequency string (e.g., '1s', '100ms', '0.1s')
            method: Aggregation method ('mean', 'median', 'sum', 'min', 'max', 'std')
            **kwargs: Additional arguments passed to pandas resample
            
        Returns:
            Resampled baseTs object
            
        Examples:
            # Downsample to 1Hz
            ts_1hz = ts.resample('1s', method='mean')
            
            # Upsample to 100Hz with interpolation
            ts_100hz = ts.resample('10ms', method='mean')
        """
        # Create time-based index from numeric times
        time_index = pd.to_timedelta(self.index, unit='s')
        temp_series = pd.Series(self.values, index=time_index)
        
        # Resample using pandas
        resampled = temp_series.resample(freq).agg(method, **kwargs)
        
        # Convert back to numeric times
        new_times = resampled.index.total_seconds().values
        new_data = resampled.values
        
        # Create new baseTs object
        new_obj = self._create_new_with_data(new_data, new_times)
        new_obj._update_history_and_process(
            f"Resampled to {freq} using {method}",
            f"_resample_{freq}_{method}"
        )
        
        return new_obj
    
    def interpolate_gaps(self, method: str = 'linear', limit: int = None, 
                        order: int = None, inplace: bool = False, **kwargs) -> "baseTs":
        """
        Interpolate missing values (NaN) in the time series.
        
        Args:
            method: Interpolation method ('linear', 'time', 'spline', 'polynomial', 'cubic', etc.)
            limit: Maximum number of consecutive NaN values to interpolate
            order: Order for polynomial/spline interpolation (default: 1 for polynomial, 3 for spline)
            inplace: If True, modifies existing object. Otherwise returns new object.
            **kwargs: Additional parameters passed to pandas interpolate method.
                The one to know about is `limit_direction` - see "Edge gaps".

        Edge gaps:
            pandas' default `limit_direction='forward'` fills nothing before
            the first valid sample, so a gap at the *start* of the series
            survives the default call and the spectral and filter guards
            reject the result with the same message that sent you here (#77).
            Pass `limit_direction='both'` to extend the first valid value back
            over the edge. That edge fill is a constant extension, not an
            interpolation - there is nothing on the far side to interpolate
            towards - which is why it is not the default: this method does not
            invent values unless asked, for the same reason #36 stopped
            `filter_outliers` doing so. A *trailing* gap is already extended
            by the default. These statements hold for the pandas-native
            methods ('linear', 'time', 'index', 'values'); the scipy-backed
            methods behave differently at an edge in either direction:
            'cubic', 'quadratic', 'slinear', 'zero', 'nearest', 'polynomial',
            'krogh', 'piecewise_polynomial', 'akima' and 'from_derivatives'
            leave it unfilled, while 'spline', 'pchip', 'cubicspline' and
            'barycentric' extrapolate their fit over it. A `limit` caps the
            edge fill like any other: limit=2 clears two samples of a
            four-sample leading gap and leaves the rest. A series with no
            valid sample at all cannot be filled by any of these.

        Object dtype:
            An object-dtype series of numbers (the constructor keeps the
            dtype it is given) is interpolated as float64, or complex128 if
            any value is complex, with `None` and `pd.NA` read as gaps; the
            result has that dtype. pandas refuses to interpolate object
            dtype at all, so before #80 this raised a bare `TypeError` on
            exactly the input the data guard's NaN message had sent here.
            The classification is `utils.coerce_numeric_data`'s, the same
            one the guard makes.

        Returns:
            Interpolated baseTs object

        Raises:
            ValueError: If the series is object dtype and its values are not
                numbers (text, Decimal, ...), with the data guard's message.
            
        Examples:
            # Linear interpolation (default)
            ts_linear = ts.interpolate_gaps()

            # A gap at the start of the series needs the edge fill
            ts_edge = ts.interpolate_gaps(limit_direction='both')
            
            # Polynomial interpolation with order 2
            ts_poly = ts.interpolate_gaps(method='polynomial', order=2)
            
            # Spline interpolation with order 3
            ts_spline = ts.interpolate_gaps(method='spline', order=3)
            
            # Time-based interpolation (works with numeric time index)
            ts_time = ts.interpolate_gaps(method='time')
        """
        # An object-dtype series is settled to a numeric dtype first; pandas
        # cannot interpolate object dtype and said so with a bare TypeError
        # (#80). Only object dtype takes this path - every other dtype is
        # interpolated as it is, exactly as before - and a non-numeric one
        # raises the guard's own "not numeric" ValueError here.
        values = self.values
        if values.dtype.kind == "O":
            values = coerce_numeric_data(values, allow_complex=True)
            source = pd.Series(values, index=self.index)
        else:
            source = self

        # Handle special case for time method with numeric index
        if method == 'time':
            # For numeric time index, convert to timedelta for time interpolation
            time_index = pd.to_timedelta(self.index, unit='s')
            temp_series = pd.Series(values, index=time_index)
            interpolated = temp_series.interpolate(method=method, limit=limit, **kwargs)
            # Convert back to numeric index
            interpolated.index = interpolated.index.total_seconds()
        else:
            # Set default orders for polynomial and spline methods
            if order is None:
                if method == 'polynomial':
                    order = 1  # Linear polynomial by default
                elif method == 'spline':
                    order = 3  # Cubic spline by default
            
            # Apply interpolation with order parameter if needed
            if method in ['polynomial', 'spline'] and order is not None:
                interpolated = source.interpolate(method=method, order=order, limit=limit, **kwargs)
            else:
                interpolated = source.interpolate(method=method, limit=limit, **kwargs)
        
        # is_interpolated means "at least one value is an interpolated
        # estimate" (#90): set exactly when this call filled a gap. A limit
        # or a leading gap under forward fill can leave gaps behind - what
        # counts is whether any was filled, not whether all were.
        filled_a_gap = int(pd.isna(interpolated.values).sum()) < int(pd.isna(self.values).sum())
        if inplace:
            # Update current object
            self._adopt_data_inplace(interpolated.values, interpolated.index)
            order_str = f", order={order}" if order is not None else ""
            self._update_history_and_process(
                f"Interpolated gaps using {method}{order_str}",
                f"_interpolate_{method}"
            )
            if filled_a_gap:
                self.is_interpolated = True
            return self
        else:
            new_obj = self._create_new_with_data(interpolated.values, interpolated.index.values)
            order_str = f", order={order}" if order is not None else ""
            new_obj._update_history_and_process(
                f"Interpolated gaps using {method}{order_str}",
                f"_interpolate_{method}"
            )
            if filled_a_gap:
                new_obj.is_interpolated = True
            return new_obj
    
    def align_with(self, other: "baseTs", method: str = 'outer') -> tuple:
        """
        Align two time series on a common time index.
        
        Args:
            other: Another baseTs object to align with
            method: Join method ('outer', 'inner', 'left', 'right')
            
        Returns:
            Tuple of (aligned_self, aligned_other) as baseTs objects
        """
        aligned_self, aligned_other = self.align(other, join=method)
        
        # Convert back to baseTs objects
        new_self = self._create_new_with_data(
            aligned_self.values, 
            aligned_self.index.values
        )
        new_other = other._create_new_with_data(
            aligned_other.values, 
            aligned_other.index.values
        )
        
        new_self._update_history_and_process(
            f"Aligned with {other.signal_name} using {method} join",
            f"_align_{method}"
        )
        new_other._update_history_and_process(
            f"Aligned with {self.signal_name} using {method} join",
            f"_align_{method}"
        )
        
        return new_self, new_other
    
    def shift_time(self, periods: int, inplace: bool = False) -> "baseTs":
        """
        Shift the time series by a number of periods.
        
        Args:
            periods: Number of periods to shift (positive = forward, negative = backward)
            inplace: If True, modifies existing object. Otherwise returns new object.
            
        Returns:
            Time-shifted baseTs object
        """
        shifted = self.shift(periods=periods)
        
        if inplace:
            # Update current object, removing NaN values
            valid_mask = ~shifted.isna()
            self._adopt_data_inplace(
                shifted[valid_mask].values,
                shifted[valid_mask].index
            )
            self._update_history_and_process(
                f"Shifted time by {periods} periods",
                f"_shift_{periods}"
            )
            return self
        else:
            # Remove NaN values from shifted data
            valid_mask = ~shifted.isna()
            new_obj = self._create_new_with_data(
                shifted[valid_mask].values, 
                shifted[valid_mask].index.values
            )
            new_obj._update_history_and_process(
                f"Shifted time by {periods} periods",
                f"_shift_{periods}"
            )
            return new_obj
    
    def correlation_with(self, other: "baseTs", method: str = 'pearson') -> float:
        """
        Calculate correlation with another time series.
        
        Args:
            other: Another baseTs object
            method: Correlation method ('pearson', 'kendall', 'spearman')
            
        Returns:
            Correlation coefficient
        """
        # Align the time series first
        aligned_self, aligned_other = self.align_with(other, method='inner')
        
        # Calculate correlation
        return aligned_self.corr(aligned_other, method=method)
    
    def detect_outliers(self, method: str = 'zscore', threshold: float = 3.0) -> np.ndarray:
        """
        Detect outliers using statistical methods.
        
        Args:
            method: Detection method ('zscore', 'iqr', 'modified_zscore')
            threshold: Threshold for outlier detection
            
        Returns:
            Boolean array indicating outlier positions
        """
        if method == 'zscore':
            z_scores = np.abs((self.values - self.mean()) / self.std())
            return z_scores > threshold
        elif method == 'iqr':
            Q1 = self.quantile(0.25)
            Q3 = self.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            return (self.values < lower_bound) | (self.values > upper_bound)
        elif method == 'modified_zscore':
            # Iglewicz-Hoaglin modified z-score. Note pandas' removed Series.mad()
            # returned the MEAN absolute deviation about the mean, not the median
            # absolute deviation, so this is deliberately not a like-for-like
            # restoration - see CHANGELOG under "Behavior change".
            median = self.median()
            # nanmedian, not median: self.median() skips NaN, so a NaN-propagating
            # denominator would silently return an all-False mask.
            mad = np.nanmedian(np.abs(self.values - median))
            if mad > 0:
                modified_z_scores = 0.6745 * (self.values - median) / mad
            else:
                # MAD collapses when over half the values are identical. Iglewicz
                # and Hoaglin define a mean-absolute-deviation fallback for exactly
                # this case rather than leaving the score undefined.
                mean_val = np.nanmean(self.values)
                meanad = np.nanmean(np.abs(self.values - mean_val))
                if not meanad > 0:
                    warnings.warn(
                        "Series is constant; no outliers are detectable with "
                        "method='modified_zscore'.",
                        RuntimeWarning,
                        stacklevel=2,
                    )
                    return np.zeros(len(self), dtype=bool)
                modified_z_scores = (self.values - median) / (1.253314 * meanad)
            return np.abs(modified_z_scores) > threshold
        else:
            raise ValueError(f"Unknown outlier detection method: {method}")

    def remove_outliers(self, method: str = 'zscore', threshold: float = 3.0,
                         inplace: bool = False) -> "baseTs":
        """
        Remove points flagged by detect_outliers() from the series.

        This is the simple statistical counterpart to filter_outliers(): it drops
        outlier points rather than interpolating over them with the LOWESS-based
        outlier_filter workflow (see set_outlier_filter/filter_outliers).

        Args:
            method: Detection method passed to detect_outliers ('zscore', 'iqr',
                'modified_zscore')
            threshold: Threshold passed to detect_outliers
            inplace: If True, modifies existing object. Otherwise returns new object.

        Returns:
            baseTs object with outlier points removed
        """
        mask = self.detect_outliers(method=method, threshold=threshold)
        new_data = self.values[~mask]
        new_times = self.index.values[~mask]

        if inplace:
            self.data = new_data
            self.times = new_times
            self._update_history_and_process(
                f"Removed outliers using {method} method (threshold={threshold})",
                f"_rmoutliers_{method}"
            )
            return self
        else:
            new_obj = self._create_new_with_data(new_data, new_times)
            new_obj._update_history_and_process(
                f"Removed outliers using {method} method (threshold={threshold})",
                f"_rmoutliers_{method}"
            )
            return new_obj

    def get_frequency_content(self, window: str = None) -> tuple:
        """
        Get frequency domain representation using pandas-optimized FFT.
        
        Args:
            window: Window function to apply ('hann', 'hamming', 'blackman', None)
            
        Returns:
            Tuple of (frequencies, power_spectrum)

        Raises:
            ValueError: If the series is empty, if the sampling frequency is
                not usable (NaN, zero, or negative), if the data is complex or
                contains NaN or Inf, or if the window function is unknown
        """
        from scipy import signal

        # This method builds its own FFT rather than routing through
        # compute_fft_power, so it needs all three guards in its own right.
        # get_peak_freq, relative_band_power, falff and plot_fft_power all
        # arrive here, so this is where the family agrees (#28, #62).
        #
        # Checked against self.values rather than the windowed copy below, so
        # the error describes what the caller passed in. That placement is a
        # readability choice, not a correctness one: a window multiplies a NaN
        # through rather than removing it, so a check after windowing catches
        # the same inputs. Verified by mutation - moving it below does not
        # fail any test, and no test claims otherwise.
        validate_non_empty(self.values)
        validate_sampling_freq(self.freq)
        # The guard returns the array it checked, coerced where it had to
        # be (#75). Until #93 the result was discarded and the FFT ran on
        # self.values itself, so an object array of ordinary floats passed
        # the guard and died in np.fft with a bare TypeError. Nothing below
        # writes into `data` - a window multiplies into a new array - so the
        # numeric case, where the guard hands back self.values as is, needs
        # no copy.
        data = validate_finite_data(self.values)

        # Apply window function if specified
        if window:
            if window == 'hann':
                window_func = signal.windows.hann(len(data))
            elif window == 'hamming':
                window_func = signal.windows.hamming(len(data))
            elif window == 'blackman':
                window_func = signal.windows.blackman(len(data))
            else:
                raise ValueError(f"Unknown window function: {window}")
            data = data * window_func
        
        # Compute FFT
        freqs = np.fft.fftfreq(len(data), 1/self.freq)
        fft_data = np.fft.fft(data)
        power_spectrum = np.abs(fft_data) ** 2
        
        # Return only positive frequencies
        positive_freq_mask = freqs >= 0
        return freqs[positive_freq_mask], power_spectrum[positive_freq_mask]
    
    # Utility functions
    
    def compute_fft_power(self, max_rate: float = np.nan, demean: bool = True, scale_power: bool = True) -> tuple:
        """
        Compute the FFT power of the timeseries.

        Computed on a float64 copy of the data: an integer, bool or
        narrower-float series gives exactly its float64 cast's spectrum
        (#96). See utils.compute_fft_power.

        Raises:
            ValueError: If the series is empty or has fewer than two samples,
                if the sampling frequency is not usable, if the data is
                complex or contains NaN or Inf, or if `max_rate` is invalid.
                See utils.compute_fft_power.
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

    def get_peak_freq(self, num_pks: int = 1, window: str = None, 
                     min_freq: float = None, max_freq: float = None) -> Union[float, List[float]]:
        """
        Compute the peak frequency(ies) of the timeseries using enhanced frequency analysis.
        
        Args:
            num_pks: Number of peak frequencies to return
            window: Window function to apply ('hann', 'hamming', 'blackman', None)
            min_freq: Minimum frequency to consider (Hz, defaults to exclude DC component)
            max_freq: Maximum frequency to consider (Hz, defaults to Nyquist)
            
        Returns:
            Single peak frequency (if num_pks=1) or list of peak frequencies

        Raises:
            ValueError: If the series is empty, if the sampling frequency is
                not usable, if the data is complex, or if it contains NaN or
                Inf. Fill gaps first, e.g. with interpolate_gaps() - an FFT
                over data containing NaN returns an all-NaN spectrum, from
                which any peak is meaningless.

        Examples:
            # Basic peak frequency
            peak = ts.get_peak_freq()
            
            # Top 3 peaks with Hanning window
            peaks = ts.get_peak_freq(num_pks=3, window='hann')
            
            # Peak in specific frequency range
            peak = ts.get_peak_freq(window='blackman', min_freq=1.0, max_freq=50.0)
        """
        from .utils import get_peak_freq
        return get_peak_freq(self, num_pks=num_pks, window=window, 
                           min_freq=min_freq, max_freq=max_freq)

    def relative_band_power(self, low_freq: float = 0.01, high_freq: float = 0.1,
                            ratio: str = 'power', window: str = None,
                            details: bool = False) -> Union[float, BandPowerResult]:
        """
        Compute the relative power (or amplitude) in a frequency band.

        This is the quantity behind fractional amplitude of low-frequency
        fluctuations (fALFF) and its EEG/HRV cousin, relative band power.

        The band defaults to 0.01-0.1 Hz, a common low-frequency band for
        resting-state fMRI and other slow physiological fluctuations. It is
        one convention among several: Zou et al. (2008) computed fALFF over
        0.01-0.08 Hz, and the HRV literature's LF band is 0.04-0.15 Hz.
        Pass both edges to measure a different band. The default does not relax the
        constraints below: the upper edge still has to sit at or below
        Nyquist, so a series sampled below 0.2 Hz raises, and at least one
        FFT bin still has to fall inside the band.

        The two conventions are not interchangeable:

        - ratio='power' sums |X(f)|^2 and gives the fraction of the signal's
          variance in the band. Parseval-exact, and roughly stable across
          sampling rates.
        - ratio='amplitude' sums |X(f)| and reproduces classic fALFF (Zou et
          al., 2008). Its denominator scales with the number of noise bins,
          so values are not comparable across different bandwidths.

        The DC (0 Hz) bin is always excluded from both numerator and
        denominator, so the result is robust to an undetrended mean offset.

        Preconditions:
            - Detrend first for meaningful results on trending data:
              ts.detrend('linear'). This method does not detrend for you;
              that belongs in your processing pipeline.
            - Resample to a uniform grid first if the series is irregular,
              since self.freq is an effective sampling frequency.
            - The series must be long enough to resolve the band. Resolution
              is 1 / duration, so a 0.01 Hz lower edge needs at least 100 s.

        Args:
            low_freq: Lower band edge in Hz (inclusive). Defaults to 0.01.
            high_freq: Upper band edge in Hz (inclusive). Defaults to 0.1.
            ratio: 'power' (variance fraction, default) or 'amplitude'
            window: Window function ('hann', 'hamming', 'blackman', None)
            details: If True, return a BandPowerResult breakdown instead of
                a bare float

        Returns:
            Relative band power as a float, or a BandPowerResult if
            details=True

        Raises:
            ValueError: If the band is invalid, exceeds Nyquist or is narrower
                than the frequency resolution, if the series is empty, if the
                data is complex or contains NaN or Inf, or if the signal has
                no spectral power outside DC. See utils.relative_band_power.

        Examples:
            # Fraction of variance in the default 0.01-0.1 Hz band
            ts.detrend('linear').relative_band_power()

            # A different band, here the HRV low-frequency band
            ts.relative_band_power(0.04, 0.15)

            # Classic fALFF convention (or use falff(), which defaults to it)
            ts.relative_band_power(ratio='amplitude')

            # Compare against the white-noise null
            res = ts.relative_band_power(details=True)
            print(res.ratio, res.bin_fraction)
        """
        return relative_band_power(self, low_freq, high_freq, ratio=ratio,
                                   window=window, details=details)

    def falff(self, low_freq: float = 0.01, high_freq: float = 0.1,
              ratio: str = 'amplitude', window: str = None,
              details: bool = False) -> Union[float, BandPowerResult]:
        """
        Fractional amplitude of low-frequency fluctuations (fALFF).

        Convenience wrapper around relative_band_power() using the
        convention from Zou et al. (2008), J Neurosci Methods 172(1):137-141.
        Both methods default to the same 0.01-0.1 Hz band, which is wider
        than the 0.01-0.08 Hz that paper used; pass (0.01, 0.08) to
        reproduce it.

        What differs is the convention, and the split is deliberate:
        relative_band_power() defaults to ratio='power' as the
        better-behaved general-purpose measure, while this method defaults
        to ratio='amplitude' so it reproduces published fALFF values.

        Caveat: amplitude-convention values are not comparable across
        acquisitions with different sampling rates or bandwidth. Use
        ratio='power' if you need that comparability.

        Args:
            low_freq: Lower band edge in Hz. Defaults to 0.01.
            high_freq: Upper band edge in Hz. Defaults to 0.1.
            ratio: 'amplitude' (default, classic fALFF) or 'power'
            window: Window function ('hann', 'hamming', 'blackman', None)
            details: If True, return a BandPowerResult breakdown

        Returns:
            fALFF value as a float, or a BandPowerResult if details=True

        Raises:
            ValueError: Everything relative_band_power raises, including an
                empty series; this is a thin wrapper over it.

        Examples:
            # Classic fALFF on a detrended signal
            ts.detrend('linear').falff()

            # The band Zou et al. (2008) used
            ts.falff(0.01, 0.08)
        """
        return falff(self, low_freq=low_freq, high_freq=high_freq,
                     ratio=ratio, window=window, details=details)

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

    @property
    def plot(self) -> _PlotAccessor:
        """
        Line plot, or the pandas plotting accessor.

        Calling it is the historical baseTs behaviour - an alias for
        :meth:`plot_line`. Attribute access falls through to the pandas
        ``.plot`` accessor, which a plain method alias made unreachable.

        Examples:
            ts.plot()                     # baseTs line plot
            ts.plot(lowess=True, ax=ax)   # plot_line keyword arguments
            ts.plot.bar()                 # pandas PlotAccessor
            ts.plot.hist(bins=30)
        """
        return _PlotAccessor(self)

    
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
                            min_rate: float = 0.0,
                            window: str = None,
                            ax = None,
                            title: str = None,
                            xlabel: str = None,
                            ylabel: str = None, 
                            show: bool = False,
                            scale_power: bool = False,
                            highlight_band: Optional[Tuple[float, float]] = None) -> plt.Axes:
        """
        Plot the power spectrum of the timeseries using enhanced frequency analysis.

        Args:
            max_rate (float, optional): Maximum frequency rate to display. Defaults to np.nan (Nyquist).
            min_rate (float, optional): Minimum frequency rate to display. Defaults to 0.0.
            window (str, optional): Window function to apply ('hann', 'hamming', 'blackman', None).
                                   Defaults to None for no windowing.
            ax (matplotlib.axes.Axes, optional): Matplotlib Axes object to plot on. Defaults to None.
            title (str, optional): Title of the plot. Defaults to None.
            xlabel (str, optional): Label for the x-axis. Defaults to None.
            ylabel (str, optional): Label for the y-axis. Defaults to None.
            show (bool, optional): Whether to display the plot. Defaults to False.
            scale_power (bool, optional): Whether to scale the power spectrum. Defaults to False.
            highlight_band (tuple, optional): (low_freq, high_freq) in Hz to shade on the plot,
                e.g. (0.01, 0.1) to mark the fALFF band. Defaults to None.

        Returns:
            matplotlib.axes.Axes: The Axes object with the plot.

        Raises:
            ValueError: If the sampling rate is unusable (NaN, zero or negative),
                if the data is complex or contains NaN or Inf, if `window`
                names an unknown
                window function, if `min_rate`/`max_rate` is not a real finite
                scalar (`max_rate` also takes NaN, its "use Nyquist" sentinel),
                if [min_rate, max_rate] selects no frequency bins, or if
                `highlight_band` is not a strictly increasing pair of real
                finite frequencies, or if the series is empty (#62; it was a
                `ZeroDivisionError` from inside numpy before). A rejected
                call draws nothing.

            Until issue #34 these were swallowed and drawn as text on the axes,
            so a failing call returned a normal Axes. Gappy data needs an
            `interpolate_gaps()` first - since #36 `filter_outliers` leaves the
            gaps it did not create as NaN, and since #28 the spectral guards
            reject them.

        Examples:
            # Basic power spectrum
            ts.plot_fft_power()
            
            # With Hanning window and frequency range
            ts.plot_fft_power(window='hann', min_rate=0.1, max_rate=50)
            
            # High-quality spectrum with Blackman window
            ts.plot_fft_power(window='blackman', scale_power=True)
            
            # Shade the fALFF band alongside the measurement
            ts.plot_fft_power(max_rate=0.5, highlight_band=(0.01, 0.1))
        """
        # Import plotting here to avoid circular imports
        from .plotting import plot_fft_power
        
        return plot_fft_power(self,
                        max_rate=max_rate,
                        min_rate=min_rate,
                        window=window,
                        ax=ax,
                        title=title,
                        xlabel=xlabel,
                        ylabel=ylabel,  
                        show=show,
                        scale_power=scale_power,
                        highlight_band=highlight_band)
    
    def lag_plot(self, lag: Union[int, float], lag_unit: str = "index", ax: Optional[plt.Axes] = None, show: bool = False) -> plt.Axes:
        """
        Plot a lag plot of the timeseries.
        """
        # Import plotting here to avoid circular imports
        from .plotting import lag_plot  
        return lag_plot(self, lag=lag, lag_unit=lag_unit, ax=ax, show=show)

    def copy(self, deep: bool = True) -> "baseTs":
        """
        Create a copy of the baseTs object.

        Args:
            deep: Whether to make a deep copy (pandas compatibility)

        Returns:
            baseTs: A new instance of baseTs with the same data.
        """
        if deep:
            # Create a new baseTs object to avoid pandas deepcopy recursion.
            # No signal_name kwarg: the loop below copies it with the rest of
            # _metadata. Passing it here as well meant the name went through
            # the constructor's upper-casing and was then overwritten by the
            # copy - so this path preserved case by accident while
            # _create_new_with_data, which had no second assignment, did not
            # (#56).
            new_obj = baseTs(
                data=self.values.copy(),
                times=self.index.values.copy(),
            )
            
            # Deep copy metadata. The allow-list bounds what gets copied:
            # an unguarded deepcopy turns any non-copyable metadata value into
            # a hard error. outlier_filter needs no copy - see
            # _detach_shared_metadata.
            for attr in self._metadata:
                if hasattr(self, attr):
                    # Routed through the shared helper so the positional slots
                    # get copied inside their (value, index) tuple, which a
                    # bare isinstance check on the tuple silently skips.
                    setattr(new_obj, attr,
                            deepcopy_metadata_value(attr, getattr(self, attr)))

            # deepcopy(None) is None, so without this the default copy path
            # was the one derivation that could still hand back a history
            # that is not a list.
            _detach_shared_metadata(new_obj)
            # attrs and flags are not in _metadata, so the loop above cannot
            # carry them however complete it is. pandas calls this method
            # itself - head() is iloc[:n].copy() on pandas 3.0 - so this is
            # not only the user-facing copy path.
            _carry_identity(new_obj, self)
            return new_obj
        else:
            # Shallow copy using pandas Series copy
            copied = super().copy(deep=False)
            # Ensure it's still a baseTs object
            if not isinstance(copied, baseTs):
                copied = baseTs(copied.values, copied.index.values)
                # Copy metadata
                for attr in self._metadata:
                    if hasattr(self, attr):
                        setattr(copied, attr, getattr(self, attr))
                _detach_shared_metadata(copied)
            # No _carry_identity call on this branch, unlike the deep one
            # above. pandas' own copy has already run __finalize__ here, which
            # carries all three fields, and the rebuild it falls back to is
            # unreachable while `_constructor` returns baseTs. Both spellings
            # were tried and neither could be made to fail a test, so neither
            # is shipped: an unpinned line that reads as a safeguard is how a
            # later reader comes to trust something that was never doing
            # anything. The deep branch differs because it constructs its
            # object from bare arrays, where nothing has finalized anything.
            return copied

    def apply_function(self, func, *args, inplace=False, **kwargs) -> "baseTs":
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
        
        # normalise_history, not a truthiness test: `self.history or []`
        # raises on an ndarray ("truth value ... is ambiguous") after the
        # header is already on stdout, and a bare loop over a str prints one
        # line per character. Kept identical to TimeSeriesData.info().
        print("\nHistory:")
        for entry in normalise_history(getattr(self, 'history', None)):
            print(f"  {entry}")
            
    def set_timestamp_offset(self, ts_offset: float):
        """
        Declare the origin the index's seconds are counted from.

        `ts_offset` is the origin in epoch seconds; `datetimes` then reads
        the index as origin + seconds. The index itself does not move. It
        used to: this method both shifted the index by the offset and
        recorded it, which under "seconds since the origin" counted the
        offset twice (#100). A second call replaces the origin.

        Args:
            ts_offset: The origin, in seconds since the Unix epoch
        """
        self.ts_offset = ts_offset
        self._update_history_and_process(
            f"Set timestamp offset to {ts_offset}", "_tso" + str(ts_offset)
        )
        self.has_timestamp_offset = True
        self._origin_index = self.index          # the origin describes this index

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
        Detrend the data by subtracting a robust LOWESS fit.

        The trend is the LOWESS line produced by the outlier filter, so spikes
        do not drag the trend down towards themselves. The result is the
        *original* data minus that trend: outliers are preserved, not
        interpolated away. Pipe through filter_outliers first if you want them
        gone.

        Args:
            frac: LOWESS bandwidth, in (0, 1]. The fraction of points included
                in each local regression window - not the fraction of points
                expected to be outliers.
            inplace: If True, modifies existing object. Otherwise returns new object.

        Returns:
            Detrended baseTs object

        Notes:
            The trend is fitted with the filter's *default* parameters and the
            given frac. Any filter you configured on this object is ignored
            here - and left untouched, rather than being overwritten as it was
            before. `is_outlier_filtered` and `outlier_indices` are likewise
            left alone: detrending is not filtering, and the returned data
            still contains its outliers. Beyond `data` and `lowess_fit`, the
            target gains a `history` entry and a new `last_process`.
        """
        if not 0 < frac <= 1:
            raise ValueError(f"frac must be in (0, 1], got {frac}")

        # Configure a throwaway holder rather than self, so the caller's filter
        # config survives. It is deliberately a minimal two-point series and
        # not self.copy(), which would clone the whole series just to carry a
        # config. Routing through set_outlier_filter keeps the parameter
        # defaults in a single place rather than restating them here.
        scratch = baseTs(np.zeros(2), np.arange(2.0))
        # z_threshold and max_iterations are spelled out because they used to
        # arrive by accident: set_outlier_filter carried real defaults, so
        # naming frac alone also set these two. Now that unnamed parameters are
        # left alone, stating them keeps the trend identical to before.
        scratch.set_outlier_filter(frac=frac, z_threshold=7, max_iterations=10)

        # filter() does not mutate the series it is handed, so self is safe here.
        _, _, lowess_fit = scratch.outlier_filter.filter(self, return_lowess=True)

        detrended = np.asarray(self.data, dtype=float) - lowess_fit

        # Read before the data changes: the positional properties check the
        # live values (#40), and after `target.data = detrended` the source's
        # own record would read None on the inplace path.
        positions = self.outlier_indices

        target = self if inplace else self.copy()
        target.data = detrended
        target.lowess_fit = lowess_fit
        # Re-asserted, not left to propagate. The docstring promises the
        # outlier record survives detrending, and since #40 a slot only
        # survives a change of values if the producer stamps it against the
        # values it leaves behind - which is what assigning through the
        # property does. A copy of the list, so the two objects do not share
        # one record; `None` when the source had none.
        target.outlier_indices = None if positions is None else copy.copy(positions)
        target._update_history_and_process(
            hist_msg=f"Detrended with lowess fit frac={frac}",
            last_process="_lowess_detrend"
        )
        return target
    
    def detrend(self, method: str = 'linear', inplace: bool = False) -> "baseTs":
        """
        Remove trend from the signal using various detrending methods.
        
        Args:
            method: Detrending method ('linear', 'constant')
                - 'linear': Remove linear trend (best fit line)
                - 'constant': Remove mean (demean the signal)
            inplace: If True, modifies existing object. Otherwise returns new object.
        
        Returns:
            baseTs: Detrended baseTs object
            
        Raises:
            ValueError: If method is not supported
        """
        if method not in ['linear', 'constant']:
            raise ValueError(f"Unsupported detrend method: {method}. Use 'linear' or 'constant'")
        
        def detrend_func(data):
            if method == 'linear':
                # Remove linear trend using least squares fit
                x = np.arange(len(data))
                coeffs = np.polyfit(x, data, 1)  # Linear fit (degree 1)
                trend = np.polyval(coeffs, x)
                detrended = data - trend
                return detrended, trend
            elif method == 'constant':
                # Remove mean (constant detrending)
                mean_val = np.mean(data)
                detrended = data - mean_val
                trend = np.full_like(data, mean_val)
                return detrended, trend
        
        def process_result(result):
            detrended_data, trend = result
            if inplace:
                self.data = detrended_data
                self._update_history_and_process(
                    hist_msg=f"Detrended using {method} method",
                    last_process=f"_detrend_{method}"
                )
                return self
            else:
                new_obj = self._create_new_with_data(detrended_data, self.times)
                new_obj._update_history_and_process(
                    hist_msg=f"Detrended using {method} method",
                    last_process=f"_detrend_{method}"
                )
                return new_obj
        
        result = detrend_func(self.data)
        return process_result(result)

    def set_indices_to_nan_and_interpolate(self, 
                                          indices: Union[List[int], np.ndarray], 
                                          interpolation_method: str = 'linear',
                                          order: int = 2,
                                          inplace: bool = False) -> "baseTs":
        """
        Set specific indices to NaN and interpolate the missing values.
        
        Args:
            indices: List or array of indices to set to NaN
            interpolation_method: Method for interpolation ('linear', 'polynomial', 'spline', etc.)
            order: Order for polynomial/spline interpolation (default: 2)
            inplace: If True, modifies existing object. Otherwise returns new object.
            
        Returns:
            baseTs: Object with interpolated values at the specified indices
            
        Examples:
            # Set indices 10, 20, 30 to NaN and interpolate
            ts_interpolated = ts.set_indices_to_nan_and_interpolate([10, 20, 30])
            
            # Use polynomial interpolation with order 3
            ts_interpolated = ts.set_indices_to_nan_and_interpolate([10, 20, 30], 
                                                                   interpolation_method='polynomial', 
                                                                   order=3)
        """
        # Convert indices to numpy array if needed
        if isinstance(indices, list):
            indices = np.array(indices)
        
        # Validate indices
        if not np.issubdtype(indices.dtype, np.integer):
            raise ValueError("Indices must be integers")
        
        if np.any(indices < 0) or np.any(indices >= len(self)):
            raise ValueError("All indices must be within the valid range [0, len(data))")
        
        def process_func(data):
            # Create a copy of the data and ensure it's float dtype for NaN assignment
            new_data = data.astype(float).copy()
            
            # Set specified indices to NaN
            new_data[indices] = np.nan
            
            # Interpolate missing values using pandas
            cleaned_series = pd.Series(new_data, index=self.times)
            interpolated_series = cleaned_series.interpolate(
                method=interpolation_method,
                order=order
            )
            
            # Handle any remaining NaN values with forward/backward fill
            if interpolated_series.isnull().any():
                interpolated_series = interpolated_series.ffill().bfill()
            
            return interpolated_series.values
        
        return self._enhanced_process_with_flags(
            func=process_func,
            hist_msg=f"Set indices {indices.tolist()} to NaN and interpolated using {interpolation_method}",
            last_process=f"_set_nan_interp_{interpolation_method}",
            inplace=inplace,
            # The flag means "at least one value is an interpolated
            # estimate" (#90), so it is set only when an index was given:
            # an empty integer array passes the guards (an empty *list*
            # is refused only because np.array([]) is float64), estimates
            # nothing, and must leave the flag as found (review round 2).
            **({"is_interpolated": True} if len(indices) else {})
        )
