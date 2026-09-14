"""Correlating a frame: one seed against every column, or frame against frame."""
import warnings

import numpy as np
import pandas as pd
import pytest

from baseTs import baseTs
from baseTs.frame import baseDf
from baseTs.utils import ValidationError

N = 200
TIMES = np.arange(N) / 10.0


def _left() -> baseDf:
    rng = np.random.default_rng(0)
    data = {f"l{i}": rng.normal(size=N) + np.sin(2 * np.pi * 0.1 * TIMES) * i
            for i in range(4)}
    data["l2"][5] = np.nan
    return baseDf(pd.DataFrame(data, index=TIMES), freq=10.0)


def _right() -> baseDf:
    rng = np.random.default_rng(1)
    data = {f"r{j}": rng.normal(size=N) + np.cos(2 * np.pi * 0.1 * TIMES) * j
            for j in range(3)}
    return baseDf(pd.DataFrame(data, index=TIMES), freq=10.0)


def _seed() -> baseTs:
    rng = np.random.default_rng(2)
    return baseTs(data=rng.normal(size=N), times=TIMES.copy(), freq=10.0,
                  signal_name="behaviour")


def test_a_seed_gives_one_value_per_column():
    got = _left().correlation_with(_seed())
    assert isinstance(got, pd.Series)
    assert list(got.index) == ["l0", "l1", "l2", "l3"]
    assert got.dtype.kind == "f"


def test_the_seed_result_equals_the_per_column_baseTs_call():
    frame, seed = _left(), _seed()
    got = frame.correlation_with(seed)
    for label in frame.columns:
        assert got[label] == pytest.approx(
            frame[label].correlation_with(seed), nan_ok=True)


@pytest.mark.parametrize("method", ["pearson", "spearman", "kendall"])
def test_the_matrix_equals_the_per_pair_calls(method):
    warnings.filterwarnings("ignore")
    left, right = _left(), _right()
    got = left.correlation_matrix(right, method=method)
    assert got.shape == (4, 3)
    for lc in left.columns:
        for rc in right.columns:
            assert got.at[lc, rc] == pytest.approx(
                left[lc].correlation_with(right[rc], method=method), nan_ok=True)


def test_the_matrix_against_itself_is_square_and_symmetric():
    got = _left().correlation_matrix()
    assert got.shape == (4, 4)
    assert np.allclose(np.diag(got.to_numpy()), 1.0)
    assert np.allclose(got.to_numpy(), got.to_numpy().T, equal_nan=True)


def test_a_frame_passed_to_correlation_with_is_refused():
    with pytest.raises(ValidationError, match="correlation_matrix"):
        _left().correlation_with(_right())


def test_a_series_passed_to_correlation_matrix_is_refused():
    with pytest.raises(ValidationError, match="correlation_with"):
        _left().correlation_matrix(_seed())


def test_frames_sharing_no_timepoints_are_refused():
    other = _right()
    other._df.index = pd.Index(np.asarray(other._df.index) + 10_000.0)
    with pytest.raises(ValidationError, match="no timepoints"):
        _left().correlation_matrix(other)
