"""A DatetimeIndex becomes seconds since its first stamp at the constructor (#100).

The package keeps one time base: a float index of seconds. A `DatetimeIndex`
handed to the constructor (or to the `times` setter) is converted at that
door - the index becomes seconds since its first stamp, and that stamp is
recorded as `ts_offset`, in epoch seconds, with `has_timestamp_offset`
True. Every method then reads the index it has always read, and the
`datetimes` accessor rebuilds the stamps from the pair.

The meaning this gives `ts_offset` - the origin the seconds are counted
from - is the one `set_timestamp_offset` now records too. It used to move
the index by the offset *and* record it, which under this meaning counted
the offset twice; it records only.

Measured on `main` at 0cbffcb before this change: such a series derived
`freq` as NaN, and `duration()`, `get_statistics()`, `resample()` and
`diff_ts()` raised on it.
"""

import datetime
import pickle
from decimal import Decimal
from fractions import Fraction

import numpy as np
import pandas as pd
import pytest

from baseTs import TimeSeriesData, baseTs, from_df

DAILY = pd.date_range('2023-01-01', periods=365, freq='D')
FAST = pd.date_range('2023-01-01 12:00:00', periods=1000, freq='10ms')   # 100 Hz


def seconds_since_first(index):
    return np.asarray((index - index[0]).total_seconds(), dtype=float)


def epoch_seconds(stamp):
    return stamp.value / 1e9


def two_tone(n=len(FAST)):
    t = np.arange(n) / 100.0
    return np.sin(2 * np.pi * 3.0 * t) + 0.3 * np.sin(2 * np.pi * 17.0 * t)


def stamped(index=FAST, data=None):
    data = two_tone(len(index)) if data is None else data
    return baseTs(data, times=index)


def numeric_twin(index=FAST, data=None):
    data = two_tone(len(index)) if data is None else data
    return baseTs(data, times=seconds_since_first(index))


class TestTheConstructorConvertsAStampedIndex:

    def test_the_index_is_float_seconds_from_zero(self):
        ts = stamped(DAILY, np.random.default_rng(0).standard_normal(365))
        assert ts.index.dtype == np.float64
        assert not isinstance(ts.index, pd.DatetimeIndex)
        np.testing.assert_array_equal(ts.times, np.arange(365) * 86400.0)

    def test_the_first_stamp_is_the_origin_in_epoch_seconds(self):
        ts = stamped(DAILY, np.zeros(365))
        assert ts.ts_offset == epoch_seconds(DAILY[0]) == 1672531200.0
        assert ts.has_timestamp_offset is True

    def test_the_rate_derives(self):
        assert stamped(DAILY, np.zeros(365)).freq == 1 / 86400
        assert stamped(FAST).freq == pytest.approx(100.0)

    def test_a_declared_rate_is_still_honoured(self):
        ts = baseTs(np.arange(5.0), pd.date_range('2024', periods=5, freq='10ms'),
                    freq=100.0)
        assert ts.freq == 100.0

    @pytest.mark.parametrize("spelling", [
        lambda: FAST,
        lambda: FAST.values,                          # datetime64 ndarray
        lambda: list(FAST),                           # Timestamp objects
        lambda: pd.Series(np.arange(len(FAST)), index=FAST).index,
    ], ids=['DatetimeIndex', 'datetime64_ndarray', 'list_of_Timestamps', 'Series_index'])
    def test_every_spelling_of_a_stamped_index_converts(self, spelling):
        ts = baseTs(two_tone(), times=spelling())
        np.testing.assert_array_equal(ts.times, seconds_since_first(FAST))
        assert ts.ts_offset == epoch_seconds(FAST[0])

    def test_the_index_alias_converts_too(self):
        ts = baseTs(two_tone(), index=FAST)
        assert ts.ts_offset == epoch_seconds(FAST[0])

    def test_a_series_with_a_stamped_index_converts(self):
        ts = baseTs(pd.Series(two_tone(), index=FAST))
        np.testing.assert_array_equal(ts.times, seconds_since_first(FAST))
        assert ts.has_timestamp_offset is True

    def test_the_superclass_converts_on_its_own(self):
        """TimeSeriesData is the door; baseTs only rides through it."""
        tsd = TimeSeriesData(two_tone(), index=FAST)
        assert tsd.index.dtype == np.float64
        assert tsd.ts_offset == epoch_seconds(FAST[0])
        assert tsd.has_timestamp_offset is True

    def test_the_origin_is_the_first_stamp_not_the_earliest(self):
        """Seconds are counted from index[0]; an unsorted index goes negative.

        The rule is stated rather than sorted-for: the numeric path keeps
        an unsorted index as given, and this one does the same.
        """
        idx = pd.DatetimeIndex(['2023-01-02', '2023-01-01', '2023-01-03'])
        ts = baseTs(np.arange(3.0), times=idx)
        np.testing.assert_array_equal(ts.times, [0.0, -86400.0, 86400.0])
        assert ts.ts_offset == epoch_seconds(idx[0])

    def test_an_empty_stamped_index_has_no_origin(self):
        ts = baseTs(np.array([]), times=pd.DatetimeIndex([]))
        assert len(ts) == 0
        assert ts.index.dtype == np.float64
        assert (ts.ts_offset, ts.has_timestamp_offset) == (0, False)

    def test_an_interior_nat_becomes_nan_seconds(self):
        """Parity with the numeric index, which admits NaN."""
        idx = pd.DatetimeIndex(['2023-01-01', 'NaT', '2023-01-03'])
        ts = baseTs(np.arange(3.0), times=idx)
        assert np.isnan(ts.times[1])
        np.testing.assert_array_equal(ts.times[[0, 2]], [0.0, 172800.0])

    def test_a_nat_first_stamp_is_refused(self):
        """The origin has to be a stamp; NaT would make every second NaN and
        the offset NaN with it, a pair nothing downstream can read."""
        idx = pd.DatetimeIndex(['NaT', '2023-01-02'])
        with pytest.raises(ValueError, match="first stamp is NaT"):
            baseTs(np.arange(2.0), times=idx)


