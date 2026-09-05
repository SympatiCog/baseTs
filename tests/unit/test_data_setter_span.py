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

REFUSAL = "no span"


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

    def test_two_samples_at_one_timestamp_refuse(self):
        """The rule is about the span, and sample count was only its proxy.

        Review round 1 (codex + agy): a two-sample index whose first and last
        timestamps coincide has no span either, and grew into a fully
        duplicated `linspace(x, x, n)` - the hazard #65 was opened to kill,
        one sample further along.
        """
        ts = baseTs(np.array([1.0, 2.0]), times=np.array([5.0, 5.0]))
        with pytest.raises(ValidationError, match=REFUSAL):
            ts.data = np.array([1.0, 2.0, 3.0])

    def test_a_longer_index_whose_ends_coincide_refuses(self):
        ts = baseTs(np.array([1.0, 2.0, 3.0]), times=np.array([0.0, 1.0, 0.0]))
        with pytest.raises(ValidationError, match=REFUSAL):
            ts.data = np.arange(5.0)

    def test_a_nan_endpoint_refuses(self):
        """`nan == nan` is False, so an equality test alone let a NaN
        endpoint through to `linspace(nan, 1.0, 5)` - four invented NaN
        labels and one real one (round 2, glm; measured on `main`)."""
        ts = baseTs(np.array([1.0, 2.0]), times=np.array([np.nan, 1.0]))
        with pytest.raises(ValidationError, match="unmeasurable"):
            ts.data = np.arange(5.0)

    @pytest.mark.parametrize("source, word", [
        (empty, "empty"),
        (one_sample, "single sample"),
        (lambda: baseTs(np.array([1.0, 2.0]), times=np.array([5.0, 5.0])),
         "coincide"),
        (lambda: baseTs(np.array([1.0, 2.0]), times=np.array([np.nan, 1.0])),
         "unmeasurable"),
    ], ids=['empty', 'one-sample', 'zero-span', 'nan-endpoint'])
    def test_the_message_says_why_for_each_kind_of_source(self, source, word):
        ts = source()
        with pytest.raises(ValidationError, match=word):
            ts.data = np.array([1.0, 2.0, 3.0])

    def test_a_declared_rate_does_not_change_the_answer(self):
        """The rule is about the span; a rate is not a span.

        Pinned so that changing it is an edit to a stated rule rather than
        a drift: a declared rate could plausibly build the grid the
        constructor builds, and if that is ever wanted it should be decided,
        not discovered.
        """
        ts = baseTs(np.array([1.0]), freq=100.0)
        assert ts.freq == 100.0            # the declaration is attached
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

    def test_shrinking_a_zero_span_index_keeps_its_one_label(self):
        """A no-span index cannot grow; it can shrink, and what it keeps are
        labels it already had. Round 2 (glm): refusing the shrink too broke
        `diff_ts` on two samples at one timestamp, which `main` handled."""
        ts = baseTs(np.array([1.0, 2.0, 3.0]), times=np.array([5.0, 5.0, 5.0]))
        ts.data = np.array([1.0, 2.0])
        assert ts.times.tolist() == [5.0, 5.0]

    def test_shrinking_a_nan_endpoint_index_keeps_its_labels(self):
        ts = baseTs(np.array([1.0, 2.0, 3.0]), times=np.array([np.nan, 0.5, 1.0]))
        ts.data = np.array([1.0, 2.0])
        assert np.isnan(ts.times[0]) and ts.times[1] == 0.5

    def test_shrinking_a_one_sample_series_to_empty(self):
        ts = one_sample()
        ts.data = np.array([])
        assert len(ts) == 0
        assert len(ts.times) == 0

    def test_shrinking_a_non_numeric_index_to_empty_keeps_its_dtype(self):
        """Incidental: on `main` this crashed inside numpy (`linspace` on
        `Timestamp` endpoints with n=0). Review round 1 measured it on a
        DatetimeIndex; since #100 the constructor converts one to seconds,
        so an object index of strings is what still exercises the slice."""
        ts = baseTs(np.arange(3.0), times=np.array(['a', 'b', 'c'], dtype=object))
        before = ts.index.dtype       # object, or pandas 3's `str`
        ts.data = np.array([])
        assert len(ts) == 0
        assert ts.index.dtype == before
        assert ts.index.dtype != np.float64

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
        """Regression guard over spanning sources: true on `main` too. The
        no-span cases are the refusal tests above, not this sweep."""
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

    def test_diff_ts_on_two_samples_at_one_timestamp(self):
        """The shrinker round 2 (glm) caught: `main` gave `[3.0] @ [5.0]`."""
        ts = baseTs(np.array([1.0, 4.0]), times=np.array([5.0, 5.0]))
        out = ts.diff_ts()
        assert out.data.tolist() == [3.0]
        assert out.times.tolist() == [5.0]

    def test_diff_ts_on_one_sample_is_refused_before_the_two_step_route_runs(self):
        """Until #89 this pinned an empty result - the shrink-to-empty leg of
        the route. A first difference now needs two samples, so the method
        raises at utils.diff and the setter never sees the transient."""
        ts = one_sample()
        before = ts.data.tolist()
        with pytest.raises(ValueError, match="at least two samples"):
            ts.diff_ts()
        assert ts.data.tolist() == before

    def test_time_slice_inplace_shrinks_a_one_sample_series_to_empty(self):
        """The shrink-to-empty leg of the route, which the diff_ts pin used
        to carry (#89 review): time_slice(inplace=True) assigns data then
        times, and a window holding no sample takes it to zero length."""
        ts = one_sample()
        out = ts.time_slice(start_time=99.0, inplace=True)
        assert out is ts
        assert len(ts) == 0
        assert ts.times.tolist() == []

    def test_remove_outliers_on_one_sample(self):
        out = one_sample().remove_outliers()
        assert len(out) == 1

    @pytest.mark.parametrize("source", [
        lambda: one_sample(),
        lambda: baseTs(np.array([1.0, 2.0]), times=np.array([5.0, 5.0])),
    ], ids=['one-sample', 'zero-span'])
    def test_interpto_samples_refuses_a_degenerate_source_at_its_own_door(
            self, source):
        """The one package method that grew a no-span source.

        Review round 1 (codex + agy): `interpto_samples` builds its own
        `linspace` over the source span - on `main` a one-sample source came
        back as five copies of one value at five copies of one timestamp -
        and its `self.data = ...` line then hit the setter's refusal, whose
        message talks about `ts.data` and offers remedies for an assignment
        the caller never wrote. It now checks the precondition `interpto_hz`
        already checks, in its own words, before anything runs.
        """
        with pytest.raises(ValueError, match="degenerate") as caught:
            source().interpto_samples(5)
        assert "ts.data" not in str(caught.value)
        assert "5 samples" in str(caught.value)

    @pytest.mark.parametrize("resample", [
        lambda ts: ts.interpto_hz(10.0),
        lambda ts: ts.interpto_samples(5),
    ], ids=['interpto_hz', 'interpto_samples'])
    def test_an_unmeasurable_span_is_refused_not_leaked(self, resample):
        """The shared precondition's non-finite arm and its TypeError catch.

        `duration()` on a non-numeric index raises TypeError (`'c' - 'a'`
        has no meaning; a DatetimeIndex used to be the case, until #100
        converted it to seconds at the constructor); the helper turns that
        into the same degenerate-span refusal with `duration nan` rather
        than leaking the conversion error. Mutation testing found neither
        arm pinned for `interpto_hz` before the extraction; both resamplers
        pin them now.
        """
        ts = baseTs(np.arange(3.0), times=np.array(['a', 'b', 'c'], dtype=object))
        with pytest.raises(ValueError, match="degenerate \\(duration nan\\)"):
            resample(ts)

    def test_each_resampler_says_why_the_span_defeats_it_in_its_own_words(self):
        """One check, two consequences; the wordings must not be swapped."""
        ts = one_sample()
        with pytest.raises(ValueError, match="stamping the requested rate"):
            ts.interpto_hz(10.0)
        with pytest.raises(ValueError, match="spread the new grid"):
            ts.interpto_samples(5)

    def test_interpto_samples_still_works_on_a_two_sample_span(self):
        ts = baseTs(np.array([0.0, 4.0]), times=np.array([0.0, 1.0]))
        out = ts.interpto_samples(5)
        np.testing.assert_allclose(out.data, [0.0, 1.0, 2.0, 3.0, 4.0])
        np.testing.assert_allclose(out.times, np.linspace(0.0, 1.0, 5))

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
