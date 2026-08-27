# Derived `freq` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop storing the sampling rate as a drifting attribute — derive it from the time index, and treat an explicit rate as a declaration that expires when the index it was made against changes.

**Architecture:** `freq` becomes a property on `TimeSeriesData`. A single private attribute `_freq_declaration = (value, token)` holds an explicitly supplied rate together with the index fingerprint it was declared against, where `token = (len(index), index[0], index[-1])` — deliberately the exact three values `_calculate_effective_frequency` reads. A matching token therefore *proves* that re-deriving now would return the same number, so honouring the declaration is safe; a mismatch re-derives. The property setter becomes the single validating door for rates entering the object.

**Tech Stack:** Python 3.8+, pandas ≥ 2.0.0, numpy, scipy, pytest.

**Spec:** `docs/superpowers/specs/2026-08-27-derived-freq-design.md` — read it before starting. It carries the reasoning, the seven breaking changes, and the adversarial-review findings this plan already incorporates.

## Global Constraints

- **pandas ≥ 2.0.0**, Python 3.8 target. CI runs pandas 2.3.3 on Python 3.9/3.10; local development is on pandas 3.0.5. Behaviour that differs across that matrix has broken this project twice (`objs`/`input_objs` in PR #25, `float(np.array([30.0]))` in PR #26). **Never merge on a green local interpreter alone.**
- **Line length:** aim for 100 characters (`pyproject.toml`).
- **Naming:** classes camelCase (`baseTs`, `TimeSeriesData`), functions/variables snake_case.
- **Type annotations** on all new function parameters and return values.
- **Docstrings** triple-quoted, with Args/Returns/Raises. This codebase's docstrings explain *why*, citing the failure the code prevents — match that register, do not write "Sets the frequency."
- **Never** use `git stash` to check whether something is pre-existing; use `git worktree add /tmp/baseline main`.
- Commits 1, 2 and 3 below must each be independently revertable. Do not combine them.

---

## Commit boundaries

| Commit | Tasks | Closes | Moves numbers? |
|---|---|---|---|
| 1 — property and validation | 1, 2, 3 | #29, #31 | No |
| 2 — `interpto_hz` grid | 4 | #23 | **Yes** |
| 3 — cleanup and docs | 5, 6 | — | No |

Commit 2 is the only one that changes values any method returns. Keeping it alone means a regression in resampled data bisects to one commit and reverts without losing the metadata fix.

---

## Task 1: Index token and derivation hardening

Pure addition plus one narrowing guard. Nothing depends on it yet, so the suite stays green.

**Files:**
- Modify: `baseTs/series.py` (add `_freq_token` near `normalise_history`, ~line 72; modify `_calculate_effective_frequency`, lines 229-239)
- Test: `tests/unit/test_series_freq.py` (create)

**Interfaces:**
- Consumes: nothing.
- Produces: `_freq_token(index) -> tuple` — module-level function in `baseTs/series.py`. Task 3 imports it for the property.
  `TimeSeriesData._calculate_effective_frequency(self) -> float` — unchanged signature, now returns `np.nan` instead of raising `TypeError` on a non-numeric index.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_series_freq.py`:

```python
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
    eagerly. Once derivation moves to read-time, an unguarded TypeError would
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
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
python -m pytest tests/unit/test_series_freq.py -v
```

Expected: collection error, `ImportError: cannot import name '_freq_token' from 'baseTs.series'`.

- [ ] **Step 3: Add `_freq_token` to `baseTs/series.py`**

Insert after `normalise_history` (after line 71, before `class _FinalizingWindow`):

```python
def _freq_token(index: Any) -> tuple:
    """Fingerprint an index for the purpose of sampling-rate derivation.

    Deliberately exactly the three values _calculate_effective_frequency
    reads - length, first timestamp, last timestamp - and nothing else. That
    is what makes the token trustworthy rather than merely convenient: two
    equal tokens guarantee that re-deriving the rate right now would return
    the number it returned when the token was taken, so a declaration stamped
    against it is as valid as it was on the day it was made.

    It follows that the token is blind to interior reordering. That is
    correct, not a gap - the derivation is blind to it too, and an index
    permutation that leaves length and endpoints alone leaves the mean rate
    alone. It does NOT mean the grid is still uniform; nothing in this class
    has ever claimed that.

    Args:
        index: Any pandas Index or sequence supporting len() and [] access

    Returns:
        A tuple safe to compare with ==; (0,) for an empty index
    """
    n = len(index)
    if n == 0:
        return (0,)
    return (n, index[0], index[-1])
```

- [ ] **Step 4: Harden `_calculate_effective_frequency`**

Replace lines 229-239 of `baseTs/series.py`:

```python
    def _calculate_effective_frequency(self) -> float:
        """Derive the sampling frequency from the time index.

        Returns NaN rather than raising for any index this cannot measure -
        too short, zero or negative duration, or a non-numeric dtype. NaN is
        the value the consumption guards (validate_sampling_freq and friends)
        are built to reject with a message naming the degenerate time base;
        a raw TypeError escaping from here would name the subtraction
        instead, some distance from the mistake.

        The TypeError arm specifically covers a DatetimeIndex, where
        index[-1] - index[0] is a Timedelta and float() refuses it.

        Returns:
            Samples per unit time, or NaN when the index cannot support a rate
        """
        if len(self.index) < 2:
            return np.nan
        try:
            duration = float(self.index[-1] - self.index[0])
        except (TypeError, ValueError):
            return np.nan
        if duration <= 0:
            return np.nan
        # n samples span n-1 intervals. Using len(self) here over-reported the
        # rate by n/(n-1) - 11% at n=10, 25% at n=5 - for every series built
        # from a times array without an explicit freq.
        return (len(self) - 1) / duration
```

- [ ] **Step 5: Run the new tests and the full suite**

```bash
python -m pytest tests/unit/test_series_freq.py -v
python -m pytest -q
```

Expected: new file all PASS; full suite PASS with no new failures.

- [ ] **Step 6: Commit**

```bash
git add baseTs/series.py tests/unit/test_series_freq.py
git commit -m "Add the index token, and derive NaN rather than raising on a non-numeric index

The token is exactly the three values _calculate_effective_frequency reads,
so token equality proves re-derivation would return the same number.

A DatetimeIndex made float(index[-1] - index[0]) raise TypeError. That fired
at the constructor while derivation was eager; once it moves to read-time an
unguarded raise would surface from .freq or __repr__ instead. Refs #29, #31."
```

---

## Task 2: Make the legacy freq tests independent of freq storage

Three existing tests reach their subject by writing a bad rate onto a constructed object. Task 3's validating setter makes all three raise at the assignment. Rewriting them **first** — in a form that passes both before and after — keeps Task 3's atomic switch from also being a test rewrite, and proves the rewrites do not depend on the change they precede.

**Files:**
- Modify: `tests/unit/test_core.py:711-738` (`TestNanFreqIsNotLaundered`)
- Modify: `tests/unit/test_utils.py:457-473` (`test_get_peaks_still_accepts_nonpositive_freq`)
- Modify: `tests/unit/test_utils.py:490-505` (`test_get_peaks_rejects_nonfinite_numpy_scalars`)

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: `_FreqStub` — a local test helper in `tests/unit/test_utils.py` exposing `.data` and `.freq`, which is the entire interface `get_peaks` requires (`baseTs/utils.py:547-551`).

- [ ] **Step 1: Rewrite `TestNanFreqIsNotLaundered` in `tests/unit/test_core.py`**

Replace lines 711-738 entirely:

```python
class TestNanFreqIsNotLaundered:
    """A NaN rate must not become a fabricated healthy number.

    Reaches a NaN rate through a degenerate time base rather than by
    assigning one. Assignment is no longer a route: the freq setter validates,
    so a NaN can only enter by being derived. A zero-duration index is the
    only remaining way in, which makes it the honest subject for this test.
    """

    @staticmethod
    def _nan_freq():
        return baseTs(np.sin(np.arange(200) / 10.0), np.zeros(200))

    def test_derivation_paths_agree(self):
        ts = self._nan_freq()
        assert np.isnan(ts.zscale().freq)
        assert np.isnan(ts.iloc[:100].freq)

    def test_guard_still_fires_after_derivation(self):
        with pytest.raises(ValueError, match="Invalid sampling frequency"):
            self._nan_freq().zscale().get_frequency_content()

    def test_explicit_freq_still_honoured(self):
        """A real declared rate must survive an index-preserving transform."""
        ts = baseTs(np.sin(np.arange(200) / 10.0), np.arange(200) / 10.0, freq=999.0)
        assert ts.zscale().freq == 999.0
```

- [ ] **Step 2: Rewrite both `get_peaks` tests in `tests/unit/test_utils.py`**

Replace `test_get_peaks_still_accepts_nonpositive_freq` (lines 457-473):

```python
class _FreqStub:
    """The whole interface get_peaks needs: .data and .freq.

    Used where the point is get_peaks' own tolerance of a rate, not baseTs'
    willingness to hold one. baseTs now rejects freq <= 0 at construction, so
    routing these cases through the constructor would test the constructor.
    """

    def __init__(self, data, freq):
        self.data = data
        self.freq = freq


@pytest.mark.parametrize("freq", [0.0, -1.0])
def test_get_peaks_ignores_nonpositive_freq(freq):
    """freq <= 0 provably never influenced the result and still must not.

    int(min_dist_secs * 0.0) is 0 and the max(25, ...) floor absorbs it. This
    guards get_peaks' deliberately-narrow guard: it rejects only non-finite
    rates, not non-positive ones, and must stay narrower than
    validate_sampling_freq.

    Previously constructed a baseTs with freq=0.0. baseTs now refuses that at
    construction - the premise for tolerating such objects was that
    interpto_hz(0) minted them, and interpto_hz(0) now raises. The subject
    here was always get_peaks' arithmetic, so it tests that directly.
    """
    from baseTs.utils import get_peaks

    sig = np.zeros(300)
    sig[[50, 150, 250]] = 5.0

    assert get_peaks(_FreqStub(sig, freq)) == [50, 150, 250]
```

Replace the body of `test_get_peaks_rejects_nonfinite_numpy_scalars` (lines 499-505) so it no longer assigns onto a `baseTs`:

```python
    from baseTs.utils import get_peaks

    sig = np.sin(np.arange(200) / 10.0)
    for bad in (dtype(np.nan), dtype(np.inf)):
        with pytest.raises(ValueError, match="Invalid sampling frequency"):
            get_peaks(_FreqStub(sig, bad))
```

Leave that test's existing docstring untouched — it still describes exactly why numpy scalar dtypes are the subject.

- [ ] **Step 3: Run both files and confirm they pass on unmodified library code**

```bash
python -m pytest tests/unit/test_core.py::TestNanFreqIsNotLaundered tests/unit/test_utils.py -v
```

Expected: all PASS. This is the point of the task — the rewrites must be green *before* Task 3, proving they test the intended subject rather than the change.

- [ ] **Step 4: Confirm the rewrites still pin something**

Temporarily edit `baseTs/utils.py` `get_peaks`, replacing its narrow non-finite check with a full `validate_sampling_freq(ts.freq)` call. Run:

```bash
python -m pytest tests/unit/test_utils.py::test_get_peaks_ignores_nonpositive_freq -v
```

Expected: FAIL. Then `git checkout baseTs/utils.py` to revert. This repo has shipped tests that passed with the guard they protected deleted — do not skip this step.

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_core.py tests/unit/test_utils.py
git commit -m "Test freq guards through reachable states, not planted ones

Three tests reached their subject by writing a bad rate onto a constructed
object. The validating setter in the next commit makes that raise, so they
move to routes that will still exist: a degenerate time base for NaN, and a
direct stub for get_peaks' own tolerance of a non-positive rate.

Green before and after the change they precede. Refs #31."
```

---

## Task 3: The atomic switch — `freq` becomes a property

**This task is atomic.** The suite is red between its edits and that is expected: the property's validating setter makes every remaining `self.freq = <derived NaN>` raise, so the property and all five write sites must land together. Do not commit partway.

**Files:**
- Modify: `baseTs/series.py` — imports (line 15), `_metadata` (147-152), `__init__` (180-184), `_initialize_default_metadata` (193-207), and add the property after `_calculate_effective_frequency`
- Modify: `baseTs/core.py` — `__init__` (242-244), `times` setter (285-290), `_create_new_with_data` (340-391), `filter_outliers` (1189, 1199)
- Test: `tests/unit/test_series_freq.py` (extend)

**Interfaces:**
- Consumes: `_freq_token(index) -> tuple` and the hardened `_calculate_effective_frequency` from Task 1.
- Produces: `TimeSeriesData.freq` — a property returning `float`; its setter accepts a positive finite real or `None` (which clears the declaration) and raises `ValueError` otherwise. `TimeSeriesData._freq_declaration` — `None`, or `(float, tuple)`; listed in `_metadata` so every pandas operation propagates it.

- [ ] **Step 1: Write the failing acceptance tests**

Append to `tests/unit/test_series_freq.py`:

```python
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
        NaN as unset, while assignment rejects it.
        """
        ts = baseTs(np.sin(np.arange(100) / 10.0), np.arange(100) / 10.0, freq=np.nan)
        assert ts.freq == pytest.approx(10.0)

    def test_metadata_no_longer_carries_the_raw_rate(self):
        assert 'freq' not in TimeSeriesData._metadata
        assert '_freq_declaration' in TimeSeriesData._metadata
```

- [ ] **Step 2: Run them to verify they fail**

```bash
python -m pytest tests/unit/test_series_freq.py -v
```

Expected: `TestDerivationPathsAgree::test_decimation_re_derives` FAILS (returns 10.0, wants 5.0); `test_sort_values_re_derives_to_nan` FAILS; every `TestValidationAtProductionSites` case FAILS (no exception raised); `test_metadata_no_longer_carries_the_raw_rate` FAILS.

- [ ] **Step 3: Import the validator into `baseTs/series.py`**

At line 15, alongside the existing `LowessOutlierFilter` import (`baseTs/utils.py` imports nothing from this package, so there is no cycle):

```python
from .LowessOutlierFilter import LowessOutlierFilter
from .utils import validate_sampling_freq
```

- [ ] **Step 4: Swap the `_metadata` entry**

In `baseTs/series.py`, change `'freq'` to `'_freq_declaration'` in the `_metadata` list (line 148) and add a note to the comment block above it:

```python
    # Every attribute pandas should carry across an operation. Anything missing
    # here is silently dropped by slicing, rolling, dropna, etc.
    #
    # 'filtered_indices' used to be listed here but was only ever initialised to
    # None and never written by anything - a half-finished rename. The attribute
    # that actually holds outlier positions is 'outlier_indices', which was
    # absent, so `ts.iloc[:50].outlier_indices` raised AttributeError.
    #
    # '_freq_declaration' replaces 'freq'. What propagates is the declaration
    # plus the index token it was made against, not the rate - so pandas'
    # __finalize__ copying it verbatim is now correct, because the child
    # re-validates it against its own index. Listing the property here instead
    # would be actively wrong: __finalize__ copies with object.__setattr__,
    # which honours data descriptors, so every propagation would run the
    # validating setter.
    _metadata = [
        '_freq_declaration', 'signal_name', 'history', 'is_filtered',
        'is_interpolated', 'is_uniform_grid', 'ts_offset',
        'has_timestamp_offset', 'outlier_indices', 'lowess_fit',
        'last_process', 'is_outlier_filtered', 'outlier_filter',
    ]
```

- [ ] **Step 5: Add the property to `TimeSeriesData`**

Insert immediately after `_calculate_effective_frequency` in `baseTs/series.py`:

```python
    @property
    def freq(self) -> float:
        """The sampling rate in Hz, derived from the index unless declared.

        An explicitly supplied rate is honoured only while the index still
        matches the token it was declared against - see _freq_token. This is
        what makes every derivation path agree: __finalize__, copy() and
        _create_new_with_data all just carry the declaration, and this one
        property decides whether it still applies.

        Returns:
            The declared rate when its token still matches, otherwise the
            rate derived from the current index (NaN if it cannot support one)
        """
        declaration = getattr(self, '_freq_declaration', None)
        if declaration is not None:
            try:
                if declaration[1] == _freq_token(self.index):
                    return declaration[0]
            except Exception:
                # Any failure to build or compare a token - an exotic index
                # dtype, an object array - falls through to re-deriving.
                # Failing toward derivation is the safe direction: it is what
                # the index actually supports.
                pass
        return self._calculate_effective_frequency()

    @freq.setter
    def freq(self, value: Any) -> None:
        """Declare an explicit sampling rate against the current index.

        The single validating door for a rate entering the object. Issue #31
        is that there was no such door: `freq=` reached __init__ unchecked and
        __finalize__ copied it onward, so a bad rate was reported some
        distance from the mistake, with a diagnosis that could be flatly
        wrong - a NaN blamed the timestamps when the constructor kwarg was
        the problem.

        Args:
            value: A positive finite rate, or None to clear the declaration
                and return the object to deriving from its index

        Raises:
            ValueError: If value is not a positive, finite real scalar
        """
        if value is None:
            self._freq_declaration = None
            return
        self._freq_declaration = (validate_sampling_freq(value),
                                  _freq_token(self.index))
```

- [ ] **Step 6: Update `TimeSeriesData.__init__` and `_initialize_default_metadata`**

In `_initialize_default_metadata` (line 193), replace nothing but add the declaration default alongside the others:

```python
        self.is_outlier_filtered = False
        self.outlier_filter = LowessOutlierFilter()
        # _metadata declares this; test_type_preservation.py asserts every
        # declared name exists on a constructed object.
        self._freq_declaration = None
```

In `TimeSeriesData.__init__`, replace lines 180-184:

```python
        # Declare the rate only when one was supplied. With no declaration the
        # `freq` property derives from the index on read, so there is nothing
        # to store - the `else` branch that used to derive into an attribute
        # here was the first of the two places that made freq a value able to
        # drift from the index it described.
        if freq is not None:
            self.freq = freq
```

- [ ] **Step 7: Delete the second derive-into-storage branch in `baseTs/core.py`**

Remove lines 242-244 entirely:

```python
        # Calculate frequency if not provided
        if _is_unset(freq):
            self.freq = self._calculate_effective_frequency()
```

This one is load-bearing, not tidying: left in place it routes a degenerate index's derived NaN straight through the validating setter, so `baseTs(data, np.zeros(200))` would raise at construction — breaking Task 2's rewritten `TestNanFreqIsNotLaundered` and contradicting the design's own "a degenerate index derives NaN rather than raising".

- [ ] **Step 8: Validate the rate before building an index from it**

In `baseTs/core.py`, replace lines 196-201:

```python
        # Handle times array - create if not provided
        if times is None:
            if not _is_unset(freq):
                # Validated before use, not after: this builds the index FROM
                # the rate, so freq=0 produced times [nan, inf, inf, ...],
                # freq=-10 ran the index backwards, and freq=inf collapsed it
                # to all-zeros - each of them a silently degenerate object
                # whose real complaint surfaced much later.
                freq = validate_sampling_freq(freq)
                times = np.arange(0, len(data)) / freq
            else:
                raise ValueError("You must provide either a times array or a frequency")
```

- [ ] **Step 9: Simplify `_create_new_with_data`**

In `baseTs/core.py`, replace lines 340-391:

```python
        if new_times is None:
            new_times = self.times

        # No freq handling here any more. The `freq` property derives from the
        # index, and an explicit declaration travels as _freq_declaration in
        # the metadata copy below - where the property re-validates it against
        # this object's own index. The index_unchanged test and the
        # post-construction re-assert that used to live here were a second
        # implementation of the "did the index change?" rule, which is
        # precisely how it came to disagree with __finalize__ (#29).
        new_kwargs = {'signal_name': self.signal_name}
        new_kwargs.update(kwargs)

        new_obj = baseTs(new_data, new_times, **new_kwargs)

        if preserve_metadata:
            # Copy metadata
            metadata_attrs = ['is_filtered', 'is_interpolated', 'is_uniform_grid',
                            'is_outlier_filtered', 'has_timestamp_offset', 'ts_offset',
                            'outlier_indices', 'lowess_fit', 'last_process',
                            'outlier_filter']

            # Not iterating self._metadata: this list is deliberately curated
            # and excludes history and signal_name, which are handled above and
            # below. _freq_declaration must be added by name, and is skipped
            # when the caller declared a rate explicitly - otherwise this copy
            # would silently overwrite their kwarg with the parent's.
            if 'freq' not in kwargs:
                metadata_attrs.append('_freq_declaration')

            for attr in metadata_attrs:
                if hasattr(self, attr):
                    setattr(new_obj, attr, getattr(self, attr))

            # Copy history (make a copy to avoid reference issues). Shares one
            # normaliser with __finalize__: every non-inplace method routes
            # through here, so a history that arrived as None would otherwise
            # die on .copy() before reaching any of the guarded append paths,
            # and a bare list() would explode a str into characters.
            new_obj.history = normalise_history(self.history)

        return new_obj
```

- [ ] **Step 10: Simplify the `times` setter**

In `baseTs/core.py`, replace lines 285-290:

```python
    @times.setter
    def times(self, value: np.ndarray):
        """Set the time values (backward compatibility)."""
        self.index = pd.Index(value)
        # No freq recalculation. The property derives from the index, so a new
        # index re-derives on the next read - and any declaration made against
        # the old index stops matching its token, which is the correct
        # outcome rather than a side effect to remember to trigger here.
```

- [ ] **Step 11: Remove the two `filter_outliers` rate assignments**

In `baseTs/core.py`, delete line 1189 (`self.freq = filt.freq`) and line 1199 (`newTs.freq = filt.freq`). Both sit inside `filter_outliers`, which assigns `.data` and `.times` immediately above each one; the property derives from the new index, making the assignment redundant — and a hazard, since `filt.freq` can be NaN and the setter now rejects it.

- [ ] **Step 12: Run the full suite**

```bash
python -m pytest -q
```

Expected: PASS. If `test_type_preservation.py::test_declared_metadata_is_actually_reachable` fails, Step 6's `_freq_declaration = None` default is missing.

- [ ] **Step 13: Verify against a real baseline, not memory**

```bash
git worktree add /tmp/basets-baseline main
python - <<'PY'
import subprocess, sys
snippet = (
    "import numpy as np; from baseTs import baseTs; "
    "ts = baseTs(np.sin(np.arange(100)/10.0), np.arange(100)/10.0); "
    "print(ts.iloc[::2].freq, ts.sort_values().freq)"
)
for label, cwd in (("baseline", "/tmp/basets-baseline"), ("HEAD", ".")):
    out = subprocess.run([sys.executable, "-c", snippet], cwd=cwd,
                         capture_output=True, text=True)
    print(label, out.stdout.strip() or out.stderr.strip()[-200:])
PY
git worktree remove /tmp/basets-baseline
```

Expected: baseline prints `10.0 10.0`; HEAD prints `5.0 nan`.

- [ ] **Step 14: Confirm the acceptance tests actually pin the fix**

Temporarily revert Step 9's `_freq_declaration` append (delete the two lines adding it to `metadata_attrs`) and run:

```bash
python -m pytest tests/unit/test_series_freq.py::TestDeclarationLifecycle -v
```

Expected: `test_declaration_survives_index_preserving_ops[<lambda>0]` (the `zscale` case) FAILS. Restore the lines and re-run to confirm PASS. This repo has shipped tests that passed with their subject deleted; do not skip.

- [ ] **Step 15: Commit**

```bash
git add baseTs/series.py baseTs/core.py tests/unit/test_series_freq.py
git commit -m "Derive freq from the index instead of storing it (#29, #31)

freq becomes a property. An explicit rate is a declaration stamped with the
(len, index[0], index[-1]) token it was made against - exactly the inputs the
derivation reads - so a matching token proves re-deriving would return the
same number, and a mismatch re-derives. __finalize__ is untouched: what it
copies is now a declaration the child re-validates against its own index.

The setter becomes the single validating door, which is #31. Three
production sites now refuse a bad rate: assignment, the freq= kwarg, and the
no-times path that builds the index FROM the rate (freq=0 gave times
[nan, inf, inf, ...]; freq=-10 ran the index backwards).

Deletes the second implementation of the did-the-index-change rule in
_create_new_with_data, the manual re-derivation in the times setter, and two
redundant rate assignments in filter_outliers.

Breaking: a declared rate expires when the index changes; assigning an
invalid rate raises; a DatetimeIndex series now constructs with freq NaN;
_metadata no longer contains 'freq'.

Closes #29. Closes #31."
```

---

## Task 4: Fix the `interpto_hz` grid

**This is the only task that changes numbers any method returns.** Its own commit.

**Files:**
- Modify: `baseTs/core.py:566-607` (`interpto_hz`)
- Test: `tests/unit/test_series_freq.py` (extend)

**Interfaces:**
- Consumes: `TimeSeriesData.freq` setter from Task 3.
- Produces: `baseTs.interpto_hz(new_freq, kind='linear', inplace=False) -> baseTs` — same signature; now raises `ValueError` for an invalid `new_freq` or a source that cannot be resampled.

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_series_freq.py`:

```python
class TestInterpToHzGrid:
    """The produced grid must actually have the rate it reports.

    linspace(t0, t1, int(duration * new_freq)) puts N points across the full
    duration, so the spacing is duration/(N-1) and the real rate falls short
    by (N-1)/N: interpto_hz(5) measured 4.984985 while reporting 5.
    """

    @pytest.fixture
    def ts(self):
        return baseTs(np.sin(np.arange(1000) / 10.0), np.arange(1000) / 10.0)

    @pytest.mark.parametrize("rate", [3, 5, 7, 20, 100])
    def test_grid_spacing_is_exact(self, ts, rate):
        r = ts.interpto_hz(rate)
        spacing = np.diff(r.times)
        assert spacing == pytest.approx(1.0 / rate)

    @pytest.mark.parametrize("rate", [3, 5, 7, 20, 100])
    def test_reported_rate_matches_the_grid(self, ts, rate):
        r = ts.interpto_hz(rate)
        derived = (len(r) - 1) / float(r.times[-1] - r.times[0])
        assert r.freq == pytest.approx(rate)
        assert derived == pytest.approx(rate)

    def test_same_rate_round_trip_keeps_every_sample(self):
        """Regression: a bare floor() drops a trailing sample.

        (np.arange(1000)/30.0) spans 998.9999999999999 * 30, not 999.0, so
        floor(duration * new_freq) + 1 gives 999 - one sample lost to float
        representation, nothing to do with the grid correction.
        """
        ts = baseTs(np.sin(np.arange(1000) / 10.0), np.arange(1000) / 30.0)
        assert len(ts.interpto_hz(30)) == 1000

    def test_grid_never_exceeds_the_source_range(self, ts):
        for rate in (3, 5, 7, 20, 100):
            r = ts.interpto_hz(rate)
            assert r.times[-1] <= ts.times[-1] + 1e-9
            assert r.times[0] == pytest.approx(ts.times[0])

    def test_declaration_expires_like_any_other(self, ts):
        assert ts.interpto_hz(5).iloc[::2].freq == pytest.approx(2.5)


class TestInterpToHzRejections:
    """Issue #31's sharpest production site: the one place a user hands
    baseTs a rate directly."""

    @pytest.fixture
    def ts(self):
        return baseTs(np.sin(np.arange(1000) / 10.0), np.arange(1000) / 10.0)

    @pytest.mark.parametrize("bad", [0, -1, np.inf, np.nan, '30', True])
    def test_rejects_an_invalid_rate(self, ts, bad):
        with pytest.raises(ValueError, match="Invalid sampling frequency"):
            ts.interpto_hz(bad)

    def test_rejects_a_degenerate_source(self):
        """Previously returned a length-0 series stamped with the rate.

        deg.interpto_hz(5) gave (0, 5) - a healthy-looking rate on an empty
        result, silently.
        """
        deg = baseTs(np.sin(np.arange(300) / 10.0), np.zeros(300))
        with pytest.raises(ValueError, match="degenerate|duration"):
            deg.interpto_hz(5)

    def test_rejects_a_rate_too_low_to_produce_a_series(self, ts):
        with pytest.raises(ValueError, match="at least two samples"):
            ts.interpto_hz(0.001)
```

- [ ] **Step 2: Run them to verify they fail**

```bash
python -m pytest tests/unit/test_series_freq.py::TestInterpToHzGrid tests/unit/test_series_freq.py::TestInterpToHzRejections -v
```

Expected: `test_grid_spacing_is_exact` FAILS (spacing is `duration/(N-1)`, not `1/rate`); `test_reported_rate_matches_the_grid` FAILS on `derived`; every rejection case FAILS with no exception (or a raw `TypeError` for `np.nan`).

- [ ] **Step 3: Rewrite `interpto_hz`**

Replace `baseTs/core.py:566-607`:

```python
    def interpto_hz(self, new_freq: float, kind: str = 'linear',
                    inplace: bool = False) -> "baseTs":
        """
        Resample onto a uniform grid at exactly new_freq.

        The grid is built from the rate rather than by subdividing the
        duration. np.linspace(t0, t1, int(duration * new_freq)) spreads N
        points across the whole span, so the spacing is duration/(N-1) and the
        real rate falls short by (N-1)/N - interpto_hz(5) produced a grid
        measuring 4.984985 Hz while reporting 5. Building from the rate makes
        the reported and produced rates the same number.

        Args:
            new_freq: The desired sampling rate in Hz. Must be positive and
                finite; it is validated here rather than at the point the
                result is consumed.
            kind: Interpolation type passed to scipy.interpolate.interp1d
            inplace: If True, modifies existing object. Otherwise returns a
                new object. Defaults to False.

        Returns:
            baseTs: Interpolated data on an exact new_freq grid

        Raises:
            ValueError: If new_freq is not a positive finite rate, if the
                source time base is degenerate, or if the requested rate is
                too low to produce at least two samples
        """
        new_freq = validate_sampling_freq(new_freq)

        # duration() is float(index[-1] - index[0]), which raises TypeError on
        # a non-numeric index (a DatetimeIndex yields a Timedelta). Caught so
        # this method keeps the ValueError contract its docstring promises
        # rather than leaking a conversion error from two frames down.
        try:
            duration = self.duration()
        except (TypeError, ValueError):
            duration = np.nan
        if not np.isfinite(duration) or duration <= 0:
            raise ValueError(
                f"Cannot interpolate to {new_freq} Hz: the source time base is "
                f"degenerate (duration {duration}). A zero, negative or "
                f"unmeasurable span has no rate to resample from, and stamping "
                f"the requested rate on the empty result would report a healthy "
                f"number for a series that has none."
            )

        # Rounded before flooring. The product lands just below the integer
        # for an exact-rate source - (np.arange(1000)/30.0) spans
        # 998.9999999999999 * 30, not 999.0 - so a bare floor silently drops
        # a trailing sample on a same-rate round trip. Nine places absorbs
        # representation error while leaving a genuine fractional product
        # (998.9999 from real data) to floor as it should.
        n_samples = int(np.floor(np.round(duration * new_freq, 9))) + 1
        if n_samples < 2:
            raise ValueError(
                f"Cannot interpolate to {new_freq} Hz: a {duration}s series "
                f"yields {n_samples} sample(s), and at least two samples are "
                f"needed to carry a rate."
            )

        # Clipped defensively, not to fix an observed bug: n-1 <= duration *
        # new_freq holds by construction, so the last point cannot exceed t1
        # mathematically, and a 200,000-case sweep across rates, lengths and
        # offsets found no overshoot. But np.round above can nudge the product
        # up past its true value, and interp1d rejects anything above its
        # range outright - a one-line clamp against a hard error that would
        # only ever appear on a user's data.
        new_times = self.times[0] + np.arange(n_samples) / new_freq
        new_times[-1] = min(new_times[-1], self.times[-1])

        interpolator = interpolate.interp1d(self.times, self.data, kind=kind)
        new_data = interpolator(new_times)

        if inplace:
            target = self
        else:
            target = self.copy()

        target.data = new_data
        target.times = new_times
        # Declared, not left to derive. After the grid fix the derived rate is
        # correct, but it round-trips through floating point -
        # (n-1) / ((n-1)/f) is not bit-exact f - so .freq could read
        # 99.99999999999999. The declaration is now true rather than the
        # (N-1)/N overstatement it used to be, and it expires on an index
        # change like any other.
        target.freq = new_freq
        target.is_interpolated = True
        target.is_uniform_grid = True

        target._update_history_and_process(
            hist_msg=f"Interpolated to {new_freq}Hz",
            last_process=f"_interpto_{new_freq}Hz"
        )
        return target
```

- [ ] **Step 4: Run the new tests, then the full suite**

```bash
python -m pytest tests/unit/test_series_freq.py -v
python -m pytest -q
```

Expected: new tests PASS, and exactly one existing test fails —
`tests/unit/test_core.py:83`, `test_interpolation_to_frequency`. Its fixture is
`np.linspace(0, 10, 1000)`, a duration of exactly 10.0 s, so at 200 Hz the old
`int(duration * new_freq)` gave 2000 points and the new
`floor(round(duration * new_freq, 9)) + 1` gives **2001**. Update the assertion
and its comment:

```python
        # Duration is 10 seconds at exactly 200 Hz: 2000 intervals, 2001 samples.
        # Was 2000 before the grid fix, when the points were spread across the
        # span and the real rate was 199.9 Hz.
        assert len(ts_interp.data) == 2001
```

`assert ts_interp.freq == new_freq` on the next line still passes. If any
*other* test fails, read it before touching it: if it asserts a downstream
numeric result rather than a length, confirm the new value is correct rather
than pasting in whatever the code now prints.

- [ ] **Step 5: Measure the change to the output, and record it**

```bash
python - <<'PY'
import numpy as np
from baseTs import baseTs
ts = baseTs(np.sin(np.arange(1000) / 10.0), np.arange(1000) / 10.0)
for rate in (3, 5, 7, 20, 100):
    r = ts.interpto_hz(rate)
    derived = (len(r) - 1) / float(r.times[-1] - r.times[0])
    print(f"{rate:>4} Hz -> n={len(r):>5}  derived={derived:.9f}  last={r.times[-1]:.6f}")
PY
```

Paste the output into the commit message. It is the evidence the grid now has the rate it claims.

- [ ] **Step 6: Commit**

```bash
git add baseTs/core.py tests/unit/test_series_freq.py
git commit -m "Build interpto_hz's grid at the requested rate (#23)

linspace(t0, t1, int(duration * new_freq)) spread N points across the whole
span, so spacing was duration/(N-1) and the real rate fell short by (N-1)/N:
interpto_hz(5) produced a 4.984985 Hz grid while reporting 5. Hidden because
the requested rate was stored verbatim.

Builds from the rate instead. Rounds before flooring - an exact-rate source
spans 998.9999999999999 * 30 rather than 999.0, so a bare floor drops a
trailing sample on a same-rate round trip; that case is pinned by a test.

Also validates new_freq, and rejects a degenerate source instead of
returning a length-0 series stamped with the requested rate.

Breaking: interpto_hz returns a different grid - one more sample, exact
spacing, and a final timestamp that may fall short of the source's last.

Closes #23."
```

---

## Task 5: Remove the now-redundant `freq` plumbing

Pure tidying, verified by prototype to be optional: a NaN `self.freq` is absorbed by `_is_unset` before it reaches the setter, so these paths are already correct. Sequenced last so it carries no risk budget.

**Files:**
- Modify: `baseTs/series.py:388-410` (`to_basetseries`), `baseTs/series.py:570-590` (the arithmetic wrap)
- Modify: `baseTs/core.py:2190-2226` (`copy`)

**Interfaces:**
- Consumes: `TimeSeriesData._freq_declaration` from Task 3.
- Produces: no signature changes.

- [ ] **Step 1: Simplify `to_basetseries`**

In `baseTs/series.py`, drop the `freq=self.freq` kwarg and the special-case that compensates for it:

```python
        base_ts = baseTs(
            data=self.values,
            times=self.index.values,
            signal_name=self.signal_name
        )

        # Copy metadata. freq is no longer special-cased out: the rate is not
        # in _metadata any more, _freq_declaration is, and the constructed
        # object derives from an index identical to this one.
        for attr in self._metadata:
            if hasattr(self, attr) and attr != 'signal_name':
                setattr(base_ts, attr, getattr(self, attr))
```

- [ ] **Step 2: Simplify the arithmetic wrap**

In `baseTs/series.py`, in `_wrap_result_as_basets` (line 552), the constructor call already omits `freq`. Update only the copy loop and its comment:

```python
        # Copy relevant metadata. _freq_declaration rides along like any other
        # name: arithmetic between two operands on different time bases
        # produces a union index, whose token will not match the declaration,
        # so the result re-derives. The explicit freq exclusion this loop used
        # to carry is what the token now does properly.
        for attr in self._metadata:
            if hasattr(self, attr) and attr != 'signal_name':
                setattr(new_basets, attr, getattr(self, attr))
```

- [ ] **Step 3: Simplify `copy`**

In `baseTs/core.py`, remove `freq=self.freq` from both constructor calls (the `deep=True` branch at ~line 2193 and the shallow `isinstance` fallback at ~line 2222). Both already copy `_metadata` afterwards, which now carries `_freq_declaration`.

- [ ] **Step 4: Run the full suite**

```bash
python -m pytest -q
python -m pytest tests/unit/test_series_freq.py -v
```

Expected: PASS, with no change in behaviour. If anything fails here, the step was not tidying and needs re-examining rather than patching.

- [ ] **Step 5: Lint and type check**

```bash
flake8 baseTs/*.py
mypy baseTs/*.py
```

Expected: no new findings relative to `main`. Check against the baseline — this codebase does not start clean.

- [ ] **Step 6: Commit**

```bash
git add baseTs/series.py baseTs/core.py
git commit -m "Drop the freq plumbing the property made redundant

to_basetseries, the arithmetic wrap and both copy() branches passed
freq=self.freq into a constructor and then excluded 'freq' from their
metadata loops to compensate. The rate is no longer in _metadata and
_freq_declaration rides along like any other name.

No behaviour change - these paths were already correct, because a NaN
self.freq is absorbed by _is_unset before reaching the setter. Tidying only."
```

---

## Task 6: Documentation and changelog

**Files:**
- Modify: `docs/EXAMPLES.md:1064`, `docs/API.md`, `docs/API_SERIES.md`, `docs/USER_GUIDE.md`, `docs/CHANGELOG.md`

**Interfaces:**
- Consumes: the finished behaviour from Tasks 3-5.
- Produces: nothing code depends on.

- [ ] **Step 1: Find every place the docs describe `freq`**

```bash
grep -rn "freq" docs/*.md | grep -vi "min_freq\|max_freq\|low_freq\|high_freq\|get_peak_freq\|get_frequency_content" | less
```

Read each hit. The three claims that are now wrong: that `freq` is a stored attribute, that an explicitly set rate persists across operations, and `interpto_hz`'s grid and sample count.

- [ ] **Step 2: Fix `docs/EXAMPLES.md:1064`**

The line `ts.freq = sampling_rate` is still valid for a positive rate, but the surrounding text should say the declaration expires if the index later changes. Add one sentence rather than restructuring the example.

- [ ] **Step 3: Update the API docs**

In `docs/API.md` and `docs/API_SERIES.md`, replace whatever describes `freq` as an attribute with this, adapted to each file's formatting:

> **`freq`** *(property, float)* — the sampling rate in Hz. Derived from the
> time index unless you set one explicitly. An explicitly set rate is honoured
> only while the index still matches the one it was set against; any operation
> that changes the index (`iloc`, `sort_values`, `resample`, `dropna`) re-derives.
> Setting a non-positive, non-finite or non-numeric rate raises `ValueError`.
> Reads as `NaN` when the index cannot support a rate — fewer than two samples,
> a zero or negative span, or a non-numeric index such as a `DatetimeIndex`.

For `interpto_hz`, replace the description of its grid with:

> Resamples onto a grid with exactly `1/new_freq` spacing, starting at the
> source's first timestamp. The final sample may fall short of the source's
> last timestamp rather than landing on it. Raises `ValueError` if `new_freq`
> is not a positive finite rate, if the source time base is degenerate, or if
> the requested rate yields fewer than two samples.

- [ ] **Step 4: Write the changelog entry**

In `docs/CHANGELOG.md`, add all seven breaking changes verbatim from the spec's Consequences section, each with a one-line migration note. Numbers 1, 3 and 6 are the ones that will actually bite users:

1. A declared rate expires when the index changes.
2. Assigning an invalid rate raises `ValueError`.
3. `interpto_hz` returns a different grid.
4. `interpto_hz` raises on a degenerate source.
5. `TimeSeriesData._metadata` no longer contains `'freq'`.
6. `baseTs(data, times, freq=0.0)` and `freq=-1.0` raise at construction.
7. A `DatetimeIndex` series constructs instead of raising `TypeError`; `.freq` reads NaN.
8. Arithmetic preserves a declared rate when the result's index is unchanged, where it previously always re-derived. Found during implementation (Task 3 fix round 1) and added to the spec's Consequences section — see it for the full reasoning.

- [ ] **Step 5: Commit**

```bash
git add docs/
git commit -m "Document the derived freq property and its seven breaking changes

Refs #29, #31, #23."
```

---

## Before opening the PR

- [ ] **Run the full suite one more time:** `python -m pytest -q`
- [ ] **Verify on the oldest supported pandas.** The design was prototyped on pandas 3.0.5 only, and this project has twice shipped a change that was correct locally and broken on the CI matrix — `objs`/`input_objs` in PR #25, `float(np.array([30.0]))` in PR #26. Property descriptors on a `Series` subclass, `__finalize__` metadata copying and `_metadata` handling are all exactly the kind of internals that move between majors.

```bash
python -m venv /tmp/pandas2 && /tmp/pandas2/bin/pip install -q "pandas==2.3.3" numpy scipy matplotlib pytest
/tmp/pandas2/bin/python -m pytest -q
```

Expected: PASS. If it does not, that is a blocker, not a follow-up.

- [ ] **Check the CI matrix matches what was tested:** read `.github/workflows/python-package.yml` and confirm no leg installs a pandas or numpy version neither run above covered.
- [ ] **Wait for CI to go green before merging**, even if every review round says trivial.
- [ ] **Send the diff to the `consensus-review` agent** before merge, per the project's standing practice. Verify each finding against a `git worktree` baseline rather than `git stash` — the fixes are committed by then, so stash hides nothing.
