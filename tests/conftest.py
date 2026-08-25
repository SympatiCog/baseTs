"""
Pytest configuration and fixtures.
"""
import pytest
import numpy as np
import pandas as pd
import sys
import os

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from baseTs import baseTs

@pytest.fixture
def sample_data():
    """Generate a simple sine wave dataset for testing."""
    n_points = 1000
    t = np.linspace(0, 10, n_points)
    # Signal with multiple frequency components
    signal = (
        np.sin(2 * np.pi * 0.5 * t) +       # 0.5 Hz component
        0.5 * np.sin(2 * np.pi * 1.5 * t)   # 1.5 Hz component
    )
    return {'data': signal, 'times': t}


@pytest.fixture
def noisy_data():
    """Generate a sine wave with noise for testing."""
    n_points = 1000
    t = np.linspace(0, 10, n_points)
    # Signal with multiple frequency components and noise
    signal = (
        np.sin(2 * np.pi * 0.5 * t) +           # 0.5 Hz component
        0.5 * np.sin(2 * np.pi * 1.5 * t) +     # 1.5 Hz component
        0.2 * np.random.randn(n_points)         # Noise
    )
    signal += 1 # Add a constant offset to the signal
    return {'data': signal, 'times': t}


@pytest.fixture
def data_with_outliers():
    """Generate a dataset with outliers for testing outlier detection."""
    np.random.seed(42)  # For reproducibility
    n_points = 1000
    t = np.linspace(0, 10, n_points)
    # Signal with multiple frequency components and noise
    signal = (
        np.sin(2 * np.pi * 0.5 * t) +          # 0.5 Hz component
        0.5 * np.sin(2 * np.pi * 1.5 * t) +     # 1.5 Hz component
        0.2 * np.random.randn(n_points)         # Noise
    )
    
    # Add outliers
    outlier_indices = np.random.choice(range(n_points), size=20, replace=False)
    signal[outlier_indices] += 3 * np.random.randn(len(outlier_indices))
    
    return {'data': signal, 'times': t, 'outlier_indices': outlier_indices}


@pytest.fixture
def simple_baseTsObj(sample_data):
    """Create a simple baseTs object for testing."""
    return baseTs(
        data=sample_data['data'],
        times=sample_data['times'],
        signal_name="TestSignal"
    )


@pytest.fixture
def noisy_baseTsObj(noisy_data):
    """Create a noisy baseTs object for testing."""
    return baseTs(
        data=noisy_data['data'],
        times=noisy_data['times'],
        signal_name="NoisyTestSignal"
    )


@pytest.fixture
def outlier_baseTsObj(data_with_outliers):
    """Create a baseTs object with outliers for testing."""
    return baseTs(
        data=data_with_outliers['data'],
        times=data_with_outliers['times'],
        signal_name="OutlierTestSignal"
    )


@pytest.fixture
def sample_dataframe():
    """Create a sample pandas DataFrame for testing."""
    n_points = 1000
    t = np.linspace(0, 10, n_points)
    signal = np.sin(2 * np.pi * 0.5 * t)
    
    df = pd.DataFrame({
        'time': t,
        'value': signal
    })
    
    return df

@pytest.fixture
def spiked():
    """Sine with two large, unambiguous spikes.

    Returns (data, times) rather than a dict, matching the signature this
    fixture had while it was local to tests/unit/test_lowess_backend.py.
    """
    t = np.linspace(0, 10, 500)
    d = np.sin(2 * np.pi * 0.5 * t) + 0.05 * np.random.default_rng(0).standard_normal(500)
    d[150] += 5.0
    d[350] -= 5.0
    return d, t
