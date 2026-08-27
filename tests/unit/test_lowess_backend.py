"""Tests for the statsmodels LOWESS backend of LowessOutlierFilter.

Covers the swap away from moepy: that the statsmodels path is genuinely live,
that config knobs reach it, that the deprecated num_fits parameter is inert,
and the non-finite input edge cases the old backend never had to handle.
"""
import builtins
import logging
import warnings

import numpy as np
import pytest

from baseTs import baseTs
from baseTs.LowessOutlierFilter import (
    MIN_WINDOW_POINTS,
    SCALE_FLOOR,
    FilterConfig,
    LowessOutlierFilter,
)


class TestBackendIsStatsmodels:
    def test_moepy_is_not_imported(self, spiked):
        """The filter must work with moepy made unimportable."""
        d, t = spiked
        real_import = builtins.__import__

        def blocked(name, *args, **kwargs):
            if name == "moepy" or name.startswith("moepy."):
                raise ImportError("moepy is blocked for this test")
            return real_import(name, *args, **kwargs)

        f = LowessOutlierFilter(FilterConfig(frac=0.1, z_threshold=5.0))
        builtins.__import__ = blocked
        try:
            cleaned, idx, line = f.filter(d, t, return_lowess=True)
        finally:
            builtins.__import__ = real_import

        assert len(idx) > 0
        assert np.all(np.isfinite(line))
        assert len(line) == len(d)

    def test_no_moepy_in_package_source(self):
        """Guard against the dependency creeping back in."""
        from pathlib import Path

        import baseTs as pkg

        offenders = [
            p.name
            for p in Path(pkg.__file__).parent.glob("*.py")
            if "import moepy" in p.read_text() or "from moepy" in p.read_text()
        ]
        assert offenders == []


class TestConfigReachesTheFit:
    def test_it_is_honored(self, spiked):
        """config.it must reach statsmodels, not be hardcoded."""
        d, t = spiked
        captured = []
        f = LowessOutlierFilter(FilterConfig(frac=0.1, it=2))

        from statsmodels.nonparametric import smoothers_lowess

        real = smoothers_lowess.lowess

        def spy(*args, **kwargs):
            captured.append(kwargs)
            return real(*args, **kwargs)

        smoothers_lowess.lowess = spy
        try:
            f.filter(d, t, return_lowess=True)
        finally:
            smoothers_lowess.lowess = real

        assert captured, "statsmodels lowess was never called"
        assert all(c["it"] == 2 for c in captured)

    def test_it_defaults_to_zero(self):
        assert FilterConfig().it == 0

    def test_delta_frac_defaults_to_exact_fit(self):
        assert FilterConfig().delta_frac == 0.0

    def test_delta_frac_scales_by_x_range(self, spiked):
        """delta must be delta_frac * ptp(x), not delta_frac itself."""
        d, t = spiked
        captured = []
        f = LowessOutlierFilter(FilterConfig(frac=0.1, delta_frac=0.01))

        from statsmodels.nonparametric import smoothers_lowess

        real = smoothers_lowess.lowess

        def spy(*args, **kwargs):
            captured.append(kwargs)
            return real(*args, **kwargs)

        smoothers_lowess.lowess = spy
        try:
            f.filter(d, t, return_lowess=True)
        finally:
            smoothers_lowess.lowess = real

        assert captured
        assert captured[0]["delta"] == pytest.approx(0.01 * np.ptp(t))

    def test_delta_frac_zero_means_delta_zero(self, spiked):
        d, t = spiked
        captured = []
        f = LowessOutlierFilter(FilterConfig(frac=0.1, delta_frac=0.0))

        from statsmodels.nonparametric import smoothers_lowess

        real = smoothers_lowess.lowess

        def spy(*args, **kwargs):
            captured.append(kwargs)
            return real(*args, **kwargs)

        smoothers_lowess.lowess = spy
        try:
            f.filter(d, t, return_lowess=True)
        finally:
            smoothers_lowess.lowess = real

        assert captured[0]["delta"] == 0.0


