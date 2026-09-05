"""Every fenced Python block in docs/ runs (#69).

The document is the source of truth: each ```python block in a doc file
is executed, in order, in one namespace shared across that file (so a
later block sees the names an earlier one binds, as a reader working
top-down would). A block that is a signature or declaration fragment
rather than a runnable example carries the fence info string
```python no-run``` and is compiled but not executed; its stubs are then
checked against the class (a `def` must name a method with those
parameters, a `@property` a property, an annotated name an instance
attribute), since a stub that only has to compile can rot without limit
(review). The number of such blocks per file is pinned below, so marking
a block no-run is a visible change, not a way to hide rot.

A block runs with warnings as errors: a block that runs but warns is
documenting something that is about to break or already returns NaN.
Fences are pinned to one spelling - an unindented ```python - and any
other Python-ish fence (```py, ```python3, ~~~python, indented) fails the
census rather than slipping past the regex (review).

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

import ast
import contextlib
import inspect
import io
import re
import warnings
from pathlib import Path

import numpy as np
import pytest

from baseTs import baseTs

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
# Any opening or closing fence, however spelled or indented.
ANY_FENCE = re.compile(r"^([ \t]*)(`{3,}|~{3,})[ \t]*(\S*)", re.M)
PYTHONISH = {"py", "python", "python3", "ipython", "pycon", "py3"}
# The one warning the test backend itself causes: plt.show() under Agg.
BACKEND_NOISE = "FigureCanvasAgg is non-interactive"


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
                warnings.simplefilter("error")
                warnings.filterwarnings("ignore", message=BACKEND_NOISE)
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


def python_fences(file):
    """Every opening fence whose info word names Python, however spelled."""
    text = (DOCS / file).read_text()
    openings, open_fence = [], None
    for m in ANY_FENCE.finditer(text):
        indent, fence, info = m.groups()
        if open_fence is None:
            open_fence = fence
            if info.split(":")[0].lower() in PYTHONISH:
                openings.append((text[:m.start()].count("\n") + 1, indent, fence, info))
        elif fence[0] == open_fence[0] and len(fence) >= len(open_fence):
            # CommonMark: a closing fence is the same character, at least as
            # long. A ```python line inside an open ```` block is content,
            # not an opening (review).
            open_fence = None
    return openings


@pytest.mark.parametrize("file", FILES)
def test_every_python_fence_is_spelled_the_one_way_the_census_reads(file):
    """A ```py, ```python3, ~~~python or indented fence would be invisible
    to FENCE and so to every test above; it fails here instead."""
    for line, indent, fence, info in python_fences(file):
        assert (indent, fence, info) == ("", "```", "python"), (
            f"docs/{file}:{line}: write the fence as ```python at column 0 "
            f"(got {indent!r} + {fence + info!r})")
    assert len(python_fences(file)) == len(BLOCKS[file])


def _stubs(block):
    """The top-level definitions a no-run block declares."""
    return [node for node in ast.parse(block.code).body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AnnAssign))]


NOT_A_LITERAL = object()


def _literal_default(node):
    """A default's value when it is a literal (np.nan counts); else
    NOT_A_LITERAL. A real `None` default is a value to compare, not a
    "could not tell" (review: `hp_hz=None` against a real 0.01 passed)."""
    try:
        return ast.literal_eval(node)
    except ValueError:
        return np.nan if ast.unparse(node) == "np.nan" else NOT_A_LITERAL


NO_RUN = [b for b in ALL if b.no_run]


@pytest.mark.parametrize("block", NO_RUN, ids=[b.id for b in NO_RUN])
def test_a_no_run_stub_describes_the_class(block):
    """Compiled-only stubs rotted without limit (review found `copy(self)`
    against `copy(self, deep=True)`, a `plot` stub for what is a property,
    `@property` stubs for what are instance attributes, and a legacy
    block whose four signatures were all stale). A `def` must name a
    method whose parameters match in name and order, and whose literal
    defaults match; a `@property` must be a property; an annotated name
    must be an instance attribute and not a property; a class stub's
    bases must be the real bases."""
    instance = baseTs(np.zeros(4), np.arange(4) / 4.0, freq=4.0)
    for node in _stubs(block):
        if isinstance(node, ast.ClassDef):
            assert node.name == baseTs.__name__
            assert [ast.unparse(b) for b in node.bases] == [b.__name__ for b in baseTs.__bases__]
            continue
        name = node.target.id if isinstance(node, ast.AnnAssign) else node.name
        attr = getattr(baseTs, name, None)
        if isinstance(node, ast.AnnAssign):
            assert hasattr(instance, name), f"{block.id}: no attribute {name}"
            assert not isinstance(attr, property), f"{block.id}: {name} is a property"
            continue
        decorators = {ast.unparse(d) for d in node.decorator_list}
        if "property" in decorators:
            assert isinstance(attr, property), f"{block.id}: {name} is not a property"
            continue
        assert callable(attr), f"{block.id}: {name} is not a method"
        real = inspect.signature(attr)
        stub = [a.arg for a in node.args.args] + (
            ["*" + node.args.vararg.arg] if node.args.vararg else []) + [
            a.arg for a in node.args.kwonlyargs] + (
            ["**" + node.args.kwarg.arg] if node.args.kwarg else [])
        want = []
        for p in real.parameters.values():
            prefix = {p.VAR_POSITIONAL: "*", p.VAR_KEYWORD: "**"}.get(p.kind, "")
            want.append(prefix + p.name)
        assert stub == want, f"{block.id}: {name}{stub} vs real {name}{want}"
        positional = [a.arg for a in node.args.args]
        with_default = positional[-len(node.args.defaults):] if node.args.defaults else []
        defaults = dict(zip(with_default, node.args.defaults))
        # Keyword-only defaults live in kw_defaults, None where absent (review).
        defaults.update({a.arg: d for a, d in zip(node.args.kwonlyargs, node.args.kw_defaults)
                         if d is not None})
        for pname, dnode in defaults.items():
            got = _literal_default(dnode)
            if got is NOT_A_LITERAL:
                continue
            real_default = real.parameters[pname].default
            same = (got is real_default) or (got == real_default) or (
                isinstance(got, float) and isinstance(real_default, float)
                and np.isnan(got) and np.isnan(real_default))
            assert same, (
                f"{block.id}: {name}({pname}={ast.unparse(dnode)}) vs real {real_default!r}")


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
