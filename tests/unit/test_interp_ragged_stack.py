"""interp_to_uniform_grid: fill_value pads outside the data, max_gap refuses to
bridge wide interior gaps.

Motivated by a tester averaging cpCST crash epochs: the trials are of
different lengths, and the period right after the crash carries a ~2.6 s
hole. Padding the ragged tails with NaN lets ``baseDf.from_series`` stack
them; ``max_gap`` keeps the interior hole honest instead of drawing a
straight line across the recovery window.
"""
import numpy as np
import pytest

from baseTs import baseTs
from baseTs.frame import baseDf
from baseTs.utils import ValidationError


def _trial(n: int, dt: float = 0.1) -> baseTs:
    """A trial of n samples at 1/dt Hz, data == time so interpolation is exact."""
    t = np.arange(n) * dt
    return baseTs(t.copy(), t, freq=1.0 / dt)


def _gapped(gap_from: float, gap_to: float, dt: float = 0.1, end: float = 5.0) -> baseTs:
    """A trial with a hole in its timestamps between gap_from and gap_to."""
    t = np.arange(0.0, end, dt)
    t = t[(t <= gap_from) | (t >= gap_to)]
    return baseTs(t.copy(), t)


class TestFillValue:
    def test_default_still_raises_outside_the_data(self):
        """Unchanged default: a grid past the data is an error, not silent NaN."""
        ts = _trial(10)
        with pytest.raises(ValueError):
            ts.interp_to_uniform_grid(np.arange(0, 2.0, 0.1), inplace=False)

    def test_nan_pads_beyond_the_last_sample(self):
        ts = _trial(10)  # covers 0.0 .. 0.9
        grid = np.arange(0, 2.0, 0.1)
        out = ts.interp_to_uniform_grid(grid, fill_value=np.nan, inplace=False)
        vals = np.asarray(out.data, float)
        inside = grid <= 0.9 + 1e-9
        assert np.allclose(vals[inside], grid[inside])
        assert np.all(np.isnan(vals[~inside]))
        assert len(out) == len(grid)

    def test_nan_pads_before_the_first_sample(self):
        t = np.arange(1.0, 2.0, 0.1)
        ts = baseTs(t.copy(), t)
        grid = np.arange(0.0, 2.0, 0.1)
        out = ts.interp_to_uniform_grid(grid, fill_value=np.nan, inplace=False)
        vals = np.asarray(out.data, float)
        assert np.all(np.isnan(vals[grid < 1.0 - 1e-9]))
        assert not np.any(np.isnan(vals[grid >= 1.0 - 1e-9]))

    def test_numeric_fill_value_is_used_verbatim(self):
        ts = _trial(10)
        grid = np.arange(0, 2.0, 0.1)
        out = ts.interp_to_uniform_grid(grid, fill_value=0.0, inplace=False)
        vals = np.asarray(out.data, float)
        assert np.all(vals[grid > 0.9 + 1e-9] == 0.0)

    def test_history_counts_padded_points(self):
        ts = _trial(10)
        grid = np.arange(0, 2.0, 0.1)  # 20 points, 10 outside
        out = ts.interp_to_uniform_grid(grid, fill_value=np.nan, inplace=False)
        assert any("10 grid point(s) outside the data padded" in e for e in out.history)

    def test_history_silent_when_nothing_padded(self):
        ts = _trial(10)
        out = ts.interp_to_uniform_grid(np.arange(0, 0.9, 0.05),
                                        fill_value=np.nan, inplace=False)
        assert not any("padded" in e for e in out.history)

    def test_inplace_path_pads_too(self):
        ts = _trial(10)
        grid = np.arange(0, 2.0, 0.1)
        ts.interp_to_uniform_grid(grid, fill_value=np.nan, inplace=True)
        assert len(ts) == len(grid)
        assert np.isnan(np.asarray(ts.data, float)[-1])
        assert ts.is_interpolated

    @pytest.mark.parametrize("bad", ["nan", "extrapolate", [0.0], True])
    def test_refuses_non_numeric_fill_value(self, bad):
        ts = _trial(10)
        with pytest.raises(ValidationError, match="fill_value"):
            ts.interp_to_uniform_grid(np.arange(0, 2.0, 0.1),
                                      fill_value=bad, inplace=False)


