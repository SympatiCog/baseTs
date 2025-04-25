# baseTs

A Python library for time series analysis, focusing on filtering, outlier detection, and data processing.

## Features

- Time series filtering (lowpass, highpass, bandpass, Butterworth, Savitzky-Golay)
- Outlier detection using LOWESS (Locally Weighted Scatterplot Smoothing)
- Interpolation of missing values and resampling to uniform time grids
- FFT power spectrum analysis
- Data normalization and standardization
- Peak detection
- Visualization tools

## Installation

```bash
# Clone the repository
git clone https://github.com/YourUsername/baseTs.git
cd baseTs

# Install dependencies
pip install numpy scipy pandas matplotlib
```

## Usage

```python
import numpy as np
from baseTs import baseTs

# Create sample time series
t = np.linspace(0, 10, 1000)
y = np.sin(2 * np.pi * t) + 0.2 * np.random.randn(len(t))

# Create baseTs object
ts = baseTs(data=y, times=t)

# Apply filtering and processing
filtered_ts = ts.lowpass_filter(cutoff=0.5).remove_outliers()

# Plot the result
filtered_ts.plot()
```

## Documentation

See the [CLAUDE.md](CLAUDE.md) file for development guidelines and code style.

## Requirements

- Python 3.6+
- NumPy
- SciPy
- Pandas
- Matplotlib

## License

MIT
