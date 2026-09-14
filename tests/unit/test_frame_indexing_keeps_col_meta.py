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
