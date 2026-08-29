"""
Unit tests for baseTs utility functions.
"""
import pytest
import numpy as np
from baseTs.utils import (find_closest, find_closest_time, compute_fft_power,
                         get_peak_freq, get_peaks, relative_band_power, falff,
                         BandPowerResult)
from baseTs import baseTs


def test_find_closest():
    """Test find_closest function."""
    # Test exact match
    test_array = np.array([1, 3, 5, 7, 9])

    result = find_closest(5, test_array)
    assert result.location == 2
    assert result.value == 5
    assert result.abs_err == 0
    assert result.target == 5

    # Test closest match
    result = find_closest(6, test_array)
    assert result.location == 2  
    assert result.value == 5
    assert result.abs_err == 1
    assert result.target == 6

    # Test edge cases
    result = find_closest(0, test_array)
    assert result.location == 0  # 1 is closest to 0

    result = find_closest(10, test_array)
    assert result.location == 4  # 9 is closest to 10


def test_find_closest_time(simple_baseTsObj):
    """Test find_closest_time function."""
    # Time at exact sample
    result = find_closest_time(simple_baseTsObj, 5.0)
    # assert result.value == 5.0
    # assert result.abs_err == 0
    
    # Time between samples
    result = find_closest_time(simple_baseTsObj, 5.005)
    assert abs(result.value - 5.005) < 0.01  # Should be close
    
    # Time outside range but close to edge
    result = find_closest_time(simple_baseTsObj, 10.1)
    assert result.value == 10.0  # Should return the last time point


def test_compute_fft_power(simple_baseTsObj):
    """Test compute_fft_power function."""
    # Our signal has components at 0.5 Hz and 1.5 Hz
    freqs, power = compute_fft_power(simple_baseTsObj)
    
    # Find peaks in power spectrum
    peak_indices = np.argsort(power)[-3:]  # Top 3 peaks (including DC)
    peak_freqs = freqs[peak_indices]
    
    # Check that our known frequencies are found
    # Allow for some numerical error with isclose
    assert any(np.isclose(peak_freqs, 0.5, atol=0.1))
    assert any(np.isclose(peak_freqs, 1.5, atol=0.1))
    
    # Test with max_rate
    freqs_limited, power_limited = compute_fft_power(simple_baseTsObj, max_rate=1.0)
    assert np.max(freqs_limited) <= 1.0


def test_get_peak_freq(simple_baseTsObj, noisy_baseTsObj):
    """Test get_peak_freq function."""
    # For the simple signal, the peak should be at 0.5 Hz
    peak_freq = get_peak_freq(simple_baseTsObj)
    assert np.isclose(peak_freq, 0.5, atol=0.1)
    
    # For the noisy signal, it should still find the main peak
    peak_freq = get_peak_freq(noisy_baseTsObj)
    assert np.isclose(peak_freq, 0.5, atol=0.1)


def test_get_peaks():
    """Test get_peaks function."""
    # Seeded: this test adds unseeded noise and asserts an exact peak count, so
    # its result depended on whatever global random state ran before it.
    np.random.seed(42)
    # Create a simple signal with known peaks
    n_points = 1000
    t = np.linspace(0, 10, n_points)
    # Signal with several peaks
    signal = np.zeros_like(t)
    
    # Add peaks at specific locations
    peak_locations = [100, 300, 500, 700, 900]
    for loc in peak_locations:
        signal[loc] = 5.0
    
    # Add some noise
    signal += 0.1 * np.random.randn(n_points)
    
    ts = baseTs(signal, t)
    
    # Find peaks with default parameters
    peaks = get_peaks(ts)
    
    # With no min_height the 0.1-amplitude noise can also register, so assert
    # the real peaks are all found rather than pinning an exact count. The
    # exact-count assertions below use min_height, which excludes the noise.
    for loc in peak_locations:
        assert any(abs(p - loc) <= 2 for p in peaks), f"missed peak at {loc}"
    
    # Test with min_height
    peaks = get_peaks(ts, min_height=4.0)
    assert len(peaks) == len(peak_locations)
    
    # Test with higher min_height that should exclude all peaks
    peaks = get_peaks(ts, min_height=6.0)
    assert len(peaks) == 0
    
    # Test with min_dist_secs
    # Our peaks are 200 samples apart, which is 2 seconds
    peaks = get_peaks(ts, min_dist_secs=1.5)
    assert len(peaks) == len(peak_locations)
    
    # With larger min_dist_secs, it should only find some peaks
    peaks = get_peaks(ts, min_dist_secs=3.0)
    assert len(peaks) < len(peak_locations)

