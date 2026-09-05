"""compute_fft_power computes on a float64 copy of the validated data (#96).

The shared data guard, `validate_finite_data`, admits integer and bool
data (neither can hold NaN) and hands numeric arrays back as they are.
`compute_fft_power` then demeaned *in place* on a copy of that array, and
numpy refuses to write a float difference into an integer or bool array
under its `same_kind` casting rule - a bare `UFuncTypeError`, outside the
`ValueError` contract the docstring makes, from the one spectral entry
point that demeans by hand. The other four accept both dtypes.

The sibling found by #93's review: the constancy check
(`np.std(data) < 1e-15`) was taken in the input's own precision, where
`relative_band_power` has always taken it in float64, so a float32 series
could get the other verdict.

Both settle on one line: compute on `validate_finite_data(...).astype(float)`,
a float64 copy. The tests below pin what that buys - and what it changes:
on numpy 2.x the FFT of a float32 array is taken in float32 (and on either
numpy the demeaning was), so a float32 series' spectrum now matches its
float64 cast's, and the returned power is float64 for every accepted dtype,
as the annotation says.
"""

import numpy as np
import pytest

from baseTs import baseTs

FS = 2.0
N = 600


def _sine(f=0.05):
    return np.sin(2 * np.pi * f * np.arange(N) / FS)


def _ts(values):
    return baseTs(values, np.arange(N) / FS, freq=FS)


def _assert_same_spectrum(got, expected):
    freqs, power = got
    exp_freqs, exp_power = expected
    assert freqs.dtype == np.float64
    assert power.dtype == np.float64
    np.testing.assert_array_equal(freqs, exp_freqs)
    np.testing.assert_array_equal(power, exp_power)


SETTINGS = [
    dict(demean=True, scale_power=True),
    dict(demean=True, scale_power=False),
    dict(demean=False, scale_power=True),
    dict(demean=False, scale_power=False),
]
SETTING_IDS = ["demean-scaled", "demean-raw", "raw-scaled", "raw-raw"]

NON_FLOAT = [
    (_sine() * 100).astype(np.int64),
    (_sine() * 100).astype(np.int8),
    (_sine() * 100 + 100).astype(np.uint8),
    _sine() > 0,
]
NON_FLOAT_IDS = ["int64", "int8", "uint8", "bool"]


# --- the defect: integer and bool data could not be demeaned -----------------

class TestIntegerAndBoolDataCompute:

    @pytest.mark.parametrize("values", NON_FLOAT, ids=NON_FLOAT_IDS)
    @pytest.mark.parametrize("kw", SETTINGS, ids=SETTING_IDS)
    def test_a_non_float_series_gives_its_float64_casts_spectrum(self, values, kw):
        """`demean=True` on an integer or bool series raised numpy's bare
        `UFuncTypeError` (`Cannot cast ufunc 'subtract' output from
        dtype('float64') to dtype('int64')`); `demean=False` on the same
        series worked. Both now give exactly what the float64 cast of the
        series gives - the float cast is what `np.fft.fft` computes on for
        these dtypes anyway, so `demean=False` is a pin and `demean=True`
        the fix."""
        expected = _ts(values.astype(float)).compute_fft_power(**kw)

        got = _ts(values).compute_fft_power(**kw)

        _assert_same_spectrum(got, expected)

    def test_integer_data_reaches_the_utils_function_the_same_way(self):
        """The method is a one-line wrapper; this pins the free function's
        own signature (demean is its second positional)."""
        from baseTs.utils import compute_fft_power

        values = NON_FLOAT[0]
        expected = compute_fft_power(_ts(values.astype(float)), True, False)

        got = compute_fft_power(_ts(values), True, False)

        _assert_same_spectrum(got, expected)


# --- the sibling: the working array is float64 whatever the input ------------

