"""A broadcast column must equal the same call made on a lone baseTs.

This is the test the container's design rests on: if a frame's column can
diverge from the series it stands for, nothing else here is trustworthy.
"""
import inspect
import warnings

import numpy as np
import pandas as pd
import pytest

from baseTs import baseTs
from baseTs.frame import baseDf
from baseTs.frame_meta import COL_META_FIELDS
from baseTs.utils import ValidationError

N = 256
TIMES = np.arange(N) / 16.0


def _columns() -> dict:
    rng = np.random.default_rng(0)
    a = rng.normal(size=N) + np.sin(2 * np.pi * 1.5 * TIMES)
    b = rng.normal(size=N) + np.sin(2 * np.pi * 3.0 * TIMES)
    a[40] = 30.0          # an outlier in one column only, so the columns
    b[200] = -25.0        # genuinely diverge in values and flags
    return {"c0": a, "c1": b}


def _frame() -> baseDf:
    cols = _columns()
    return baseDf(pd.DataFrame(cols, index=TIMES), freq=16.0)


def _lone(label: str) -> baseTs:
    # history=[] explicitly, matching how hydrate_column builds a frame's
    # column: passing an explicit list (even empty) takes baseTs.__init__'s
    # "else" branch, not the "history unset" branch that mints a "Created
    # baseTs object with N samples" entry (core.py, TimeSeriesData.__init__).
    # Without this, _lone would carry that entry and frame_out[label] would
    # not (the frame deliberately suppresses it - a hydrated column is an
    # internal view, not a fresh user construction), so an otherwise-identical
    # transform call would produce histories differing only by that phantom
    # entry, failing the equality check below for every single case. Verified
    # live before writing this comment.
    #
    # signal_name is set via the property setter, not the signal_name=
    # constructor keyword: baseTs.__init__ upper-cases a signal_name it
    # receives as a keyword (verified live: signal_name="c0" comes back as
    # "C0"), but the setter does not - the exact asymmetry frame_meta.py's
    # hydrate_column documents and works around by assigning after
    # construction. A frame's column is hydrated the same way, so it keeps
    # the label's original case; _lone must match that or every case here
    # would fail on signal_name alone, for a difference that isn't real.
    ts = baseTs(data=_columns()[label], times=TIMES.copy(), freq=16.0, history=[])
    ts.signal_name = label
    return ts


# (method name, positional args, keyword args)
CALLS = [
    ("zscale", (), {}),
    ("center", (), {}),
    ("abs", (), {}),
    ("scale", (2.0,), {}),
    ("normalize_range", (), {}),
    ("detrend", (), {}),
    ("lowess_detrend", (), {}),
    ("lowpass_at", (4.0,), {}),
    ("highpass_at", (0.5,), {}),
    ("bandpass_at", (0.5, 4.0), {}),
    ("notch_at", (2.0,), {}),
    ("lowpass_filter", (4.0,), {}),
    ("highpass_filter", (0.5,), {}),
    ("bandpass_filter", (0.5, 4.0), {}),
    ("notch_filter", (2.0,), {}),
    ("butterpass_at", (0.5, 4.0), {}),
    ("gauss_filter", (2.0,), {}),
    ("sg_filter", (11, 2), {}),
    ("rolling_mean", (5,), {}),
    ("rolling_std", (5,), {}),
    ("rolling_median", (5,), {}),
    ("rolling_max", (5,), {}),
    ("rolling_min", (5,), {}),
    ("diff_ts", (), {}),
    ("diff_ts", (), {"zeropad": True}),
    ("interpolate_missing", (), {}),
    ("interpto_hz", (8.0,), {}),
    ("interpto_samples", (128,), {}),
    ("interp_to_uniform_grid", (), {"inplace": False}),
    ("time_slice", (1.0, 8.0), {}),
    ("trimto_timepoints", (1.0, 8.0), {}),
    ("shift_time", (3,), {}),
    ("set_outlier_filter", (), {}),
    ("filter_outliers", (), {}),
    ("apply_function", (np.sqrt,), {}),
    ("dediff_ts", (), {}),
    ("resample", ("1s",), {}),
    ("interpolate_gaps", (), {}),
    ("set_indices_to_nan_and_interpolate", ([10, 11],), {}),
]


