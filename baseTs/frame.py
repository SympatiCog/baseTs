# -*- coding: utf-8 -*-
"""`baseDf` - many time series on one shared index.

Backed by a ``pd.DataFrame`` but deliberately *not* a subclass of one. The
metadata contract is code written here and called where we call it, rather
than an override pandas invokes at moments that have to be discovered; see
the design spec for why that decision was taken.
"""
from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Hashable,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

import numpy as np
import pandas as pd

from .frame_average import averaged_row, common_prefix  # noqa: F401
from .frame_meta import (
    COL_META_FIELDS,
    _IndexMeta,
    default_col_meta_row,
    harvest_col_meta,
    hydrate_column,
    refuse_reserved_columns,
)
from .utils import ValidationError

if TYPE_CHECKING:
    from .core import baseTs


def _is_listlike(key: Any) -> bool:
    """True for a key that selects several columns rather than one."""
    return isinstance(key, (list, tuple, set, pd.Index, np.ndarray, pd.Series))


class baseDf:
    """A set of time series sharing one index.

    Attributes:
        df: The values, as a plain pandas DataFrame.
        col_meta: One row per column: the nine maintained metadata fields plus
            any user attributes supplied at construction.
    """

    def __init__(
        self,
        data: Union[pd.DataFrame, np.ndarray, Dict[Hashable, Any]],
        times: Optional[Sequence[float]] = None,
        freq: float = np.nan,
        ts_offset: float = np.nan,
        col_meta: Optional[pd.DataFrame] = None,
    ) -> None:
        """Build a frame.

        Args:
            data: A DataFrame, a 2-D array, or a mapping of label to column.
            times: The shared index in seconds. Defaults to ``data``'s index
                when it has one, otherwise to sample numbers.
            freq: Declared sampling rate in Hz. Left undeclared by default, in
                which case it is derived from the index.
            ts_offset: Origin the index seconds are counted from, in epoch
                seconds. Supplying one sets ``has_timestamp_offset``.
            col_meta: Per-column user attributes, indexed by column label.

        Raises:
            ValidationError: On duplicate labels, non-numeric columns,
                reserved ``col_meta`` names, or labels not present in the data.
        """
        df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)

        if df.columns.has_duplicates:
            duplicated = sorted({str(c) for c in df.columns[df.columns.duplicated()]})
            raise ValidationError(
                f"baseDf refuses duplicate column labels {duplicated}: a "
                f"col_meta row keyed by a duplicated label cannot say which "
                f"column it describes. Rename them, or select one of each."
            )

        if times is not None:
            index = pd.Index(np.asarray(times, dtype=float))
            if len(index) != len(df):
                raise ValidationError(
                    f"times has {len(index)} entries but the data has "
                    f"{len(df)} rows; they must match. Pass a times array the "
                    f"same length as the data, or omit times to use the "
                    f"DataFrame's own index."
                )
        else:
            index = pd.Index(np.asarray(df.index, dtype=float))

        non_numeric = [c for c in df.columns
                       if not pd.api.types.is_numeric_dtype(df[c])]
        if non_numeric:
            raise ValidationError(
                f"these columns are not numeric and cannot be time series: "
                f"{non_numeric!r}. Drop them, or pass only the value columns."
            )

        self._df: pd.DataFrame = pd.DataFrame(
            {c: np.asarray(df[c], dtype=float) for c in df.columns},
            index=index,
            columns=df.columns,
        )
        self._index_meta = _IndexMeta(
            declared_freq=float(freq),
            ts_offset=(0.0 if np.isnan(ts_offset) else float(ts_offset)),
            has_timestamp_offset=not np.isnan(ts_offset),
            is_uniform_grid=False,
        )
        self._col_meta = self._build_col_meta(col_meta)
        self._check_invariants()

    @classmethod
    def from_df(
        cls,
        df: pd.DataFrame,
        time_col: str = "time",
        value_cols: Optional[Sequence[Hashable]] = None,
        freq: float = np.nan,
        ts_offset: float = np.nan,
        col_meta: Optional[pd.DataFrame] = None,
    ) -> "baseDf":
        """Build a frame from a wide table: one time column, many value columns.

        Args:
            df: The wide table.
            time_col: Column holding the time values, in seconds.
            value_cols: Columns to take. Defaults to every numeric column
                except ``time_col``.
            freq: Declared sampling rate in Hz.
            ts_offset: Origin the index seconds are counted from.
            col_meta: Per-column user attributes.

        Returns:
            baseDf: The frame.

        Raises:
            ValidationError: If ``time_col`` is absent, or a requested value
                column is absent or non-numeric.
        """
        if time_col not in df.columns:
            raise ValidationError(
                f"no time column {time_col!r} in the table. Columns present: "
                f"{list(df.columns)!r}; pass time_col= to name the right one."
            )
        if not pd.api.types.is_numeric_dtype(df[time_col]):
            raise ValidationError(
                f"time column {time_col!r} is not numeric (dtype "
                f"{df[time_col].dtype}), so it cannot become an index of "
                f"seconds. Pass time_col= to name the right column, or "
                f"convert it to seconds first."
            )
        if value_cols is None:
            chosen: list = [c for c in df.columns
                            if c != time_col and pd.api.types.is_numeric_dtype(df[c])]
            refused = [c for c in df.columns
                       if c != time_col and not pd.api.types.is_numeric_dtype(df[c])]
            if refused:
                raise ValidationError(
                    f"these columns are not numeric and cannot be time series: "
                    f"{refused!r}. Pass value_cols= to choose explicitly, or "
                    f"drop them first."
                )
        else:
            chosen = list(value_cols)
            missing = [c for c in chosen if c not in df.columns]
            if missing:
                raise ValidationError(
                    f"no such column(s): {missing!r}. Columns present: "
                    f"{list(df.columns)!r}"
                )
        if not df[time_col].is_monotonic_increasing:
            df = df.sort_values(time_col)
        return cls(
            df[chosen],
            times=np.asarray(df[time_col], dtype=float).tolist(),
            freq=freq,
            ts_offset=ts_offset,
            col_meta=col_meta,
        )

    @classmethod
    def from_series(
        cls,
        series: Sequence[Any],
        labels: Optional[Sequence[Hashable]] = None,
    ) -> "baseDf":
        """Build a frame from existing baseTs objects sharing one index.

        Each series' own metadata becomes its col_meta row, so nothing is lost
        on the way in.

        Args:
            series: The baseTs objects, all on the same index.
            labels: Column labels. Defaults to each series' ``signal_name``,
                falling back to its position.

        Returns:
            baseDf: The frame.

        Raises:
            ValidationError: On an empty list, mismatched indices, or
                conflicting freq/ts_offset declarations.
        """
        items = list(series)
        if not items:
            raise ValidationError(
                "from_series needs at least one baseTs; there is nothing to "
                "put on a shared index."
            )
        first = items[0]
        names = (list(labels) if labels is not None
                 else [(ts.signal_name or f"c{i}") for i, ts in enumerate(items)])
        if len(names) != len(items):
            raise ValidationError(
                f"got {len(names)} label(s) for {len(items)} series; they "
                f"must match one-to-one. Pass exactly one label per series, "
                f"or omit labels= to derive them from each series' "
                f"signal_name."
            )

        index_meta = _IndexMeta.from_series(first)
        for label, ts in zip(names, items):
            if not first.index.equals(ts.index):
                raise ValidationError(
                    f"{label!r} is on a different index from {names[0]!r}; "
                    f"baseDf needs one shared index. Use baseTs.align_with() "
                    f"to put them on a common index first."
                )
            other = _IndexMeta.from_series(ts)
            if other.ts_offset != index_meta.ts_offset:
                raise ValidationError(
                    f"{label!r} declares ts_offset={other.ts_offset!r} but "
                    f"{names[0]!r} declares {index_meta.ts_offset!r}; one "
                    f"frame has one origin. Reconcile the two series' "
                    f"ts_offset before combining them, or drop it from "
                    f"whichever one set it in error."
                )
            same_freq = (
                (np.isnan(other.declared_freq) and np.isnan(index_meta.declared_freq))
                or other.declared_freq == index_meta.declared_freq
            )
            if not same_freq:
                raise ValidationError(
                    f"{label!r} declares freq={other.declared_freq!r} but "
                    f"{names[0]!r} declares {index_meta.declared_freq!r}; one "
                    f"frame has one sampling rate. Pass the same freq to "
                    f"both series' constructors, or leave it undeclared on "
                    f"whichever one shouldn't set it."
                )

        values = pd.DataFrame(
            {label: np.asarray(ts.data, dtype=float)
             for label, ts in zip(names, items)},
            index=pd.Index(np.asarray(first.index, dtype=float)),
            columns=list(names),
        )
        rows = {label: harvest_col_meta(ts) for label, ts in zip(names, items)}
        # dtype=object, matching _build_col_meta: several fields are
        # non-scalar, and letting pandas infer a narrow dtype for a column
        # that happens to be uniform (e.g. every is_filtered starts False)
        # would silently promote a Python bool to numpy.bool_, breaking
        # identity/equality checks callers make against it.
        table = pd.DataFrame.from_dict(rows, orient="index", dtype=object)
        table = table.reindex(list(names))[list(COL_META_FIELDS)]

        frame = object.__new__(cls)
        frame._df = values
        frame._col_meta = table
        frame._index_meta = index_meta
        frame._check_invariants()
        return frame

    def _build_col_meta(self, user: Optional[pd.DataFrame]) -> pd.DataFrame:
        """Compose the maintained fields with any user attributes."""
        refuse_reserved_columns(user)
        rows = {label: default_col_meta_row(label) for label in self._df.columns}
        # dtype=object throughout: several fields (history, outlier_indices,
        # lowess_fit, outlier_filter) are non-scalar, and letting pandas infer
        # a narrow dtype for a column that happens to be uniform (e.g. every
        # is_filtered starts False) would silently promote a Python bool to
        # numpy.bool_, breaking identity checks callers make against it.
        table = pd.DataFrame.from_dict(rows, orient="index", dtype=object)
        table = table.reindex(self._df.columns)[list(COL_META_FIELDS)]
        if user is not None:
            if user.index.has_duplicates:
                duplicated = sorted({str(i) for i in
                                     user.index[user.index.duplicated()]})
                raise ValidationError(
                    f"col_meta has duplicate row label(s) {duplicated}: a "
                    f"column can only have one row of metadata. De-duplicate "
                    f"the col_meta index before passing it."
                )
            unknown = [i for i in user.index if i not in set(self._df.columns)]
            if unknown:
                raise ValidationError(
                    f"col_meta describes column(s) not in the data: "
                    f"{unknown!r}. Columns present: {list(self._df.columns)!r}"
                )
            for column in user.columns:
                table[column] = user[column].reindex(self._df.columns)
        return table

    def _check_invariants(self) -> None:
        """Refuse any state in which a col_meta row could not name its column.

        Raises:
            ValidationError: On duplicate labels, misaligned rows, or a
                col_meta missing one of the maintained fields.
        """
        columns = self._df.columns
        if columns.has_duplicates:
            duplicated = sorted({str(c) for c in columns[columns.duplicated()]})
            raise ValidationError(
                f"baseDf refuses duplicate column labels {duplicated}: a "
                f"col_meta row keyed by a duplicated label cannot say which "
                f"column it describes. Rename them, or select one of each."
            )
        if list(self._col_meta.index) != list(columns):
            raise ValidationError(
                f"col_meta rows are out of step with the columns: "
                f"col_meta.index={list(self._col_meta.index)!r} vs "
                f"columns={list(columns)!r}. Pass col_meta indexed by exactly "
                f"the data's columns, in the same order, or omit it and let "
                f"baseDf build the default rows."
            )
        missing = [f for f in COL_META_FIELDS if f not in self._col_meta.columns]
        if missing:
            raise ValidationError(f"col_meta is missing maintained field(s): {missing!r}")

    def _with(
        self,
        df: pd.DataFrame,
        col_meta: pd.DataFrame,
        index_meta: Optional[_IndexMeta] = None,
    ) -> "baseDf":
        """Build a sibling frame directly, bypassing construction validation."""
        new = object.__new__(baseDf)
        new._df = df
        new._col_meta = col_meta
        new._index_meta = self._index_meta if index_meta is None else index_meta
        new._check_invariants()
        return new

    def _resolve_labels(
        self,
        select: Any = None,
        where: Optional[str] = None,
    ) -> List[Hashable]:
        """Turn a selection into an ordered list of existing column labels.

        Args:
            select: Labels, or a boolean mask the length of ``columns``.
            where: A pandas query string evaluated against ``col_meta``.

        Returns:
            list: The chosen labels, in frame order for a query and in the
                caller's order for an explicit list.

        Raises:
            ValidationError: On unknown labels, a mask of the wrong length,
                a repeated label, an invalid ``where`` query, a ``select``
                that isn't list-like, or a selection matching nothing.
        """
        labels: List[Hashable] = list(self._df.columns)
        if where is not None:
            try:
                labels = list(self._col_meta.query(where).index)
            except ValidationError:
                raise
            except Exception as exc:
                # col_meta.query() runs pandas' own expression engine, which
                # raises its own SyntaxError/UndefinedVariableError/etc. for a
                # typo or an unknown column - a routine mistake on a
                # documented, first-class parameter, not an edge case. Found
                # in post-implementation review: both leaked uncaught.
                raise ValidationError(
                    f"where={where!r} is not a valid query against col_meta: "
                    f"{exc}. col_meta's columns are "
                    f"{list(self._col_meta.columns)!r} - check the column "
                    f"name and the query syntax."
                ) from exc
        if select is not None:
            if not _is_listlike(select):
                raise ValidationError(
                    f"select must be a list of labels or a boolean mask, not "
                    f"a bare {type(select).__name__} ({select!r}). Wrap a "
                    f"single label in a list: select=[{select!r}]."
                )
            values = list(select)
            if values and all(isinstance(v, (bool, np.bool_)) for v in values):
                if len(values) != len(self._df.columns):
                    raise ValidationError(
                        f"a boolean column mask must have one entry per column: "
                        f"got {len(values)} for {len(self._df.columns)} "
                        f"columns. Pass exactly one True/False per column, "
                        f"or a list of labels instead."
                    )
                chosen = [c for c, keep in zip(self._df.columns, values) if keep]
            else:
                chosen = values
                unknown = [c for c in chosen if c not in set(self._df.columns)]
                if unknown:
                    raise ValidationError(
                        f"no such column(s): {unknown!r}. Columns present: "
                        f"{list(self._df.columns)!r}"
                    )
                duplicated = sorted({c for c in chosen if chosen.count(c) > 1})
                if duplicated:
                    raise ValidationError(
                        f"select repeats column(s) {duplicated!r}. A "
                        f"repeated label would be counted twice in an "
                        f"average, or produce a frame with a duplicate "
                        f"column - list each label once."
                    )
            allowed = set(labels)
            labels = [c for c in chosen if c in allowed]
        if not labels:
            raise ValidationError(
                "the selection matched no columns. An average or a slice over "
                "nothing is never what was meant: check the labels, or inspect "
                "col_meta for the attribute the query named."
            )
        return labels

    def select(self, where: Optional[str] = None, select: Any = None) -> "baseDf":
        """Take a subset of the columns, keeping their metadata.

        Args:
            where: A query string against ``col_meta``, e.g.
                ``"network == 'DMN' and not bad"``.
            select: Labels, or a boolean mask the length of ``columns``.

        Returns:
            baseDf: A frame holding the chosen columns.
        """
        labels = self._resolve_labels(select=select, where=where)
        return self._with(self._df[labels], self._col_meta.loc[labels])

    def __getitem__(self, key: Any) -> Union["baseDf", Any]:
        """One column as a baseTs, several as a baseDf.

        This mirrors pandas' own ``__getitem__`` contract deliberately, which
        is the one place this class returns two different types from one call.
        """
        if _is_listlike(key):
            return self.select(select=list(key))
        if key not in self._df.columns:
            raise ValidationError(
                f"no such column: {key!r}. Columns present: "
                f"{list(self._df.columns)!r}"
            )
        return hydrate_column(
            np.asarray(self._df[key], dtype=float),
            [float(v) for v in self._df.index],
            self._index_meta,
            self._col_meta.loc[key],
            key,
        )

    @property
    def df(self) -> pd.DataFrame:
        """The values as a plain DataFrame - the escape hatch to pandas."""
        return self._df

    @property
    def col_meta(self) -> pd.DataFrame:
        """One row of metadata per column."""
        return self._col_meta

    @property
    def columns(self) -> pd.Index:
        """The column labels."""
        return self._df.columns

    @property
    def index(self) -> pd.Index:
        """The shared index, in seconds."""
        return self._df.index

    @property
    def shape(self) -> Tuple[int, int]:
        """(samples, columns)."""
        return self._df.shape

    @property
    def ts_offset(self) -> float:
        """Origin the index seconds are counted from, in epoch seconds."""
        return self._index_meta.ts_offset

    @property
    def freq(self) -> float:
        """Sampling rate in Hz: the declaration if one was made, else derived.

        Derived by asking a probe column, so the answer is whatever baseTs
        would say about this index rather than a second implementation of the
        same rule. One construction per access, which is negligible at the
        sizes this container targets.
        """
        probe = hydrate_column(
            np.zeros(len(self._df.index)),
            [float(v) for v in self._df.index],
            self._index_meta,
            default_col_meta_row("_probe"), "_probe",
        )
        return probe.freq

    def __len__(self) -> int:
        """Number of samples."""
        return len(self._df.index)

    def __repr__(self) -> str:
        rate = self.freq
        rate_text = "undeclared" if np.isnan(rate) else f"{rate:g} Hz"
        return (f"baseDf({self.shape[1]} columns x {self.shape[0]} samples, "
                f"{rate_text})")

    def copy(self, deep: bool = True) -> "baseDf":
        """Create an independent copy of this frame.

        Args:
            deep: If True (the default), the values and column metadata are
                copied too, so mutating the result cannot affect this frame
                or vice versa. If False, both share the same underlying
                DataFrames - mirrors ``pd.DataFrame.copy``'s own contract.

        Returns:
            baseDf: The copy.
        """
        return self._with(self._df.copy(deep=deep), self._col_meta.copy(deep=deep))

    #: Every baseTs method annotated as returning a baseTs that is *not*
    #: broadcast. `copy` is excluded because the frame has its own.
    #: `remove_outliers` is excluded because it fails the load-bearing invariant
    #: (the spec's "no transform's output index depends on its data values"):
    #: measured live, two series sharing an index but differing only in *where*
    #: their outlier sits come back with genuinely different indices (one drops
    #: the sample at 2.5s, the other at 12.5s). Broadcasting it would raise
    #: _broadcast's index-mismatch refusal on essentially any real multichannel
    #: dataset, since channels rarely spike at the same sample. Use
    #: filter_outliers or set_outlier_filter instead - both are LOWESS-based and
    #: interpolate rather than drop, so they keep every column on the shared
    #: index (see the spec's "filter_outliers is frame-safe" measurement).
    NOT_BROADCAST = frozenset({"copy", "remove_outliers"})

    #: The methods generated onto this class at import time, one per baseTs
    #: transform. Kept explicit so a reader can see the surface; a test
    #: asserts it equals introspection-minus-NOT_BROADCAST, so it cannot
    #: silently drift.
    TRANSFORMS = (
        "abs", "apply_function", "bandpass_at", "bandpass_filter",
        "butterpass_at", "center", "dediff_ts", "detrend", "diff_ts",
        "filter_outliers", "gauss_filter", "highpass_at", "highpass_filter",
        "interp_to_uniform_grid", "interpolate_gaps", "interpolate_missing",
        "interpto_hz", "interpto_samples", "lowess_detrend", "lowpass_at",
        "lowpass_filter", "normalize_range", "notch_at", "notch_filter",
        "resample", "rolling_max", "rolling_mean",
        "rolling_median", "rolling_min", "rolling_std", "scale",
        "set_indices_to_nan_and_interpolate", "set_outlier_filter",
        "sg_filter", "shift_time", "time_slice", "trimto_timepoints",
        "zscale",
    )

    def _broadcast(self, name: str, args: tuple, kwargs: dict) -> "baseDf":
        """Run one baseTs method on every column and reassemble the frame.

        Args:
            name: The baseTs method to call.
            args: Positional arguments for it.
            kwargs: Keyword arguments. ``inplace`` is handled here, at the
                frame level, and is never forwarded to the column call.

        Returns:
            baseDf: A new frame, or ``self`` when ``inplace=True``.

        Raises:
            ValidationError: If the method returns a different index for
                different columns, which a shared-index frame cannot hold.
        """
        inplace = bool(kwargs.pop("inplace", False))
        index: Optional[pd.Index] = None
        first_out: Optional["baseTs"] = None
        values: Dict[Hashable, np.ndarray] = {}
        rows: Dict[Hashable, Dict[str, Any]] = {}

        for label in self._df.columns:
            out = getattr(self[label], name)(*args, **kwargs)
            if index is None:
                index, first_out = out.index, out
            elif not index.equals(out.index):
                first_label = list(self._df.columns)[0]
                if len(out.index) != len(index):
                    # Different sample counts: that alone is the whole story.
                    divergence = (f"{len(out.index)} samples vs "
                                  f"{len(index)} samples")
                else:
                    # Same count, different values - reporting "N samples"
                    # for both sides would say nothing, so name where and by
                    # how much they actually diverge. Found in
                    # post-implementation review: the length-only message
                    # gave identical numbers for both columns here.
                    mismatched = np.asarray(index, dtype=float) != np.asarray(
                        out.index, dtype=float)
                    first_bad = int(np.argmax(mismatched))
                    divergence = (
                        f"same length ({len(index)} samples) but "
                        f"{int(mismatched.sum())} differing value(s), first "
                        f"at position {first_bad} ({out.index[first_bad]!r} "
                        f"vs {index[first_bad]!r})"
                    )
                raise ValidationError(
                    f"{name}() returned a different index for column {label!r} "
                    f"than for {first_label!r}: {divergence}. baseDf requires "
                    f"every column to share one index, so a transform whose "
                    f"output index depends on its data values cannot be "
                    f"broadcast. Pull the columns out with frame[label] and "
                    f"handle them individually."
                )
            values[label] = np.asarray(out.data, dtype=float)
            rows[label] = harvest_col_meta(out)

        # self._df.columns is never empty (baseDf refuses an empty frame at
        # construction), so the loop above ran at least once and both are set.
        assert index is not None and first_out is not None
        new_df = pd.DataFrame(values, index=index, columns=self._df.columns)
        # dtype=object, matching _build_col_meta/from_series: without it, a
        # column that happens to be uniform (e.g. every is_filtered now False)
        # gets narrowed to numpy.bool_/native str on assignment below, silently
        # breaking the `is True`/`is False` identity checks baseTs and this
        # test suite make against it. Found in post-implementation review -
        # confirmed live that a broadcast column's is_filtered came back
        # numpy.bool_ rather than the Python bool it started as.
        harvested = pd.DataFrame.from_dict(
            rows, orient="index", dtype=object).reindex(self._df.columns)
        # Copy rather than rebuild, so user attributes ride along untouched.
        new_col_meta = self._col_meta.copy()
        for field in COL_META_FIELDS:
            new_col_meta[field] = harvested[field]
        new_index_meta = _IndexMeta.from_series(first_out)

        if inplace:
            self._df = new_df
            self._col_meta = new_col_meta
            self._index_meta = new_index_meta
            self._check_invariants()
            return self
        return self._with(new_df, new_col_meta, new_index_meta)

    #: How each measurement's per-column result is collapsed into one object.
    #: "scalar"     -> pd.Series indexed by column
    #: "mapping"    -> pd.DataFrame, columns as rows and dict keys as columns
    #: "per_sample" -> pd.DataFrame, frame index x columns
    #: "object"     -> pd.Series of objects, for results that are lists
    #: "shared_axis"-> (axis, pd.DataFrame) for 2-tuples whose first element
    #:                 is an axis every column must agree on
    MEASURE_KINDS = {
        "falff": "scalar",
        "relative_band_power": "scalar",
        "get_statistics": "mapping",
        "detect_outliers": "per_sample",
        "get_peaks": "object",
        "get_peak_freq": "object",
        "compute_fft_power": "shared_axis",
        "get_frequency_content": "shared_axis",
    }

    def measure(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Run one baseTs measurement on every column and collect the results.

        Args:
            name: The baseTs method to call. Must be in MEASURE_KINDS.
            *args: Positional arguments for it.
            **kwargs: Keyword arguments for it.

        Returns:
            A pandas Series or DataFrame keyed by column label, or, for a
            shared-axis measurement, a ``(axis, DataFrame)`` pair.

        Raises:
            ValidationError: If ``name`` is not a known measurement, or a
                shared-axis measurement disagrees between columns.
        """
        if name not in self.MEASURE_KINDS:
            raise ValidationError(
                f"{name!r} is not a known baseDf measurement. Known: "
                f"{sorted(self.MEASURE_KINDS)!r}. For anything else, pull the "
                f"column out with frame[label] and call it there."
            )
        if name in ("falff", "relative_band_power") and kwargs.get("details"):
            raise ValidationError(
                f"{name}(details=True) returns a BandPowerResult, not a "
                f"number, so it cannot fill a numeric pd.Series across "
                f"columns. Call frame[label].{name}(details=True) on one "
                f"column at a time instead."
            )
        kind = self.MEASURE_KINDS[name]
        results = {label: getattr(self[label], name)(*args, **kwargs)
                   for label in self._df.columns}

        if kind == "scalar":
            return pd.Series(results, index=self._df.columns, dtype=float)
        if kind == "object":
            return pd.Series(results, index=self._df.columns, dtype=object)
        if kind == "mapping":
            return pd.DataFrame.from_dict(results, orient="index").reindex(
                self._df.columns)
        if kind == "per_sample":
            return pd.DataFrame(
                {label: np.asarray(value) for label, value in results.items()},
                index=self._df.index, columns=self._df.columns,
            )
        # shared_axis
        axis: Optional[np.ndarray] = None
        payload: Dict[Hashable, np.ndarray] = {}
        for label in self._df.columns:
            first, second = results[label]
            first = np.asarray(first)
            if axis is None:
                axis = first
            elif not np.array_equal(axis, first):
                raise ValidationError(
                    f"{name}() produced a different axis for column {label!r} "
                    f"than for {list(self._df.columns)[0]!r}; the columns "
                    f"share an index, so they must share this axis too."
                )
            payload[label] = np.asarray(second)
        # self._df.columns is never empty (baseDf refuses an empty frame at
        # construction), so the loop above ran at least once and axis is set.
        assert axis is not None
        return axis, pd.DataFrame(payload, index=pd.Index(axis),
                                  columns=self._df.columns)

    def falff(self, *args: Any, **kwargs: Any) -> pd.Series:
        """fALFF per column. See ``baseTs.falff``.

        Returns:
            pd.Series: One value per column.
        """
        return cast(pd.Series, self.measure("falff", *args, **kwargs))

    def relative_band_power(self, *args: Any, **kwargs: Any) -> pd.Series:
        """Relative band power per column. See ``baseTs.relative_band_power``.

        Returns:
            pd.Series: One value per column.
        """
        return cast(pd.Series, self.measure("relative_band_power", *args, **kwargs))

    def get_statistics(self, *args: Any, **kwargs: Any) -> pd.DataFrame:
        """Summary statistics per column. See ``baseTs.get_statistics``.

        Returns:
            pd.DataFrame: Columns as rows, statistic names as columns.
        """
        return cast(pd.DataFrame, self.measure("get_statistics", *args, **kwargs))

    def detect_outliers(self, *args: Any, **kwargs: Any) -> pd.DataFrame:
        """Outlier mask per column. See ``baseTs.detect_outliers``.

        Returns:
            pd.DataFrame: Frame index by column.
        """
        return cast(pd.DataFrame, self.measure("detect_outliers", *args, **kwargs))

    def get_peaks(self, *args: Any, **kwargs: Any) -> pd.Series:
        """Peaks per column. See ``baseTs.get_peaks``.

        Returns:
            pd.Series: One list per column.
        """
        return cast(pd.Series, self.measure("get_peaks", *args, **kwargs))

    def get_peak_freq(self, *args: Any, **kwargs: Any) -> pd.Series:
        """Peak frequency per column. See ``baseTs.get_peak_freq``.

        Returns:
            pd.Series: One value per column - a float if ``num_pks=1`` (the
                default), a list if not.
        """
        return cast(pd.Series, self.measure("get_peak_freq", *args, **kwargs))

    def compute_fft_power(self, *args: Any,
                          **kwargs: Any) -> Tuple[np.ndarray, pd.DataFrame]:
        """FFT power per column over one shared frequency axis.

        Returns:
            tuple: ``(freqs, power)`` where ``power`` is indexed by ``freqs``.
        """
        return cast(Tuple[np.ndarray, pd.DataFrame],
                    self.measure("compute_fft_power", *args, **kwargs))

    def get_frequency_content(self, *args: Any,
                              **kwargs: Any) -> Tuple[np.ndarray, pd.DataFrame]:
        """Frequency content per column over one shared axis.

        Returns:
            tuple: ``(freqs, content)``.
        """
        return cast(Tuple[np.ndarray, pd.DataFrame],
                    self.measure("get_frequency_content", *args, **kwargs))

    def correlation_with(self, other: Any, method: str = "pearson") -> pd.Series:
        """Correlate one series against every column.

        The seed case: a behavioural regressor against a per-electrode measure,
        or a seed timeseries against each ROI. Delegates to
        ``baseTs.correlation_with`` per column, so the answer is identical to
        pulling each column out and calling it there - including that method's
        inner-join alignment, which is harmless here because the results are
        scalars and every column aligns the same way against the same series.

        Args:
            other: A baseTs to correlate every column against.
            method: 'pearson', 'kendall' or 'spearman'.

        Returns:
            pd.Series: One coefficient per column, keyed by column label.

        Raises:
            ValidationError: If ``other`` is a baseDf.
        """
        if isinstance(other, baseDf):
            raise ValidationError(
                "correlation_with takes one series to correlate every column "
                "against. For a frame-against-frame matrix, use "
                "correlation_matrix()."
            )
        return pd.Series(
            {label: self[label].correlation_with(other, method=method)
             for label in self._df.columns},
            index=self._df.columns,
            dtype=float,
        )

    def correlation_matrix(
        self,
        other: Optional["baseDf"] = None,
        method: str = "pearson",
    ) -> pd.DataFrame:
        """Correlate every column against every column of another frame.

        Never implicit: an all-pairs matrix costs O(k*m) and answers a
        different question from the seed case, so it has its own name.

        Intersects the two indices once rather than aligning per pair, which
        400 x 400 columns would make 160,000 aligned calls. Measured identical
        to the per-pair path for pearson, spearman and kendall.

        Args:
            other: The right-hand frame. None means this frame against itself,
                which is the within-frame connectivity matrix.
            method: 'pearson', 'kendall' or 'spearman'.

        Returns:
            pd.DataFrame: This frame's columns as rows, ``other``'s as columns.

        Raises:
            ValidationError: If ``other`` is not a baseDf, or the two frames
                share no timepoints.
        """
        if other is None:
            other = self
        if not isinstance(other, baseDf):
            raise ValidationError(
                "correlation_matrix takes another baseDf, or None for this "
                "frame against itself. To correlate a single series against "
                "every column, use correlation_with()."
            )
        common = self._df.index.intersection(other._df.index)
        if len(common) == 0:
            raise ValidationError(
                "the two frames share no timepoints, so there is nothing to "
                "correlate. Put them on a common index first - baseTs."
                "align_with() or interpto_hz() will do it."
            )
        left, right = self._df.loc[common], other._df.loc[common]
        corr_method = cast(Literal["pearson", "kendall", "spearman"], method)
        return pd.DataFrame(
            {rc: left.corrwith(right[rc], method=corr_method) for rc in right.columns},
            index=left.columns,
            columns=right.columns,
        )

    def duration(self) -> float:
        """Span of the shared index in seconds.

        Returns:
            float: The duration, which is a property of the index and so is
                the same for every column.
        """
        index = np.asarray(self._df.index, dtype=float)
        return float(index[-1] - index[0]) if len(index) else 0.0

    def _average_values(
        self,
        labels: Sequence[Hashable],
        skipna: bool,
        min_count: Optional[int],
    ) -> Tuple[np.ndarray, int]:
        """Mean across the chosen columns, and how many timepoints lost contributors."""
        block = self._df[list(labels)]
        if not skipna:
            if min_count is not None:
                raise ValidationError(
                    "min_count is meaningful only with skipna=True: with the "
                    "default skipna=False a single NaN already propagates, so "
                    "a floor on the contributor count has nothing to act on. "
                    "Pass skipna=True, or drop min_count."
                )
            return np.asarray(block.mean(axis=1, skipna=False), dtype=float), 0
        counts = np.asarray(block.notna().sum(axis=1), dtype=int)
        if min_count is not None and int(min_count) < 1:
            raise ValidationError(
                f"min_count must be at least 1 contributor, got {min_count!r}. "
                f"A floor below 1 would keep timepoints with zero "
                f"contributors, which have nothing to average - drop "
                f"min_count to use the default floor of 1, or pass 1 or more."
            )
        floor = 1 if min_count is None else int(min_count)
        values = np.asarray(block.mean(axis=1, skipna=True), dtype=float)
        values = np.where(counts >= floor, values, np.nan)
        return values, int((counts < len(labels)).sum())

    def average(
        self,
        select: Any = None,
        where: Optional[str] = None,
        skipna: bool = False,
        min_count: Optional[int] = None,
        name: Optional[str] = None,
    ) -> "baseTs":
        """Average a selection of columns into one series.

        Args:
            select: Labels, or a boolean mask the length of ``columns``.
            where: A query against ``col_meta``, e.g. ``"network == 'DMN'"``.
            skipna: If True, average over whatever columns are present at each
                timepoint. Off by default: skipping means a different set of
                columns contributes at different timepoints, which silently
                changes the estimator mid-series.
            min_count: Minimum contributors for a timepoint to be kept.
                Only meaningful with ``skipna=True``.
            name: Signal name for the result.

        Returns:
            baseTs: The averaged series, on the frame's index.

        Raises:
            ValidationError: If the selection matches nothing, or ``min_count``
                is given with ``skipna=False``.
        """
        labels = self._resolve_labels(select=select, where=where)
        description = where if where is not None else ", ".join(str(x) for x in labels)
        values, reduced = self._average_values(labels, skipna, min_count)
        row = averaged_row(self._col_meta, labels, skipna, reduced, description, name)
        return hydrate_column(
            values,
            [float(v) for v in self._df.index],
            self._index_meta,
            row,
            row["signal_name"],
        )

    def average_by(
        self,
        by: Union[str, Sequence[str]],
        select: Any = None,
        where: Optional[str] = None,
        skipna: bool = False,
        min_count: Optional[int] = None,
    ) -> "baseDf":
        """Average columns within each group, giving one column per group.

        Args:
            by: Column name(s) in ``col_meta`` to group on.
            select: Labels, or a boolean mask, to restrict the input columns.
            where: A query against ``col_meta`` to restrict the input columns.
            skipna: As for ``average``.
            min_count: As for ``average``.

        Returns:
            baseDf: One column per group, on the frame's index. A group of one
                column is legal, and its history says so.

        Raises:
            ValidationError: If a grouping column is absent from ``col_meta``,
                the selection matches nothing, or a selected column has no
                value for the grouping key(s).
        """
        # Not scalar (a list, an array-or-None, or a per-column filter
        # instance), so pandas' groupby cannot hash them as a key - it fails
        # with a bare TypeError deep inside groupby, naming neither the
        # field nor a remedy. Refuse explicitly instead. Found in
        # post-implementation review: `average_by(by="history")` crashed
        # with `TypeError: unhashable type: 'list'`.
        _UNGROUPABLE_FIELDS = ("history", "outlier_indices", "lowess_fit",
                               "outlier_filter")
        keys = [by] if isinstance(by, str) else list(by)
        missing = [k for k in keys if k not in self._col_meta.columns]
        if missing:
            raise ValidationError(
                f"no such col_meta column(s) to group by: {missing!r}. "
                f"Available: {[c for c in self._col_meta.columns]!r}"
            )
        ungroupable = [k for k in keys if k in _UNGROUPABLE_FIELDS]
        if ungroupable:
            raise ValidationError(
                f"col_meta field(s) {ungroupable!r} cannot be grouped by: "
                f"each holds a non-scalar or per-column object, not a "
                f"comparable value. Group by a scalar field instead, such as "
                f"a user attribute like 'network', or 'signal_name'."
            )
        labels = self._resolve_labels(select=select, where=where)
        subset = self._col_meta.loc[labels]

        # pandas' groupby drops a NaN key by default, which would silently
        # drop the column from the result with no error, warning, or history
        # entry - and if EVERY selected column's key were NaN, the loop below
        # would run zero times and the reindex after it would raise a raw
        # pandas KeyError instead of the ValidationError every other empty
        # outcome in this module gets. Refuse explicitly instead: a group a
        # column cannot be assigned to is a decision for the caller, not a
        # column to make disappear. Found in post-implementation review.
        no_key = subset[keys].isna().any(axis=1)
        if no_key.any():
            bad = [label for label, missing_key in zip(labels, no_key) if missing_key]
            raise ValidationError(
                f"column(s) {bad!r} have no value for grouping key(s) "
                f"{keys!r}, so they cannot be assigned to a group. Give them "
                f"a value in col_meta, or exclude them first with select= or "
                f"where=."
            )

        values: Dict[Hashable, np.ndarray] = {}
        rows: Dict[Hashable, Dict[str, Any]] = {}
        # dropna=False is now documentation, not a behavior change: the
        # refusal above already ruled out every NaN key among these labels.
        for group, members in subset.groupby(
                keys[0] if len(keys) == 1 else keys, sort=True, dropna=False):
            group_labels = list(members.index)
            column, reduced = self._average_values(group_labels, skipna, min_count)
            values[group] = column
            rows[group] = averaged_row(self._col_meta, group_labels, skipna,
                                       reduced, f"{keys[0]} == {group!r}",
                                       name=str(group))

        order = list(values.keys())
        new_df = pd.DataFrame(values, index=self._df.index, columns=order)
        # dtype=object, matching _build_col_meta/from_series/_broadcast: see
        # those comments - the same numpy.bool_ narrowing was confirmed live
        # on this path too during post-implementation review.
        new_col_meta = pd.DataFrame.from_dict(rows, orient="index", dtype=object)
        new_col_meta = new_col_meta.reindex(order)[list(COL_META_FIELDS)]
        return self._with(new_df, new_col_meta)


def _make_broadcast_method(name: str):
    """Build the frame-level method that broadcasts one baseTs transform."""
    def method(self: baseDf, *args: Any, **kwargs: Any) -> baseDf:
        return self._broadcast(name, args, kwargs)

    from .core import baseTs as _baseTs
    source_doc = (getattr(_baseTs, name).__doc__ or "").strip()
    method.__name__ = name
    method.__qualname__ = f"baseDf.{name}"
    method.__doc__ = (
        f"Broadcast ``baseTs.{name}`` over every column.\n\n"
        f"Each column's history records the operation. ``inplace=True``\n"
        f"replaces this frame's contents instead of returning a new frame.\n\n"
        f"Returns:\n    baseDf: The transformed frame.\n\n"
        f"--- baseTs.{name} ---\n{source_doc}\n"
    )
    return method


for _transform_name in baseDf.TRANSFORMS:
    setattr(baseDf, _transform_name, _make_broadcast_method(_transform_name))
del _transform_name
