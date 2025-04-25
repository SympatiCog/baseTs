"""
Created on Oct 19 2024
@author: stan@sympaticog.com
"""

from typing import Tuple, List, Union
import numpy as np
import pandas as pd
from scipy.stats import median_abs_deviation
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class lowess_outlier_filter:
    """
    A class to apply LOWESS smoothing and outlier detection on time series data.
    """

    def __init__(
        self,
        z_threshold: float = 7.0,
        max_iterations: int = 5,
        frac: float = 0.05,
        tails: str = 'both',
        interpolation_method: str = 'linear',
        order: int = 2,
        use_median: bool = True,
        num_fits: int = 25,
    ):
        """
        Initialize the LowessOutlierFilter with filtering parameters.

        Parameters
        ----------
        z_threshold : float, optional
            Z-score threshold to identify outliers. Defaults to 7.0.
        max_iterations : int, optional
            Maximum number of iterations for outlier removal. Defaults to 5.
        frac : float, optional
            Fraction of data used when estimating each y-value in LOWESS. Defaults to 0.05.
        tails : str, optional
            Specifies whether to trim 'upper', 'lower', or 'both' tails. Defaults to 'both'.
        interpolation_method : str, optional
            Method to use for interpolation of missing values. Defaults to 'linear'.
        use_median : bool, optional
            Whether to use median/MAD for robust Z-score calculation.
        """
        self.z_threshold = z_threshold
        self.max_iterations = max_iterations
        self.frac = frac
        self.tails = tails
        self.interpolation_method = interpolation_method
        self.use_median = use_median
        self.order = order
        self.num_fits = num_fits
        
    def filter(self,
               data: Union[np.ndarray, List[float], 'baseTs'],
               time_index: Union[np.ndarray, List[float], None] = None,
               return_lowess: bool = True) -> Tuple:
        """
        Apply LOWESS smoothing and outlier detection to the data.

        Parameters
        ----------
        data : array_like, np.ndarray, or baseTs
            The time series data to be filtered.
        time_index : array_like, optional
            The time indices corresponding to the data.
            If None and data is not a baseTs instance, indices are generated automatically.

        Returns
        -------
        cleaned_data : np.ndarray or baseTs
            The cleaned data series.
        outlier_indices : List[int]
            The indices of the values that were identified as outliers and changed.
        """
        # Avoid circular imports by importing here
        from .core import baseTs

        # Validate data and time_index
        data_values = self._validate_data(data)
        time_index = self._validate_time_index(data, data_values, time_index)

        cleaned_data = data_values.copy()
        outlier_indices = []
        previous_outliers = np.zeros(len(cleaned_data), dtype=bool)

        from moepy import lowess

        for iteration in range(self.max_iterations):
            valid_mask = ~np.isnan(cleaned_data)
            if not np.any(valid_mask):
                logger.warning("All data points are NaN. Exiting the loop.")
                break

            # LOWESS smoothing with moepy
            y = cleaned_data[valid_mask]
            x = time_index[valid_mask]
            lowess_model = lowess.Lowess()
            lowess_model.fit(x, y, frac=self.frac, num_fits=self.num_fits)
            lowess_fit = lowess_model.predict(x)

            # Residual calculation
            lowess_line = np.full_like(cleaned_data, np.nan)
            lowess_line[valid_mask] = lowess_fit
            residuals = cleaned_data - lowess_line

            # Robust statistics
            center, scale = self._compute_robust_statistics(residuals)

            # Outlier detection
            outliers = self._identify_outliers(residuals, center, scale)

            new_outliers = outliers & ~previous_outliers
            if not np.any(new_outliers):
                logger.info(f"All outliers removed in iteration {iteration}.")
                break

            cleaned_data[new_outliers] = np.nan
            outlier_indices.extend(np.where(new_outliers)[0].tolist())
            previous_outliers = outliers

            # logger.info(f"Iteration {iteration}: Found {np.sum(new_outliers)} new outliers.")

        # Interpolation
        if np.any(np.isnan(cleaned_data)):
            cleaned_data = self._interpolate_missing_values(cleaned_data, time_index)

        # Interpolation for lowess_line
        if return_lowess and np.any(np.isnan(lowess_line)):
            lowess_line = self._interpolate_missing_values(lowess_line, time_index)

        # Return the same data type as input
        if isinstance(data, baseTs):
            cleaned_data = baseTs(cleaned_data, time_index)

        outlier_indices = sorted(set(outlier_indices))

        if return_lowess:
            return cleaned_data, outlier_indices, lowess_line
        else:
            return cleaned_data, outlier_indices

    def _validate_data(self, data: Union[np.ndarray, List[float], 'baseTs']) -> np.ndarray:
        """
        Validate and convert input data to a NumPy array.
        Return a copy of the data to avoid modifying the original.
        """
        # Import baseTs inside the method to avoid circular import issues
        from .core import baseTs

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
                             time_index: Union[np.ndarray, List[float], None],
                             ) -> np.ndarray:
        """
        Validate and obtain the time index.
        """
        # Import baseTs inside the method to avoid circular import issues
        from .core import baseTs

        if isinstance(data, baseTs):
            return np.asarray(data.times)
        elif time_index is not None:
            time_index = np.asarray(time_index)
            if len(time_index) != len(data_values):
                raise ValueError("Length of time_index must match length of data.")
            return time_index
        else:
            return np.arange(len(data_values))

    def _compute_robust_statistics(self, residuals: np.ndarray) -> Tuple[float, float]:
        """
        Compute the center and scale (median/MAD or mean/std) of the residuals.
        """
        if self.use_median:
            center = np.nanmedian(residuals)
            scale = median_abs_deviation(residuals, nan_policy='omit')
        else:
            center = np.nanmean(residuals)
            scale = np.nanstd(residuals, ddof=1)

        epsilon = 1e-6
        if scale < epsilon:
            scale = epsilon

        return center, scale

    def _identify_outliers(self,
                           residuals: np.ndarray,
                           center: float,
                           scale: float,
                        ) -> np.ndarray:
        """
        Identify outliers based on robust Z-scores.
        """
        z_scores = (residuals - center) / scale

        if self.tails == 'both':
            outliers = np.abs(z_scores) > self.z_threshold
        elif self.tails == 'upper':
            outliers = z_scores > self.z_threshold
        elif self.tails == 'lower':
            outliers = z_scores < -self.z_threshold
        else:
            raise ValueError("Invalid 'tails' parameter: choose from 'upper', 'lower', or 'both'.")

        return outliers

    def _interpolate_missing_values(
        self,
        data: np.ndarray,
        time_index: np.ndarray,
    ) -> np.ndarray:
        """
        Interpolate missing values in the data.
        """
        cleaned_series = pd.Series(data, index=time_index)
        interpolated_series = cleaned_series.interpolate(method=self.interpolation_method, order=self.order)
        if interpolated_series.isnull().any():
            interpolated_series = interpolated_series.ffill() 
            interpolated_series = interpolated_series.bfill()
        return interpolated_series.values