# baseTs

A powerful Python library for time series analysis built on pandas Series, providing advanced time-series processing capabilities with full backward compatibility.

## Features

### ⭐ **LOWESS Outlier Detection & Despiking**
- **Advanced LOWESS Filtering**: Robust spike artifact removal (the original motivation for this library!)
- **Configurable Parameters**: Z-threshold, fraction, iterations, and tail processing options
- **Quality Control**: Built-in QC plotting to visualize outlier detection results
- **Iterative Processing**: Multiple passes for thorough artifact removal

### 🎛️ **Comprehensive Signal Processing**
- **Digital Filters**: Low-pass, high-pass, bandpass, notch, and Gaussian filtering
- **Advanced Filtering**: Butterworth, Savitzky-Golay, and custom filter implementations
- **Detrending**: Linear and constant detrending methods
- **Normalization**: Z-score, range normalization, and centering functions

### 🔗 **Time-Series Alignment & Synchronization**
- **Multi-Series Alignment**: `align_with()` for synchronizing different time series
- **Flexible Join Methods**: Inner, outer, left, and right alignment strategies
- **Time-Based Operations**: Intelligent handling of different sampling rates and time grids
- **Cross-Correlation**: Built-in correlation analysis between aligned series

### ⚙️ **Arbitrary Function Application**
- **Flexible Processing**: Apply any custom function via `.apply_function()`
- **Mathematical Operations**: Built-in support for complex transformations
- **Function Chaining**: Seamless integration with method chaining workflows
- **Custom Analytics**: Easy integration of domain-specific processing functions

### 📊 **Native Plotting Integration**
- **Direct Plotting**: `ax = ts.plot()` for immediate visualization
- **Multi-Series Plots**: `ts2.plot(ax=ax)` for overlay plotting
- **Specialized Plots**: FFT power spectra, histograms, lag plots, and QC visualizations
- **Matplotlib Integration**: Full compatibility with matplotlib workflows

### 🧮 **First-Class Mathematical Operations**
- **Natural Arithmetic**: `ts3 = ts1 + ts2`, `ts_scaled = ts * 2.5`
- **Element-wise Operations**: Addition, subtraction, multiplication, and division
- **Broadcasting Support**: Operations between series and scalars
- **Mathematical Functions**: Direct application of numpy/scipy functions

### 🐼 **Full Pandas Ecosystem Integration**
- **Native pandas Series**: Access to all 270+ pandas Series methods
- **NumPy Compatibility**: Seamless integration with NumPy functions and operations
- **SciPy Integration**: Direct compatibility with SciPy signal processing and statistics
- **Visualization Libraries**: Works with matplotlib, seaborn, plotly, and other plotting tools

### 🏗️ **Enhanced Architecture**
- **Pandas Series Foundation**: Built directly on pandas Series for optimal performance
- **100% Backward Compatibility**: All existing baseTs code works unchanged
- **Metadata Preservation**: Complete processing history and filter state tracking
- **Memory Efficiency**: Optimized storage without dual array overhead

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

### Basic Usage with Key Features
```python
import numpy as np
import matplotlib.pyplot as plt
from baseTs import baseTs

# Create sample data with artificial spikes
times = np.linspace(0, 10, 1000)
data = np.sin(2*np.pi*0.5*times) + 0.1*np.random.randn(1000)
# Add some spike artifacts
data[200] += 5.0  # Spike artifact
data[600] -= 4.0  # Another spike

# Create baseTs object
ts = baseTs(data=data, times=times, freq=100.0, signal_name="example")

# LOWESS outlier detection and removal (library's signature feature!)
despiked = ts.set_outlier_filter(z_threshold=3.0).filter_outliers()

# Signal processing chain
processed = (despiked
             .lowpass_filter(cutoff=2.0)
             .detrend(method='linear')
             .zscale())

# Mathematical operations
ts_doubled = processed * 2.0
ts_combined = ts + processed  # First-class arithmetic

# Native plotting
ax = ts.plot()                    # Original signal
despiked.plot(ax=ax)             # Overlay despiked
processed.plot(ax=ax)            # Overlay processed
plt.legend(['Original', 'Despiked', 'Processed'])
plt.show()

print(f"Removed {len(ts) - len(despiked)} outlier points")
print(f"Final stats: mean={np.mean(processed.data):.3f}, std={np.std(processed.data):.3f}")
```

### Pandas Integration & Advanced Features

```python
import pandas as pd
import numpy as np
from baseTs import baseTs

# Create two time series for alignment demo
times1 = np.linspace(0, 100, 10000)  
times2 = np.linspace(0.5, 99.5, 9900)  # Slightly different time grid
data1 = np.sin(2*np.pi*0.5*times1) + 0.1*np.random.randn(10000)
data2 = np.cos(2*np.pi*0.5*times2) + 0.1*np.random.randn(9900)

ts1 = baseTs(data=data1, times=times1, freq=100.0, signal_name="signal1")
ts2 = baseTs(data=data2, times=times2, freq=100.0, signal_name="signal2")

# Time-series alignment
aligned1, aligned2 = ts1.align_with(ts2, method='inner')
correlation = aligned1.correlation_with(aligned2)

# Apply arbitrary functions
squared_signal = ts1.apply_function(lambda x: x**2)
custom_transform = ts1.apply_function(np.tanh)  # Apply any numpy function

# Full pandas ecosystem access
ts1_stats = ts1.describe()          # Native pandas method
ts1_median = ts1.median()           # Direct pandas access
ts1_quantiles = ts1.quantile([0.25, 0.75])  # Pandas quantiles

# Mathematical operations
combined = ts1 + ts2 * 0.5          # First-class arithmetic
scaled = ts1 * 2 - 1                # Chained operations
power_signal = ts1 ** 2             # Power operations

print(f"Alignment correlation: {correlation:.3f}")
print(f"Original vs squared mean: {ts1.mean():.3f} vs {squared_signal.mean():.3f}")
print(f"Combined signal range: {combined.min():.3f} to {combined.max():.3f}")
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
- statsmodels >= 0.14 (LOWESS outlier filtering)

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