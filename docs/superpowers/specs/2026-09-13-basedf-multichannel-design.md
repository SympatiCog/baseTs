# Design: `baseDf` — many time series on one shared index

Spec 1 of 2. Spec 2 (`epoch()`, the trial dimension) is a follow-on and is
scoped out here deliberately; see "Why epoching comes second".

Brainstormed with Stan 2026-09-13, branching from `main` at `87e2c28`.
Working rules this repo's review arc has settled on:
`~/.claude/projects/-Users-stan-python-baseTs/memory/basets-adversarial-review-rounds.md`.

## Intent

Not an EEG stack — MNE-Python already owns that, and replicating it is an
explicit non-goal (Stan, 2026-09-13). The target is **derived** multichannel
data that this library's existing measures already speak to:

- specparam outputs across channels (aperiodic exponent, offset, peak
  parameters) over sliding windows or epochs
- fMRI region-of-interest timeseries

The second case is not speculative. `baseTs.falff(low_freq=0.01,
high_freq=0.1)` (core.py:2551) and `baseTs.relative_band_power` with the same
defaults (core.py:2477) are canonical fMRI resting-state measures that today
can only see one ROI at a time. `baseDf` is the missing container for measures
already written.

## The two decisions that shaped everything

### Decision 1 (Stan, 2026-09-13): DataFrame-backed, not DataFrame-subclassed

`series.py` is 2008 lines, of which roughly the first 1000 — everything from
`_carries_metadata` (line 51) through `_freq_token` (line 990) — is not
time-series logic. It is propagation plumbing for subclassing `pd.Series`:
duplicate-label refusal, origin stamping, positional-metadata invalidation,
`__setstate__` healing a pickle that predates `_name`. That plumbing was paid
for over #39, #56, #90, #96, #100.

`pd.DataFrame` is worse to subclass than `pd.Series`: a block manager,
`_constructor_sliced` firing on every column access, and more `__finalize__`
entry points. The expensive bugs in this repo's history came from pandas
calling *into* metadata at moments not yet enumerated. A non-subclass has no
such moments — the metadata contract is code we wrote, called where we call it.

Rejected: a true `pd.DataFrame` subclass (maximum ergonomics, second plumbing
campaign); a pure composition container holding a list of `baseTs` (zero
pandas risk, but reimplements selection, alignment and MultiIndex by hand and
is not a DataFrame).

The cost accepted: `frame.rolling(...)` and every other pandas method is **not**
inherited. `.df` is the escape hatch; each forward is a deliberate addition.

### Decision 2 (Stan, 2026-09-13): flat columns now, MultiIndex-tolerant

One frame holds one measure across many columns, so columns are commensurable
by construction and `average()` never has to ask which axis is meaningful.
A `MultiIndex` (e.g. `(measure, channel)` for a full specparam table) is not
forbidden — it passes through transforms untouched — but any operation where
level matters requires an explicit `level=` rather than guessing. Averaging an
aperiodic exponent (unitless) with a peak centre frequency (Hz) must never
happen by default.

## Measured facts on `main` at 87e2c28 (pandas 3.0.1, numpy 2.5.2, py3.12)

**The load-bearing invariant holds today.** No transform's output *index*
depends on its data *values*. Twenty-five transform calls (24 distinct methods) were run on two
datasets sharing one input index (one seeded with an outlier at sample 50, one
without); every output index matched in shape and value, including the
length-changing ones:

```
zscale center abs lowpass_at highpass_at bandpass_at notch_at gauss_filter
sg_filter detrend lowess_detrend filter_outliers rolling_mean rolling_std
diff_ts diff_ts(zeropad) interpto_hz interpto_samples time_slice
trimto_timepoints shift_time interp_to_uniform_grid interpolate_missing
normalize_range scale
    -> checked 25, data-dependent-index: 0, errored: 0
```

This is what makes column-wise broadcast safe. The design **enforces** it
rather than assuming it (rule 3 below), so a future method that breaks it
fails loudly instead of corrupting a frame.

**`filter_outliers` is frame-safe.** It was the one method suspected of being
hostile to a shared index, because it assigns both `self.data` and
`self.times`. Measured: 500 samples in, 500 out, index identical, 53 values
replaced, 0 NaN. It diverges per column in values and flags, never in index.