# ---------------------------------------------------------------------------
# Relative band power / fALFF
# ---------------------------------------------------------------------------

@pytest.fixture
def lf_baseTsObj():
    """
    Long, slowly-varying signal suitable for 0.01-0.1 Hz band analysis.

    600 s at 2 Hz gives a frequency resolution of 1/600 Hz, which is fine
    enough to resolve the low end of the classic fALFF band.
    """
    np.random.seed(42)
    fs, n = 2.0, 1200
    t = np.arange(n) / fs
    sig = np.sin(2 * np.pi * 0.05 * t) + 0.5 * np.random.randn(n)
    return baseTs(sig, t, freq=fs)


def test_relative_band_power_basic(lf_baseTsObj):
    """A dominant 0.05 Hz component should put most power in the 0.01-0.1 band."""
    ratio = relative_band_power(lf_baseTsObj, 0.01, 0.1)

    assert isinstance(ratio, float)
    assert not isinstance(ratio, np.floating)  # builtin float, not np.float64
    assert 0.6 < ratio < 0.8


def test_relative_band_power_dc_invariance(lf_baseTsObj):
    """
    Adding a constant offset must not change the result.

    get_frequency_content() does not demean, so the DC bin of an offset signal
    holds the overwhelming majority of raw power. Excluding DC from both the
    numerator and the denominator is what keeps this measurement meaningful
    when the caller has not detrended upstream.
    """
    baseline = relative_band_power(lf_baseTsObj, 0.01, 0.1)

    offset = baseTs(lf_baseTsObj.data + 100.0, lf_baseTsObj.times,
                    freq=lf_baseTsObj.freq)
    assert np.isclose(relative_band_power(offset, 0.01, 0.1), baseline)

    # And it agrees with the properly detrended pipeline
    detrended = lf_baseTsObj.detrend('constant')
    assert np.isclose(relative_band_power(detrended, 0.01, 0.1), baseline,
                      rtol=1e-6)


def test_relative_band_power_white_noise_null():
    """
    For white noise both conventions converge on the bin fraction.

    That makes n_band_bins / n_total_bins the reference point for 'no
    band-specific structure' - the null is not zero.
    """
    np.random.seed(7)
    fs, n = 2.0, 4096
    t = np.arange(n) / fs
    ts = baseTs(np.random.randn(n), t, freq=fs)

    details = relative_band_power(ts, 0.01, 0.1, details=True)
    amp = relative_band_power(ts, 0.01, 0.1, ratio='amplitude')

    assert np.isclose(details.ratio, details.bin_fraction, atol=0.03)
    assert np.isclose(amp, details.bin_fraction, atol=0.03)


def test_relative_band_power_parseval(lf_baseTsObj):
    """Disjoint bands tiling the non-DC spectrum sum to 1.0 for ratio='power'."""
    df = lf_baseTsObj.freq / len(lf_baseTsObj)
    # Half-bin offsets so no band edge lands on a bin (no overlap, no gaps)
    edge_1 = 150.5 * df
    edge_2 = 400.5 * df

    total = (
        relative_band_power(lf_baseTsObj, 0.0, edge_1)
        + relative_band_power(lf_baseTsObj, edge_1, edge_2)
        + relative_band_power(lf_baseTsObj, edge_2, lf_baseTsObj.freq / 2)
    )
    assert np.isclose(total, 1.0)


