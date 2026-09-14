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
    # baseTs.__init__ upper-cases a signal_name passed as a keyword (it is a
    # normalising property; see frame_meta.hydrate_column's comment on this), so
    # "Cz" is already "CZ" the moment `a` is constructed - before from_series ever
    # sees it. The frame reads signal_name faithfully; it does not restore a case
    # baseTs itself never kept.
    times = np.arange(32) / 8.0
    a = baseTs(data=np.arange(32.0), times=times, freq=8.0, signal_name="Cz")
    b = baseTs(data=np.arange(32.0) * 2, times=times, freq=8.0, signal_name="Pz")
    a = a.lowpass_at(2.0)
    frame = baseDf.from_series([a, b])
    assert list(frame.columns) == ["CZ", "PZ"]
    assert frame.col_meta.at["CZ", "history"] == list(a.history)
    # baseTs.__init__ always appends a "Created baseTs object..." entry, so a
    # freshly constructed series' history is never empty - verified
    # interactively (b.history == ["Created baseTs object with 32 samples"]).
    # from_series must carry that entry faithfully, not manufacture []. `a`
    # additionally has the lowpass entry appended on top of its own creation
    # entry, which is what the first assertion above already covers.
    assert frame.col_meta.at["PZ", "history"] == list(b.history)
    assert frame.col_meta.at["CZ", "is_filtered"] == a.is_filtered


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


def test_baseDf_is_exported_from_the_package():
    import baseTs

    assert baseTs.baseDf is baseDf
    assert "baseDf" in baseTs.__all__
