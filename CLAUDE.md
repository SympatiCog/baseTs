# baseTs Development Guide

## Commands
- Run code directly with: `python baseTs.py`
- Lint: `flake8 *.py`
- Type check: `mypy *.py` (configured in pyproject.toml with Python 3.8 target)
- Test: `pytest` (configured to look in tests directory)
- Run single test: `pytest path/to/test.py::test_function -v`

## Code Style Guidelines
- **Formatting**: 4-space indentation, PEP 8 compliant, use Black formatter and isort for imports
- **Imports**: Standard libraries first, then third-party, then local modules
- **Types**: Use Python type annotations for all function parameters and return values
- **Naming**:
  - Classes: camelCase (e.g., `baseTs`)
  - Functions/Variables: snake_case (e.g., `lowpass_filter`)
  - Constants: UPPER_CASE
- **Error Handling**: Validate inputs with explicit error messages, use try/except blocks
- **Docstrings**: Triple quotes (""") with parameter descriptions and return values
- **Line Length**: Aim for 100 characters as specified in pyproject.toml
- **Documentation**: Update docstrings when modifying functions

## Libraries
- Core dependencies: numpy, scipy, pandas, matplotlib
- Time series analysis focused on filtering and outlier detection