def test_relative_band_power_amplitude_convention(lf_baseTsObj):
    """ratio='amplitude' sums sqrt(power) and differs materially from power."""
    power_ratio = relative_band_power(lf_baseTsObj, 0.01, 0.1, ratio='power')
    amp_ratio = relative_band_power(lf_baseTsObj, 0.01, 0.1, ratio='amplitude')

    # Hand-computed reference
    freqs, power = lf_baseTsObj.get_frequency_content()
    keep = freqs > 0
    freqs, power = freqs[keep], power[keep]
    amp = np.sqrt(power)
    band = (freqs >= 0.01) & (freqs <= 0.1)
    assert np.isclose(amp_ratio, amp[band].sum() / amp.sum())

    # The square root compresses the in-band peak, so amplitude reads much lower
    assert amp_ratio < power_ratio


def test_relative_band_power_bandwidth_sensitivity():
    """
    Expected behaviour, not a bug: the amplitude ratio falls as the sampling
    rate rises because its denominator grows with the number of noise bins,
    while the power ratio stays roughly stable. This is the standard caveat
    on comparing fALFF across acquisitions with different bandwidth.
    """
    power_ratios, amp_ratios = [], []
    for fs in (0.5, 2.0, 10.0):
        np.random.seed(3)
        n = int(600 * fs)
        t = np.arange(n) / fs
        ts = baseTs(np.sin(2 * np.pi * 0.05 * t) + 0.5 * np.random.randn(n),
                    t, freq=fs)
        power_ratios.append(relative_band_power(ts, 0.01, 0.1))
        amp_ratios.append(relative_band_power(ts, 0.01, 0.1, ratio='amplitude'))

    # Amplitude ratio collapses with bandwidth
    assert amp_ratios[0] > amp_ratios[1] > amp_ratios[2]
    assert amp_ratios[0] / amp_ratios[2] > 5

    # Power ratio holds up
    assert max(power_ratios) - min(power_ratios) < 0.15


def test_relative_band_power_details(lf_baseTsObj):
    """details=True returns a self-consistent BandPowerResult."""
    res = relative_band_power(lf_baseTsObj, 0.01, 0.1, details=True)

    assert isinstance(res, BandPowerResult)
    assert res.ratio_type == 'power'
    assert np.isclose(res.band_sum / res.total_sum, res.ratio)
    assert np.isclose(res.bin_fraction, res.n_band_bins / res.n_total_bins)
    assert res.low_freq == 0.01 and res.high_freq == 0.1
    assert 0 < res.n_band_bins < res.n_total_bins
    assert np.isclose(res.freq_resolution, lf_baseTsObj.freq / len(lf_baseTsObj))
    assert np.isclose(res.nyquist, lf_baseTsObj.freq / 2)


def test_relative_band_power_validation(lf_baseTsObj):
    """Each precondition raises a ValueError naming the problem."""
    with pytest.raises(ValueError, match="negative"):
        relative_band_power(lf_baseTsObj, -1.0, 0.1)

    with pytest.raises(ValueError, match="low_freq"):
        relative_band_power(lf_baseTsObj, 0.2, 0.1)

    with pytest.raises(ValueError, match="Nyquist"):
        relative_band_power(lf_baseTsObj, 0.01, 5.0)

    with pytest.raises(ValueError, match="ratio"):
        relative_band_power(lf_baseTsObj, 0.01, 0.1, ratio='bogus')

    # Band narrower than the frequency resolution
    with pytest.raises(ValueError, match="resolution"):
        relative_band_power(lf_baseTsObj, 0.0001, 0.0002)

    # NaN in the data
    bad = lf_baseTsObj.data.copy()
    bad[10] = np.nan
    nan_ts = baseTs(bad, lf_baseTsObj.times, freq=lf_baseTsObj.freq)
    with pytest.raises(ValueError, match="NaN"):
        relative_band_power(nan_ts, 0.01, 0.1)

    # Constant signal has no power outside DC
    n = 1200
    const_ts = baseTs(np.ones(n), np.arange(n) / 2.0, freq=2.0)
    with pytest.raises(ValueError, match="no spectral power"):
        relative_band_power(const_ts, 0.01, 0.1)


