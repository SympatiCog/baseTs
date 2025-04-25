import numpy as np
from scipy.stats import exponnorm, chi2, kstest
from scipy.optimize import minimize


def get_exg_fits(data:np.array, res:dict)->dict:
    """
    Get the fits for the ex-Gaussian distribution and perform statistical tests.
    """
    K = res["K"]
    loc = res["loc"]
    scale = res["scale"]
    ks_stat, ks_pval = kstest(data, 'exponnorm', args=(K, loc, scale))
    chi_stat, chi_pval = chi_square_test(data, K, loc, scale, bins=30)
    aic_value = calculate_aic(data, K, loc, scale)
    bic_value = calculate_bic(data, K, loc, scale)
    res_dict = {"ks_stat":ks_stat, "ks_pval":ks_pval, "chi_stat":chi_stat, "chi_pval":chi_pval,
             "aic_value":aic_value, "bic_value":bic_value}
    return(res_dict)

def exg_initial_guess(rt):
    """
    Compute an initial guess for the parameters of the ex-Gaussian distribution.
    """
    rt = np.array(rt)  # Ensure rt is a NumPy array
    mean_rt = np.mean(rt)
    median_rt = np.median(rt)
    variance_rt = np.var(rt, ddof=1)
    tau_guess = max(1e-6, mean_rt - median_rt)
    sigma_squared_guess = variance_rt - tau_guess ** 2
    sigma_guess = np.sqrt(max(1e-6, sigma_squared_guess))
    mu_guess = mean_rt - tau_guess
    K_guess = tau_guess / sigma_guess if sigma_guess > 0 else 1e6  # Avoid division by zero
    
    return [K_guess, mu_guess, sigma_guess]

# def negative_log_likelihood(params, data):
#     """
#     Compute the negative log-likelihood of the data given the parameters K, loc, and scale.
#     """
#     K, loc, scale = params
#     if scale <= 0 or K <= 0:
#         return np.inf
#     return -np.sum(exponnorm.logpdf(data, K, loc=loc, scale=scale))
def negative_log_likelihood(params, data):
    """
    Compute the negative log-likelihood of the data given the parameters K, loc, and scale.
    """
    K, loc, scale = params
    # Add parameter validation with meaningful error messages
    if scale <= 0:
        return np.inf, "Scale parameter must be positive"
    if K <= 0:
        return np.inf, "K parameter must be positive"
    try:
        return -np.sum(exponnorm.logpdf(data, K, loc=loc, scale=scale))
    except Exception as e:
        return np.inf, f"Error in likelihood calculation: {str(e)}"
    
# def iterative_exgaussian_fit(data, initial_params=None, tol=1e-7, max_iter=100):
#     """
#     Iteratively fit the data to the ex-Gaussian distribution using the negative log-likelihood function.
#     """
#     if initial_params is None:
#         # Set default with educated guesses
#         K, loc, scale = exg_initial_guess(data)
#         initial_params = [K, loc, scale]
    
#     prev_params = np.array(initial_params)
#     for i in range(max_iter):
#         # Fit the model
#         result = minimize(
#             negative_log_likelihood,
#             x0=prev_params,
#             args=(data,),
#             bounds=[(1e-5, None), (None, None), (1e-5, None)],
#             method='L-BFGS-B'
#         )
#         current_params = result.x
#         # Check for convergence
#         if np.all(np.abs(current_params - prev_params) < tol):
#             print(f"Converged after {i} iterations.")
#             break
#         prev_params = current_params
#     else:
#         print("Maximum iterations reached without convergence.")
    
#     K_hat, loc_hat, scale_hat = current_params
#     lambda_hat = 1 / (K_hat * scale_hat)
#     return {
#         'K': K_hat,
#         'loc': loc_hat,
#         'scale': scale_hat,
#         'lambda': lambda_hat,
#         'num_iters': i,
#     }
def iterative_exgaussian_fit(data, initial_params=None, tol=1e-7, max_iter=100):
    """
    Iteratively fit the data to the ex-Gaussian distribution.
    """
    # Add input validation
    data = np.asarray(data)
    if data.size == 0:
        raise ValueError("Empty data array provided")
    
    if initial_params is None:
        initial_params = exg_initial_guess(data)
    
    # Add bounds with more reasonable limits
    bounds = [
        (1e-5, 100),    # K: shape parameter
        (None, None),   # loc: location parameter
        (1e-5, np.std(data) * 10)  # scale: reasonable upper bound based on data
    ]
    
    result = minimize(
        negative_log_likelihood,
        x0=initial_params,
        args=(data,),
        bounds=bounds,
        method='L-BFGS-B'
    )
    
    if not result.success:
        print(f"Warning: Optimization failed: {result.message}")
    
    K_hat, loc_hat, scale_hat = result.x
    return {
        'K': K_hat,
        'loc': loc_hat,
        'scale': scale_hat,
        'lambda': 1 / (K_hat * scale_hat),
        'success': result.success,
        'message': result.message,
        'nll': result.fun  # Add negative log-likelihood to output
    }
 
def chi_square_test(data, K, loc, scale, bins=10):
    """
    Perform a chi-square test for the fit of the data to the ex-Gaussian
    given the parameters K, loc, and scale.
    """
    # Histogram of observed
    observed_counts, bin_edges = np.histogram(data, bins=bins)
    # Expected 
    cdf_vals = exponnorm.cdf(bin_edges, K, loc=loc, scale=scale)
    expected_counts = np.diff(cdf_vals) * len(data)
    
    # Ensure no expected counts are zero
    expected_counts = np.where(expected_counts == 0, 1e-6, expected_counts)
    
    # Compute Chi-square
    chi_square_stat = np.sum((observed_counts - expected_counts) ** 2 / expected_counts)
    
    # Degrees of freedom: number of bins - number of estimated parameters - 1
    dof = bins - 3 - 1  # 3 parameters estimated for ex-Gaussian
    
    # P-value
    p_value = chi2.sf(chi_square_stat, dof)
    
    res = {"chi_square_stat":chi_square_stat, "chi_square_pval":p_value}

    return(res)

def calculate_aic(data, K, loc, scale):
    """
    Calculate the Akaike Information Criterion (AIC) for the fit of the data to the ex-Gaussian distribution.
    """
    # Log-likelihood
    log_likelihood = np.sum(exponnorm.logpdf(data, K, loc=loc, scale=scale))
    
    # Number of estimated parameters
    k = 3  # K, loc, scale
    
    # AIC
    aic = 2 * k - 2 * log_likelihood
    
    print(f"AIC: {aic:.2f}")
    return aic

def calculate_bic(data, K, loc, scale):
    """
    Calculate the Bayesian Information Criterion (BIC) for the fit of the data to the ex-Gaussian distribution.
    """
    # Log-likelihood
    log_likelihood = np.sum(exponnorm.logpdf(data, K, loc=loc, scale=scale))
    
    # Number of estimated parameters
    k = 3  # K, loc, scale
    
    # Number of observations
    n = len(data)
    
    # BIC
    bic = k * np.log(n) - 2 * log_likelihood
    
    print(f"BIC: {bic:.2f}")
    return bic
