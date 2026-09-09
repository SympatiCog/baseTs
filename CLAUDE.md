# baseTs Development Guide

## Commands
- Run code directly with: `python baseTs.py`
- Lint: `flake8 *.py`
- Type check: `mypy *.py` (configured in pyproject.toml with Python 3.9 target)
- Test: `pytest` (configured to look in tests directory)
- Run single test: `pytest path/to/test.py::test_function -v`

## Architecture Overview

### Pandas Series Foundation
baseTs is now built directly on pandas Series, providing:
- **TimeSeriesData**: Custom pandas Series subclass with metadata
- **Direct Inheritance**: baseTs inherits from TimeSeriesData
- **Native Pandas Integration**: Access to 270+ pandas methods
- **Backward Compatibility**: All legacy numpy array operations preserved

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

### Adding New Methods
1. **Design**: Consider if pandas has a native method first
2. **Implementation**: Add to `baseTs/core.py` with proper metadata handling
3. **Testing**: Add unit tests in `tests/unit/test_core.py`
4. **Documentation**: Update docstrings and API docs

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