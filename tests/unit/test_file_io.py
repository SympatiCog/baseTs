"""Loading baseTs / baseDf objects from CSV and Parquet files."""
import numpy as np
import pandas as pd
import pytest

from baseTs import baseTs, from_csv, from_parquet
from baseTs.frame import baseDf
from baseTs.utils import ValidationError


def _long(n: int = 20) -> pd.DataFrame:
    return pd.DataFrame({
        "time": np.arange(n) / 4.0,
        "value": np.sin(np.arange(n)),
    })


def _wide(n: int = 20) -> pd.DataFrame:
    return pd.DataFrame({
        "time": np.arange(n) / 4.0,
        "c0": np.arange(n, dtype=float),
        "c1": np.arange(n, dtype=float) * 2,
    })


class TestBaseTsFromCsv:
    def test_round_trips_through_csv(self, tmp_path):
        path = tmp_path / "signal.csv"
        _long().to_csv(path, index=False)

        ts = from_csv(path)

        assert isinstance(ts, baseTs)
        assert len(ts.data) == 20
        assert ts.signal_name == "VALUE"

    def test_honours_custom_columns_and_freq(self, tmp_path):
        path = tmp_path / "signal.csv"
        _long().rename(columns={"time": "t", "value": "v"}).to_csv(path, index=False)

        ts = from_csv(path, time_col="t", data_col="v", freq=4.0, signal_name="Custom")

        assert ts.signal_name == "CUSTOM"
        assert ts.freq == 4.0

    def test_forwards_read_csv_kwargs(self, tmp_path):
        path = tmp_path / "signal.csv"
        _long().to_csv(path, index=False, sep=";")

        ts = from_csv(path, sep=";")

        assert len(ts.data) == 20

    def test_missing_column_raises_like_from_df(self, tmp_path):
        path = tmp_path / "signal.csv"
        _long().to_csv(path, index=False)

        with pytest.raises(ValueError, match="nope"):
            from_csv(path, data_col="nope")

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            from_csv(tmp_path / "does_not_exist.csv")


class TestBaseTsFromParquet:
    def test_round_trips_through_parquet(self, tmp_path):
        path = tmp_path / "signal.parquet"
        _long().to_parquet(path, index=False)

        ts = from_parquet(path)

        assert isinstance(ts, baseTs)
        assert len(ts.data) == 20
        assert ts.signal_name == "VALUE"

    def test_honours_custom_columns_and_freq(self, tmp_path):
        path = tmp_path / "signal.parquet"
        _long().rename(columns={"time": "t", "value": "v"}).to_parquet(path, index=False)

        ts = from_parquet(path, time_col="t", data_col="v", freq=4.0, signal_name="Custom")

        assert ts.signal_name == "CUSTOM"
        assert ts.freq == 4.0

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(Exception):
            from_parquet(tmp_path / "does_not_exist.parquet")


class TestBaseDfFromCsv:
    def test_takes_every_numeric_column_but_the_time_column(self, tmp_path):
        path = tmp_path / "wide.csv"
        _wide().to_csv(path, index=False)

        frame = baseDf.from_csv(path, time_col="time", freq=4.0)

        assert list(frame.columns) == ["c0", "c1"]
        assert np.allclose(frame.index, np.arange(20) / 4.0)

    def test_honours_an_explicit_value_cols(self, tmp_path):
        path = tmp_path / "wide.csv"
        _wide().to_csv(path, index=False)

        frame = baseDf.from_csv(path, time_col="time", value_cols=["c1"])

        assert list(frame.columns) == ["c1"]

    def test_refuses_a_missing_time_column(self, tmp_path):
        path = tmp_path / "wide.csv"
        _wide().to_csv(path, index=False)

        with pytest.raises(ValidationError, match="nope"):
            baseDf.from_csv(path, time_col="nope")


class TestBaseDfFromParquet:
    def test_takes_every_numeric_column_but_the_time_column(self, tmp_path):
        path = tmp_path / "wide.parquet"
        _wide().to_parquet(path, index=False)

        frame = baseDf.from_parquet(path, time_col="time", freq=4.0)

        assert list(frame.columns) == ["c0", "c1"]
        assert np.allclose(frame.index, np.arange(20) / 4.0)

    def test_honours_an_explicit_value_cols(self, tmp_path):
        path = tmp_path / "wide.parquet"
        _wide().to_parquet(path, index=False)

        frame = baseDf.from_parquet(path, time_col="time", value_cols=["c1"])

        assert list(frame.columns) == ["c1"]

    def test_refuses_a_missing_time_column(self, tmp_path):
        path = tmp_path / "wide.parquet"
        _wide().to_parquet(path, index=False)

        with pytest.raises(ValidationError, match="nope"):
            baseDf.from_parquet(path, time_col="nope")