class TestATimezoneAwareIndexIsAnInstant:
    """Recorded as the UTC instant; the zone name is kept nowhere.

    An aware stamp *is* an instant, and epoch seconds identify it exactly,
    so nothing is lost but the display zone. The accessor gives naive UTC
    back; `.tz_localize('UTC').tz_convert(zone)` restores the zone.
    """

    AWARE = pd.date_range('2023-03-12 00:00', periods=48, freq='h', tz='US/Eastern')

    def test_seconds_are_elapsed_seconds_across_the_dst_change(self):
        ts = baseTs(np.arange(48.0), times=self.AWARE)
        np.testing.assert_array_equal(ts.times, np.arange(48) * 3600.0)

    def test_the_origin_is_the_utc_instant(self):
        ts = baseTs(np.arange(48.0), times=self.AWARE)
        assert ts.ts_offset == epoch_seconds(self.AWARE[0])
        assert ts.ts_offset == epoch_seconds(self.AWARE.tz_convert(None)[0])

    def test_the_accessor_returns_naive_utc(self):
        ts = baseTs(np.arange(48.0), times=self.AWARE)
        assert ts.datetimes.tz is None
        assert ts.datetimes.equals(self.AWARE.tz_convert(None))
        assert ts.datetimes.tz_localize('UTC').tz_convert('US/Eastern').equals(self.AWARE)


class TestATimedeltaIndexIsDurations:

    DELTAS = pd.timedelta_range(0, periods=5, freq='10ms')

    def test_it_converts_to_seconds_with_no_origin(self):
        ts = baseTs(np.arange(5.0), times=self.DELTAS)
        np.testing.assert_array_equal(ts.times, np.arange(5) * 0.01)
        assert (ts.ts_offset, ts.has_timestamp_offset) == (0, False)

    def test_it_accepts_an_explicit_origin(self):
        """Durations carry no origin, so a caller may name one."""
        ts = baseTs(np.arange(5.0), times=self.DELTAS, ts_offset=1672531200.0)
        assert (ts.ts_offset, ts.has_timestamp_offset) == (1672531200.0, True)
        assert ts.datetimes[0] == pd.Timestamp('2023-01-01')

    def test_a_nonzero_start_is_kept_as_is(self):
        """Seconds are the durations themselves, not durations since the first."""
        ts = baseTs(np.arange(3.0), times=pd.to_timedelta([5, 6, 7], unit='s'))
        np.testing.assert_array_equal(ts.times, [5.0, 6.0, 7.0])


class TestAnExplicitOffsetAlongsideAStampedIndex:

    def test_is_refused_as_a_second_origin(self):
        with pytest.raises(ValueError, match="carries its own origin"):
            baseTs(two_tone(), times=FAST, ts_offset=5.0)

    def test_is_refused_through_from_df_too(self):
        df = pd.DataFrame({'time': FAST, 'value': two_tone()})
        with pytest.raises(ValueError, match="carries its own origin"):
            from_df(df, ts_offset=5.0)

    def test_is_refused_by_the_superclass(self):
        with pytest.raises(ValueError, match="carries its own origin"):
            TimeSeriesData(two_tone(), index=FAST, ts_offset=5.0)

    def test_clearing_the_flag_keeps_the_seconds_and_drops_the_origin(self):
        """A caller asking for relative seconds only. Coherent, so allowed."""
        ts = baseTs(two_tone(), times=FAST, has_timestamp_offset=False)
        np.testing.assert_array_equal(ts.times, seconds_since_first(FAST))
        assert (ts.ts_offset, ts.has_timestamp_offset) == (0, False)


