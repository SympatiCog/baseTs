"""
Created on Oct 19 2024
@author: stan@sympaticog.com
"""

from typing import Tuple, List, Union, Optional
import numpy as np
import pandas as pd
from scipy.stats import median_abs_deviation
import sys
import logging
from dataclasses import dataclass
from enum import Enum, auto

# sys.path.append('/Users/stan/Projects/cpCST_MoBI/baseTs')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TailType(Enum):
    """Enum for specifying which tails to process in outlier detection."""
    BOTH = auto()
    UPPER = auto()
    LOWER = auto()

@dataclass
class FilterConfig:
    """Configuration parameters for the LowessOutlierFilter."""
    z_threshold: float = 7.0
    max_iterations: int = 5
    frac: float = 0.075
    tails: TailType = TailType.BOTH
    interpolation_method: str = 'linear'
    order: int = 2
    use_median: bool = True
    num_fits: int = 25

class LowessOutlierFilter:
    """
    A class to apply LOWESS smoothing and outlier detection on time series data.
    
    This class implements a robust outlier detection method using LOWESS smoothing
    and robust statistics. It can handle both numpy arrays and baseTs objects.
    """

    def __init__(self, config: Optional[FilterConfig] = None):
        """
        Initialize the LowessOutlierFilter with filtering parameters.

        Parameters
        ----------
        config : FilterConfig, optional
            Configuration object containing filter parameters. If None, uses default values.
        """
        self.config = config or FilterConfig()
        
    def filter(self,
               data: Union[np.ndarray, List[float], 'baseTs'],
               time_index: Optional[Union[np.ndarray, List[float]]] = None,
               return_lowess: bool = True) -> Tuple:
        """
        Apply LOWESS smoothing and outlier detection to the data.

        Parameters
        ----------
        data : Union[np.ndarray, List[float], baseTs]
            The time series data to be filtered.
        time_index : Optional[Union[np.ndarray, List[float]]]
            The time indices corresponding to the data.
            If None and data is not a baseTs instance, indices are generated automatically.
        return_lowess : bool, default=True
            Whether to return the LOWESS fit line along with the filtered data.

        Returns
        -------
        Tuple
            If return_lowess is True:
                (cleaned_data, outlier_indices, lowess_line)
            Otherwise:
                (cleaned_data, outlier_indices)
        """
        from baseTs import baseTs
        from moepy import lowess

        # Validate inputs
        data_values = self._validate_data(data)
        time_index = self._validate_time_index(data, data_values, time_index)

        # Initialize tracking variables
        cleaned_data = data_values.copy()
        outlier_indices = []
        previous_outliers = np.zeros(len(cleaned_data), dtype=bool)
        lowess_line = np.full_like(cleaned_data, np.nan)

        # Main filtering loop
        for iteration in range(self.config.max_iterations):
            valid_mask = ~np.isnan(cleaned_data)
            if not np.any(valid_mask):
                logger.warning("All data points are NaN. Exiting the loop.")
                break

            # Apply LOWESS smoothing
            lowess_fit = self._apply_lowess(
                cleaned_data[valid_mask],
                time_index[valid_mask]
            )
            lowess_line[valid_mask] = lowess_fit

            # Detect and handle outliers
            new_outliers = self._process_iteration(
                cleaned_data,
                lowess_line,
                previous_outliers
            )
            
            if not np.any(new_outliers):
                logger.info(f"All outliers removed in iteration {iteration}.")
                break

            cleaned_data[new_outliers] = np.nan
            outlier_indices.extend(np.where(new_outliers)[0].tolist())
            previous_outliers = new_outliers

        # Post-processing
        cleaned_data = self._interpolate_missing_values(cleaned_data, time_index)
        if return_lowess and np.any(np.isnan(lowess_line)):
            lowess_line = self._interpolate_missing_values(lowess_line, time_index)

        # Convert back to original type if needed
        if isinstance(data, baseTs):
            cleaned_data = baseTs(cleaned_data, time_index)

        outlier_indices = sorted(set(outlier_indices))

        return (cleaned_data, outlier_indices, lowess_line) if return_lowess else (cleaned_data, outlier_indices)

    def _apply_lowess(self, y: np.ndarray, x: np.ndarray) -> np.ndarray:
        """Apply LOWESS smoothing to the data."""
        from moepy import lowess
        lowess_model = lowess.Lowess()
        lowess_model.fit(x, y, frac=self.config.frac, num_fits=self.config.num_fits)
        return lowess_model.predict(x)

    def _process_iteration(self,
                          data: np.ndarray,
                          lowess_line: np.ndarray,
                          previous_outliers: np.ndarray) -> np.ndarray:
        """Process a single iteration of outlier detection."""
        residuals = data - lowess_line
        center, scale = self._compute_robust_statistics(residuals)
        outliers = self._identify_outliers(residuals, center, scale)
        return outliers & ~previous_outliers

    def _validate_data(self, data: Union[np.ndarray, List[float], 'baseTs']) -> np.ndarray:
        """Validate and convert input data to a NumPy array."""
        from baseTs import baseTs

        if isinstance(data, baseTs):
            data_values = np.asarray(data.data, dtype=float).copy()
        else:
            data_values = np.asarray(data, dtype=float).copy()

        if not np.issubdtype(data_values.dtype, np.number):
            raise ValueError("All elements in 'data' must be numeric.")

        return data_values

    def _validate_time_index(self,
                           data: Union[np.ndarray, List[float], 'baseTs'],
                           data_values: np.ndarray,
                           time_index: Optional[Union[np.ndarray, List[float]]],
                           ) -> np.ndarray:
        """Validate and obtain the time index."""
        from baseTs import baseTs

        if isinstance(data, baseTs):
            return np.asarray(data.times)
        elif time_index is not None:
            time_index = np.asarray(time_index)
            if len(time_index) != len(data_values):
                raise ValueError("Length of time_index must match length of data.")
            return time_index
        return np.arange(len(data_values))

    def _compute_robust_statistics(self, residuals: np.ndarray) -> Tuple[float, float]:
        """Compute the center and scale of the residuals."""
        if self.config.use_median:
            center = np.nanmedian(residuals)
            scale = median_abs_deviation(residuals, nan_policy='omit')
        else:
            center = np.nanmean(residuals)
            scale = np.nanstd(residuals, ddof=1)

        return center, max(scale, 1e-6)  # Prevent division by zero

    def _identify_outliers(self,
                          residuals: np.ndarray,
                          center: float,
                          scale: float) -> np.ndarray:
        """Identify outliers based on robust Z-scores."""
        z_scores = (residuals - center) / scale

        if self.config.tails == TailType.BOTH:
            return np.abs(z_scores) > self.config.z_threshold
        elif self.config.tails == TailType.UPPER:
            return z_scores > self.config.z_threshold
        elif self.config.tails == TailType.LOWER:
            return z_scores < -self.config.z_threshold
        raise ValueError("Invalid 'tails' parameter")

    def _interpolate_missing_values(self,
                                  data: np.ndarray,
                                  time_index: np.ndarray) -> np.ndarray:
        """Interpolate missing values in the data."""
        cleaned_series = pd.Series(data, index=time_index)
        interpolated_series = cleaned_series.interpolate(
            method=self.config.interpolation_method,
            order=self.config.order
        )
        
        # Handle any remaining NaN values
        if interpolated_series.isnull().any():
            interpolated_series = interpolated_series.ffill().bfill()
            
        return interpolated_series.values
