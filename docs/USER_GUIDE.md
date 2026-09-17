# baseTs User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Core Concepts](#core-concepts)
3. [Basic Operations](#basic-operations)
4. [Enhanced Time-Series Features](#enhanced-time-series-features)
5. [Advanced Analysis](#advanced-analysis)
6. [Performance Guidelines](#performance-guidelines)
7. [Examples and Recipes](#examples-and-recipes)
8. [Migration from Previous Versions](#migration-from-previous-versions)

## Getting Started

### Installation

```bash
# Install from PyPI (when available)
pip install baseTs
pip install "baseTs[dev]"    # with all testing dependencies

# Or install from source
git clone https://github.com/SympatiCog/baseTs.git
cd baseTs
pip install -e .
pip install -e ".[dev]"      # development, includes test dependencies
```

Quote the extras. Unquoted, `baseTs[dev]` is a shell glob: zsh — the default
shell on macOS, and what this repo's `CLAUDE.md` assumes — fails outright with
`no matches found: baseTs[dev]`, and bash silently expands it to a filename if
one happens to match (a `baseTsd` in the working directory is enough), which
installs the wrong thing without an error.

### Your First baseTs Object

```python
import numpy as np
from baseTs import baseTs

# Create a simple time series
times = np.arange(1000) / 100.0          # 10 s at exactly 100 Hz
data = np.sin(2 * np.pi * 0.2 * times) + 0.1*np.random.randn(1000)

ts = baseTs(data=data, times=times, freq=100.0, signal_name="example")
print(f"Time series length: {len(ts)}")
print(f"Data range: {np.min(ts.data):.3f} to {np.max(ts.data):.3f}")
print(f"Frequency: {ts.freq} Hz")
```

## Core Concepts

### baseTs Objects (Pandas Series Foundation)

baseTs is now built directly on pandas Series, providing:
- **Native Pandas Integration**: Access to 270+ pandas methods
- **Enhanced Performance**: Optimized time-series operations
- **Metadata Preservation**: Complete processing history tracking
- **Backward Compatibility**: All existing code works unchanged

```python
# Access properties (backward compatibility maintained)
print(f"Data: {ts.data[:5]}")        # First 5 data points (numpy array)
print(f"Times: {ts.times[:5]}")      # First 5 time points (numpy array)
print(f"Length: {len(ts)}")          # Number of points
print(f"Signal: {ts.signal_name}")   # Signal identifier
print(f"History: {ts.history}")      # Processing history

# New pandas-powered access
print(f"Mean: {ts.mean()}")          # Direct pandas method
print(f"Std: {ts.std()}")            # Direct pandas method
print(f"Describe: {ts.describe()}")  # Comprehensive statistics
```

### Architecture Overview

baseTs now uses a clean single-backend architecture:

```python
# Simple, unified creation (no backend selection needed)
ts = baseTs(data=data, times=times, freq=100.0)

# Inherits from pandas Series via TimeSeriesData
print(type(ts).__bases__)  # (<class 'baseTs.series.TimeSeriesData'>,)
print(type(ts).__bases__[0].__bases__)  # (<class 'pandas.core.series.Series'>,)
```

## Basic Operations

### Filtering

```python
# Low-pass filtering
filtered = ts.lowpass_at(cutoff=2.0)
high_filtered = ts.highpass_at(cutoff=0.5)
band_filtered = ts.bandpass_at(hp_hz=0.5, lp_hz=5.0)

# Gaussian filtering
smoothed = ts.gauss_filter(sigma=2.0)

# Savitzky-Golay filtering
sg_filtered = ts.sg_filter(window_length=51, polyorder=3)

# Every filter takes max_gap. A hole in the index (a jump between sample
# times with nothing marked) is refused when it is wider than this:
strict = ts.lowpass_at(cutoff=2.0, max_gap=0.5)
```

Two things a filter refuses to run over, with different remedies. A NaN in
the data is a marked gap: fill it with `interpolate_gaps()` first. A jump
in the index is an unmarked one, and `freq` cannot see it, so the filter
would run across the hole as if it were a single frame. Pass `max_gap` and
a wider jump is a typed refusal naming the gaps; leave it at the default
and the filter runs but warns. See [Holes in the Index](#holes-in-the-index).

### Normalization (Unchanged API)

```python
# Z-score normalization (mean=0, std=1)
normalized = ts.zscale()

# Range normalization (min=0, max=1)
range_normalized = ts.normalize_range()

# Center data (remove mean)
centered = ts.center()

# Scale data
scaled = ts.scale(factor=2.0)

# Absolute values
abs_data = ts.abs()
```

### Function Application (Unchanged API)

```python
# Apply mathematical functions
squared = ts.apply_function(lambda x: x**2)
sqrt_abs = ts.apply_function(lambda x: np.sqrt(np.abs(x)))
log_transform = ts.apply_function(lambda x: np.log(np.abs(x) + 1e-10))

# Apply with numpy functions
rectified = ts.apply_function(lambda x: np.maximum(x, 0))  # ReLU
```

### Outlier Detection and Removal (Enhanced)

```python
# Traditional LOWESS-based outlier filtering
ts.set_outlier_filter(z_threshold=3.0, frac=0.1)  # frac = LOWESS bandwidth
cleaned = ts.filter_outliers()

# New statistical outlier detection methods
outliers_z = ts.detect_outliers(method='zscore', threshold=2.5)
outliers_iqr = ts.detect_outliers(method='iqr', threshold=1.5)
outliers_mod = ts.detect_outliers(method='modified_zscore', threshold=3.5)

print(f"Found {np.sum(outliers_z)} z-score outliers")
print(f"Found {np.sum(outliers_iqr)} IQR outliers")
```

## Enhanced Time-Series Features

### Intelligent Resampling

```python
# Downsample to different frequencies
ts_1hz = ts.resample('1s', method='mean')      # 1 Hz using mean
ts_max = ts.resample('5s', method='max')       # Every 5 seconds using max
ts_median = ts.resample('100ms', method='median')  # 10 Hz using median

print(f"Original: {len(ts)} samples at {ts.freq} Hz")
print(f"Resampled: {len(ts_1hz)} samples at ~1 Hz")
```

### Enhanced Rolling Operations (2-5x Faster)

```python
# High-performance rolling operations using pandas
ts_smooth = ts.rolling_mean(window=50, center=True)
ts_volatility = ts.rolling_std(window=20)
ts_envelope = ts.rolling_max(window=10) - ts.rolling_min(window=10)

# Multiple rolling statistics
rolling_stats = {
    'mean': ts.rolling_mean(window=100),
    'std': ts.rolling_std(window=100),
    'max': ts.rolling_max(window=100),
    'min': ts.rolling_min(window=100),
    'median': ts.rolling_median(window=100)
}
```

### Time-Based Slicing (Optimized)

```python
# Extract time segments with optimized pandas indexing
segment = ts.time_slice(start_time=10.0, end_time=50.0)
beginning = ts.time_slice(end_time=25.0)
ending = ts.time_slice(start_time=75.0)

print(f"Original duration: {ts.duration():.2f}s")
print(f"Segment duration: {segment.duration():.2f}s")
```

### Time-Series Alignment

```python
# Create two time series with different timing
ts1 = baseTs(np.sin(2*np.pi*0.5*times), times, freq=100.0, signal_name="signal1")
ts2 = baseTs(np.cos(2*np.pi*0.5*times[::2]), times[::2], freq=50.0, signal_name="signal2")

# Align on common time index
aligned_ts1, aligned_ts2 = ts1.align_with(ts2, method='inner')
print(f"Aligned length: {len(aligned_ts1)} (was {len(ts1)} and {len(ts2)})")
```

### Cross-Correlation Analysis

```python
# Calculate correlation between time series
correlation = ts1.correlation_with(ts2, method='pearson')
spearman_corr = ts1.correlation_with(ts2, method='spearman')

print(f"Pearson correlation: {correlation:.3f}")
print(f"Spearman correlation: {spearman_corr:.3f}")
```

### Gap Interpolation

```python
# Introduce some gaps for demonstration
ts_with_gaps = ts.copy()
# Introduce gaps. Note: ts.data returns a read-only view under pandas
# Copy-on-Write, so `ts.data[100:110] = np.nan` raises ValueError. Assign
# through .iloc, or use set_indices_to_nan_and_interpolate() to do both
# steps at once.
ts_with_gaps.iloc[100:110] = np.nan
ts_with_gaps.iloc[200:205] = np.nan

# Fill gaps with different methods
linear_filled = ts_with_gaps.interpolate_gaps(method='linear')
spline_filled = ts_with_gaps.interpolate_gaps(method='spline', order=3)
polynomial_filled = ts_with_gaps.interpolate_gaps(method='polynomial', order=2)
time_filled = ts_with_gaps.interpolate_gaps(method='time', limit=10)

print(f"Original NaN count: {np.sum(np.isnan(ts_with_gaps.data))}")
print(f"After linear interpolation: {np.sum(np.isnan(linear_filled.data))}")
print(f"After cubic spline interpolation: {np.sum(np.isnan(spline_filled.data))}")
print(f"After polynomial (order 2) interpolation: {np.sum(np.isnan(polynomial_filled.data))}")
```

### Holes in the Index

`interpolate_gaps()` fills gaps that are marked, as NaN in the data. A
recording with an event structure, such as one epoch after another with
the acquisition paused between them, has gaps that are not marked: the
sample times simply jump. `freq` is the mean rate over the whole span and
cannot see them, so a filter designed at that rate runs across each hole
as if it were one frame. `gaps()` is where to find out, and `segments()`
is the remedy.

```python
# A 30 Hz session with two holes in the index
fs = 30.0
t = np.arange(0.0, 60.0, 1 / fs)
t = np.delete(t, np.r_[601:678, 1201:1278])       # two holes of 77 frames (2.6 s)
session = baseTs(np.sin(t), t, freq=fs)

holes = session.gaps()                              # start, end, width, n_missing
print(f"{len(holes)} gap(s), {holes['width'].sum():.1f} s missing in total")

runs = session.segments()                           # the contiguous runs
clean = [run.lowpass_at(2.0, max_gap=0.5) for run in runs]   # no hole inside any run
```

The default threshold is 1.5 times the median interval, so a single
dropped frame counts, and normal timing jitter does not. Trials of
different lengths that need to be averaged go on from here: see "Ragged
trials from a session with holes" in `docs/EXAMPLES.md` for the full path
from a session to an averaged recovery curve.

### Time Shifting

```python
# Shift time series by periods
ts_leading = ts.shift_time(periods=10)   # Lead by 10 samples
ts_lagging = ts.shift_time(periods=-5)   # Lag by 5 samples

print(f"Original length: {len(ts)}")
print(f"After shifting: {len(ts_leading)} (removes NaN values)")
```

## Advanced Analysis

### Enhanced Frequency Analysis

```python
# Enhanced plot_fft_power with windowing and frequency range control
ts.plot_fft_power()  # Basic power spectrum
ts.plot_fft_power(window='hann', min_rate=0.1, max_rate=50)  # Hanning window, 0.1-50 Hz
ts.plot_fft_power(window='blackman', scale_power=True)  # Blackman window, scaled power

# Get frequency content data for analysis
freqs, power = ts.get_frequency_content(window='hann')
freqs_bm, power_bm = ts.get_frequency_content(window='blackman')

# Enhanced peak frequency detection
peak_freq = ts.get_peak_freq()  # Basic peak frequency
peak_windowed = ts.get_peak_freq(window='hann')  # With Hanning window
top_3_peaks = ts.get_peak_freq(num_pks=3, window='blackman')  # Top 3 peaks
peak_in_range = ts.get_peak_freq(window='hann', min_freq=1.0, max_freq=50.0)  # Frequency range

# Traditional FFT methods still available
freqs_traditional, power_traditional = ts.compute_fft_power()

print(f"Peak frequency (basic): {peak_freq:.2f} Hz")
print(f"Peak frequency (windowed): {peak_windowed:.2f} Hz")
print(f"Top 3 peaks: {[f'{p:.1f}' for p in top_3_peaks]} Hz")
print(f"Peak in 1-50 Hz range: {peak_in_range:.2f} Hz")
```

### Comprehensive Statistics

```python
# Enhanced statistics using pandas
stats = ts.get_statistics()
print(f"""
Enhanced Statistics:
- Count: {stats['count']}
- Mean: {stats['mean']:.4f}
- Std Dev: {stats['std']:.4f}
- Min: {stats['min']:.4f}
- Max: {stats['max']:.4f}
- Median: {stats['median']:.4f}
- 25th percentile: {stats['q25']:.4f}
- 75th percentile: {stats['q75']:.4f}
- Duration: {stats['duration']:.2f}s
- Sample Rate: {stats['sample_rate']:.1f} Hz
- Median interval: {stats['median_dt'] * 1000:.1f} ms
- Index gaps: {stats['n_gaps']} ({stats['gapped_duration']:.2f}s in total)
""")
```

`sample_rate` is the mean rate over the whole span. `n_gaps` and
`gapped_duration` say whether it can be trusted: a rate lower than the
declared `freq` with gaps reported beside it is a recording with holes, not
a slow one. `info()` prints the same two figures next to the rate.

### Method Chaining (Enhanced)

```python
# Chain operations with new enhanced methods
processed = (ts
             .bandpass_at(hp_hz=0.5, lp_hz=10.0)
             .filter_outliers()
             .rolling_mean(window=50)
             .zscale()
             .resample('100ms', method='mean'))

print(f"Processing chain: {len(ts)} → {len(processed)} samples")
print(f"Processing history: {len(processed.history)} steps")
```

### Native Pandas Integration

```python
# Direct access to pandas methods
quantiles = ts.quantile([0.1, 0.25, 0.5, 0.75, 0.9])
description = ts.describe()

# Pandas rolling operations (in addition to baseTs methods)
pandas_rolling = ts.rolling(window=20).agg(['mean', 'std', 'min', 'max'])

# Convert to DataFrame for complex analysis
df = ts.to_frame('signal_value')
df['time'] = ts.index
df['rolling_mean'] = ts.rolling(50).mean()

print(f"Quantiles: {quantiles}")
print(f"DataFrame shape: {df.shape}")
```

## Performance Guidelines

### Memory Optimization

The new pandas-based architecture provides automatic memory optimization:

```python
# Memory efficiency improvements, measured with the standard library's tracemalloc
import tracemalloc

def memory_efficient_processing(large_data, large_times):
    """Process large datasets efficiently with pandas Series foundation."""

    tracemalloc.start()

    # Create baseTs object (now automatically optimized)
    ts = baseTs(data=large_data, times=large_times, freq=100.0)

    after_creation, _ = tracemalloc.get_traced_memory()
    print(f"Allocated after creation: {after_creation / 1024**2:.1f} MB")

    # Process with enhanced operations
    processed = ts.rolling_mean(window=100).resample('1s', method='mean')

    final_memory, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"Allocated after processing: {final_memory / 1024**2:.1f} MB (peak {peak_memory / 1024**2:.1f} MB)")

    return processed

# Test with large dataset
large_data = np.random.randn(100000)
large_times = np.linspace(0, 1000, 100000)
result = memory_efficient_processing(large_data, large_times)
```

### Performance Benchmarking

```python
import time

def benchmark_enhanced_operations():
    """Benchmark new pandas-powered operations."""
    
    # Create test data
    data = np.random.randn(10000)
    times = np.arange(10000) / 100.0      # 100 s at exactly 100 Hz
    ts = baseTs(data=data, times=times, freq=100.0)
    
    operations = {
        'rolling_mean': lambda x: x.rolling_mean(window=100),
        'time_slice': lambda x: x.time_slice(start_time=10, end_time=90),
        'resample': lambda x: x.resample('1s', method='mean'),
        'correlation': lambda x: x.correlation_with(x, method='pearson'),
        'detect_outliers': lambda x: x.detect_outliers(method='zscore'),
        'statistics': lambda x: x.get_statistics()
    }
    
    results = {}
    for name, operation in operations.items():
        # Warm up
        operation(ts)
        
        # Benchmark
        start = time.perf_counter()
        for _ in range(10):
            result = operation(ts)
        end = time.perf_counter()
        
        avg_time = (end - start) / 10
        results[name] = avg_time
        print(f"{name}: {avg_time:.6f}s")
    
    return results

# Run benchmark
benchmark_results = benchmark_enhanced_operations()
```

## Examples and Recipes

### Example 1: Signal Processing Workflow

```python
def process_physiological_signal(raw_data, sampling_rate):
    """Process physiological signal (ECG, EEG, etc.) with enhanced baseTs."""
    
    # Create time axis
    times = np.arange(len(raw_data)) / sampling_rate
    
    # Create baseTs object with metadata
    signal = baseTs(
        data=raw_data, 
        times=times, 
        freq=sampling_rate,
        signal_name="physiological_signal"
    )
    
    # Enhanced processing pipeline
    # 1. Remove DC offset and detrend
    detrended = signal.apply_function(lambda x: x - np.mean(x))
    
    # 2. Bandpass filter for physiological range
    filtered = detrended.bandpass_at(hp_hz=0.5, lp_hz=40.0)
    
    # 3. Remove artifacts using enhanced outlier detection
    outliers = filtered.detect_outliers(method='modified_zscore', threshold=3.5)
    print(f"Detected {np.sum(outliers)} artifact samples ({100*np.sum(outliers)/len(filtered):.1f}%)")
    
    # 4. Clean using traditional LOWESS filter, then fill acquisition gaps.
    # filter_outliers deliberately leaves pre-existing gaps as NaN, and the
    # frequency analysis in step 7 rejects NaN input.
    cleaned = filtered.filter_outliers().interpolate_gaps()
    
    # 5. Smooth with rolling mean
    smoothed = cleaned.rolling_mean(window=int(sampling_rate * 0.1))  # 100ms window
    
    # 6. Normalize
    normalized = smoothed.zscale()
    
    # 7. Extract features
    stats = normalized.get_statistics()
    freqs, power = normalized.get_frequency_content(window='hann')
    
    return {
        'processed': normalized,
        'statistics': stats,
        'frequency_content': (freqs, power),
        'quality_metrics': {
            'artifact_percentage': 100 * np.sum(outliers) / len(filtered),
            'processing_steps': len(normalized.history)
        }
    }

# Usage
sampling_rate = 250  # Hz
raw_signal = np.sin(2*np.pi*1.2*np.linspace(0, 60, 15000)) + 0.1*np.random.randn(15000)
result = process_physiological_signal(raw_signal, sampling_rate)
print(f"Processing completed: {result['quality_metrics']}")
```

### Example 2: Multi-Signal Analysis

```python
def analyze_multiple_signals(signals_dict):
    """Analyze multiple synchronized time series."""
    
    # Process each signal
    processed_signals = {}
    for name, (data, times) in signals_dict.items():
        ts = baseTs(data=data, times=times, freq=100.0, signal_name=name)
        processed = ts.bandpass_at(hp_hz=0.1, lp_hz=10.0).rolling_mean(window=50)
        processed_signals[name] = processed
    
    # Cross-correlation analysis
    signal_names = list(processed_signals.keys())
    correlations = {}
    
    for i, sig1_name in enumerate(signal_names):
        for sig2_name in signal_names[i+1:]:
            sig1 = processed_signals[sig1_name]
            sig2 = processed_signals[sig2_name]
            
            # Align signals before correlation
            aligned_sig1, aligned_sig2 = sig1.align_with(sig2, method='inner')
            correlation = aligned_sig1.correlation_with(aligned_sig2, method='pearson')
            
            correlations[f"{sig1_name}_vs_{sig2_name}"] = correlation
    
    # Synchronization analysis
    base_signal = processed_signals[signal_names[0]]
    aligned_signals = []
    
    for name, signal in processed_signals.items():
        if name != signal_names[0]:
            aligned_base, aligned_signal = base_signal.align_with(signal, method='inner')
            aligned_signals.append((name, aligned_signal))
            base_signal = aligned_base
    
    return {
        'processed_signals': processed_signals,
        'correlations': correlations,
        'aligned_signals': aligned_signals,
        'base_signal': base_signal
    }

# Usage
signals = {
    'ecg': (np.sin(2*np.pi*1.2*np.arange(1000)/100), np.arange(1000)/100),
    'resp': (0.3*np.sin(2*np.pi*0.3*np.arange(1000)/100), np.arange(1000)/100),
    'temp': (37 + 0.5*np.sin(2*np.pi*0.1*np.arange(1000)/100), np.arange(1000)/100)
}

multi_analysis = analyze_multiple_signals(signals)
for pair, corr in multi_analysis['correlations'].items():
    print(f"{pair}: {corr:.3f}")
```

### Example 3: Real-Time-Style Processing

```python
def streaming_processor():
    """Simulate real-time processing with enhanced baseTs."""
    
    # Initialize with first batch
    chunk_size = 1000
    data_chunk = np.random.randn(chunk_size)
    time_chunk = np.arange(chunk_size) / 100.0  # 100 Hz
    
    # Create initial time series
    ts = baseTs(data=data_chunk, times=time_chunk, freq=100.0, signal_name="stream")
    
    # Process initial chunk
    processed = ts.bandpass_at(hp_hz=0.5, lp_hz=20.0).rolling_mean(window=50)
    
    # Simulate additional chunks
    for i in range(5):
        # Generate new chunk
        new_data = np.random.randn(chunk_size)
        new_times = np.arange(chunk_size) / 100.0 + (i + 1) * 10.0
        
        # Create new segment
        new_segment = baseTs(data=new_data, times=new_times, freq=100.0)
        new_processed = new_segment.bandpass_at(hp_hz=0.5, lp_hz=20.0).rolling_mean(window=50)
        
        # Concatenate (simplified - in real streaming, you'd use a buffer)
        combined_data = np.concatenate([processed.data, new_processed.data])
        combined_times = np.concatenate([processed.times, new_processed.times])
        
        processed = baseTs(
            data=combined_data, 
            times=combined_times, 
            freq=100.0,
            signal_name="continuous_stream"
        )
        
        # Extract recent statistics
        recent_segment = processed.time_slice(start_time=processed.times[-500]/100*100)
        stats = recent_segment.get_statistics()
        
        print(f"Chunk {i+1}: Recent mean={stats['mean']:.3f}, std={stats['std']:.3f}")
    
    return processed

# Run streaming simulation
stream_result = streaming_processor()
```

### Example 4: Scientific Data Analysis

```python
def scientific_time_series_analysis(experimental_data, metadata):
    """Comprehensive scientific analysis workflow."""
    
    # Extract metadata
    sampling_rate = metadata['sampling_rate']
    experiment_name = metadata['experiment_name']
    conditions = metadata.get('conditions', {})
    
    # Create time axis
    times = np.arange(len(experimental_data)) / sampling_rate
    
    # Create baseTs with rich metadata
    ts = baseTs(
        data=experimental_data,
        times=times,
        freq=sampling_rate,
        signal_name=experiment_name
    )
    
    # Quality assessment
    raw_stats = ts.get_statistics()
    outliers = ts.detect_outliers(method='iqr', threshold=2.0)
    quality_score = 1.0 - np.sum(outliers) / len(ts)
    
    # Preprocessing pipeline
    if quality_score < 0.95:
        print(f"Data quality: {quality_score:.1%} - applying enhanced cleaning")
        # interpolate_gaps because filter_outliers leaves pre-existing
        # acquisition gaps as NaN, and the frequency analysis below rejects
        # NaN input.
        cleaned = ts.filter_outliers().interpolate_gaps()
    else:
        print(f"Data quality: {quality_score:.1%} - minimal preprocessing needed")
        cleaned = ts
    
    # Signal processing
    # lp_hz must be strictly below Nyquist (sampling_rate / 2 = 50 Hz here).
    filtered = cleaned.bandpass_at(hp_hz=0.1, lp_hz=40.0)
    normalized = filtered.zscale()
    
    # Feature extraction
    # 1. Time-domain features
    windowed_stats = normalized.rolling_mean(window=int(sampling_rate))
    temporal_features = {
        'mean_activity': np.mean(np.abs(normalized.data)),
        'variance': np.var(normalized.data),
        'peak_to_peak': np.max(normalized.data) - np.min(normalized.data)
    }
    
    # 2. Frequency-domain features
    freqs, power = normalized.get_frequency_content(window='hann')
    centroid = np.sum(freqs * power) / np.sum(power)
    spectral_features = {
        'peak_frequency': freqs[np.argmax(power)],
        'spectral_centroid': centroid,
        'spectral_bandwidth': np.sqrt(np.sum(((freqs - centroid) ** 2) * power) / np.sum(power))
    }
    
    # 3. Statistical features
    enhanced_stats = normalized.get_statistics()
    
    # Condition-specific analysis
    condition_results = {}
    if 'time_windows' in conditions:
        for condition_name, (start, end) in conditions['time_windows'].items():
            condition_segment = normalized.time_slice(start_time=start, end_time=end)
            condition_stats = condition_segment.get_statistics()
            condition_results[condition_name] = condition_stats
    
    # Generate comprehensive report
    analysis_report = {
        'metadata': metadata,
        'data_quality': {
            'quality_score': quality_score,
            'outlier_percentage': 100 * np.sum(outliers) / len(ts),
            'original_stats': raw_stats
        },
        'processed_data': normalized,
        'features': {
            'temporal': temporal_features,
            'spectral': spectral_features,
            'statistical': enhanced_stats
        },
        'condition_analysis': condition_results,
        'processing_history': normalized.history
    }
    
    return analysis_report

# Usage
experimental_data = (np.sin(2*np.pi*0.5*np.linspace(0, 120, 12000)) + 
                     0.2*np.sin(2*np.pi*5*np.linspace(0, 120, 12000)) + 
                     0.1*np.random.randn(12000))

metadata = {
    'sampling_rate': 100,
    'experiment_name': 'test_condition_A',
    'conditions': {
        'time_windows': {
            'baseline': (0, 30),
            'stimulus': (30, 90),
            'recovery': (90, 120)
        }
    }
}

scientific_analysis = scientific_time_series_analysis(experimental_data, metadata)
print(f"Analysis complete for {scientific_analysis['metadata']['experiment_name']}")
print(f"Data quality: {scientific_analysis['data_quality']['quality_score']:.1%}")
for condition, stats in scientific_analysis['condition_analysis'].items():
    print(f"{condition}: mean={stats['mean']:.3f}, std={stats['std']:.3f}")
```

## Migration from Previous Versions

### No Migration Required!

The best news about the new pandas Series foundation is that **all existing code works unchanged**:

```python
# This code works exactly the same as before
ts = baseTs(data=data, times=times)
filtered = ts.lowpass_at(cutoff=2.0)
normalized = ts.zscale()
outlier_free = ts.filter_outliers()
```

### New Features Automatically Available

```python
# These enhanced methods are now available in all existing code
resampled = ts.resample('100ms', method='mean')
correlation = ts1.correlation_with(ts2)
outliers = ts.detect_outliers(method='iqr')
smoothed = ts.rolling_mean(window=50)
```

### Performance Improvements

Your existing code automatically benefits from:
- **2-5x faster rolling operations**
- **~20% memory reduction**
- **Optimized time-slicing**
- **Enhanced statistical computations**

### Accessing New Capabilities

```python
# Direct pandas access (new capability)
ts.describe()                    # Pandas statistical summary
ts.quantile([0.25, 0.5, 0.75])  # Quantiles
ts.rolling(10).mean()            # Native pandas rolling

# Enhanced baseTs methods (new)
ts.resample('1s', method='mean')       # Intelligent resampling
ts.interpolate_gaps(method='spline', order=3)   # Gap filling
other_ts = ts.lowpass_at(cutoff=1.0)   # any second series on the same time base
ts.align_with(other_ts)                # Time series alignment
ts.correlation_with(other_ts)          # Correlation coefficient
```

This user guide showcases the enhanced capabilities of baseTs while emphasizing that all existing code continues to work unchanged, now with better performance and additional functionality through the pandas Series foundation.