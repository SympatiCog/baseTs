"""
Integration tests for baseTs processing pipeline.
"""
import pytest
import numpy as np
import pandas as pd
from baseTs import baseTs


def test_complete_processing_pipeline(data_with_outliers):
    """Test a complete processing pipeline with multiple steps."""
    # Create a baseTs object with outliers
    ts = baseTs(
        data=data_with_outliers['data'],
        times=data_with_outliers['times'],
        signal_name="PipelineTest"
    )
    
    # Store initial stats for comparison
    initial_std = ts.data.std()
    
    # 1. Remove outliers
    ts_cleaned = ts.set_outlier_filter(frac=0.07, z_threshold=3.0).filter_outliers()
    
    # Verify outliers were removed
    assert ts_cleaned.is_outlier_filtered is True
    assert ts_cleaned.data.std() < initial_std
    
    # 2. Apply bandpass filter to isolate frequency of interest
    ts_filtered = ts_cleaned.bandpass_at(hp_hz=0.3, lp_hz=0.7)
    
    # Verify filtering worked
    assert ts_filtered.is_filtered is True
    
    # 3. Interpolate to uniform grid
    ts_uniform = ts_filtered.interp_to_uniform_grid()
    
    # Verify interpolation worked
    assert ts_uniform.is_uniform_grid is True
    assert ts_uniform.is_interpolated is True
    
    # 4. Z-scale the data
    ts_scaled = ts_uniform.zscale()
    
    # Verify z-scaling worked
    assert np.isclose(ts_scaled.data.mean(), 0, atol=1e-10)
    assert np.isclose(ts_scaled.data.std(), 1, atol=1e-10)
    
    # 5. Test history tracking
    assert len(ts_scaled.history) > 1
    
    # Calculate peak frequency and verify it's close to our expected 0.5 Hz
    peak_freq = ts_scaled.get_peak_freq()
    assert np.isclose(peak_freq, 0.5, atol=0.1)


def test_method_chaining(data_with_outliers):
    """Test method chaining for creating a processing pipeline."""
    # Create a baseTs object with outliers
    ts = baseTs(
        data=data_with_outliers['data'],
        times=data_with_outliers['times'],
        signal_name="ChainingTest"
    )
    
    # Apply a complete pipeline with method chaining
    result = ts.set_outlier_filter(frac=0.07, z_threshold=3.0) \
               .filter_outliers() \
               .bandpass_at(hp_hz=0.3, lp_hz=0.7) \
               .interp_to_uniform_grid() \
               .zscale()
    
    # Verify the complete pipeline worked
    assert result.is_outlier_filtered is True
    assert result.is_filtered is True
    assert result.is_uniform_grid is True
    assert result.is_interpolated is True
    assert np.isclose(result.data.mean(), 0, atol=1e-10)
    assert np.isclose(result.data.std(), 1, atol=1e-10)
    
    # Verify history is tracked
    assert len(result.history) > 1


def test_dataframe_conversions():
    """Test conversions between baseTs and pandas DataFrame."""
    # Create a simple signal
    n_points = 1000
    t = np.linspace(0, 10, n_points)
    signal = np.sin(2 * np.pi * 0.5 * t)
    
    # Create a baseTs object
    ts = baseTs(signal, t, signal_name="DataFrameTest")
    
    # Convert to DataFrame
    df = ts.to_dataframe()
    
    # Verify DataFrame columns
    assert 'times' in df.columns
    assert 'data' in df.columns
#    assert 'timestamps' in df.columns
    
    # Check data integrity
    assert np.array_equal(df['times'].values, t)
    assert np.array_equal(df['data'].values, signal)
    
    # Test with timestamp offset. The offset is the origin the seconds are
    # counted from (#100); declaring it does not move the times.
    ts.set_timestamp_offset(1000.0)
    df_with_offset = ts.to_dataframe()

    assert np.array_equal(df_with_offset['times'].values, t)
    assert ts.ts_offset == 1000.0
    assert ts.datetimes[0] == pd.Timestamp('1970-01-01 00:16:40')
    
    # Test DataFrame with index
    df_indexed = ts.to_dataframe(set_index=True)
    assert df_indexed.index.name == 'times'


def test_from_df_to_pipeline():
    """Test creating baseTs from DataFrame and applying pipeline."""
    import pandas as pd
    # Create a test DataFrame
    n_points = 1000
    t = np.linspace(0, 10, n_points)
    signal = np.sin(2 * np.pi * 0.5 * t) + 0.2 * np.random.randn(n_points)
    
    df = pd.DataFrame({
        'time': t,
        'value': signal
    })
    
    # Create baseTs from DataFrame
    from baseTs.core import from_df
    ts = from_df(df)
    
    # Verify correct creation
    assert ts.len() == n_points
    assert ts.signal_name == "VALUE"
    
    # Apply a simple processing pipeline
    result = ts.sg_filter(window_length=11, polyorder=2) \
              .zscale()
    
    # Verify pipeline worked
    assert result.is_filtered is True
    assert np.isclose(result.data.mean(), 0, atol=1e-10)
    assert np.isclose(result.data.std(), 1, atol=1e-10)
