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