**API shape.** `core.py` has **40** methods returning `"baseTs"` (by introspecting
`__annotations__`; a line-based grep reports 30 because it misses multi-line
signatures such as `bandpass_at`, `time_slice`, `remove_outliers`,
`interpolate_gaps` and `set_outlier_filter`), plus 3 returning
`tuple`, 3 `np.ndarray`, 2 `dict`, and one each of `list`, `int`, `float`,
`ClosestMatch`, `pd.DataFrame`, `plt.Axes`, `_PlotAccessor`. Of the 40, all but
`copy` (the frame has its own) are the broadcast target: **39**. The rest are
measurements needing per-method handling.

**Metadata splits cleanly.** `TimeSeriesData._metadata` (series.py:1111) has 14
slots beyond `_name`. Five are functions of the index alone and are therefore
shared by every column: `_freq_declaration`, `ts_offset`, `_origin_index`,
`has_timestamp_offset`, `is_uniform_grid`. Nine are per-column: `signal_name`,
`history`, `is_filtered`, `is_interpolated`, `is_outlier_filtered`,
`last_process`, `_outlier_indices`, `_lowess_fit`, `outlier_filter`.

## Object model

One class, `baseDf`. The `TimeSeriesData`/`baseTs` split exists to separate
pandas plumbing from domain logic; decision 1 removes the plumbing, so it
removes the reason for the seam.

| State | Type | Why exactly one |
|---|---|---|
| `_df` | `pd.DataFrame`; index is seconds-since-origin (float), as `baseTs` stores post-#100. Columns are channel/ROI/trial labels. | The values. |
| `_index_meta` | Four scalars: declared freq, `ts_offset`, `has_timestamp_offset`, `is_uniform_grid`. | All are functions of the index alone, which every column shares by definition. `_origin_index` is the fifth shared slot but is **derived**, not stored: measured, passing `ts_offset` with `has_timestamp_offset=True` restamps an identical origin. |
| `_col_meta` | `pd.DataFrame`, one row per column, index aligned to `_df.columns`. | The nine per-column slots, **plus** arbitrary user attributes: `network`, `hemisphere`, `bad`, `condition`, `rt`, `trial`. |

**The frame stores declarations; `baseTs` validates them.** `_index_meta` holds
a freq *declaration*, not a rate. When `frame["Cz"]` constructs a `baseTs`,
that constructor re-validates the declaration against the index it actually
received. This is the `_freq_declaration`-plus-index-token pattern already in
`series.py:1111`, applied one level up — no validation logic is duplicated.

**`_col_meta` is a DataFrame, not a dict of metadata objects.** pandas aligns,
subsets and reorders it for free whenever columns change, which is the failure
mode a hand-rolled dict would hit first. It also generalises at no cost: the
same table holds `bad`/`network`/`hemisphere` for ROIs and
`condition`/`trial`/`rt` for trials, which is what makes one selection
predicate serve both.

## Operations

Every public `baseTs` method falls into one of four buckets.

**1. Transforms** (39, `-> "baseTs"`). Broadcast column-wise, return a new
`baseDf`. Each column's `history` row receives the same new entry — they
genuinely each got lowpassed — and `last_process`/`is_filtered` update per
column. For index-changing transforms, `_index_meta` is re-derived from the
first column's returned `baseTs`; the all-columns-same-index assertion is
precisely what licenses trusting one column to speak for all.

**2. Measurements** (`-> float`/`dict`/`tuple`/`ndarray`). Return a `pd.Series`
or `pd.DataFrame` indexed by column label. `frame.falff()` gives 400 values;
`frame.get_statistics()` gives columns × stats. `compute_fft_power` and
`get_frequency_content` return tuples and need real handling, not blind
broadcast: the frequency axis is shared, the power becomes a DataFrame.

**3. Reduction.** `average` / `average_by`, specified below.

**4. Plots.** Out of scope for this spec; minimal forwarding only.

### Correlation

**Decision (Stan, 2026-09-13): the default is one vector against every column,
not every column against every other.** The motivating case is a seed: a
continuous behavioural regressor correlated against a FOOOF-derived measure at
each electrode, or a seed timeseries against each fMRI ROI. An all-pairs matrix
is the wrong default because it answers a question nobody asked and costs
O(k^2) to answer it.

```python
frame.correlation_with(other: baseTs, method="pearson") -> pd.Series
frame.correlation_matrix(other: baseDf | None = None, method="pearson") -> pd.DataFrame
```

Two methods rather than dispatch on the type of `other`, holding to the
return-type rule. Passing a frame to the first, or a series to the second, is
refused with a message naming the other method. `correlation_matrix(None)`
means "against myself" — the within-frame connectivity matrix, which is the
dominant fMRI use and costs one line to allow.

