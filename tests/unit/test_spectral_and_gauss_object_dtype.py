"""Object-dtype data reaching the spectral family and gauss_filter (#93).

The same shape as #75 and #80, in the consumers those did not cover. Since
#75 the shared data guard, `validate_finite_data`, coerces an object array
and *returns* the coerced array. The five spectral entry points called it
and discarded the result, so an object array of ordinary floats passed the
guard and reached `np.fft.fft` as the original object array, dying with a
bare `TypeError` - outside the `ValueError` contract every one of them
documents. `gauss_filter` never called the guard at all and died inside
`scipy.ndimage.gaussian_filter` with a bare `RuntimeError`.

The consumers now compute with what the guard returns; `gauss_filter`
settles its dtype with `utils.coerce_numeric_data`, the guard's dtype half,
because NaN is allowed there (a windowed convolution widens a gap rather
than poisoning the whole output - see the sg_filter/gauss_filter note in
API.md).
"""

import numpy as np
import pytest

from baseTs import baseTs

FS = 2.0
N = 600


def _sine(f=0.05):
    return np.sin(2 * np.pi * f * np.arange(N) / FS)


def _as_object(values):
    return np.array(list(values), dtype=object)


def _ts(values):
    return baseTs(values, np.arange(N) / FS, freq=FS)


def _same(got, expected):
    """Equality across the shapes the entry points return: a baseTs, an
    array, a float, a (freqs, power) tuple or a BandPowerResult."""
    if isinstance(got, baseTs):
        assert got.dtype == expected.dtype == np.float64
        np.testing.assert_array_equal(got.values, expected.values)
    elif isinstance(got, np.ndarray):
        assert got.dtype.kind == "f"
        np.testing.assert_array_equal(got, expected)
    elif isinstance(got, tuple) and not hasattr(got, "_fields"):
        assert len(got) == len(expected)
        for g, e in zip(got, expected):
            _same(g, e)
    else:
        assert got == expected


SPECTRAL = [
    ("get_frequency_content", lambda ts: ts.get_frequency_content()),
    ("get_frequency_content-hann", lambda ts: ts.get_frequency_content(window='hann')),
    ("get_peak_freq", lambda ts: ts.get_peak_freq()),
    ("get_peak_freq-3", lambda ts: ts.get_peak_freq(num_pks=3)),
    ("compute_fft_power", lambda ts: ts.compute_fft_power()),
    ("compute_fft_power-raw", lambda ts: ts.compute_fft_power(demean=False, scale_power=False)),
    ("relative_band_power", lambda ts: ts.relative_band_power()),
    ("relative_band_power-details", lambda ts: ts.relative_band_power(details=True)),
    ("falff", lambda ts: ts.falff()),
]
SPECTRAL_IDS = [s[0] for s in SPECTRAL]

GAUSS = [
    ("gauss_filter", lambda ts: ts.gauss_filter(2.0)),
]

ENTRY_POINTS = SPECTRAL + GAUSS
ENTRY_POINT_IDS = [e[0] for e in ENTRY_POINTS]


# --- an object array of floats is the float array -----------------------------

class TestObjectArraysOfFloatsCompute:

    @pytest.mark.parametrize("name, run", ENTRY_POINTS, ids=ENTRY_POINT_IDS)
    def test_an_object_series_of_floats_gives_the_float_series_result(self, name, run):
        expected = run(_ts(_sine()))

        got = run(_ts(_as_object(_sine())))

        _same(got, expected)

    def test_constant_object_data_takes_the_dc_branch_like_float_data(self):
        """compute_fft_power's constant-signal branch reads the mean off the
        series again rather than off the validated array; it has to give the
        same DC power either way."""
        const = np.full(N, 3.0)
        expected = _ts(const).compute_fft_power(demean=False, scale_power=False)

        got = _ts(_as_object(const)).compute_fft_power(demean=False, scale_power=False)

        _same(got, expected)

    def test_the_spectral_family_still_reads_the_callers_series_after_demeaning(self):
        """compute_fft_power demeans in place on the array it computes with.
        The guard hands a numeric ndarray back *as is* - the same object -
        so computing with its return value must not demean the caller's
        series. Pins the copy the refactor keeps."""
        ts = _ts(_sine() + 5.0)
        before = ts.values.copy()

        ts.compute_fft_power(demean=True)

        np.testing.assert_array_equal(ts.values, before)


# --- what the guard refuses, the consumers refuse the same way ---------------

class TestTheGuardsRefusalsReachTheCaller:

    @pytest.mark.parametrize("name, run", ENTRY_POINTS, ids=ENTRY_POINT_IDS)
    def test_non_numeric_object_data_raises_the_guards_message(self, name, run):
        with pytest.raises(ValueError, match="not numeric"):
            run(_ts(_as_object(["1.5"] * N)))

    @pytest.mark.parametrize("name, run", SPECTRAL, ids=SPECTRAL_IDS)
    def test_complex_hiding_in_object_is_refused_by_the_spectral_family(self, name, run):
        """The spectral family refuses complex data (#43); an object array
        holding a complex value is the same input in a different box, and
        it is the guard - not the FFT - that has to say so."""
        z = _sine() + 0j
        with pytest.raises(ValueError, match="holding complex values"):
            run(_ts(_as_object(z)))


# --- gauss_filter: the dtype half of the guard, NaN allowed -------------------

class TestGaussFilterOnObjectDtype:

    def test_complex_hiding_in_object_filters_as_complex128(self):
        """Like the Butterworth family (#75): gaussian_filter handles a
        complex array part by part, so complex is allowed here and comes
        out as complex128."""
        z = np.exp(2j * np.pi * 0.05 * np.arange(N) / FS)
        expected = _ts(z).gauss_filter(2.0)

        got = _ts(_as_object(z)).gauss_filter(2.0)

        assert got.dtype == np.complex128
        np.testing.assert_array_equal(got.values, expected.values)

    def test_a_nan_in_an_object_series_stays_a_gap(self):
        """gauss_filter does not raise on NaN - a gap stays a gap, widened by
        the window (API.md). Settling the dtype must not smuggle the
        finiteness rule in with it, so this goes through the coercer, not
        the guard."""
        floats = _sine()
        floats[300:304] = np.nan
        expected = _ts(floats).gauss_filter(2.0)

        got = _ts(_as_object(floats)).gauss_filter(2.0)

        assert got.dtype == np.float64
        assert np.isnan(got.values).any()
        np.testing.assert_array_equal(got.values, expected.values)

    def test_none_is_a_gap_here_too(self):
        obj = _as_object(_sine())
        obj[300] = None

        got = _ts(obj).gauss_filter(2.0)

        assert got.dtype == np.float64
        assert np.isnan(got.values[300])

    def test_inplace_settles_the_dtype_on_the_series_itself(self):
        ts = _ts(_as_object(_sine()))
        assert ts.dtype == object

        ret = ts.gauss_filter(2.0, inplace=True)

        assert ret is ts
        assert ts.dtype == np.float64
        np.testing.assert_array_equal(ts.values, _ts(_sine()).gauss_filter(2.0).values)

    def test_a_numeric_series_is_filtered_as_given(self):
        """The coercer hands numeric arrays back untouched, so an integer
        series still filters the way scipy filters integers."""
        ints = (np.sin(2 * np.pi * 0.05 * np.arange(N) / FS) * 100).astype(int)
        from scipy.ndimage import gaussian_filter

        got = _ts(ints).gauss_filter(2.0)

        np.testing.assert_array_equal(got.values, gaussian_filter(ints, 2.0))
