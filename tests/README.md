# baseTs Test Suite

This directory contains tests for the baseTs library. The tests are organized as follows:

## Structure

- `conftest.py`: Contains shared pytest fixtures for all tests
- `unit/`: Unit tests for individual components
  - `test_core.py`: Tests for the core baseTs class functionality
  - `test_utils.py`: Tests for utility functions
- `integration/`: Integration tests for full processing pipelines
  - `test_pipeline.py`: Tests for complete processing workflows
- `fixtures/`: Custom test fixtures (data files, etc.)

## Running Tests

You can run the tests using pytest:

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run a specific test file
pytest tests/unit/test_core.py

# Run a specific test function
pytest tests/unit/test_core.py::TestBaseTsInitialization::test_init_with_data_and_times

# Run with verbose output
pytest -v
```

## Test Coverage

To check test coverage, you can use pytest-cov:

```bash
# Install pytest-cov
pip install pytest-cov

# Run tests with coverage report
pytest --cov=baseTs tests/
```

## Writing New Tests

When writing new tests:

1. Use the existing fixtures in `conftest.py` when possible
2. Follow the pattern of other tests in the appropriate directory
3. Keep unit tests focused on testing a single function or method
4. Use integration tests to verify complete workflows work together
5. Make sure tests are deterministic by setting random seeds when needed