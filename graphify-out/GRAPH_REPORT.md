# Graph Report - baseTs  (2026-08-25)

## Corpus Check
- 34 files · ~60,223 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 663 nodes · 1175 edges · 60 communities (47 shown, 13 thin omitted)
- Extraction: 97% EXTRACTED · 2% INFERRED · 1% AMBIGUOUS · INFERRED: 23 edges (avg confidence: 0.69)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6357dc49`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- TestRelativeBandPower
- TestBaseTsTransformations
- LowessOutlierFilter
- requirements.txt
- AdaptiveLowessFilter
- filters.py
- baseTs User Guide
- TestBaseTsInitialization
- test_utils.py
- TestRealWorldWorkflows
- utils.py
- exgaussian.py
- core.py
- baseTs
- TestPandasEnhancedMethods
- ._update_history_and_process
- TestMathematicalOperations
- TimeSeriesData
- ._wrap_result_as_basets
- TestFilteringOperations
- baseTs API Documentation
- .data
- .shift_time
- test_enhanced_methods.py
- BandPowerResult
- compute_fft_power
- .get_statistics
- from_df
- fixture
- find_closest_time
- .__init__
- TestPandasIntegration
- Bandpass Filter Pipeline (bp_2: 0.2Hz)
- baseTs Example Signal Processing Figure
- Example 1 Signal Processing Plot
- .info
- get_peak_freq
- get_peaks
- .len
- TestBaseTsFiltering
- lf_baseTsObj
- test_pipeline.py
- test_core.py
- ._update_history_and_process
- baseTs Development Guide
- .lowpass_at
- ._constructor_sliced
- .__truediv__
- .__pow__
- .__radd__
- .__rsub__
- .__rmul__
- Exception
- float64
- fixture

## God Nodes (most connected - your core abstractions)
1. `baseTs` - 162 edges
2. `TimeSeriesData` - 32 edges
3. `baseTs API Documentation` - 32 edges
4. `baseTs User Guide` - 30 edges
5. `baseTs README` - 22 edges
6. `baseTs Examples and Recipes` - 20 edges
7. `Enhanced Pandas Series API Documentation` - 19 edges
8. `baseTs Migration Guide (Pandas Series Foundation)` - 17 edges
9. `relative_band_power()` - 16 edges
10. `AdaptiveLowessFilter` - 13 edges

## Surprising Connections (you probably didn't know these)
- `highpass_filter(cutoff, order=4) (documented instance method)` --conceptually_related_to--> `highpass_filter()`  [AMBIGUOUS]
  docs/API.md → baseTs/filters.py
- `bandpass_filter(low_cutoff, high_cutoff, order=4) (documented instance method)` --conceptually_related_to--> `bandpass_filter()`  [AMBIGUOUS]
  docs/API.md → baseTs/filters.py
- `Design Principle: API Stability` --rationale_for--> `baseTs`  [EXTRACTED]
  CLAUDE.md → baseTs/core.py
- `Design Principle: Metadata Preservation` --rationale_for--> `baseTs`  [EXTRACTED]
  CLAUDE.md → baseTs/core.py
- `notch_filter(freq, quality=30) (documented instance method)` --conceptually_related_to--> `notch_filter()`  [AMBIGUOUS]
  docs/API.md → baseTs/filters.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **baseTs Documentation Suite** — readme_doc, docs_user_guide_doc, docs_api_doc, docs_api_series_doc, docs_examples_doc, docs_changelog_doc, claude_devguide [EXTRACTED 1.00]
- **baseTs Signal Processing Pipeline Demonstration** — imgs_basets_example_figure, imgs_basets_example_raw_signal_with_spikes, imgs_basets_example_lowess_despiking, imgs_basets_example_bandpass_filter, imgs_basets_example_fft_power_spectrum [EXTRACTED 1.00]
- **LOWESS Despiking Workflow** — basets_core_basets_set_outlier_filter, basets_core_basets_filter_outliers, lowess_outlier_detection, basets_lowessoutlierfilter [EXTRACTED 1.00]
- **Enhanced Pandas Series Methods (v2.0.0 Migration)** — basets_core_basets_resample, basets_core_basets_interpolate_gaps, basets_core_basets_align_with, basets_core_basets_correlation_with, basets_core_basets_detect_outliers, basets_core_basets_rolling_mean, basets_core_basets_time_slice, basets_core_basets_get_statistics, basets_core_basets_get_frequency_content, basets_core_basets_shift_time [EXTRACTED 1.00]
- **baseTs Signal Processing Pipeline (despike -> lowpass filter -> rolling mean smoothing)** — imgs_example1_plot_raw_signal, imgs_example1_plot_despiked, imgs_example1_plot_filtered, imgs_example1_plot_smoothed [INFERRED 0.85]

## Communities (60 total, 13 thin omitted)

### Community 0 - "TestRelativeBandPower"
Cohesion: 0.14
Nodes (11): Tests for the relative_band_power / falff methods., Slow 0.05 Hz signal long enough to resolve the 0.01-0.1 Hz band., Method delegates correctly and returns a builtin float., The headline robustness property: an undetrended mean offset must not move the…, The documented pipeline produces the same answer., falff() defaults to the amplitude convention., details=True carries the white-noise null alongside the ratio., The window argument reaches get_frequency_content. (+3 more)

### Community 1 - "TestBaseTsTransformations"
Cohesion: 0.17
Nodes (7): Test detrending functionality., Test trimming functionality., Tests for baseTs data transformations., Test interpolation to specified number of samples., Test interpolation to specified frequency., Test data normalization functions., TestBaseTsTransformations

### Community 2 - "LowessOutlierFilter"
Cohesion: 0.14
Nodes (14): FilterConfig, LowessOutlierFilter, ndarray, Apply LOWESS smoothing to the data., Process a single iteration of outlier detection., Validate and convert input data to a NumPy array., Validate and obtain the time index., Compute the center and scale of the residuals. (+6 more)

### Community 3 - "requirements.txt"
Cohesion: 0.09
Nodes (27): Python Package CI Workflow, hypothesis, Matplotlib, moepy, NumPy, Pandas, psutil, pytest (+19 more)

### Community 4 - "AdaptiveLowessFilter"
Cohesion: 0.11
Nodes (18): AdaptiveLowessFilter, demo_adaptive_lowess(), LowessConfig, ndarray, Calculate optimal segment length based on dominant frequency content., Configuration parameters for adaptive LOWESS filtering., Calculate overlap ratio based on signal complexity., Calculate LOWESS fraction based on frequency content and noise. (+10 more)

### Community 5 - "filters.py"
Cohesion: 0.10
Nodes (28): ArrayLike, Apply a notch filter at the specified frequency. Args: cutoff_hz: Notch…, Apply a Butterworth pass filter to the signal at specified low-pass and high-…, bandpass_filter(), FilterConfig, FilterError, highpass_filter(), interpolate_missing_values() (+20 more)

### Community 6 - "baseTs User Guide"
Cohesion: 0.18
Nodes (18): Apply a rolling mean to the data. Args: window: Size of the rolling window…, Resample time series to a different frequency using pandas resampling. Args:…, Interpolate missing values (NaN) in the time series. Args: method:…, Align two time series on a common time index. Args: other: Another baseTs…, Calculate correlation with another time series. Args: other: Another baseTs…, Detect outliers using statistical methods. Args: method: Detection method…, Get frequency domain representation using pandas-optimized FFT. Args: window:…, Compute the peak frequency(ies) of the timeseries using enhanced frequency… (+10 more)

### Community 7 - "TestBaseTsInitialization"
Cohesion: 0.20
Nodes (6): Tests for baseTs initialization and basic properties., Test initializing baseTs with data and times., Test initializing baseTs with data and frequency., Test initialization validation requirements., Test length and duration calculations., TestBaseTsInitialization

### Community 8 - "test_utils.py"
Cohesion: 0.12
Nodes (23): falff(), Compute the relative power (or amplitude) in a frequency band. This is the…, Fractional amplitude of low-frequency fluctuations (fALFF). Convenience wrapper…, relative_band_power(), Unit tests for baseTs utility functions., A dominant 0.05 Hz component should put most power in the 0.01-0.1 band., Adding a constant offset must not change the result. get_frequency_content()…, For white noise both conventions converge on the bin fraction. That makes… (+15 more)

### Community 9 - "TestRealWorldWorkflows"
Cohesion: 0.08
Nodes (15): Integration tests for real-world time series workflows. Tests complete end-to-…, Test batch processing multiple time series., Test realistic time series analysis workflows., Test data consistency across operations., Test complete signal processing workflow., Test workflow with larger datasets., Test scientific analysis workflow., Test compatibility across different workflow scenarios. (+7 more)

### Community 10 - "utils.py"
Cohesion: 0.13
Nodes (21): Any, add_constant(), dediff(), diff(), get_lags(), idx_to_time(), Add a constant to a time series., Dediff a time series. (+13 more)

### Community 11 - "exgaussian.py"
Cohesion: 0.19
Nodes (20): calculate_aic(), calculate_bic(), chi_square_test(), exg_initial_guess(), ExGaussianFit, FitStatistics, get_exg_fits(), iterative_exgaussian_fit() (+12 more)

### Community 12 - "core.py"
Cohesion: 0.07
Nodes (35): Axes, Plot the timeseries as a line plot. Quick and dirty visualization., # TODO: Deprecate in future versions., # TODO: Replace with generic plot() function that maps, Plot this timeseries against one or more other timeseries. e.g. for QC,…, Plot a histogram of the timeseries., Plot a lag plot of the timeseries., baseTs - A Python library for time series analysis (+27 more)

### Community 13 - "baseTs"
Cohesion: 0.08
Nodes (17): baseTs, Compute the FFT power of the timeseries., Get the peaks in the timeseries. Returns a list of the indices of the peaks., Set or updates the timestamp offset., Helper method to update object flags., Enhanced processing method that handles both data and time modifications. Args:…, Z-scale the data (zero mean, unit variance). Args: inplace: If True, modifies…, Normalize the data to a specified range. Args: target_min: Minimum value of… (+9 more)

### Community 14 - "TestPandasEnhancedMethods"
Cohesion: 0.11
Nodes (10): Test new pandas-enhanced methods., Test pandas-powered rolling mean., Test rolling standard deviation., Test time-based slicing., Test pandas resampling., Test cross-correlation between time series., Test outlier detection., Test gap interpolation. (+2 more)

### Community 15 - "._update_history_and_process"
Cohesion: 0.09
Nodes (13): Compute the first difference of the timeseries., Apply a rolling standard deviation to the data., Apply a rolling median to the data., Apply a rolling maximum to the data., Apply a rolling minimum to the data., Slice the time series between start and end times. Args: start_time: Start time…, Detrend the data using a lowess fit., Helper method to update history and last_process. (+5 more)

### Community 16 - "TestMathematicalOperations"
Cohesion: 0.12
Nodes (9): Test absolute value operations., Test method chaining works correctly., Test that arithmetic operations return baseTs objects., Test mathematical operations with pandas Series foundation., Test z-scaling operations., Test range normalization operations., Test centering operations., Test scaling operations. (+1 more)

### Community 17 - "TimeSeriesData"
Cohesion: 0.14
Nodes (8): Return constructor for pandas operations., Create a copy of the TimeSeriesData object with metadata preservation. Args:…, Pandas Series subclass optimized for time series analysis. This class extends…, Get the length of the time series (backward compatibility). Returns: Number of…, Helper method to update object flags., Convert back to a legacy baseTs object for compatibility. Returns: baseTs…, String representation of TimeSeriesData., TimeSeriesData

### Community 18 - "._wrap_result_as_basets"
Cohesion: 0.17
Nodes (6): Addition operation returning a baseTs object., Subtraction operation returning a baseTs object., Multiplication operation returning a baseTs object., Right division operation returning a baseTs object., Right power operation returning a baseTs object., Wrap arithmetic operation results as baseTs objects. Args: result: Result from…

### Community 19 - "TestFilteringOperations"
Cohesion: 0.14
Nodes (8): Test filtering operations., Test lowpass filtering., Test highpass filtering., Test bandpass filtering., Test Savitzky-Golay filtering., Test Gaussian filtering., Test chaining multiple filters., TestFilteringOperations

### Community 20 - "baseTs API Documentation"
Cohesion: 0.12
Nodes (11): Compute the cumulative sum of the timeseries., Plot the power spectrum of the timeseries using enhanced frequency analysis.…, Create a copy of the baseTs object. Args: deep: Whether to make a deep copy…, Applies a user-provided function to the data vector. Note: the times vector is…, Remove trend from the signal using various detrending methods. Args: method:…, Apply a highpass filter at the specified cutoff frequency. Args: cutoff:…, Apply a bandpass filter to the signal at specified low-pass and high-pass…, bandpass_filter(low_cutoff, high_cutoff, order=4) (documented instance method) (+3 more)

### Community 21 - ".data"
Cohesion: 0.29
Nodes (5): Get the data values as numpy array (backward compatibility)., Set the data values (backward compatibility)., Get the time values as numpy array (backward compatibility)., Set the time values (backward compatibility)., setter

### Community 22 - ".shift_time"
Cohesion: 0.18
Nodes (7): array, ndarray, Initialize baseTs object as pandas Series with time-series metadata., Shift the time series by a number of periods. Args: periods: Number of periods…, Update Series data while preserving metadata and handling length changes., Set specific indices to NaN and interpolate the missing values. Args: indices:…, Interpolate data to a uniform sampling grid. If new_grid is not specified, use…

### Community 23 - "test_enhanced_methods.py"
Cohesion: 0.18
Nodes (6): Test edge cases and error handling., Test handling of empty data., Test handling of single data point., Test handling of constant data., Test invalid parameter handling., TestEdgeCases

### Community 24 - "BandPowerResult"
Cohesion: 0.24
Nodes (10): Compute the relative power (or amplitude) in a frequency band. This is the…, Fractional amplitude of low-frequency fluctuations (fALFF). Convenience wrapper…, BandPowerResult, Detailed breakdown of a relative band power computation. Attributes: ratio: The…, baseTs Changelog, Unreleased: Relative Band Power / fALFF, baseTs 1.0.0 Release (NumPy backend), Keep a Changelog (+2 more)

### Community 25 - "compute_fft_power"
Cohesion: 0.24
Nodes (10): compute_fft_power(), find_closest(), NDArray, Compute the power spectrum of a time series using FFT. Args: ts: Time series…, Find the closest value in a list/array to a target value. Args: val: Target…, float64, Test find_closest function., Test compute_fft_power function. (+2 more)

### Community 26 - ".get_statistics"
Cohesion: 0.22
Nodes (5): Get comprehensive statistics for the time series. Returns: Dictionary…, Display information about the data, times, outlier filter parameters, and…, Calculates the duration of the times. Returns: float: Duration of the times, Get outlier filter parameters. returns a dictionary of the parameters., outlier_indices() (documented, method='iqr'/'zscore'/'modified_zscore')

### Community 27 - "from_df"
Cohesion: 0.22
Nodes (7): from_df(), Convert the timeseries to a pandas DataFrame. Args: set_index (bool): If True,…, Create a baseTs object from a pandas DataFrame. Args: df: Input DataFrame…, DataFrame, Test creating baseTs from DataFrame and applying pipeline., test_from_df_to_pipeline(), Test creating baseTs from DataFrame.

### Community 28 - "fixture"
Cohesion: 0.22
Nodes (5): fixture, Generate a noisy signal for filtering tests., Generate diverse test data., Generate time series data for enhanced method testing., Create sample time series.

### Community 29 - "find_closest_time"
Cohesion: 0.29
Nodes (7): Find the closest time in the timeseries to a target time in seconds. Args: sec:…, ClosestMatch, find_closest_time(), Find the closest time in a time series to a target time. Args: ts: Time series…, Data class for storing closest match results., Test find_closest_time function., test_find_closest_time()

### Community 30 - ".__init__"
Cohesion: 0.25
Nodes (4): Calculate effective sampling frequency from time index., Initialize TimeSeriesData object. Args: data: Array-like data or baseTs object…, Initialize default metadata values., Copy metadata from a baseTs object.

### Community 31 - "TestPandasIntegration"
Cohesion: 0.25
Nodes (5): Test direct pandas integration features., Test direct access to pandas methods., Test pandas-style indexing., Test that metadata is preserved through pandas operations., TestPandasIntegration

### Community 32 - "Bandpass Filter Pipeline (bp_2: 0.2Hz)"
Cohesion: 0.80
Nodes (5): Bandpass Filter Pipeline (bp_2: 0.2Hz), Multi-Stage Filter Chaining / Method Pipelining, baseTs Pipelined Filter Output, Filtered Signal by Time Plot, Power Spectrum of Filtered Signal Plot

### Community 33 - "baseTs Example Signal Processing Figure"
Cohesion: 0.70
Nodes (5): Bandpass Filtered Signal (0.2-2 Hz), FFT Power Spectrum Analysis, baseTs Example Signal Processing Figure, Lowess Filtering to Remove Spikes (Despiking), Raw Signal with Spikes/Outliers

### Community 34 - "Example 1 Signal Processing Plot"
Cohesion: 0.80
Nodes (5): Example 1 Signal Processing Plot, Despiked Panel (LAB SIGNAL_outfilt), Filtered Panel (LAB SIGNAL_lp_6Hz), Raw Signal Panel (LAB SIGNAL_outfilt_params), Smoothed Panel (LAB SIGNAL_rolling_mean_30)

### Community 36 - "get_peak_freq"
Cohesion: 0.50
Nodes (4): get_peak_freq(), Get the top peak frequencies of the time series using enhanced frequency…, Test get_peak_freq function., test_get_peak_freq()

### Community 37 - "get_peaks"
Cohesion: 0.50
Nodes (4): get_peaks(), Find peaks in the time series. Args: ts: Time series object with data attribute…, Test get_peaks function., test_get_peaks()

### Community 39 - "TestBaseTsFiltering"
Cohesion: 0.22
Nodes (5): Tests for baseTs filtering functionality., Test highpass filter., Test bandpass filter., Test Savitzky-Golay filter., TestBaseTsFiltering

### Community 40 - "lf_baseTsObj"
Cohesion: 0.67
Nodes (3): fixture, lf_baseTsObj(), Long, slowly-varying signal suitable for 0.01-0.1 Hz band analysis. 600 s at 2…

### Community 41 - "test_pipeline.py"
Cohesion: 0.25
Nodes (7): Integration tests for baseTs processing pipeline., Test a complete processing pipeline with multiple steps., Test method chaining for creating a processing pipeline., Test conversions between baseTs and pandas DataFrame., test_complete_processing_pipeline(), test_dataframe_conversions(), test_method_chaining()

### Community 42 - "test_core.py"
Cohesion: 0.25
Nodes (5): Unit tests for baseTs core functionality., Tests for outlier detection functionality., Test setting outlier filter parameters., Test outlier filtering., TestOutlierDetection

### Community 44 - "baseTs Development Guide"
Cohesion: 0.33
Nodes (7): baseTs Development Guide, Direct Pandas Series Inheritance Architecture, Dual Backend Architecture (removed in v2.0.0), Design Principle: API Stability, Design Principle: Metadata Preservation, Design Principle: Performance, Design Principle: Series-First

## Ambiguous Edges - Review These
- `.notch_at()` → `notch_filter(freq, quality=30) (documented instance method)`  [AMBIGUOUS]
  docs/API.md · relation: conceptually_related_to
- `.highpass_at()` → `highpass_filter(cutoff, order=4) (documented instance method)`  [AMBIGUOUS]
  docs/API.md · relation: conceptually_related_to
- `.bandpass_at()` → `bandpass_filter(low_cutoff, high_cutoff, order=4) (documented instance method)`  [AMBIGUOUS]
  docs/API.md · relation: conceptually_related_to
- `.get_outlier_filter_params()` → `outlier_indices() (documented, method='iqr'/'zscore'/'modified_zscore')`  [AMBIGUOUS]
  docs/API.md · relation: conceptually_related_to
- `.filter_outliers()` → `remove_outliers() (documented, method='iqr'/'zscore'/'modified_zscore')`  [AMBIGUOUS]
  docs/API.md · relation: conceptually_related_to
- `.detect_outliers()` → `outlier_indices() (documented, method='iqr'/'zscore'/'modified_zscore')`  [AMBIGUOUS]
  docs/API.md · relation: conceptually_related_to
- `LowessOutlierFilter.py` → `baseTs Package README`  [AMBIGUOUS]
  baseTs/README.md · relation: conceptually_related_to
- `notch_filter()` → `notch_filter(freq, quality=30) (documented instance method)`  [AMBIGUOUS]
  docs/API.md · relation: conceptually_related_to
- `highpass_filter()` → `highpass_filter(cutoff, order=4) (documented instance method)`  [AMBIGUOUS]
  docs/API.md · relation: conceptually_related_to
- `bandpass_filter()` → `bandpass_filter(low_cutoff, high_cutoff, order=4) (documented instance method)`  [AMBIGUOUS]
  docs/API.md · relation: conceptually_related_to

## Knowledge Gaps
- **11 isolated node(s):** `baseTs 1.0.0 Release (NumPy backend)`, `Keep a Changelog`, `Semantic Versioning`, `hypothesis`, `Matplotlib` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `.notch_at()` and `notch_filter(freq, quality=30) (documented instance method)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `.highpass_at()` and `highpass_filter(cutoff, order=4) (documented instance method)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `.bandpass_at()` and `bandpass_filter(low_cutoff, high_cutoff, order=4) (documented instance method)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `.get_outlier_filter_params()` and `outlier_indices() (documented, method='iqr'/'zscore'/'modified_zscore')`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `.filter_outliers()` and `remove_outliers() (documented, method='iqr'/'zscore'/'modified_zscore')`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `.detect_outliers()` and `outlier_indices() (documented, method='iqr'/'zscore'/'modified_zscore')`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `LowessOutlierFilter.py` and `baseTs Package README`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._