def test_falff(lf_baseTsObj):
    """falff() is the classic 0.01-0.1 Hz amplitude ratio."""
    assert np.isclose(
        falff(lf_baseTsObj),
        relative_band_power(lf_baseTsObj, 0.01, 0.1, ratio='amplitude'),
    )

    # Band and convention are both overridable
    assert np.isclose(
        falff(lf_baseTsObj, 0.01, 0.08, ratio='power'),
        relative_band_power(lf_baseTsObj, 0.01, 0.08, ratio='power'),
    )


def _degenerate_freq_ts():
    """A series whose time base is degenerate, so freq derives to NaN.

    _calculate_effective_frequency returns NaN when duration <= 0. This is its
    documented contract; the point of these tests is that consumers of freq
    reject the NaN loudly instead of propagating it into their output.
    """
    ts = baseTs(np.array([1.0, 2.0, 3.0, 4.0]), np.array([0.0, 0.0, 0.0, 0.0]))
    assert np.isnan(ts.freq), "fixture precondition: freq should derive to NaN"
    return ts


def test_compute_fft_power_rejects_nan_freq():
    """A NaN sampling rate raises rather than producing NaN frequencies.

    `nan <= 0` is False, so a bare `if ts.freq <= 0` guard lets NaN through
    and the FFT silently returns NaN frequency bins (issue #24).
    """
    ts = _degenerate_freq_ts()
    with pytest.raises(ValueError, match="Invalid sampling frequency"):
        compute_fft_power(ts)


def test_compute_fft_power_still_rejects_nonpositive_freq():
    """The original zero/negative rejection is preserved.

    Routed through _FreqStub rather than a constructed baseTs. baseTs can no
    longer hold freq=0 - the validating setter raises at construction, before
    compute_fft_power ever runs - so building one here would test the
    constructor instead of this guard. compute_fft_power only reads
    ts.data and ts.freq (see baseTs/utils.py), which is exactly the interface
    _FreqStub provides.
    """
    with pytest.raises(ValueError, match="Invalid sampling frequency"):
        compute_fft_power(_FreqStub(np.array([1.0, 2.0, 3.0, 4.0]), 0.0))


def test_get_frequency_content_rejects_nan_freq():
    """get_frequency_content computes its own FFT and needs its own guard.

    It does not route through compute_fft_power, so fixing that guard alone
    leaves this path returning NaN bins.
    """
    ts = _degenerate_freq_ts()
    with pytest.raises(ValueError, match="Invalid sampling frequency"):
        ts.get_frequency_content()


def test_get_peak_freq_rejects_nan_freq():
    """get_peak_freq inherits the guard through get_frequency_content."""
    ts = _degenerate_freq_ts()
    with pytest.raises(ValueError, match="Invalid sampling frequency"):
        get_peak_freq(ts)


def test_relative_band_power_rejects_nan_freq():
    """A NaN rate is rejected, via get_frequency_content downstream.

    This pins behaviour, not a particular guard: relative_band_power has no
    check of its own, and deliberately so - it calls get_frequency_content,
    whose guard raises this same error. An earlier revision added a
    redundant local guard and a test that could not tell the two apart, so
    the guard could be deleted with the suite still green.
    """
    ts = _degenerate_freq_ts()
    with pytest.raises(ValueError, match="Invalid sampling frequency"):
        relative_band_power(ts, 0.01, 0.1)


# ---------------------------------------------------------------------------
# Non-finite *data* guards (issue #28)
#
# The guards above reject a bad time base. These reject bad samples. An FFT
# over data containing NaN returns an all-NaN spectrum, and find_peaks over an
# all-NaN array still returns indices - so get_peak_freq reported a confident
# wrong number rather than failing. That is the more dangerous half of the NaN
# story: the sampling-rate NaN of #24 at least produced visible NaN output.
# ---------------------------------------------------------------------------

