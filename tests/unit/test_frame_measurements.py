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


def test_get_peak_freq_matches_the_lone_series():
    # "object" kind like get_peaks: a float at the default num_pks=1, a list
    # otherwise, so it cannot be forced into a numeric Series.
    frame = _frame()
    got = frame.get_peak_freq()
    assert isinstance(got, pd.Series)
    assert got.dtype == object
    assert got["c0"] == pytest.approx(frame["c0"].get_peak_freq())


def test_duration_is_a_frame_level_scalar():
    assert _frame().duration() == pytest.approx(_frame()["c0"].duration())


def test_measure_refuses_an_unknown_method():
    with pytest.raises(ValidationError, match="no_such_measure"):
        _frame().measure("no_such_measure")
