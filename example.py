"""
Example usage of the baseTs package.
"""
import numpy as np
import matplotlib.pyplot as plt
from baseTs import baseTs

# Create some synthetic data
n_points = 1000
t = np.linspace(0, 10, n_points)
# Signal with multiple frequency components and noise
signal = (
    np.sin(2 * np.pi * 0.5 * t) +          # 0.5 Hz component
    0.5 * np.sin(2 * np.pi * 1.5 * t) +     # 1.5 Hz component
    0.2 * np.random.randn(n_points)         # Noise
)

# Add some outliers
outlier_indices = np.random.choice(range(n_points), size=20, replace=False)
signal[outlier_indices] += 3 * np.random.randn(len(outlier_indices))

# Create baseTs object
ts = baseTs(signal, t, signal_name="Example Signal")

# Plot the raw signal
plt.figure(figsize=(12, 10))
plt.subplot(4, 1, 1)
ts.plot(show=False)
plt.title("Raw Signal with Outliers")

# Remove outliers using LOWESS
ts_filtered = ts.set_outlier_filter(frac=0.1, z_threshold=3).filter_outliers()

# Plot the filtered signal
plt.subplot(4, 1, 2)
ts_filtered.plot(show=False)
plt.title("Signal with Outliers Removed")

# Apply bandpass filter
ts_bandpass = ts_filtered.bandpass_at(hp_hz=0.4, lp_hz=0.6)

# Plot the bandpass filtered signal
plt.subplot(4, 1, 3)
ts_bandpass.plot(show=False)
plt.title("Bandpass Filtered Signal (0.4-0.6 Hz)")

# Plot FFT power spectrum
plt.subplot(4, 1, 4)
ts_filtered.plot_fft_power(show=False)
plt.title("FFT Power Spectrum")

plt.tight_layout()
plt.show()

# Print information about the timeseries
print("\nTimeseries Information:")
print(f"Number of samples: {ts.len()}")
print(f"Duration: {ts.duration()} seconds")
print(f"Effective sampling rate: {ts.freq} Hz")
print(f"Peak frequency: {ts.get_peak_freq()} Hz")