def _gappy_ts(bad=np.nan, n_bad=1):
    """A 0.16 Hz sine over 500 samples with `n_bad` samples replaced by `bad`."""
    data = np.sin(np.arange(500) / 10.0)
    data[100:100 + n_bad] = bad
    return baseTs(data, np.arange(500) / 10.0)


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_get_frequency_content_rejects_nonfinite_data(bad):
    """The production site raises instead of returning an all-NaN spectrum.

    get_frequency_content builds its own FFT and was the only spectral entry
    point without this check, so every consumer of it inherited the defect.
    """
    with pytest.raises(ValueError, match="NaN or Inf"):
        _gappy_ts(bad).get_frequency_content()


def test_get_peak_freq_rejects_nonfinite_data():
    """The headline defect: no confident wrong answer on gappy data.

    Pins behaviour, not a particular guard - get_peak_freq has no check of its
    own and deliberately so, since get_frequency_content raises first. The
    value it used to return (4.98 Hz, against a true peak of 0.16 Hz) was an
    artifact of find_peaks indexing an all-NaN array, and was insensitive to
    how many samples were bad, which is what confirmed it was meaningless
    rather than merely degraded.
    """
    ts = _gappy_ts()
    with pytest.raises(ValueError, match="NaN or Inf"):
        ts.get_peak_freq()

    # Windowing does not launder it either - the window multiplies the NaN
    # through rather than removing it.
    with pytest.raises(ValueError, match="NaN or Inf"):
        ts.get_peak_freq(window='hann')

    with pytest.raises(ValueError, match="NaN or Inf"):
        ts.get_peak_freq(num_pks=3)


def _all_four_entry_points(ts):
    """The four public ways into an FFT, as zero-argument callables."""
    return (
        lambda: ts.get_frequency_content(),
        lambda: ts.get_peak_freq(),
        lambda: relative_band_power(ts, 0.01, 0.1),
        lambda: compute_fft_power(ts),
    )


def test_nonfinite_data_message_names_the_remedy_everywhere():
    """All four spectral entry points give the same actionable error.

    They drifted before: compute_fft_power and relative_band_power each
    carried their own copy of the check with different wording, and
    get_frequency_content carried none. The shared helper is what stops a
    fifth entry point being added without one.
    """
    for call in _all_four_entry_points(_gappy_ts()):
        with pytest.raises(ValueError, match="interpolate_gaps"):
            call()


def test_non_numeric_data_raises_the_same_way_at_all_four_entry_points():
    """The uniform-ValueError contract must hold for dtype too, not just NaN.

    An object array of non-numbers is the case that broke it. Three of the
    four reach validate_finite_data first and raise ValueError, but
    relative_band_power narrows with `np.asarray(ts.values, dtype=float)`
    before delegating, and that cast raises a bare TypeError on values float()
    cannot take. Sibling tests covering only NaN-gappy float data could not
    see the asymmetry, so the contract was asserted without being checked.

    Dicts rather than strings deliberately: `float('a')` raises ValueError, so
    a string array happens to produce the right exception type for the wrong
    reason and would have passed even unguarded.
    """
    n = 500
    ts = baseTs(np.array([{} for _ in range(n)], dtype=object),
                np.arange(n) / 2.0, freq=2.0)

    for call in _all_four_entry_points(ts):
        with pytest.raises(ValueError, match="not numeric"):
            call()


@pytest.mark.parametrize("good", [
    np.arange(8),                          # int - cannot hold NaN, early return
    np.array([True, False, True]),         # bool - likewise
    np.array([1.0, 2.0], dtype=object),    # object, but of real numbers
    np.array([1 + 2j, 3 + 4j]),            # complex, both parts finite
])
def test_validate_finite_data_accepts_usable_dtypes(good):
    """The guard rejects bad values, not unfamiliar dtypes.

    Complex is the load-bearing case: np.isfinite handles it, so it is left
    unconverted. A float cast would reject it outright, which would be a
    behaviour change rather than the guard this function exists to add.
    """
    from baseTs.utils import validate_finite_data

    assert validate_finite_data(good) is None


@pytest.mark.parametrize("bad", [
    np.array([1.0, np.nan], dtype=object),
    np.array([1 + 2j, complex(np.nan, 0)]),
])
def test_validate_finite_data_looks_inside_unconverted_dtypes(bad):
    """Object and complex arrays are checked, not waved through.

    np.isfinite raises TypeError on object arrays, so the object case only
    works because it is converted first.
    """
    from baseTs.utils import validate_finite_data

    with pytest.raises(ValueError, match="NaN or Inf"):
        validate_finite_data(bad)


