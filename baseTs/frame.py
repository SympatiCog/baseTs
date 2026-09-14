# -*- coding: utf-8 -*-
"""`baseDf` - many time series on one shared index.

Backed by a ``pd.DataFrame`` but deliberately *not* a subclass of one. The
metadata contract is code written here and called where we call it, rather
than an override pandas invokes at moments that have to be discovered; see
the design spec for why that decision was taken.
"""
from __future__ import annotations

from typing import Any, Dict, Hashable, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

from .frame_meta import (
    COL_META_FIELDS,
    _IndexMeta,
    default_col_meta_row,
    hydrate_column,
    refuse_reserved_columns,
)
from .utils import ValidationError


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
