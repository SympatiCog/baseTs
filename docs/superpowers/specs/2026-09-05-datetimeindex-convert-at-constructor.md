# Handoff: #100 — convert a DatetimeIndex to seconds at the constructor

Paste this into a fresh session as the opening prompt. It records what was
measured, the decision Stan took, the design, and the working rules this
repo's review arc has settled on. Memory files with the fuller history:
`~/.claude/projects/-Users-stan-python-baseTs/memory/basets-metadata-propagation-arc.md`
and `basets-adversarial-review-rounds.md`.

## The task

Implement GitHub issue #100 in `/Users/stan/python/baseTs`, branching from
`main` at `0cbffcb` (2026-09-05). Read the issue first: `gh issue view 100`.

**Decision (Stan, 2026-09-05): convert at the constructor.** A
`pd.DatetimeIndex` passed as `times`/`index` becomes a numeric index of
seconds since its first stamp, and that first stamp is recorded as the
timestamp offset. The package keeps one time base everywhere. The
alternatives were rejected: teaching each method both index kinds is the
"guard at consumption" pattern this arc keeps paying for (four sites now,
every future method forever); refusing at the constructor is one door but
throws away pandas conveniences that work today.

## What is true on `main` at 0cbffcb (all measured, pandas 3.0.1 / numpy 2.5.2)

```python
import numpy as np, pandas as pd
from baseTs import baseTs
s = baseTs(np.random.randn(365), times=pd.date_range('2023-01-01', periods=365, freq='D'))
s.freq              # nan   (_calculate_effective_frequency's TypeError arm, series.py ~1033-1060)
s.rolling_mean(7)   # fine  (pandas-native)
s.time_slice(start_time='2023-01-01', end_time='2023-01-31')   # fine (boolean mask on the index)
s.detect_outliers() # fine
s.duration()        # TypeError: float() argument ... not 'Timedelta'   (series.py ~1238: float(index[-1] - index[0]))
s.get_statistics()  # same, via duration()
s.resample('D')     # TypeError: dtype datetime64[us] cannot be converted to timedelta64[ns]  (core.py ~1901: pd.to_timedelta(self.index, unit='s'))
s.diff_ts()         # UFuncTypeError: ufunc 'multiply' ... dtype('O') and dtype('<m8[us]')
```

Every spectral method is then unusable without a declared `freq=`.

The design already models time as seconds plus an offset: `ts_offset`
("Timestamp offset in seconds") and `has_timestamp_offset` are in
`TimeSeriesData._metadata` (series.py ~820), defaulted in
`TimeSeriesData.__init__` (~971), copied by `_copy_metadata_from_basetseries`
(~1006), settable through `baseTs.__init__(ts_offset=...)` (core.py ~172,
~265-270: an explicit offset sets `has_timestamp_offset=True`) and
`from_df(ts_offset=...)`, shown in `__repr__`/summary (~1335) - and **nothing
computes from them**. This change gives the slot its meaning.

Where the index is built: `TimeSeriesData.__init__` (series.py ~889-935;
`pd.Index(...)` at ~908, ~922, ~933) and the `times` setter (core.py ~355-358,
`self.index = pd.Index(value)`). `_update_series_data` (core.py ~471-505) has
a comment about a DatetimeIndex keeping its dtype (~500).

`from_df` (core.py ~41) currently **rejects** a datetime time column
("Time column 't' must be numeric"); with conversion at the constructor it
can accept one, which is the more useful contract. Decide and document.

## Design

1. **One door.** In `TimeSeriesData.__init__` (and the `times` setter, which
   is the other way an index arrives), if the index is a `DatetimeIndex`:
   `seconds = (index - index[0]).total_seconds()` as float64, and
   `ts_offset = index[0]` expressed as **epoch seconds** (float; Stan's
   recommended semantics - it round-trips exactly), `has_timestamp_offset =
   True`. A `TimedeltaIndex` converts to `.total_seconds()` with no offset.
   Decide, document and pin what happens when the caller *also* passes
   `ts_offset=`: the explicit value should win, or the call should be refused
   as ambiguous - not silently summed.
2. **Timezone-aware index:** record the offset as UTC epoch seconds and keep
   the tz name nowhere, or refuse tz-aware with a message naming
   `tz_convert(None)`. Pick one, state it, pin it. (Naive local stamps: epoch
   seconds as if UTC; say so.)
3. **One accessor back:** e.g. a `datetimes` property (or
   `to_datetime_index()`) returning `pd.to_datetime(ts_offset + times,
   unit='s')` when `has_timestamp_offset` else raising with a clear message.
   This is what the pandas-style doc examples (`groupby(index.month)`,
   `df.index.dayofweek`) switch to.
