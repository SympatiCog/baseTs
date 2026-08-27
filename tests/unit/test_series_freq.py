# -*- coding: utf-8 -*-
"""Tests for the derived `freq` property and its index token."""

import numpy as np
import pandas as pd
import pytest

from baseTs import baseTs
from baseTs.series import TimeSeriesData, _freq_token


class TestFreqToken:
    """The token must be exactly the inputs _calculate_effective_frequency reads.

    That equivalence is the whole design: if the token matches, re-deriving
    would return the same number, so honouring a declaration made earlier is
    provably as valid as it was when made.
    """

    def test_token_is_length_first_last(self):
        idx = pd.Index(np.arange(100) / 10.0)
        assert _freq_token(idx) == (100, idx[0], idx[-1])

    def test_empty_index(self):
        assert _freq_token(pd.Index([])) == (0,)

    def test_single_sample(self):
        idx = pd.Index([2.5])
        assert _freq_token(idx) == (1, 2.5, 2.5)

    @pytest.mark.parametrize("op,label", [
        (lambda t: t[::2], "decimation changes length"),
        (lambda t: t[:50], "truncation changes length and last"),
        (lambda t: t[::-1], "reversal swaps first and last"),
    ])
    def test_index_changes_move_the_token(self, op, label):
        idx = pd.Index(np.arange(100) / 10.0)
        assert _freq_token(op(idx)) != _freq_token(idx), label

    def test_interior_permutation_does_not_move_the_token(self):
        """And must not: the derived rate is unchanged, so the token is right.

        _calculate_effective_frequency has always been (len-1)/(last-first),
        blind to interior order. The token is blind in exactly the same way,
        by construction - not by oversight.
        """
        idx = pd.Index(np.arange(100) / 10.0)
        shuffled = pd.Index(np.concatenate([idx[:1], idx[1:-1][::-1], idx[-1:]]))
        assert _freq_token(shuffled) == _freq_token(idx)


class TestDerivationHardening:
    """A non-numeric index must derive NaN, not raise.

    float(index[-1] - index[0]) raises TypeError on a DatetimeIndex
    ("not 'Timedelta'"). Today that fires at the constructor, which derives
    eagerly. Once derivation moves to read-time an unguarded TypeError would
    surface from .freq, info(), __repr__ or any spectral call - which is
    exactly issue #31's complaint, "the error lands three calls away from the
    mistake", reintroduced by the fix for it.
    """

    def test_datetime_index_constructs_and_derives_nan(self):
        ts = baseTs(np.arange(10.0), pd.date_range('2020-01-01', periods=10, freq='s'))
        assert np.isnan(ts.freq)

    def test_datetime_index_reaches_the_consumption_guard(self):
        ts = baseTs(np.arange(64.0), pd.date_range('2020-01-01', periods=64, freq='s'))
        with pytest.raises(ValueError, match="Invalid sampling frequency"):
            ts.get_frequency_content()

    def test_numeric_index_still_derives(self):
        ts = baseTs(np.sin(np.arange(100) / 10.0), np.arange(100) / 10.0)
        assert ts.freq == 10.0

    def test_degenerate_index_still_derives_nan(self):
        assert np.isnan(baseTs(np.arange(200.0), np.zeros(200)).freq)
