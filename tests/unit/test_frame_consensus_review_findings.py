"""Regressions from Phase 3 Round 3: a non-Anthropic consensus review.

Two independent panelists (a different model lineage from the in-house
reviewers) each traced the implementation against running code. Eight
findings were confirmed by reproduction before being fixed here; five
others they raised did not reproduce and are not represented.
"""
import numpy as np
import pandas as pd
import pytest

from baseTs import baseTs
from baseTs.frame import baseDf
from baseTs.utils import ValidationError


def _frame(n: int = 16) -> baseDf:
    df = pd.DataFrame(
        {"c0": np.arange(n, dtype=float), "c1": np.arange(n, dtype=float) * 2},
        index=np.arange(n) / 8.0,
    )
    return baseDf(df, freq=8.0)


# --- from_series: ts_offset alone is not enough -----------------------------

def test_from_series_refuses_a_has_timestamp_offset_mismatch():
    # Same numeric ts_offset (0.0), but one series declared it explicitly and
    # the other never set an origin - checking only the value let this
    # through, and the frame silently took the first series' flag.
    n = 16
    t = np.arange(n) / 8.0
    a = baseTs(data=np.arange(n, dtype=float), times=t, freq=8.0,
              ts_offset=0.0, signal_name="a")
    b = baseTs(data=np.arange(n, dtype=float), times=t, freq=8.0, signal_name="b")
    with pytest.raises(ValidationError, match="has_timestamp_offset"):
        baseDf.from_series([a, b])


# --- a tuple that IS a column label must read as that one column -----------

def test_a_tuple_column_label_from_average_by_is_indexable():
    frame = baseDf(
        _frame().df,
        freq=8.0,
        col_meta=pd.DataFrame({"network": ["DMN", "FPN"], "hemi": ["L", "R"]},
                              index=["c0", "c1"]),
    )
    grouped = frame.average_by(["network", "hemi"])
    label = grouped.columns[0]
    assert isinstance(label, tuple)
    column = grouped[label]
    assert isinstance(column, baseTs)


def test_a_genuine_tuple_selector_still_selects_two_columns():
    frame = _frame()
    sub = frame[("c0", "c1")]
    assert isinstance(sub, baseDf)
    assert list(sub.columns) == ["c0", "c1"]


def test_select_also_handles_a_bare_tuple_column_label():
    # Same ambiguity as __getitem__, found while verifying that fix: select=
    # goes through _resolve_labels, which has its own _is_listlike check.
    frame = baseDf(
        _frame().df,
        freq=8.0,
        col_meta=pd.DataFrame({"network": ["DMN", "FPN"], "hemi": ["L", "R"]},
                              index=["c0", "c1"]),
    )
    grouped = frame.average_by(["network", "hemi"])
    label = grouped.columns[0]
    got = grouped.select(select=label)
    assert list(got.columns) == [label]


# --- copy() must isolate mutable per-column metadata ------------------------

def test_deep_copy_isolates_history_between_original_and_copy():
    frame = _frame()
    copy = frame.copy(deep=True)
    copy.col_meta.at["c0", "history"].append("MUTATED")
    assert "MUTATED" not in frame.col_meta.at["c0", "history"]


def test_deep_copy_still_shares_outlier_filter_matching_baseTs_convention():
    frame = _frame()
    copy = frame.copy(deep=True)
    assert (frame.col_meta.at["c0", "outlier_filter"]
            is copy.col_meta.at["c0", "outlier_filter"])


# --- an empty frame is refused, not left to crash three calls downstream ---

def test_an_empty_mapping_is_refused():
    with pytest.raises(ValidationError, match="at least one column"):
        baseDf({})


def test_a_zero_column_dataframe_is_refused():
    with pytest.raises(ValidationError, match="at least one column"):
        baseDf(pd.DataFrame(index=[1, 2, 3]))


# --- average_by carries its own grouping key(s) into the result ------------

def test_average_by_keeps_the_grouping_key_in_the_result():
    user = pd.DataFrame({"network": ["DMN", "FPN"]}, index=["c0", "c1"])
    frame = baseDf(_frame().df, freq=8.0, col_meta=user)
    got = frame.average_by("network")
    assert got.col_meta.at["DMN", "network"] == "DMN"
    assert got.col_meta.at["FPN", "network"] == "FPN"


def test_average_by_keeps_every_grouping_key_for_a_multi_key_group():
    user = pd.DataFrame({"network": ["DMN", "FPN"], "hemi": ["L", "R"]},
                        index=["c0", "c1"])
    frame = baseDf(_frame().df, freq=8.0, col_meta=user)
    got = frame.average_by(["network", "hemi"])
    row = got.col_meta.loc[("DMN", "L")]
    assert row["network"] == "DMN" and row["hemi"] == "L"


# --- min_count must be validated, not just coerced --------------------------

def test_min_count_refuses_a_non_integer_float():
    with pytest.raises(ValidationError, match="whole number"):
        _frame().average(skipna=True, min_count=1.5)


def test_min_count_refuses_a_string():
    with pytest.raises(ValidationError, match="whole number"):
        _frame().average(skipna=True, min_count="x")


def test_min_count_refuses_nan():
    with pytest.raises(ValidationError, match="whole number"):
        _frame().average(skipna=True, min_count=float("nan"))


def test_min_count_accepts_a_whole_number_float():
    frame = _frame()
    frame._df.iloc[0, 0] = np.nan
    # min_count=1.0: one contributor (c1) still present at position 0, so the
    # floor is met and the mean is that one remaining value, not NaN.
    got = frame.average(skipna=True, min_count=1.0)
    assert np.asarray(got.data)[0] == pytest.approx(np.asarray(frame.df["c1"])[0])


# --- average_by's `by` must be a valid shape --------------------------------

def test_average_by_refuses_an_empty_by():
    with pytest.raises(ValidationError, match="empty"):
        _frame().average_by(by=[])


def test_average_by_refuses_a_non_iterable_by():
    with pytest.raises(ValidationError, match="by must be"):
        _frame().average_by(by=5)


# --- correlation_matrix validates its method like everything else ----------

def test_correlation_matrix_refuses_an_unknown_method():
    with pytest.raises(ValidationError, match="method"):
        _frame().correlation_matrix(method="bogus")