@pytest.mark.parametrize("demean", [True, False])
def test_compute_fft_power_rejects_nonfinite_data_either_way(demean):
    """The guard is unconditional, not folded into the demean branch.

    demean=False is the case that needs pinning. Moving the check inside
    `if demean:` passes the entire suite otherwise, and reinstates issue #28's
    exact failure mode - an all-NaN spectrum returned in silence - through a
    documented public keyword.
    """
    with pytest.raises(ValueError, match="NaN or Inf"):
        compute_fft_power(_gappy_ts(), demean=demean)


@pytest.mark.parametrize("dtype", ["datetime64[ns]", "timedelta64[ns]"])
def test_validate_finite_data_rejects_datetime_dtypes(dtype):
    """NaT must not slip through the float cast.

    This is the one dtype family where converting to float is actively
    misleading rather than merely unnecessary: NaT is the int64 sentinel
    -2**63, so the cast succeeds and produces a large but finite float that
    np.isfinite is perfectly happy with. Rejecting the dtype outright is what
    stops that, so the check must sit *before* the conversion.
    """
    from baseTs.utils import validate_finite_data

    with pytest.raises(ValueError, match="not numeric"):
        validate_finite_data(np.array([1, 'NaT'], dtype=dtype))

    # ...and without NaT too - these are timestamps, not sample values
    with pytest.raises(ValueError, match="not numeric"):
        validate_finite_data(np.array([1, 2], dtype=dtype))


def test_datetime_remedy_does_not_recreate_the_bug_it_reports():
    """The remedy the message names must not launder NaT into a finite float.

    An integer or float cast is the obvious suggestion and is actively wrong:
    it reinterprets the int64 storage, so NaT returns as -9.22e18, which this
    guard accepts. Following that advice would move the silent-nonsense
    failure one level up rather than fixing it, which is why the message
    steers to datetime arithmetic instead - that maps NaT to NaN.

    An earlier revision did recommend `.astype(float)`, and no test looked at
    the remedy text, only at "not numeric". A later one gave the *duration*
    remedy to datetime callers too, where it raises UFuncTypeError - so each
    dtype's own remedy is exercised here rather than assumed to transfer.

    Note the first assertion in each pair deliberately pins behaviour that
    looks like a bug. It is not fixable at this layer: once a float64 array
    arrives, the dtype provenance is gone and a laundered NaT is
    indistinguishable from a genuine large value. That is precisely why the
    message had to change rather than the validator.
    """
    from baseTs.utils import validate_finite_data

    cases = [
        # dtype kind 'm': durations
        (np.array([1, 'NaT'], dtype='timedelta64[ns]'),
         np.array([1, 2], dtype='timedelta64[ns]'),
         lambda v: v / np.timedelta64(1, 's'),
         lambda v: v.astype(float),
         "values / np.timedelta64(1, 's')"),
        # dtype kind 'M': timestamps, which need a different remedy entirely -
        # dividing one by a timedelta64 raises rather than helping
        (np.array(['2020-01-01', 'NaT'], dtype='datetime64[ns]'),
         np.array(['2020-01-01', '2020-01-03'], dtype='datetime64[ns]'),
         lambda v: (v - v[0]) / np.timedelta64(1, 's'),
         lambda v: v.astype('int64').astype(float),
         "(values - values[0]) / np.timedelta64(1, 's')"),
    ]

    for gappy, clean, remedy, wrong_remedy, expected_text in cases:
        # The wrong remedy: silently accepted, which is the failure mode.
        assert validate_finite_data(wrong_remedy(gappy)) is None
        assert np.all(np.isfinite(wrong_remedy(gappy)))

        # The remedy the message names: NaT becomes NaN, so the caller lands
        # on the gap-filling error rather than on a wrong number.
        with pytest.raises(ValueError, match="interpolate_gaps"):
            validate_finite_data(remedy(gappy))

        # ...and it accepts cleanly once there is no NaT.
        assert validate_finite_data(remedy(clean)) is None

        # Pin the message against the exact remedy verified above. Asserting
        # merely that it says "np.timedelta64" is vacuous - both dtypes'
        # messages do, so the duration remedy could be handed to a datetime
        # caller (where it raises UFuncTypeError) with the test still green.
        # That mutant survived until this assertion named the whole expression.
        with pytest.raises(ValueError) as exc:
            validate_finite_data(gappy)
        assert expected_text in str(exc.value)
        assert "astype" in str(exc.value)

    # The duration remedy is not merely unhelpful on timestamps, it raises -
    # which is why the message splits by dtype instead of offering one.
    with pytest.raises(TypeError):
        np.array(['2020-01-01'], dtype='datetime64[ns]') / np.timedelta64(1, 's')


