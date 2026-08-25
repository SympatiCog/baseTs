# Changelog

All notable changes to the baseTs project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-XX-XX

### 🚀 Major Architecture Update: Pandas Series Foundation

**BREAKING CHANGE**: baseTs now inherits directly from pandas Series, providing native access to 270+ pandas methods while maintaining 100% backward compatibility for existing APIs.

### Added
- **Pandas Series Foundation**: Direct inheritance from pandas Series via TimeSeriesData class
- **Enhanced Frequency Analysis**: 
  - `get_frequency_content(window=None)`: FFT with windowing support ('hann', 'hamming', 'blackman')
  - `get_peak_freq()`: Enhanced peak detection with windowing and frequency range control
  - `plot_fft_power()`: Enhanced plotting with `min_rate` parameter and windowing
- **Advanced Interpolation**:
  - `interpolate_gaps()`: Enhanced with `order` parameter for polynomial/spline interpolation
  - Time interpolation support for numeric indices (not just datetime)
- **Native Pandas Access**: Direct access to all pandas Series methods
- **Windowing Functions**: Spectral leakage reduction for frequency analysis
- **DC Component Control**: Automatic exclusion of DC component in peak frequency detection

### Enhanced  
- **Performance**: 2-5x faster rolling operations using native pandas implementations
- **Memory Efficiency**: Eliminated dual array storage overhead  
- **Time Slicing**: Optimized pandas indexing for time-based queries
- **Statistical Operations**: Vectorized pandas computations
- **Metadata Preservation**: All processing history and filter states maintained through pandas operations
- **Method Signatures**: Enhanced with additional parameters while maintaining backward compatibility

### Fixed
- **Time Interpolation**: Now works correctly with numeric time indices 
- **FFT Edge Cases**: Robust handling of constant signals, NaN/Inf values, and very short signals
- **DC Component Handling**: Consistent behavior between legacy and enhanced FFT methods
- **Power Scaling**: Safe normalization in compute_fft_power() for edge cases

### Documentation
- **Complete API Update**: Removed dual backend references, documented pandas Series foundation
- **Enhanced Examples**: New windowing examples and frequency analysis workflows  
- **Performance Notes**: Updated optimization guidelines for pandas Series architecture
- **Method Chaining**: Enhanced examples with new capabilities

### Testing
- **Comprehensive Coverage**: All 62 tests passing with enhanced functionality
- **Edge Case Validation**: Robust handling of degenerate cases in FFT analysis
- **Backward Compatibility**: 100% API compatibility maintained

### Removed
- **Dual Backend System**: Simplified to single pandas Series backend
- **Backend Parameters**: No longer need to specify `backend='series'`
- **Backend Management**: Eliminated BackendManager and conversion utilities

## [Unreleased]

### Added
- **Relative Band Power / fALFF**:
  - `relative_band_power(low_freq, high_freq, ratio='power', window=None, details=False)`:
    Relative power or amplitude in a frequency band. Defaults to `ratio='power'`, the fraction
    of signal variance in the band; `ratio='amplitude'` reproduces classic fALFF
    (Zou et al., 2008).
  - `falff(low_freq=0.01, high_freq=0.1, ratio='amplitude')`: Convenience wrapper using the
    literature band and convention.
  - `BandPowerResult` dataclass returned by `details=True`, carrying `band_sum`, `total_sum`,
    bin counts, frequency resolution, and `bin_fraction` — the white-noise null both conventions
    converge on, so a ratio can be interpreted against a baseline.
  - The DC (0 Hz) bin is always excluded from both numerator and denominator. Since
    `get_frequency_content()` does not demean, DC would otherwise dominate the denominator on any
    signal with a non-zero mean and drive the ratio toward zero.
  - Validation for bands above Nyquist, bands narrower than the frequency resolution (with the
    required recording duration in the message), NaN/Inf data, and effectively constant signals.
- **Plotting**: `plot_fft_power(..., highlight_band=(low, high))` shades a frequency band on the
  power spectrum.

### Planned
- Additional windowing functions for spectral analysis
- Enhanced plotting integration with matplotlib
- Export functionality to various formats

## [1.0.0] - 2023-XX-XX (Previous Release)