class TestTheDatetimesAccessor:

    @pytest.mark.parametrize("index", [
        DAILY,
        FAST,
        pd.date_range('2023-01-01 12:34:56', periods=1000, freq='ms'),
        pd.date_range('2023-01-01', periods=1000, freq='us'),
        pd.date_range('2023-01-01 00:00:00.123', periods=100, freq='ms'),
        pd.date_range('2023-01-01 00:00:00.123456', periods=100, freq='ms'),
        pd.date_range('1900-01-01', periods=100, freq='D'),
        pd.date_range('1960-05-05 01:02:03.004005', periods=100, freq='D'),
        pd.date_range('2200-01-01', periods=100, freq='h'),
        pd.DatetimeIndex(['2023-01-01 00:00:00.5', '2023-01-01 00:00:01.25',
                          '2023-01-02 03:04:05.000001']),
        pd.DatetimeIndex(['2023-01-02', '2023-01-01', '2023-01-03']),
        pd.DatetimeIndex(['2023-01-01 00:00:00.000001', '2023-07-20 12:34:56.789012']),
        pd.DatetimeIndex(['2023-01-01 00:00:00.000001', '2199-07-20 12:34:56.789012']),
        pd.DatetimeIndex(['2023-01-01']).append(
            pd.date_range('2023-01-01', periods=3, freq='ns') + pd.Timedelta(days=97)),
        pd.DatetimeIndex(['2023-01-01', 'NaT', '2023-01-03']),
    ], ids=['daily', '10ms', 'ms', 'us', 'ms_start', 'us_start', '1900', 'pre_1970',
            '2200', 'irregular', 'unsorted', 'us_stamp_200_days_out',
            'us_stamp_176_years_out', 'ns_stamps_97_days_out', 'interior_nat'])
    def test_it_round_trips_the_original_index_exactly(self, index):
        """Exact whenever the first stamp lies on a microsecond and each
        later stamp is at microsecond resolution or coarser - at any span -
        or at nanosecond resolution within 2**23 s (97 days) of the
        origin. Those are the precisions a float64 second holds at those
        magnitudes; the origin is rebuilt at the microsecond because a
        float64 epoch in the 2020s resolves to ~2.4e-7 s, and the
        nanosecond digits of a finer origin are not in the float to begin
        with. A NaT comes back as NaT. (The 97-day nanosecond case keeps its
        origin at 2023-01-01 on purpose: built from the far stamps alone,
        its seconds were 0, 1 and 2 ns and the threshold mutant survived.)
        """
        ts = baseTs(np.arange(len(index), dtype=float), times=index)
        out = ts.datetimes
        assert isinstance(out, pd.DatetimeIndex)
        assert out.equals(index)
        assert out.isna().tolist() == index.isna().tolist()

    def test_a_nanosecond_origin_comes_back_to_within_a_microsecond(self):
        index = pd.date_range('2023-01-01 00:00:00.123456789', periods=10, freq='ms')
        ts = baseTs(np.arange(10.0), times=index)
        err = np.abs((ts.datetimes - index).total_seconds())
        assert err.max() < 5e-7
        assert err.max() > 0     # the pin is honest: this case is inexact

    def test_a_negative_sub_nanosecond_second_rounds_to_the_nearest_nanosecond(self):
        """Mutation found `floor` and `trunc` splits agree on every stamp
        (whole nanoseconds) and differ on one numeric second: -1.0000000005,
        exactly -1000000000.50000004 ns as a float, which `floor`'s rounded
        subtraction put at -1000000000. Only numeric times can hold it."""
        ts = baseTs(np.arange(2.0), [-1.0000000005, 0.0])
        ts.set_timestamp_offset(epoch_seconds(pd.Timestamp('2023-01-01')))
        assert ts.datetimes[0] == pd.Timestamp('2022-12-31 23:59:58.999999999')

    def test_a_nanosecond_stamp_beyond_97_days_comes_back_at_the_microsecond(self):
        """Past 2**23 s a float64 second's ulp exceeds a nanosecond, so the
        nanosecond digits are rounded away rather than reported as noise.
        97 days is 8.38e6 s, just inside; 97.1 days is just outside."""
        index = pd.DatetimeIndex(['2023-01-01', '2023-04-08 02:24:00.000000501'])   # 97.1 days
        ts = baseTs(np.arange(2.0), times=index)
        assert ts.datetimes[1] == pd.Timestamp('2023-04-08 02:24:00.000001')

    def test_a_second_beyond_the_stamp_range_is_refused_not_wrapped(self):
        """The int64 nanosecond product wrapped silently: 9.5e9 s came back
        as a date in 1686. pandas' own range is 1677-2262."""
        ts = baseTs(np.arange(2.0), [0.0, 9.5e9])
        ts.set_timestamp_offset(0.0)
        with pytest.raises(OverflowError, match="292 years"):
            ts.datetimes

    def test_it_raises_on_a_series_with_no_origin(self):
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        with pytest.raises(ValueError, match="no timestamp origin") as info:
            ts.datetimes
        assert "set_timestamp_offset" in str(info.value)

    def test_it_raises_on_a_durations_series(self):
        ts = baseTs(np.arange(5.0), times=pd.timedelta_range(0, periods=5, freq='s'))
        with pytest.raises(ValueError, match="no timestamp origin"):
            ts.datetimes

    def test_the_remedy_it_names_works(self):
        ts = baseTs(np.arange(3.0), [0.0, 0.5, 1.0])
        ts.set_timestamp_offset(1672531200.0)
        assert ts.datetimes.equals(pd.DatetimeIndex([
            '2023-01-01 00:00:00', '2023-01-01 00:00:00.5', '2023-01-01 00:00:01']))

    def test_an_offset_asserted_without_a_value_gives_the_epoch(self):
        """`has_timestamp_offset=True` with `ts_offset` 0 is a caller's own
        assertion (pinned elsewhere); the accessor reads it as origin 1970."""
        ts = baseTs(np.arange(3.0), [0.0, 1.0, 2.0], has_timestamp_offset=True)
        assert ts.datetimes[0] == pd.Timestamp('1970-01-01')

    def test_it_is_not_an_attribute_error(self):
        """A property raising AttributeError is invisible to hasattr and
        would fall into pandas' __getattr__; the refusal must be a
        ValueError so it surfaces where it happens."""
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        assert hasattr(type(ts), 'datetimes')
        with pytest.raises(ValueError):
            ts.datetimes


class TestSetTimestampOffsetRecordsTheOrigin:
    """It used to move the index by the offset and record it; the index
    stays put now. Under "seconds since the origin", moving it counted the
    offset twice: `datetimes` would have started at origin + offset."""

    def test_the_index_does_not_move(self):
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        ts.set_timestamp_offset(1.5)
        np.testing.assert_array_equal(ts.times, np.arange(10) / 10.0)
        assert (ts.ts_offset, ts.has_timestamp_offset) == (1.5, True)

    def test_the_history_entry_and_last_process_are_kept(self):
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        ts.set_timestamp_offset(1.5)
        assert ts.history[-1] == "Set timestamp offset to 1.5"
        assert ts.last_process == "_tso1.5"

    def test_a_second_call_replaces_rather_than_accumulates(self):
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        ts.set_timestamp_offset(1.5)
        ts.set_timestamp_offset(2.0)
        assert ts.ts_offset == 2.0
        np.testing.assert_array_equal(ts.times, np.arange(10) / 10.0)

    def test_a_declared_rate_survives_it(self):
        """Nothing about the index changes, so the declaration's token holds."""
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0, freq=999.0)
        ts.set_timestamp_offset(1.5)
        assert ts.freq == 999.0

    def test_it_rebases_a_stamped_series(self):
        ts = stamped(DAILY, np.zeros(365))
        ts.set_timestamp_offset(epoch_seconds(pd.Timestamp('2024-01-01')))
        assert ts.datetimes[0] == pd.Timestamp('2024-01-01')
        assert ts.datetimes[-1] == pd.Timestamp('2024-12-30')


