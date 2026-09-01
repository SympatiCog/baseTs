"""Converting a series must not reset what it was carrying (issue #57).

`TimeSeriesData.__init__` copies the source's metadata whenever the argument
looks like a baseTs, and then `baseTs.__init__` assigns its own keyword
defaults straight over the top - `False` for every flag, `""` for the strings,
a fresh list for `history`. Nine of the thirteen `_metadata` names were lost
that way, silently, on the documented conversion path.

`outlier_filter` was the exception, and only because #15 added a guard for it
alone; the comment above that guard describes this bug for every other name.
The guard does not scale to thirteen, so the constructor now distinguishes
"the caller passed this" from "this is the parameter default" and assigns only
what was actually supplied.
"""
import numpy as np
import pytest

from baseTs import baseTs
from baseTs.series import TimeSeriesData


@pytest.fixture
def carrying():
    """A series with every metadata value moved off its default."""
    ts = baseTs(np.arange(200.0), np.arange(200) / 10.0, signal_name="ECG")
    ts.set_outlier_filter(frac=0.42)
    ts.set_timestamp_offset(1.5)
    ts.last_process = "_thing"
    ts.is_filtered = True
    ts.is_interpolated = True
    ts.is_uniform_grid = True
    # The positional slots too: the constructor assigns these unconditionally
    # as well, and they are the two whose loss a flag comparison would miss.
    ts.outlier_indices = np.array([3, 7])
    ts.lowess_fit = np.arange(200.0)
    return ts


# Every name the conversion used to reset, with the value it should carry over.
PRESERVED = [
    ("signal_name", "ECG"),
    ("is_filtered", True),
    ("is_interpolated", True),
    ("is_uniform_grid", True),
    ("is_outlier_filtered", True),
    ("has_timestamp_offset", True),
    ("ts_offset", 1.5),
    ("last_process", "_thing"),
]


class TestBaseTsConversionPreservesMetadata:
    """`baseTs(ts)` is a conversion, not a reset."""

    @pytest.mark.parametrize("name,expected", PRESERVED)
    def test_value_survives(self, carrying, name, expected):
        assert getattr(baseTs(carrying), name) == expected

    def test_history_survives_verbatim(self, carrying):
        """The sharpest edge: a converted object claimed to be freshly made.

        Verbatim, not merely non-empty - a "Converted from" entry appended
        here would also satisfy a length check while changing what the object
        says about itself.
        """
        assert baseTs(carrying).history == carrying.history

    def test_the_filter_still_survives(self, carrying):
        """#15's guard, which was the only name that already worked."""
        assert baseTs(carrying).get_outlier_filter_params()["frac"] == 0.42

    def test_the_positional_slots_survive(self, carrying):
        """Assigned through the public properties, these were cleared to None.

        Read back through the properties, which return the value only while
        the index still matches - so this asserts the stamp came across too,
        not merely that something is stored.
        """
        conv = baseTs(carrying)
        assert list(conv.outlier_indices) == [3, 7]
        assert len(conv.lowess_fit) == 200

    def test_nothing_in_metadata_is_lost(self, carrying):
        """The whole list, so a name added later cannot quietly drop out."""
        conv = baseTs(carrying)
        lost = [n for n in carrying._metadata
                if repr(getattr(carrying, n, None)) != repr(getattr(conv, n, None))]
        assert lost == []


class TestTimeSeriesDataConversionPreservesMetadata:
    """The same defect on the superclass path, where it costs one name.

    `TimeSeriesData.__init__` assigns `signal_name` unconditionally after
    `_copy_metadata_from_basetseries` has just copied it.
    """

    def test_signal_name_survives(self, carrying):
        assert TimeSeriesData(carrying).signal_name == "ECG"

    def test_nothing_in_metadata_is_lost(self, carrying):
        conv = TimeSeriesData(carrying)
        lost = [n for n in carrying._metadata
                if repr(getattr(carrying, n, None)) != repr(getattr(conv, n, None))]
        assert lost == []


