"""
Created on Oct 19 2024
@author: stan@sympaticog.com
"""

from __future__ import annotations
from typing import Union, List, Tuple, Optional, TYPE_CHECKING
import numpy as np
import pandas as pd
from scipy.stats import median_abs_deviation
import logging
import warnings
from dataclasses import dataclass
from enum import Enum, auto

if TYPE_CHECKING:
    from .core import baseTs

# sys.path.append('/Users/stan/Projects/cpCST_MoBI/baseTs')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#: Lower bound on the residual scale, guarding against division by zero.
SCALE_FLOOR = 1e-6

#: Smallest local window (``int(frac * n)``) that yields a fit rather than an
#: exact interpolation of the data. Below this, tricube weighting leaves at most
#: one effectively-weighted point per window.
MIN_WINDOW_POINTS = 4


class TailType(Enum):
    """Enum for specifying which tails to process in outlier detection."""
    BOTH = auto()
    UPPER = auto()
    LOWER = auto()

@dataclass(frozen=True)
class FilterConfig:
    """Configuration parameters for the LowessOutlierFilter.

    Attributes
    ----------
    z_threshold : float
        Robust z-score above which a residual is treated as an outlier.
    max_iterations : int
        Maximum passes of the detect-and-mask loop.
    frac : float
        LOWESS bandwidth: the fraction of points included in each local
        regression window. This is *not* the fraction of points expected to be
        outliers.
    it : int
        Robustifying iterations performed *inside* the LOWESS fit. Defaults to 0
        so that robustness lives in one place: this class already runs its own
        MAD-based loop. Raising it makes the fit track the data more closely,
        which shrinks residuals and can collapse the MAD scale to SCALE_FLOOR —
        see _compute_robust_statistics. (A signal smooth enough to be fitted
        near-exactly can collapse the scale at it=0 too; `it` is not the only
        route to it.)
    delta_frac : float
        If > 0, LOWESS fits only at points separated by ``delta_frac * ptp(x)``
        and interpolates between them, trading a little accuracy for speed on
        long series. 0.0 fits every point. Successor to the removed ``num_fits``.
    """
    z_threshold: float = 3.0
    max_iterations: int = 5
    frac: float = 0.075
    tails: TailType = TailType.BOTH
    interpolation_method: str = 'linear'
    order: int = 2
    use_median: bool = True
    it: int = 0
    delta_frac: float = 0.0

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
               data: Union[np.ndarray, List[float], baseTs],
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

        # Validate inputs
        data_values = self._validate_data(data)
        time_index = self._validate_time_index(data, data_values, time_index)
        self._validate_window(data_values)

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

            # Masking outliers shrinks the usable series, and with it the local
            # window. A run that starts just above the minimum can fall below it
            # a single removal later, at which point the fit would interpolate
            # the survivors exactly. Stop instead: the previous iteration's fit
            # is sound, so keep it rather than overwrite it with a degenerate one.
            n_valid = int(np.count_nonzero(valid_mask))
            if int(self.config.frac * n_valid) < MIN_WINDOW_POINTS:
                warnings.warn(
                    f"Stopping after {iteration} iteration(s): removing outliers "
                    f"left {n_valid} usable points, and frac="
                    f"{self.config.frac:g} gives a local window of "
                    f"{int(self.config.frac * n_valid)} there, below the "
                    f"{MIN_WINDOW_POINTS} needed to fit rather than interpolate. "
                    f"The fit from the previous iteration is retained. Raise frac "
                    f"to use the full max_iterations={self.config.max_iterations}.",
                    RuntimeWarning,
                    stacklevel=3,
                )
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

    def _validate_window(self, data_values: np.ndarray) -> None:
        """Reject configurations whose local window is too small to smooth.

        LOWESS fits a weighted line within each window of ``k = int(frac * n)``
        points. Tricube weighting gives the window's edge points zero weight, so
        for ``k <= 3`` the line is determined by at most one effectively-weighted
        point and passes exactly through the data. The "fit" is then the input,
        every residual is zero, the MAD scale collapses to SCALE_FLOOR and
        z_threshold stops discriminating — a silently useless result.

        The threshold is on ``k``, not on ``frac``: ``frac=0.001`` is fine on a
        long series and degenerate on a short one, so neither bound alone catches
        this. Measured to be independent of n; k >= 4 is the first well-behaved
        window at every length tested.
        """
        n = int(np.count_nonzero(~np.isnan(data_values)))
        k = int(self.config.frac * n)
        if k >= MIN_WINDOW_POINTS:
            return

        if n < MIN_WINDOW_POINTS:
            raise ValueError(
                f"LOWESS needs at least {MIN_WINDOW_POINTS} usable points to fit "
                f"anything but the data itself; got {n}. No frac can rescue a "
                f"series this short."
            )
        needed = MIN_WINDOW_POINTS / n
        raise ValueError(
            f"frac={self.config.frac:g} on {n} points gives a local window of "
            f"{k} point(s); LOWESS needs at least {MIN_WINDOW_POINTS} or it "
            f"interpolates the data exactly, leaving every residual zero and "
            f"z_threshold inoperative. Use frac >= {needed:.4g} for this series."
        )

    def _apply_lowess(self, y: np.ndarray, x: np.ndarray) -> np.ndarray:
        """Apply LOWESS smoothing to the data.

        Uses statsmodels' Cleveland LOWESS. Note the argument order:
        ``lowess(endog, exog)`` is ``(y, x)``.

        ``return_sorted=False`` is load-bearing. statsmodels defaults to
        ``missing='drop'``; with ``return_sorted=False`` it re-inserts NaN at the
        dropped positions so the output length always matches the input, which
        the caller relies on when assigning into ``lowess_line[valid_mask]``.
        """
        from statsmodels.nonparametric.smoothers_lowess import lowess

        delta = self.config.delta_frac * float(np.ptp(x)) if self.config.delta_frac else 0.0
        return lowess(
            y, x,
            frac=self.config.frac,
            it=self.config.it,
            delta=delta,
            return_sorted=False,
        )

    def _process_iteration(self,
                          data: np.ndarray,
                          lowess_line: np.ndarray,
                          previous_outliers: np.ndarray) -> np.ndarray:
        """Process a single iteration of outlier detection."""
        residuals = data - lowess_line
        center, scale = self._compute_robust_statistics(residuals)
        outliers = self._identify_outliers(residuals, center, scale)
        return outliers & ~previous_outliers

    def _validate_data(self, data: Union[np.ndarray, List[float], baseTs]) -> np.ndarray:
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
                           data: Union[np.ndarray, List[float], baseTs],
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

        if scale < SCALE_FLOOR:
            # The spread of residuals has collapsed, so every z-score is divided by
            # the floor and z_threshold stops discriminating. Usually means the fit
            # is interpolating the data (e.g. a staircase signal fitted with
            # internal robustifying iterations, config.it >= 2).
            #
            # warnings.warn rather than logger.warning: this says the caller's
            # result is meaningless, which must reach them under default config.
            # Logging only surfaces if the application configured handlers.
            warnings.warn(
                f"Residual scale {scale:.3g} is below the {SCALE_FLOOR:.0e} floor; "
                f"z-scores are being divided by the floor and z_threshold is "
                f"effectively inoperative. Check that the LOWESS fit is not "
                f"interpolating the data (config.it={self.config.it}, "
                f"config.frac={self.config.frac:g}).",
                RuntimeWarning,
                stacklevel=4,
            )

        return center, max(scale, SCALE_FLOOR)  # Prevent division by zero

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
