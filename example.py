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
plt.figure(figsize=(12, 12))
ax = plt.subplot(5, 1, 1)
ts.plot(show=False, ax=ax)
plt.title("Raw Signal with Spikes/Outliers")

# Remove outliers using LOWESS
ts_filtered = ts.set_outlier_filter(frac=0.07, z_threshold=3).filter_outliers()

# Plot the filtered signal
ax = plt.subplot(5, 1, 2)
ts_filtered.plot(show=False, lowess=True, ax=ax)
plt.title("Lowess Filtered to Remove Spikes")
plt.legend(["De-Spiked Signal", "Lowess Fit Line"])
                 
# Apply bandpass filter
ts_bandpass = ts_filtered.bandpass_at(hp_hz=0.2, lp_hz=2)

# Plot the bandpass filtered signal
ax = plt.subplot(5, 1, 3)
ts_bandpass.plot(show=False, ax=ax)
plt.title("Bandpass Filtered Signal (0.2-2 Hz)")

# Plot FFT power spectrum
ax = plt.subplot(5, 1, 4)
ts_filtered.plot_fft_power(show=False, ax=ax)
plt.title("FFT Power Spectrum")

# Plot Zoomed FFT power spectrum
ax = plt.subplot(5, 1, 5)
ts_filtered.plot_fft_power(show=False, max_rate=2, ax=ax)
plt.title("FFT Power Spectrum - Zoomed")

plt.tight_layout()
plt.show()

# Print information about the timeseries
print("\nTimeseries Information:")
print(f"Number of samples: {ts.len()}")
print(f"Duration: {ts.duration()} seconds")
print(f"Effective sampling rate: {ts.freq} Hz")
print(f"Peak frequency: {ts.get_peak_freq()} Hz")