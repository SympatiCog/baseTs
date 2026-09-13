# baseDf Multichannel Container Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `baseDf`, a container holding many time series on one shared index, so a 64-channel specparam table or a 400-ROI fMRI extract can be filtered, measured and selectively averaged with the `baseTs` methods that already exist.

**Architecture:** `baseDf` is *backed by* a `pd.DataFrame` but does **not** subclass one. It holds three pieces of state: `_df` (values), `_index_meta` (the metadata that belongs to the shared index), and `_col_meta` (a DataFrame with one row per column holding the metadata that belongs to each column, plus arbitrary user attributes). Transforms are broadcast by hydrating each column into a real `baseTs`, calling the existing method, and harvesting the result.

**Tech Stack:** Python 3.12, pandas 3.0.1, numpy 2.5.2, pytest. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-09-13-basedf-multichannel-design.md` — read it first. The plan argues from it; where this plan gives a number the spec also gives, the spec is the authority.

## Global Constraints

- **Do not modify `baseTs`, `TimeSeriesData`, or the module-level `from_df`.** Spec scope boundary. If a task appears to require it, stop and raise it.
- **Naming:** classes camelCase (`baseDf`), functions/variables snake_case, constants UPPER_CASE. Per `CLAUDE.md`.
- **Style:** 4-space indent, PEP 8, Black + isort, 100-character line target, type annotations on every parameter and return, `"""` docstrings with Args/Returns.
- **Errors:** raise `ValidationError` (from `baseTs.utils`; it subclasses `TimeSeriesError` and `ValueError`). Messages must state what was refused **and what to do instead**.
- **Flag rule, applied everywhere:** contamination ORs, treatment ANDs. `is_interpolated` propagates if **any** contributor carries it and is never reset. `is_filtered` / `is_outlier_filtered` hold only if **every** contributor was treated.
- **NaN rule:** `skipna=False` is the default for averaging. `min_count` is meaningful only when `skipna=True`; passing it alongside `skipna=False` is refused, not ignored.
- **Test commands:** `pytest tests/unit/<file> -v`; full suite `pytest`; lint `flake8 baseTs/*.py`; types `mypy baseTs/*.py`.
- **Commit trailers:** every commit ends with
  `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`

---

## File Structure

| File | Responsibility |
|---|---|
| `baseTs/frame_meta.py` (new) | Splits `TimeSeriesData._metadata` into shared vs per-column. Owns `_IndexMeta`, `COL_META_FIELDS`, `harvest_col_meta`, `hydrate_column`, `default_col_meta_row`. Nothing here knows what a frame is. |
| `baseTs/frame.py` (new) | The `baseDf` container: state, invariants, entry points, indexing, broadcast, measurements, correlation. |
| `baseTs/frame_average.py` (new) | Averaging: selection resolution, the flag rules, common-prefix history. Free functions, so the rules are testable without a frame. |
| `baseTs/__init__.py` (modify) | Export `baseDf`. |
| `docs/API_FRAME.md` (new) | Public API reference, matching `docs/API.md` style. |
| `docs/EXAMPLES.md` (modify) | Parquet and long→wide recipes. |

Tests, one file per concern, matching the repo's intent-naming convention:
`test_frame_meta_round_trip.py`, `test_frame_refuses_bad_construction.py`, `test_frame_entry_points.py`, `test_frame_indexing_keeps_col_meta.py`, `test_frame_broadcast_equals_series.py`, `test_frame_measurements.py`, `test_frame_correlation.py`, `test_frame_average_rules.py`.

---

### Task 1: Metadata split — `frame_meta.py`

**Files:**
- Create: `baseTs/frame_meta.py`
- Test: `tests/unit/test_frame_meta_round_trip.py`

**Interfaces:**
- Consumes: `baseTs.core.baseTs`, `baseTs.utils.ValidationError`, `baseTs.LowessOutlierFilter.LowessOutlierFilter`
- Produces: `COL_META_FIELDS: tuple[str, ...]` (9 names), `_IndexMeta` (frozen dataclass with `declared_freq`, `ts_offset`, `has_timestamp_offset`, `is_uniform_grid`; classmethod `from_series(ts)`; method `constructor_kwargs() -> dict`), `harvest_col_meta(ts) -> dict`, `hydrate_column(values, index, index_meta, row, label) -> baseTs`, `default_col_meta_row(label) -> dict`, `refuse_reserved_columns(user_col_meta) -> None`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_frame_meta_round_trip.py`:

```python
"""A column's metadata must survive the trip out of a baseTs and back."""
import numpy as np
import pytest

from baseTs import baseTs
from baseTs.frame_meta import (
    COL_META_FIELDS,
    _IndexMeta,
    default_col_meta_row,
    harvest_col_meta,
    hydrate_column,
    refuse_reserved_columns,
)
from baseTs.utils import ValidationError


def _series() -> baseTs:
    times = np.arange(64) / 8.0
    ts = baseTs(data=np.arange(64.0), times=times, freq=8.0,
                ts_offset=1.7e9, signal_name="Cz")
    return ts.lowpass_at(2.0)


def test_round_trip_preserves_every_column_field():
    ts = _series()
    row = harvest_col_meta(ts)
    back = hydrate_column(np.asarray(ts.data), ts.index,
                          _IndexMeta.from_series(ts), row, "Cz")
    for field in COL_META_FIELDS:
        original, restored = getattr(ts, field), getattr(back, field)
        if isinstance(original, list):
            assert list(restored) == list(original), field
        elif field == "outlier_filter":
            assert restored is original, field
        else:
            assert restored == original or restored is original, field


def test_round_trip_preserves_the_shared_index_metadata():
    ts = _series()
    back = hydrate_column(np.asarray(ts.data), ts.index,
                          _IndexMeta.from_series(ts), harvest_col_meta(ts), "Cz")
    assert back.freq == ts.freq
    assert back.ts_offset == ts.ts_offset
    assert back.has_timestamp_offset == ts.has_timestamp_offset
    assert np.array_equal(np.asarray(back.__dict__["_origin_index"]),
                          np.asarray(ts.__dict__["_origin_index"]))


def test_history_is_not_shared_with_the_source():
    ts = _series()
    row = harvest_col_meta(ts)
    ts.history.append("mutated after harvest")
    assert "mutated after harvest" not in row["history"]


def test_an_underived_freq_is_not_promoted_to_a_declaration():
    # ts.freq computes an effective rate when nothing was declared. Storing
    # that would silently turn a derived rate into a declared one.
    ts = baseTs(data=np.arange(16.0), times=np.arange(16) / 4.0)
    assert np.isnan(_IndexMeta.from_series(ts).declared_freq)


def test_reserved_column_names_are_refused():
    import pandas as pd
    bad = pd.DataFrame({"history": [[]], "network": ["DMN"]}, index=["Cz"])
    with pytest.raises(ValidationError, match="history"):
        refuse_reserved_columns(bad)


