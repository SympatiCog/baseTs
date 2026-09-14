"""Regressions from Phase 3 adversarial review of the baseDf implementation.

Two rounds of review found and confirmed real bugs by running the actual
code, not by inspection alone. Each is pinned here so it cannot silently
come back. See the plan's Self-Review Notes / commit history for the
context each fix was found under.
"""
import numpy as np
import pandas as pd
import pytest

from baseTs.frame import baseDf
from baseTs.utils import ValidationError


def _frame(n: int = 16) -> baseDf:
    df = pd.DataFrame(
        {"c0": np.arange(n, dtype=float), "c1": np.arange(n, dtype=float) * 2},
        index=np.arange(n) / 8.0,
    )
    return baseDf(df, freq=8.0)


# --- average_by and a NaN grouping key -------------------------------------

def test_average_by_refuses_a_column_with_no_grouping_key():
    user = pd.DataFrame({"network": ["DMN", np.nan]}, index=["c0", "c1"])
    frame = baseDf(_frame().df, freq=8.0, col_meta=user)
    with pytest.raises(ValidationError, match="c1"):
        frame.average_by("network")


def test_average_by_refuses_rather_than_crashes_when_every_key_is_missing():
    user = pd.DataFrame({"network": [np.nan, np.nan]}, index=["c0", "c1"])
    frame = baseDf(_frame().df, freq=8.0, col_meta=user)
    with pytest.raises(ValidationError, match="no value for grouping key"):
        frame.average_by("network")


def test_average_by_refuses_grouping_by_a_non_scalar_field():
    with pytest.raises(ValidationError, match="history"):
        _frame().average_by(by="history")


# --- col_meta dtype survives a broadcast or an average_by -------------------

def test_broadcast_col_meta_flags_stay_python_bool():
    user = pd.DataFrame({"network": ["DMN", "FPN"]}, index=["c0", "c1"])
    frame = baseDf(_frame().df, freq=8.0, col_meta=user)
    out = frame.center()
    assert out.col_meta["is_filtered"].dtype == object
    assert out["c0"].is_filtered is False


def test_average_by_col_meta_flags_stay_python_bool():
    user = pd.DataFrame({"network": ["DMN", "FPN"]}, index=["c0", "c1"])
    frame = baseDf(_frame().df, freq=8.0, col_meta=user)
    got = frame.average_by("network")
    assert got.col_meta["is_filtered"].dtype == object
    assert got["DMN"].is_filtered is False


# --- from_df's time column must be numeric ----------------------------------

def test_from_df_refuses_a_non_numeric_time_column():
    wide = pd.DataFrame({"time": ["a", "b", "c"], "x": [1.0, 2.0, 3.0]})
    with pytest.raises(ValidationError, match="not numeric"):
        baseDf.from_df(wide, time_col="time")


# --- select= must be list-like, not a bare scalar ---------------------------

def test_select_refuses_a_bare_string_rather_than_iterating_it():
    with pytest.raises(ValidationError, match=r"Wrap a single label in a list"):
        _frame().select(select="c0")


def test_select_refuses_a_bare_bool():
    with pytest.raises(ValidationError, match="bool"):
        _frame().select(select=True)


def test_select_refuses_a_repeated_label():
    with pytest.raises(ValidationError, match="repeats"):
        _frame().average(select=["c0", "c0", "c1"])


# --- where= wraps pandas' own query errors ----------------------------------

def test_where_wraps_a_syntax_error():
    with pytest.raises(ValidationError, match="valid query"):
        _frame().select(where="network == ")


def test_where_wraps_an_undefined_column():
    with pytest.raises(ValidationError, match="valid query"):
        _frame().select(where="nonexistent_col == 1")


# --- a duplicated col_meta index is refused up front ------------------------

def test_construction_refuses_a_duplicated_col_meta_index():
    user = pd.DataFrame({"network": ["DMN", "FPN"]}, index=["c0", "c0"])
    with pytest.raises(ValidationError, match="duplicate row label"):
        baseDf(_frame().df, col_meta=user)


# --- min_count has a floor of 1 ---------------------------------------------

@pytest.mark.parametrize("bad", [0, -1, -5])
def test_min_count_below_one_is_refused(bad):
    with pytest.raises(ValidationError, match="min_count"):
        _frame().average(skipna=True, min_count=bad)


# --- the broadcast index-mismatch message actually distinguishes the case --

def test_the_index_mismatch_message_names_the_real_divergence():
    from baseTs import baseTs

    n = 16
    t = np.arange(n) / 8.0
    frame = baseDf(
        pd.DataFrame({"a": np.arange(n, dtype=float),
                     "b": np.arange(n, dtype=float) * 2}, index=t),
        freq=8.0,
    )

    def _shifted(self, **kw):
        shift = 0.0 if self.signal_name == "a" else 100.0
        return baseTs(data=np.asarray(self.data),
                      times=np.asarray(self.index) + shift,
                      freq=self.freq, history=list(self.history))

    baseDf._shifted_test = lambda self, **kw: self._broadcast("_shifted_src", (), kw)
    baseTs._shifted_src = _shifted
    try:
        with pytest.raises(ValidationError) as exc:
            frame._shifted_test()
        message = str(exc.value)
        # Same sample count on both sides - the old message said "16 samples"
        # for both, which told a reader nothing. It must now say how the
        # indices actually differ.
        assert "same length" in message
        assert "differing value" in message
    finally:
        del baseDf._shifted_test, baseTs._shifted_src
