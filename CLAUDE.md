# baseTs Development Guide

## Commands
- Run code directly with: `python baseTs.py`
- Lint: `flake8 *.py`
- Type check: `mypy *.py` (configured in pyproject.toml with Python 3.11 target)
- Test: `pytest` (configured to look in tests directory)
- Run single test: `pytest path/to/test.py::test_function -v`

## Architecture Overview

### Pandas Series Foundation
baseTs is now built directly on pandas Series, providing:
- **TimeSeriesData**: Custom pandas Series subclass with metadata
- **Direct Inheritance**: baseTs inherits from TimeSeriesData
- **Native Pandas Integration**: Access to 270+ pandas methods
- **Backward Compatibility**: All legacy numpy array operations preserved

### Multi-Channel Container (`baseDf`)
`baseDf` (`baseTs/frame.py`, `baseTs/frame_meta.py`, `baseTs/frame_average.py`)
holds many `baseTs` series — channels, ROIs, electrodes — as columns of one
table sharing a single index:
- **DataFrame-backed, not DataFrame-subclassed**: deliberately, to avoid the
  block-manager/`_constructor_sliced`/`__finalize__` surface a `pd.DataFrame`
  subclass would expose. See `docs/superpowers/specs/2026-09-13-basedf-multichannel-design.md` ("Decision 1").
- **Three pieces of state**: a plain `pd.DataFrame` of values, a `pd.DataFrame`
  of per-column metadata (`_col_meta`), and four scalars describing the
  shared index (`_index_meta`)
- **Explicit forwarding, not inheritance**: broadcasts `baseTs` transforms
  and measurements across columns deliberately; `.df` is the escape hatch for
  a pandas method that isn't forwarded
- **Full reference**: `docs/API_FRAME.md`

### Key Design Principles
1. **Series-First**: All operations leverage pandas Series capabilities
2. **Metadata Preservation**: Processing history and filter states maintained
3. **API Stability**: Existing method signatures unchanged
4. **Performance**: Optimized for time-series operations

## Code Style Guidelines
- **Formatting**: 4-space indentation, PEP 8 compliant, use Black formatter and isort for imports
- **Imports**: Standard libraries first, then third-party, then local modules
- **Types**: Use Python type annotations for all function parameters and return values
- **Naming**:
  - Classes: camelCase (e.g., `baseTs`, `TimeSeriesData`)
  - Functions/Variables: snake_case (e.g., `lowpass_filter`, `rolling_mean`)
  - Constants: UPPER_CASE
- **Error Handling**: Validate inputs with explicit error messages, use try/except blocks
- **Docstrings**: Triple quotes (""") with parameter descriptions and return values
- **Line Length**: Aim for 100 characters as specified in pyproject.toml
- **Documentation**: Update docstrings when modifying functions

## Libraries
- **Core dependencies**: numpy, scipy, pandas, matplotlib
- **Time series focus**: Filtering, outlier detection, resampling, correlation analysis
- **Pandas integration**: Rolling operations, time-based indexing, gap interpolation

## Development Workflow

### Adding New Methods (`baseTs`)
1. **Design**: Consider if pandas has a native method first
2. **Implementation**: Add to `baseTs/core.py` with proper metadata handling
3. **Testing**: Add unit tests in `tests/unit/test_core.py`
4. **Documentation**: Update docstrings and `docs/API.md` (or
   `docs/API_SERIES.md` for the pandas-era methods documented there), plus
   `README.md` and `docs/USER_GUIDE.md` if the change adds a user-facing
   capability rather than a corner case; `docs/API.md` carries a no-run
   stub test that fails when a documented signature drifts

### Adding New Methods (`baseDf`)
1. **Design**: Most new behavior should be a broadcast or reduction over
   existing `baseTs` methods rather than a new primitive — check
   `_broadcast`/`measure`/`average` in `baseTs/frame.py` first
2. **Implementation**: Add to `baseTs/frame.py` (or `frame_meta.py`/
   `frame_average.py` for metadata/averaging-specific logic); validate inputs
   explicitly rather than letting a bare pandas error leak through
3. **Testing**: Add unit tests in `tests/unit/test_frame_*.py`; a new public
   method needs both a happy-path test and a refusal test for its invalid
   inputs
4. **Documentation**: Update `docs/API_FRAME.md` and, if the change adds a
   new on-ramp rather than a new corner case, `docs/EXAMPLES.md`

### Method Patterns
```python
def new_method(self, param: type, inplace: bool = False) -> "baseTs":
    """
    Brief description.
    
    Args:
        param: Parameter description
        inplace: If True, modifies existing object. Otherwise returns new object.
        
    Returns:
        Processed baseTs object
    """
    # Use pandas operations when possible
    result = self.some_pandas_operation(param)
    
    if inplace:
        self.data = result.values
        self.times = result.index.values
        self._update_history_and_process("Applied new_method", "_new_method")
        return self
    else:
        new_obj = self._create_new_with_data(result.values, result.index.values)
        new_obj._update_history_and_process("Applied new_method", "_new_method")
        return new_obj
```

### History Messages
A history entry is `"<operation and parameters>; <what happened to this
series>"`. `baseDf.average()` compares contributors' histories step by
step on the part before the first `"; "` (`frame_average.operation_head`),
so:
- Put every parameter in the head (`"Lowpass filtered at 2.0 Hz"`,
  `"Interpolated to uniform grid of n=400 @ 50.0Hz, fill_value=nan"`).
  Two columns filtered at different cutoffs must diverge.
- Put per-series outcomes after the separator (`"; 150 grid point(s)
  outside the data padded with nan"`, `"; left 3 pre-existing gap
  sample(s) as NaN"`). Ten trials padded by different amounts must *not*
  diverge; the prefix keeps the head plus `"; per-input details differ"`.
- Round derived numbers in the head (a rate carries float noise).
Getting this wrong does not fail a test on the method itself; it makes an
average over its outputs report a spurious "inputs diverged".

### Index Rules
Anything that reasons about the spacing of the index goes through
`baseTs._gap_positions`, which enforces the three rules gaps need: every
timestamp finite, non-decreasing, and a median interval above zero. Do not
grow a private check. Filters raise only `InvalidParameterError` (the
`filters` module's type) and check the rate before scanning the index, so a
degenerate time base still reports "Invalid sampling frequency"; a filter
that mixes neighbouring samples should call `_check_index_gaps` before it
runs, with `needs_rate=False` if it is not designed at `freq`.

### Testing Guidelines
- **Unit Tests**: Test individual methods in isolation
- **Integration Tests**: Test method chaining and workflows
- **Backward Compatibility**: Ensure all legacy operations work
- **Performance Tests**: Benchmark time-series operations

### Enhanced Features Testing
```python
def test_enhanced_feature():
    # Test new pandas-powered functionality
    ts = baseTs(data, times, freq=100.0)
    
    # Test new method
    result = ts.new_enhanced_method()
    
    # Verify pandas integration works
    assert isinstance(result, baseTs)
    assert hasattr(result, 'freq')
    assert len(result.history) > 0
```