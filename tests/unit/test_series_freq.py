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


class TestDerivationPathsAgree:
    """Issue #29's acceptance test.

    The same index change had two answers depending on which path built the
    object: _create_new_with_data re-derived, __finalize__ carried the
    parent's rate verbatim.
    """

    @pytest.fixture
    def ts(self):
        return baseTs(np.sin(np.arange(100) / 10.0), np.arange(100) / 10.0)

    def test_decimation_re_derives(self, ts):
        assert ts.iloc[::2].freq == pytest.approx(5.0)

    def test_sort_values_re_derives_to_nan(self, ts):
        """A value-sorted series has a non-monotonic index and no honest rate.

        The carried rate was finite, so relative_band_power returned a
        confident number against the wrong Nyquist instead of raising.
        """
        assert np.isnan(ts.sort_values().freq)

    def test_both_paths_give_the_same_answer(self, ts):
        assert ts.iloc[:51].freq == pytest.approx(ts.trimto_timepoints(0, 5).freq)

    def test_index_preserving_ops_keep_the_rate(self, ts):
        assert ts.zscale().freq == pytest.approx(10.0)
        assert (ts * 2).freq == pytest.approx(10.0)
        assert ts.rolling(5).mean().freq == pytest.approx(10.0)


class TestDeclarationLifecycle:
    """An explicit rate is honoured until the index it describes changes."""

    @pytest.fixture
    def declared(self):
        return baseTs(np.sin(np.arange(100) / 10.0), np.arange(100) / 10.0, freq=999.0)

    def test_declaration_is_honoured(self, declared):
        assert declared.freq == 999.0

    @pytest.mark.parametrize("op", [
        lambda t: t.iloc[:50],
        lambda t: t.iloc[::2],
        lambda t: t.sort_values(),
    ])
    def test_declaration_expires_on_index_change(self, declared, op):
        assert op(declared).freq != 999.0

    @pytest.mark.parametrize("op", [
        lambda t: t.zscale(),
        lambda t: t * 2,
        lambda t: t.copy(),
        lambda t: t.copy(deep=True),
        lambda t: t.rolling(5).mean(),
    ])
    def test_declaration_survives_index_preserving_ops(self, declared, op):
        """Guards the _freq_declaration entry in _create_new_with_data's
        metadata_attrs list. Without that one-line addition, zscale() drops
        the declaration and nothing else in the suite notices."""
        assert op(declared).freq == 999.0

    def test_none_clears_the_declaration(self, declared):
        declared.freq = None
        assert declared.freq == pytest.approx(10.0)

    def test_reassignment_redeclares_against_the_current_index(self, declared):
        trimmed = declared.iloc[:50]
        trimmed.freq = 42.0
        assert trimmed.freq == 42.0
        assert trimmed.iloc[:25].freq != 42.0


class TestValidationAtProductionSites:
    """Issue #31: a bad rate must be refused where it enters the object."""

    BAD = [0.0, -1.0, np.inf, -np.inf, '30', True, np.bool_(True), b'30']

    @pytest.mark.parametrize("bad", BAD)
    def test_constructor_rejects(self, bad):
        with pytest.raises(ValueError, match="Invalid sampling frequency"):
            baseTs(np.sin(np.arange(100) / 10.0), np.arange(100) / 10.0, freq=bad)

    @pytest.mark.parametrize("bad", BAD)
    def test_assignment_rejects(self, bad):
        ts = baseTs(np.sin(np.arange(100) / 10.0), np.arange(100) / 10.0)
        with pytest.raises(ValueError, match="Invalid sampling frequency"):
            ts.freq = bad

    @pytest.mark.parametrize("bad", [0.0, -1.0, np.inf])
    def test_index_built_from_a_bad_rate_is_rejected(self, bad):
        """baseTs(data, freq=...) with no times builds the index FROM the rate.

        freq=0 produced times [nan, inf, inf, inf, inf]; freq=-10 ran the
        index backwards; freq=inf collapsed it to all-zeros. A third
        production site neither #29 nor #31 named.
        """
        with pytest.raises(ValueError, match="Invalid sampling frequency"):
            baseTs(np.ones(5), freq=bad)

    def test_nan_is_still_the_not_supplied_sentinel(self):
        """baseTs' public default is freq=np.nan, so it cannot mean "invalid".

        Deliberate asymmetry, documented in the spec: the constructor treats
        NaN as unset, while assignment rejects it. Both halves live in this
        one test so they are read together - the natural "fix" a future
        maintainer would reach for is making the setter treat NaN like None,
        exactly as the constructor does, and nothing else in the suite would
        catch that.
        """
        ts = baseTs(np.sin(np.arange(100) / 10.0), np.arange(100) / 10.0, freq=np.nan)
        assert ts.freq == pytest.approx(10.0)

        with pytest.raises(ValueError, match="Invalid sampling frequency"):
            ts.freq = np.nan

    def test_metadata_no_longer_carries_the_raw_rate(self):
        assert 'freq' not in TimeSeriesData._metadata
        assert '_freq_declaration' in TimeSeriesData._metadata


class TestInterptoHzRoutesThroughTheValidatingSetter:
    """interpto_hz was not one of this task's five write sites - it is
    Task 4's - but its `self.freq = freq` / `new_obj.freq = freq` now reach
    the same validating setter, so its public contract changed too:
    interpto_hz(0) used to hand back a degenerate object and now raises.

    Pinned here, separately from Task 4's own rewrite of this method, so
    Task 3 stands alone as an independently revertable commit with its own
    behaviour covered - and because Task 4 also raises for 0, this test
    survives that rewrite unchanged.
    """

    def test_interpto_hz_zero_raises(self):
        ts = baseTs(np.sin(np.arange(100) / 10.0), np.arange(100) / 10.0)
        with pytest.raises(ValueError, match="Invalid sampling frequency"):
            ts.interpto_hz(0)

    def test_interpto_hz_valid_rate_is_honoured(self):
        ts = baseTs(np.sin(np.arange(100) / 10.0), np.arange(100) / 10.0)
        assert ts.interpto_hz(50).freq == pytest.approx(50.0)
