# baseTs

A Python library for time series analysis with dual backend architecture, supporting both NumPy arrays and Pandas Series for enhanced time-series capabilities.

## Features

### Core Functionality
- **Dual Backend Architecture**: Choose between NumPy (performance) or Pandas Series (time-series features)
- **Signal Processing**: Low-pass filtering, normalization, outlier detection
- **Time-Series Analysis**: Rolling statistics, time-based slicing, datetime indexing
- **Data Processing**: Function application, interpolation, resampling
- **100% Backward Compatibility**: Existing code works unchanged

### New in Latest Version
- **Pandas Series Backend**: Enhanced time-series operations with native datetime support
- **Rolling Operations**: `rolling_mean()`, `rolling_std()`, `rolling_max()`, `rolling_min()`, `rolling_median()`
- **Time-Based Slicing**: Extract data by date ranges with `time_slice()`
- **Rich Statistics**: Comprehensive analysis with `get_statistics()`
- **Metadata Preservation**: Processing history and filter state tracking
- **Performance Benchmarking**: Built-in tools for backend comparison

## Installation

```bash
# Install from PyPI (when available)
pip install basets

# For full Series backend functionality
pip install basets[series]  # Includes pandas

# Or install from source
git clone https://github.com/SympatiCog/baseTs.git
cd baseTs
pip install -e .

# For development
pip install -e ".[dev]"  # Includes test dependencies
```

## Quick Start

### Basic Usage (NumPy Backend)
```python
import numpy as np
from baseTs import baseTs

# Create sample data
data = np.sin(np.linspace(0, 4*np.pi, 1000)) + 0.1*np.random.randn(1000)
times = np.linspace(0, 10, 1000)

# Create baseTs object (NumPy backend - default)
ts = baseTs(data=data, times=times)

# Basic operations
filtered = ts.lowpass_filter(cutoff=0.3)
normalized = filtered.zscale()
print(f"Length: {normalized.len()}, Mean: {np.mean(normalized.data):.3f}")
```

### Enhanced Time-Series Features (Series Backend)

```python
import pandas as pd
from baseTs import baseTs

# Create time series with datetime index
dates = pd.date_range('2023-01-01', periods=365, freq='D')
data = np.random.randn(365)

# Use Series backend for enhanced features
ts = baseTs(data=data, times=dates, backend='series')

# Enhanced operations
monthly_avg = ts.rolling_mean(window=30)
january = ts.time_slice(start='2023-01-01', end='2023-01-31')
stats = ts.get_statistics()

print(f"January mean: {np.mean(january.data):.3f}")
print(f"Annual statistics: {stats}")
```

## Backend Comparison

| Feature | NumPy Backend | Series Backend |
|---------|---------------|----------------|
| **Performance** | Fastest for numerical ops | Competitive (1-5x overhead) |
| **Memory** | Minimal | ~20% more (metadata) |
| **Time Indexing** | Numeric only | Native datetime support |
| **Rolling Ops** | Manual | Optimized built-ins |
| **Compatibility** | All existing code | All existing code + new features |

## Migration Guide

Existing code works unchanged:
```python
# This still works exactly the same
ts = baseTs(data=data, times=times)
filtered = ts.lowpass_filter(cutoff=0.3)
```

Opt-in to new features:
```python
# Explicitly choose Series backend for new features
ts = baseTs(data=data, times=times, backend='series')
```

See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for detailed migration instructions.

## Documentation

- **[User Guide](docs/USER_GUIDE.md)**: Comprehensive usage guide with examples
- **[Migration Guide](MIGRATION_GUIDE.md)**: Detailed migration instructions
- **[API Documentation](docs/API.md)**: Complete method reference
- **[Changelog](docs/CHANGELOG.md)**: Version history and updates
- **[Development Guide](CLAUDE.md)**: Contributing guidelines

## Requirements

### Core Dependencies
- Python 3.8+
- NumPy >= 1.19
- SciPy >= 1.6

### Optional Dependencies
- Pandas >= 1.3 (for Series backend)
- Matplotlib >= 3.3 (for plotting)

## Testing

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/test_migration.py
pytest tests/test_integration_workflows.py

# Run performance benchmarks
python tests/test_performance_phase3.py

# Run migration validation
python tests/test_migration_validation.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines.

## License

MIT - see LICENSE file for details