class TestNumFitsDeprecation:
    def test_keyword_warns(self, spiked):
        d, t = spiked
        ts = baseTs(data=d, times=t)
        with pytest.warns(DeprecationWarning, match="num_fits is deprecated"):
            ts.set_outlier_filter(num_fits=50)

    def test_params_dict_warns(self, spiked):
        d, t = spiked
        ts = baseTs(data=d, times=t)
        with pytest.warns(DeprecationWarning, match="num_fits is deprecated"):
            ts.set_outlier_filter(params={"frac": 0.1, "num_fits": 50})

    def test_omitting_it_is_silent(self, spiked):
        d, t = spiked
        ts = baseTs(data=d, times=t)
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            ts.set_outlier_filter(frac=0.1, z_threshold=5.0)

    def test_num_fits_does_not_survive_on_config(self, spiked):
        """The unslotted dataclass must not resurrect the attribute."""
        d, t = spiked
        ts = baseTs(data=d, times=t)
        with pytest.warns(DeprecationWarning):
            ts.set_outlier_filter(num_fits=50)
        assert "num_fits" not in ts.get_outlier_filter_params()
        assert not hasattr(ts.outlier_filter.config, "num_fits")

    def test_num_fits_in_params_does_not_land_on_config(self, spiked):
        d, t = spiked
        ts = baseTs(data=d, times=t)
        with pytest.warns(DeprecationWarning):
            ts.set_outlier_filter(params={"frac": 0.1, "num_fits": 50})
        assert not hasattr(ts.outlier_filter.config, "num_fits")
        assert ts.get_outlier_filter_params()["frac"] == 0.1


class TestNonFiniteInput:
    def test_nan_input_preserves_length(self, spiked):
        """statsmodels defaults to missing='drop'; return_sorted=False must
        re-insert NaN so the output length still matches the input."""
        d, t = spiked
        d = d.copy()
        d[10] = np.nan
        d[400] = np.nan
        f = LowessOutlierFilter(FilterConfig(frac=0.1, z_threshold=5.0))
        cleaned, idx, line = f.filter(d, t, return_lowess=True)
        assert len(cleaned) == len(d)
        assert len(line) == len(d)

        # The two input NaNs stay NaN (#36): an acquisition gap is not an
        # outlier, and filling it returns synthetic samples with nothing left
        # to mark them. This assertion used to be `np.all(np.isfinite(...))`,
        # which pinned the fill-everything behaviour that issue removed.
        assert np.isnan(cleaned[[10, 400]]).all()
        others = np.delete(cleaned, [10, 400])
        assert np.all(np.isfinite(others))

    def test_nan_input_is_filled_when_asked(self, spiked):
        """fill_input_gaps=True restores the pre-#36 behaviour."""
        d, t = spiked
        d = d.copy()
        d[10] = np.nan
        d[400] = np.nan
        f = LowessOutlierFilter(
            FilterConfig(frac=0.1, z_threshold=5.0, fill_input_gaps=True)
        )
        cleaned, idx, line = f.filter(d, t, return_lowess=True)
        assert len(cleaned) == len(d)
        assert np.all(np.isfinite(cleaned))

    def test_inf_input_does_not_crash(self, spiked):
        """~np.isnan does not catch inf, but statsmodels drops on isfinite.

        The inf therefore yields NaN in the fit at that index rather than an
        exception. Pinning the behavior so a future change is a visible break.
        """
        d, t = spiked
        d = d.copy()
        d[200] = np.inf
        f = LowessOutlierFilter(FilterConfig(frac=0.1, z_threshold=5.0))
        cleaned, idx, line = f.filter(d, t, return_lowess=True)
        assert len(cleaned) == len(d)
        assert len(line) == len(d)

    def test_unsorted_x_is_handled(self, spiked):
        """statsmodels is_sorted=False must cope with permuted input."""
        d, t = spiked
        rng = np.random.default_rng(1)
        perm = rng.permutation(len(d))
        f = LowessOutlierFilter(FilterConfig(frac=0.1, z_threshold=5.0))
        _, _, line_sorted = f.filter(d, t, return_lowess=True)
        _, _, line_perm = f.filter(d[perm], t[perm], return_lowess=True)
        inv = np.argsort(perm)
        assert np.allclose(line_perm[inv], line_sorted, atol=1e-10)

    def test_duplicate_x_values(self, spiked):
        """Real cpCST files contain one duplicate timestamp each."""
        d, t = spiked
        t = t.copy()
        t[100] = t[99]
        f = LowessOutlierFilter(FilterConfig(frac=0.1, z_threshold=5.0))
        cleaned, _, line = f.filter(d, t, return_lowess=True)
        assert len(line) == len(d)
        assert np.all(np.isfinite(cleaned))


