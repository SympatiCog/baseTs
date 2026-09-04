"""`signal_name` and `last_process` are always strings, in place too (#61).

#33 made the rule "the label metadata is always a string" hold on every
derivation and through both constructors, and pinned its own boundary: it
did not heal an object you mutate. `ts.signal_name = None` stored `None`, and
it was the next derivation that turned it into `""`. That half is what let
`lag_plot`'s bare `except` fire at all (#61), and it is what this closes, the
way #33's note said it would be closed - a normalising property, the `freq` /
`lowess_fit` shape: the value is coerced where it enters the object, so no
reader has to guard it.

Both labels, not one. The rule is about the label metadata, and a property on
one label with a plain attribute on the other would be a carve-out from it.

The private slots are `_signal_name` and `_last_process`; `_metadata` keeps
the *public* names, deliberately. pandas propagates `_metadata` entries with
`object.__setattr__`, which honours data descriptors, so every propagation
path - `__finalize__`, `copy`, `__setstate__` - runs the setter. For the
positional slots that would be laundering (#20); for a label it is exactly
the normalisation wanted, and it is what lets a legacy pickle carrying `None`
restore as `""`.
"""
import copy
import pickle

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from baseTs import baseTs  # noqa: E402
from baseTs.series import TimeSeriesData  # noqa: E402


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def _ts():
    return baseTs(np.arange(10.0), np.arange(10) / 10.0)


LABELS = ["signal_name", "last_process"]

COERCIONS = [
    pytest.param(None, "", id="none"),
    pytest.param(12, "12", id="int"),
    pytest.param(3.5, "3.5", id="float"),
    pytest.param("Heart Rate", "Heart Rate", id="str-verbatim"),
    pytest.param("", "", id="empty"),
]


class TestAssignmentNormalisesInPlace:
    """The half #33 left open: the object you mutate, not the one you derive."""

    @pytest.mark.parametrize("label", LABELS)
    @pytest.mark.parametrize("value, expected", COERCIONS)
    def test_baseTs(self, label, value, expected):
        ts = _ts()
        setattr(ts, label, value)
        assert getattr(ts, label) == expected
        assert type(getattr(ts, label)) is str

    @pytest.mark.parametrize("label", LABELS)
    @pytest.mark.parametrize("value, expected", COERCIONS)
    def test_TimeSeriesData(self, label, value, expected):
        """The property lives on the base class, so the pandas-level object
        gets it without going through baseTs."""
        tsd = TimeSeriesData(np.arange(10.0), index=np.arange(10) / 10.0)
        setattr(tsd, label, value)
        assert getattr(tsd, label) == expected

    def test_the_mutated_object_itself_plots(self):
        """#33's live crash, on the object that was mutated rather than on a
        derivation of it: `signal_name + " " + last_process`."""
        ts = _ts()
        ts.signal_name = None
        ts.last_process = None
        ts.plot()

    @pytest.mark.parametrize("label", LABELS)
    def test_del_returns_the_label_to_empty(self, label):
        """One more door. A plain attribute could be deleted, after which
        the next read raised; the property's deleter resets to ""."""
        ts = _ts()
        setattr(ts, label, "Heart Rate")
        delattr(ts, label)
        assert getattr(ts, label) == ""
        delattr(ts, label)   # idempotent: nothing to remove is not an error
        assert getattr(ts, label) == ""

    def test_the_attribute_setter_does_not_re_case(self):
        """#56's rule is untouched: the constructor upper-cases its own
        argument, and nothing else rewrites a name someone chose."""
        ts = _ts()
        ts.signal_name = "Heart Rate"
        assert ts.signal_name == "Heart Rate"
        assert baseTs(np.arange(3.0), np.arange(3.0), signal_name="hr").signal_name == "HR"


class TestTheRegistryAndPropagation:
    """The public names stay in `_metadata`; propagation runs the setter."""

    @pytest.mark.parametrize("label", LABELS)
    def test_public_name_is_the_registered_one(self, label):
        assert label in TimeSeriesData._metadata
        assert "_" + label not in TimeSeriesData._metadata

    @pytest.mark.parametrize("label", LABELS)
    def test_pickle_round_trip_keeps_the_value(self, label):
        ts = _ts()
        setattr(ts, label, "Heart Rate")
        back = pickle.loads(pickle.dumps(ts))
        assert getattr(back, label) == "Heart Rate"

    @pytest.mark.parametrize("label", LABELS)
    def test_a_legacy_pickle_carrying_none_restores_as_empty(self, label):
        """A blob written before this change can hold `None` under the public
        name - #33 stopped it propagating but not from being stored. pandas'
        __setstate__ assigns each `_metadata` entry with object.__setattr__,
        which reaches the setter."""
        ts = _ts()
        state = ts.__getstate__()
        assert label in state
        state[label] = None
        back = TimeSeriesData.__new__(TimeSeriesData)
        back.__setstate__(state)
        assert getattr(back, label) == ""

    @pytest.mark.parametrize("derive", [
        pytest.param(lambda ts: ts.iloc[:5], id="finalize"),
        pytest.param(lambda ts: ts.copy(), id="copy_deep"),
        pytest.param(lambda ts: ts.copy(deep=False), id="copy_shallow"),
        pytest.param(lambda ts: ts + 1, id="arithmetic"),
        pytest.param(lambda ts: ts.zscale(), id="create_new_with_data"),
        pytest.param(lambda ts: ts.head(3), id="head"),
        pytest.param(lambda ts: ts.dropna(), id="dropna"),
        pytest.param(lambda ts: copy.deepcopy(ts), id="deepcopy"),
    ])
    def test_a_name_survives_derivation_through_the_property(self, derive):
        ts = _ts()
        ts.signal_name = "Heart Rate"
        assert derive(ts).signal_name == "Heart Rate"

    def test_a_fresh_object_reads_empty_before_anything_is_assigned(self):
        """The getter defaults rather than raising: pandas can build a
        subclass instance without running __init__ and finalize it later."""
        bare = TimeSeriesData.__new__(TimeSeriesData)
        assert bare.signal_name == ""
        assert bare.last_process == ""
