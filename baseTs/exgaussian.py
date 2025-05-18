# -*- coding: utf-8 -*-
"""
Ex-Gaussian distribution fitting and analysis utilities.
Created on Oct 19 2024
@author: stan@sympaticog.com
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from numpy.typing import NDArray
from scipy.stats import exponnorm, chi2, kstest
from scipy.optimize import minimize

@dataclass
class ExGaussianFit:
    """Data class for storing ex-Gaussian fit results."""
    K: float
    loc: float
    scale: float
    lambda_: float  # Using lambda_ to avoid Python keyword conflict
    success: bool
    message: str
    nll: float  # Negative log-likelihood

@dataclass
class FitStatistics:
    """Data class for storing fit statistics."""
    ks_stat: float
    ks_pval: float
    chi_stat: float
    chi_pval: float
    aic_value: float
    bic_value: float

def get_exg_fits(data: NDArray[np.float64], res: Dict[str, float]) -> FitStatistics:
    """
    Get the fits for the ex-Gaussian distribution and perform statistical tests.

    Args:
        data: Input data array
        res: Dictionary containing fit parameters (K, loc, scale)

    Returns:
        FitStatistics object containing statistical test results
    """
    K = res["K"]
    loc = res["loc"]
    scale = res["scale"]
    
    # Perform Kolmogorov-Smirnov test
    ks_stat, ks_pval = kstest(data, 'exponnorm', args=(K, loc, scale))
    
    # Perform Chi-square test
    chi_stat, chi_pval = chi_square_test(data, K, loc, scale, bins=30)
    
    # Calculate information criteria
    aic_value = calculate_aic(data, K, loc, scale)
    bic_value = calculate_bic(data, K, loc, scale)
    
    return FitStatistics(
        ks_stat=ks_stat,
        ks_pval=ks_pval,
        chi_stat=chi_stat,
        chi_pval=chi_pval,
        aic_value=aic_value,
        bic_value=bic_value
    )

def exg_initial_guess(rt: NDArray[np.float64]) -> List[float]:
    """
    Compute an initial guess for the parameters of the ex-Gaussian distribution.

    Args:
        rt: Response time data array

    Returns:
        List of initial parameter guesses [K, mu, sigma]
    """
    rt = np.asarray(rt, dtype=np.float64)
    mean_rt = np.mean(rt)
    median_rt = np.median(rt)
    variance_rt = np.var(rt, ddof=1)
    
    # Calculate initial parameters with safeguards
    tau_guess = max(1e-6, mean_rt - median_rt)
    sigma_squared_guess = max(1e-6, variance_rt - tau_guess ** 2)
    sigma_guess = np.sqrt(sigma_squared_guess)
    mu_guess = mean_rt - tau_guess
    K_guess = tau_guess / sigma_guess if sigma_guess > 0 else 1e6
    
    return [K_guess, mu_guess, sigma_guess]

def negative_log_likelihood(params: List[float], data: NDArray[np.float64]) -> Tuple[float, Optional[str]]:
    """
    Compute the negative log-likelihood of the data given the parameters.

    Args:
        params: List of parameters [K, loc, scale]
        data: Input data array

    Returns:
        Tuple of (negative log-likelihood, error message if any)
    """
    K, loc, scale = params
    
    # Parameter validation
    if scale <= 0:
        return np.inf, "Scale parameter must be positive"
    if K <= 0:
        return np.inf, "K parameter must be positive"
    
    try:
        return -np.sum(exponnorm.logpdf(data, K, loc=loc, scale=scale)), None
    except Exception as e:
        return np.inf, f"Error in likelihood calculation: {str(e)}"

def iterative_exgaussian_fit(
    data: NDArray[np.float64],
    initial_params: Optional[List[float]] = None,
    tol: float = 1e-7,
    max_iter: int = 100
) -> ExGaussianFit:
    """
    Iteratively fit the data to the ex-Gaussian distribution.

    Args:
        data: Input data array
        initial_params: Optional initial parameter guesses
        tol: Optimization tolerance
        max_iter: Maximum number of iterations

    Returns:
        ExGaussianFit object containing fit results

    Raises:
        ValueError: If input data is empty
    """
    # Input validation
    data = np.asarray(data, dtype=np.float64)
    if data.size == 0:
        raise ValueError("Empty data array provided")
    
    if initial_params is None:
        initial_params = exg_initial_guess(data)
    
    # Define parameter bounds
    bounds = [
        (1e-5, 100),    # K: shape parameter
        (None, None),   # loc: location parameter
        (1e-5, np.std(data) * 10)  # scale: reasonable upper bound based on data
    ]
    
    # Perform optimization
    result = minimize(
        negative_log_likelihood,
        x0=initial_params,
        args=(data,),
        bounds=bounds,
        method='L-BFGS-B',
        tol=tol,
        options={'maxiter': max_iter}
    )
    
    if not result.success:
        print(f"Warning: Optimization failed: {result.message}")
    
    K_hat, loc_hat, scale_hat = result.x
    return ExGaussianFit(
        K=K_hat,
        loc=loc_hat,
        scale=scale_hat,
        lambda_=1 / (K_hat * scale_hat),
        success=result.success,
        message=result.message,
        nll=result.fun
    )

def chi_square_test(
    data: NDArray[np.float64],
    K: float,
    loc: float,
    scale: float,
    bins: int = 10
) -> Tuple[float, float]:
    """
    Perform a chi-square test for the fit of the data to the ex-Gaussian.

    Args:
        data: Input data array
        K: Shape parameter
        loc: Location parameter
        scale: Scale parameter
        bins: Number of histogram bins

    Returns:
        Tuple of (chi-square statistic, p-value)
    """
    # Calculate observed and expected counts
    observed_counts, bin_edges = np.histogram(data, bins=bins)
    cdf_vals = exponnorm.cdf(bin_edges, K, loc=loc, scale=scale)
    expected_counts = np.diff(cdf_vals) * len(data)
    
    # Ensure no expected counts are zero
    expected_counts = np.where(expected_counts == 0, 1e-6, expected_counts)
    
    # Compute Chi-square statistic
    chi_square_stat = np.sum((observed_counts - expected_counts) ** 2 / expected_counts)
    
    # Calculate degrees of freedom and p-value
    dof = bins - 3 - 1  # 3 parameters estimated for ex-Gaussian
    p_value = chi2.sf(chi_square_stat, dof)
    
    return chi_square_stat, p_value

def calculate_aic(data: NDArray[np.float64], K: float, loc: float, scale: float) -> float:
    """
    Calculate the Akaike Information Criterion (AIC) for the fit.

    Args:
        data: Input data array
        K: Shape parameter
        loc: Location parameter
        scale: Scale parameter

    Returns:
        AIC value
    """
    log_likelihood = np.sum(exponnorm.logpdf(data, K, loc=loc, scale=scale))
    k = 3  # Number of estimated parameters
    aic = 2 * k - 2 * log_likelihood
    return aic

def calculate_bic(data: NDArray[np.float64], K: float, loc: float, scale: float) -> float:
    """
    Calculate the Bayesian Information Criterion (BIC) for the fit.

    Args:
        data: Input data array
        K: Shape parameter
        loc: Location parameter
        scale: Scale parameter

    Returns:
        BIC value
    """
    log_likelihood = np.sum(exponnorm.logpdf(data, K, loc=loc, scale=scale))
    k = 3  # Number of estimated parameters
    n = len(data)  # Number of observations
    bic = k * np.log(n) - 2 * log_likelihood
    return bic