def test_validate_finite_data_reports_non_numeric_as_valueerror():
    """Non-numeric data gets the documented ValueError, not a numpy TypeError.

    Before the shared guard, a string series reached np.fft.fft (or np.isnan)
    and died with "ufunc not supported for the input types", which names an
    internal ufunc rather than the caller's data.
    """
    from baseTs.utils import validate_finite_data

    for bad in (np.array(['a', 'b'], dtype=object), np.array(['a', 'b'])):
        with pytest.raises(ValueError, match="not numeric"):
            validate_finite_data(bad)


def test_interpolating_the_gaps_recovers_the_true_peak():
    """The remedy the error message names actually resolves it.

    Without this, the guard could name a method that does not in fact make the
    call succeed. 0.16 Hz is the peak of the same series with no NaN in it.
    """
    recovered = _gappy_ts().interpolate_gaps().get_peak_freq()
    assert np.isclose(recovered, 0.16), recovered


def test_validate_sampling_freq_rejects_non_real_scalars():
    """The documented ValueError holds for non-numeric input too.

    `freq > 0` raises TypeError for a string and the ambiguous-truth-value
    error for an array; both must surface as the documented ValueError.
    """
    from baseTs.utils import validate_sampling_freq

    for bad in ("30", None, np.array([1.0, 2.0]), [1.0], {}):
        with pytest.raises(ValueError, match="Invalid sampling frequency"):
            validate_sampling_freq(bad)

    # bool is a Real, so True would otherwise be accepted as 1.0 Hz
    with pytest.raises(ValueError, match="not a real number"):
        validate_sampling_freq(True)


@pytest.mark.parametrize("bad", [np.inf, -np.inf, np.nan, 0.0, -1.0])
def test_validate_sampling_freq_rejects_unusable_rates(bad):
    """Non-finite and non-positive rates alike."""
    from baseTs.utils import validate_sampling_freq

    with pytest.raises(ValueError, match="Invalid sampling frequency"):
        validate_sampling_freq(bad)


def test_validate_sampling_freq_hint_is_specific_to_nan():
    """Only NaN gets the degenerate-time-base hint.

    A zero or negative rate is nearly always an explicit freq= argument;
    pointing those at the timestamps sends the reader the wrong way.
    """
    from baseTs.utils import validate_sampling_freq

    with pytest.raises(ValueError, match="time base is degenerate"):
        validate_sampling_freq(np.nan)

    for bad in (0.0, -1.0, np.inf):
        with pytest.raises(ValueError) as exc:
            validate_sampling_freq(bad)
        assert "time base is degenerate" not in str(exc.value)


def test_validate_sampling_freq_accepts_real_types_numpy_handles():
    """Types float() converts must not be rejected, nor crash on isfinite.

    An earlier revision gated on numbers.Real, which let Fraction through to
    np.isfinite - no object-dtype loop, so TypeError, breaking the documented
    ValueError contract and escaping filters' except-ValueError translation.
    """
    from fractions import Fraction
    from decimal import Decimal
    from baseTs.utils import validate_sampling_freq

    assert validate_sampling_freq(Fraction(30, 1)) == 30.0
    assert validate_sampling_freq(Decimal("2.5")) == 2.5
    assert validate_sampling_freq(np.array(30.0)) == 30.0   # 0-d array
    assert validate_sampling_freq(2 ** 63 + 1) > 0


