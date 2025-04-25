# baseTs Package

This directory contains the core modules of the baseTs package.

## Modules

- `core.py`: Main baseTs class definition and core functionality
- `filters.py`: Signal filtering implementations (Butterworth, SG, etc.)
- `lowess_filter.py`: Implementation of LOWESS-based outlier detection
- `plotting.py`: Visualization tools for time series data
- `utils.py`: Helper functions for time series analysis
- `exgaussian.py`: Statistical fitting using ex-Gaussian distributions 

## Usage

```python
from baseTs import baseTs

# Create a time series object
ts = baseTs(data, times, signal_name="My Signal")

# Apply filters and processing
filtered_ts = ts.lowpass_at(10).remove_outliers()

# Plot the results
filtered_ts.plot()
```