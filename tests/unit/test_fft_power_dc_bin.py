"""compute_fft_power's constant-signal branch reports the FFT branch's DC bin (#98).

`compute_fft_power` has two branches. Data whose std is below 1e-15 takes
the constant branch, which wrote `power[0] = mean**2`; anything else takes
the FFT branch, `np.abs(fft)**2 / n`, whose DC bin is `|n * mean|**2 / n =
n * mean**2`. So with `scale_power=False` a constant series and one nudged
one ulp-cluster past the threshold reported DC powers a factor of `n`
apart (9.0 vs 5400 for 600 samples of 3.0), and the "600x" that #93's and
#96's entries report for a float32 series was this factor, not precision.

The constant branch now reports `n * mean**2`, what its own FFT branch
would compute, so the function has one scaling. `get_frequency_content`
is a different function with a different scaling (`np.abs(fft)**2`, not
divided by `n`: `(n * mean)**2` for a constant series) and is not changed
here; the issue's comment records the three conventions as measured.
"""

import numpy as np
import pytest

from baseTs import baseTs

N = 600
FS = 2.0


def _ts(values):
    return baseTs(values, np.arange(N) / FS, freq=FS)


# 1e-8 is the case pytest.approx's default absolute tolerance (1e-12) would
# wave through: n * c**2 is 6e-14 and c**2 is 1e-16, closer than 1e-12.
# Every comparison below passes abs=0 for that reason.
CONSTANTS = [3.0, 0.1, -2.5, 1e-8]


class TestTheConstantBranchReportsTheFftBranchsDcBin:

    @pytest.mark.parametrize("c", CONSTANTS)
    def test_dc_is_n_times_mean_squared(self, c):
        freqs, power = _ts(np.full(N, c)).compute_fft_power(demean=False, scale_power=False)

        assert power[0] == pytest.approx(N * c ** 2, rel=1e-12, abs=0)
        assert not power[1:].any()

    @pytest.mark.parametrize("c", CONSTANTS)
    def test_dc_is_what_the_fft_itself_gives(self, c):
        """The number the FFT branch would have produced for the same
        array, computed here the way that branch computes it."""
        data = np.full(N, c)
        expected = (np.abs(np.fft.fft(data)) ** 2 / N)[0]

        _, power = _ts(data).compute_fft_power(demean=False, scale_power=False)

        assert power[0] == pytest.approx(expected, rel=1e-12, abs=0)

    def test_the_two_branches_agree_across_the_threshold(self):
        """600 samples of 3.0, and the same with every other sample raised
        by 1e-13: std 0 and 5e-14, one each side of 1e-15. The DC bins
        were 9.0 and 5400; they now differ by the nudge alone."""
        base = np.full(N, 3.0)
        nudged = base.copy()
        nudged[::2] += 1e-13
        assert np.std(base) < 1e-15 < np.std(nudged)

        _, constant = _ts(base).compute_fft_power(demean=False, scale_power=False)
        _, fft_branch = _ts(nudged).compute_fft_power(demean=False, scale_power=False)

        assert constant[0] == pytest.approx(fft_branch[0], rel=1e-9, abs=0)


class TestWhatDoesNotChange:

    def test_demeaned_constant_data_has_no_power(self):
        _, power = _ts(np.full(N, 3.0)).compute_fft_power(demean=True, scale_power=False)
        assert not power.any()

    def test_scaled_constant_data_is_all_dc(self):
        """Under the default scale_power=True the DC bin is the only
        non-zero one on either branch, so it normalises to 1.0 regardless
        of the scaling - which is why the factor of n was invisible."""
        _, power = _ts(np.full(N, 3.0)).compute_fft_power(demean=False, scale_power=True)
        assert power[0] == 1.0
        assert not power[1:].any()

    def test_the_agreement_is_to_precision_and_ends_at_overflow(self):
        """Review round 1: `n * mean**2` reimplements the FFT branch's DC
        bin rather than computing it, so the two agree to a few ulps (the
        rel=1e-12 above), and part company where `np.abs(fft)**2` overflows
        before its division. Observed and pinned, not a defect this change
        makes: a constant of 1e152 stays finite on the constant branch
        while a series of that magnitude with enough spread to take the
        FFT branch reports inf at DC."""
        _, constant = _ts(np.full(N, 1e152)).compute_fft_power(demean=False, scale_power=False)
        spread = np.full(N, 1e152)
        spread[::2] += 1e137
        assert np.std(spread) > 1e-15
        with pytest.warns(RuntimeWarning, match="overflow"):
            _, fft_branch = _ts(spread).compute_fft_power(demean=False, scale_power=False)

        assert np.isfinite(constant[0])
        assert constant[0] == pytest.approx(N * 1e304, rel=1e-12, abs=0)
        assert np.isinf(fft_branch[0])

    def test_get_frequency_content_keeps_its_own_scaling(self):
        """Observed and not changed: a different function, not divided by n."""
        _, power = _ts(np.full(N, 3.0)).get_frequency_content()
        assert power[0] == pytest.approx((N * 3.0) ** 2, rel=1e-12, abs=0)
