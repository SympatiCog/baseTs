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
