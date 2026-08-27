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
    """The original zero/negative rejection is preserved."""
    ts = baseTs(np.array([1.0, 2.0, 3.0, 4.0]), np.arange(4) / 4.0, freq=0.0)
    with pytest.raises(ValueError, match="Invalid sampling frequency"):
        compute_fft_power(ts)


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
