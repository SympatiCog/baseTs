"""Every fenced Python block in docs/ runs (#69).

The document is the source of truth: each ```python block in a doc file
is executed, in order, in one namespace shared across that file (so a
later block sees the names an earlier one binds, as a reader working
top-down would). A block that is a signature or declaration fragment
rather than a runnable example carries the fence info string
```python no-run``` and is compiled but not executed. The number of such
blocks per file is pinned below, so marking a block no-run is a visible
change, not a way to hide rot.

docs/CHANGELOG.md is excluded on purpose: its snippets illustrate what a
change did, often in the API as it was, and are not documentation of the
current API.

Issue #44 was the motivating case: USER_GUIDE.md's Example 4 had been
unrunnable for two independent reasons and nothing executed it. Measured
before this harness existed, 44 of 108 blocks failed (#69); most of
API.md's were one cascade - bare `@property def data(self)` signature
fragments bound `data`, `times` and `freq` to property objects in the
shared namespace, and every later example built from them broke.
"""

import contextlib
import io
import re
import warnings
from pathlib import Path

import numpy as np
import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

DOCS = Path(__file__).resolve().parents[2] / "docs"
FILES = ["USER_GUIDE.md", "EXAMPLES.md", "API.md", "API_SERIES.md"]

# Fragments the harness compiles but does not run, per file.
EXPECTED_NO_RUN = {
    "USER_GUIDE.md": 0,
    "EXAMPLES.md": 0,
    "API.md": 12,
    "API_SERIES.md": 0,
}

FENCE = re.compile(r"^```python([^\n]*)\n(.*?)^```", re.S | re.M)


class Block:
    def __init__(self, file, line, info, code):
        self.file, self.line, self.info, self.code = file, line, info, code

    @property
    def id(self):
        return f"{self.file}:{self.line}"

    @property
    def no_run(self):
        return self.info == "no-run"


def blocks_in(file):
    text = (DOCS / file).read_text()
    return [Block(file, text[:m.start()].count("\n") + 1, m.group(1).strip(), m.group(2))
            for m in FENCE.finditer(text)]


BLOCKS = {file: blocks_in(file) for file in FILES}
ALL = [b for file in FILES for b in BLOCKS[file]]

_outcomes = {}


def outcome(block):
    """The exception a block raised when its file was executed, or None.

    A file is executed once, every runnable block in order, and the
    per-block result cached, so each block gets its own test id without
    the file being re-run per block.
    """
    if block.file not in _outcomes:
        _outcomes[block.file] = _execute(block.file)
    return _outcomes[block.file][block.line]


def _execute(file):
    namespace = {}
    results = {}
    for block in BLOCKS[file]:
        if block.no_run:
            results[block.line] = None
            continue
        np.random.seed(0)
        try:
            with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():
                warnings.simplefilter("ignore")
                exec(compile(block.code, f"docs/{block.id}", "exec"), namespace)
            results[block.line] = None
        except Exception as exc:  # noqa: BLE001 - the point is to report it
            results[block.line] = exc
        finally:
            plt.close("all")
    return results


@pytest.mark.parametrize("block", ALL, ids=[b.id for b in ALL])
def test_every_fenced_python_block_runs(block):
    if block.no_run:
        compile(block.code, f"docs/{block.id}", "exec")
        return
    exc = outcome(block)
    if exc is not None:
        raise AssertionError(
            f"docs/{block.id} raised {type(exc).__name__}: {exc}"
        ) from exc


@pytest.mark.parametrize("file", FILES)
def test_the_no_run_count_is_the_pinned_one(file):
    """Marking a block no-run must show up here, not slip past."""
    assert sum(b.no_run for b in BLOCKS[file]) == EXPECTED_NO_RUN[file]


@pytest.mark.parametrize("block", ALL, ids=[b.id for b in ALL])
def test_the_fence_info_string_is_known(block):
    """`python` or `python no-run`; a typo would silently un-mark a block."""
    assert block.info in ("", "no-run"), block.info


def test_the_census_is_the_whole_docs_directory():
    """A new doc file has to be listed (or excluded here with a reason)."""
    present = sorted(p.name for p in DOCS.glob("*.md"))
    assert present == sorted(FILES + ["CHANGELOG.md"])
