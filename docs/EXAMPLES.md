# baseTs Examples and Recipes

This document provides practical examples and code recipes for common use cases with baseTs.

## Table of Contents
1. [Getting Started Examples](#getting-started-examples)
2. [Signal Processing Workflows](#signal-processing-workflows)
3. [Time-Series Analysis](#time-series-analysis)
4. [Financial Data Analysis](#financial-data-analysis)
5. [Scientific Data Processing](#scientific-data-processing)
6. [IoT and Sensor Data](#iot-and-sensor-data)
7. [Performance Optimization](#performance-optimization)
8. [Integration Examples](#integration-examples)

---

## Getting Started Examples

### Basic Signal Creation and Processing

```python
import numpy as np
import pandas as pd
from baseTs import baseTs
import matplotlib.pyplot as plt

# Create a synthetic signal
def create_test_signal(n_points=1000, duration=10):
    """Create a test signal with multiple components."""
    t = np.linspace(0, duration, n_points)
    
    # Multiple frequency components
    signal = (
        2.0 * np.sin(2 * np.pi * 0.5 * t) +      # 0.5 Hz component
        1.0 * np.sin(2 * np.pi * 2.0 * t) +      # 2.0 Hz component
        0.5 * np.sin(2 * np.pi * 5.0 * t) +      # 5.0 Hz component
        0.2 * np.random.randn(n_points)          # Noise
    )
    
    # Add some outliers
    outlier_indices = np.random.choice(n_points, size=20, replace=False)
    signal[outlier_indices] += 5 * np.random.randn(len(outlier_indices))
    
    return signal, t

# Create and process the signal
data, times = create_test_signal()
ts = baseTs(data=data, times=times, signal_name="Test Signal")

print(f"Created signal with {ts.len()} points")
print(f"Data range: {np.min(ts.data):.2f} to {np.max(ts.data):.2f}")

# Basic processing pipeline
filtered = ts.lowpass_filter(cutoff=0.3)
cleaned = filtered.remove_outliers(method='iqr', factor=2.0)
normalized = cleaned.zscale()

print(f"After processing: {normalized.len()} points")
print(f"Normalized mean: {np.mean(normalized.data):.6f}")
print(f"Normalized std: {np.std(normalized.data):.6f}")
```

### Backend Comparison

```python
def compare_backends(data, times):
    """Compare results between NumPy and Series backends."""
    
    # Process with NumPy backend
    ts_numpy = baseTs(data=data, times=times, backend='numpy')
    filtered_numpy = ts_numpy.lowpass_filter(cutoff=0.3).zscale()
    
    # Process with Series backend
    ts_series = baseTs(data=data, times=times, backend='series')
    filtered_series = ts_series.lowpass_filter(cutoff=0.3).zscale()
    
    # Compare results
    diff = np.abs(filtered_numpy.data - filtered_series.data)
    max_diff = np.max(diff)
    mean_diff = np.mean(diff)
    
    print(f"Backend Comparison:")
    print(f"  Max difference: {max_diff:.2e}")
    print(f"  Mean difference: {mean_diff:.2e}")
    print(f"  Results identical: {max_diff < 1e-10}")
    
    return filtered_numpy, filtered_series

# Test backend compatibility
numpy_result, series_result = compare_backends(data, times)
```

---

## Signal Processing Workflows

### EEG Signal Processing

```python
def process_eeg_signal(raw_eeg, sampling_rate=250):
    """
    Process EEG signal with standard preprocessing steps.
    
    Args:
        raw_eeg: Raw EEG data (microvolts)
        sampling_rate: Sampling rate in Hz
    
    Returns:
        Processed EEG signal
    """
    # Create time axis
    times = np.arange(len(raw_eeg)) / sampling_rate
    
    # Create baseTs object
    eeg = baseTs(data=raw_eeg, times=times, backend='numpy', 
                 signal_name="EEG", freq=sampling_rate)
    
    # EEG processing pipeline
    # 1. Remove DC offset and linear trend
    detrended = eeg.apply_function(lambda x: x - np.mean(x))
    
    # 2. Bandpass filter (1-50 Hz for typical EEG analysis)
    # Note: cutoff is normalized by Nyquist frequency
    nyquist = sampling_rate / 2
    low_cutoff = 1.0 / nyquist    # 1 Hz
    high_cutoff = 50.0 / nyquist  # 50 Hz
    
    if high_cutoff < 1.0:  # Ensure valid cutoff
        bandpassed = detrended.lowpass_filter(cutoff=high_cutoff)
        # For highpass, we'd need to implement or use alternative
    else:
        bandpassed = detrended.lowpass_filter(cutoff=0.8)  # Conservative filter
    
    # 3. Remove artifacts (muscle artifacts, eye blinks)
    cleaned = bandpassed.remove_outliers(method='zscore', threshold=4)
    
    # 4. Z-score normalization
    normalized = cleaned.zscale()
    
    return normalized

# Example usage
sampling_rate = 250  # Hz
duration = 60        # seconds
n_samples = sampling_rate * duration

# Simulate EEG signal
t = np.arange(n_samples) / sampling_rate
eeg_signal = (
    10 * np.sin(2 * np.pi * 10 * t) +  # Alpha rhythm (10 Hz)
    5 * np.sin(2 * np.pi * 20 * t) +   # Beta rhythm (20 Hz)
    2 * np.random.randn(n_samples)      # Background noise
)

# Add some artifacts
artifact_times = [15, 30, 45]  # seconds
for artifact_time in artifact_times:
    start_idx = int(artifact_time * sampling_rate)
    end_idx = start_idx + int(0.5 * sampling_rate)  # 500ms artifact
    eeg_signal[start_idx:end_idx] += 50 * np.random.randn(end_idx - start_idx)

processed_eeg = process_eeg_signal(eeg_signal, sampling_rate)
print(f"Processed EEG: {processed_eeg.len()} samples")
```

### Audio Signal Processing

```python
def process_audio_signal(audio_data, sample_rate=44100):
    """
    Process audio signal for analysis or enhancement.
    
    Args:
        audio_data: Audio samples (typically float32, range [-1, 1])
        sample_rate: Audio sample rate in Hz
    
    Returns:
        Processed audio signal
    """
    # Create time axis
    times = np.arange(len(audio_data)) / sample_rate
    
    # Create baseTs object
    audio = baseTs(data=audio_data, times=times, backend='numpy',
                   signal_name="Audio", freq=sample_rate)
    
    # Audio processing pipeline
    # 1. Remove DC offset
    dc_removed = audio.apply_function(lambda x: x - np.mean(x))
    
    # 2. Apply high-pass filter to remove low-frequency rumble
    # Remove frequencies below 80 Hz
    nyquist = sample_rate / 2
    hp_cutoff = 80.0 / nyquist
    if hp_cutoff < 1.0:
        # Note: This is a low-pass filter, ideally we'd have high-pass
        # For demonstration, we'll use a gentle low-pass filter
        filtered = dc_removed.lowpass_filter(cutoff=0.8)
    else:
        filtered = dc_removed
    
    # 3. Compress dynamic range (simple compression)
    def soft_compression(x, threshold=0.7, ratio=4.0):
        """Simple soft compression."""
        compressed = np.copy(x)
        mask = np.abs(x) > threshold
        excess = np.abs(x[mask]) - threshold
        compressed[mask] = np.sign(x[mask]) * (threshold + excess / ratio)
        return compressed
    
    compressed = filtered.apply_function(
        lambda x: soft_compression(x, threshold=0.7, ratio=4.0)
    )
    
    # 4. Normalize to prevent clipping
    normalized = compressed.normalize_range(new_min=-0.95, new_max=0.95)
    
    return normalized

# Example: Process a synthetic audio signal
sample_rate = 44100
duration = 5  # seconds
t = np.arange(sample_rate * duration) / sample_rate

# Create a complex audio signal
audio_signal = (
    0.3 * np.sin(2 * np.pi * 440 * t) +      # A4 note
    0.2 * np.sin(2 * np.pi * 880 * t) +      # A5 note (octave)
    0.1 * np.sin(2 * np.pi * 1320 * t) +     # E6 note (fifth)
    0.05 * np.random.randn(len(t))           # Background noise
)

# Add some distortion/clipping
audio_signal = np.clip(audio_signal, -1.2, 1.2)

processed_audio = process_audio_signal(audio_signal, sample_rate)
print(f"Processed audio: {processed_audio.len()} samples")
```

---

## Time-Series Analysis

### Stock Price Analysis

```python
def analyze_stock_data(prices, dates):
    """
    Comprehensive stock price analysis using Series backend.
    
    Args:
        prices: Array of stock prices
        dates: Array of dates (datetime objects or strings)
    
    Returns:
        Dictionary containing analysis results
    """
    # Ensure dates are datetime objects
    if not isinstance(dates, pd.DatetimeIndex):
        dates = pd.to_datetime(dates)
    
    # Create time series with Series backend for datetime features
    stock = baseTs(data=prices, times=dates, backend='series',
                   signal_name="Stock Price")
    
    # Calculate log returns
    log_prices = stock.apply_function(np.log)
    returns = log_prices.apply_function(lambda x: np.diff(x, prepend=x[0]))
    
    # Technical indicators
    sma_20 = stock.rolling_mean(window=20)     # 20-day simple moving average
    sma_50 = stock.rolling_mean(window=50)     # 50-day simple moving average
    
    # Volatility (20-day rolling standard deviation of returns)
    volatility = returns.rolling_std(window=20)
    
    # Bollinger Bands (20-day SMA ± 2 standard deviations)
    rolling_std = stock.rolling_std(window=20)
    upper_band = sma_20.data + 2 * rolling_std.data
    lower_band = sma_20.data - 2 * rolling_std.data
    
    # Performance metrics
    total_return = (prices[-1] / prices[0] - 1) * 100
    annualized_vol = np.std(returns.data) * np.sqrt(252) * 100  # 252 trading days
    
    # Time-based analysis
    ytd_data = stock.time_slice(start=f"{dates[-1].year}-01-01")
    ytd_return = (ytd_data.data[-1] / ytd_data.data[0] - 1) * 100 if len(ytd_data.data) > 1 else 0
    
    # Statistical analysis
    stats = stock.get_statistics()
    
    return {
        'stock': stock,
        'returns': returns,
        'sma_20': sma_20,
        'sma_50': sma_50,
        'volatility': volatility,
        'bollinger_bands': {
            'upper': upper_band,
            'middle': sma_20.data,
            'lower': lower_band
        },
        'performance': {
            'total_return_pct': total_return,
            'ytd_return_pct': ytd_return,
            'annualized_volatility_pct': annualized_vol
        },
        'statistics': stats
    }

# Example usage
np.random.seed(42)  # For reproducible results
dates = pd.date_range('2022-01-01', '2023-12-31', freq='D')
n_days = len(dates)

# Simulate stock price with trend and volatility
returns = np.random.randn(n_days) * 0.02 + 0.0005  # 2% daily vol, 0.05% daily drift
log_prices = np.cumsum(returns)
prices = 100 * np.exp(log_prices)  # Start at $100

analysis = analyze_stock_data(prices, dates)

print("Stock Analysis Results:")
print(f"Total Return: {analysis['performance']['total_return_pct']:.2f}%")
print(f"YTD Return: {analysis['performance']['ytd_return_pct']:.2f}%")
print(f"Annualized Volatility: {analysis['performance']['annualized_volatility_pct']:.2f}%")
print(f"Current Price: ${analysis['stock'].data[-1]:.2f}")
print(f"20-day SMA: ${analysis['sma_20'].data[-1]:.2f}")
```

### Seasonal Decomposition

```python
def seasonal_analysis(data, dates, period=365):
    """
    Analyze seasonal patterns in time series data.
    
    Args:
        data: Time series data
        dates: Date index
        period: Seasonal period (365 for daily data with yearly seasonality)
    
    Returns:
        Seasonal analysis components
    """
    ts = baseTs(data=data, times=pd.to_datetime(dates), backend='series')
    
    # Calculate trend using long-term moving average
    trend_window = min(period // 4, len(data) // 10)  # Adaptive window
    if trend_window >= 3:
        trend = ts.rolling_mean(window=trend_window, center=True)
    else:
        trend = ts
    
    # Remove trend to get detrended series
    detrended_data = data - trend.data
    detrended = baseTs(data=detrended_data, times=dates, backend='series')
    
    # Calculate seasonal component by averaging over periods
    seasonal_data = np.zeros_like(data)
    if len(data) >= period:
        for i in range(period):
            indices = np.arange(i, len(data), period)
            if len(indices) > 1:
                seasonal_data[indices] = np.mean(detrended_data[indices])
    
    seasonal = baseTs(data=seasonal_data, times=dates, backend='series')
    
    # Calculate residual (noise)
    residual_data = data - trend.data - seasonal_data
    residual = baseTs(data=residual_data, times=dates, backend='series')
    
    # Statistics
    trend_strength = 1 - np.var(residual_data) / np.var(data - seasonal_data)
    seasonal_strength = 1 - np.var(residual_data) / np.var(data - trend.data)
    
    return {
        'original': ts,
        'trend': trend,
        'seasonal': seasonal,
        'residual': residual,
        'trend_strength': trend_strength,
        'seasonal_strength': seasonal_strength
    }

# Example: Seasonal analysis of temperature data
dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
n_days = len(dates)

# Simulate temperature data with seasonal pattern
day_of_year = np.array([d.timetuple().tm_yday for d in dates])
seasonal_temp = 20 + 15 * np.sin(2 * np.pi * day_of_year / 365.25)  # Seasonal pattern
trend_temp = 0.001 * np.arange(n_days)  # Slight warming trend
noise_temp = 3 * np.random.randn(n_days)  # Daily variation
temperature = seasonal_temp + trend_temp + noise_temp

seasonal_analysis_result = seasonal_analysis(temperature, dates)

print("Seasonal Analysis Results:")
print(f"Trend strength: {seasonal_analysis_result['trend_strength']:.3f}")
print(f"Seasonal strength: {seasonal_analysis_result['seasonal_strength']:.3f}")
```

---

## Financial Data Analysis

### Portfolio Analysis

```python
def portfolio_analysis(price_data, weights=None):
    """
    Analyze a portfolio of stocks.
    
    Args:
        price_data: Dictionary of {symbol: (prices, dates)} 
        weights: Portfolio weights (default: equal weights)
    
    Returns:
        Portfolio analysis results
    """
    symbols = list(price_data.keys())
    n_assets = len(symbols)
    
    if weights is None:
        weights = np.ones(n_assets) / n_assets  # Equal weights
    
    # Convert to baseTs objects and calculate returns
    returns_data = {}
    for symbol, (prices, dates) in price_data.items():
        ts = baseTs(data=prices, times=pd.to_datetime(dates), 
                   backend='series', signal_name=symbol)
        
        # Calculate log returns
        log_returns = ts.apply_function(lambda x: np.diff(np.log(x), prepend=np.log(x[0])))
        returns_data[symbol] = log_returns
    
    # Align all return series to same dates
    common_dates = returns_data[symbols[0]].times
    for symbol in symbols[1:]:
        common_dates = np.intersect1d(common_dates, returns_data[symbol].times)
    
    # Create return matrix
    return_matrix = np.zeros((len(common_dates), n_assets))
    for i, symbol in enumerate(symbols):
        ts = returns_data[symbol]
        # Simple alignment - in practice, you'd want more sophisticated alignment
        if len(ts.times) == len(common_dates):
            return_matrix[:, i] = ts.data
    
    # Portfolio returns
    portfolio_returns = np.dot(return_matrix, weights)
    portfolio_ts = baseTs(data=portfolio_returns, times=common_dates, 
                         backend='series', signal_name="Portfolio")
    
    # Risk metrics
    portfolio_vol = np.std(portfolio_returns) * np.sqrt(252)  # Annualized
    individual_vols = np.std(return_matrix, axis=0) * np.sqrt(252)
    
    # Correlation matrix
    correlation_matrix = np.corrcoef(return_matrix.T)
    
    # Performance metrics
    total_return = np.sum(portfolio_returns)
    sharpe_ratio = np.mean(portfolio_returns) / np.std(portfolio_returns) * np.sqrt(252)
    
    # Rolling metrics
    rolling_vol = portfolio_ts.rolling_std(window=30) * np.sqrt(252)
    rolling_returns = portfolio_ts.rolling_mean(window=30) * 252
    
    return {
        'portfolio_returns': portfolio_ts,
        'individual_returns': {symbol: returns_data[symbol] for symbol in symbols},
        'weights': dict(zip(symbols, weights)),
        'risk_metrics': {
            'portfolio_volatility': portfolio_vol,
            'individual_volatilities': dict(zip(symbols, individual_vols)),
            'correlation_matrix': correlation_matrix
        },
        'performance_metrics': {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio
        },
        'rolling_metrics': {
            'volatility': rolling_vol,
            'returns': rolling_returns
        }
    }

# Example portfolio analysis
np.random.seed(42)
symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
dates = pd.date_range('2022-01-01', '2023-12-31', freq='D')

# Simulate correlated stock prices
n_days = len(dates)
correlation = 0.3  # Moderate correlation between stocks

price_data = {}
for i, symbol in enumerate(symbols):
    # Generate correlated returns
    if i == 0:
        returns = np.random.randn(n_days) * 0.02
    else:
        returns = (correlation * price_data[symbols[0]][0][1:] / price_data[symbols[0]][0][:-1] - 1 +
                  np.sqrt(1 - correlation**2) * np.random.randn(n_days-1) * 0.02)
        returns = np.concatenate([[0], returns])
    
    prices = 100 * np.exp(np.cumsum(returns))
    price_data[symbol] = (prices, dates)

# Equal-weighted portfolio
portfolio_result = portfolio_analysis(price_data)

print("Portfolio Analysis:")
print(f"Portfolio Volatility: {portfolio_result['risk_metrics']['portfolio_volatility']:.2%}")
print(f"Sharpe Ratio: {portfolio_result['performance_metrics']['sharpe_ratio']:.2f}")
```

---

## Scientific Data Processing

### Experimental Data Analysis

```python
def analyze_experimental_data(measurements, timestamps, metadata=None):
    """
    Analyze experimental measurements with quality control.
    
    Args:
        measurements: Array of measured values
        timestamps: Array of measurement timestamps
        metadata: Dictionary of experimental metadata
    
    Returns:
        Analysis results with quality metrics
    """
    if metadata is None:
        metadata = {}
    
    # Create time series
    ts = baseTs(data=measurements, times=pd.to_datetime(timestamps),
               backend='series', signal_name=metadata.get('experiment_name', 'Experiment'))
    
    # Quality control
    # 1. Check for missing values
    n_missing = np.sum(np.isnan(measurements))
    
    # 2. Detect outliers using multiple methods
    outliers_iqr = ts.outlier_indices(method='iqr', factor=2.0)
    outliers_zscore = ts.outlier_indices(method='zscore', threshold=3)
    
    # 3. Check measurement stability (drift analysis)
    # Divide into segments and check means
    n_segments = 10
    segment_size = len(measurements) // n_segments
    segment_means = []
    
    for i in range(n_segments):
        start_idx = i * segment_size
        end_idx = min((i + 1) * segment_size, len(measurements))
        if end_idx > start_idx:
            segment_mean = np.nanmean(measurements[start_idx:end_idx])
            segment_means.append(segment_mean)
    
    drift_variance = np.var(segment_means) if len(segment_means) > 1 else 0
    
    # Data cleaning
    cleaned = ts.remove_outliers(method='iqr', factor=2.5)
    
    # Statistical analysis
    stats = cleaned.get_statistics()
    
    # Smoothing for trend analysis
    if len(cleaned.data) > 50:
        smoothed = cleaned.rolling_mean(window=min(50, len(cleaned.data) // 10))
    else:
        smoothed = cleaned
    
    # Uncertainty estimation
    measurement_uncertainty = np.std(measurements) / np.sqrt(len(measurements))
    
    # Data quality score (0-1, higher is better)
    quality_factors = {
        'completeness': 1 - (n_missing / len(measurements)),
        'stability': 1 / (1 + drift_variance / np.var(measurements)) if np.var(measurements) > 0 else 1,
        'outlier_rate': 1 - (len(outliers_iqr) / len(measurements))
    }
    
    quality_score = np.mean(list(quality_factors.values()))
    
    return {
        'original': ts,
        'cleaned': cleaned,
        'smoothed': smoothed,
        'statistics': stats,
        'quality_metrics': {
            'n_missing': n_missing,
            'n_outliers': len(outliers_iqr),
            'drift_variance': drift_variance,
            'measurement_uncertainty': measurement_uncertainty,
            'quality_factors': quality_factors,
            'overall_quality_score': quality_score
        },
        'outlier_indices': outliers_iqr,
        'metadata': metadata
    }

# Example: Analyze sensor calibration data
np.random.seed(42)
n_measurements = 1000
timestamps = pd.date_range('2023-01-01', periods=n_measurements, freq='1min')

# Simulate sensor measurements with drift and noise
true_value = 25.0  # Temperature in Celsius
drift = 0.001 * np.arange(n_measurements)  # Sensor drift
noise = 0.1 * np.random.randn(n_measurements)  # Measurement noise
measurements = true_value + drift + noise

# Add some outliers (sensor glitches)
outlier_indices = np.random.choice(n_measurements, size=20, replace=False)
measurements[outlier_indices] += 2 * np.random.randn(len(outlier_indices))

# Add some missing values
missing_indices = np.random.choice(n_measurements, size=10, replace=False)
measurements[missing_indices] = np.nan

metadata = {
    'experiment_name': 'Temperature Sensor Calibration',
    'sensor_id': 'TEMP_001',
    'true_value': true_value,
    'expected_uncertainty': 0.1
}

analysis_result = analyze_experimental_data(measurements, timestamps, metadata)

print("Experimental Data Analysis:")
print(f"Data quality score: {analysis_result['quality_metrics']['overall_quality_score']:.3f}")
print(f"Missing values: {analysis_result['quality_metrics']['n_missing']}")
print(f"Outliers detected: {analysis_result['quality_metrics']['n_outliers']}")
print(f"Measurement uncertainty: ±{analysis_result['quality_metrics']['measurement_uncertainty']:.4f}")
print(f"Mean value: {analysis_result['statistics']['mean']:.3f}")
```

---

## IoT and Sensor Data

### Multi-Sensor Data Fusion

```python
def fuse_sensor_data(sensor_readings, sensor_weights=None):
    """
    Fuse data from multiple sensors measuring the same quantity.
    
    Args:
        sensor_readings: Dictionary of {sensor_id: (data, times, uncertainty)}
        sensor_weights: Dictionary of sensor weights (default: uncertainty-based)
    
    Returns:
        Fused sensor data with uncertainty estimation
    """
    sensor_ids = list(sensor_readings.keys())
    
    # Align all sensor data to common time grid
    all_times = []
    for sensor_id, (data, times, uncertainty) in sensor_readings.items():
        all_times.extend(times)
    
    # Create common time grid (simplified - use first sensor's times)
    common_times = sensor_readings[sensor_ids[0]][1]
    
    # Interpolate all sensors to common time grid
    aligned_data = {}
    uncertainties = {}
    
    for sensor_id, (data, times, uncertainty) in sensor_readings.items():
        ts = baseTs(data=data, times=times, backend='series', signal_name=sensor_id)
        
        # Simple alignment (in practice, you'd want proper interpolation)
        if len(times) == len(common_times):
            aligned_data[sensor_id] = data
            uncertainties[sensor_id] = uncertainty
        else:
            # Skip sensors with different time grids for this example
            continue
    
    # Calculate weights based on uncertainties (inverse variance weighting)
    if sensor_weights is None:
        weights = {}
        for sensor_id in aligned_data.keys():
            weights[sensor_id] = 1.0 / (uncertainties[sensor_id] ** 2)
        
        # Normalize weights
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}
    else:
        weights = sensor_weights
    
    # Weighted fusion
    fused_data = np.zeros(len(common_times))
    fused_uncertainty = np.zeros(len(common_times))
    
    for i in range(len(common_times)):
        weighted_sum = 0
        weight_sum = 0
        variance_sum = 0
        
        for sensor_id in aligned_data.keys():
            weight = weights[sensor_id]
            value = aligned_data[sensor_id][i]
            uncertainty = uncertainties[sensor_id]
            
            if not np.isnan(value):
                weighted_sum += weight * value
                weight_sum += weight
                variance_sum += (weight ** 2) * (uncertainty ** 2)
        
        if weight_sum > 0:
            fused_data[i] = weighted_sum / weight_sum
            fused_uncertainty[i] = np.sqrt(variance_sum) / weight_sum
        else:
            fused_data[i] = np.nan
            fused_uncertainty[i] = np.inf
    
    # Create fused time series
    fused_ts = baseTs(data=fused_data, times=common_times, backend='series',
                     signal_name="Fused_Sensors")
    
    # Quality metrics
    agreement_metrics = {}
    for sensor_id in aligned_data.keys():
        differences = aligned_data[sensor_id] - fused_data
        rmse = np.sqrt(np.nanmean(differences ** 2))
        agreement_metrics[sensor_id] = {
            'rmse': rmse,
            'bias': np.nanmean(differences),
            'correlation': np.corrcoef(aligned_data[sensor_id], fused_data)[0, 1]
        }
    
    return {
        'fused_data': fused_ts,
        'uncertainty': fused_uncertainty,
        'weights': weights,
        'individual_sensors': {
            sensor_id: baseTs(data=data, times=common_times, backend='series', signal_name=sensor_id)
            for sensor_id, data in aligned_data.items()
        },
        'agreement_metrics': agreement_metrics
    }

# Example: Fuse temperature readings from multiple sensors
np.random.seed(42)
n_points = 100
times = pd.date_range('2023-01-01', periods=n_points, freq='1min')

# True temperature
true_temp = 20 + 5 * np.sin(2 * np.pi * np.arange(n_points) / 50) + np.random.randn(n_points) * 0.1

# Simulate multiple sensors with different characteristics
sensor_readings = {}

# High-precision sensor
sensor_readings['TEMP_HIGH_PREC'] = (
    true_temp + 0.05 * np.random.randn(n_points),  # Low noise
    times,
    0.05  # Low uncertainty
)

# Medium-precision sensor
sensor_readings['TEMP_MEDIUM_PREC'] = (
    true_temp + 0.2 * np.random.randn(n_points),  # Medium noise
    times,
    0.2   # Medium uncertainty
)

# Low-precision sensor with bias
sensor_readings['TEMP_LOW_PREC'] = (
    true_temp + 0.5 + 0.5 * np.random.randn(n_points),  # High noise + bias
    times,
    0.5   # High uncertainty
)

fusion_result = fuse_sensor_data(sensor_readings)

print("Sensor Fusion Results:")
print("Sensor weights:")
for sensor_id, weight in fusion_result['weights'].items():
    print(f"  {sensor_id}: {weight:.3f}")

print("\nAgreement metrics:")
for sensor_id, metrics in fusion_result['agreement_metrics'].items():
    print(f"  {sensor_id}:")
    print(f"    RMSE: {metrics['rmse']:.3f}")
    print(f"    Bias: {metrics['bias']:.3f}")
    print(f"    Correlation: {metrics['correlation']:.3f}")
```

---

## Performance Optimization

### Large Dataset Processing

```python
def process_large_dataset(data_source, chunk_size=100000, operations=None):
    """
    Process large datasets in chunks to manage memory usage.
    
    Args:
        data_source: Function that yields (data, times) chunks
        chunk_size: Size of each processing chunk
        operations: List of operations to apply to each chunk
    
    Returns:
        Processed results
    """
    if operations is None:
        operations = [
            lambda ts: ts.lowpass_filter(cutoff=0.3),
            lambda ts: ts.zscale()
        ]
    
    processed_chunks = []
    chunk_stats = []
    
    for chunk_idx, (data_chunk, times_chunk) in enumerate(data_source(chunk_size)):
        print(f"Processing chunk {chunk_idx + 1}: {len(data_chunk)} points")
        
        # Process chunk
        ts_chunk = baseTs(data=data_chunk, times=times_chunk, backend='numpy')
        
        # Apply operations
        processed_chunk = ts_chunk
        for operation in operations:
            processed_chunk = operation(processed_chunk)
        
        processed_chunks.append(processed_chunk)
        
        # Collect statistics
        stats = {
            'mean': np.mean(processed_chunk.data),
            'std': np.std(processed_chunk.data),
            'min': np.min(processed_chunk.data),
            'max': np.max(processed_chunk.data)
        }
        chunk_stats.append(stats)
    
    # Combine chunks
    combined_data = np.concatenate([chunk.data for chunk in processed_chunks])
    combined_times = np.concatenate([chunk.times for chunk in processed_chunks])
    
    combined_ts = baseTs(data=combined_data, times=combined_times, backend='numpy',
                        signal_name="Large_Dataset_Processed")
    
    # Overall statistics
    overall_stats = {
        'total_points': len(combined_data),
        'n_chunks': len(processed_chunks),
        'chunk_stats': chunk_stats,
        'overall_mean': np.mean(combined_data),
        'overall_std': np.std(combined_data)
    }
    
    return combined_ts, overall_stats

# Example data generator
def large_data_generator(chunk_size):
    """Generate large dataset in chunks."""
    total_size = 1000000  # 1 million points
    n_chunks = total_size // chunk_size
    
    for i in range(n_chunks):
        start_time = i * chunk_size / 1000.0  # 1 kHz sampling
        times = start_time + np.arange(chunk_size) / 1000.0
        
        # Generate synthetic data with different characteristics per chunk
        frequency = 1 + i * 0.1  # Varying frequency
        data = np.sin(2 * np.pi * frequency * times) + 0.1 * np.random.randn(chunk_size)
        
        yield data, times

# Process large dataset
result_ts, stats = process_large_dataset(large_data_generator, chunk_size=50000)

print(f"Processed {stats['total_points']} points in {stats['n_chunks']} chunks")
print(f"Overall mean: {stats['overall_mean']:.6f}")
print(f"Overall std: {stats['overall_std']:.6f}")
```

### Performance Benchmarking

```python
import time
import psutil
import os

def benchmark_operations(data_sizes, operations, backends=['numpy', 'series']):
    """
    Benchmark baseTs operations across different data sizes and backends.
    
    Args:
        data_sizes: List of data sizes to test
        operations: Dictionary of {name: operation_function}
        backends: List of backends to test
    
    Returns:
        Benchmark results
    """
    results = {}
    
    for backend in backends:
        results[backend] = {}
        
        for size in data_sizes:
            print(f"Benchmarking {backend} backend with {size} points...")
            
            # Generate test data
            data = np.random.randn(size)
            times = np.arange(size) / 1000.0  # 1 kHz sampling
            
            if backend == 'series':
                times = pd.date_range('2023-01-01', periods=size, freq='1ms')
            
            results[backend][size] = {}
            
            for op_name, operation in operations.items():
                # Memory before
                process = psutil.Process(os.getpid())
                mem_before = process.memory_info().rss / 1024 / 1024  # MB
                
                # Create baseTs object
                ts = baseTs(data=data, times=times, backend=backend)
                
                # Benchmark operation
                start_time = time.perf_counter()
                try:
                    result = operation(ts)
                    end_time = time.perf_counter()
                    
                    execution_time = end_time - start_time
                    success = True
                except Exception as e:
                    execution_time = float('inf')
                    success = False
                
                # Memory after
                mem_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_used = mem_after - mem_before
                
                results[backend][size][op_name] = {
                    'execution_time': execution_time,
                    'memory_used': memory_used,
                    'success': success
                }
    
    return results

# Define benchmark operations
benchmark_ops = {
    'lowpass_filter': lambda ts: ts.lowpass_filter(cutoff=0.3),
    'zscale': lambda ts: ts.zscale(),
    'normalize_range': lambda ts: ts.normalize_range(),
    'remove_outliers': lambda ts: ts.remove_outliers(),
    'rolling_mean': lambda ts: ts.rolling_mean(window=100) if hasattr(ts, 'rolling_mean') else ts
}

# Run benchmarks
data_sizes = [1000, 10000, 50000]
benchmark_results = benchmark_operations(data_sizes, benchmark_ops)

# Print results
print("\nBenchmark Results:")
print("=" * 60)
for backend in benchmark_results:
    print(f"\n{backend.upper()} Backend:")
    for size in benchmark_results[backend]:
        print(f"  Data size: {size}")
        for op_name in benchmark_results[backend][size]:
            result = benchmark_results[backend][size][op_name]
            if result['success']:
                print(f"    {op_name}: {result['execution_time']:.4f}s, {result['memory_used']:.1f}MB")
            else:
                print(f"    {op_name}: FAILED")
```

---

## Integration Examples

### Pandas Integration

```python
def integrate_with_pandas(ts_data):
    """
    Demonstrate integration between baseTs and pandas workflows.
    
    Args:
        ts_data: baseTs object with Series backend
    
    Returns:
        Analysis results using pandas functionality
    """
    # Ensure we're using Series backend
    if ts_data._backend != 'series':
        print("Converting to Series backend for pandas integration...")
        ts_data = baseTs(data=ts_data.data, 
                        times=pd.to_datetime(ts_data.times), 
                        backend='series')
    
    # Access underlying Series for pandas operations
    series_data = ts_data._data
    
    # Pandas time series operations
    results = {}
    
    # Resampling
    monthly_mean = series_data.resample('M').mean()
    weekly_std = series_data.resample('W').std()
    
    # Groupby operations
    monthly_stats = series_data.groupby(series_data.index.month).agg({
        'mean': 'mean',
        'std': 'std',
        'min': 'min',
        'max': 'max'
    })
    
    # Rolling operations with pandas
    rolling_corr = series_data.rolling(window=30).corr(series_data.shift(1))
    
    # Time-based indexing
    if hasattr(series_data.index, 'year'):
        yearly_data = series_data.groupby(series_data.index.year).mean()
    else:
        yearly_data = None
    
    # Convert results back to baseTs if needed
    results['monthly_mean'] = baseTs(
        data=monthly_mean.values,
        times=monthly_mean.index,
        backend='series',
        signal_name=f"{ts_data.signal_name}_monthly"
    )
    
    results['weekly_std'] = baseTs(
        data=weekly_std.values,
        times=weekly_std.index,
        backend='series',
        signal_name=f"{ts_data.signal_name}_weekly_std"
    )
    
    return {
        'results': results,
        'monthly_stats': monthly_stats,
        'rolling_correlation': rolling_corr,
        'yearly_data': yearly_data
    }

# Example usage
dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
data = np.random.randn(len(dates)) + 0.1 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25)

ts = baseTs(data=data, times=dates, backend='series', signal_name="Daily_Data")
pandas_results = integrate_with_pandas(ts)

print("Pandas Integration Results:")
print(f"Monthly data points: {pandas_results['results']['monthly_mean'].len()}")
print(f"Weekly std data points: {pandas_results['results']['weekly_std'].len()}")
```

### Plotting Integration

```python
def create_comprehensive_plots(ts_data):
    """
    Create comprehensive plots for time series analysis.
    
    Args:
        ts_data: baseTs object
    
    Returns:
        matplotlib figure
    """
    import matplotlib.pyplot as plt
    from matplotlib.dates import DateFormatter
    
    fig, axes = plt.subplots(4, 1, figsize=(12, 16))
    
    # Plot 1: Original time series
    axes[0].plot(ts_data.times, ts_data.data, 'b-', alpha=0.7, linewidth=1)
    axes[0].set_title(f'{ts_data.signal_name} - Original Data')
    axes[0].set_ylabel('Value')
    axes[0].grid(True, alpha=0.3)
    
    # Plot 2: Processed data
    filtered = ts_data.lowpass_filter(cutoff=0.3)
    normalized = filtered.zscale()
    
    axes[1].plot(normalized.times, normalized.data, 'r-', linewidth=1)
    axes[1].set_title('Filtered and Normalized')
    axes[1].set_ylabel('Normalized Value')
    axes[1].grid(True, alpha=0.3)
    
    # Plot 3: Rolling statistics (if Series backend)
    if ts_data._backend == 'series' and hasattr(ts_data, 'rolling_mean'):
        rolling_mean = ts_data.rolling_mean(window=30)
        rolling_std = ts_data.rolling_std(window=30)
        
        axes[2].plot(rolling_mean.times, rolling_mean.data, 'g-', label='30-day Mean', linewidth=2)
        axes[2].fill_between(
            rolling_mean.times,
            rolling_mean.data - rolling_std.data,
            rolling_mean.data + rolling_std.data,
            alpha=0.3, color='green', label='±1 Std Dev'
        )
        axes[2].set_title('Rolling Statistics')
        axes[2].set_ylabel('Value')
        axes[2].legend()
        axes[2].grid(True, alpha=0.3)
    else:
        # For NumPy backend, show distribution
        axes[2].hist(ts_data.data, bins=50, alpha=0.7, color='purple')
        axes[2].set_title('Data Distribution')
        axes[2].set_xlabel('Value')
        axes[2].set_ylabel('Frequency')
        axes[2].grid(True, alpha=0.3)
    
    # Plot 4: Statistics summary
    stats = ts_data.get_statistics() if hasattr(ts_data, 'get_statistics') else {
        'mean': np.mean(ts_data.data),
        'std': np.std(ts_data.data),
        'min': np.min(ts_data.data),
        'max': np.max(ts_data.data)
    }
    
    # Create text summary
    stats_text = f"""
    Statistics Summary:
    Mean: {stats['mean']:.4f}
    Std Dev: {stats['std']:.4f}
    Min: {stats['min']:.4f}
    Max: {stats['max']:.4f}
    Range: {stats['max'] - stats['min']:.4f}
    Points: {ts_data.len()}
    Backend: {ts_data._backend}
    """
    
    axes[3].text(0.1, 0.5, stats_text, transform=axes[3].transAxes, 
                fontsize=12, verticalalignment='center',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
    axes[3].set_title('Summary Statistics')
    axes[3].axis('off')
    
    # Format x-axis for time plots
    for ax in axes[:3]:
        if hasattr(ts_data.times[0], 'strftime'):  # datetime objects
            ax.xaxis.set_major_formatter(DateFormatter('%Y-%m'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    return fig

# Example usage
dates = pd.date_range('2023-01-01', periods=365, freq='D')
data = 10 + 3 * np.sin(2 * np.pi * np.arange(365) / 365) + np.random.randn(365)

ts = baseTs(data=data, times=dates, backend='series', signal_name="Temperature")
fig = create_comprehensive_plots(ts)
plt.show()
```

This comprehensive examples document provides practical, real-world usage patterns for baseTs across various domains and use cases.