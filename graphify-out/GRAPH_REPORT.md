# Graph Report - baseTs  (2026-09-03)

## Corpus Check
- 54 files · ~142,826 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1945 nodes · 3496 edges · 134 communities (128 shown, 6 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 214 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `77cf597d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- TestRelativeBandPower
- validate_sampling_freq
- LowessOutlierFilter
- TestRealWorldWorkflows
- AdaptiveLowessFilter
- .falff
- baseTs API Documentation
- TestBaseTsInitialization
- validate_finite_data
- conftest.py
- TestInvalidationOnDerivation
- exgaussian.py
- _PlotAccessor
- baseTs
- TestPandasEnhancedMethods
- TestHistoryInvariantHoldsEverywhere
- TestMathematicalOperations
- TestButterpassAt
- lf_baseTsObj
- TestFilteringOperations
- time_to_idx
- test_pandas_compat.py
- ._adopt_data_inplace
- test_utils.py
- test_lag_conversion_guards.py
- TestNoInterpolationAcrossAGap
- Derived `freq` Implementation Plan
- test_gap_preservation.py
- ._wrap_result_as_basets
- TestBaseTsTransformations
- TestReadIsPureAndDerivationReleases
- TestPandasIntegration
- Bandpass Filter Pipeline (bp_2: 0.2Hz)
- baseTs Example Signal Processing Figure
- Example 1 Signal Processing Plot
- bandpass_filter
- TailType
- Design
- test_plot_accessor.py
- get_peak_freq
- TestMetadataPropagation
- ._enhanced_process_with_flags
- TestLabelMetadataSurvivesDerivation
- FilterConfig
- TestEffectiveFrequency
- TestInvalidationOnInPlaceIndexChange
- requirements.txt
- parametrize
- ValidationError
- _FinalizingWindow
- TestWindowGuard
- test_qc_plot.py
- TestHistoryNoneSurvivesRealOperations
- TestDerivationPathsAgree
- TestFiltersRejectNanFreq
- TestArithmeticOperators
- TestHistoryNoneGuard
- Carrying pandas' identity fields across derivation (#35, #39)
- TestANonFiniteLagIsDiagnosed
- test_filters.py
- test_exception_hierarchy.py
- test_type_preservation.py
- TestIndexMutationsWithNoHookAtAll
- TestTheStampIsNotLaunderable
- TestInheritedPandasInplaceMethods
- test_core.py
- _freq_token
- parametrize
- Derived `freq`: closing #29, #31 and #23
- TestDeepCopyIndependence
- TestTheInvalidParameterContractIsComplete
- TestAnExplicitArgumentStillWins
- TestNoWriteThrough
- InvalidParameterError
- test_conversion_preserves_metadata.py
- series.py
- plotting.py
- plot_fft_power
- TestBaseTsConversionPreservesMetadata
- .info
- TestInvalidationThroughCreateNewWithData
- .freq
- TestRejectionMessagesNameTheRealLimit
- TestScaleFloorWarning
- _gappy_ts
- TestTheDisplayBoundsAreValidatedBeforeDrawing
- TestOutlierFilterSurvivesDerivation
- TestEveryBandpassEntryPointRejectsABadLowerEdge
- TestDuplicateLabelRefusal
- test_enhanced_methods.py
- test_derived_lowess_invalidation.py
- TestWindowingParamsAreGuardedLikeTheBandEdges
- parametrize
- TestTheOutcomeCensusIsComplete
- TimeSeriesData
- from_df
- core.py
- .test_augmented_assignment_is_still_in_place
- shift_timeseries
- get_peaks
- .__mul__
- .test_invalid_parameter_type_raises_valueerror
- TestNumFitsDeprecation
- TestNaNSentinel
- test_identity_propagation.py
- basets_owned_inplace_methods
- _validate_display_rate
- .copy
- .plot_fft_power
- test_the_legend_label_keeps_the_callers_own_formatting
- fixture
- test_pipeline.py
- bad_rate_ts
- TestInterpToHzRejections
- .bandpass_at
- TestAFiniteInputCannotProduceANonFiniteResult
- seeded
- _ExtendedForPickling
- _positional_property
- TestArithmeticNameFollowsPandas
- TestLabelMetadataAtConstruction
- TestPickleWrittenBeforeTheFix
- TestNanFreqIsNotLaundered
- TestReinitHasOneDoor
- TestAttrsIsolation
- TestFlagsAssignmentAssumption
- .test_copy_configuring_does_not_reach_the_original
- .test_get_outlier_filter_params_is_a_snapshot
- .test_outlier_indices_is_reachable_after_slicing

## God Nodes (most connected - your core abstractions)
1. `baseTs` - 324 edges
2. `TimeSeriesData` - 135 edges
3. `LowessOutlierFilter` - 79 edges
4. `FilterConfig` - 53 edges
5. `ValidationError` - 42 edges
6. `InvalidParameterError` - 39 edges
7. `plot_fft_power()` - 38 edges
8. `bandpass_filter()` - 34 edges
9. `baseTs API Documentation` - 32 edges
10. `baseTs User Guide` - 30 edges

## Surprising Connections (you probably didn't know these)
- `notch_filter(freq, quality=30) (documented instance method)` --conceptually_related_to--> `notch_filter()`  [AMBIGUOUS]
  docs/API.md → baseTs/filters.py
- `highpass_filter(cutoff, order=4) (documented instance method)` --conceptually_related_to--> `highpass_filter()`  [AMBIGUOUS]
  docs/API.md → baseTs/filters.py
- `bandpass_filter(low_cutoff, high_cutoff, order=4) (documented instance method)` --conceptually_related_to--> `bandpass_filter()`  [AMBIGUOUS]
  docs/API.md → baseTs/filters.py
- `baseTs API Documentation` --references--> `from_df()`  [EXTRACTED]
  docs/API.md → baseTs/core.py
- `Direct Pandas Series Inheritance Architecture` --rationale_for--> `baseTs`  [EXTRACTED]
  MIGRATION_GUIDE.md → baseTs/core.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **baseTs Documentation Suite** — readme_doc, docs_user_guide_doc, docs_api_doc, docs_api_series_doc, docs_examples_doc, docs_changelog_doc, claude_devguide [EXTRACTED 1.00]
- **baseTs Signal Processing Pipeline Demonstration** — imgs_basets_example_figure, imgs_basets_example_raw_signal_with_spikes, imgs_basets_example_lowess_despiking, imgs_basets_example_bandpass_filter, imgs_basets_example_fft_power_spectrum [EXTRACTED 1.00]
- **LOWESS Despiking Workflow** — basets_core_basets_set_outlier_filter, basets_core_basets_filter_outliers, lowess_outlier_detection, basets_lowessoutlierfilter [EXTRACTED 1.00]
- **Enhanced Pandas Series Methods (v2.0.0 Migration)** — basets_core_basets_resample, basets_core_basets_interpolate_gaps, basets_core_basets_align_with, basets_core_basets_correlation_with, basets_core_basets_detect_outliers, basets_core_basets_rolling_mean, basets_core_basets_time_slice, basets_core_basets_get_statistics, basets_core_basets_get_frequency_content, basets_core_basets_shift_time [EXTRACTED 1.00]
- **baseTs Signal Processing Pipeline (despike -> lowpass filter -> rolling mean smoothing)** — imgs_example1_plot_raw_signal, imgs_example1_plot_despiked, imgs_example1_plot_filtered, imgs_example1_plot_smoothed [INFERRED 0.85]

## Communities (134 total, 6 thin omitted)

### Community 0 - "TestRelativeBandPower"
Cohesion: 0.14
Nodes (11): Tests for the relative_band_power / falff methods., Slow 0.05 Hz signal long enough to resolve the 0.01-0.1 Hz band., Method delegates correctly and returns a builtin float., The headline robustness property: an undetrended mean offset must not move the…, The documented pipeline produces the same answer., falff() defaults to the amplitude convention., details=True carries the white-noise null alongside the ratio., The window argument reaches get_frequency_content. (+3 more)

### Community 1 - "validate_sampling_freq"
Cohesion: 0.17
Nodes (13): coerce_real_scalar(), ValueError, Coerce a scalar argument to a float, or raise ValueError naming it. The type…, Reject a sampling rate that cannot produce meaningful frequency bins. Written…, validate_sampling_freq(), The documented ValueError holds for non-numeric input too. `freq > 0` raises…, Only NaN gets the degenerate-time-base hint. A zero or negative rate is nearly…, Types float() converts must not be rejected, nor crash on isfinite. An earlier… (+5 more)

### Community 2 - "LowessOutlierFilter"
Cohesion: 0.17
Nodes (12): LowessOutlierFilter, ndarray, Apply LOWESS smoothing and outlier detection to the data. Parameters ----------…, Reject configurations whose local window is too small to smooth. LOWESS fits a…, Apply LOWESS smoothing to the data. Uses statsmodels' Cleveland LOWESS. Note…, Process a single iteration of outlier detection., Validate and convert input data to a NumPy array., Validate and obtain the time index. (+4 more)

### Community 3 - "TestRealWorldWorkflows"
Cohesion: 0.08
Nodes (15): Integration tests for real-world time series workflows. Tests complete end-to-…, Test batch processing multiple time series., Test realistic time series analysis workflows., Test data consistency across operations., Test complete signal processing workflow., Test workflow with larger datasets., Test scientific analysis workflow., Test compatibility across different workflow scenarios. (+7 more)

### Community 4 - "AdaptiveLowessFilter"
Cohesion: 0.11
Nodes (18): AdaptiveLowessFilter, demo_adaptive_lowess(), LowessConfig, ndarray, Calculate optimal segment length based on dominant frequency content., Configuration parameters for adaptive LOWESS filtering., Calculate overlap ratio based on signal complexity., Calculate LOWESS fraction based on frequency content and noise. (+10 more)

### Community 5 - ".falff"
Cohesion: 0.27
Nodes (8): Compute the relative power (or amplitude) in a frequency band. This is the…, Fractional amplitude of low-frequency fluctuations (fALFF). Convenience wrapper…, baseTs Changelog, Unreleased: Relative Band Power / fALFF, baseTs 1.0.0 Release (NumPy backend), Keep a Changelog, Semantic Versioning, Zou et al. 2008, J Neurosci Methods 172(1):137-141 (fALFF)

### Community 6 - "baseTs API Documentation"
Cohesion: 0.09
Nodes (32): Apply a lowpass filter at the specified cutoff frequency. Args: cutoff: Lowpass…, Apply a lowpass filter to the data. Args: cutoff: Lowpass cutoff frequency in…, Set outlier filter parameters. Parameters ---------- params : dict, optional…, Apply the outlier filter to the signal. Args: inplace (bool, optional): If…, Apply a rolling mean to the data. Args: window: Size of the rolling window…, Apply a rolling standard deviation to the data., Apply a rolling median to the data., Apply a rolling maximum to the data. (+24 more)

### Community 7 - "TestBaseTsInitialization"
Cohesion: 0.20
Nodes (6): Tests for baseTs initialization and basic properties., Test initializing baseTs with data and times., Test initializing baseTs with data and frequency., Test initialization validation requirements., Test length and duration calculations., TestBaseTsInitialization

### Community 8 - "validate_finite_data"
Cohesion: 0.12
Nodes (19): Reject sample values an FFT cannot produce a meaningful spectrum from. The…, validate_finite_data(), parametrize, The production site raises instead of returning an all-NaN spectrum.…, The guard rejects bad values, not unfamiliar dtypes. Complex is the load-…, Object and complex arrays are checked, not waved through. np.isfinite raises…, NaT must not slip through the float cast. This is the one dtype family where…, The remedy the message names must not launder NaT into a finite float. An… (+11 more)

### Community 9 - "conftest.py"
Cohesion: 0.15
Nodes (18): data_with_outliers(), noisy_baseTsObj(), noisy_data(), outlier_baseTsObj(), fixture, Pytest configuration and fixtures., Sine with two large, unambiguous spikes. Returns (data, times) rather than a…, Generate a simple sine wave dataset for testing. (+10 more)

### Community 10 - "TestInvalidationOnDerivation"
Cohesion: 0.14
Nodes (6): rolling() routes through _FinalizingWindow, not __finalize__ directly., A different index means neither attribute describes the object., Stricter than the `freq` token, deliberately. `_freq_token` is (len, first,…, Invalidation is about the index, not about deriving at all., The rule is index equality, not "was a slicing method called"., TestInvalidationOnDerivation

### Community 11 - "exgaussian.py"
Cohesion: 0.19
Nodes (20): calculate_aic(), calculate_bic(), chi_square_test(), exg_initial_guess(), ExGaussianFit, FitStatistics, get_exg_fits(), iterative_exgaussian_fit() (+12 more)

### Community 12 - "_PlotAccessor"
Cohesion: 0.20
Nodes (4): _PlotAccessor, Callable proxy backing ``baseTs.plot``. ``plot`` used to be a plain alias for…, Plot the timeseries as a line plot. Quick and dirty visualization., Line plot, or the pandas plotting accessor. Calling it is the historical baseTs…

### Community 13 - "baseTs"
Cohesion: 0.06
Nodes (24): baseTs, Interpolate missing values in the data., Compute the first difference of the timeseries., Basic data class to hold a timeseries and data. Built on pandas Series…, Compute the FFT power of the timeseries., Get the peaks in the timeseries. Returns a list of the indices of the peaks., Set or updates the timestamp offset., Keep pandas operations returning baseTs rather than downgrading. Without this,… (+16 more)

### Community 14 - "TestPandasEnhancedMethods"
Cohesion: 0.11
Nodes (10): Test new pandas-enhanced methods., Test pandas-powered rolling mean., Test rolling standard deviation., Test time-based slicing., Test pandas resampling., Test cross-correlation between time series., Test outlier detection., Test gap interpolation. (+2 more)

### Community 15 - "TestHistoryInvariantHoldsEverywhere"
Cohesion: 0.07
Nodes (21): parametrize, Tests for lowess_detrend, centred on its inplace=False purity contract., Guard for the purity tests below. They assert that self.data survives…, Issue #6: the caller's object must survive a non-inplace detrend., Issue #6: detrending must not rewrite the caller's filter config.…, The inplace path removes the trend and reports the fit it used., Detrending subtracts a robust trend from the *original* data. The spikes are…, Regression guard for the is_outlier_filtered decoupling. lowess_detrend… (+13 more)

### Community 16 - "TestMathematicalOperations"
Cohesion: 0.12
Nodes (9): Test absolute value operations., Test method chaining works correctly., Test that arithmetic operations return baseTs objects., Test mathematical operations with pandas Series foundation., Test z-scaling operations., Test range normalization operations., Test centering operations., Test scaling operations. (+1 more)

### Community 17 - "TestButterpassAt"
Cohesion: 0.12
Nodes (13): Every metadata slot must come out where bandpass_at puts it. Asserted against…, Delegation is deliberate: the entry reads bandpass, not butterworth. No caller…, butterpass_at must actually run, and must mean what its name says (#27). It…, Amplitude of one tone by projection, so no FFT bin has to line up., The issue's reproduction: this raised TypeError on every call., The band kept must be [hp_freq, lp_freq], not its mirror image. A positional…, An alias that computes something else is not an alias., A source carrying a non-default value in every seedable metadata slot. The… (+5 more)

### Community 18 - "lf_baseTsObj"
Cohesion: 0.67
Nodes (3): lf_baseTsObj(), fixture, Long, slowly-varying signal suitable for 0.01-0.1 Hz band analysis. 600 s at 2…

### Community 19 - "TestFilteringOperations"
Cohesion: 0.14
Nodes (8): Test filtering operations., Test lowpass filtering., Test highpass filtering., Test bandpass filtering., Test Savitzky-Golay filtering., Test Gaussian filtering., Test chaining multiple filters., TestFilteringOperations

### Community 20 - "time_to_idx"
Cohesion: 0.11
Nodes (14): _coerce_lag(), idx_to_time(), Convert a lag to a float, or say which argument is wrong. validate_lag is the…, Convert an index to a time value. Args: lag_idx: Index to convert freq:…, Convert a time value to an index. Args: lag_secs: Time in seconds freq:…, time_to_idx(), Existing code that names the domain type must be unaffected., Both are public utilities, so neither can rely on its caller. (+6 more)

### Community 21 - "test_pandas_compat.py"
Cohesion: 0.07
Nodes (16): fixture, parametrize, Regression tests for pandas 2.x/3.x compatibility. Each test here corresponds…, baseTs.duration() shadowed the guarded TimeSeriesData.duration()., get_statistics() calls duration(), so it inherited the crash., 5000 normal samples with one unmistakable spike at index 100., pandas 3.0 removed fillna(method=...)., Series.interpolate() does not fill leading/trailing NaN, so this path always… (+8 more)

### Community 22 - "._adopt_data_inplace"
Cohesion: 0.18
Nodes (9): ndarray, setter, Set specific indices to NaN and interpolate the missing values. Args: indices:…, Get the data values as numpy array (backward compatibility)., Set the data values (backward compatibility)., Get the time values as numpy array (backward compatibility)., Set the time values (backward compatibility)., Re-initialise this object's data and index, keeping everything else. The single… (+1 more)

### Community 23 - "test_utils.py"
Cohesion: 0.10
Nodes (27): Compute the relative power (or amplitude) in a frequency band. This is the…, relative_band_power(), Unit tests for baseTs utility functions., Test find_closest function., A dominant 0.05 Hz component should put most power in the 0.01-0.1 band., Adding a constant offset must not change the result. get_frequency_content()…, For white noise both conventions converge on the bin fraction. That makes…, Disjoint bands tiling the non-DC spectrum sum to 1.0 for ratio='power'. (+19 more)

### Community 24 - "test_lag_conversion_guards.py"
Cohesion: 0.16
Nodes (10): get_lags(), Get lag values in both seconds and indices. Args: lag: Lag value lag_unit: Unit…, _degenerate(), Guards on the two lag-conversion primitives (issue #32). `time_to_idx` and…, Every timestamp identical, so the derived rate is NaN. This is the object from…, The rate must be rejected where it enters the conversion. Each of these fails…, The silent half of #32. On main this returns successfully with `lag_secs=nan`:…, Index mode is `lag_plot`'s default, and on main it draws a plot titled "nan… (+2 more)

### Community 25 - "TestNoInterpolationAcrossAGap"
Cohesion: 0.32
Nodes (4): An input gap is a boundary, not something to interpolate through. Filling the…, It must not be pulled toward the first valid sample after the gap., Two gaps, three segments; an outlier in each must stay local., TestNoInterpolationAcrossAGap

### Community 26 - "Derived `freq` Implementation Plan"
Cohesion: 0.18
Nodes (10): Before opening the PR, Commit boundaries, Derived `freq` Implementation Plan, Global Constraints, Task 1: Index token and derivation hardening, Task 2: Make the legacy freq tests independent of freq storage, Task 3: The atomic switch — `freq` becomes a property, Task 4: Fix the `interpto_hz` grid (+2 more)

### Community 27 - "test_gap_preservation.py"
Cohesion: 0.09
Nodes (22): _gappy(), _nan_mask(), fixture, parametrize, _quiet(), Tests for issue #36: filter_outliers must not invent data in pre-existing gaps.…, The old fill-everything behaviour stays reachable for anyone relying on it., Silent is the failure mode; the history entry should carry the count. (+14 more)

### Community 28 - "._wrap_result_as_basets"
Cohesion: 0.09
Nodes (11): Helper method to update history and last_process. Normalises rather than…, Addition operation returning a baseTs object., Right addition operation returning a baseTs object., Subtraction operation returning a baseTs object., Right subtraction operation returning a baseTs object., Right multiplication operation returning a baseTs object., Division operation returning a baseTs object., Right division operation returning a baseTs object. (+3 more)

### Community 29 - "TestBaseTsTransformations"
Cohesion: 0.17
Nodes (7): Test data normalization functions., Test detrending functionality., Test trimming functionality., Tests for baseTs data transformations., Test interpolation to specified number of samples., Test interpolation to specified frequency., TestBaseTsTransformations

### Community 30 - "TestReadIsPureAndDerivationReleases"
Cohesion: 0.19
Nodes (7): Two halves of one contract, neither depending on who read what. Reading is a…, The asymmetry that clearing-on-read introduced., Specified, not accidental. Within this property's scope - do the samples still…, The other half: derivation destroys, so a revert cannot undo it., Memory: a slice must not pin the parent's full-length array., Every derived object gets a new Index, so a first read is O(n). Re-stamping…, TestReadIsPureAndDerivationReleases

### Community 31 - "TestPandasIntegration"
Cohesion: 0.20
Nodes (6): Test direct pandas integration features., Create sample time series., Test direct access to pandas methods., Test pandas-style indexing., Test that metadata is preserved through pandas operations., TestPandasIntegration

### Community 32 - "Bandpass Filter Pipeline (bp_2: 0.2Hz)"
Cohesion: 0.80
Nodes (5): Bandpass Filter Pipeline (bp_2: 0.2Hz), Multi-Stage Filter Chaining / Method Pipelining, baseTs Pipelined Filter Output, Filtered Signal by Time Plot, Power Spectrum of Filtered Signal Plot

### Community 33 - "baseTs Example Signal Processing Figure"
Cohesion: 0.70
Nodes (5): Bandpass Filtered Signal (0.2-2 Hz), FFT Power Spectrum Analysis, baseTs Example Signal Processing Figure, Lowess Filtering to Remove Spikes (Despiking), Raw Signal with Spikes/Outliers

### Community 34 - "Example 1 Signal Processing Plot"
Cohesion: 0.80
Nodes (5): Example 1 Signal Processing Plot, Despiked Panel (LAB SIGNAL_outfilt), Filtered Panel (LAB SIGNAL_lp_6Hz), Raw Signal Panel (LAB SIGNAL_outfilt_params), Smoothed Panel (LAB SIGNAL_rolling_mean_30)

### Community 35 - "bandpass_filter"
Cohesion: 0.10
Nodes (18): bandpass_filter(), Apply a symmetric bandpass filter to the input data. Args: data: Input data…, parametrize, All of these must raise; four of the seven previously did not. The negative,…, A message about ordering is useless without the two values in it., The asymmetry that made this bug position-dependent. `max(0.1, nan)` returns…, Nyquist must come from the effective rate, not the declared one. The filter…, Pins that the check above is about the effective rate. Without this, the… (+10 more)

### Community 36 - "TailType"
Cohesion: 0.08
Nodes (18): Created on Oct 19 2024 @author: stan@sympaticog.com, Enum for specifying which tails to process in outlier detection., TailType, baseTs Package README, Enum, LOWESS Outlier Detection & Despiking, Tests for the statsmodels LOWESS backend of LowessOutlierFilter. Covers the…, fill_input_gaps=True restores the pre-#36 behaviour. (+10 more)

### Community 37 - "Design"
Cohesion: 0.12
Nodes (16): Behaviour changes, Deep copy and detachment, Design, Eager release on derivation, Order of checks, Pickles written before this change, Problem, Producers (+8 more)

### Community 38 - "test_plot_accessor.py"
Cohesion: 0.10
Nodes (11): close_figures(), fixture, parametrize, Tests for the hybrid baseTs.plot accessor. `plot` was a plain alias for…, The historical spelling must be unchanged., The accessor is a property, so it must follow the preserved type., Each accessor plots its own data, not the parent's., TestAccessorSurvivesOperations (+3 more)

### Community 39 - "get_peak_freq"
Cohesion: 0.14
Nodes (14): get_peak_freq(), Get the top peak frequencies of the time series using enhanced frequency…, _degenerate_freq_ts(), A series whose time base is degenerate, so freq derives to NaN.…, A NaN sampling rate raises rather than producing NaN frequencies. `nan <= 0` is…, get_frequency_content computes its own FFT and needs its own guard. It does not…, get_peak_freq inherits the guard through get_frequency_content., A NaN rate is rejected, via get_frequency_content downstream. This pins… (+6 more)

### Community 40 - "TestMetadataPropagation"
Cohesion: 0.09
Nodes (11): The __finalize__ concat special-case exists for nlargest/nsmallest's internal…, pandas' default __finalize__ assigns metadata by reference, so parent and child…, pandas' _inplace_method reindexes the result back to self before adopting it.…, TimeSeriesData never set outlier_filter despite declaring it in _metadata, so a…, baseTs(ts) takes the conversion branch in TimeSeriesData.__init__, which…, Every parameter used to carry a real default, so naming frac also set…, The whole design rests on this: a frozen config plus a rebinding…, Two series built from one list would cross-contaminate. (+3 more)

### Community 41 - "._enhanced_process_with_flags"
Cohesion: 0.08
Nodes (14): Apply a Gaussian filter to the data. Args: sigma: Standard deviation for…, Apply a Savitzky-Golay filter to the signal. Args: window_length: Length of the…, Helper method to update object flags., Enhanced processing method that handles both data and time modifications. Args:…, Normalize the data to a specified range. Args: target_min: Minimum value of…, Center the data around zero (remove mean). Args: inplace: If True, modifies…, Scale the data by a constant factor. Args: factor: Scaling factor inplace: If…, Take absolute value of the data. Args: inplace: If True, modifies existing… (+6 more)

### Community 42 - "TestLabelMetadataSurvivesDerivation"
Cohesion: 0.11
Nodes (14): _DuckSeries, parametrize, The other route to a None: the metadata-copy fallback in series.py.…, signal_name and last_process are always strings" - same defect class. Issue #33…, A number is as fatal to `name + " " + process` as a None is. On the…, The live crash: TypeError: unsupported operand 'NoneType' + 'str'., Restoring a default must not rewrite a name someone chose. Deliberately already…, `is_outlier_filtered` is a flag, and the fallback left it None. The defaulting… (+6 more)

### Community 43 - "FilterConfig"
Cohesion: 0.11
Nodes (13): FilterConfig, Configuration parameters for the LowessOutlierFilter. Attributes ----------…, Initialize the LowessOutlierFilter with filtering parameters. Parameters…, np.asarray drops a mask and exposes the payload underneath., TestMaskedArrayGapsAreSeen, statsmodels defaults to missing='drop'; return_sorted=False must re-insert NaN…, statsmodels is lowess(endog, exog) = (y, x); moepy was fit(x, y). Transposing…, Same y, x stretched: the fitted values must be essentially unchanged. (+5 more)

### Community 44 - "TestEffectiveFrequency"
Cohesion: 0.09
Nodes (12): n samples span n-1 intervals., rolling() does not call __finalize__, so freq is recomputed from the index - it…, nlargest(3) is excluded from the op list above - it is the one op there that…, #19: resample changes the time base, so the carried freq described the old…, An explicitly supplied freq may legitimately disagree with the times it was…, #19: arithmetic on two different time bases must derive from the union index…, #19: interpto_samples assigned n/duration over the corrected derivation., #19: same n/duration error as interpto_samples. (+4 more)

### Community 45 - "TestInvalidationOnInPlaceIndexChange"
Cohesion: 0.17
Nodes (5): The index can change without any derivation at all., `.index` is pandas' own setter, and `.times` is not the only door., The inplace branch calls pd.Series.__init__ directly, bypassing…, The data setter rebuilds the index when the length changes., TestInvalidationOnInPlaceIndexChange

### Community 46 - "requirements.txt"
Cohesion: 0.18
Nodes (11): Python Package CI Workflow, hypothesis, Matplotlib, moepy, NumPy, Pandas, psutil, pytest (+3 more)

### Community 47 - "parametrize"
Cohesion: 0.11
Nodes (9): parametrize, pandas supports `for window in ts.rolling(3): ...`, yielding each window as its…, The contract is behavioural, not identity. FilterConfig is frozen and…, Independence must not cost the config: the values still carry over., Arithmetic returns via _wrap_result_as_basets, which assigned every metadata…, pandas implements `ts += 1` by calling __add__ and keeping only the values,…, _create_new_with_data omitted outlier_filter from the attributes it carries, so…, ts is uniformly sampled, so every op here should agree with it. (+1 more)

### Community 48 - "ValidationError"
Cohesion: 0.14
Nodes (10): Exception raised for validation errors. Also a ValueError, because a rejected…, Validate lag parameters. Args: lag: Lag value lag_idx: Lag index lag_unit: Unit…, validate_lag(), ValidationError, `_name` now reaches deepcopy_metadata_value; it must pass through., Which is why the isinstance gate in that helper never matches it. Recorded as a…, `_metadata` must extend pandas' list rather than replace it., Every name pandas declares must still be carried. Asserted against… (+2 more)

### Community 54 - "_FinalizingWindow"
Cohesion: 0.16
Nodes (7): _FinalizingWindow, Wraps a pandas window object (Rolling/Expanding/ExponentialMovingWindow) so its…, Python looks up dunder methods on the type, bypassing __getattr__, so this…, See _FinalizingWindow: rolling()/expanding()/ewm() never call __finalize__., Rolling window whose aggregations propagate metadata - see _FinalizingWindow., Expanding window whose aggregations propagate metadata - see _FinalizingWindow., EWM window whose aggregations propagate metadata - see _FinalizingWindow.

### Community 55 - "TestWindowGuard"
Cohesion: 0.13
Nodes (7): A window of <= 3 points makes LOWESS interpolate the data exactly. The fit is…, The same default frac that is fine at n=500 is degenerate at n=20., The suggested frac must actually satisfy the guard., A run starting at exactly k == 4 falls to k == 3 after one removal. The loop…, NaNs do not count towards the window: 500 slots, 10 real points., The issue was reported through lowess_detrend, which returned all-zero…, TestWindowGuard

### Community 56 - "test_qc_plot.py"
Cohesion: 0.20
Nodes (13): _close_figures(), fixture, parametrize, Tests for filter_outliers(qcplot=True). The QC plot exists to show the filter's…, The plotting path must not become a second route to the #6 bug., Asking for a plot must not change what the filter returns., spiked_ts(), test_lowess_fit_trace_is_present() (+5 more)

### Community 57 - "TestHistoryNoneSurvivesRealOperations"
Cohesion: 0.26
Nodes (5): The None-history guard must hold on the paths users actually take. Guarding…, zscale() dies in _create_new_with_data's history.copy()., info() iterates history; None raised TypeError., __finalize__ turns a propagated None into a list., TestHistoryNoneSurvivesRealOperations

### Community 58 - "TestDerivationPathsAgree"
Cohesion: 0.29
Nodes (3): Issue #29's acceptance test. The same index change had two answers depending on…, A value-sorted series has a non-monotonic index and no honest rate. The carried…, TestDerivationPathsAgree

### Community 59 - "TestFiltersRejectNanFreq"
Cohesion: 0.27
Nodes (4): A degenerate time base must not filter to silent all-NaN output.…, butterpass_at was absent from this family because it never ran (#27). It…, The guard must not disturb an ordinary series., TestFiltersRejectNanFreq

### Community 60 - "TestArithmeticOperators"
Cohesion: 0.20
Nodes (5): parametrize, The operator dunders do not route through __finalize__. `__add__` and friends…, A scalar cannot change the index, so nothing should be dropped., `ts += x` cannot change ts's index, so it must not drop anything.…, TestArithmeticOperators

### Community 61 - "TestHistoryNoneGuard"
Cohesion: 0.29
Nodes (4): A `history` of None must not crash the next operation (issue #22). __finalize__…, The superclass guard is hasattr-only, so None slips past it too., The guard must not discard a history that is genuinely present., TestHistoryNoneGuard

### Community 62 - "Carrying pandas' identity fields across derivation (#35, #39)"
Cohesion: 0.10
Nodes (19): Carrying pandas' identity fields across derivation (#35, #39), Decisions taken, Deliberately not in scope, Design, Half A — `_name` joins `_metadata`, Half B, Group 1 — one door for the identity triple, Half B, Group 2 — collapse three doors into one, Making a tenth site fail loudly (+11 more)

### Community 63 - "TestANonFiniteLagIsDiagnosed"
Cohesion: 0.11
Nodes (11): parametrize, `validate_lag` never gets to speak, because `get_lags` converts first. The rate…, A string lag dies on main with `can't multiply sequence by non-int`. It must…, float(10**400) raises OverflowError, which is neither TypeError nor ValueError…, It is a perfectly good real number; it is out of float's range. Collapsing…, `{lag!r}` on a large object builds a megabyte-long exception. A 200k-element…, The str/bytes exclusion is load-bearing for both, not just str. `float(b"0.5")`…, One argument, one exception type, whichever mode it arrives in. Guarding only… (+3 more)

### Community 64 - "test_filters.py"
Cohesion: 0.13
Nodes (12): register, _DeclaresOneHz, _LiesAboutDivision, Unit tests for baseTs.filters parameter validation., Registers as a Real but cannot become one. numbers.Real is a registrable ABC,…, A Real that converts to 1.0 and supports nothing else. Registers, coerces,…, Validation is worthless if the filter then uses a different value. Five review…, It declared float() == 1.0, so 1.0 is what the filter must use. (+4 more)

### Community 65 - "test_exception_hierarchy.py"
Cohesion: 0.10
Nodes (18): FilterError, Exception, Base exception for filter-related errors., Exception, Base exception for time series related errors., TimeSeriesError, _degenerate(), The domain exceptions are also ValueErrors. Both validating families raise a… (+10 more)

### Community 66 - "test_type_preservation.py"
Cohesion: 0.18
Nodes (7): fixture, Tests that pandas operations preserve the baseTs type and its metadata. Before…, The documented pattern: a pandas op followed by a baseTs op., pandas builds subclasses as _constructor(values, index=...)., pandas looks this up on the class; a plain method breaks that., TestTypePreservation, ts()

### Community 67 - "TestIndexMutationsWithNoHookAtAll"
Cohesion: 0.22
Nodes (3): The doors that defeated the write-side design. These reach past `__finalize__`,…, The third `pd.Series.__init__` site, and the one an explicit audit for that…, TestIndexMutationsWithNoHookAtAll

### Community 68 - "TestTheStampIsNotLaunderable"
Cohesion: 0.22
Nodes (5): A copy must move the (value, index) pair, never re-stamp it. Any path that…, The discriminating case for laundering. sg_filter routes through…, Memory, not correctness: the getter already reads a slice as None. Without this…, The behavioural form of the laundering check. Starting from a *valid* fit is…, TestTheStampIsNotLaunderable

### Community 69 - "TestInheritedPandasInplaceMethods"
Cohesion: 0.18
Nodes (5): `inplace=True` on an inherited pandas method swaps the block manager. pandas…, The reported crash, reachable without any baseTs method at all., The silent variant: same length, every position moved., These change values, not positions, so the rule must not fire., TestInheritedPandasInplaceMethods

### Community 70 - "test_core.py"
Cohesion: 0.12
Nodes (10): Unit tests for baseTs core functionality., Tests for baseTs filtering functionality., Test highpass filter., Test bandpass filter., Test Savitzky-Golay filter., Tests for outlier detection functionality., Test setting outlier filter parameters., Test outlier filtering. (+2 more)

### Community 71 - "_freq_token"
Cohesion: 0.18
Nodes (7): _freq_token(), Fingerprint an index for the purpose of sampling-rate derivation. Deliberately…, The token must be exactly the inputs _calculate_effective_frequency reads. That…, interpto_hz was not one of this task's five write sites - it is Task 4's - but…, And must not: the derived rate is unchanged, so the token is right.…, TestFreqToken, TestInterptoHzRoutesThroughTheValidatingSetter

### Community 72 - "parametrize"
Cohesion: 0.09
Nodes (11): parametrize, An explicit rate is honoured until the index it describes changes., Guards the _freq_declaration entry in _create_new_with_data's metadata_attrs…, Issue #31: a bad rate must be refused where it enters the object., baseTs(data, freq=...) with no times builds the index FROM the rate. freq=0…, baseTs' public default is freq=np.nan, so it cannot mean "invalid". Deliberate…, The produced grid must actually have the rate it reports. linspace(t0, t1,…, Regression: a bare floor() drops a trailing sample. (np.arange(1000)/30.0)… (+3 more)

### Community 73 - "Derived `freq`: closing #29, #31 and #23"
Cohesion: 0.14
Nodes (13): 1. The `freq` property, 2. Propagation, 3. Validation at production sites (#31), 4. `interpto_hz` (#23), 5. Deletions, 6. Edge cases, Approach, Consequences (+5 more)

### Community 74 - "TestDeepCopyIndependence"
Cohesion: 0.29
Nodes (3): `copy(deep=True)` must hand back arrays the parent does not share. Both copy…, The constructor types this as np.array, so a list check is not enough., TestDeepCopyIndependence

### Community 75 - "TestTheInvalidParameterContractIsComplete"
Cohesion: 0.31
Nodes (5): Every known bad input raises InvalidParameterError, enumerated. The CHANGELOG…, Every known bad input raises, with the message its own guard makes., The number in the prose is asserted against the table. Adding a case without…, A fragment true of another case's message pins nothing. Three fragments were…, TestTheInvalidParameterContractIsComplete

### Community 76 - "TestAnExplicitArgumentStillWins"
Cohesion: 0.17
Nodes (6): parametrize, The conversion branch takes its index from the source, so a `times` argument…, Preserving what was not passed must not ignore what was. The fix distinguishes…, `history=None` is the documented way to ask for a fresh entry. Folding it into…, TestAnExplicitArgumentStillWins, TestAnIgnoredIndexIsRefused

### Community 77 - "TestNoWriteThrough"
Cohesion: 0.33
Nodes (3): outlier_indices is a mutable list; two objects must not share one., sg_filter keeps the index, so the list survives - it must not be shared., TestNoWriteThrough

### Community 78 - "InvalidParameterError"
Cohesion: 0.11
Nodes (31): ArrayLike, _as_real_float(), FilterConfig, highpass_filter(), interpolate_missing_values(), InvalidParameterError, lowpass_filter(), notch_filter() (+23 more)

### Community 79 - "test_conversion_preserves_metadata.py"
Cohesion: 0.14
Nodes (10): carrying(), fixture, Converting a series must not reset what it was carrying (issue #57).…, The conversion branch was gated on `.times` and `.data`. Only `baseTs` defines…, An empty carried history must not become a fabricated creation entry. The…, A series with every metadata value moved off its default., The ordinary path must still start from defaults, not from nothing. Nothing is…, TestAnEmptyHistoryIsAHistory (+2 more)

### Community 80 - "series.py"
Cohesion: 0.09
Nodes (28): Initialize baseTs object as pandas Series with time-series metadata. Args:…, _apply_duplicate_label_declaration(), _carries_metadata(), _carry_identity(), deepcopy_metadata_value(), _detach_shared_metadata(), _drop_stale_positional_metadata(), normalise_history() (+20 more)

### Community 81 - "plotting.py"
Cohesion: 0.13
Nodes (21): hist(), lag_plot(), plot(), plot_series(), array, Axes, ndarray, qc_plot() (+13 more)

### Community 82 - "plot_fft_power"
Cohesion: 0.09
Nodes (31): plot_fft_power(), Plots the power spectrum of a timeseries signal using enhanced FFT with…, Tests for issue #34: plot_fft_power must raise, not draw the error.…, ts.plot_fft_power() is the path users actually call., setup_plot used to run before the guard, so every failure left a figure. In a…, A caller passing ax= gets it back as they left it, not titled and annotated., The band check ran after the spectrum was already plotted. Ordering matters for…, The consequence users actually meet, and the fix the docs name. Since #36… (+23 more)

### Community 83 - "TestBaseTsConversionPreservesMetadata"
Cohesion: 0.20
Nodes (6): `baseTs(ts)` is a conversion, not a reset., The sharpest edge: a converted object claimed to be freshly made. Verbatim, not…, #15's guard, which was the only name that already worked., Assigned through the public properties, these were cleared to None. Read back…, The whole list, so a name added later cannot quietly drop out., TestBaseTsConversionPreservesMetadata

### Community 84 - ".info"
Cohesion: 0.40
Nodes (3): Get outlier filter parameters as a plain dict. A snapshot, not the live config.…, Display information about the data, times, outlier filter parameters, and…, outlier_indices() (documented, method='iqr'/'zscore'/'modified_zscore')

### Community 85 - "TestInvalidationThroughCreateNewWithData"
Cohesion: 0.33
Nodes (3): _create_new_with_data copies the metadata slots outside pandas' machinery.…, Same index, so both still describe the result., TestInvalidationThroughCreateNewWithData

### Community 86 - ".freq"
Cohesion: 0.25
Nodes (5): setter, String representation of TimeSeriesData., Derive the sampling frequency from the time index. Returns NaN rather than…, The sampling rate in Hz, derived from the index unless declared. An explicitly…, Declare an explicit sampling rate against the current index. The single…

### Community 87 - "TestRejectionMessagesNameTheRealLimit"
Cohesion: 0.31
Nodes (4): A message that states no number sends the caller round the loop twice. At…, Pull the Nyquist figure the message quotes., Execute the remedy rather than asserting the string., TestRejectionMessagesNameTheRealLimit

### Community 88 - "TestScaleFloorWarning"
Cohesion: 0.22
Nodes (4): parametrize, A perfectly-fit signal drives MAD to zero; z_threshold then means nothing, so…, k == 4 must be allowed: the guard rejects degenerate, not merely small., TestScaleFloorWarning

### Community 89 - "_gappy_ts"
Cohesion: 0.14
Nodes (14): _all_four_entry_points(), _gappy_ts(), A 0.16 Hz sine over 500 samples with `n_bad` samples replaced by `bad`., The headline defect: no confident wrong answer on gappy data. Pins behaviour,…, The four public ways into an FFT, as zero-argument callables., All four spectral entry points give the same actionable error. They drifted…, The uniform-ValueError contract must hold for dtype too, not just NaN. An…, The guard is unconditional, not folded into the demean branch. demean=False is… (+6 more)

### Community 90 - "TestTheDisplayBoundsAreValidatedBeforeDrawing"
Cohesion: 0.17
Nodes (6): The frequency bounds reach ax.set_xlim, which rejects NaN and Inf. An infinite…, NaN is the documented public sentinel for max_rate - not an error., min_rate has no sentinel, so NaN is simply invalid there., Pins the shared door's ndarray branch, which mutation testing found bare.…, The other half of that branch: 0-d arrays convert alike on both majors., TestTheDisplayBoundsAreValidatedBeforeDrawing

### Community 91 - "TestOutlierFilterSurvivesDerivation"
Cohesion: 0.16
Nodes (9): _cleared_filter(), A series whose filter has been cleared - the state issue #33 reports., outlier_filter is always a filter" must hold on every derived object. Without…, __finalize__ copies the parent's None; the chokepoint must fix it., zscale() routes through _create_new_with_data, not __finalize__., info() reads outlier_filter.config to print the filter block., The filter itself is read off the object, so it died here too. Long enough for…, The deliberate boundary of a chokepoint fix, pinned so it is visible.… (+1 more)

### Community 92 - "TestEveryBandpassEntryPointRejectsABadLowerEdge"
Cohesion: 0.43
Nodes (3): The contract must hold on all three names, on the axis it is about. #28's…, Reachable at all only since #27, which was dead before it., TestEveryBandpassEntryPointRejectsABadLowerEdge

### Community 93 - "TestDuplicateLabelRefusal"
Cohesion: 0.09
Nodes (13): _Flags, Only a *stale* shadow is dropped, not any shadow. Deleting unconditionally also…, The restore arm, exercised directly. Since the pre-commit check landed, no path…, A stand-in whose flag setter raises what the caller chooses., Raising pandas' real class, not a look-alike. An earlier version of this test…, An error that names a remedy is code; the remedy must run. This repo shipped an…, The remedy that was there before, and why it was wrong. `ts.data = ...`,…, A diagnosis must not become the payload. Naming every duplicated label built an… (+5 more)

### Community 94 - "test_enhanced_methods.py"
Cohesion: 0.18
Nodes (6): Test edge cases and error handling., Test handling of empty data., Test handling of single data point., Test handling of constant data., Test invalid parameter handling., TestEdgeCases

### Community 95 - "test_derived_lowess_invalidation.py"
Cohesion: 0.20
Nodes (7): _close_figures(), filtered(), fixture, Tests for #20: lowess_fit and outlier_indices on derived objects. `lowess_fit`…, A filtered series carrying a real fit and a real outlier record., Invalidation must not disturb the methods whose job is to produce a fit., TestProducersStillSetTheFit

### Community 96 - "TestWindowingParamsAreGuardedLikeTheBandEdges"
Cohesion: 0.40
Nodes (3): `max(1, window_step - overlap)` is the same defect one line down (#30). The…, validate_band_params is public, so it cannot rely on its caller.…, TestWindowingParamsAreGuardedLikeTheBandEdges

### Community 97 - "parametrize"
Cohesion: 0.15
Nodes (9): parametrize, ValueError, matching every other bound failure in this function. '30' and True…, `band_low >= band_high` is False for NaN, so a NaN edge passed the guard. Pre-…, One ValueError for every malformed band, from two different doors. The 1- and…, One contract for the whole function, generated from a census against main.…, Newly accepted, in the opposite direction to the rest of the census. On main…, test_every_rejected_input_raises_valueerror_and_draws_nothing(), test_high_precision_bounds_are_now_accepted() (+1 more)

### Community 98 - "TestTheOutcomeCensusIsComplete"
Cohesion: 0.25
Nodes (4): The CHANGELOG's census, asserted rather than described. Every earlier branch in…, The whole of #32 in one assertion: no lag, and no choice of unit, gets a…, Index mode on a degenerate base with a usable integer lag. Both returned…, TestTheOutcomeCensusIsComplete

### Community 99 - "TimeSeriesData"
Cohesion: 0.07
Nodes (15): baseTs - A Python library for time series analysis, Calculate the duration of the time series. Returns: Duration in seconds (or…, Get the length of the time series (backward compatibility). Returns: Number of…, Helper method to update object flags., Display information about the time series data., Adopt an arithmetic result in place, history entry included. pandas implements…, Pandas Series subclass optimized for time series analysis. This class extends…, Restore from a pickle, healing a blob that predates `_name`. Adding '_name' to… (+7 more)

### Community 100 - "from_df"
Cohesion: 0.22
Nodes (7): from_df(), Convert the timeseries to a pandas DataFrame. Args: set_index (bool): If True,…, Create a baseTs object from a pandas DataFrame. Args: df: Input DataFrame…, DataFrame, Test creating baseTs from DataFrame and applying pipeline., test_from_df_to_pipeline(), Test creating baseTs from DataFrame.

### Community 101 - "core.py"
Cohesion: 0.12
Nodes (27): _is_unset(), True if a numeric argument was not supplied. The constructor uses np.nan as its…, Find the closest time in the timeseries to a target time in seconds. Args: sec:…, add_constant(), BandPowerResult, ClosestMatch, compute_fft_power(), dediff() (+19 more)

### Community 103 - "shift_timeseries"
Cohesion: 0.15
Nodes (12): Shift a time series by a lag value. Args: ts: Time series object with data and…, shift_timeseries(), One argument, one exception type. `validate_lag` raises ValidationError for…, Unchanged, and deliberately so: `idx_to_time` divides rather than truncating,…, Coercion must not start *accepting* what validate_lag rejects: a Decimal…, `lag_secs=inf` used to ride out into the returned dict and the plot title,…, Pinned so a future guard cannot quietly change what a good call returns. The…, 99.99999999999999 Hz gives 49, not 50. Guarding the rate must not be mistaken… (+4 more)

### Community 104 - "get_peaks"
Cohesion: 0.14
Nodes (14): get_peaks(), Find peaks in the time series. Args: ts: Time series object with data attribute…, _FreqStub, The original zero/negative rejection is preserved. Routed through _FreqStub…, get_peaks scales min_dist_secs by freq; NaN must not reach int()., The whole interface get_peaks needs: .data and .freq. Used where the point is…, freq <= 0 provably never influenced the result and still must not.…, np.float32/16 are not float subclasses, so an isinstance gate missed them. They… (+6 more)

### Community 105 - ".__mul__"
Cohesion: 0.33
Nodes (3): Multiplication operation returning a baseTs object., A deliberate narrowing, pinned so it is not mistaken for a bug. `lag * rate`…, float() declared 0.5 s, so 0.5 s is what must be converted.

### Community 108 - "TestNaNSentinel"
Cohesion: 0.25
Nodes (4): `freq is np.nan` only matched the one np.nan object., Previously this silently produced an all-NaN time index instead of raising,…, Deriving freq from the times array must still work. NB: the derived value is…, TestNaNSentinel

### Community 109 - "test_identity_propagation.py"
Cohesion: 0.21
Nodes (7): identity_of(), The three identity fields pandas owns must survive derivation (#35, #39). A…, The bar is pandas' own behaviour, not an invented one. If a future pandas stops…, The three fields as one comparable tuple., `ts += 1` keeps the target's own identity, as stock pandas does. Pinned because…, TestIdentitySurvivesDerivation, TestInplaceArithmeticIsUnaffected

### Community 110 - "basets_owned_inplace_methods"
Cohesion: 0.50
Nodes (3): basets_owned_inplace_methods(), Every public method this package defines that takes `inplace`. Restricted to…, A new `inplace=` method fails here until someone classifies it. The point of…

### Community 111 - "_validate_display_rate"
Cohesion: 0.50
Nodes (5): Any, Coerce a frequency bound to a float matplotlib can use as an axis limit. The…, Unpack and coerce a (low, high) band, or raise ValueError naming it. Both edges…, _validate_display_rate(), _validate_highlight_band()

### Community 112 - ".copy"
Cohesion: 0.18
Nodes (6): array, Compute the cumulative sum of the timeseries., Create a copy of the baseTs object. Args: deep: Whether to make a deep copy…, Detrend the data by subtracting a robust LOWESS fit. The trend is the LOWESS…, Resample onto a uniform grid at exactly new_freq. The grid is built from the…, Interpolate data to a uniform sampling grid. If new_grid is not specified, use…

### Community 113 - ".plot_fft_power"
Cohesion: 0.14
Nodes (10): Axes, Plot this timeseries against one or more other timeseries. e.g. for QC,…, Plot a histogram of the timeseries., Plot the power spectrum of the timeseries using enhanced frequency analysis.…, Plot a lag plot of the timeseries., Direct Pandas Series Inheritance Architecture, baseTs 2.0.0 Release (Pandas Series Foundation), Dual Backend Architecture (removed in v2.0.0) (+2 more)

### Community 114 - "test_the_legend_label_keeps_the_callers_own_formatting"
Cohesion: 0.33
Nodes (6): Validation coerces to float; the label must not inherit that. Routing the label…, A generator band worked before; unpacking it twice broke it. An earlier…, The data-space x range of an axvspan patch, on any matplotlib. axvspan returned…, _span_x_extent(), test_a_one_shot_iterable_band_is_unpacked_exactly_once(), test_the_legend_label_keeps_the_callers_own_formatting()

### Community 115 - "fixture"
Cohesion: 0.29
Nodes (4): fixture, Generate diverse test data., Generate a noisy signal for filtering tests., Generate time series data for enhanced method testing.

### Community 116 - "test_pipeline.py"
Cohesion: 0.25
Nodes (7): Integration tests for baseTs processing pipeline., Test a complete processing pipeline with multiple steps., Test method chaining for creating a processing pipeline., Test conversions between baseTs and pandas DataFrame., test_complete_processing_pipeline(), test_dataframe_conversions(), test_method_chaining()

### Community 117 - "bad_rate_ts"
Cohesion: 0.25
Nodes (8): bad_rate_ts(), _close_figures(), good_ts(), nan_data_ts(), fixture, A series with a usable rate and finite data., The issue's own reproduction: every timestamp identical, so freq is NaN., A usable rate carrying gaps - the #28 guard's input.

### Community 118 - "TestInterpToHzRejections"
Cohesion: 0.33
Nodes (3): Issue #31's sharpest production site: the one place a user hands baseTs a rate…, Previously returned a length-0 series stamped with the rate. deg.interpto_hz(5)…, TestInterpToHzRejections

### Community 119 - ".bandpass_at"
Cohesion: 0.29
Nodes (4): Apply a bandpass filter to the signal at specified low-pass and high-pass…, Apply a bandpass filter between two cutoff frequencies (alias for bandpass_at).…, Apply a Butterworth bandpass filter (alias for bandpass_at). Args: hp_freq:…, bandpass_filter(low_cutoff, high_cutoff, order=4) (documented instance method)

### Community 120 - "TestAFiniteInputCannotProduceANonFiniteResult"
Cohesion: 0.25
Nodes (4): Checking the operands is not the same as checking the result. Both arguments…, The result check must not swallow the NaN index that validate_lag diagnoses…, The check is finiteness, not a magnitude policy. This is absurd input, but it…, TestAFiniteInputCannotProduceANonFiniteResult

### Community 121 - "seeded"
Cohesion: 0.19
Nodes (9): parametrize, Each of these raised AttributeError: no attribute '_name'. Parametrised one…, `inplace=True` mutates the object; it must not reset its identity. This is the…, A baseTs whose three identity fields are all at non-default values. Every field…, The identity fix must not cost what already worked. These survived a re-init…, #39: the round-trip always worked; what came back did not. Stated precisely…, seeded(), TestInplaceMethodsPreserveIdentity (+1 more)

### Community 122 - "_ExtendedForPickling"
Cohesion: 0.40
Nodes (3): _ExtendedForPickling, A subclass adding a `_metadata` name, defined at module level. Module level…, The class-level case, which must keep working either way.

### Community 123 - "_positional_property"
Cohesion: 0.67
Nodes (3): _positional_property(), Build a property that hands back `value` only while the index it was computed…, property

### Community 124 - "TestArithmeticNameFollowsPandas"
Cohesion: 0.39
Nodes (3): The one place carrying `_name` could silently diverge from pandas.…, `result.name` is pandas-resolved whichever dunder produced it., TestArithmeticNameFollowsPandas

### Community 125 - "TestLabelMetadataAtConstruction"
Cohesion: 0.31
Nodes (4): The constructor kwargs are a door of their own, and one was left open.…, TypeError: can only concatenate str (not "NoneType") to str., The sibling door, already closed - here so the pair stays closed., TestLabelMetadataAtConstruction

### Community 127 - "TestPickleWrittenBeforeTheFix"
Cohesion: 0.26
Nodes (5): A blob already on disk must load too, and that needs more than #35. Adding…, A state dict shaped like a blob written before `_name` was added. Both edits…, The heal must survive the next operation, not just the load. Without this, a…, None, because the name genuinely is not in those bytes. Healing the object must…, TestPickleWrittenBeforeTheFix

### Community 128 - "TestNanFreqIsNotLaundered"
Cohesion: 0.38
Nodes (3): A NaN rate must not become a fabricated healthy number. Reaches a NaN rate…, A real declared rate must survive an index-preserving transform., TestNanFreqIsNotLaundered

### Community 130 - "TestReinitHasOneDoor"
Cohesion: 0.24
Nodes (7): _calls_in_own_scope(), Yield the `ast.Call` nodes belonging to `node` itself. A flat `ast.walk`…, `super(TimeSeriesData, self).__init__` may appear in exactly one place. A…, Functions in core.py that re-initialise self through pandas. Parsed, not…, The scan must attribute a call to its *nearest* enclosing function. A flat…, Guards the scan itself against silently matching nothing. An assertion that a…, TestReinitHasOneDoor

### Community 134 - "TestAttrsIsolation"
Cohesion: 0.29
Nodes (4): attrs must be copied, never shared - pandas deep-copies it., A shallow dict copy passes the test above and fails this one. pandas'…, The emptiness guard must not invent a dict where none was set., TestAttrsIsolation

### Community 135 - "TestFlagsAssignmentAssumption"
Cohesion: 0.20
Nodes (5): Why `_carry_identity` may assign the flag rather than AND it. pandas 2.3.3's…, `_copy_metadata_from_basetseries` accepts anything with `.times`/`.data`, so a…, Assignment, not AND - the direction only a direct call can reach. Written…, An operation that cannot keep the declaration must change nothing. Checked…, TestFlagsAssignmentAssumption

## Ambiguous Edges - Review These
- `LowessOutlierFilter.py` → `baseTs Package README`  [AMBIGUOUS]
  baseTs/README.md · relation: conceptually_related_to
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
- `notch_filter()` → `notch_filter(freq, quality=30) (documented instance method)`  [AMBIGUOUS]
  docs/API.md · relation: conceptually_related_to
- `highpass_filter()` → `highpass_filter(cutoff, order=4) (documented instance method)`  [AMBIGUOUS]
  docs/API.md · relation: conceptually_related_to
- `bandpass_filter()` → `bandpass_filter(low_cutoff, high_cutoff, order=4) (documented instance method)`  [AMBIGUOUS]
  docs/API.md · relation: conceptually_related_to

## Knowledge Gaps
- **60 isolated node(s):** `Why this is a separate decision from #20, and what the issue left open`, `The stamp gains a third element`, `The comparison`, `Order of checks`, `Eager release on derivation` (+55 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `LowessOutlierFilter.py` and `baseTs Package README`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
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