# baseTs Development Guide

## Commands
- Run code directly with: `python baseTs.py`
- Lint: `flake8 *.py`
- Type check: `mypy --ignore-missing-imports *.py`
- Test: `pytest`
- Run single test: `pytest path/to/test.py::test_function -v`

## Code Style Guidelines
- **Formatting**: 4-space indentation, PEP 8 compliant
- **Imports**: Standard libraries first, then third-party, then local modules
- **Types**: Use Python type annotations for all function parameters and return values
- **Naming**:
  - Classes: camelCase (e.g., `baseTs`)
  - Functions/Variables: snake_case (e.g., `lowpass_filter`)
  - Constants: UPPER_CASE
- **Error Handling**: Validate inputs with explicit error messages, use try/except blocks
- **Docstrings**: Triple quotes (""") with parameter descriptions and return values
- **Line Length**: Aim for 80 characters, but flexibility allowed for complex expressions
- **Documentation**: Update docstrings when modifying functions

## Libraries
- Core dependencies: numpy, scipy, pandas, matplotlib
- Time series analysis focused on filtering and outlier detection