class TestMaxGap:
    def test_default_bridges_interior_gaps(self):
        """Unchanged default: a hole in the timestamps is linearly bridged."""
        ts = _gapped(1.0, 3.6)
        out = ts.interp_to_uniform_grid(np.arange(0, 4.9, 0.1), inplace=False)
        assert not np.any(np.isnan(np.asarray(out.data, float)))

    def test_blanks_points_inside_a_gap_wider_than_max_gap(self):
        ts = _gapped(1.0, 3.6)  # 2.6 s hole, the cpCST post-crash case
        grid = np.arange(0, 4.9, 0.1)
        out = ts.interp_to_uniform_grid(grid, max_gap=1.0, inplace=False)
        vals = np.asarray(out.data, float)
        in_hole = (grid > 1.0 + 1e-9) & (grid < 3.6 - 1e-9)
        assert np.all(np.isnan(vals[in_hole]))
        assert not np.any(np.isnan(vals[~in_hole]))

    def test_gap_edges_keep_their_sample_values(self):
        """A grid point landing exactly on a sample is data, not a bridge."""
        ts = _gapped(1.0, 3.6)
        out = ts.interp_to_uniform_grid(np.array([0.5, 1.0, 2.0, 3.6, 4.0]),
                                        max_gap=1.0, inplace=False)
        vals = np.asarray(out.data, float)
        assert np.allclose(vals[[0, 1, 3, 4]], [0.5, 1.0, 3.6, 4.0])
        assert np.isnan(vals[2])

    def test_gaps_narrower_than_max_gap_are_bridged(self):
        ts = _gapped(1.0, 1.5)  # 0.5 s hole
        out = ts.interp_to_uniform_grid(np.arange(0, 4.9, 0.1), max_gap=1.0, inplace=False)
        assert not np.any(np.isnan(np.asarray(out.data, float)))

    def test_history_counts_blanked_points(self):
        ts = _gapped(1.0, 3.6)
        grid = np.arange(0, 4.9, 0.1)
        out = ts.interp_to_uniform_grid(grid, max_gap=1.0, inplace=False)
        n = int(np.count_nonzero((grid > 1.0 + 1e-9) & (grid < 3.6 - 1e-9)))
        assert any(f"{n} grid point(s) inside gap(s) wider than max_gap left as NaN" in e
                   for e in out.history)

    def test_history_head_names_the_parameters(self):
        """Parameters go before '; ' so averaging treats equal calls as one
        step and different max_gap values as a real divergence."""
        ts = _gapped(1.0, 3.6)
        out = ts.interp_to_uniform_grid(np.arange(0, 4.9, 0.1), fill_value=np.nan,
                                        max_gap=1.0, inplace=False)
        head = out.history[-1].split("; ")[0]
        assert "fill_value=nan" in head and "max_gap=1.0s" in head

    def test_history_head_is_unchanged_without_the_keywords(self):
        ts = _gapped(1.0, 3.6)
        out = ts.interp_to_uniform_grid(np.arange(0, 4.9, 0.1), inplace=False)
        assert "fill_value" not in out.history[-1]
        assert "max_gap" not in out.history[-1]

    def test_history_silent_when_nothing_blanked(self):
        ts = _gapped(1.0, 1.5)
        out = ts.interp_to_uniform_grid(np.arange(0, 4.9, 0.1), max_gap=1.0, inplace=False)
        assert not any("wider than" in e for e in out.history)

    def test_max_gap_works_without_a_new_grid(self):
        ts = _gapped(1.0, 3.6)
        out = ts.interp_to_uniform_grid(max_gap=1.0, inplace=False)
        vals = np.asarray(out.data, float)
        t = np.asarray(out.times, float)
        assert np.all(np.isnan(vals[(t > 1.0 + 1e-9) & (t < 3.6 - 1e-9)]))

    @pytest.mark.parametrize("bad", [0, -1.0, "1", np.nan, np.inf, True])
    def test_refuses_non_positive_max_gap(self, bad):
        ts = _gapped(1.0, 3.6)
        with pytest.raises(ValidationError, match="max_gap"):
            ts.interp_to_uniform_grid(np.arange(0, 4.9, 0.1), max_gap=bad, inplace=False)


class TestRaggedStackEndToEnd:
    """Ten trials of different lengths, one call each, then average."""

    def test_pad_stack_average_with_min_count(self):
        grid = np.arange(0, 3.0, 0.1)
        trials = [_trial(n).interp_to_uniform_grid(grid, fill_value=np.nan, inplace=False)
                  for n in (10, 15, 20, 25, 30)]
        df = baseDf.from_series(trials, labels=[f"t{i}" for i in range(5)])
        avg = df.average(skipna=True, min_count=2)
        vals = np.asarray(avg.data, float)
        # every trial's data == time, so wherever >= 2 contribute the mean is t
        keep = grid <= 2.4 + 1e-9  # trial n=25 covers 0..2.4, so 2 remain to there
        assert np.allclose(vals[keep], grid[keep])
        assert np.all(np.isnan(vals[~keep]))
        assert any("reduced n" in e for e in avg.history)
        # Same call on every trial, different padded counts: one shared step,
        # not "inputs diverged".
        assert "diverged" not in avg.history[-1]
        assert any(e.startswith("Interpolated to uniform grid") for e in avg.history)

    def test_gap_and_tail_together(self):
        grid = np.arange(0, 4.9, 0.1)
        full = _gapped(1.0, 3.6, end=4.9)
        short = _gapped(1.0, 3.6, end=4.0)
        stacked = [ts.interp_to_uniform_grid(grid, fill_value=np.nan, max_gap=1.0,
                                             inplace=False)
                   for ts in (full, short)]
        df = baseDf.from_series(stacked, labels=["full", "short"])
        avg = df.average(skipna=True, min_count=1)
        vals = np.asarray(avg.data, float)
        in_hole = (grid > 1.0 + 1e-9) & (grid < 3.6 - 1e-9)
        assert np.all(np.isnan(vals[in_hole]))
        assert not np.any(np.isnan(vals[~in_hole]))
