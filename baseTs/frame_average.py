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