class TestTheFourMethodsThatRaisedNowAgreeWithTheNumericTwin:
    """Same data on the same seconds: bit-identical results."""

    def test_duration(self):
        assert stamped().duration() == numeric_twin().duration() == 9.99

    def test_get_statistics(self):
        got, want = stamped().get_statistics(), numeric_twin().get_statistics()
        assert got == want
        assert got['duration'] == 9.99
        assert got['frequency'] == pytest.approx(100.0)

    def test_resample_keeps_the_origin(self):
        got, want = stamped().resample('100ms'), numeric_twin().resample('100ms')
        np.testing.assert_array_equal(got.data, want.data)
        np.testing.assert_array_equal(got.times, want.times)
        assert got.ts_offset == epoch_seconds(FAST[0])
        assert got.has_timestamp_offset is True
        assert got.datetimes[0] == FAST[0]

    def test_resample_bins_from_the_origin_not_the_calendar(self):
        """The seconds index is what is resampled, so a series starting at
        08:00 has day bins at 08:00, and a calendar-anchored rule ('W',
        'ME') is refused by pandas as it is on any seconds index."""
        idx = pd.date_range('2023-01-01 08:00', periods=48, freq='h')
        ts = baseTs(np.arange(48.0), times=idx)
        daily = ts.resample('D')
        assert daily.datetimes.equals(pd.DatetimeIndex(['2023-01-01 08:00',
                                                        '2023-01-02 08:00']))
        with pytest.raises(ValueError, match="fixed-duration"):
            ts.resample('W')

    def test_diff_ts(self):
        got, want = stamped().diff_ts(), numeric_twin().diff_ts()
        np.testing.assert_array_equal(got.data, want.data)
        np.testing.assert_array_equal(got.times, want.times)
        assert got.ts_offset == epoch_seconds(FAST[0])

    @pytest.mark.parametrize("entry", [
        lambda ts: ts.get_frequency_content(),
        lambda ts: ts.get_frequency_content(window='hann'),
        lambda ts: ts.compute_fft_power(),
        lambda ts: ts.get_peak_freq(),
        lambda ts: ts.relative_band_power(low_freq=2.0, high_freq=4.0),
    ], ids=['get_frequency_content', 'windowed', 'compute_fft_power', 'get_peak_freq',
            'relative_band_power'])
    def test_every_spectral_entry_point_with_the_derived_rate(self, entry):
        got, want = entry(stamped()), entry(numeric_twin())
        np.testing.assert_array_equal(np.asarray(got, dtype=object).ravel(),
                                      np.asarray(want, dtype=object).ravel())

    def test_info_prints(self, capsys):
        stamped().info()
        assert "Timestamp Offset" in capsys.readouterr().out


class TestTimeSliceTakesCalendarBounds:

    @pytest.fixture
    def daily(self):
        return stamped(DAILY, np.arange(365.0))

    def test_date_strings_select_the_same_rows_as_seconds(self, daily):
        by_date = daily.time_slice(start_time='2023-01-01', end_time='2023-01-31')
        by_secs = daily.time_slice(start_time=0.0, end_time=30 * 86400.0)
        np.testing.assert_array_equal(by_date.data, by_secs.data)
        np.testing.assert_array_equal(by_date.times, by_secs.times)
        assert len(by_date) == 31

    @pytest.mark.parametrize("bound", [
        pd.Timestamp('2023-01-31'),
        datetime.datetime(2023, 1, 31),
        datetime.date(2023, 1, 31),
        np.datetime64('2023-01-31'),
        '2023-01-31T00:00:00',
    ], ids=['Timestamp', 'datetime', 'date', 'datetime64', 'iso_string'])
    def test_every_datetime_like_bound_is_a_calendar_bound(self, daily, bound):
        assert len(daily.time_slice(end_time=bound)) == 31

    def test_an_aware_bound_is_an_instant(self, daily):
        bound = pd.Timestamp('2023-01-31 00:00', tz='UTC')
        assert len(daily.time_slice(end_time=bound)) == 31
        earlier = pd.Timestamp('2023-01-30 19:00', tz='US/Eastern')   # 00:00 UTC on the 31st
        assert len(daily.time_slice(end_time=earlier)) == 31

    def test_one_bound_only(self, daily):
        assert len(daily.time_slice(start_time='2023-12-25')) == 7

    def test_the_slice_keeps_the_origin(self, daily):
        out = daily.time_slice(start_time='2023-02-01', end_time='2023-02-28')
        assert out.ts_offset == daily.ts_offset
        assert out.times[0] == 31 * 86400.0
        assert out.datetimes[0] == pd.Timestamp('2023-02-01')

    def test_inplace(self, daily):
        daily.time_slice(start_time='2023-02-01', end_time='2023-02-28', inplace=True)
        assert len(daily) == 28
        assert daily.datetimes[0] == pd.Timestamp('2023-02-01')

    def test_a_sub_second_bound_lands_on_the_sample(self):
        """The bound is turned into seconds the way the index was, so a
        bound that names a sample includes it."""
        ts = stamped()
        out = ts.time_slice(end_time='2023-01-01 12:00:00.030')
        assert len(out) == 4

    def test_numeric_bounds_are_still_seconds_on_the_index(self):
        ts = stamped()
        assert len(ts.time_slice(start_time=0.0, end_time=0.03)) == 4

    @pytest.mark.parametrize("bound", [np.int64(30 * 86400), np.float32(30 * 86400),
                                       np.float64(30 * 86400), 30 * 86400],
                             ids=['np_int64', 'np_float32', 'np_float64', 'int'])
    def test_a_numpy_number_is_seconds_not_a_stamp(self, daily, bound):
        """`pd.Timestamp(2592000)` is 2.592 ms into 1970; the rule is
        `numbers.Real`, which every numpy number registers under."""
        assert len(daily.time_slice(end_time=bound)) == 31

    def test_a_sub_microsecond_bound_is_placed_to_the_nanosecond(self):
        """`Timedelta.total_seconds()` rounds to the microsecond; the bound
        is placed as integer nanoseconds so a 500 ns stamp is its own bound."""
        index = pd.DatetimeIndex(['2023-01-01', '2023-01-01 00:00:00.0000005',
                                  '2023-01-01 00:00:00.000001'])
        ts = baseTs(np.arange(3.0), times=index)
        assert len(ts.time_slice(end_time='2023-01-01 00:00:00.0000005')) == 2

    def test_a_calendar_bound_on_a_series_with_no_origin_is_refused(self):
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        with pytest.raises(TypeError, match="no timestamp origin") as info:
            ts.time_slice(start_time='2023-01-01')
        assert "set_timestamp_offset" in str(info.value)

    def test_a_string_that_is_not_a_date_is_refused_as_such(self):
        with pytest.raises(ValueError):
            stamped().time_slice(start_time='not a date')

    def test_on_a_series_with_no_origin_the_kind_of_bound_is_the_message(self):
        """Whatever the string says: the origin check runs before parsing."""
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        with pytest.raises(TypeError, match="no timestamp origin"):
            ts.time_slice(start_time='not a date')