def test_default_row_gives_each_column_its_own_filter():
    a, b = default_col_meta_row("c0"), default_col_meta_row("c1")
    assert a["outlier_filter"] is not b["outlier_filter"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_frame_meta_round_trip.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'baseTs.frame_meta'`

- [ ] **Step 3: Write the implementation**

Create `baseTs/frame_meta.py`:

```python
# -*- coding: utf-8 -*-
"""Metadata bookkeeping for :class:`baseTs.frame.baseDf`.

`TimeSeriesData._metadata` declares fourteen slots beyond ``_name``. They split
in two, and the split is what makes a shared-index container possible at all:

* Four are functions of the **index**, so a frame holds exactly one of each.
  (`_origin_index` is a fifth index-derived slot, but it is *derived* rather
  than stored: passing ``ts_offset`` with ``has_timestamp_offset=True``
  restamps an identical origin at the constructor.)
* Nine belong to a **column** and are held as one row of ``baseDf.col_meta``.

Nothing in this module knows what a frame is; it moves a column between a
``baseTs`` and a row of metadata, and that is all.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Hashable, Optional, Sequence

import numpy as np
import pandas as pd

from .core import baseTs
from .LowessOutlierFilter import LowessOutlierFilter
from .utils import ValidationError

# The nine slots of TimeSeriesData._metadata that belong to one column.
# Public names throughout: `outlier_indices` and `lowess_fit` are properties
# over the underscore-prefixed attributes, and are the names the baseTs
# constructor accepts.
COL_META_FIELDS = (
    "signal_name",
    "history",
    "is_filtered",
    "is_interpolated",
    "is_outlier_filtered",
    "last_process",
    "outlier_indices",
    "lowess_fit",
    "outlier_filter",
)

# All of those except `outlier_filter`, which baseTs.__init__ does not accept
# as a keyword and which is therefore assigned after construction.
_CONSTRUCTOR_FIELDS = tuple(f for f in COL_META_FIELDS if f != "outlier_filter")


@dataclass(frozen=True)
class _IndexMeta:
    """The half of the metadata that is a function of the shared index alone."""

    declared_freq: float = np.nan
    ts_offset: float = 0.0
    has_timestamp_offset: bool = False
    is_uniform_grid: bool = False

    @classmethod
    def from_series(cls, ts: baseTs) -> "_IndexMeta":
        """Read the index metadata off a baseTs.

        Args:
            ts: The series to read.

        Returns:
            _IndexMeta: The four index-derived values.
        """
        # The *declaration*, not `ts.freq`: the property computes an effective
        # rate from the index when nothing was declared, and storing that would
        # silently promote a derived rate to a declared one. Reading __dict__
        # rather than getattr is the pandas-subclass rule - the property
        # getters read __dict__ themselves.
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
            dict: Keywords accepted by ``baseTs.__init__``.
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


def harvest_col_meta(ts: baseTs) -> Dict[str, Any]:
    """Take a column's own metadata off a baseTs, ready to become a row.

    Args:
        ts: The series to read.

    Returns:
        dict: The nine per-column fields.
    """
    row = {field: getattr(ts, field) for field in COL_META_FIELDS}
    # history is a mutable list the source object keeps using; sharing it would
    # let a later append on either side be seen by both.
    row["history"] = list(row["history"] or [])
    return row


def hydrate_column(
    values: np.ndarray,
    index: Sequence[float],
    index_meta: _IndexMeta,
    row: Any,
    label: Hashable,
) -> baseTs:
    """Build a real baseTs from one column's values and its metadata row.

    Args:
        values: The column's data.
        index: The frame's shared index, in seconds.
        index_meta: The frame's shared index metadata.
        row: The column's metadata, as a mapping or a pandas Series.
        label: The column's label, used as a fallback signal name.

    Returns:
        baseTs: A series carrying every slot the frame was holding for it.
    """
    kwargs: Dict[str, Any] = index_meta.constructor_kwargs()
    for field in _CONSTRUCTOR_FIELDS:
        kwargs[field] = row[field]
    kwargs["history"] = list(row["history"] or [])
    if kwargs.get("signal_name") in (None, ""):
        kwargs["signal_name"] = str(label)

    ts = baseTs(data=np.asarray(values), times=np.asarray(index, dtype=float), **kwargs)
    # Not a constructor keyword. Shared by reference deliberately, matching
    # baseTs.copy(), which shares the filter rather than duplicating it.
    ts.outlier_filter = row["outlier_filter"]
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
            f"col_meta may not define {collisions!r}: baseDf maintains those "
            f"itself from each column's own processing. Rename them, or drop "
            f"them and let the frame fill them in. Reserved names: "
            f"{list(COL_META_FIELDS)!r}"
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_frame_meta_round_trip.py -v`
Expected: PASS, 6 tests

- [ ] **Step 5: Commit**

```bash
git add baseTs/frame_meta.py tests/unit/test_frame_meta_round_trip.py
git commit -m "Split the metadata a column owns from the metadata the index owns

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: The container — state, invariants, refusals

**Files:**
- Create: `baseTs/frame.py`
- Test: `tests/unit/test_frame_refuses_bad_construction.py`

**Interfaces:**
- Consumes: everything Task 1 produces.
- Produces: `baseDf(data, times=None, freq=np.nan, ts_offset=np.nan, col_meta=None)`; properties `df`, `col_meta`, `columns`, `index`, `shape`, `freq`, `ts_offset`; `__len__`, `__repr__`; private `_check_invariants()`, `_with(df, col_meta, index_meta=None) -> baseDf`.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_frame_refuses_bad_construction.py`:

```python
"""baseDf refuses the states in which its metadata could not mean one thing."""
import numpy as np
import pandas as pd
import pytest

from baseTs.frame import baseDf
from baseTs.utils import ValidationError


def _frame_df(n: int = 32) -> pd.DataFrame:
    return pd.DataFrame(
        {"c0": np.arange(n, dtype=float), "c1": np.arange(n, dtype=float) * 2},
        index=np.arange(n) / 8.0,
    )


def test_builds_from_a_dataframe_and_reports_its_shape():
    frame = baseDf(_frame_df(), freq=8.0)
    assert list(frame.columns) == ["c0", "c1"]
    assert len(frame) == 32
    assert frame.shape == (32, 2)
    assert frame.freq == 8.0


def test_every_column_starts_with_its_own_metadata_row():
    frame = baseDf(_frame_df())
    assert list(frame.col_meta.index) == ["c0", "c1"]
    assert frame.col_meta.at["c0", "signal_name"] == "c0"
    assert frame.col_meta.at["c0", "history"] == []
    assert (frame.col_meta.at["c0", "outlier_filter"]
            is not frame.col_meta.at["c1", "outlier_filter"])


def test_duplicate_column_labels_are_refused():
    df = _frame_df()
    df.columns = ["c0", "c0"]
    with pytest.raises(ValidationError, match="duplicate column labels"):
        baseDf(df)


def test_reserved_col_meta_names_are_refused():
    user = pd.DataFrame({"is_filtered": [True, True]}, index=["c0", "c1"])
    with pytest.raises(ValidationError, match="is_filtered"):
        baseDf(_frame_df(), col_meta=user)


def test_user_attributes_are_kept_alongside_the_maintained_fields():
    user = pd.DataFrame({"network": ["DMN", "FPN"], "bad": [False, True]},
                        index=["c0", "c1"])
    frame = baseDf(_frame_df(), col_meta=user)
    assert frame.col_meta.at["c1", "network"] == "FPN"
    assert bool(frame.col_meta.at["c1", "bad"]) is True
    assert frame.col_meta.at["c1", "is_filtered"] is False


def test_col_meta_for_an_unknown_column_is_refused():
    user = pd.DataFrame({"network": ["DMN"]}, index=["nope"])
    with pytest.raises(ValidationError, match="nope"):
        baseDf(_frame_df(), col_meta=user)


def test_non_numeric_columns_are_refused_by_name():
    df = _frame_df()
    df["label"] = ["x"] * len(df)
    with pytest.raises(ValidationError, match="label"):
        baseDf(df)


def test_an_explicit_offset_sets_has_timestamp_offset():
    frame = baseDf(_frame_df(), freq=8.0, ts_offset=1.7e9)
    assert frame.ts_offset == 1.7e9
    assert frame._index_meta.has_timestamp_offset is True


def test_the_alignment_invariant_is_enforced():
    frame = baseDf(_frame_df())
    frame._col_meta = frame._col_meta.reindex(["c1", "c0"])
    with pytest.raises(ValidationError, match="out of step"):
        frame._check_invariants()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_frame_refuses_bad_construction.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'baseTs.frame'`

- [ ] **Step 3: Write the implementation**

Create `baseTs/frame.py`:

```python
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

        if times is not None:
            index = pd.Index(np.asarray(times, dtype=float))
            if len(index) != len(df):
                raise ValidationError(
                    f"times has {len(index)} entries but the data has "
                    f"{len(df)} rows; they must match."
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
        table = pd.DataFrame.from_dict(rows, orient="index")
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
                f"columns={list(columns)!r}"
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
            np.zeros(len(self._df.index)), self._df.index, self._index_meta,
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_frame_refuses_bad_construction.py -v`
Expected: PASS, 9 tests

- [ ] **Step 5: Commit**

```bash
git add baseTs/frame.py tests/unit/test_frame_refuses_bad_construction.py
git commit -m "Add the baseDf container, its invariants and its refusals

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Entry points — `from_df` and `from_series`

**Files:**
- Modify: `baseTs/frame.py` (add two classmethods to `baseDf`)
- Test: `tests/unit/test_frame_entry_points.py`

**Interfaces:**
- Consumes: `baseDf.__init__` from Task 2; `_IndexMeta.from_series` and `harvest_col_meta` from Task 1.
- Produces: `baseDf.from_df(df, time_col="time", value_cols=None, freq=np.nan, ts_offset=np.nan, col_meta=None) -> baseDf`; `baseDf.from_series(series, labels=None) -> baseDf`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_frame_entry_points.py`:

```python
"""Getting into a frame from a wide table or from existing baseTs objects."""
import numpy as np
import pandas as pd
import pytest

from baseTs import baseTs
from baseTs.frame import baseDf
from baseTs.utils import ValidationError


def _wide(n: int = 32) -> pd.DataFrame:
    return pd.DataFrame({
        "time": np.arange(n) / 8.0,
        "c0": np.arange(n, dtype=float),
        "c1": np.arange(n, dtype=float) * 2,
    })


def test_from_df_takes_every_numeric_column_but_the_time_column():
    frame = baseDf.from_df(_wide(), time_col="time", freq=8.0)
    assert list(frame.columns) == ["c0", "c1"]
    assert np.allclose(frame.index, np.arange(32) / 8.0)


def test_from_df_honours_an_explicit_value_cols():
    frame = baseDf.from_df(_wide(), time_col="time", value_cols=["c1"])
    assert list(frame.columns) == ["c1"]


def test_from_df_refuses_a_missing_time_column():
    with pytest.raises(ValidationError, match="nope"):
        baseDf.from_df(_wide(), time_col="nope")


def test_from_df_names_the_non_numeric_columns_it_refuses():
    wide = _wide()
    wide["site"] = ["a"] * len(wide)
    with pytest.raises(ValidationError, match="site"):
        baseDf.from_df(wide, time_col="time")


def test_from_df_sorts_by_time_when_the_table_is_out_of_order():
    wide = _wide().sample(frac=1.0, random_state=0)
    frame = baseDf.from_df(wide, time_col="time")
    assert np.all(np.diff(np.asarray(frame.index)) > 0)


def test_from_series_carries_each_series_own_metadata():
    times = np.arange(32) / 8.0
    a = baseTs(data=np.arange(32.0), times=times, freq=8.0, signal_name="Cz")
    b = baseTs(data=np.arange(32.0) * 2, times=times, freq=8.0, signal_name="Pz")
    a = a.lowpass_at(2.0)
    frame = baseDf.from_series([a, b])
    assert list(frame.columns) == ["Cz", "Pz"]
    assert frame.col_meta.at["Cz", "history"] == list(a.history)
    assert frame.col_meta.at["Pz", "history"] == []
    assert frame.col_meta.at["Cz", "is_filtered"] == a.is_filtered


def test_from_series_refuses_mismatched_indices():
    a = baseTs(data=np.arange(32.0), times=np.arange(32) / 8.0, freq=8.0,
               signal_name="a")
    b = baseTs(data=np.arange(32.0), times=np.arange(32) / 4.0, freq=4.0,
               signal_name="b")
    with pytest.raises(ValidationError, match="align_with"):
        baseDf.from_series([a, b])


def test_from_series_refuses_conflicting_offsets():
    times = np.arange(32) / 8.0
    a = baseTs(data=np.arange(32.0), times=times, freq=8.0, ts_offset=1.0,
               signal_name="a")
    b = baseTs(data=np.arange(32.0), times=times, freq=8.0, ts_offset=2.0,
               signal_name="b")
    with pytest.raises(ValidationError, match="ts_offset"):
        baseDf.from_series([a, b])


def test_from_series_refuses_an_empty_list():
    with pytest.raises(ValidationError, match="at least one"):
        baseDf.from_series([])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_frame_entry_points.py -v`
Expected: FAIL — `AttributeError: type object 'baseDf' has no attribute 'from_df'`

- [ ] **Step 3: Write the implementation**

Add to `baseTs/frame.py`, inside `class baseDf`, after `__init__`.

```python
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
            chosen = [c for c in df.columns
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
            times=np.asarray(df[time_col], dtype=float),
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
        table = pd.DataFrame.from_dict(rows, orient="index")
        table = table.reindex(list(names))[list(COL_META_FIELDS)]

        frame = object.__new__(cls)
        frame._df = values
        frame._col_meta = table
        frame._index_meta = index_meta
        frame._check_invariants()
        return frame
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_frame_entry_points.py -v`
Expected: PASS, 9 tests

- [ ] **Step 5: Commit**

```bash
git add baseTs/frame.py tests/unit/test_frame_entry_points.py
git commit -m "Add from_df and from_series entry points to baseDf

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Indexing — one column out, several columns across

**Files:**
- Modify: `baseTs/frame.py`
- Test: `tests/unit/test_frame_indexing_keeps_col_meta.py`

**Interfaces:**
- Consumes: `_with`, `hydrate_column`.
- Produces: `baseDf.__getitem__(key)` returning `baseTs` for a scalar label and `baseDf` for a list-like; `baseDf.select(where=None, select=None) -> baseDf`; `baseDf.time_slice` is **not** added here (it arrives as a broadcast transform in Task 5).

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_frame_indexing_keeps_col_meta.py`:

```python
"""Selecting columns must carry each column's metadata with it."""
import numpy as np
import pandas as pd
import pytest

from baseTs import baseTs
from baseTs.frame import baseDf
from baseTs.utils import ValidationError


def _frame() -> baseDf:
    n = 32
    df = pd.DataFrame(
        {"c0": np.arange(n, dtype=float),
         "c1": np.arange(n, dtype=float) * 2,
         "c2": np.arange(n, dtype=float) * 3},
        index=np.arange(n) / 8.0,
    )
    user = pd.DataFrame({"network": ["DMN", "FPN", "DMN"], "bad": [False, False, True]},
                        index=["c0", "c1", "c2"])
    return baseDf(df, freq=8.0, col_meta=user)


def test_a_scalar_label_gives_a_real_baseTs():
    column = _frame()["c1"]
    assert isinstance(column, baseTs)
    assert column.freq == 8.0
    assert column.signal_name == "c1"
    assert np.allclose(np.asarray(column.data), np.arange(32) * 2)


def test_a_list_gives_a_frame_and_keeps_the_user_attributes():
    sub = _frame()[["c2", "c0"]]
    assert isinstance(sub, baseDf)
    assert list(sub.columns) == ["c2", "c0"]
    assert list(sub.col_meta.index) == ["c2", "c0"]
    assert sub.col_meta.at["c2", "network"] == "DMN"
    assert bool(sub.col_meta.at["c2", "bad"]) is True


def test_selection_by_query_uses_the_user_attributes():
    sub = _frame().select(where="network == 'DMN' and not bad")
    assert list(sub.columns) == ["c0"]


def test_a_boolean_mask_selects_columns():
    sub = _frame()[[True, False, True]]
    assert list(sub.columns) == ["c0", "c2"]


def test_an_unknown_label_is_refused_by_name():
    with pytest.raises(ValidationError, match="nope"):
        _frame()[["c0", "nope"]]


def test_a_selection_matching_nothing_is_refused():
    with pytest.raises(ValidationError, match="matched no columns"):
        _frame().select(where="network == 'nowhere'")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_frame_indexing_keeps_col_meta.py -v`
Expected: FAIL — `TypeError: 'baseDf' object is not subscriptable`

- [ ] **Step 3: Write the implementation**

Add to `class baseDf` in `baseTs/frame.py`:

```python
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
            self._df.index,
            self._index_meta,
            self._col_meta.loc[key],
            key,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_frame_indexing_keeps_col_meta.py -v`
Expected: PASS, 6 tests

- [ ] **Step 5: Commit**

```bash
git add baseTs/frame.py tests/unit/test_frame_indexing_keeps_col_meta.py
git commit -m "Index a baseDf by label, list, mask or col_meta query

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Broadcast — the 39 transforms

This is the task the design exists for. Its test is the reason to trust the rest.

**Files:**
- Modify: `baseTs/frame.py`
- Test: `tests/unit/test_frame_broadcast_equals_series.py`

**Interfaces:**
- Consumes: `__getitem__`, `harvest_col_meta`, `_IndexMeta.from_series`, `_with`.
- Produces: `baseDf.TRANSFORMS: tuple[str, ...]` (39 names), `baseDf.NOT_BROADCAST: frozenset[str]`, `baseDf._broadcast(name, args, kwargs)`, and one generated method per name in `TRANSFORMS`.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_frame_broadcast_equals_series.py`:

```python
"""A broadcast column must equal the same call made on a lone baseTs.

This is the test the container's design rests on: if a frame's column can
diverge from the series it stands for, nothing else here is trustworthy.
"""
import inspect
import warnings

import numpy as np
import pandas as pd
import pytest

from baseTs import baseTs
from baseTs.frame import baseDf
from baseTs.frame_meta import COL_META_FIELDS
from baseTs.utils import ValidationError

N = 256
TIMES = np.arange(N) / 16.0


def _columns() -> dict:
    rng = np.random.default_rng(0)
    a = rng.normal(size=N) + np.sin(2 * np.pi * 1.5 * TIMES)
    b = rng.normal(size=N) + np.sin(2 * np.pi * 3.0 * TIMES)
    a[40] = 30.0          # an outlier in one column only, so the columns
    b[200] = -25.0        # genuinely diverge in values and flags
    return {"c0": a, "c1": b}


def _frame() -> baseDf:
    cols = _columns()
    return baseDf(pd.DataFrame(cols, index=TIMES), freq=16.0)


def _lone(label: str) -> baseTs:
    return baseTs(data=_columns()[label], times=TIMES.copy(), freq=16.0,
                  signal_name=label)


# (method name, positional args, keyword args)
CALLS = [
    ("zscale", (), {}),
    ("center", (), {}),
    ("abs", (), {}),
    ("scale", (2.0,), {}),
    ("normalize_range", (), {}),
    ("detrend", (), {}),
    ("lowess_detrend", (), {}),
    ("lowpass_at", (4.0,), {}),
    ("highpass_at", (0.5,), {}),
    ("bandpass_at", (0.5, 4.0), {}),
    ("notch_at", (2.0,), {}),
    ("lowpass_filter", (4.0,), {}),
    ("highpass_filter", (0.5,), {}),
    ("bandpass_filter", (0.5, 4.0), {}),
    ("notch_filter", (2.0,), {}),
    ("butterpass_at", (0.5, 4.0), {}),
    ("gauss_filter", (2.0,), {}),
    ("sg_filter", (11, 2), {}),
    ("rolling_mean", (5,), {}),
    ("rolling_std", (5,), {}),
    ("rolling_median", (5,), {}),
    ("rolling_max", (5,), {}),
    ("rolling_min", (5,), {}),
    ("diff_ts", (), {}),
    ("diff_ts", (), {"zeropad": True}),
    ("interpolate_missing", (), {}),
    ("interpto_hz", (8.0,), {}),
    ("interpto_samples", (128,), {}),
    ("interp_to_uniform_grid", (), {"inplace": False}),
    ("time_slice", (1.0, 8.0), {}),
    ("trimto_timepoints", (1.0, 8.0), {}),
    ("shift_time", (3,), {}),
    ("set_outlier_filter", (), {}),
    ("filter_outliers", (), {}),
    ("remove_outliers", (), {}),
    ("apply_function", (np.sqrt,), {}),
    ("dediff_ts", (), {}),
    ("resample", ("1s",), {}),
    ("interpolate_gaps", (), {}),
    ("set_indices_to_nan_and_interpolate", ([10, 11],), {}),
]


@pytest.mark.parametrize("name,args,kwargs", CALLS,
                         ids=[f"{n}{sorted(k)}" for n, _, k in CALLS])
def test_a_broadcast_column_equals_the_lone_series(name, args, kwargs):
    warnings.filterwarnings("ignore")
    frame_out = getattr(_frame(), name)(*args, **kwargs)
    for label in ("c0", "c1"):
        expected = getattr(_lone(label), name)(*args, **kwargs)
        actual = frame_out[label]
        assert np.allclose(np.asarray(actual.data, dtype=float),
                           np.asarray(expected.data, dtype=float),
                           equal_nan=True), f"{name} values for {label}"
        assert np.allclose(np.asarray(actual.index, dtype=float),
                           np.asarray(expected.index, dtype=float)), f"{name} index"
        for field in ("signal_name", "is_filtered", "is_interpolated",
                      "is_outlier_filtered", "last_process"):
            assert getattr(actual, field) == getattr(expected, field), \
                f"{name}.{field} for {label}"
        assert list(actual.history) == list(expected.history), f"{name} history"


def test_the_call_table_covers_every_broadcast_transform():
    """A transform added later without a frame test fails here, rather than
    being silently unbroadcast."""
    covered = {name for name, _, _ in CALLS}
    assert covered == set(baseDf.TRANSFORMS), (
        f"untested: {sorted(set(baseDf.TRANSFORMS) - covered)}; "
        f"stale: {sorted(covered - set(baseDf.TRANSFORMS))}"
    )


def test_the_transform_inventory_matches_baseTs():
    """State the rule, don't maintain a carve-out list: TRANSFORMS is every
    baseTs method annotated as returning a baseTs, minus NOT_BROADCAST."""
    found = set()
    for name, func in inspect.getmembers(baseTs, predicate=inspect.isfunction):
        if name.startswith("_") or func.__qualname__.split(".")[0] != "baseTs":
            continue
        if inspect.signature(func).return_annotation in ('"baseTs"', "baseTs"):
            found.add(name)
    assert found - baseDf.NOT_BROADCAST == set(baseDf.TRANSFORMS)


def test_inplace_replaces_the_frames_contents():
    frame = _frame()
    before = np.asarray(frame.df["c0"]).copy()
    returned = frame.center(inplace=True)
    assert returned is frame
    assert not np.allclose(np.asarray(frame.df["c0"]), before)


def test_user_attributes_survive_a_broadcast():
    cols = _columns()
    user = pd.DataFrame({"network": ["DMN", "FPN"]}, index=["c0", "c1"])
    frame = baseDf(pd.DataFrame(cols, index=TIMES), freq=16.0, col_meta=user)
    assert frame.lowpass_at(4.0).col_meta.at["c1", "network"] == "FPN"


def test_a_data_dependent_index_is_refused():
    frame = _frame()

    def _ragged(self, **kwargs):
        # Returns a different length depending on the data, which is exactly
        # what a shared index cannot survive.
        # argmax differs by construction: c0 spikes at 40, c1 at 200.
        keep = 200 + int(np.argmax(np.abs(np.asarray(self.data, dtype=float)))) % 7
        return self.iloc[:keep]

    baseDf._ragged = lambda self, **kw: self._broadcast("_ragged_src", (), kw)
    baseTs._ragged_src = _ragged
    try:
        with pytest.raises(ValidationError, match="different index"):
            frame._ragged()
    finally:
        del baseDf._ragged, baseTs._ragged_src
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_frame_broadcast_equals_series.py -v`
Expected: FAIL — `AttributeError: type object 'baseDf' has no attribute 'TRANSFORMS'`

- [ ] **Step 3: Write the implementation**

Add to `class baseDf` in `baseTs/frame.py`:

```python
    #: Every baseTs method annotated as returning a baseTs that is *not*
    #: broadcast. `copy` is excluded because the frame has its own.
    NOT_BROADCAST = frozenset({"copy"})

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
        "remove_outliers", "resample", "rolling_max", "rolling_mean",
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
        first_out = None
        values: Dict[Hashable, np.ndarray] = {}
        rows: Dict[Hashable, Dict[str, Any]] = {}

        for label in self._df.columns:
            out = getattr(self[label], name)(*args, **kwargs)
            if index is None:
                index, first_out = out.index, out
            elif not index.equals(out.index):
                raise ValidationError(
                    f"{name}() returned a different index for column {label!r} "
                    f"({len(out.index)} samples) than for "
                    f"{list(self._df.columns)[0]!r} ({len(index)} samples). "
                    f"baseDf requires every column to share one index, so a "
                    f"transform whose output index depends on its data values "
                    f"cannot be broadcast. Pull the columns out with "
                    f"frame[label] and handle them individually."
                )
            values[label] = np.asarray(out.data, dtype=float)
            rows[label] = harvest_col_meta(out)

        new_df = pd.DataFrame(values, index=index, columns=self._df.columns)
        harvested = pd.DataFrame.from_dict(rows, orient="index").reindex(self._df.columns)
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
```

Note: `harvest_col_meta` and `COL_META_FIELDS` are already imported by Task 2.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_frame_broadcast_equals_series.py -v`
Expected: PASS — 40 parametrized equivalence cases (one per entry in `CALLS`) plus 5 others. Every one of those 40 calls was run against a lone `baseTs` on this fixture before the plan was written; all 40 succeed, so an error here is in the broadcast machinery, not in the arguments.

If `test_the_call_table_covers_every_broadcast_transform` ever fails, add the missing name to `CALLS` with arguments that work on a 256-sample 16 Hz series. Do **not** shrink `TRANSFORMS` to make it pass — that is the failure the guard exists to prevent.

- [ ] **Step 5: Commit**

```bash
git add baseTs/frame.py tests/unit/test_frame_broadcast_equals_series.py
git commit -m "Broadcast every baseTs transform across a frame's columns

The equivalence test asserts a broadcast column equals the same call on a
lone baseTs in values, index and metadata, and a guard test asserts the
inventory is every annotated transform minus NOT_BROADCAST, so a method
added later cannot be silently unbroadcast.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Measurements — column in, value out

**Files:**
- Modify: `baseTs/frame.py`
- Test: `tests/unit/test_frame_measurements.py`

**Interfaces:**
- Consumes: `__getitem__`.
- Produces: `baseDf.measure(name, *args, **kwargs)`; wrappers `get_statistics() -> pd.DataFrame`, `falff(**kw) -> pd.Series`, `relative_band_power(**kw) -> pd.Series`, `detect_outliers(**kw) -> pd.DataFrame`, `get_peaks(**kw) -> pd.Series`, `compute_fft_power(**kw) -> tuple[np.ndarray, pd.DataFrame]`, `get_frequency_content(**kw) -> tuple[np.ndarray, pd.DataFrame]`, `duration() -> float`.

Measured return shapes on a 1024-sample series, so the dispatch table is not guesswork: `get_statistics` → `dict` of 11 keys; `falff` → `float`; `relative_band_power` → `float`; `detect_outliers` → `ndarray` of length N; `get_peaks` → `list`; `compute_fft_power` and `get_frequency_content` → 2-tuples whose first element is the shared frequency axis.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_frame_measurements.py`:

```python
"""Measuring a frame gives one value per column, keyed by column label."""
import warnings

import numpy as np
import pandas as pd
import pytest

from baseTs import baseTs
from baseTs.frame import baseDf
from baseTs.utils import ValidationError

N = 1024
TIMES = np.arange(N) / 10.0


def _frame() -> baseDf:
    rng = np.random.default_rng(0)
    df = pd.DataFrame(
        {"c0": rng.normal(size=N) + np.sin(2 * np.pi * 0.05 * TIMES),
         "c1": rng.normal(size=N) + np.sin(2 * np.pi * 0.20 * TIMES)},
        index=TIMES,
    )
    return baseDf(df, freq=10.0)


def test_a_scalar_measure_gives_a_series_keyed_by_column():
    warnings.filterwarnings("ignore")
    got = _frame().falff()
    assert isinstance(got, pd.Series)
    assert list(got.index) == ["c0", "c1"]
    assert got.dtype.kind == "f"


def test_a_scalar_measure_matches_the_lone_series():
    warnings.filterwarnings("ignore")
    frame = _frame()
    expected = frame["c1"].falff()
    assert frame.falff()["c1"] == pytest.approx(expected)


def test_a_mapping_measure_gives_a_dataframe():
    got = _frame().get_statistics()
    assert isinstance(got, pd.DataFrame)
    assert list(got.index) == ["c0", "c1"]
    assert got.shape[1] == len(_frame()["c0"].get_statistics())


def test_a_per_sample_measure_gives_a_frame_shaped_result():
    got = _frame().detect_outliers()
    assert isinstance(got, pd.DataFrame)
    assert got.shape == (N, 2)
    assert np.array_equal(np.asarray(got.index), TIMES)


def test_a_shared_axis_measure_returns_the_axis_once():
    warnings.filterwarnings("ignore")
    freqs, power = _frame().compute_fft_power()
    assert isinstance(freqs, np.ndarray)
    assert isinstance(power, pd.DataFrame)
    assert len(freqs) == len(power.index)
    assert list(power.columns) == ["c0", "c1"]


def test_an_object_measure_gives_a_series_of_objects():
    got = _frame().get_peaks()
    assert isinstance(got, pd.Series)
    assert isinstance(got["c0"], list)


def test_duration_is_a_frame_level_scalar():
    assert _frame().duration() == pytest.approx(_frame()["c0"].duration())


def test_measure_refuses_an_unknown_method():
    with pytest.raises(ValidationError, match="no_such_measure"):
        _frame().measure("no_such_measure")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_frame_measurements.py -v`
Expected: FAIL — `AttributeError: 'baseDf' object has no attribute 'falff'`

- [ ] **Step 3: Write the implementation**

Add to `class baseDf` in `baseTs/frame.py`:

```python
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
        return axis, pd.DataFrame(payload, index=pd.Index(axis),
                                  columns=self._df.columns)

    def falff(self, *args: Any, **kwargs: Any) -> pd.Series:
        """fALFF per column. See ``baseTs.falff``.

        Returns:
            pd.Series: One value per column.
        """
        return self.measure("falff", *args, **kwargs)

    def relative_band_power(self, *args: Any, **kwargs: Any) -> pd.Series:
        """Relative band power per column. See ``baseTs.relative_band_power``.

        Returns:
            pd.Series: One value per column.
        """
        return self.measure("relative_band_power", *args, **kwargs)

    def get_statistics(self, *args: Any, **kwargs: Any) -> pd.DataFrame:
        """Summary statistics per column. See ``baseTs.get_statistics``.

        Returns:
            pd.DataFrame: Columns as rows, statistic names as columns.
        """
        return self.measure("get_statistics", *args, **kwargs)

    def detect_outliers(self, *args: Any, **kwargs: Any) -> pd.DataFrame:
        """Outlier mask per column. See ``baseTs.detect_outliers``.

        Returns:
            pd.DataFrame: Frame index by column.
        """
        return self.measure("detect_outliers", *args, **kwargs)

    def get_peaks(self, *args: Any, **kwargs: Any) -> pd.Series:
        """Peaks per column. See ``baseTs.get_peaks``.

        Returns:
            pd.Series: One list per column.
        """
        return self.measure("get_peaks", *args, **kwargs)

    def compute_fft_power(self, *args: Any,
                          **kwargs: Any) -> Tuple[np.ndarray, pd.DataFrame]:
        """FFT power per column over one shared frequency axis.

        Returns:
            tuple: ``(freqs, power)`` where ``power`` is indexed by ``freqs``.
        """
        return self.measure("compute_fft_power", *args, **kwargs)

    def get_frequency_content(self, *args: Any,
                              **kwargs: Any) -> Tuple[np.ndarray, pd.DataFrame]:
        """Frequency content per column over one shared axis.

        Returns:
            tuple: ``(freqs, content)``.
        """
        return self.measure("get_frequency_content", *args, **kwargs)

    def duration(self) -> float:
        """Span of the shared index in seconds.

        Returns:
            float: The duration, which is a property of the index and so is
                the same for every column.
        """
        index = np.asarray(self._df.index, dtype=float)
        return float(index[-1] - index[0]) if len(index) else 0.0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_frame_measurements.py -v`
Expected: PASS, 8 tests

- [ ] **Step 5: Commit**

```bash
git add baseTs/frame.py tests/unit/test_frame_measurements.py
git commit -m "Measure a frame column-wise into Series and DataFrames

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Correlation — one seed against every column

**Files:**
- Modify: `baseTs/frame.py`
- Test: `tests/unit/test_frame_correlation.py`

**Interfaces:**
- Consumes: `__getitem__` (Task 4), `_df`, `columns`.
- Produces: `baseDf.correlation_with(other, method="pearson") -> pd.Series`; `baseDf.correlation_matrix(other=None, method="pearson") -> pd.DataFrame`.

The default is a **seed**: one series correlated against every column — a behavioural regressor against a FOOOF measure per electrode, or a seed timeseries against each ROI. An all-pairs matrix is available but never implicit.

`baseTs.correlation_with` (core.py:2242) inner-joins then calls `Series.corr`. The vector case delegates per column, so it is equivalent by construction. The matrix case cannot delegate — 400 x 400 would be 160,000 aligned calls — so it intersects the indices once and uses `DataFrame.corrwith` per right-hand column. That was measured identical to the per-pair path for `pearson`, `spearman` and `kendall` with a NaN present; the test below pins it.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_frame_correlation.py`:

```python
"""Correlating a frame: one seed against every column, or frame against frame."""
import warnings

import numpy as np
import pandas as pd
import pytest

from baseTs import baseTs
from baseTs.frame import baseDf
from baseTs.utils import ValidationError

N = 200
TIMES = np.arange(N) / 10.0


def _left() -> baseDf:
    rng = np.random.default_rng(0)
    data = {f"l{i}": rng.normal(size=N) + np.sin(2 * np.pi * 0.1 * TIMES) * i
            for i in range(4)}
    data["l2"][5] = np.nan
    return baseDf(pd.DataFrame(data, index=TIMES), freq=10.0)


def _right() -> baseDf:
    rng = np.random.default_rng(1)
    data = {f"r{j}": rng.normal(size=N) + np.cos(2 * np.pi * 0.1 * TIMES) * j
            for j in range(3)}
    return baseDf(pd.DataFrame(data, index=TIMES), freq=10.0)


def _seed() -> baseTs:
    rng = np.random.default_rng(2)
    return baseTs(data=rng.normal(size=N), times=TIMES.copy(), freq=10.0,
                  signal_name="behaviour")


def test_a_seed_gives_one_value_per_column():
    got = _left().correlation_with(_seed())
    assert isinstance(got, pd.Series)
    assert list(got.index) == ["l0", "l1", "l2", "l3"]
    assert got.dtype.kind == "f"


def test_the_seed_result_equals_the_per_column_baseTs_call():
    frame, seed = _left(), _seed()
    got = frame.correlation_with(seed)
    for label in frame.columns:
        assert got[label] == pytest.approx(
            frame[label].correlation_with(seed), nan_ok=True)


@pytest.mark.parametrize("method", ["pearson", "spearman", "kendall"])
def test_the_matrix_equals_the_per_pair_calls(method):
    warnings.filterwarnings("ignore")
    left, right = _left(), _right()
    got = left.correlation_matrix(right, method=method)
    assert got.shape == (4, 3)
    for lc in left.columns:
        for rc in right.columns:
            assert got.at[lc, rc] == pytest.approx(
                left[lc].correlation_with(right[rc], method=method), nan_ok=True)


def test_the_matrix_against_itself_is_square_and_symmetric():
    got = _left().correlation_matrix()
    assert got.shape == (4, 4)
    assert np.allclose(np.diag(got.to_numpy()), 1.0)
    assert np.allclose(got.to_numpy(), got.to_numpy().T, equal_nan=True)


def test_a_frame_passed_to_correlation_with_is_refused():
    with pytest.raises(ValidationError, match="correlation_matrix"):
        _left().correlation_with(_right())


def test_a_series_passed_to_correlation_matrix_is_refused():
    with pytest.raises(ValidationError, match="correlation_with"):
        _left().correlation_matrix(_seed())


def test_frames_sharing_no_timepoints_are_refused():
    other = _right()
    other._df.index = pd.Index(np.asarray(other._df.index) + 10_000.0)
    with pytest.raises(ValidationError, match="no timepoints"):
        _left().correlation_matrix(other)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_frame_correlation.py -v`
Expected: FAIL — `AttributeError: 'baseDf' object has no attribute 'correlation_with'`

- [ ] **Step 3: Write the implementation**

Add to `class baseDf` in `baseTs/frame.py`:

```python
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
        return pd.DataFrame(
            {rc: left.corrwith(right[rc], method=method) for rc in right.columns},
            index=left.columns,
            columns=right.columns,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_frame_correlation.py -v`
Expected: PASS, 9 tests (3 of them the parametrized matrix-equivalence case)

- [ ] **Step 5: Commit**

```bash
git add baseTs/frame.py tests/unit/test_frame_correlation.py
git commit -m "Correlate a frame against a seed, or against another frame

The default is one series against every column; an all-pairs matrix has
its own name so it is never implicit. The matrix path vectorises via
corrwith, measured identical to the per-pair baseTs calls.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Selective averaging — `average` and `average_by`

**Files:**
- Create: `baseTs/frame_average.py`
- Modify: `baseTs/frame.py`
- Test: `tests/unit/test_frame_average_rules.py`

**Interfaces:**
- Consumes: `_resolve_labels`, `hydrate_column`, `_IndexMeta`, `COL_META_FIELDS`.
- Produces: `common_prefix(histories) -> list`, `averaged_row(col_meta, labels, skipna, reduced, selection_desc, name) -> dict`; `baseDf.average(select=None, where=None, skipna=False, min_count=None, name=None) -> baseTs`; `baseDf.average_by(by, select=None, where=None, skipna=False, min_count=None) -> baseDf`.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_frame_average_rules.py`:

```python
"""Averaging columns: which flags survive, what history says, and NaN policy."""
import warnings

import numpy as np
import pandas as pd
import pytest

from baseTs import baseTs
from baseTs.frame import baseDf
from baseTs.frame_average import common_prefix
from baseTs.utils import ValidationError

N = 64
TIMES = np.arange(N) / 8.0


def _frame(**kw) -> baseDf:
    df = pd.DataFrame(
        {"c0": np.ones(N), "c1": np.ones(N) * 3.0, "c2": np.ones(N) * 5.0},
        index=TIMES,
    )
    user = pd.DataFrame({"network": ["DMN", "DMN", "FPN"]},
                        index=["c0", "c1", "c2"])
    return baseDf(df, freq=8.0, col_meta=user, **kw)


def test_average_returns_a_baseTs_on_the_shared_index():
    got = _frame().average()
    assert isinstance(got, baseTs)
    assert np.allclose(np.asarray(got.data), 3.0)
    assert np.allclose(np.asarray(got.index), TIMES)
    assert got.freq == 8.0


def test_average_honours_a_col_meta_query():
    got = _frame().average(where="network == 'DMN'")
    assert np.allclose(np.asarray(got.data), 2.0)


def test_average_by_returns_one_column_per_group():
    got = _frame().average_by("network")
    assert isinstance(got, baseDf)
    assert sorted(got.columns) == ["DMN", "FPN"]
    assert np.allclose(np.asarray(got.df["DMN"]), 2.0)
    assert np.allclose(np.asarray(got.df["FPN"]), 5.0)
    assert got.col_meta.at["DMN", "signal_name"] == "DMN"


def test_contamination_ors_and_treatment_ands():
    frame = _frame()
    frame._col_meta.at["c0", "is_interpolated"] = True
    frame._col_meta.at["c0", "is_filtered"] = True
    got = frame.average()
    assert got.is_interpolated is True     # any contributor contaminates
    assert got.is_filtered is False        # not every contributor was treated


def test_treatment_holds_when_every_contributor_was_treated():
    frame = _frame()
    for label in ("c0", "c1", "c2"):
        frame._col_meta.at[label, "is_filtered"] = True
    assert frame.average().is_filtered is True


def test_history_keeps_the_common_prefix_and_summarises_divergence():
    frame = _frame()
    for label in ("c0", "c1", "c2"):
        frame._col_meta.at[label, "history"] = ["shared step"]
    frame._col_meta.at["c2", "history"] = ["shared step", "extra step"]
    history = frame.average().history
    assert history[0] == "shared step"
    assert "extra step" not in history
    assert "diverged" in history[-1]
    assert "Averaged 3" in history[-1]


def test_history_records_the_dropped_per_column_artifacts():
    assert "dropped" in _frame().average().history[-1]


def test_nan_propagates_by_default():
    frame = _frame()
    frame._df.iloc[10, 0] = np.nan
    assert np.isnan(np.asarray(frame.average().data)[10])


def test_skipna_is_explicit_and_says_so_in_history():
    frame = _frame()
    frame._df.iloc[10, 0] = np.nan
    got = frame.average(skipna=True)
    assert np.asarray(got.data)[10] == pytest.approx(4.0)
    assert "skipna=True" in got.history[-1]
    assert "reduced n" in got.history[-1]


def test_min_count_alongside_skipna_false_is_refused():
    with pytest.raises(ValidationError, match="min_count"):
        _frame().average(min_count=2)


def test_min_count_floors_the_contributor_count():
    frame = _frame()
    frame._df.iloc[10, 0] = np.nan
    frame._df.iloc[10, 1] = np.nan
    got = frame.average(skipna=True, min_count=3)
    assert np.isnan(np.asarray(got.data)[10])


def test_an_empty_selection_is_refused():
    with pytest.raises(ValidationError, match="matched no columns"):
        _frame().average(where="network == 'nowhere'")


def test_a_name_overrides_the_derived_signal_name():
    assert _frame().average(name="DMN mean").signal_name == "DMN mean"


def test_common_prefix_stops_at_the_first_difference():
    assert common_prefix([["a", "b", "c"], ["a", "b"], ["a", "x"]]) == ["a"]
    assert common_prefix([]) == []
    assert common_prefix([["a"], ["a"]]) == ["a"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_frame_average_rules.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'baseTs.frame_average'`

- [ ] **Step 3: Write the implementation**

Create `baseTs/frame_average.py`:

```python
# -*- coding: utf-8 -*-
"""The rules that decide what an average of several columns may claim.

Free functions rather than methods, so the rules can be tested without a
frame. Two of them carry the weight:

* **Contamination ORs, treatment ANDs.** ``is_interpolated`` says *some values
  here were not measured* - a property of the data, so it propagates if any
  contributor carries it. ``is_filtered`` says *this series has been treated* -
  a claim about the whole series, so it holds only if every contributor was.
* **History is the common prefix, then a summary.** Claiming "bandpassed
  1-10 Hz" is honest only if every input was bandpassed.
"""
from __future__ import annotations

from typing import Any, Dict, Hashable, List, Optional, Sequence

import pandas as pd

from .LowessOutlierFilter import LowessOutlierFilter


def common_prefix(histories: Sequence[Sequence[str]]) -> List[str]:
    """The leading entries every history shares.

    Args:
        histories: One history per contributing column.

    Returns:
        list: The shared leading entries, which may be empty.
    """
    if not histories:
        return []
    shared: List[str] = []
    for entries in zip(*histories):
        first = entries[0]
        if all(entry == first for entry in entries):
            shared.append(first)
        else:
            break
    return shared


def averaged_row(
    col_meta: pd.DataFrame,
    labels: Sequence[Hashable],
    skipna: bool,
    reduced: int,
    selection_desc: str,
    name: Optional[str] = None,
) -> Dict[str, Any]:
    """The metadata an averaged series is entitled to.

    Args:
        col_meta: The frame's column metadata.
        labels: The contributing column labels.
        skipna: Whether NaNs were skipped rather than propagated.
        reduced: How many timepoints ran at less than full contributor count.
        selection_desc: Human-readable description of the selection.
        name: Signal name to use instead of one derived from the selection.

    Returns:
        dict: A row of the nine per-column fields.
    """
    rows = col_meta.loc[list(labels)]
    n = len(labels)
    histories = [list(h or []) for h in rows["history"]]
    shared = common_prefix(histories)
    diverged = sum(1 for h in histories if len(h) > len(shared))

    message = f"Averaged {n} column(s) [{selection_desc}]"
    if skipna:
        message += f"; skipna=True, {reduced} timepoint(s) at reduced n"
    else:
        message += "; skipna=False, any NaN propagates"
    if diverged:
        message += (f"; inputs diverged after step {len(shared)}: {diverged} of "
                    f"{n} carried further processing")
    message += ("; per-column outlier_indices, lowess_fit and outlier_filter "
                "dropped as meaningless for a mean")

    return {
        "signal_name": name if name is not None else f"mean({selection_desc})",
        "history": shared + [message],
        # Contamination ORs.
        "is_interpolated": bool(rows["is_interpolated"].any()),
        # Treatment ANDs.
        "is_filtered": bool(rows["is_filtered"].all()),
        "is_outlier_filtered": bool(rows["is_outlier_filtered"].all()),
        "last_process": "_average",
        "outlier_indices": None,
        "lowess_fit": None,
        "outlier_filter": LowessOutlierFilter(),
    }
```

Add to `class baseDf` in `baseTs/frame.py` (and import `averaged_row` from `.frame_average`):

```python
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
    ) -> Any:
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
        return hydrate_column(values, self._df.index, self._index_meta, row,
                              row["signal_name"])

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
                or the selection matches nothing.
        """
        keys = [by] if isinstance(by, str) else list(by)
        missing = [k for k in keys if k not in self._col_meta.columns]
        if missing:
            raise ValidationError(
                f"no such col_meta column(s) to group by: {missing!r}. "
                f"Available: {[c for c in self._col_meta.columns]!r}"
            )
        labels = self._resolve_labels(select=select, where=where)
        subset = self._col_meta.loc[labels]

        values: Dict[Hashable, np.ndarray] = {}
        rows: Dict[Hashable, Dict[str, Any]] = {}
        for group, members in subset.groupby(keys[0] if len(keys) == 1 else keys,
                                             sort=True):
            group_labels = list(members.index)
            column, reduced = self._average_values(group_labels, skipna, min_count)
            values[group] = column
            rows[group] = averaged_row(self._col_meta, group_labels, skipna,
                                       reduced, f"{keys[0]} == {group!r}",
                                       name=str(group))

        order = list(values.keys())
        new_df = pd.DataFrame(values, index=self._df.index, columns=order)
        new_col_meta = pd.DataFrame.from_dict(rows, orient="index")
        new_col_meta = new_col_meta.reindex(order)[list(COL_META_FIELDS)]
        return self._with(new_df, new_col_meta)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_frame_average_rules.py -v`
Expected: PASS, 14 tests

- [ ] **Step 5: Commit**

```bash
git add baseTs/frame_average.py baseTs/frame.py tests/unit/test_frame_average_rules.py
git commit -m "Average selected columns, honestly

Contamination ORs and treatment ANDs; history keeps the common prefix and
summarises divergence rather than claiming a step not every input took;
NaN propagates unless skipna is asked for explicitly.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: Export and documentation

**Files:**
- Modify: `baseTs/__init__.py`
- Create: `docs/API_FRAME.md`
- Modify: `docs/EXAMPLES.md`
- Test: existing `tests/unit/test_docs_fenced_blocks.py` must still pass.

**Interfaces:**
- Consumes: everything above.
- Produces: `from baseTs import baseDf`.

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_frame_entry_points.py`:

```python
def test_baseDf_is_exported_from_the_package():
    import baseTs

    assert baseTs.baseDf is baseDf
    assert "baseDf" in baseTs.__all__
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_frame_entry_points.py::test_baseDf_is_exported_from_the_package -v`
Expected: FAIL — `AttributeError: module 'baseTs' has no attribute 'baseDf'`

- [ ] **Step 3: Write the implementation**

Replace `baseTs/__init__.py` with:

```python
"""
baseTs - A Python library for time series analysis
"""

from .core import baseTs, from_df
from .frame import baseDf
from .series import TimeSeriesData
from .version import __version__

__all__ = ['baseTs', 'baseDf', 'from_df', 'TimeSeriesData']
```

Create `docs/API_FRAME.md` documenting, in the style of `docs/API.md`: the three pieces of state; `baseDf.__init__`, `from_df`, `from_series`; indexing and `select`; the broadcast transforms (list `baseDf.TRANSFORMS`); `measure` and its wrappers; `correlation_with` and `correlation_matrix`, making clear which is the default and why; `average` and `average_by` including the flag and NaN rules verbatim from the spec.

Check `docs/API.md` for the exact heading and code-fence conventions first — `tests/unit/test_docs_fenced_blocks.py` executes fenced Python blocks in the docs, so every example must actually run.

Add to `docs/EXAMPLES.md` two recipes, each a runnable fenced block:

```python
# Parquet -> baseDf
import pandas as pd
from baseTs import baseDf

wide = pd.read_parquet("channels.parquet")
frame = baseDf.from_df(wide, time_col="time", freq=250.0)
cleaned = frame.bandpass_at(1.0, 40.0).filter_outliers()
network = cleaned.average(where="network == 'DMN'")
```

```python
# Long table -> baseDf
import pandas as pd
from baseTs import baseDf

long = pd.read_parquet("roi_timeseries.parquet")   # time, roi, value
wide = long.pivot(index="time", columns="roi", values="value").reset_index()
frame = baseDf.from_df(wide, time_col="time", freq=0.5)
```

- [ ] **Step 4: Run the tests**

Run: `pytest tests/unit/test_frame_entry_points.py tests/unit/test_docs_fenced_blocks.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add baseTs/__init__.py docs/API_FRAME.md docs/EXAMPLES.md tests/unit/test_frame_entry_points.py
git commit -m "Export baseDf and document it

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 10: Full-suite verification

**Files:** none created; fixes only, wherever the suite points.

- [ ] **Step 1: Run the whole suite**

Run: `pytest`
Expected: every pre-existing test still passes (the baseline before this work was 2319 passed, 0 skipped; the new tests add to that). Nothing in `baseTs/core.py` or `baseTs/series.py` was modified, so a failure there means an import-time side effect from `frame.py` — most likely the `setattr` loop at the bottom — and must be fixed, not suppressed.

- [ ] **Step 2: Lint and type-check**

Run: `flake8 baseTs/*.py` then `mypy baseTs/*.py`
Expected: clean, or no new findings relative to `git stash`-ing the branch.

- [ ] **Step 3: Check the frame does not leak into baseTs**

Run:

```bash
grep -n "frame" baseTs/core.py baseTs/series.py || echo "clean: no frame references in core or series"
```

Expected: `clean` — the dependency points one way only.

- [ ] **Step 4: Sanity-check at the target scale**

Run:

```bash
python - <<'PY'
import time, warnings, numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from baseTs import baseDf
n, k = 1200, 400                      # an fMRI ROI extract
rng = np.random.default_rng(0)
df = pd.DataFrame(rng.normal(size=(n, k)),
                  columns=[f"roi{i:03d}" for i in range(k)],
                  index=np.arange(n) * 0.72)
meta = pd.DataFrame({"network": ["DMN", "FPN"] * (k // 2)}, index=df.columns)
t0 = time.time()
frame = baseDf(df, freq=1/0.72, col_meta=meta)
out = frame.bandpass_at(0.01, 0.1).average_by("network")
print(f"400 ROI x 1200 TR bandpass + average_by: {time.time()-t0:.2f}s -> {out.shape}")
print(out.col_meta[["signal_name", "is_filtered"]])
PY
```

Expected: completes in seconds, `out.shape == (1200, 2)`, and `is_filtered` is True for both groups (every contributor was bandpassed, so treatment ANDs to True).

- [ ] **Step 5: Commit any fixes**

```bash
git add -A
git commit -m "Fix findings from full-suite verification

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review Notes

**Spec coverage.** Object model → Tasks 1–2. Four operation buckets → Tasks 5 (transforms), 6 and 7 (measurements and correlation), 8 (reduction); plots are out of scope per the spec. `average`/`average_by` with flag, history and NaN rules → Task 8. Correlation → Task 7. Indexing exception → Task 4. Three entry points and the persistence deferral → Task 3 and Task 9 (`to_dataframe` is `frame.df`, which the docs say). Error rules 1–8 → rules 1, 2, 4 in Task 2; 5 in Tasks 2 and 3; 7, 8 in Task 3; 3 in Task 5; 6 in Task 4. Testing section → the test file per task, with broadcast equivalence in Task 5.

**Verified before writing.** All 40 entries in Task 5's `CALLS` table were run against a lone `baseTs` on that exact fixture (256 samples, 16 Hz, an outlier at index 40): 40 calls, 0 failures. The table therefore covers all 39 names in `TRANSFORMS` — `diff_ts` appears twice, with and without `zeropad` — and the coverage guard passes on a correct implementation rather than needing to be grown first.

**Correlation (Stan, 2026-09-13).** Resolved into its own task rather than left in `MEASURE_KINDS`: the default is one seed series against every column, and the all-pairs matrix has a separate name so it is never implicit. The matrix path vectorises through `DataFrame.corrwith`, verified identical to per-pair `baseTs.correlation_with` for all three methods with a NaN present.
