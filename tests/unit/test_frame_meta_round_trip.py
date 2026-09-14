"""Round-trip a baseTs' metadata through frame_meta and back."""
import numpy as np
import pytest

from baseTs import baseTs
from baseTs.frame_meta import (
    COL_META_FIELDS,
    _IndexMeta,
    default_col_meta_row,
    harvest_col_meta,
    hydrate_column,
    refuse_reserved_columns,
)
from baseTs.utils import ValidationError


def _ts():
    times = np.arange(32) / 8.0
    ts = baseTs(data=np.arange(32.0), times=times, freq=8.0, signal_name="c0")
    return ts.lowpass_at(2.0)


def test_col_meta_fields_are_the_nine_per_column_slots():
    assert COL_META_FIELDS == (
        "signal_name", "history", "is_filtered", "is_interpolated",
        "is_outlier_filtered", "last_process", "outlier_indices",
        "lowess_fit", "outlier_filter",
    )


def test_index_meta_round_trips_from_a_series():
    ts = _ts()
    meta = _IndexMeta.from_series(ts)
    assert meta.declared_freq == 8.0
    assert meta.ts_offset == ts.ts_offset
    assert meta.has_timestamp_offset == ts.has_timestamp_offset
    assert meta.is_uniform_grid == ts.is_uniform_grid
    kwargs = meta.constructor_kwargs()
    assert kwargs["freq"] == 8.0
    assert kwargs["ts_offset"] == ts.ts_offset
    assert kwargs["has_timestamp_offset"] == ts.has_timestamp_offset
    assert kwargs["is_uniform_grid"] == ts.is_uniform_grid


def test_index_meta_reads_the_declaration_not_the_effective_freq():
    # A series with no declared freq still has an effective .freq (derived
    # from the index); _IndexMeta must read the declaration, not that
    # derived value, or a derived rate would be silently promoted to a
    # declared one on the next hydrate.
    times = np.arange(32) / 8.0
    ts = baseTs(data=np.arange(32.0), times=times)
    meta = _IndexMeta.from_series(ts)
    assert np.isnan(meta.declared_freq)


def test_harvest_col_meta_reads_the_nine_fields():
    ts = _ts()
    row = harvest_col_meta(ts)
    assert set(row.keys()) == set(COL_META_FIELDS)
    assert row["signal_name"] == ts.signal_name
    assert row["is_filtered"] == ts.is_filtered
    assert row["history"] == list(ts.history)


def test_harvest_col_meta_history_is_an_independent_copy():
    ts = _ts()
    row = harvest_col_meta(ts)
    row["history"].append("mutated")
    assert "mutated" not in ts.history


def test_hydrate_column_rebuilds_an_equivalent_baseTs():
    ts = _ts()
    index_meta = _IndexMeta.from_series(ts)
    row = harvest_col_meta(ts)
    rebuilt = hydrate_column(
        values=np.asarray(ts.values), index=np.asarray(ts.index),
        index_meta=index_meta, row=row, label="c0",
    )
    assert isinstance(rebuilt, baseTs)
    assert np.allclose(np.asarray(rebuilt.values), np.asarray(ts.values))
    assert np.allclose(np.asarray(rebuilt.index), np.asarray(ts.index))
    assert rebuilt.signal_name == ts.signal_name
    assert rebuilt.is_filtered == ts.is_filtered
    assert list(rebuilt.history) == list(ts.history)
    assert rebuilt.freq == ts.freq


def test_hydrate_column_preserves_a_lowercase_label_exactly():
    # baseTs.__init__ upper-cases a signal_name passed as a constructor
    # keyword (it is a normalising property that only __init__ upper-cases;
    # the property setter alone does not). hydrate_column must not lose a
    # column's exact case by routing it through that keyword.
    index_meta = _IndexMeta.from_series(_ts())
    row = default_col_meta_row("c1")
    rebuilt = hydrate_column(
        values=np.arange(32.0), index=np.arange(32) / 8.0,
        index_meta=index_meta, row=row, label="c1",
    )
    assert rebuilt.signal_name == "c1"


def test_hydrate_column_falls_back_to_the_label_when_signal_name_is_blank():
    index_meta = _IndexMeta.from_series(_ts())
    row = harvest_col_meta(_ts())
    row["signal_name"] = ""
    rebuilt = hydrate_column(
        values=np.arange(32.0), index=np.arange(32) / 8.0,
        index_meta=index_meta, row=row, label="fallback_label",
    )
    assert rebuilt.signal_name == "fallback_label"


def test_default_col_meta_row_has_the_nine_fields_and_sane_defaults():
    row = default_col_meta_row("c0")
    assert set(row.keys()) == set(COL_META_FIELDS)
    assert row["signal_name"] == "c0"
    assert row["history"] == []
    assert row["is_filtered"] is False
    assert row["is_interpolated"] is False
    assert row["is_outlier_filtered"] is False


def test_default_col_meta_row_outlier_filters_are_independent_instances():
    a = default_col_meta_row("c0")
    b = default_col_meta_row("c1")
    assert a["outlier_filter"] is not b["outlier_filter"]


def test_refuse_reserved_columns_accepts_none_and_disjoint_columns():
    import pandas as pd
    refuse_reserved_columns(None)
    refuse_reserved_columns(pd.DataFrame({"network": ["DMN"]}, index=["c0"]))


def test_refuse_reserved_columns_rejects_a_maintained_field_name():
    import pandas as pd
    with pytest.raises(ValidationError, match="signal_name"):
        refuse_reserved_columns(pd.DataFrame({"signal_name": ["x"]}, index=["c0"]))