class TestTheTimesSetterIsTheOtherDoor:

    def test_a_stamped_index_converts_and_sets_the_origin(self):
        ts = numeric_twin(DAILY)
        assert ts.has_timestamp_offset is False
        ts.times = DAILY
        np.testing.assert_array_equal(ts.times, np.arange(365) * 86400.0)
        assert ts.ts_offset == epoch_seconds(DAILY[0])
        assert ts.has_timestamp_offset is True

    def test_a_durations_index_converts_and_leaves_the_origin(self):
        ts = stamped()
        origin = ts.ts_offset
        ts.times = pd.timedelta_range(0, periods=len(ts), freq='s')
        np.testing.assert_array_equal(ts.times, np.arange(len(ts), dtype=float))
        assert (ts.ts_offset, ts.has_timestamp_offset) == (origin, True)

    def test_a_numeric_index_leaves_the_origin(self):
        ts = stamped()
        origin = ts.ts_offset
        ts.times = np.arange(len(ts)) / 50.0
        assert (ts.ts_offset, ts.has_timestamp_offset) == (origin, True)

    def test_an_aware_index_is_an_instant_here_too(self):
        ts = numeric_twin(DAILY[:5])
        aware = pd.date_range('2023-01-01', periods=5, freq='D', tz='Europe/Paris')
        ts.times = aware
        assert ts.ts_offset == epoch_seconds(aware[0])


class TestFromDfAcceptsADatetimeColumn:

    def test_a_datetime_column_converts(self):
        df = pd.DataFrame({'time': FAST, 'value': two_tone()})
        ts = from_df(df)
        np.testing.assert_array_equal(ts.times, seconds_since_first(FAST))
        assert ts.ts_offset == epoch_seconds(FAST[0])
        assert ts.datetimes.equals(FAST)

    def test_an_aware_column_converts(self):
        aware = pd.date_range('2023-01-01', periods=5, freq='h', tz='Asia/Tokyo')
        ts = from_df(pd.DataFrame({'time': aware, 'value': np.arange(5.0)}))
        assert ts.ts_offset == epoch_seconds(aware[0])

    def test_an_unsorted_datetime_column_is_sorted_first(self):
        df = pd.DataFrame({'time': FAST[::-1], 'value': two_tone()[::-1]})
        ts = from_df(df)
        np.testing.assert_array_equal(ts.times, seconds_since_first(FAST))
        np.testing.assert_array_equal(ts.data, two_tone())

    def test_a_timedelta_column_converts(self):
        df = pd.DataFrame({'time': pd.timedelta_range(0, periods=5, freq='s'),
                           'value': np.arange(5.0)})
        ts = from_df(df)
        np.testing.assert_array_equal(ts.times, np.arange(5.0))
        assert ts.has_timestamp_offset is False

    def test_a_nat_is_a_missing_value(self):
        df = pd.DataFrame({'time': pd.DatetimeIndex(['2023-01-01', 'NaT']),
                           'value': [1.0, 2.0]})
        with pytest.raises(ValueError, match="contains missing values"):
            from_df(df)

    def test_a_text_column_is_still_refused(self):
        df = pd.DataFrame({'time': ['a', 'b'], 'value': [1.0, 2.0]})
        with pytest.raises(ValueError, match="must be numeric, datetime or timedelta"):
            from_df(df)

    def test_the_numeric_path_is_unchanged(self):
        df = pd.DataFrame({'time': np.arange(5) / 10.0, 'value': np.arange(5.0)})
        ts = from_df(df, ts_offset=1.5)
        np.testing.assert_array_equal(ts.times, np.arange(5) / 10.0)
        assert (ts.ts_offset, ts.has_timestamp_offset) == (1.5, True)


class TestTheOriginSurvivesEveryDerivation:

    ORIGIN = epoch_seconds(FAST[0])

    @pytest.mark.parametrize("derive", [
        lambda ts: ts.iloc[2:50],
        lambda ts: ts[ts.index >= 0.5],
        lambda ts: ts * 2.0,
        lambda ts: ts + ts,
        lambda ts: ts.copy(),
        lambda ts: ts.copy(deep=False),
        lambda ts: pickle.loads(pickle.dumps(ts)),
        lambda ts: ts.lowpass_at(cutoff=5.0),
        lambda ts: ts.filter_outliers(),
        lambda ts: ts.zscale(),
        lambda ts: ts.interpolate_gaps(),
        lambda ts: ts.rolling_mean(window=5),
        lambda ts: ts.rolling(5).mean(),
        lambda ts: ts.interpto_hz(50.0),
        lambda ts: ts.shift_time(2),
        lambda ts: ts.dropna(),
        lambda ts: ts.sort_values(),
        lambda ts: baseTs(ts),
        lambda ts: TimeSeriesData(ts),
        lambda ts: ts._create_new_with_data(ts.data * 2),
    ], ids=['iloc', 'boolean_mask', 'scalar_multiply', 'add', 'copy', 'shallow_copy', 'pickle',
            'lowpass_at', 'filter_outliers', 'zscale', 'interpolate_gaps', 'rolling_mean',
            'pandas_rolling', 'interpto_hz', 'shift_time', 'dropna', 'sort_values',
            'baseTs_conversion', 'TimeSeriesData_conversion', '_create_new_with_data'])
    def test_the_pair_is_carried(self, derive):
        out = derive(stamped())
        assert out.ts_offset == self.ORIGIN
        assert out.has_timestamp_offset is True

    def test_iloc_keeps_the_seconds_so_the_stamps_shift_with_it(self):
        out = stamped().iloc[10:20]
        assert out.times[0] == 0.1
        assert out.datetimes[0] == FAST[10]

    def test_shrinking_through_the_data_setter_keeps_a_float_index(self):
        """`_update_series_data`'s no-span shrink slices the index it has;
        on `main` that index was a DatetimeIndex and stayed one."""
        ts = baseTs(np.arange(3.0), times=pd.date_range("2024-01-01", periods=3, freq="s"))
        ts.data = np.array([])
        assert len(ts) == 0
        assert ts.index.dtype == np.float64
        assert ts.has_timestamp_offset is True

    def test_inplace_methods_keep_the_pair(self):
        ts = stamped()
        ts.lowpass_at(cutoff=5.0, inplace=True)
        ts.interpolate_gaps(inplace=True)
        ts.shift_time(1, inplace=True)
        assert ts.ts_offset == self.ORIGIN