@pytest.mark.parametrize("name,args,kwargs", CALLS,
                         ids=[f"{n}{sorted(k)}" for n, _, k in CALLS])
def test_a_broadcast_column_equals_the_lone_series(name, args, kwargs):
    warnings.filterwarnings("ignore")
    frame_out = getattr(_frame(), name)(*args, **kwargs)
    for label in ("c0", "c1"):
        expected = getattr(_lone(label), name)(*args, **kwargs)
        actual = frame_out[label]
        assert np.allclose(np.asarray(actual.data, dtype=float),
                           np.asarray(expected.data, dtype=float),
                           equal_nan=True), f"{name} values for {label}"
        assert np.allclose(np.asarray(actual.index, dtype=float),
                           np.asarray(expected.index, dtype=float)), f"{name} index"
        for field in ("signal_name", "is_filtered", "is_interpolated",
                      "is_outlier_filtered", "last_process"):
            assert getattr(actual, field) == getattr(expected, field), \
                f"{name}.{field} for {label}"
        assert list(actual.history) == list(expected.history), f"{name} history"


def test_the_call_table_covers_every_broadcast_transform():
    """A transform added later without a frame test fails here, rather than
    being silently unbroadcast."""
    covered = {name for name, _, _ in CALLS}
    assert covered == set(baseDf.TRANSFORMS), (
        f"untested: {sorted(set(baseDf.TRANSFORMS) - covered)}; "
        f"stale: {sorted(covered - set(baseDf.TRANSFORMS))}"
    )


def test_the_transform_inventory_matches_baseTs():
    """State the rule, don't maintain a carve-out list: TRANSFORMS is every
    baseTs method annotated as returning a baseTs, minus NOT_BROADCAST.

    core.py has `from __future__ import annotations`, and its methods are
    written with an already-quoted forward reference (`-> "baseTs":`). PEP 563
    stringifies the unparsed source, so `inspect.signature(...).return_annotation`
    comes back as the 8-character string `'baseTs'` - literal single quotes
    included, not the bare name and not a double-quoted string. Strip whichever
    quote character survived before comparing.
    """
    found = set()
    for name, func in inspect.getmembers(baseTs, predicate=inspect.isfunction):
        if name.startswith("_") or func.__qualname__.split(".")[0] != "baseTs":
            continue
        annotation = str(inspect.signature(func).return_annotation).strip("'\"")
        if annotation == "baseTs":
            found.add(name)
    assert found - baseDf.NOT_BROADCAST == set(baseDf.TRANSFORMS)


def test_inplace_replaces_the_frames_contents():
    frame = _frame()
    before = np.asarray(frame.df["c0"]).copy()
    returned = frame.center(inplace=True)
    assert returned is frame
    assert not np.allclose(np.asarray(frame.df["c0"]), before)


def test_user_attributes_survive_a_broadcast():
    cols = _columns()
    user = pd.DataFrame({"network": ["DMN", "FPN"]}, index=["c0", "c1"])
    frame = baseDf(pd.DataFrame(cols, index=TIMES), freq=16.0, col_meta=user)
    assert frame.lowpass_at(4.0).col_meta.at["c1", "network"] == "FPN"


def test_a_data_dependent_index_is_refused():
    frame = _frame()

    def _ragged(self, **kwargs):
        # Returns a different length depending on the data, which is exactly
        # what a shared index cannot survive.
        # argmax differs by construction: c0 spikes at 40, c1 at 200.
        keep = 200 + int(np.argmax(np.abs(np.asarray(self.data, dtype=float)))) % 7
        return self.iloc[:keep]

    baseDf._ragged = lambda self, **kw: self._broadcast("_ragged_src", (), kw)
    baseTs._ragged_src = _ragged
    try:
        with pytest.raises(ValidationError, match="different index"):
            frame._ragged()
    finally:
        del baseDf._ragged, baseTs._ragged_src
