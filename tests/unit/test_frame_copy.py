"""baseDf.copy(): an independent frame, not a view.

Added after Task 9 review: NOT_BROADCAST's own comment claims "copy is
excluded because the frame has its own," but no such method existed - a
misleading comment is worse than a missing one, so this closes the gap
rather than just correcting the words.
"""
import numpy as np
import pandas as pd

from baseTs.frame import baseDf


def _frame() -> baseDf:
    n = 16
    df = pd.DataFrame(
        {"c0": np.arange(n, dtype=float), "c1": np.arange(n, dtype=float) * 2},
        index=np.arange(n) / 8.0,
    )
    user = pd.DataFrame({"network": ["DMN", "FPN"]}, index=["c0", "c1"])
    return baseDf(df, freq=8.0, col_meta=user)


def test_copy_is_a_baseDf_with_equal_values_and_col_meta():
    frame = _frame()
    got = frame.copy()
    assert isinstance(got, baseDf)
    assert got is not frame
    assert np.allclose(np.asarray(got.df), np.asarray(frame.df))
    assert list(got.col_meta.columns) == list(frame.col_meta.columns)
    assert got.col_meta.at["c1", "network"] == "FPN"


def test_a_deep_copy_is_independent_of_the_original():
    frame = _frame()
    got = frame.copy(deep=True)
    got._df.iloc[0, 0] = 999.0
    got._col_meta.at["c0", "network"] = "changed"
    assert frame.df.iloc[0, 0] == 0.0
    assert frame.col_meta.at["c0", "network"] == "DMN"


def test_a_shallow_copy_shares_the_underlying_frames():
    frame = _frame()
    got = frame.copy(deep=False)
    assert got.df is frame.df or np.shares_memory(
        np.asarray(got.df), np.asarray(frame.df)
    )
