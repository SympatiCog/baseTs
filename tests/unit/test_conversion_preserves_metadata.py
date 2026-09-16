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

    @pytest.mark.parametrize("falsy", [False, np.False_, 0],
                             ids=["bool", "numpy_bool", "int"])
    def test_any_falsy_flag_clears_the_offset(self, falsy):
        """`is False` matches one object; numpy booleans are not it.

        `arr.any()`, a comparison result, a column read out of a DataFrame -
        all produce `np.False_`, which is falsy but not the `False` singleton,
        so an identity test let exactly the incoherent pair through.
        """
        conv = baseTs(self._offset_source(), has_timestamp_offset=falsy)
        assert conv.ts_offset == 0

    def test_asserting_the_flag_without_an_offset_is_the_callers_business(self):
        """The coherence rule runs one way, deliberately, and this pins it.

        Clearing the flag clears the offset, because "no offset applied, offset
        1.5" is a state nothing downstream expects. The reverse is a caller
        asserting an offset was applied without saying what it was, which is
        odd but is their assertion to make - and turning it into an error would
        reject a call that works today.
        """
        conv = baseTs(np.arange(10.0), np.arange(10) / 10.0,
                      has_timestamp_offset=True)
        assert conv.has_timestamp_offset is True
        assert conv.ts_offset == 0


class TestAnIgnoredIndexIsRefused:
    """The conversion branch takes its index from the source, so a `times`
    argument passed alongside was silently dropped.

    On `main` this was visible for a `TimeSeriesData` source - it reindexed to
    all-NaN, wrong but loud. Recognising that type as a source (which is the
    #57 fix) made it quiet instead, which is the wrong direction of travel for
    a change that exists to stop objects lying about themselves.
    """

    @pytest.mark.parametrize("source", ["basets", "timeseriesdata"])
    def test_a_conflicting_index_raises(self, source):
        src = baseTs(np.arange(200.0), np.arange(200) / 10.0)
        if source == "timeseriesdata":
            src = TimeSeriesData(np.arange(200.0), np.arange(200) / 10.0)
        with pytest.raises(ValueError, match="index"):
            baseTs(src, times=np.arange(5.0))

    def test_converting_without_an_index_is_unaffected(self):
        src = baseTs(np.arange(200.0), np.arange(200) / 10.0)
        assert len(baseTs(src)) == 200


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
            "Created baseTs object; 200 samples"]


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
        assert ts.history == ["Created baseTs object; 10 samples"]