`baseTs.correlation_with` (core.py:2242) aligns with an **inner** join and then
calls `Series.corr`. Alignment is harmless here in a way it is not elsewhere:
the result is scalars, so there is no shared index to preserve, and every
column aligns identically against the same `other`.

The vector case delegates per column and is therefore equivalent by
construction. The matrix case cannot — 400 x 400 would be 160,000 aligned
`baseTs` calls — so it intersects the two indices **once** and then uses
`DataFrame.corrwith` per right-hand column. Measured equivalent to the
per-pair path for `pearson`, `spearman` and `kendall`, with a NaN present, so
the vectorisation is a speed-up and not a second definition of correlation. A
test pins that equivalence.

### Selective averaging

Two methods, not one overloaded method — a function whose return *type* depends
on its arguments is a trap, and this spec holds itself to that (it is also why
the module-level `from_df` is left exactly as it is, rather than taught to
return a frame sometimes).

```python
frame.average(select=None, where=None, skipna=False, min_count=None, name=None) -> baseTs
frame.average_by(by, select=None, where=None, skipna=False, min_count=None) -> baseDf
```

`min_count` defaults to `None`, not a number: `None` means "not requested," which
is what distinguishes a bare call from one that actually asked for a floor. A
literal default of `1` would be indistinguishable from the user passing `1`, so it
could never coexist with the refusal two paragraphs below without breaking every
bare `frame.average()` call.

- `select` — labels or a boolean mask
- `where` — a query string against `_col_meta`: `where="network == 'DMN' and not bad"`
- `by` — grouping column(s) in `_col_meta`; `average_by` returns one column per group

ROI→network is `average_by("network")`. An ERP, once spec 2 lands, is
`epoched.average(where="condition == 'B'")`. Same table, same predicate
language, both uses — which is the finding that collapsed two apparently
separate features into one primitive.

**Flag propagation: contamination ORs, treatment ANDs.**

`is_interpolated` means *some values here were not measured*. It is a property
of the data, so it propagates if **any** contributor carries it, and is never
reset — #90's rule, unchanged. `is_filtered` and `is_outlier_filtered` mean
*this series has been treated*, a claim about the whole series, so they hold
only if **every** contributor was treated. Averaging 17 ROIs of which 3 were
outlier-filtered yields `is_filtered=False`, with the divergence recorded in
history. That matches the existing norm at core.py:1552 — *"Say what was left
alone, not just what was configured... the history is where a reader looks to
find out."*

**History is the common prefix, then a summary.** Claiming "bandpassed 1–10 Hz"
is honest only if every input was bandpassed. The result's history is the
common prefix of the contributors' histories, then one entry naming the
selection, `n`, and the NaN policy; divergence beyond the prefix is summarised
(`inputs diverged after step 4; 3 of 17 additionally outlier-filtered`).
`_outlier_indices`, `_lowess_fit` and `outlier_filter` are per-column artifacts
with no meaning for a mean — dropped, and history says so.
`signal_name` is `name` if given, else derived from the selection.

**NaN default is propagate, not skip.** `skipna=False`. A specparam fit that
failed on channel 17 at window 40 means `skipna=True` averages a *different set
of channels* at that window than everywhere else, silently changing the
estimator mid-series. That is the failure #36 is about, so it cannot be the
default. `skipna=True` is explicit and records in history how many timepoints
ran at reduced `n`; `min_count` guards the floor. The full per-timepoint count
is `frame.df.notna().sum(axis=1)`, so no new slot is invented for it.

**What `average_by` writes into the result's `_col_meta`.** One row per group.
`signal_name` is the group label; `history` is that group's own common prefix
plus its summary entry; the flag rules above apply within each group
independently. Group membership and `n` are recorded in each row's history, so
a group of 1 is legal and says so rather than looking like an untouched column.

**`min_count` applies only when `skipna=True`.** With the default
`skipna=False` a single NaN already propagates, so a floor on the contributor
count has nothing to act on; passing `min_count` alongside `skipna=False` is
refused rather than silently ignored.

### Indexing

`frame["Cz"]` returns a `baseTs`; `frame[["Cz", "Pz"]]` returns a `baseDf`.
This is a **deliberate exception** to the two-return-types rule above, because
it is pandas' own `__getitem__` contract and users' hands already know it.
`frame.loc[t0:t1]` forwards to `.df` and rewraps, re-deriving `_index_meta`.

## Construction