class TestTheNumericPathIsUntouched:
    """A series built from seconds must come out byte-for-byte as before.

    The pair's outcomes below were measured on `main` at 0cbffcb for every
    combination of the two keywords, on the array path and on the
    conversion path from a source carrying (1.5, True).
    """

    UNSET = object()

    @pytest.mark.parametrize("ts_offset, flag, expected", [
        (UNSET, UNSET, (0, False)),
        (1.5, UNSET, (1.5, True)),
        (1.5, False, (1.5, True)),
        (UNSET, False, (0, False)),
        (UNSET, True, (0, True)),
    ], ids=['neither', 'offset', 'offset_and_cleared_flag', 'cleared_flag', 'asserted_flag'])
    def test_the_pair_on_the_array_path(self, ts_offset, flag, expected):
        kwargs = {}
        if ts_offset is not self.UNSET:
            kwargs['ts_offset'] = ts_offset
        if flag is not self.UNSET:
            kwargs['has_timestamp_offset'] = flag
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0, **kwargs)
        assert (ts.ts_offset, ts.has_timestamp_offset) == expected
        assert type(ts.ts_offset) is type(expected[0])
        np.testing.assert_array_equal(ts.times, np.arange(10) / 10.0)

    @pytest.mark.parametrize("ts_offset, flag, expected", [
        (UNSET, UNSET, (1.5, True)),
        (2.5, UNSET, (2.5, True)),
        (2.5, False, (2.5, True)),
        (UNSET, False, (0, False)),
        (UNSET, True, (1.5, True)),
    ], ids=['neither', 'offset', 'offset_and_cleared_flag', 'cleared_flag', 'asserted_flag'])
    def test_the_pair_on_the_conversion_path(self, ts_offset, flag, expected):
        src = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        src.set_timestamp_offset(1.5)
        kwargs = {}
        if ts_offset is not self.UNSET:
            kwargs['ts_offset'] = ts_offset
        if flag is not self.UNSET:
            kwargs['has_timestamp_offset'] = flag
        ts = baseTs(src, **kwargs)
        assert (ts.ts_offset, ts.has_timestamp_offset) == expected

    def test_every_metadata_field_of_a_seconds_series_is_at_its_default(self):
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        assert ts.index.dtype == np.float64
        census = {name: getattr(ts, name) for name in TimeSeriesData._metadata}
        assert census['ts_offset'] == 0 and type(census['ts_offset']) is int
        assert census['has_timestamp_offset'] is False
        assert census['_freq_declaration'] is None
        assert census['history'] == ['Created baseTs object with 10 samples']

    def test_an_object_index_still_derives_nan_rather_than_raising(self):
        """The TypeError arm in the rate derivation used to be described as
        the DatetimeIndex arm; that index no longer reaches it, but a
        non-numeric one still must derive NaN, not raise. (The retargeted
        pins in test_series_freq.py and test_data_setter_span.py cover the
        consumption guard and the span helper the same way.)"""
        ts = baseTs(np.arange(3.0), np.array(['a', 'b', 'c'], dtype=object))
        assert np.isnan(ts.freq)


class TestSetAxisIsTheOneDoor:
    """Review round 1 (consensus panel, codex + agy): the first cut converted
    in `__init__` and the `times` setter, so pandas' own doors -
    `ts.index = dates`, `set_axis(dates)` - installed a raw DatetimeIndex on
    an object whose pair said "no origin". The door is `_set_axis` now,
    which every one of those routes through (measured on pandas 2.2.3 and
    3.0.1)."""

    def test_assigning_index_converts_and_sets_the_origin(self):
        ts = baseTs(np.arange(3.0), [0.0, 1.0, 2.0])
        ts.index = pd.date_range('2020-01-01', periods=3, freq='D')
        assert ts.index.dtype == np.float64
        np.testing.assert_array_equal(ts.times, [0.0, 86400.0, 172800.0])
        assert ts.ts_offset == epoch_seconds(pd.Timestamp('2020-01-01'))
        assert ts.duration() == 172800.0
        assert ts.datetimes[1] == pd.Timestamp('2020-01-02')

    def test_set_axis_returns_a_converted_series_with_the_origin(self):
        ts = baseTs(np.arange(3.0), [0.0, 1.0, 2.0])
        out = ts.set_axis(pd.date_range('2020-01-01', periods=3, freq='D'))
        assert out.index.dtype == np.float64
        assert out.ts_offset == epoch_seconds(pd.Timestamp('2020-01-01'))
        assert ts.has_timestamp_offset is False           # the source is untouched

    def test_reindex_to_dates_keeps_the_dates_origin_not_the_parents(self):
        """`reindex` builds through the constructor and then `__finalize__`
        copies the parent's pair; the child's index carries its origin.

        The parent is hourly and the child daily, on purpose: a daily
        parent's seconds contain a daily child's, so a stamp left over from
        the parent would pass the subset check by coincidence (mutation
        round 4 found the pin vacuous that way)."""
        parent = baseTs(np.arange(4.0), times=pd.date_range('2023-01-01', periods=4, freq='h'))
        out = parent.reindex(pd.date_range('2024-01-01', periods=3, freq='D'))
        assert out.ts_offset == epoch_seconds(pd.Timestamp('2024-01-01'))
        assert out.datetimes.equals(pd.date_range('2024-01-01', periods=3, freq='D'))
        assert np.isnan(out.data).all()                    # no overlap, as pandas says

    def test_dates_assigned_through_index_are_stamped_too(self):
        """The stamp is set where the origin is, in `_set_axis`, so a later
        replacement of the index is still caught (mutation round 4: with
        the stamp left None there, positions read as seconds again)."""
        ts = baseTs(np.arange(4.0), [0.0, 1.0, 2.0, 3.0])
        ts.index = pd.date_range('2020-01-01', periods=4, freq='h')
        ts.reset_index(drop=True, inplace=True)
        with pytest.raises(ValueError, match="no longer describes this index"):
            ts.datetimes

    def test_create_new_with_data_given_dates_keeps_their_origin(self):
        """The hardcoded copy list overwrote the fresh origin with the
        parent's: 2024 dates came back labelled 2023."""
        parent = stamped(DAILY[:3], np.arange(3.0))
        out = parent._create_new_with_data(
            parent.data * 2, pd.date_range('2024-01-01', periods=3, freq='D'))
        assert out.ts_offset == epoch_seconds(pd.Timestamp('2024-01-01'))
        assert out.datetimes.equals(pd.date_range('2024-01-01', periods=3, freq='D'))

    def test_create_new_with_data_given_seconds_keeps_the_parents_origin(self):
        parent = stamped(DAILY[:3], np.arange(3.0))
        out = parent._create_new_with_data(parent.data * 2, np.array([0.0, 1.0, 2.0]))
        assert out.ts_offset == parent.ts_offset

    def test_adopt_data_inplace_given_dates_keeps_their_origin(self):
        """No package path hands a stamped index here; pinned directly."""
        ts = stamped(DAILY[:3], np.arange(3.0))
        ts._adopt_data_inplace(np.arange(3.0), pd.date_range('2024-01-01', periods=3, freq='D'))
        assert ts.ts_offset == epoch_seconds(pd.Timestamp('2024-01-01'))

    def test_a_reinitialised_object_with_seconds_keeps_its_pair(self):
        ts = stamped(DAILY[:3], np.arange(3.0))
        origin = ts.ts_offset
        ts.data = np.arange(2.0)                 # shrinks through _adopt_data_inplace
        assert ts.ts_offset == origin

    def test_the_origin_note_is_not_pickled_and_not_propagated(self):
        """`_origin_from_index` describes one object's own index; a copy
        must not inherit a note about a different index."""
        ts = stamped(DAILY[:3], np.arange(3.0))
        assert '_origin_from_index' not in pickle.loads(pickle.dumps(ts)).__dict__
        assert '_origin_from_index' not in TimeSeriesData._metadata


