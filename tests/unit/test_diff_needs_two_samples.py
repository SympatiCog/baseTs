"""utils.diff and diff_ts refuse a series with fewer than two samples (#89).

`np.diff` of zero or one sample is empty. With `zeropad=False` that empty
array came back as an empty series, quietly; with `zeropad=True` the
padding read `d[0]` off it and raised a bare `IndexError` ("index 0 is out
of bounds for axis 0 with size 0"). The two branches disagreed on whether
a degenerate input is an error, and the one that was loud was loud by
accident.

Decided here: a first difference needs two samples, so both branches
raise `ValidationError` (a `ValueError`) naming the precondition, for
n=0 and n=1, through the free function and the method. The alternative -
an empty result on both branches - cannot honour `zeropad=True`'s own
contract (the input's length and index) without inventing a value, and
the family's other degenerate inputs are refused with a diagnosis rather
than returned empty (#62). `dediff` is unchanged: a cumulative sum of an
empty series is empty, and of one sample is that sample.
"""

import numpy as np
import pytest

from baseTs import baseTs
from baseTs.utils import ValidationError, dediff, diff

SHORT = [np.array([]), np.array([1.0])]
SHORT_IDS = ["n=0", "n=1"]


def _ts(values):
    return baseTs(values, np.arange(len(values)) / 10.0, freq=10.0)


class TestFewerThanTwoSamplesIsRefused:

    @pytest.mark.parametrize("zeropad", [False, True], ids=["plain", "zeropad"])
    @pytest.mark.parametrize("values", SHORT, ids=SHORT_IDS)
    def test_the_free_function_raises_the_precondition(self, values, zeropad):
        with pytest.raises(ValidationError, match="at least two samples") as info:
            diff(_ts(values), zeropad=zeropad)
        assert f"has {len(values)}" in str(info.value)

    @pytest.mark.parametrize("zeropad", [False, True], ids=["plain", "zeropad"])
    @pytest.mark.parametrize("values", SHORT, ids=SHORT_IDS)
    def test_it_is_a_value_error_for_callers_that_catch_that(self, values, zeropad):
        with pytest.raises(ValueError):
            diff(_ts(values), zeropad=zeropad)

    @pytest.mark.parametrize("zeropad", [False, True], ids=["plain", "zeropad"])
    @pytest.mark.parametrize("inplace", [False, True], ids=["copy", "inplace"])
    @pytest.mark.parametrize("values", SHORT, ids=SHORT_IDS)
    def test_the_method_raises_the_same_message_and_leaves_the_series_alone(
            self, values, zeropad, inplace):
        ts = _ts(values)
        before = ts.copy()

        with pytest.raises(ValidationError, match="at least two samples"):
            ts.diff_ts(zeropad=zeropad, inplace=inplace)

        np.testing.assert_array_equal(ts.values, before.values)
        assert list(ts.history) == list(before.history)


class TestTwoSamplesIsTheBoundary:

    @pytest.mark.parametrize("zeropad, expected", [(False, [2.0]), (True, [2.0, 2.0])],
                             ids=["plain", "zeropad"])
    def test_two_samples_give_one_difference(self, zeropad, expected):
        out = diff(_ts(np.array([1.0, 3.0])), zeropad=zeropad)
        np.testing.assert_array_equal(out.values, expected)


class TestDediffIsUntouched:

    @pytest.mark.parametrize("values", SHORT, ids=SHORT_IDS)
    def test_a_short_series_still_sums(self, values):
        out = dediff(_ts(values))
        np.testing.assert_array_equal(out.values, np.cumsum(values))
