"""A length-changing `ts.data = x` resamples over the span it has (#65).

The rule. When the new array has a different length, the index is rebuilt as
`linspace(first, last, n)` - the grid `interpto_samples` builds, the same
series resampled over the same span. That needs a span, and a series with
fewer than two samples has none. Before this change such a series invented
one: on a single sample `first == last`, so every replacement timestamp was
identical and the object silently acquired a fully duplicated index; on an
empty series it minted `0, 1, ..., n-1`, a 1 Hz grid nobody asked for. Both
now refuse, naming the remedy, and leave the object untouched.

Shrinking to empty is not refused: nothing is placed, so no span is needed.

Every length-changing method in the package (`diff_ts`, `remove_outliers`,
`interpto_samples`, ...) assigns `data` first and `times` second, so the
resampled index is a transient those methods overwrite - and the `times`
setter alone rejects a length mismatch, so the two-step is the only route a
caller has. The rule therefore only ever bites where the transient would have
been *kept*: a caller who changes the length and does not supply times.
"""
import numpy as np
import pytest

from baseTs import baseTs
from baseTs.utils import ValidationError

REFUSAL = "fewer than two samples"


def one_sample(**kwargs) -> baseTs:
    return baseTs(np.array([1.0]), times=np.array([2.0]), **kwargs)


def empty() -> baseTs:
    return baseTs(np.array([]), times=np.array([]))


class TestGrowingASeriesWithNoSpanIsRefused:

    def test_one_sample_series_refuses(self):
        ts = one_sample()
        with pytest.raises(ValidationError, match=REFUSAL):
            ts.data = np.array([1.0, 2.0, 3.0])

    def test_empty_series_refuses(self):
        ts = empty()
        with pytest.raises(ValidationError, match=REFUSAL):
            ts.data = np.array([1.0, 2.0, 3.0])

    def test_empty_series_refuses_even_a_single_sample(self):
        """One sample still has to be placed somewhere."""
        ts = empty()
        with pytest.raises(ValidationError, match=REFUSAL):
            ts.data = np.array([1.0])

    def test_a_declared_rate_does_not_change_the_answer(self):
        """The rule is about the span; a rate is not a span.

        Pinned so that changing it is an edit to a stated rule rather than
        a drift: a declared rate could plausibly build the grid the
        constructor builds, and if that is ever wanted it should be decided,
        not discovered.
        """
        ts = baseTs(np.array([1.0]), freq=100.0)
        with pytest.raises(ValidationError, match=REFUSAL):
            ts.data = np.array([1.0, 2.0, 3.0])

    def test_the_refusal_is_a_value_error(self):
        """`except ValueError` is the family's promised catch."""
        ts = one_sample()
        with pytest.raises(ValueError):
            ts.data = np.array([1.0, 2.0, 3.0])

    def test_the_refusal_leaves_the_object_untouched(self):
        ts = one_sample(signal_name="sig")
        ts.name = "kept"
        with pytest.raises(ValidationError):
            ts.data = np.array([1.0, 2.0, 3.0])
        assert ts.data.tolist() == [1.0]
        assert ts.times.tolist() == [2.0]
        assert ts.signal_name == "SIG"
        assert ts.name == "kept"

    def test_the_message_names_both_remedies_and_both_run(self):
        """An error that names a remedy is code; the remedy must run."""
        ts = one_sample()
        new = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValidationError) as caught:
            ts.data = new
        message = str(caught.value)
        assert "times=" in message
        assert "freq=" in message

        by_times = baseTs(new, times=np.array([2.0, 2.5, 3.0]))
        by_rate = baseTs(new, freq=2.0)
        for built in (by_times, by_rate):
            assert len(built) == 3
            assert not built.index.has_duplicates

    def test_the_message_says_what_the_caller_asked_for(self):
        ts = one_sample()
        with pytest.raises(ValidationError, match=r"3 samples.*series of 1"):
            ts.data = np.array([1.0, 2.0, 3.0])