class TestTheWorkingArrayIsFloat64:

    def test_constancy_is_judged_in_float64_for_a_float32_series(self):
        """The review of #93 built a float32 series the two precisions
        disagree on: alternating between two adjacent float32 values near
        2.9e-8, its float64 std is 8.9e-16 (constant: the DC branch) and its
        float32 std is 1.3e-15 (the FFT branch). Until #98 the two branches
        reported DC bins a factor of n apart (`mean**2` vs `n * mean**2`),
        which is how the verdict was visible; they agree now, so this pins
        the verdict by result equality with the float64 series alone.
        `relative_band_power` has always judged in float64; this pins
        compute_fft_power to the same verdict, which is the float64 series'
        verdict."""
        f32 = np.where(np.arange(N) % 2 == 0, np.float32(2.8994840e-08),
                       np.float32(2.8994842e-08)).astype(np.float32)
        assert np.std(f32.astype(np.float64)) < 1e-15 < np.std(f32)
        expected = _ts(f32.astype(np.float64)).compute_fft_power(demean=False, scale_power=False)

        got = _ts(f32).compute_fft_power(demean=False, scale_power=False)

        _assert_same_spectrum(got, expected)
        assert got[1][0] == pytest.approx(N * np.mean(f32.astype(np.float64)) ** 2, abs=0)

    @pytest.mark.parametrize("dtype", [np.float32, np.float16], ids=["float32", "float16"])
    @pytest.mark.parametrize("kw", SETTINGS, ids=SETTING_IDS)
    def test_a_narrow_float_series_gives_its_float64_casts_spectrum(self, dtype, kw):
        """numpy 2.x takes the FFT of a float32 array in float32 and returns
        a float32 power; numpy 1.x widened the FFT to float64 but the
        in-place demeaning before it still ran in float32 (measured on
        main under numpy 1.26: the two `demean=True` float32 cases differ
        from the float64 cast's, the other six match). The annotation says
        float64, and a spectrum that depends on the numpy major version is
        not one contract. Computing on the float64 copy, a float32 or
        float16 series gives the spectrum of its float64 cast, bit for bit,
        on either numpy."""
        values = _sine().astype(dtype)
        expected = _ts(values.astype(np.float64)).compute_fft_power(**kw)

        got = _ts(values).compute_fft_power(**kw)

        _assert_same_spectrum(got, expected)

    @pytest.mark.parametrize("values", [_sine() + 5.0, NON_FLOAT[0], NON_FLOAT[3]],
                             ids=["float64", "int64", "bool"])
    def test_the_callers_series_is_untouched(self, values):
        """The demeaning is still an in-place subtraction, so the float64
        copy is load-bearing: `astype(float, copy=False)` would hand a
        float64 series' own array back and demean the caller's series -
        on pandas 2; on pandas 3 that array is read-only under
        copy-on-write and the subtraction raises instead (review). This
        fails either way."""
        ts = _ts(values)
        before = ts.values.copy()

        ts.compute_fft_power(demean=True)

        np.testing.assert_array_equal(ts.values, before)
        assert ts.dtype == values.dtype


# --- the array computed on is the guard's, not a second cast of the raw one --

class TestTheGuardsArrayIsTheOneComputedOn:

    def test_an_object_element_that_converts_once_is_converted_once(self):
        """#93's rule, which the object-array-of-floats tests cannot pin:
        `np.array(obj, dtype=float)` converts a column of ordinary floats
        the same way the guard does, so discarding the guard's array and
        casting `ts.data` again passes every one of them (a mutant that
        survived). An element whose `__float__` answers once and then
        raises tells the two apart: the guard converts it, and whatever
        is computed on must be the array the guard handed back."""
        import numbers

        @numbers.Real.register
        class _ConvertsOnce:
            def __init__(self, value):
                self._value = float(value)
                self._spent = False

            def __float__(self):
                if self._spent:
                    raise RuntimeError("converted a second time")
                self._spent = True
                return self._value

        values = _sine()
        expected = _ts(values).compute_fft_power()

        got = _ts(np.array([_ConvertsOnce(v) for v in values], dtype=object)).compute_fft_power()

        _assert_same_spectrum(got, expected)
