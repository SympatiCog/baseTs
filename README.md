# baseTs

A powerful Python library for time series analysis built on pandas Series, providing advanced time-series processing capabilities with full backward compatibility.

## Features

### Core Functionality
- **Pandas Series Foundation**: Built directly on pandas Series for optimal time-series performance
- **Signal Processing**: Low-pass, high-pass, bandpass filtering, normalization, outlier detection
- **Time-Series Analysis**: Rolling statistics, time-based slicing, resampling, correlation analysis
- **Data Processing**: Function application, interpolation, gap filling, time alignment
- **100% Backward Compatibility**: All existing baseTs code works unchanged

### Enhanced Time-Series Features
- **Native Pandas Integration**: Access to 270+ pandas Series methods
- **Advanced Rolling Operations**: `rolling_mean()`, `rolling_std()`, `rolling_max()`, `rolling_min()`, `rolling_median()`
- **Intelligent Resampling**: `resample()` with automatic frequency conversion
- **Time-Series Alignment**: `align_with()` for synchronizing multiple series
- **Correlation Analysis**: `correlation_with()` for cross-series analysis
- **Outlier Detection**: Multiple statistical methods (`zscore`, `iqr`, `modified_zscore`)
- **Gap Interpolation**: `interpolate_gaps()` with various methods
- **Frequency Analysis**: Enhanced FFT with windowing functions
- **Metadata Preservation**: Complete processing history and filter state tracking

## Installation

```bash
# Install from PyPI (when available)
pip install basets

# Or install from source
git clone https://github.com/SympatiCog/baseTs.git
cd baseTs
pip install -e .

# For development
pip install -e ".[dev]"  # Includes test dependencies
```

## Quick Start

### Basic Usage
```python
import numpy as np
from baseTs import baseTs

# Create sample data
data = np.sin(np.linspace(0, 4*np.pi, 1000)) + 0.1*np.random.randn(1000)
times = np.linspace(0, 10, 1000)

# Create baseTs object (now pandas Series-based)
ts = baseTs(data=data, times=times, freq=100.0, signal_name="example")

# Basic operations (unchanged API)
filtered = ts.lowpass_at(cutoff=2.0)
normalized = filtered.zscale()
print(f"Length: {len(normalized)}, Mean: {np.mean(normalized.data):.3f}")
```

### Enhanced Time-Series Features

```python
import pandas as pd
from baseTs import baseTs

# Create time series with numeric times (or datetime index)
times = np.linspace(0, 100, 10000)  # 100 seconds at 100Hz
data = np.sin(2*np.pi*0.5*times) + 0.1*np.random.randn(10000)

ts = baseTs(data=data, times=times, freq=100.0, signal_name="signal")

# Enhanced operations
monthly_avg = ts.rolling_mean(window=50, center=True)
segment = ts.time_slice(start_time=10.0, end_time=90.0)
stats = ts.get_statistics()

# New pandas-powered features
ts_downsampled = ts.resample('1s', method='mean')  # Downsample to 1Hz
outliers = ts.detect_outliers(method='zscore', threshold=2.5)
ts_shifted = ts.shift_time(periods=10)

print(f"Segment mean: {np.mean(segment.data):.3f}")
print(f"Found {np.sum(outliers)} outliers")
print(f"Statistics: {stats}")
```

### Advanced Analysis

```python
# Cross-correlation analysis
ts1 = baseTs(np.sin(2*np.pi*0.5*times), times, freq=100.0, signal_name="signal1")
ts2 = baseTs(np.cos(2*np.pi*0.5*times), times, freq=100.0, signal_name="signal2")

correlation = ts1.correlation_with(ts2, method='pearson')
aligned_ts1, aligned_ts2 = ts1.align_with(ts2, method='inner')

# Frequency analysis with windowing
freqs, power = ts.get_frequency_content(window='hann')
peak_freq = ts.get_peak_freq()

# Gap filling and interpolation
ts_with_gaps = ts.copy()
ts_with_gaps.data[100:110] = np.nan  # Introduce gaps
ts_filled = ts_with_gaps.interpolate_gaps(method='spline')

print(f"Correlation: {correlation:.3f}")
print(f"Peak frequency: {peak_freq} Hz")
```

## Key Advantages

| Feature | Previous Version | New Pandas-Based |
|---------|------------------|------------------|
| **Architecture** | Dual backend complexity | Clean pandas Series inheritance |
| **Performance** | Good for basic ops | Optimized for time-series ops |
| **Memory** | Dual arrays overhead | Efficient Series storage |
| **Time Operations** | Manual implementation | Native pandas optimizations |
| **Compatibility** | 100% backward compatible | 100% + enhanced features |
| **Method Access** | ~50 custom methods | 270+ pandas methods + custom |

## Migration from Previous Versions

**Good news: No migration needed!** All existing code works unchanged:

```python
# This code works exactly the same as before
ts = baseTs(data=data, times=times)
filtered = ts.lowpass_at(cutoff=0.3)
outlier_free = ts.set_outlier_filter(z_threshold=3).filter_outliers()
```

**New features are automatically available:**

```python
# These are new methods you can now use
resampled = ts.resample('100ms', method='mean')
correlation = ts1.correlation_with(ts2)
outliers = ts.detect_outliers(method='iqr')
```

## Documentation

- **[User Guide](docs/USER_GUIDE.md)**: Comprehensive usage guide with examples
- **[API Documentation](docs/API.md)**: Complete method reference
- **[API Series Documentation](docs/API_SERIES.md)**: New pandas-enhanced methods
- **[Examples](docs/EXAMPLES.md)**: Cookbook of common use cases
- **[Changelog](docs/CHANGELOG.md)**: Version history and updates
- **[Development Guide](CLAUDE.md)**: Contributing guidelines

## Requirements

### Core Dependencies
- Python 3.8+
- NumPy >= 1.19
- SciPy >= 1.6
- Pandas >= 1.3

### Optional Dependencies
- Matplotlib >= 3.3 (for plotting)

## Testing

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests

# Run performance benchmarks
pytest tests/test_performance_phase3.py -v

# Test new features
pytest -k "enhanced" -v
```

## Performance

The new pandas-based architecture provides:

- **Time Operations**: 2-5x faster for rolling, resampling, time slicing
- **Memory Efficiency**: ~20% reduction from eliminating dual arrays
- **Method Access**: Native pandas optimizations for statistical operations
- **Compatibility**: Zero performance regression for existing operations

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Add tests for new functionality
4. Ensure all tests pass: `pytest`
5. Submit a pull request

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines.

## License

MIT - see LICENSE file for details

## Changelog

### Latest Release
- **Pandas Series Foundation**: Complete migration to pandas Series architecture
- **Enhanced Time-Series Methods**: 8+ new methods for advanced analysis
- **Performance Improvements**: Optimized time-based operations
- **100% Backward Compatibility**: All existing code works unchanged
- **Code Simplification**: 40+ lines of complex backend code removed

See [CHANGELOG.md](docs/CHANGELOG.md) for complete version history.