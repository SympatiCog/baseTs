"""Splits TimeSeriesData's metadata into what belongs to a shared index and
what belongs to one column.

Nothing here knows what a frame is - these are free functions and one small
dataclass, testable without baseDf existing at all.
"""
from dataclasses import dataclass
from typing import Any, Dict, Hashable, Optional, Sequence

import numpy as np
import pandas as pd

from .core import baseTs
from .LowessOutlierFilter import LowessOutlierFilter
from .utils import ValidationError

#: The nine per-column metadata fields: everything in TimeSeriesData._metadata
#: except the five that describe the shared index (freq declaration, ts_offset,
#: origin, has_timestamp_offset, is_uniform_grid - _IndexMeta owns those).
COL_META_FIELDS = (
    "signal_name", "history", "is_filtered", "is_interpolated",
    "is_outlier_filtered", "last_process", "outlier_indices",
    "lowess_fit", "outlier_filter",
)

# Constructor keyword names for the per-column fields that pass straight
# through to baseTs.__init__ unchanged. signal_name is handled separately
# (see hydrate_column) because the constructor upper-cases it as a keyword
# and a column's exact-case label must survive a round trip.
_CONSTRUCTOR_FIELDS = (
    "is_filtered", "is_interpolated", "is_outlier_filtered", "last_process",
    "outlier_indices", "lowess_fit",
)


@dataclass(frozen=True)
class _IndexMeta:
    """The four index-derived metadata values a frame's shared index carries.

    (Origin is not a fifth field here: it is derived from ts_offset and
    has_timestamp_offset rather than stored, matching how baseTs itself
    treats _origin_index.)
    """
    declared_freq: float
    ts_offset: float
    has_timestamp_offset: bool
    is_uniform_grid: bool

    @classmethod
    def from_series(cls, ts: "baseTs") -> "_IndexMeta":
        """Read the index metadata off a baseTs.

        Args:
            ts: The series to read.

        Returns:
            _IndexMeta: The four index-derived values.
        """
        # The *declaration*, not `ts.freq`: the property computes an
        # effective rate from the index when nothing was declared, and
        # storing that would silently promote a derived rate to a declared
        # one. Reading __dict__ rather than getattr is the pandas-subclass
        # rule - the property getters read __dict__ themselves.
        declaration = ts.__dict__.get("_freq_declaration")
        return cls(
            declared_freq=(declaration[0] if declaration else np.nan),
            ts_offset=ts.ts_offset,
            has_timestamp_offset=ts.has_timestamp_offset,
            is_uniform_grid=ts.is_uniform_grid,
        )

    def constructor_kwargs(self) -> Dict[str, Any]:
        """The keyword arguments that reproduce this index metadata.

        Returns:
            dict: Keywords accepted by baseTs.__init__.
        """
        return {
            "freq": self.declared_freq,
            "ts_offset": self.ts_offset,
            "has_timestamp_offset": self.has_timestamp_offset,
            "is_uniform_grid": self.is_uniform_grid,
        }


def default_col_meta_row(label: Hashable) -> Dict[str, Any]:
    """The metadata a column starts life with.

    Args:
        label: The column's label, which becomes its default signal name.

    Returns:
        dict: One row's worth of the nine per-column fields.
    """
    return {
        "signal_name": str(label),
        "history": [],
        "is_filtered": False,
        "is_interpolated": False,
        "is_outlier_filtered": False,
        "last_process": "",
        "outlier_indices": None,
        "lowess_fit": None,
        # Its own instance, never a shared default: configuring one column's
        # filter must not reach into another's.
        "outlier_filter": LowessOutlierFilter(),
    }


def harvest_col_meta(ts: "baseTs") -> Dict[str, Any]:
    """Take a column's own metadata off a baseTs, ready to become a row.

    Args:
        ts: The series to read.

    Returns:
        dict: The nine per-column fields.
    """
    row = {field: getattr(ts, field) for field in COL_META_FIELDS}
    # history is a mutable list the source object keeps using; sharing it
    # would let a later append on either side be seen by both.
    row["history"] = list(row["history"] or [])
    return row


def hydrate_column(
    values: np.ndarray,
    index: Sequence[float],
    index_meta: "_IndexMeta",
    row: Any,
    label: Hashable,
) -> "baseTs":
    """Build a real baseTs from one column's values and its metadata row.

    Args:
        values: The column's data.
        index: The frame's shared index, in seconds.
        index_meta: The frame's shared index metadata.
        row: The column's metadata, as a mapping or a pandas Series - either
            supports `.get()`, which is all this relies on.
        label: The column's label, used as a fallback signal name.

    Returns:
        baseTs: A series carrying every slot the frame was holding for it.
    """
    kwargs: Dict[str, Any] = index_meta.constructor_kwargs()
    for field in _CONSTRUCTOR_FIELDS:
        kwargs[field] = row.get(field)
    kwargs["history"] = list(row.get("history") or [])
    # signal_name is not a constructor keyword here: baseTs.__init__
    # upper-cases any signal_name it is *given as a keyword*, but its
    # property setter does not - only __init__ does. col_meta rows carry the
    # label in whatever case the caller used, and hydrating a column must
    # not mangle it. So the field is left out of kwargs and assigned through
    # the setter below, the same pattern used for outlier_filter.
    signal_name = row.get("signal_name")
    if signal_name in (None, ""):
        signal_name = str(label)

    ts = baseTs(data=np.asarray(values), times=np.asarray(index, dtype=float), **kwargs)
    ts.signal_name = signal_name
    # Not a constructor keyword either. Shared by reference deliberately,
    # matching baseTs.copy(), which shares the filter rather than
    # duplicating it.
    ts.outlier_filter = row.get("outlier_filter")
    return ts


def refuse_reserved_columns(user_col_meta: Optional[pd.DataFrame]) -> None:
    """Refuse user attributes that collide with the fields baseDf maintains.

    Args:
        user_col_meta: Caller-supplied column attributes, or None.

    Raises:
        ValidationError: If any column name is one of COL_META_FIELDS.
    """
    if user_col_meta is None:
        return
    collisions = [c for c in user_col_meta.columns if c in COL_META_FIELDS]
    if collisions:
        raise ValidationError(
            f"col_meta column(s) {collisions!r} collide with fields baseDf "
            f"maintains itself ({list(COL_META_FIELDS)!r}). Rename your "
            f"column(s), or drop them if you meant to let baseDf manage them."
        )