class TestATimeSeriesDataSourceConvertsToo:
    """The conversion branch was gated on `.times` and `.data`.

    Only `baseTs` defines those two properties, so a `TimeSeriesData` source
    fell through to the plain-pandas arm and had every name reset - by both
    constructors. The fix has to recognise the superclass as a source, or it
    covers `baseTs(basets)` alone while the docs claim more.
    """

    @staticmethod
    def _carrying_tsd():
        tsd = TimeSeriesData(np.arange(10.0), np.arange(10) / 10.0)
        tsd.signal_name = "X"
        tsd.is_filtered = True
        tsd.last_process = "_thing"
        return tsd

    def test_basets_from_a_timeseriesdata(self):
        conv = baseTs(self._carrying_tsd())
        assert conv.signal_name == "X"
        assert conv.is_filtered is True
        assert conv.last_process == "_thing"

    def test_timeseriesdata_from_a_timeseriesdata(self):
        conv = TimeSeriesData(self._carrying_tsd())
        assert conv.signal_name == "X"
        assert conv.is_filtered is True


class TestAnEmptyHistoryIsAHistory:
    """An empty carried history must not become a fabricated creation entry.

    The condition tested falsiness rather than absence, so a source whose
    history is `[]` came back claiming "Created baseTs object with N samples" -
    the same "claims to be something it is not" failure this change exists to
    remove, one layer down.
    """

    def test_an_empty_history_stays_empty(self):
        src = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        src.history = []
        assert baseTs(src).history == []


class TestTheOffsetPairStaysCoherent:
    """`has_timestamp_offset` False with a non-zero `ts_offset` was unreachable.

    The `else` branch that zeroed both together enforced it. Removing that
    branch - which is what stopped a conversion losing its offset - also made
    the incoherent pair reachable, and `__finalize__` copies the pair onward,
    so it would propagate through every derivation.
    """

    @staticmethod
    def _offset_source():
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        ts.set_timestamp_offset(1.5)
        return ts

    def test_clearing_the_flag_clears_the_offset(self):
        conv = baseTs(self._offset_source(), has_timestamp_offset=False)
        assert conv.has_timestamp_offset is False
        assert conv.ts_offset == 0

    def test_supplying_an_offset_still_sets_the_flag(self):
        conv = baseTs(self._offset_source(), ts_offset=2.5)
        assert conv.ts_offset == 2.5
        assert conv.has_timestamp_offset is True

    def test_omitting_both_preserves_both(self):
        conv = baseTs(self._offset_source())
        assert conv.ts_offset == 1.5
        assert conv.has_timestamp_offset is True


class TestAnExplicitArgumentStillWins:
    """Preserving what was not passed must not ignore what was.

    The fix distinguishes "supplied" from "defaulted", so a caller who names a
    value explicitly - including one equal to the old default - must still get
    it, or the sentinel has simply moved the bug.
    """

    @pytest.mark.parametrize("name,value", [
        ("signal_name", "OTHER"),
        ("is_filtered", False),
        ("is_interpolated", False),
        ("is_uniform_grid", False),
        ("is_outlier_filtered", False),
        ("last_process", ""),
        ("ts_offset", 0.0),
    ])
    def test_explicit_value_overrides_the_source(self, carrying, name, value):
        conv = baseTs(carrying, **{name: value})
        expected = value.upper() if name == "signal_name" else value
        assert getattr(conv, name) == expected

    def test_explicit_history_overrides_the_source(self, carrying):
        assert baseTs(carrying, history=["fresh"]).history == ["fresh"]

    def test_explicit_none_history_is_not_the_same_as_omitting_it(self, carrying):
        """`history=None` is the documented way to ask for a fresh entry.

        Folding it into the "not supplied" case made it the one nullable
        keyword that preserves rather than clears, silently disagreeing with
        both the signature and every sibling argument.
        """
        assert baseTs(carrying, history=None).history == [
            "Created baseTs object with 200 samples"]


class TestConstructionFromArraysIsUnchanged:
    """The ordinary path must still start from defaults, not from nothing.

    Nothing is copied when the data is an array, so every name has to come
    from the constructor's own defaults - which is what the internal callers
    in series.py and core.py rely on.
    """

    def test_defaults_are_still_applied(self):
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        assert ts.is_filtered is False
        assert ts.is_interpolated is False
        assert ts.is_uniform_grid is False
        assert ts.is_outlier_filtered is False
        assert ts.has_timestamp_offset is False
        assert ts.ts_offset == 0
        assert ts.last_process == ""
        assert ts.signal_name == ""
        assert ts.history == ["Created baseTs object with 10 samples"]
