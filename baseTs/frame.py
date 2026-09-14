# -*- coding: utf-8 -*-
"""`baseDf` - many time series on one shared index.

Backed by a ``pd.DataFrame`` but deliberately *not* a subclass of one. The
metadata contract is code written here and called where we call it, rather
than an override pandas invokes at moments that have to be discovered; see
the design spec for why that decision was taken.
"""
from __future__ import annotations

from typing import Any, Dict, Hashable, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

from .frame_meta import (
    COL_META_FIELDS,
    _IndexMeta,
    default_col_meta_row,
    harvest_col_meta,
    hydrate_column,
    refuse_reserved_columns,
)
from .utils import ValidationError


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
                f"got {len(names)} label(s) for {len(items)} series."
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
                    f"frame has one origin."
                )
            same_freq = (
                (np.isnan(other.declared_freq) and np.isnan(index_meta.declared_freq))
                or other.declared_freq == index_meta.declared_freq
            )
            if not same_freq:
                raise ValidationError(
                    f"{label!r} declares freq={other.declared_freq!r} but "
                    f"{names[0]!r} declares {index_meta.declared_freq!r}; one "
                    f"frame has one sampling rate."
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
            ValidationError: On unknown labels, a mask of the wrong length, or
                a selection matching nothing.
        """
        labels: List[Hashable] = list(self._df.columns)
        if where is not None:
            labels = list(self._col_meta.query(where).index)
        if select is not None:
            values = list(select)
            if values and all(isinstance(v, (bool, np.bool_)) for v in values):
                if len(values) != len(self._df.columns):
                    raise ValidationError(
                        f"a boolean column mask must have one entry per column: "
                        f"got {len(values)} for {len(self._df.columns)} columns."
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