```python
baseDf(data, index=None, freq=None, ts_offset=None, col_meta=None)
baseDf.from_df(df, time_col="time", value_cols=None, freq=None, col_meta=None)
baseDf.from_series([ts1, ts2, ...])
```

`from_df` with `value_cols=None` takes every numeric column except `time_col`;
non-numeric columns are refused with their names listed, never silently
dropped. `from_series` validates that indices match, lifts shared metadata into
`_index_meta` and each series' own into a `_col_meta` row — it is the bridge
from today's workflow, and it is what `epoch()` will call in spec 2.

No `read_parquet` wrapper: `pd.read_parquet(p)` then `baseDf.from_df(...)` is
two lines. No long→wide helper: `df.pivot(...)` then `from_df`, documented as a
recipe in `EXAMPLES.md`.

**Persistence is deferred as a decision, not omitted.** `to_dataframe()` returns
the values and `col_meta` is a public `DataFrame`, so a caller saves both in
whatever layout they like. This spec does not invent a sidecar-file convention
and does not lean on `DataFrame.attrs`, which `to_parquet` does not reliably
carry. If round-tripping a frame with its provenance proves to be a real need,
it gets its own spec with evidence behind the format.

## Error handling

A private `_check_invariants()` runs after anything that can change columns.

1. `_col_meta.index` equals `_df.columns`, same order — the single alignment
   invariant, checked in one place.
2. **Duplicate column labels refused**, reusing the pattern of
   `_raise_duplicate_label_refusal` (series.py:519). `_col_meta` keyed by a
   duplicated label is ambiguous — the same class of problem that machinery
   already solves for the index.
3. **Index-invariant violation after broadcast** — raises, naming the offending
   column and both differing indices.
4. **Reserved `_col_meta` names** — the nine metadata fields. A colliding user
   attribute is refused at construction with the collisions listed.
5. **Non-numeric source columns** — refused with names.
6. **Empty selection** — `where=` matching nothing, or an empty `select`,
   raises. A silently-empty average is the worst available outcome.
7. **`from_series` with mismatched indices** — refused, pointing at `align_with`.
8. **`from_series` with conflicting `freq` or `ts_offset`** — refused.

## Testing

New files follow the repo's one-file-per-concern intent-naming convention
(`tests/unit/test_is_interpolated_means_one_thing.py` is the model).

**The test that justifies the design: broadcast equivalence.** For every public
`-> baseTs` transform, `baseDf(...).method(args)["c0"]` must equal
`baseTs(c0_data).method(args)` in values, index, **and every metadata field**.
Parametrized over an explicit inventory, with a guard test asserting that
inventory covers every public transform on `baseTs` — so a method added later
without frame coverage fails the suite rather than being silently unbroadcast.
This is "state rules, not carve-out lists" applied to the broadcast surface.

Around it:

- the index invariant, per length-changing transform, with columns carrying
  different data
- `_col_meta` surviving column selection, reordering, dropping, and `.loc`
  time slicing
- averaging: NaN propagation, the `skipna` history entry, contamination-OR,
  treatment-AND, common-prefix history, empty-selection refusal, and
  `min_count` alongside `skipna=False` refused
- `from_series` metadata round-trip: `baseDf.from_series([a, b])["a"]` is
  metadata-equal to `a`
- duplicate column labels refused
- object-dtype `_col_meta` columns holding `history` lists under pandas 3 —
  the fragile spot in this version matrix

## Why epoching comes second

Selecting both readings of "selective averaging" (Stan, 2026-09-13) produced
the structural finding that shaped this spec: **an epoch set and a channel set
are the same object.** Cutting a series at event onsets with equal-length
windows yields one shared index (peri-event time) and many labelled columns
(trials) — structurally identical to one shared index (acquisition time) and
many labelled columns (ROIs). So:

```
ts.epoch(events, tmin, tmax)     -> baseDf   (columns are trials)
frame.average(where=...)         -> baseTs
ERP = the two composed;  ROI->network = the second alone
```

There is only one averaging primitive, it works across columns, and "selective"
is a predicate over column labels. Epoching's *output type is `baseDf`*, so it
cannot be designed before `baseDf` exists. Hence the order.

Known edge to name now and solve in spec 2: unequal-length epochs break the
one-shared-index shape.

## Scope boundary

Out of scope for spec 1: epoching and the trial dimension; plotting beyond
minimal forwarding; a persistence format; general pandas-method forwarding;
any change to `baseTs`, `TimeSeriesData`, or the module-level `from_df`.
