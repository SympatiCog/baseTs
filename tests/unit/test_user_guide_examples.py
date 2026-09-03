"""Executable pins on the worked examples in docs/USER_GUIDE.md.

The example is read from the document and executed, so the document is the
source of truth: a copy pasted into a test would pin the copy, and the two
would drift the way the spectral guards did before #28. Issue #44 is the
motivating case - Example 4 had been unrunnable for two independent reasons,
and nothing executed it.
"""

import io
import re
import contextlib
from pathlib import Path

import numpy as np
import pytest

from baseTs import baseTs

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")

USER_GUIDE = Path(__file__).resolve().parents[2] / "docs" / "USER_GUIDE.md"


def fenced_python_under(heading: str) -> str:
    """The first ```python block after the given markdown heading line."""
    text = USER_GUIDE.read_text()
    start = text.index(heading)
    match = re.search(r"```python\n(.*?)```", text[start:], re.S)
    assert match, f"no python block under {heading!r}"
    return match.group(1)


def run_example(code: str) -> dict:
    """Execute a doc block and return its namespace.

    The guide's opening block does `import numpy as np` and
    `from baseTs import baseTs`; every later example assumes both, so they
    are seeded here rather than re-imported in each block.
    """
    namespace = {"np": np, "baseTs": baseTs}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(code, str(USER_GUIDE), "exec"), namespace)
    return namespace


def test_example_4_runs_to_completion():
    """Issue #44: a self-referential dict literal and a cutoff at Nyquist.

    The Nyquist failure fires first - bandpass_at(hp_hz=0.1, lp_hz=50.0) at
    the example's own sampling_rate=100 - and masked the NameError in the
    spectral_features literal a few lines below it. Both have to be fixed for
    this to pass.
    """
    ns = run_example(fenced_python_under("### Example 4: Scientific Data Analysis"))

    report = ns["scientific_analysis"]
    spectral = report["features"]["spectral"]
    assert set(spectral) == {"peak_frequency", "spectral_centroid", "spectral_bandwidth"}
    assert np.isfinite(spectral["spectral_bandwidth"])
    assert set(report["condition_analysis"]) == {"baseline", "stimulus", "recovery"}


def test_example_4_enhanced_cleaning_branch_completes():
    """The `quality_score < 0.95` branch, which the example's own data never takes.

    Over 40 seeds the usage block's sine-plus-noise scores exactly 1.0 under
    IQR at threshold 2.0, so the branch #28 patched - filter_outliers leaves
    gaps as NaN, and the spectral step rejects NaN - is dead in the document
    as written. Driving the function with spiky, gappy data is what pins the
    interpolate_gaps() call #28 added: with the call removed, the spectral
    step rejects the NaN that filter_outliers preserves.
    """
    ns = run_example(fenced_python_under("### Example 4: Scientific Data Analysis"))
    analyse = ns["scientific_time_series_analysis"]

    rng = np.random.default_rng(1)
    n = 12000
    data = np.sin(2 * np.pi * 0.5 * np.linspace(0, 120, n)) + 0.1 * rng.standard_normal(n)
    spikes = rng.choice(n, size=n // 10, replace=False)
    data[spikes] += rng.choice([-1.0, 1.0], size=spikes.size) * 8
    # Acquisition dropouts. filter_outliers leaves these as NaN (#36), which
    # is what makes the interpolate_gaps() step load-bearing: without input
    # gaps the filter's own blanks are re-interpolated and nothing is left
    # for the spectral guard to reject.
    data[rng.choice(n, size=50, replace=False)] = np.nan
    metadata = {
        "sampling_rate": 100,
        "experiment_name": "spiky",
        "conditions": {"time_windows": {"first": (0, 60), "second": (60, 120)}},
    }

    with contextlib.redirect_stdout(io.StringIO()):
        report = analyse(data, metadata)

    assert report["data_quality"]["quality_score"] < 0.95
    assert any("Interpolated gaps" in step for step in report["processing_history"])
    assert np.isfinite(report["features"]["spectral"]["spectral_bandwidth"])
