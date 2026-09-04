"""The signal name's case follows one rule on every derivation (issue #56).

The constructor has always upper-cased the name it is handed, and nothing
else ever did. That left a split: a derivation that copied the parent's name
preserved its case, while one that re-minted it through the constructor
upper-cased it a second time. `ts.iloc[:5]` and `ts.zscale()` disagreed about
the name of the same series, and every plot title is built from it.

The rule now: the constructor normalises its *own argument*; a derived object
carries the parent's name unchanged, whichever path built it. A mixed-case
name can only arrive by assignment after construction, which is what every
case below does.

Out of scope, and not pinned either way: `plotting.lag_plot` upper-cases the
name when it builds its *title*, which is #61's neighbourhood; and the free
functions in utils.py and `LowessOutlierFilter.filter` drop the name outright,
which is #66's.
"""
import numpy as np
import pytest

from baseTs import baseTs
from baseTs.series import TimeSeriesData

MIXED = "Heart Rate"


def _named(name=MIXED):
    ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
    ts.signal_name = name
    return ts


DERIVATIONS = [
    pytest.param(lambda ts: ts.iloc[:5], id="finalize"),
    pytest.param(lambda ts: ts.head(3), id="head"),
    pytest.param(lambda ts: ts.copy(), id="copy_deep"),
    pytest.param(lambda ts: ts.copy(deep=False), id="copy_shallow"),
    pytest.param(lambda ts: ts.zscale(), id="create_new_with_data"),
    pytest.param(lambda ts: ts.detrend(), id="create_new_with_data_detrend"),
    pytest.param(lambda ts: ts.rolling_mean(3), id="rolling_mean"),
    pytest.param(lambda ts: ts + 1, id="arith"),
    pytest.param(lambda ts: 1 + ts, id="arith_reflected"),
    pytest.param(lambda ts: ts * ts, id="arith_two_operands"),
    pytest.param(lambda ts: ts.to_basetseries(), id="to_basetseries"),
    pytest.param(lambda ts: baseTs(ts), id="convert_basets"),
    pytest.param(lambda ts: TimeSeriesData(ts), id="convert_timeseriesdata"),
]


class TestDerivedObjectsKeepTheParentsCase:

    @pytest.mark.parametrize("derive", DERIVATIONS)
    def test_a_mixed_case_name_survives_a_derivation(self, derive):
        assert derive(_named()).signal_name == MIXED

    @pytest.mark.parametrize("derive", DERIVATIONS)
    def test_a_lower_case_name_survives_a_derivation(self, derive):
        """Distinct from the mixed case: `.title()` or `.capitalize()` in
        place of a verbatim copy would pass the case above and fail this."""
        assert derive(_named("hr")).signal_name == "hr"

    def test_two_derivations_agree_about_the_name(self):
        """The live symptom: the same series titled two ways."""
        ts = _named()
        assert ts.iloc[:5].signal_name == ts.zscale().signal_name

    def test_preserve_metadata_false_still_carries_the_name(self):
        """The name was never part of the metadata that flag withholds."""
        ts = _named()
        derived = ts._create_new_with_data(ts.values * 2, preserve_metadata=False)
        assert derived.signal_name == MIXED

    @pytest.mark.parametrize("derive", DERIVATIONS)
    def test_a_none_name_still_becomes_empty_on_every_path(self, derive):
        """Copying the name verbatim must not reopen what #33 closed: the
        constructor used to normalise a None on the re-minting paths, and
        now each of them has to reach _detach_shared_metadata or normalise
        by hand. Parametrised over every derivation, not only the ones this
        fix touched: review round 3 (glm-5.3) pointed out that the case pins
        covered thirteen paths and the None pin covered one."""
        assert derive(_named(None)).signal_name == ""

    def test_a_none_name_becomes_empty_even_without_preserved_metadata(self):
        """preserve_metadata=False skips _detach_shared_metadata, so the copy
        is the only normaliser on the path. A mutant that copied the raw
        value survived the case above and is killed by this one."""
        ts = _named(None)
        derived = ts._create_new_with_data(ts.values, preserve_metadata=False)
        assert derived.signal_name == ""


class TestTheConstructorStillNormalisesItsOwnArgument:
    """The other half of the rule, pinned so a fix cannot quietly drop it."""

    def test_construction_from_arrays_upper_cases(self):
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0, signal_name=MIXED)
        assert ts.signal_name == "HEART RATE"

    def test_an_explicit_name_on_a_derivation_is_normalised(self):
        """A name the caller passes is a constructor argument, not an
        inheritance, so it takes the constructor's rule."""
        ts = _named()
        derived = ts._create_new_with_data(ts.values, signal_name="Other")
        assert derived.signal_name == "OTHER"

    def test_an_explicit_name_on_a_conversion_is_normalised(self):
        assert baseTs(_named(), signal_name="Other").signal_name == "OTHER"