class TestScaleFloorWarning:
    @pytest.mark.parametrize(
        "label,data,frac,it",
        [
            # The real-world case: a staircase signal (like cpCST lambda_val)
            # fitted with internal robustifying iterations.
            ("staircase", np.repeat(np.arange(20, dtype=float), 20), 0.05, 3),
            # Deterministic and independent of `it`: LOWESS fits a line exactly.
            ("line", 2.0 * np.arange(400, dtype=float) + 1.0, 0.3, 0),
        ],
    )
    def test_warns_when_scale_collapses(self, label, data, frac, it):
        """A perfectly-fit signal drives MAD to zero; z_threshold then means
        nothing, so the clamp must announce itself rather than pass silently.

        Asserted through `warnings`, not `logging`: this tells the caller their
        result is meaningless and must reach them under default configuration.
        """
        t = np.arange(len(data), dtype=float)
        f = LowessOutlierFilter(FilterConfig(frac=frac, z_threshold=3.0, it=it))
        with pytest.warns(RuntimeWarning, match="below the .* floor"):
            f.filter(data, t, return_lowess=True)

    def test_no_warning_on_well_behaved_data(self, spiked):
        d, t = spiked
        f = LowessOutlierFilter(FilterConfig(frac=0.1, z_threshold=5.0))
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            f.filter(d, t, return_lowess=True)

    def test_scale_floor_constant_is_exported(self):
        assert SCALE_FLOOR == 1e-6


class TestWindowGuard:
    """A window of <= 3 points makes LOWESS interpolate the data exactly.

    The fit is then the input, every residual is zero, the MAD scale collapses
    and z_threshold stops discriminating — a result that looks like a clean
    signal. The threshold is on the window `int(frac * n)`, not on `frac`:
    frac=0.001 is fine on a long series and degenerate on a short one.
    """

    @pytest.mark.parametrize("frac", [1e-9, 0.001, 0.003, 0.006])
    def test_tiny_frac_on_long_series_raises(self, frac):
        d, t = np.arange(500, dtype=float), np.arange(500, dtype=float)
        f = LowessOutlierFilter(FilterConfig(frac=frac))
        with pytest.raises(ValueError, match="local window"):
            f.filter(d, t, return_lowess=True)

    def test_reasonable_frac_on_short_series_raises(self):
        """The same default frac that is fine at n=500 is degenerate at n=20."""
        d, t = np.arange(20, dtype=float), np.arange(20, dtype=float)
        f = LowessOutlierFilter(FilterConfig(frac=0.075))  # k = 1
        with pytest.raises(ValueError, match="local window"):
            f.filter(d, t, return_lowess=True)

    def test_series_too_short_for_any_frac(self):
        d, t = np.arange(3, dtype=float), np.arange(3, dtype=float)
        f = LowessOutlierFilter(FilterConfig(frac=1.0))
        with pytest.raises(ValueError, match="No frac can rescue"):
            f.filter(d, t, return_lowess=True)

    def test_error_names_a_frac_that_works(self):
        """The suggested frac must actually satisfy the guard."""
        n = 60
        d, t = np.arange(n, dtype=float), np.arange(n, dtype=float)
        f = LowessOutlierFilter(FilterConfig(frac=0.01))
        with pytest.raises(ValueError) as exc:
            f.filter(d, t, return_lowess=True)
        suggested = float(str(exc.value).split("frac >= ")[1].split()[0])
        assert int(suggested * n) >= MIN_WINDOW_POINTS

    @pytest.mark.parametrize("n,frac", [(500, 0.008), (100, 0.04), (50, 0.08), (20, 0.2)])
    def test_smallest_passing_window_is_accepted(self, n, frac):
        """k == 4 must be allowed: the guard rejects degenerate, not merely small."""
        assert int(frac * n) == MIN_WINDOW_POINTS
        rng = np.random.default_rng(0)
        t = np.linspace(0, 10, n)
        d = np.sin(t) + 0.1 * rng.standard_normal(n)
        f = LowessOutlierFilter(FilterConfig(frac=frac, z_threshold=5.0))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)  # may stop early; see below
            _, _, line = f.filter(d, t, return_lowess=True)
        assert len(line) == n
        assert not np.allclose(line, d, atol=1e-12), "should fit, not interpolate"

    def test_stops_early_when_masking_shrinks_the_window(self):
        """A run starting at exactly k == 4 falls to k == 3 after one removal.

        The loop must stop and keep the last sound fit rather than overwrite it
        with one that interpolates the survivors exactly.
        """
        n, frac = 500, 0.008
        rng = np.random.default_rng(0)
        t = np.linspace(0, 10, n)
        d = np.sin(t) + 0.1 * rng.standard_normal(n)
        f = LowessOutlierFilter(FilterConfig(frac=frac, z_threshold=5.0))
        with pytest.warns(RuntimeWarning, match="Stopping after"):
            _, _, line = f.filter(d, t, return_lowess=True)
        # The retained fit is the sound one, not an interpolation of the data.
        assert not np.allclose(line, d, atol=1e-12)
        assert np.all(np.isfinite(line))

    def test_comfortable_window_does_not_stop_early(self, spiked):
        d, t = spiked
        f = LowessOutlierFilter(FilterConfig(frac=0.1, z_threshold=5.0))
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            f.filter(d, t, return_lowess=True)

    def test_guard_counts_usable_points_not_length(self):
        """NaNs do not count towards the window: 500 slots, 10 real points."""
        d = np.full(500, np.nan)
        d[:10] = np.arange(10, dtype=float)
        t = np.arange(500, dtype=float)
        f = LowessOutlierFilter(FilterConfig(frac=0.1))  # k=50 on length, k=1 on usable
        with pytest.raises(ValueError, match="local window"):
            f.filter(d, t, return_lowess=True)

    def test_guard_reaches_filter_outliers(self, spiked):
        d, t = spiked
        ts = baseTs(data=d, times=t)
        ts.set_outlier_filter(frac=0.001)
        with pytest.raises(ValueError, match="local window"):
            ts.filter_outliers()

    def test_guard_reaches_lowess_detrend(self, spiked):
        """The issue was reported through lowess_detrend, which returned all-zero
        detrended data because the trend was the data."""
        d, t = spiked
        with pytest.raises(ValueError, match="local window"):
            baseTs(data=d, times=t).lowess_detrend(frac=0.001, inplace=False)


