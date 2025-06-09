import numpy as np
import scipy.signal as signal
from scipy.stats import median_abs_deviation
from sklearn.linear_model import LinearRegression
from joblib import Parallel, delayed
import warnings
from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, List
import matplotlib.pyplot as plt

@dataclass
class LowessConfig:
    """Configuration parameters for adaptive LOWESS filtering."""
    min_segment_length: int = 100
    max_segment_length: int = 2000
    base_overlap_ratio: float = 0.5
    min_lowess_frac: float = 0.01
    max_lowess_frac: float = 0.3
    base_lowess_frac: float = 0.1
    n_jobs: int = -1
    robust_iterations: int = 2
    freq_adaptation_factor: float = 2.0
    complexity_threshold: float = 0.1
    
@dataclass 
class SignalCharacteristics:
    """Container for analyzed signal characteristics."""
    sampling_rate: float
    dominant_freqs: np.ndarray
    bandwidth: float
    noise_level: float
    complexity_score: float
    recommended_segment_length: int
    recommended_overlap: float
    recommended_frac: float
    spectral_entropy: float = field(default=0.0)

class AdaptiveLowessFilter:
    """
    Adaptive piecewise LOWESS filter optimized for physiological timeseries.
    
    Automatically determines optimal segmentation and LOWESS parameters based on
    signal frequency content, noise characteristics, and complexity.
    """
    
    def __init__(self, config: Optional[LowessConfig] = None):
        self.config = config or LowessConfig()
        self.signal_chars = None
        
    def analyze_signal_characteristics(self, data: np.ndarray, 
                                    sampling_rate: float) -> SignalCharacteristics:
        """
        Analyze signal to determine optimal adaptive parameters.
        
        Parameters:
        -----------
        data : np.ndarray
            Input timeseries data
        sampling_rate : float
            Sampling rate in Hz
            
        Returns:
        --------
        SignalCharacteristics
            Container with analyzed signal properties and recommended parameters
        """
        # Spectral analysis
        freqs, psd = signal.welch(data, fs=sampling_rate, nperseg=min(len(data)//4, 1024))
        
        # Find dominant frequencies (above noise floor)
        noise_floor = np.percentile(psd, 25)
        significant_mask = psd > 3 * noise_floor
        dominant_freqs = freqs[significant_mask]
        
        # Calculate bandwidth and complexity
        if len(dominant_freqs) > 0:
            bandwidth = dominant_freqs.max() - dominant_freqs.min()
            # Weight by power for frequency centroid
            freq_centroid = np.average(freqs, weights=psd)
        else:
            bandwidth = 0
            freq_centroid = 0
            
        # Estimate noise level using robust statistics
        noise_level = median_abs_deviation(np.diff(data), scale='normal')
        
        # Calculate spectral entropy as complexity measure
        psd_norm = psd / np.sum(psd)
        spectral_entropy = -np.sum(psd_norm * np.log2(psd_norm + 1e-10))
        
        # Signal complexity score based on derivative statistics
        derivatives = np.diff(data)
        complexity_score = np.std(derivatives) / (np.abs(np.mean(data)) + 1e-10)
        
        # Determine adaptive parameters
        segment_length = self._calculate_segment_length(freq_centroid, sampling_rate, len(data))
        overlap_ratio = self._calculate_overlap_ratio(complexity_score, spectral_entropy)
        lowess_frac = self._calculate_lowess_fraction(bandwidth, sampling_rate, noise_level)
        
        return SignalCharacteristics(
            sampling_rate=sampling_rate,
            dominant_freqs=dominant_freqs,
            bandwidth=bandwidth,
            noise_level=noise_level,
            complexity_score=complexity_score,
            recommended_segment_length=segment_length,
            recommended_overlap=overlap_ratio,
            recommended_frac=lowess_frac,
            spectral_entropy=spectral_entropy
        )
    
    def _calculate_segment_length(self, freq_centroid: float, 
                                sampling_rate: float, data_length: int) -> int:
        """Calculate optimal segment length based on dominant frequency content."""
        if freq_centroid > 0:
            # Aim for 3-5 cycles of dominant frequency per segment
            cycles_per_segment = 4
            samples_per_cycle = sampling_rate / freq_centroid
            target_length = int(cycles_per_segment * samples_per_cycle)
        else:
            # Fallback for DC or very low frequency signals
            target_length = min(data_length // 4, 1000)
            
        # Constrain to reasonable bounds
        segment_length = np.clip(target_length, 
                               self.config.min_segment_length, 
                               min(self.config.max_segment_length, data_length // 3))
        
        return segment_length
    
    def _calculate_overlap_ratio(self, complexity_score: float, 
                               spectral_entropy: float) -> float:
        """Calculate overlap ratio based on signal complexity."""
        # Higher complexity signals need more overlap for continuity
        base_overlap = self.config.base_overlap_ratio
        
        # Increase overlap for complex signals
        complexity_factor = min(complexity_score / self.config.complexity_threshold, 2.0)
        entropy_factor = spectral_entropy / 10.0  # Normalize typical entropy range
        
        adaptive_overlap = base_overlap + 0.2 * (complexity_factor + entropy_factor)
        
        return np.clip(adaptive_overlap, 0.3, 0.8)
    
    def _calculate_lowess_fraction(self, bandwidth: float, sampling_rate: float, 
                                 noise_level: float) -> float:
        """Calculate LOWESS fraction based on frequency content and noise."""
        base_frac = self.config.base_lowess_frac
        
        # Adjust based on bandwidth relative to Nyquist
        nyquist = sampling_rate / 2
        bandwidth_ratio = bandwidth / nyquist if nyquist > 0 else 0
        
        # Higher bandwidth signals need smaller fractions to preserve detail
        bandwidth_adjustment = -0.05 * bandwidth_ratio
        
        # Higher noise signals need larger fractions for more smoothing
        noise_adjustment = 0.02 * min(noise_level, 5.0)
        
        adaptive_frac = base_frac + bandwidth_adjustment + noise_adjustment
        
        return np.clip(adaptive_frac, self.config.min_lowess_frac, self.config.max_lowess_frac)
    
    def _create_segments(self, data_length: int, segment_length: int, 
                        overlap_ratio: float) -> List[Tuple[int, int]]:
        """Create overlapping segment indices."""
        step_size = int(segment_length * (1 - overlap_ratio))
        segments = []
        
        start = 0
        while start < data_length:
            end = min(start + segment_length, data_length)
            segments.append((start, end))
            
            if end == data_length:
                break
            start += step_size
            
        return segments
    
    def _lowess_segment(self, data: np.ndarray, frac: float, 
                       robust_iterations: int) -> np.ndarray:
        """Apply LOWESS to a single segment."""
        try:
            from statsmodels.nonparametric.smoothers_lowess import lowess
            
            x = np.arange(len(data))
            smoothed = lowess(data, x, frac=frac, it=robust_iterations, 
                            return_sorted=False)
            return smoothed
            
        except ImportError:
            # Fallback to simple moving average if statsmodels not available
            warnings.warn("statsmodels not available, using moving average fallback")
            window_size = max(int(len(data) * frac), 3)
            return signal.savgol_filter(data, window_size, 2)
    
    def _blend_segments(self, segments_data: List[np.ndarray], 
                       segments_indices: List[Tuple[int, int]], 
                       total_length: int, overlap_ratio: float) -> np.ndarray:
        """Blend overlapping segments using weighted averaging."""
        result = np.zeros(total_length)
        weights = np.zeros(total_length)
        
        for segment_data, (start, end) in zip(segments_data, segments_indices):
            segment_length = end - start
            
            # Create blending weights (higher in center, lower at edges)
            if len(segments_data) > 1:  # Only blend if multiple segments
                edge_fade = int(segment_length * overlap_ratio * 0.5)
                segment_weights = np.ones(segment_length)
                
                # Fade in at start
                if start > 0:
                    fade_length = min(edge_fade, segment_length // 3)
                    segment_weights[:fade_length] = np.linspace(0.1, 1.0, fade_length)
                
                # Fade out at end  
                if end < total_length:
                    fade_length = min(edge_fade, segment_length // 3)
                    segment_weights[-fade_length:] = np.linspace(1.0, 0.1, fade_length)
            else:
                segment_weights = np.ones(segment_length)
            
            result[start:end] += segment_data * segment_weights
            weights[start:end] += segment_weights
        
        # Normalize by weights
        weights[weights == 0] = 1  # Avoid division by zero
        return result / weights
    
    def filter(self, data: np.ndarray, sampling_rate: float, 
              force_params: Optional[Dict] = None) -> Tuple[np.ndarray, SignalCharacteristics]:
        """
        Apply adaptive piecewise LOWESS filtering.
        
        Parameters:
        -----------
        data : np.ndarray
            Input timeseries data
        sampling_rate : float
            Sampling rate in Hz
        force_params : dict, optional
            Override adaptive parameters with manual values
            
        Returns:
        --------
        Tuple[np.ndarray, SignalCharacteristics]
            Filtered data and signal characteristics
        """
        # Analyze signal characteristics
        self.signal_chars = self.analyze_signal_characteristics(data, sampling_rate)
        
        # Override with manual parameters if provided
        if force_params:
            for param, value in force_params.items():
                if hasattr(self.signal_chars, param):
                    setattr(self.signal_chars, param, value)
        
        # Create segments
        segments = self._create_segments(
            len(data), 
            self.signal_chars.recommended_segment_length,
            self.signal_chars.recommended_overlap
        )
        
        # Process segments in parallel
        segment_results = Parallel(n_jobs=self.config.n_jobs)(
            delayed(self._lowess_segment)(
                data[start:end], 
                self.signal_chars.recommended_frac,
                self.config.robust_iterations
            ) for start, end in segments
        )
        
        # Blend segments
        filtered_data = self._blend_segments(
            segment_results, segments, len(data), 
            self.signal_chars.recommended_overlap
        )
        
        return filtered_data, self.signal_chars
    
    def plot_analysis(self, data: np.ndarray, filtered_data: np.ndarray, 
                     sampling_rate: float, figsize: Tuple[int, int] = (12, 8)):
        """Plot original vs filtered data with analysis summary."""
        if self.signal_chars is None:
            raise ValueError("Must run filter() before plotting analysis")
            
        fig, axes = plt.subplots(3, 1, figsize=figsize)
        
        time = np.arange(len(data)) / sampling_rate
        
        # Time domain comparison
        axes[0].plot(time, data, alpha=0.7, label='Original', color='gray')
        axes[0].plot(time, filtered_data, label='Filtered', color='blue', linewidth=2)
        axes[0].set_xlabel('Time (s)')
        axes[0].set_ylabel('Amplitude')
        axes[0].set_title('Adaptive LOWESS Filtering Results')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Frequency domain analysis
        freqs_orig, psd_orig = signal.welch(data, fs=sampling_rate)
        freqs_filt, psd_filt = signal.welch(filtered_data, fs=sampling_rate)
        
        axes[1].semilogy(freqs_orig, psd_orig, alpha=0.7, label='Original', color='gray')
        axes[1].semilogy(freqs_filt, psd_filt, label='Filtered', color='blue')
        axes[1].set_xlabel('Frequency (Hz)')
        axes[1].set_ylabel('PSD')
        axes[1].set_title('Power Spectral Density')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        # Parameter summary
        axes[2].axis('off')
        summary_text = f"""
        Adaptive Parameters:
        • Segment Length: {self.signal_chars.recommended_segment_length} samples
        • Overlap Ratio: {self.signal_chars.recommended_overlap:.2f}
        • LOWESS Fraction: {self.signal_chars.recommended_frac:.3f}
        • Dominant Freq Range: {self.signal_chars.dominant_freqs.min():.1f} - {self.signal_chars.dominant_freqs.max():.1f} Hz
        • Bandwidth: {self.signal_chars.bandwidth:.1f} Hz
        • Noise Level: {self.signal_chars.noise_level:.3f}
        • Complexity Score: {self.signal_chars.complexity_score:.3f}
        • Spectral Entropy: {self.signal_chars.spectral_entropy:.2f}
        """
        axes[2].text(0.1, 0.5, summary_text, fontsize=10, family='monospace',
                    verticalalignment='center')
        
        plt.tight_layout()
        plt.show()

# Example usage and testing function
def demo_adaptive_lowess():
    """Demonstrate the adaptive LOWESS filter with synthetic physiological data."""
    
    # Create synthetic ECG-like signal with noise and artifacts
    fs = 250  # Hz
    t = np.linspace(0, 10, fs * 10)
    
    # Base ECG-like signal (mix of frequencies)
    ecg_signal = (np.sin(2 * np.pi * 1.2 * t) +  # Heart rate ~72 bpm
                  0.3 * np.sin(2 * np.pi * 15 * t) +  # Higher frequency component
                  0.1 * np.sin(2 * np.pi * 50 * t))   # Muscle artifact frequency
    
    # Add noise and artifacts
    noise = 0.1 * np.random.randn(len(t))
    artifacts = np.zeros_like(t)
    
    # Add some spike artifacts
    artifact_indices = np.random.choice(len(t), size=20, replace=False)
    artifacts[artifact_indices] = np.random.randn(20) * 2
    
    data = ecg_signal + noise + artifacts
    
    # Apply adaptive filtering
    filter_obj = AdaptiveLowessFilter()
    filtered_data, characteristics = filter_obj.filter(data, fs)
    
    # Plot results
    filter_obj.plot_analysis(data, filtered_data, fs)
    
    return data, filtered_data, characteristics

if __name__ == "__main__":
    # Run demonstration
    original, filtered, chars = demo_adaptive_lowess()