4. **`time_slice` bounds:** accept a datetime-like or date string when
   `has_timestamp_offset`, converting through the offset; numeric seconds as
   now. A string against a series with no offset raises `TypeError` as now
   (`docs/API.md` documents this; update the sentence).
5. **`resample` on a converted series** works unchanged on the seconds
   index. The result should keep `ts_offset`/`has_timestamp_offset` (it
   derives via the constructor/`_create_new_with_data` - check which, and
   that the offset survives; `_create_new_with_data` has a hardcoded copy
   list separate from `_metadata`, see the #20 lesson in memory).
6. **Every derivation keeps the offset** - it is in `_metadata` already;
   pin it through `iloc`, arithmetic, `copy`, pickle round-trip, and the
   `_create_new_with_data` path.
7. **Breaking change, stated in the CHANGELOG:** `ts.index` is numeric for
   callers who passed dates, so `ts.index.month` and date-string bounds on
   the raw index stop working on the object; the accessor and `time_slice`
   are the replacements. Also state that `freq` now derives for such series.

Design doc convention: the three files beside this one in
`docs/superpowers/specs/` show the shape (problem, decision, alternatives,
mechanism, what changes, what is pinned). Write one before code if the
timezone/offset choices turn out to need more than a paragraph; run
`consensus-review` on the spec before coding (that caught seven things on
#40 before any code).

## Docs to update (they currently work around #100 and say so)

- `docs/API.md`: the constructor example builds `ts_series` from
  `pd.date_range(...)` (~line 64 block); the `time_slice` section's
  Parameters/Raises text about date strings vs seconds (~757-770); the
  `from_df` section says the time column must be numeric (~83-100).
- `docs/API_SERIES.md:~399` (pandas-integration block: "baseTs.resample()
  reads a numeric-seconds index and cannot take a DatetimeIndex yet (#100)").
- `docs/EXAMPLES.md:~103` (describe() instead of get_statistics()), `~392`
  (docstring: "timestamps ... in seconds ... see issue #100"), `~1644`
  (drops to pandas' resample on a plain Series).
- `docs/CHANGELOG.md`: new `[Unreleased]` entry at the **top** (above the
  #98 entry); the #69 entry's "Filed, not folded in - #100" paragraph should
  be annotated as answered, past tense (the pattern: when an entry fixes what
  an older entry lists as open, edit the older entry).

Every fenced block in those four docs is executed by
`tests/unit/test_docs_fenced_blocks.py` (warnings are errors; `no-run` stubs
are checked against the class), so the examples are the integration test.

## Tests to write first (TDD; the harness must be red before the code)

New file, e.g. `tests/unit/test_datetime_index_converts_at_the_constructor.py`:
constructor from a DatetimeIndex (naive; tz-aware per the decision;
TimedeltaIndex) - index is float64 seconds starting at 0.0, `ts_offset` is
the first stamp's epoch seconds, `has_timestamp_offset` is True, `freq`
derives (1/86400 for daily); `duration`, `get_statistics`, `resample('D')`,
`diff_ts`, every spectral entry point with a declared rate - all work and
return what the same data on a numeric index returns (bit-identical where
the arrays are the same); the accessor round-trips the original index
exactly; `time_slice` with date strings selects the same rows as the
numeric equivalent; the `times` setter given a DatetimeIndex converts the
same way; `from_df` with a datetime column (per the decision); offset
survives `iloc`, arithmetic, `copy()`, pickle, `_create_new_with_data`
derivations (`lowpass_at`, `filter_outliers`), and `baseTs(ts)` conversion
(#57's sentinel rule); explicit `ts_offset=` alongside a DatetimeIndex per
the decision; a series built from numeric seconds is byte-for-byte
unchanged in every metadata field (the change must not touch the numeric
path - pin with a metadata census, the `_seeded` pattern in
`tests/unit/test_core.py`).

Existing pins to expect to change: `tests/unit/test_data_setter_span.py`
(index dtype), anything asserting `freq` is NaN on a DatetimeIndex, and
`from_df`'s rejection test if that contract changes. Grep
`DatetimeIndex|date_range|to_datetime` under `tests/` first.

## Working rules this arc has settled on (see the memory files for the why)

- Branch from `main`; commit only what `git show --stat HEAD` shows you
  meant to (a `git stash` / `pop` around a rebase drops the index - use
  `--index` or re-`git add`).
- `git checkout -- graphify-out` before every commit; the hook rewrites it.
- Legs: default `python3` (numpy 2.5.2 / pandas 3.0.1);
  `uv run -q --no-project --python 3.11 --with pandas==2.2.3 --with "numpy<2" --with "scipy<1.14" --with statsmodels --with matplotlib --with pytest -m pytest -q ...`
  (numpy 1.26 / pandas 2.2.3); pandas 2.3.3 on 3.10 the same way. CI runs
  3.9/3.10/3.11 with `requirements.txt`.
- mypy: `uv run -q --no-project --with mypy --with numpy --with pandas --with scipy --with matplotlib --with statsmodels -m mypy baseTs --python-version 3.12 --ignore-missing-imports`
  - compare the count with `main` in a worktree (73 = 73 today).
- flake8 the new test files at `--max-line-length=100`.
- Reviews: `consensus-review` agent (codex + agy) on the committed diff, then
  `quick-review` (a different harness) on the fix commits; each round's
  findings verified against `main` before acting; a round-N commit names
  what the round found. The consensus agent may check out `main` under the
  tree - do not edit while it runs, and run mutation harnesses in a
  worktree under the scratchpad (`git worktree add <dir> HEAD`,
  `PYTHONDONTWRITEBYTECODE=1`), never on uncommitted code.
- Mutation-test every new guard/condition; report survivors as equivalent
  or turn them into tests.
- `pytest.approx` has a 1e-12 absolute tolerance by default: pass `abs=0`
  when values are small.
- Prose claims are the recurring defect: every number in the CHANGELOG is
  measured on the exact example it describes, an issue's rationale is a
  claim to verify, "refuses X" needs the ndarray spelling too, and when a
  new entry fixes something an older entry lists as open, edit the older
  entry.
- PR body: what was wrong, the fix, behaviour changes stated, verification
  (legs, mypy, mutation, rounds), then `🤖 Generated with [Claude Code](https://claude.com/claude-code)`
  and the session link; merge on green CI with `gh pr merge N --merge --delete-branch`.
- Update the two memory files above when done (merge sha, lessons).

## Decisions taken while implementing (2026-09-05)

The open choices above, as pinned by
`tests/unit/test_datetime_index_converts_at_the_constructor.py`:

1. **Timezone-aware index: accepted as its UTC instant.** Epoch seconds
   identify an instant exactly, so nothing is lost but the display zone;
   `datetimes` returns naive UTC and `.tz_localize('UTC').tz_convert(zone)`
   restores the zone. Refusing would have added a carve-out for a case
   the arithmetic already handles.
2. **Explicit `ts_offset=` alongside a `DatetimeIndex`: refused** as a
   second origin, at every door (constructor, `TimeSeriesData`,
   `from_df`). Alongside a `TimedeltaIndex`, which carries no origin, it
   is accepted and sets one. `has_timestamp_offset=False` alongside a
   `DatetimeIndex` keeps the seconds and drops the origin: a coherent
   request for relative seconds, so allowed.
3. **`from_df` accepts a datetime or timedelta column.** Same rule as the
   constructor, NaT is a missing value as before.
4. **`set_timestamp_offset` records the origin and no longer moves the
   index.** Not foreseen above: the method shifted the times by the offset
   *and* recorded it, the opposite convention to "index relative, offset
   is the origin", and under that convention `datetimes` would have
   counted the offset twice. One integration pin (`test_pipeline.py`)
   asserted the shift; it now asserts the times stay put.
5. **The offset pair moved to `TimeSeriesData.__init__`** (two new
   keywords, passed through by `baseTs.__init__`), because the refusal in
   (2) needs the index kind and the explicit offset in one place, and a
   proxy read of the flag after the fact would have been a rule stated as
   its symptom. Every keyword combination's outcome was measured on `main`
   first and is pinned on both the array and the conversion path.
6. **Precision rule for `datetimes`**: origin rebuilt at the microsecond,
   seconds split whole/fraction before scaling to nanoseconds. Exact for
   any stamp at microsecond resolution or coarser; a nanosecond origin is
   within 0.5 µs. `pd.to_datetime(origin + seconds, unit='s')` was
   inexact on 7 of 14 census cases. `Timedelta.total_seconds()` rounds to
   the microsecond, so `time_slice` places bounds as `.value / 1e9`.
7. **`resample` bins from the origin**, per point 5 above; calendar-anchored
   rules (`'W'`, `'ME'`) are refused by pandas on the seconds index and
   documented as pandas' resample over `datetimes`.
8. Known limit, documented not pinned: a pandas operation that hands a
   *new* `DatetimeIndex` to `_constructor` (`reindex(dates)`,
   `set_axis(dates)`) converts it and records its origin, and
   `__finalize__` then copies the parent's origin over that. Build a new
   object instead.