class TestArgumentOrder:
    """statsmodels is lowess(endog, exog) = (y, x); moepy was fit(x, y).

    Transposing them is the single most likely way to break this file, and the
    detection tests alone do not catch it, so assert the fit directly.
    """

    def test_fit_tracks_the_signal_not_the_time_axis(self):
        # A signal whose shape is unmistakable if fitted correctly, and which
        # cannot be confused with x: y is bounded, x climbs to 100.
        x = np.linspace(0, 100, 400)
        y = np.sin(2 * np.pi * x / 100.0)
        f = LowessOutlierFilter(FilterConfig(frac=0.3, z_threshold=10.0))
        _, _, line = f.filter(y, x, return_lowess=True)
        # A correct fit follows y closely; a transposed one returns something on
        # the scale of x (0..100) and correlates with x instead.
        assert np.max(np.abs(line - y)) < 0.1, "fit does not track the signal"
        assert np.corrcoef(line, y)[0, 1] > 0.99

    def test_fit_is_not_a_function_of_x(self):
        """Same y, x stretched: the fitted values must be essentially unchanged."""
        x = np.linspace(0, 10, 300)
        y = np.sin(2 * np.pi * x / 10.0)
        f = LowessOutlierFilter(FilterConfig(frac=0.3, z_threshold=10.0))
        _, _, a = f.filter(y, x, return_lowess=True)
        _, _, b = f.filter(y, x * 1000.0, return_lowess=True)
        assert np.allclose(a, b, atol=1e-8)


class TestSignatureCompatibility:
    """num_fits must keep its positional slot; the new knobs are keyword-only."""

    def test_ninth_positional_is_still_num_fits(self, spiked):
        from baseTs.LowessOutlierFilter import TailType

        d, t = spiked
        ts = baseTs(data=d, times=t)
        with pytest.warns(DeprecationWarning, match="num_fits is deprecated"):
            ts.set_outlier_filter(
                None, 7, 0.075, 10, 'linear', 2, True, TailType.BOTH, 25
            )
        # 25 must not have landed on `it`, which would mean 25 robustifying
        # LOWESS iterations and a destroyed z_threshold.
        assert ts.get_outlier_filter_params()["it"] == 0

    def test_it_and_delta_frac_are_keyword_only(self, spiked):
        from baseTs.LowessOutlierFilter import TailType

        d, t = spiked
        ts = baseTs(data=d, times=t)
        with pytest.raises(TypeError):
            ts.set_outlier_filter(
                None, 7, 0.075, 10, 'linear', 2, True, TailType.BOTH, None, 2
            )


class TestDetectionStillWorks:
    def test_finds_injected_spikes(self, spiked):
        d, t = spiked
        f = LowessOutlierFilter(FilterConfig(frac=0.1, z_threshold=5.0))
        _, idx, _ = f.filter(d, t, return_lowess=True)
        assert any(abs(i - 150) <= 2 for i in idx)
        assert any(abs(i - 350) <= 2 for i in idx)

    def test_filtering_reduces_spread(self, spiked):
        d, t = spiked
        f = LowessOutlierFilter(FilterConfig(frac=0.1, z_threshold=5.0))
        cleaned, _, _ = f.filter(d, t, return_lowess=True)
        assert np.std(cleaned) < np.std(d)