class TestWhatIsStillAllowed:

    def test_same_length_on_a_one_sample_series_keeps_the_index(self):
        ts = one_sample()
        ts.data = np.array([5.0])
        assert ts.data.tolist() == [5.0]
        assert ts.times.tolist() == [2.0]

    def test_same_length_keeps_a_non_uniform_index_verbatim(self):
        """Pinned because a mutant that resampled the same-length path too
        survived every uniform-grid test: on a uniform index `linspace`
        reproduces the timestamps, so only an irregular one can tell."""
        irregular = np.array([0.0, 0.1, 0.35, 0.4, 1.0])
        ts = baseTs(np.arange(5.0), times=irregular)
        ts.data = np.arange(5.0) * 2
        np.testing.assert_array_equal(ts.times, irregular)

    def test_shrinking_a_one_sample_series_to_empty(self):
        ts = one_sample()
        ts.data = np.array([])
        assert len(ts) == 0
        assert len(ts.times) == 0

    def test_two_samples_resample_over_their_span(self):
        ts = baseTs(np.array([1.0, 2.0]), times=np.array([0.0, 1.0]))
        ts.data = np.arange(5.0)
        np.testing.assert_array_equal(ts.times, np.linspace(0.0, 1.0, 5))

    def test_a_longer_series_resamples_over_its_span(self):
        ts = baseTs(np.arange(10.0), times=np.arange(10) / 10.0)
        ts.data = np.arange(20.0)
        np.testing.assert_allclose(ts.times, np.linspace(0.0, 0.9, 20))
        assert not ts.index.has_duplicates

    @pytest.mark.parametrize("n_old", [2, 3, 7])
    @pytest.mark.parametrize("n_new", [0, 1, 2, 5, 11])
    def test_a_unique_index_never_becomes_a_duplicated_one(self, n_old, n_new):
        """The property the single-sample case violated, over a sweep."""
        ts = baseTs(np.arange(float(n_old)), times=np.arange(n_old) * 0.25)
        ts.data = np.arange(float(n_new))
        assert len(ts) == n_new
        assert not ts.index.has_duplicates

    def test_a_declared_rate_expires_with_the_span_it_was_declared_on(self):
        """As everywhere since #38: the token no longer matches, so it derives."""
        ts = baseTs(np.arange(10.0), freq=10.0)
        ts.data = np.arange(20.0)
        assert ts.freq == pytest.approx(19 / 0.9)


class TestTheTwoStepRouteStillWorks:
    """Package methods assign data then times; the transient must not bite."""

    def test_diff_ts_on_two_samples(self):
        ts = baseTs(np.array([1.0, 4.0]), times=np.array([0.0, 1.0]))
        out = ts.diff_ts()
        assert out.data.tolist() == [3.0]
        assert out.times.tolist() == [1.0]

    def test_diff_ts_on_one_sample_gives_an_empty_series(self):
        out = one_sample().diff_ts()
        assert len(out) == 0

    def test_remove_outliers_on_one_sample(self):
        out = one_sample().remove_outliers()
        assert len(out) == 1

    def test_apply_function_that_grows_a_one_sample_series_is_refused(self):
        """The one package route that could keep the transient.

        `apply_function` never touches `times`, so on a single sample a
        length-changing function used to leave a duplicated index behind;
        the refusal is the same one the setter gives.
        """
        with pytest.raises(ValidationError, match=REFUSAL):
            one_sample().apply_function(lambda d: np.repeat(d, 3))

    def test_apply_function_that_grows_a_longer_series_resamples(self):
        ts = baseTs(np.array([1.0, 2.0]), times=np.array([0.0, 1.0]))
        out = ts.apply_function(lambda d: np.repeat(d, 2))
        np.testing.assert_array_equal(out.times, np.linspace(0.0, 1.0, 4))