def test_validate_sampling_freq_accepts_usable_rates():
    """Ordinary rates pass through unchanged, as floats."""
    from baseTs.utils import validate_sampling_freq

    assert validate_sampling_freq(30) == 30.0
    assert validate_sampling_freq(0.5) == 0.5
    assert validate_sampling_freq(np.float64(100.0)) == 100.0
    assert isinstance(validate_sampling_freq(30), float)


def test_get_peaks_rejects_nan_freq():
    """get_peaks scales min_dist_secs by freq; NaN must not reach int()."""
    from baseTs.utils import get_peaks

    ts = _degenerate_freq_ts()
    with pytest.raises(ValueError, match="Invalid sampling frequency"):
        get_peaks(ts)


class _FreqStub:
    """The whole interface get_peaks needs: .data and .freq.

    Used where the point is get_peaks' own tolerance of a rate, not baseTs'
    willingness to hold one. baseTs now rejects freq <= 0 at construction, so
    routing these cases through the constructor would test the constructor.
    """

    def __init__(self, data, freq):
        self.data = data
        self.freq = freq


@pytest.mark.parametrize("freq", [0.0, -1.0])
def test_get_peaks_ignores_nonpositive_freq(freq):
    """freq <= 0 provably never influenced the result and still must not.

    int(min_dist_secs * 0.0) is 0 and the max(25, ...) floor absorbs it. This
    guards get_peaks' deliberately-narrow guard: it rejects only non-finite
    rates, not non-positive ones, and must stay narrower than
    validate_sampling_freq.

    Previously constructed a baseTs with freq=0.0. baseTs now refuses that at
    construction - the premise for tolerating such objects was that
    interpto_hz(0) minted them, and interpto_hz(0) now raises. The subject
    here was always get_peaks' arithmetic, so it tests that directly.
    """
    from baseTs.utils import get_peaks

    sig = np.zeros(300)
    sig[[50, 150, 250]] = 5.0

    assert get_peaks(_FreqStub(sig, freq)) == [50, 150, 250]


@pytest.mark.parametrize("bad,label", [
    (10 ** 400, "OverflowError from float()"),
    (np.bool_(True), "np.bool_ is not a bool subclass"),
    (np.array([30.0]), "size-1 array: float() differs across numpy majors"),
    (np.array([1.0, 2.0]), "multi-element array"),
])
def test_validate_sampling_freq_rejects_lookalikes(bad, label):
    """Each of these reached a non-ValueError or was silently accepted."""
    from baseTs.utils import validate_sampling_freq

    with pytest.raises(ValueError, match="Invalid sampling frequency"):
        validate_sampling_freq(bad)


@pytest.mark.parametrize("dtype", [np.float32, np.float16, np.float64])
def test_get_peaks_rejects_nonfinite_numpy_scalars(dtype):
    """np.float32/16 are not float subclasses, so an isinstance gate missed them.

    They fell through to int(), raising the raw conversion error the guard
    exists to replace - or OverflowError for an infinity, which is not even a
    ValueError.
    """
    from baseTs.utils import get_peaks

    sig = np.sin(np.arange(200) / 10.0)
    for bad in (dtype(np.nan), dtype(np.inf)):
        with pytest.raises(ValueError, match="Invalid sampling frequency"):
            get_peaks(_FreqStub(sig, bad))


def test_filters_use_the_normalised_rate():
    """validate_sampling_freq accepts Decimal; the caller must use its return.

    Discarding it left `0.5 * fs` to raise a raw TypeError outside the
    try/except, so it was not an InvalidParameterError.
    """
    from decimal import Decimal
    from baseTs.filters import highpass_filter, lowpass_filter

    data = np.sin(np.arange(200) / 10.0)
    assert len(highpass_filter(data, 1.0, Decimal('30'), 4)) == 200
    assert len(lowpass_filter(data, 1.0, Decimal('30'), 4)) == 200