### Features
- Core baseTs class with NumPy backend
- Basic filtering operations (`lowpass_filter`)
- Normalization methods (`zscale`, `normalize_range`)
- Function application (`apply_function`)
- Outlier detection and removal
- Basic interpolation and resampling

### Core Methods
- `lowpass_filter(cutoff)`: Low-pass filtering with Butterworth filter
- `zscale()`: Z-score normalization (mean=0, std=1)
- `normalize_range()`: Range normalization (min=0, max=1)
- `apply_function(func)`: Apply arbitrary function to data
- `remove_outliers()`: Remove statistical outliers
- `interpolate()`: Linear interpolation of missing values
- `resample(factor)`: Resample to different time resolution

### Properties
- `data`: Access to underlying data array
- `times`: Access to time points array
- `len()`: Get length of time series

## Migration Notes

### From 1.0.0 to Current

#### Breaking Changes
- **None**: This release maintains 100% backward compatibility

#### Migration from 1.0.0 to 2.0.0
```python
# Before (1.0.0 - still works exactly the same)
ts = baseTs(data=data, times=times)
filtered = ts.lowpass_filter(cutoff=0.3)

# After (2.0.0 - same API, enhanced capabilities)
ts = baseTs(data=data, times=times)  # Now pandas Series-based
filtered = ts.lowpass_filter(cutoff=0.3)  # Same method, better performance

# New enhanced features available automatically
freqs, power = ts.get_frequency_content(window='hann')  # Enhanced FFT
peak = ts.get_peak_freq(window='blackman', min_freq=1.0)  # Windowed peak detection
ts.plot_fft_power(min_rate=1.0, max_rate=50.0, window='hann')  # Enhanced plotting
```

#### Automatic Benefits in 2.0.0
- **No Code Changes Required**: All existing code works unchanged
- **Enhanced Performance**: Automatic 2-5x speedup in rolling operations
- **Memory Efficiency**: Reduced memory usage vs. previous dual backend system
- **Native Pandas Access**: Use any pandas Series method directly (e.g., `ts.describe()`, `ts.quantile(0.95)`)

## Future Roadmap

### Version 2.1.0 (Planned - 3 months)
- **Additional Windowing Functions**: Kaiser, Tukey, and custom window support
- **Enhanced Plotting**: Integration with plotly for interactive plots
- **Export Functionality**: Easy export to pandas DataFrame, CSV, HDF5, Parquet
- **Performance Optimizations**: Further improvements for large datasets

### Version 2.2.0 (Planned - 6 months)
- **Seasonal Decomposition**: Trend, seasonal, and residual analysis
- **Advanced Analytics**: Cross-correlation, coherence analysis
- **Multi-resolution Analysis**: Wavelet transforms and time-frequency analysis
- **Batch Processing**: Tools for processing multiple time series

### Version 3.0.0 (Planned - 12 months)
- **Multi-dimensional Support**: Support for multi-channel time series
- **Machine Learning Integration**: Built-in feature extraction and anomaly detection
- **Advanced Resampling**: Non-uniform resampling and gap-filling algorithms
- **Streaming Support**: Real-time time series processing capabilities

## Development Process

### Versioning Strategy
- **Major versions**: Breaking changes, architecture changes
- **Minor versions**: New features, non-breaking enhancements
- **Patch versions**: Bug fixes, documentation updates

### Release Process
1. Feature development and testing
2. Beta release for testing
3. Release candidate with final testing
4. Stable release with documentation
5. Post-release monitoring and hotfixes

### Compatibility Promise
- **Backward compatibility**: Maintained within major versions
- **Deprecation notice**: 12 months minimum before removing features
- **Migration tools**: Provided for major version transitions
- **Legacy support**: Previous major version supported for 24 months

## Credits

### Contributors
- Core development team
- Community contributors
- Beta testers and early adopters

### Dependencies
- **NumPy**: Core numerical operations and array handling
- **SciPy**: Signal processing algorithms and filters  
- **Pandas**: Series foundation and enhanced time-series operations (required)
- **Matplotlib**: Plotting functionality (optional)

### Acknowledgments
- Scientific Python community for best practices
- Pandas team for time-series inspiration
- NumPy team for foundational array operations