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
    SCALE_FLOOR,
    FilterConfig,
    LowessOutlierFilter,
)


@pytest.fixture
def spiked():
    """Sine with two large, unambiguous spikes."""
    t = np.linspace(0, 10, 500)
    d = np.sin(2 * np.pi * 0.5 * t) + 0.05 * np.random.default_rng(0).standard_normal(500)
    d[150] += 5.0
    d[350] -= 5.0
    return d, t


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
    def test_warns_when_scale_collapses(self, caplog, label, data, frac, it):
        """A perfectly-fit signal drives MAD to zero; z_threshold then means
        nothing, so the clamp must announce itself rather than pass silently."""
        t = np.arange(len(data), dtype=float)
        f = LowessOutlierFilter(FilterConfig(frac=frac, z_threshold=3.0, it=it))
        with caplog.at_level(logging.WARNING, logger="baseTs.LowessOutlierFilter"):
            f.filter(data, t, return_lowess=True)
        assert any("floor" in r.message.lower() for r in caplog.records), caplog.text

    def test_no_warning_on_well_behaved_data(self, spiked, caplog):
        d, t = spiked
        f = LowessOutlierFilter(FilterConfig(frac=0.1, z_threshold=5.0))
        with caplog.at_level(logging.WARNING, logger="baseTs.LowessOutlierFilter"):
            f.filter(d, t, return_lowess=True)
        assert not any("floor" in r.message.lower() for r in caplog.records)

    def test_scale_floor_constant_is_exported(self):
        assert SCALE_FLOOR == 1e-6


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