class TestAnObjectIndexOfDatetimesIsStamped:
    """Review round 1 (both panelists): Timestamps in different zones cannot
    be one DatetimeIndex, so `pd.Index` left them as objects and the first
    cut left them alone - `times` returned Timestamps and nothing raised.
    The rule is by element type: calendar datetimes are stamps whatever
    container they came in."""

    def test_mixed_zone_timestamps_are_instants(self):
        mixed = np.array([pd.Timestamp('2023-01-01', tz='UTC'),
                          pd.Timestamp('2023-01-02', tz='US/Eastern')], dtype=object)
        ts = baseTs(np.arange(2.0), times=mixed)
        assert ts.index.dtype == np.float64
        assert ts.times[1] == 86400.0 + 5 * 3600.0            # 05:00 UTC
        assert ts.ts_offset == epoch_seconds(pd.Timestamp('2023-01-01'))

    def test_dates_are_their_midnights(self):
        ts = baseTs(np.arange(2.0), times=[datetime.date(2023, 1, 1), datetime.date(2023, 1, 2)])
        np.testing.assert_array_equal(ts.times, [0.0, 86400.0])
        assert ts.datetimes[1] == pd.Timestamp('2023-01-02')

    def test_a_missing_element_among_stamps_is_a_nan_second(self):
        ts = baseTs(np.arange(3.0), times=np.array([pd.Timestamp('2023-01-01'), None,
                                                   pd.Timestamp('2023-01-03')], dtype=object))
        assert np.isnan(ts.times[1]) and ts.times[2] == 172800.0
        assert ts.datetimes.isna().tolist() == [False, True, False]

    def test_strings_are_not_stamps_however_they_read(self):
        ts = baseTs(np.arange(2.0), times=np.array(['2023-01-01', '2023-01-02'], dtype=object))
        assert ts.index.dtype != np.float64
        assert ts.has_timestamp_offset is False

    def test_a_stamp_next_to_a_string_is_not_a_stamped_index(self):
        ts = baseTs(np.arange(2.0), times=np.array([pd.Timestamp('2023-01-01'), 'x'], dtype=object))
        assert ts.has_timestamp_offset is False


class TestRoundOneBoundsAndLimits:

    @pytest.mark.parametrize("bound", [Decimal('0.5'), Fraction(1, 2)], ids=['Decimal', 'Fraction'])
    def test_a_decimal_or_fraction_bound_is_seconds_as_on_main(self, bound):
        """`Decimal` registers under `numbers.Number`, not `numbers.Real`;
        `main` compared it against the index and returned 6 rows."""
        ts = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        assert len(ts.time_slice(end_time=bound)) == 6

    def test_a_span_past_292_years_is_refused_by_the_accessor(self):
        """A microsecond index from 1700 to 2200 is a valid DatetimeIndex
        (unit us), converts to seconds, and cannot be rebuilt in int64
        nanoseconds; the refusal names the limit instead of wrapping."""
        arr = np.array(['1700-01-01T00:00:00.000001', '2200-01-01T00:00:00.000001'],
                       dtype='datetime64[us]')
        ts = baseTs(np.arange(2.0), times=pd.DatetimeIndex(arr))
        assert ts.times[1] == 182621 * 86400.0                  # 500 calendar years
        with pytest.raises(OverflowError, match="292 years"):
            ts.datetimes

    @pytest.mark.parametrize("path", ['array', 'conversion'])
    def test_an_offset_with_the_flag_asserted_sets_the_pair(self, path):
        """The remaining keyword combination of the pinned pair table."""
        src = baseTs(np.arange(10.0), np.arange(10) / 10.0)
        if path == 'conversion':
            src.set_timestamp_offset(1.5)
            ts = baseTs(src, ts_offset=2.5, has_timestamp_offset=True)
        else:
            ts = baseTs(np.arange(10.0), np.arange(10) / 10.0, ts_offset=2.5,
                        has_timestamp_offset=True)
        assert (ts.ts_offset, ts.has_timestamp_offset) == (2.5, True)

    def test_an_object_index_with_no_datetime_in_it_is_not_stamped(self):
        """Mutation: a rule that counted missing values alone as a stamped
        index would send `[None, None]` through `pd.to_datetime` to a NaT
        first stamp and refuse it. Such an index is left as it is."""
        ts = baseTs(np.arange(2.0), times=np.array([None, None], dtype=object))
        assert ts.index.dtype == object
        assert ts.index.tolist() == [None, None]
        assert ts.has_timestamp_offset is False


class TestTheOriginDescribesTheIndexItWasRecordedAgainst:
    """Review round 2 (consensus panel, codex + agy): the pair rode along
    through pandas operations that replace the index with something that is
    not seconds - positions, group keys, the values - and `datetimes` read
    positions 0..3 of an hourly series as the first four seconds after
    midnight. Same mechanism as the positional slots (#20): the origin
    carries the index it was declared against (`_origin_index`), and a read
    checks that the index now held is drawn from those seconds."""

    HOURLY = pd.date_range('2020-01-01', periods=4, freq='h')

    def _hourly(self):
        return baseTs([10.0, 20.0, 30.0, 40.0], times=self.HOURLY)

    @pytest.mark.parametrize("replace", [
        lambda ts: ts.reset_index(drop=True),
        lambda ts: ts.groupby(ts.index // 7200).mean(),
        lambda ts: ts.reindex([0.5, 1.5]),
        lambda ts: ts + baseTs([1.0, 1.0], times=[0.0, 5.0]),
        lambda ts: ts.set_axis([0.0, 60.0, 120.0, 180.0]),
    ], ids=['reset_index', 'groupby_keys', 'reindex_new_grid',
            'aligned_onto_another_grid', 'set_axis_new_grid'])
    def test_an_index_that_is_no_longer_those_seconds_refuses_the_calendar(self, replace):
        out = replace(self._hourly())
        assert out.has_timestamp_offset is True          # the pair was carried
        with pytest.raises(ValueError, match="no longer describes this index"):
            out.datetimes
        with pytest.raises(TypeError, match="no longer describes this index"):
            out.time_slice(start_time='2020-01-01 01:00')

    def test_reset_index_inplace_skips_finalize_and_is_still_caught(self):
        """`_update_inplace` swaps the manager without `__finalize__`; the
        read-time check needs nothing to run at write time."""
        ts = self._hourly()
        ts.reset_index(drop=True, inplace=True)
        assert list(ts.index) == [0, 1, 2, 3]
        with pytest.raises(ValueError, match="no longer describes this index"):
            ts.datetimes

    @pytest.mark.parametrize("keep", [
        lambda ts: ts.iloc[1:3],
        lambda ts: ts[ts.index >= 3600.0],
        lambda ts: ts.sort_values(ascending=False),
        lambda ts: ts.sort_index(ascending=False),
        lambda ts: ts.dropna(),
        lambda ts: ts * 2.0,
        lambda ts: ts + ts.iloc[::2],
        lambda ts: ts.astype('float32'),
        lambda ts: ts.where(ts > 15.0),
        lambda ts: ts.resample('2h'),
        lambda ts: ts.interpto_hz(1 / 1800.0),
        lambda ts: ts.time_slice(end_time='2020-01-01 02:00'),
        lambda ts: ts.diff_ts(),
        lambda ts: ts.copy(),
        lambda ts: pickle.loads(pickle.dumps(ts)),
    ], ids=['iloc', 'mask', 'sort_values', 'sort_index', 'dropna', 'scalar_mul',
            'aligned_onto_own_subgrid', 'astype', 'where', 'resample', 'interpto_hz',
            'time_slice', 'diff_ts', 'copy', 'pickle'])
    def test_an_index_drawn_from_those_seconds_still_reads(self, keep):
        out = keep(self._hourly())
        stamps = out.datetimes
        assert len(stamps) == len(out)
        assert stamps[0] >= self.HOURLY[0] - pd.Timedelta(hours=1)

    def test_the_data_setter_regrids_in_the_same_base(self):
        ts = self._hourly()
        ts.data = np.arange(7.0)                        # linspace over the same span
        assert ts.datetimes[-1] == self.HOURLY[-1]

    def test_the_times_setter_declares_seconds_in_this_base(self):
        """The package's door asserts the base; pandas' door does not."""
        ts = self._hourly()
        ts.times = np.array([0.0, 60.0, 120.0, 180.0])
        assert ts.datetimes[1] == pd.Timestamp('2020-01-01 00:01')

    def test_pandas_index_assignment_of_a_new_grid_is_refused_at_read(self):
        """`ts.index = ...` is the door `reset_index(inplace=True)` uses to
        install positions, so a numeric index arriving there is not
        re-stamped; one drawn from the origin's seconds still reads."""
        ts = self._hourly()
        ts.index = pd.Index([0.0, 60.0, 120.0, 180.0])
        with pytest.raises(ValueError, match="no longer describes this index"):
            ts.datetimes
        ts = self._hourly()
        ts.index = pd.Index([10800.0, 7200.0, 3600.0, 0.0])          # the same seconds
        assert ts.datetimes[0] == self.HOURLY[3]

    def test_concat_of_pieces_sharing_an_origin_keeps_it(self):
        ts = self._hourly()
        out = pd.concat([ts.iloc[:2], ts.iloc[2:]])
        assert out.ts_offset == ts.ts_offset
        assert out.datetimes.equals(self.HOURLY)

    def test_concat_of_pieces_with_different_origins_has_none(self):
        a = self._hourly()
        b = baseTs([1.0, 2.0], times=pd.date_range('2021-01-01', periods=2, freq='h'))
        out = pd.concat([a, b])
        assert out.has_timestamp_offset is False

    def test_concat_with_a_piece_that_has_no_origin_has_none(self):
        out = pd.concat([self._hourly(), baseTs([1.0, 2.0], times=[0.0, 1.0])])
        assert out.has_timestamp_offset is False

    def test_an_object_index_of_nat_alone_is_a_stamped_index_and_refused(self):
        """NaT is typed missing: `[NaT]` behaves like `DatetimeIndex([NaT])`,
        where `[None]` (untyped) is left as it is (round 2, agy)."""
        with pytest.raises(ValueError, match="first stamp is NaT"):
            baseTs([1.0], times=pd.Index([pd.NaT], dtype=object))

    def test_a_pickle_from_before_the_stamp_is_healed_on_load(self):
        """A blob written before `_origin_index` existed carries the pair,
        no stamp, and the registry of its day - which is the shape a real
        one has, not merely a missing attribute."""
        ts = self._hourly()
        state = ts.__getstate__()
        state = dict(state)
        state.pop('_origin_index')
        state['_metadata'] = [n for n in state['_metadata'] if n != '_origin_index']
        legacy = baseTs.__new__(baseTs)
        legacy.__setstate__(state)
        assert legacy.datetimes.equals(self.HOURLY)
        assert legacy._origin_index.equals(legacy.index)
        assert '_origin_index' in legacy._metadata            # the class registry governs

    def test_the_stamp_is_in_metadata_and_defaults_to_none(self):
        assert '_origin_index' in TimeSeriesData._metadata
        assert baseTs(np.arange(3.0), [0.0, 1.0, 2.0])._origin_index is None
        assert self._hourly()._origin_index.equals(pd.Index([0.0, 3600.0, 7200.0, 10800.0]))
