# Graph Report - baseTs  (2026-09-03)

## Corpus Check
- 56 files · ~150,616 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2068 nodes · 3660 edges · 153 communities (138 shown, 15 thin omitted)
- Extraction: 93% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 233 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3b5775b8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- TestRelativeBandPower
- utils.py
- LowessOutlierFilter
- TestOutlierFilterSurvivesDerivation
- AdaptiveLowessFilter
- baseTs API Documentation
- baseTs User Guide
- TestBaseTsInitialization
- .__init__
- conftest.py
- TestInvalidationOnDerivation
- exgaussian.py
- _PlotAccessor
- baseTs
- validate_finite_data
- TestHistoryInvariantHoldsEverywhere
- TestMathematicalOperations
- TestButterpassAt
- TestLabelMetadataSurvivesDerivation
- TestFilteringOperations
- ValueError
- test_pandas_compat.py
- .__init__
- parametrize
- test_lag_conversion_guards.py
- TestNoInterpolationAcrossAGap
- Derived `freq` Implementation Plan
- test_gap_preservation.py
- TestPandasEnhancedMethods
- test_core.py
- TestReadIsPureAndDerivationReleases
- TestPandasIntegration
- Bandpass Filter Pipeline (bp_2: 0.2Hz)
- baseTs Example Signal Processing Figure
- Example 1 Signal Processing Plot
- bandpass_filter
- test_lowess_backend.py
- Design
- test_plot_accessor.py
- test_utils.py
- TestMetadataPropagation
- ._enhanced_process_with_flags
- TestWindowGuard
- FilterConfig
- TestEffectiveFrequency
- TestInvalidationOnInPlaceIndexChange
- TestBaseTsConversionPreservesMetadata
- ._wrap_result_as_basets
- TestMetadataRegistry
- _FinalizingWindow
- TestInheritedPandasInplaceMethods
- test_qc_plot.py
- TestHistoryNoneSurvivesRealOperations
- TestDerivationPathsAgree
- TestFiltersRejectNanFreq
- TestArithmeticOperators
- identity_of
- Carrying pandas' identity fields across derivation (#35, #39)
- time_to_idx
- test_filters.py
- ValidationError
- TestTypePreservation
- TestIndexMutationsWithNoHookAtAll
- TestTheStampIsNotLaunderable
- test_identity_propagation.py
- TestBaseTsFiltering
- _freq_token
- idx_to_time
- Derived `freq`: closing #29, #31 and #23
- TestDeepCopyIndependence
- TestTheInvalidParameterContractIsComplete
- plot_fft_power
- test_derived_lowess_invalidation.py
- InvalidParameterError
- test_plot_error_propagation.py
- test_user_guide_examples.py
- plotting.py
- test_conversion_preserves_metadata.py
- test_data_stamp_invalidation.py
- .bandpass_at
- TestHistoryNoneGuard
- .freq
- TestRejectionMessagesNameTheRealLimit
- shift_timeseries
- _complete_positional_slots
- TestTheDisplayBoundsAreValidatedBeforeDrawing
- test_enhanced_methods.py
- TestEveryBandpassEntryPointRejectsABadLowerEdge
- TestDuplicateLabelRefusal
- TestTheGuardsAreInertOnValidInput
- .test_augmented_assignment_is_still_in_place
- TestPlotting
- parametrize
- TestNonFiniteInput
- TimeSeriesData
- .test_invalid_parameter_type_raises_valueerror
- _degenerate_freq_ts
- compute_fft_power
- _DuckSeries
- TestArgumentOrder
- parametrize
- TestTheStamp
- TestLabelMetadataAtConstruction
- TestTheValidatedValueIsTheOneThatGetsFiltered
- TestInplaceMethodsPreserveIdentity
- .highpass_at
- TestTheOffsetPairStaysCoherent
- TestTheOutcomeCensusIsComplete
- TestLegacyPickles
- test_the_legend_label_keeps_the_callers_own_formatting
- _validate_display_rate
- TestInPlaceValueWrites
- bad_rate_ts
- TestDeclarationLifecycle
- TestNoWriteThrough
- zscale
- seeded
- _ExtendedForPickling
- _positional_property
- TestArithmeticNameFollowsPandas
- TestValuesEquality
- TestInterpToHzGrid
- TestPickleWrittenBeforeTheFix
- TestNanFreqIsNotLaundered
- TestInterpToHzRejections
- TestReinitHasOneDoor
- TestInvalidationThroughCreateNewWithData
- fixture
- from_df
- TestAttrsIsolation
- TestFlagsAssignmentAssumption
- test_series_freq.py
- parametrize
- TestTheStampIsNotLaunderable
- TestValuePreservingDerivationsKeepBoth
- .test_a_deliberately_extended_instance_registry_is_kept
- _detach_shared_metadata
- .test_the_stale_fit_is_not_drawn
- .test_naming_one_parameter_leaves_the_others_alone
- test_an_exhausted_iterable_band_is_still_rejected_cleanly
- setter
- Exception
- TestWindowingParamsAreGuardedLikeTheBandEdges
- fixture
- TestNonScalarBandEdgesKeepTheContract
- float64
- ValueError
- parametrize

## God Nodes (most connected - your core abstractions)
1. `baseTs` - 330 edges
2. `TimeSeriesData` - 132 edges
3. `LowessOutlierFilter` - 76 edges
4. `FilterConfig` - 49 edges
5. `ValidationError` - 42 edges
6. `plot_fft_power()` - 39 edges
7. `InvalidParameterError` - 39 edges
8. `bandpass_filter()` - 33 edges
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
- `baseTs API Documentation` --references--> `baseTs`  [EXTRACTED]
  docs/API.md → baseTs/core.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **baseTs Documentation Suite** — readme_doc, docs_user_guide_doc, docs_api_doc, docs_api_series_doc, docs_examples_doc, docs_changelog_doc, claude_devguide [EXTRACTED 1.00]
- **baseTs Signal Processing Pipeline Demonstration** — imgs_basets_example_figure, imgs_basets_example_raw_signal_with_spikes, imgs_basets_example_lowess_despiking, imgs_basets_example_bandpass_filter, imgs_basets_example_fft_power_spectrum [EXTRACTED 1.00]
- **LOWESS Despiking Workflow** — basets_core_basets_set_outlier_filter, basets_core_basets_filter_outliers, lowess_outlier_detection, basets_lowessoutlierfilter [EXTRACTED 1.00]
- **Enhanced Pandas Series Methods (v2.0.0 Migration)** — basets_core_basets_resample, basets_core_basets_interpolate_gaps, basets_core_basets_align_with, basets_core_basets_correlation_with, basets_core_basets_detect_outliers, basets_core_basets_rolling_mean, basets_core_basets_time_slice, basets_core_basets_get_statistics, basets_core_basets_get_frequency_content, basets_core_basets_shift_time [EXTRACTED 1.00]
- **baseTs Signal Processing Pipeline (despike -> lowpass filter -> rolling mean smoothing)** — imgs_example1_plot_raw_signal, imgs_example1_plot_despiked, imgs_example1_plot_filtered, imgs_example1_plot_smoothed [INFERRED 0.85]

## Communities (153 total, 15 thin omitted)

### Community 0 - "TestRelativeBandPower"
Cohesion: 0.14
Nodes (11): Tests for the relative_band_power / falff methods., Slow 0.05 Hz signal long enough to resolve the 0.01-0.1 Hz band., Method delegates correctly and returns a builtin float., The headline robustness property: an undetrended mean offset must not move the…, The documented pipeline produces the same answer., falff() defaults to the amplitude convention., details=True carries the white-noise null alongside the ratio., The window argument reaches get_frequency_content. (+3 more)

### Community 1 - "utils.py"
Cohesion: 0.08
Nodes (37): _is_unset(), True if a numeric argument was not supplied. The constructor uses np.nan as its…, Find the closest time in the timeseries to a target time in seconds. Args: sec:…, baseTs - A Python library for time series analysis, Created on Oct 19 2024 @author: stan@sympaticog.com, baseTs Package README, add_constant(), ClosestMatch (+29 more)

### Community 2 - "LowessOutlierFilter"
Cohesion: 0.17
Nodes (12): LowessOutlierFilter, ndarray, Apply LOWESS smoothing and outlier detection to the data. Parameters ----------…, Reject configurations whose local window is too small to smooth. LOWESS fits a…, Apply LOWESS smoothing to the data. Uses statsmodels' Cleveland LOWESS. Note…, Process a single iteration of outlier detection., Validate and convert input data to a NumPy array., Validate and obtain the time index. (+4 more)

### Community 3 - "TestOutlierFilterSurvivesDerivation"
Cohesion: 0.16
Nodes (9): _cleared_filter(), A series whose filter has been cleared - the state issue #33 reports., outlier_filter is always a filter" must hold on every derived object. Without…, __finalize__ copies the parent's None; the chokepoint must fix it., zscale() routes through _create_new_with_data, not __finalize__., info() reads outlier_filter.config to print the filter block., The filter itself is read off the object, so it died here too. Long enough for…, The deliberate boundary of a chokepoint fix, pinned so it is visible.… (+1 more)

### Community 4 - "AdaptiveLowessFilter"
Cohesion: 0.11
Nodes (18): AdaptiveLowessFilter, demo_adaptive_lowess(), LowessConfig, ndarray, Calculate optimal segment length based on dominant frequency content., Configuration parameters for adaptive LOWESS filtering., Calculate overlap ratio based on signal complexity., Calculate LOWESS fraction based on frequency content and noise. (+10 more)

### Community 5 - "baseTs API Documentation"
Cohesion: 0.12
Nodes (17): Compute the first difference of the timeseries., Get comprehensive statistics for the time series. Returns: Dictionary…, Compute the relative power (or amplitude) in a frequency band. This is the…, Fractional amplitude of low-frequency fluctuations (fALFF). Convenience wrapper…, Plot the power spectrum of the timeseries using enhanced frequency analysis.…, Applies a user-provided function to the data vector. Note: the times vector is…, BandPowerResult, Detailed breakdown of a relative band power computation. Attributes: ratio: The… (+9 more)

### Community 6 - "baseTs User Guide"
Cohesion: 0.09
Nodes (28): Apply a lowpass filter at the specified cutoff frequency. Args: cutoff: Lowpass…, Apply a lowpass filter to the data. Args: cutoff: Lowpass cutoff frequency in…, Set outlier filter parameters. Parameters ---------- params : dict, optional…, Apply the outlier filter to the signal. Args: inplace (bool, optional): If…, Apply a rolling mean to the data. Args: window: Size of the rolling window…, Apply a rolling standard deviation to the data., Apply a rolling median to the data., Apply a rolling maximum to the data. (+20 more)

### Community 7 - "TestBaseTsInitialization"
Cohesion: 0.17
Nodes (7): Tests for baseTs initialization and basic properties., Test initializing baseTs with data and times., Test initializing baseTs with data and frequency., Test initialization validation requirements., Test length and duration calculations., Test creating baseTs from DataFrame., TestBaseTsInitialization

### Community 8 - ".__init__"
Cohesion: 0.22
Nodes (6): _carries_metadata(), The type of `_UNSET`. Distinct so it can be annotated and matched., True if `data` is a source whose metadata a constructor should copy. Both…, Initialize TimeSeriesData object. Args: data: Array-like data or baseTs object…, Initialize default metadata values., _UnsetType

### Community 9 - "conftest.py"
Cohesion: 0.08
Nodes (29): Python Package CI Workflow, hypothesis, Matplotlib, moepy, NumPy, Pandas, psutil, pytest (+21 more)

### Community 10 - "TestInvalidationOnDerivation"
Cohesion: 0.14
Nodes (6): rolling() routes through _FinalizingWindow, not __finalize__ directly. A window…, A different index means neither attribute describes the object., Stricter than the `freq` token, deliberately. `_freq_token` is (len, first,…, Invalidation is about the index, not about deriving at all. `+ 0.0` rather than…, The rule is index equality, not "was a slicing method called"., TestInvalidationOnDerivation

### Community 11 - "exgaussian.py"
Cohesion: 0.19
Nodes (20): calculate_aic(), calculate_bic(), chi_square_test(), exg_initial_guess(), ExGaussianFit, FitStatistics, get_exg_fits(), iterative_exgaussian_fit() (+12 more)

### Community 12 - "_PlotAccessor"
Cohesion: 0.12
Nodes (8): _PlotAccessor, Axes, Callable proxy backing ``baseTs.plot``. ``plot`` used to be a plain alias for…, Plot the timeseries as a line plot. Quick and dirty visualization., Line plot, or the pandas plotting accessor. Calling it is the historical baseTs…, Plot this timeseries against one or more other timeseries. e.g. for QC,…, Plot a histogram of the timeseries., Plot a lag plot of the timeseries.

### Community 13 - "baseTs"
Cohesion: 0.04
Nodes (38): baseTs, Interpolate missing values in the data., Basic data class to hold a timeseries and data. Built on pandas Series…, Compute the FFT power of the timeseries., Get the peaks in the timeseries. Returns a list of the indices of the peaks., Set or updates the timestamp offset., Keep pandas operations returning baseTs rather than downgrading. Without this,…, Calculates the length of the data. Returns: int: Length of the data (+30 more)

### Community 14 - "validate_finite_data"
Cohesion: 0.07
Nodes (31): _complex_data_message(), The rejection text for complex sample values (issue #43). `what` describes the…, Reject sample values an FFT cannot produce a meaningful spectrum from. The…, validate_finite_data(), parametrize, _FreqStub, The guard rejects bad values, not unfamiliar dtypes., Object arrays are checked, not waved through. np.isfinite raises TypeError on… (+23 more)

### Community 15 - "TestHistoryInvariantHoldsEverywhere"
Cohesion: 0.07
Nodes (21): parametrize, Tests for lowess_detrend, centred on its inplace=False purity contract., Guard for the purity tests below. They assert that self.data survives…, Issue #6: the caller's object must survive a non-inplace detrend., Issue #6: detrending must not rewrite the caller's filter config.…, The inplace path removes the trend and reports the fit it used., Detrending subtracts a robust trend from the *original* data. The spikes are…, Regression guard for the is_outlier_filtered decoupling. lowess_detrend… (+13 more)

### Community 16 - "TestMathematicalOperations"
Cohesion: 0.12
Nodes (9): Test absolute value operations., Test method chaining works correctly., Test that arithmetic operations return baseTs objects., Test mathematical operations with pandas Series foundation., Test z-scaling operations., Test range normalization operations., Test centering operations., Test scaling operations. (+1 more)

### Community 17 - "TestButterpassAt"
Cohesion: 0.12
Nodes (13): Every metadata slot must come out where bandpass_at puts it. Asserted against…, Delegation is deliberate: the entry reads bandpass, not butterworth. No caller…, butterpass_at must actually run, and must mean what its name says (#27). It…, Amplitude of one tone by projection, so no FFT bin has to line up., The issue's reproduction: this raised TypeError on every call., The band kept must be [hp_freq, lp_freq], not its mirror image. A positional…, An alias that computes something else is not an alias., A source carrying a non-default value in every seedable metadata slot. The… (+5 more)

### Community 18 - "TestLabelMetadataSurvivesDerivation"
Cohesion: 0.20
Nodes (8): parametrize, signal_name and last_process are always strings" - same defect class. Issue #33…, A number is as fatal to `name + " " + process` as a None is. On the…, The live crash: TypeError: unsupported operand 'NoneType' + 'str'., Restoring a default must not rewrite a name someone chose. Deliberately already…, The normaliser must restore a default, never impose one. A fix that assigned…, TestAConfiguredFilterIsNotReplaced, TestLabelMetadataSurvivesDerivation

### Community 19 - "TestFilteringOperations"
Cohesion: 0.14
Nodes (8): Test filtering operations., Test lowpass filtering., Test highpass filtering., Test bandpass filtering., Test Savitzky-Golay filtering., Test Gaussian filtering., Test chaining multiple filters., TestFilteringOperations

### Community 20 - "ValueError"
Cohesion: 0.16
Nodes (9): array, Compute the cumulative sum of the timeseries., Create a copy of the baseTs object. Args: deep: Whether to make a deep copy…, Detrend the data by subtracting a robust LOWESS fit. The trend is the LOWESS…, Remove trend from the signal using various detrending methods. Args: method:…, Set specific indices to NaN and interpolate the missing values. Args: indices:…, Resample onto a uniform grid at exactly new_freq. The grid is built from the…, Interpolate data to a uniform sampling grid. If new_grid is not specified, use… (+1 more)

### Community 21 - "test_pandas_compat.py"
Cohesion: 0.06
Nodes (20): fixture, parametrize, Regression tests for pandas 2.x/3.x compatibility. Each test here corresponds…, baseTs.duration() shadowed the guarded TimeSeriesData.duration()., get_statistics() calls duration(), so it inherited the crash., `freq is np.nan` only matched the one np.nan object., Previously this silently produced an all-NaN time index instead of raising,…, Deriving freq from the times array must still work. NB: the derived value is… (+12 more)

### Community 22 - ".__init__"
Cohesion: 0.17
Nodes (10): ndarray, Initialize baseTs object as pandas Series with time-series metadata. Args:…, Get the data values as numpy array (backward compatibility)., Set the data values (backward compatibility)., Get the time values as numpy array (backward compatibility)., Set the time values (backward compatibility)., Re-initialise this object's data and index, keeping everything else. The single…, Update Series data while preserving metadata and handling length changes. (+2 more)

### Community 23 - "parametrize"
Cohesion: 0.12
Nodes (8): parametrize, pandas supports `for window in ts.rolling(3): ...`, yielding each window as its…, The contract is behavioural, not identity. FilterConfig is frozen and…, Independence must not cost the config: the values still carry over., Arithmetic returns via _wrap_result_as_basets, which assigned every metadata…, pandas implements `ts += 1` by calling __add__ and keeping only the values,…, _create_new_with_data omitted outlier_filter from the attributes it carries, so…, ts is uniformly sampled, so every op here should agree with it.

### Community 24 - "test_lag_conversion_guards.py"
Cohesion: 0.14
Nodes (12): lag_plot(), Generate a lag plot for a given timeseries object and lag., get_lags(), Get lag values in both seconds and indices. Args: lag: Lag value lag_unit: Unit…, _degenerate(), Guards on the two lag-conversion primitives (issue #32). `time_to_idx` and…, Every timestamp identical, so the derived rate is NaN. This is the object from…, The rate must be rejected where it enters the conversion. Each of these fails… (+4 more)

### Community 25 - "TestNoInterpolationAcrossAGap"
Cohesion: 0.32
Nodes (4): An input gap is a boundary, not something to interpolate through. Filling the…, It must not be pulled toward the first valid sample after the gap., Two gaps, three segments; an outlier in each must stay local., TestNoInterpolationAcrossAGap

### Community 26 - "Derived `freq` Implementation Plan"
Cohesion: 0.18
Nodes (10): Before opening the PR, Commit boundaries, Derived `freq` Implementation Plan, Global Constraints, Task 1: Index token and derivation hardening, Task 2: Make the legacy freq tests independent of freq storage, Task 3: The atomic switch — `freq` becomes a property, Task 4: Fix the `interpto_hz` grid (+2 more)

### Community 27 - "test_gap_preservation.py"
Cohesion: 0.09
Nodes (20): _gappy(), _nan_mask(), fixture, parametrize, _quiet(), Tests for issue #36: filter_outliers must not invent data in pre-existing gaps.…, Silent is the failure mode; the history entry should carry the count., bool('False') is True - every non-empty string is truthy. (+12 more)

### Community 28 - "TestPandasEnhancedMethods"
Cohesion: 0.11
Nodes (10): Test new pandas-enhanced methods., Test pandas-powered rolling mean., Test rolling standard deviation., Test time-based slicing., Test pandas resampling., Test cross-correlation between time series., Test outlier detection., Test gap interpolation. (+2 more)

### Community 29 - "test_core.py"
Cohesion: 0.10
Nodes (12): Unit tests for baseTs core functionality., Test data normalization functions., Test detrending functionality., Test trimming functionality., Tests for outlier detection functionality., Test setting outlier filter parameters., Test outlier filtering., Tests for baseTs data transformations. (+4 more)

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
Cohesion: 0.12
Nodes (14): bandpass_filter(), Apply a symmetric bandpass filter to the input data. Args: data: Input data…, `except ValueError -> raise InvalidParameterError` in filters now has a self-…, parametrize, All of these must raise; four of the seven previously did not. The negative,…, A message about ordering is useless without the two values in it., The asymmetry that made this bug position-dependent. `max(0.1, nan)` returns…, Nyquist must come from the effective rate, not the declared one. The filter… (+6 more)

### Community 36 - "test_lowess_backend.py"
Cohesion: 0.10
Nodes (12): Enum for specifying which tails to process in outlier detection., TailType, Enum, Tests for the statsmodels LOWESS backend of LowessOutlierFilter. Covers the…, The unslotted dataclass must not resurrect the attribute., The filter must work with moepy made unimportable., num_fits must keep its positional slot; the new knobs are keyword-only., Guard against the dependency creeping back in. (+4 more)

### Community 37 - "Design"
Cohesion: 0.11
Nodes (18): Behaviour changes, Deep copy and detachment, Design, Documentation, Eager release on derivation, Order of checks, Pickles written before this change, Problem (+10 more)

### Community 38 - "test_plot_accessor.py"
Cohesion: 0.10
Nodes (11): close_figures(), fixture, parametrize, Tests for the hybrid baseTs.plot accessor. `plot` was a plain alias for…, The historical spelling must be unchanged., The accessor is a property, so it must follow the preserved type., Each accessor plots its own data, not the parent's., TestAccessorSurvivesOperations (+3 more)

### Community 39 - "test_utils.py"
Cohesion: 0.05
Nodes (58): Compute the relative power (or amplitude) in a frequency band. This is the…, relative_band_power(), fixture, _all_four_entry_points(), _analytic_ts(), _gappy_ts(), lf_baseTsObj(), Unit tests for baseTs utility functions. (+50 more)

### Community 40 - "TestMetadataPropagation"
Cohesion: 0.08
Nodes (13): The __finalize__ concat special-case exists for nlargest/nsmallest's internal…, pandas' default __finalize__ assigns metadata by reference, so parent and child…, pandas' _inplace_method reindexes the result back to self before adopting it.…, TimeSeriesData never set outlier_filter despite declaring it in _metadata, so a…, Issue #11: the reported path, copy() rather than a pandas op., The accessor must not hand out the live config. Derived objects share one…, baseTs(ts) takes the conversion branch in TimeSeriesData.__init__, which…, The whole design rests on this: a frozen config plus a rebinding… (+5 more)

### Community 41 - "._enhanced_process_with_flags"
Cohesion: 0.10
Nodes (11): Apply a Gaussian filter to the data. Args: sigma: Standard deviation for…, Apply a Savitzky-Golay filter to the signal. Args: window_length: Length of the…, Helper method to update object flags., Enhanced processing method that handles both data and time modifications. Args:…, Normalize the data to a specified range. Args: target_min: Minimum value of…, Center the data around zero (remove mean). Args: inplace: If True, modifies…, Scale the data by a constant factor. Args: factor: Scaling factor inplace: If…, Take absolute value of the data. Args: inplace: If True, modifies existing… (+3 more)

### Community 42 - "TestWindowGuard"
Cohesion: 0.10
Nodes (10): parametrize, A perfectly-fit signal drives MAD to zero; z_threshold then means nothing, so…, A window of <= 3 points makes LOWESS interpolate the data exactly. The fit is…, The same default frac that is fine at n=500 is degenerate at n=20., The suggested frac must actually satisfy the guard., k == 4 must be allowed: the guard rejects degenerate, not merely small., A run starting at exactly k == 4 falls to k == 3 after one removal. The loop…, NaNs do not count towards the window: 500 slots, 10 real points. (+2 more)

### Community 43 - "FilterConfig"
Cohesion: 0.14
Nodes (11): FilterConfig, Configuration parameters for the LowessOutlierFilter. Attributes ----------…, Initialize the LowessOutlierFilter with filtering parameters. Parameters…, The old fill-everything behaviour stays reachable for anyone relying on it., np.asarray drops a mask and exposes the payload underneath., TestMaskedArrayGapsAreSeen, TestOptOut, config.it must reach statsmodels, not be hardcoded. (+3 more)

### Community 44 - "TestEffectiveFrequency"
Cohesion: 0.09
Nodes (12): n samples span n-1 intervals., rolling() does not call __finalize__, so freq is recomputed from the index - it…, nlargest(3) is excluded from the op list above - it is the one op there that…, #19: resample changes the time base, so the carried freq described the old…, An explicitly supplied freq may legitimately disagree with the times it was…, #19: arithmetic on two different time bases must derive from the union index…, #19: interpto_samples assigned n/duration over the corrected derivation., #19: same n/duration error as interpto_samples. (+4 more)

### Community 45 - "TestInvalidationOnInPlaceIndexChange"
Cohesion: 0.15
Nodes (6): The index can change without any derivation at all., `.index` is pandas' own setter, and `.times` is not the only door., The inplace branch calls pd.Series.__init__ directly, bypassing…, The data setter rebuilds the index when the length changes., Same length keeps the index; equal values keep the fit (#40). Assigning zeros…, TestInvalidationOnInPlaceIndexChange

### Community 46 - "TestBaseTsConversionPreservesMetadata"
Cohesion: 0.09
Nodes (12): parametrize, The conversion branch takes its index from the source, so a `times` argument…, Preserving what was not passed must not ignore what was. The fix distinguishes…, `history=None` is the documented way to ask for a fresh entry. Folding it into…, `baseTs(ts)` is a conversion, not a reset., The sharpest edge: a converted object claimed to be freshly made. Verbatim, not…, #15's guard, which was the only name that already worked., Assigned through the public properties, these were cleared to None. Read back… (+4 more)

### Community 47 - "._wrap_result_as_basets"
Cohesion: 0.08
Nodes (12): Helper method to update history and last_process. Normalises rather than…, Addition operation returning a baseTs object., Right addition operation returning a baseTs object., Subtraction operation returning a baseTs object., Right subtraction operation returning a baseTs object., Multiplication operation returning a baseTs object., Right multiplication operation returning a baseTs object., Division operation returning a baseTs object. (+4 more)

### Community 48 - "TestMetadataRegistry"
Cohesion: 0.40
Nodes (3): `_metadata` must extend pandas' list rather than replace it., Every name pandas declares must still be carried. Asserted against…, TestMetadataRegistry

### Community 54 - "_FinalizingWindow"
Cohesion: 0.16
Nodes (8): _FinalizingWindow, Any, See _FinalizingWindow: rolling()/expanding()/ewm() never call __finalize__., Rolling window whose aggregations propagate metadata - see _FinalizingWindow., Expanding window whose aggregations propagate metadata - see _FinalizingWindow., EWM window whose aggregations propagate metadata - see _FinalizingWindow., Wraps a pandas window object (Rolling/Expanding/ExponentialMovingWindow) so its…, Python looks up dunder methods on the type, bypassing __getattr__, so this…

### Community 55 - "TestInheritedPandasInplaceMethods"
Cohesion: 0.18
Nodes (5): `inplace=True` on an inherited pandas method swaps the block manager. pandas…, The reported crash, reachable without any baseTs method at all., The silent variant: same length, every position moved., These keep the positions, so the index rule must not fire. On this fixture they…, TestInheritedPandasInplaceMethods

### Community 56 - "test_qc_plot.py"
Cohesion: 0.20
Nodes (13): _close_figures(), fixture, parametrize, Tests for filter_outliers(qcplot=True). The QC plot exists to show the filter's…, The plotting path must not become a second route to the #6 bug., Asking for a plot must not change what the filter returns., spiked_ts(), test_lowess_fit_trace_is_present() (+5 more)

### Community 57 - "TestHistoryNoneSurvivesRealOperations"
Cohesion: 0.26
Nodes (5): The None-history guard must hold on the paths users actually take. Guarding…, zscale() dies in _create_new_with_data's history.copy()., info() iterates history; None raised TypeError., __finalize__ turns a propagated None into a list., TestHistoryNoneSurvivesRealOperations

### Community 58 - "TestDerivationPathsAgree"
Cohesion: 0.18
Nodes (4): fixture, Issue #29's acceptance test. The same index change had two answers depending on…, A value-sorted series has a non-monotonic index and no honest rate. The carried…, TestDerivationPathsAgree

### Community 59 - "TestFiltersRejectNanFreq"
Cohesion: 0.27
Nodes (4): A degenerate time base must not filter to silent all-NaN output.…, butterpass_at was absent from this family because it never ran (#27). It…, The guard must not disturb an ordinary series., TestFiltersRejectNanFreq

### Community 60 - "TestArithmeticOperators"
Cohesion: 0.20
Nodes (5): parametrize, The operator dunders do not route through __finalize__. `__add__` and friends…, A scalar cannot change the index, so the index rule must not fire. Zero, so the…, `ts += x` cannot change ts's index, so the index rule never fires.…, TestArithmeticOperators

### Community 61 - "identity_of"
Cohesion: 0.18
Nodes (7): identity_of(), The bar is pandas' own behaviour, not an invented one. If a future pandas stops…, The three fields as one comparable tuple., The check must hand back what it built, not drain the caller's. Building a…, `ts += 1` keeps the target's own identity, as stock pandas does. Pinned because…, TestIdentitySurvivesDerivation, TestInplaceArithmeticIsUnaffected

### Community 62 - "Carrying pandas' identity fields across derivation (#35, #39)"
Cohesion: 0.10
Nodes (19): Carrying pandas' identity fields across derivation (#35, #39), Decisions taken, Deliberately not in scope, Design, Half A — `_name` joins `_metadata`, Half B, Group 1 — one door for the identity triple, Half B, Group 2 — collapse three doors into one, Making a tenth site fail loudly (+11 more)

### Community 63 - "time_to_idx"
Cohesion: 0.11
Nodes (14): Convert a time value to an index. Args: lag_secs: Time in seconds freq:…, time_to_idx(), Existing code that names the domain type must be unaffected., Both are public utilities, so neither can rely on its caller., It does not divide, so it dies silently instead: `int(0.5 * 0.0)` is a…, `validate_lag` never gets to speak, because `get_lags` converts first. The rate…, A string lag dies on main with `can't multiply sequence by non-int`. It must…, float(10**400) raises OverflowError, which is neither TypeError nor ValueError… (+6 more)

### Community 64 - "test_filters.py"
Cohesion: 0.20
Nodes (8): register, _DeclaresOneHz, _LiesAboutDivision, Unit tests for baseTs.filters parameter validation., Registers as a Real but cannot become one. numbers.Real is a registrable ABC,…, A Real that converts to 1.0 and supports nothing else. Registers, coerces,…, Converts to 1.0 but divides to something else entirely. The nastier half of the…, _UnconvertibleReal

### Community 65 - "ValidationError"
Cohesion: 0.10
Nodes (21): FilterError, Exception, Base exception for filter-related errors., Base exception for time series related errors., Exception raised for validation errors. Also a ValueError, because a rejected…, Validate lag parameters. Args: lag: Lag value lag_idx: Lag index lag_unit: Unit…, TimeSeriesError, validate_lag() (+13 more)

### Community 66 - "TestTypePreservation"
Cohesion: 0.20
Nodes (5): The point of preserving the type is keeping the domain methods., The documented pattern: a pandas op followed by a baseTs op., pandas builds subclasses as _constructor(values, index=...)., pandas looks this up on the class; a plain method breaks that., TestTypePreservation

### Community 67 - "TestIndexMutationsWithNoHookAtAll"
Cohesion: 0.22
Nodes (3): The doors that defeated the write-side design. These reach past `__finalize__`,…, The third `pd.Series.__init__` site, and the one an explicit audit for that…, TestIndexMutationsWithNoHookAtAll

### Community 68 - "TestTheStampIsNotLaunderable"
Cohesion: 0.22
Nodes (5): A copy must move the (value, index) pair, never re-stamp it. Any path that…, The discriminating case for laundering. interpolate_gaps routes through…, Memory, not correctness: the getter already reads a slice as None. Without this…, The behavioural form of the laundering check. Starting from a *valid* fit is…, TestTheStampIsNotLaunderable

### Community 69 - "test_identity_propagation.py"
Cohesion: 0.15
Nodes (12): _apply_duplicate_label_declaration(), deepcopy_metadata_value(), _raise_duplicate_label_refusal(), Deep-copy a `_metadata` entry, reaching inside a positional slot. Both `copy()`…, Reject an index the declaration could not survive, before anything moves.…, The one wording for both the pre-check and the restore arm. The labels are…, Carry `allows_duplicate_labels`, diagnosing pandas' refusal. Setting the flag…, _refuse_undeclarable_index() (+4 more)

### Community 70 - "TestBaseTsFiltering"
Cohesion: 0.22
Nodes (5): Tests for baseTs filtering functionality., Test highpass filter., Test bandpass filter., Test Savitzky-Golay filter., TestBaseTsFiltering

### Community 71 - "_freq_token"
Cohesion: 0.29
Nodes (5): _freq_token(), Fingerprint an index for the purpose of sampling-rate derivation. Deliberately…, The token must be exactly the inputs _calculate_effective_frequency reads. That…, And must not: the derived rate is unchanged, so the token is right.…, TestFreqToken

### Community 72 - "idx_to_time"
Cohesion: 0.12
Nodes (10): _coerce_lag(), idx_to_time(), Convert a lag to a float, or say which argument is wrong. validate_lag is the…, Convert an index to a time value. Args: lag_idx: Index to convert freq:…, #32 names this one explicitly: `ZeroDivisionError: float division by zero` says…, Checking the operands is not the same as checking the result. Both arguments…, The result check must not swallow the NaN index that validate_lag diagnoses…, The check is finiteness, not a magnitude policy. This is absurd input, but it… (+2 more)

### Community 73 - "Derived `freq`: closing #29, #31 and #23"
Cohesion: 0.14
Nodes (13): 1. The `freq` property, 2. Propagation, 3. Validation at production sites (#31), 4. `interpto_hz` (#23), 5. Deletions, 6. Edge cases, Approach, Consequences (+5 more)

### Community 74 - "TestDeepCopyIndependence"
Cohesion: 0.29
Nodes (3): `copy(deep=True)` must hand back arrays the parent does not share. Both copy…, The constructor types this as np.array, so a list check is not enough., TestDeepCopyIndependence

### Community 75 - "TestTheInvalidParameterContractIsComplete"
Cohesion: 0.31
Nodes (5): Every known bad input raises InvalidParameterError, enumerated. The CHANGELOG…, Every known bad input raises, with the message its own guard makes., The number in the prose is asserted against the table. Adding a case without…, A fragment true of another case's message pins nothing. Three fragments were…, TestTheInvalidParameterContractIsComplete

### Community 76 - "plot_fft_power"
Cohesion: 0.14
Nodes (14): plot_fft_power(), Plots the power spectrum of a timeseries signal using enhanced FFT with…, setup_plot used to run before the guard, so every failure left a figure. In a…, A caller passing ax= gets it back as they left it, not titled and annotated., The band check ran after the spectrum was already plotted. Ordering matters for…, Pins the one documented hole in the "all ValueError" contract. Pre-existing and…, Above Nyquist, so the frequency mask is empty., test_a_range_selecting_no_bins_raises() (+6 more)

### Community 77 - "test_derived_lowess_invalidation.py"
Cohesion: 0.20
Nodes (7): _close_figures(), filtered(), fixture, Tests for #20: lowess_fit and outlier_indices on derived objects. `lowess_fit`…, A filtered series carrying a real fit and a real outlier record., Invalidation must not disturb the methods whose job is to produce a fit., TestProducersStillSetTheFit

### Community 78 - "InvalidParameterError"
Cohesion: 0.12
Nodes (29): ArrayLike, _as_real_float(), FilterConfig, highpass_filter(), interpolate_missing_values(), InvalidParameterError, lowpass_filter(), notch_filter() (+21 more)

### Community 79 - "test_plot_error_propagation.py"
Cohesion: 0.12
Nodes (15): Tests for issue #34: plot_fft_power must raise, not draw the error.…, ts.plot_fft_power() is the path users actually call., The consequence users actually meet, and the fix the docs name. Since #36…, Pins that moving the computation above setup_plot did not break it., Pins coerce_real_scalar's ValueError arm, which mutation testing found bare.…, The issue's reproduction. The docstring's `Raises:` becomes true., #28's guard reaches the caller instead of becoming on-plot text., test_a_bad_rate_raises_rather_than_drawing_the_error() (+7 more)

### Community 80 - "test_user_guide_examples.py"
Cohesion: 0.29
Nodes (9): fenced_python_under(), Executable pins on the worked examples in docs/USER_GUIDE.md. The example is…, The first ```python block after the given markdown heading line., Execute a doc block and return its namespace. The guide's opening block does…, Issue #44: a self-referential dict literal and a cutoff at Nyquist. The Nyquist…, The `quality_score < 0.95` branch, which the example's own data never takes.…, run_example(), test_example_4_enhanced_cleaning_branch_completes() (+1 more)

### Community 81 - "plotting.py"
Cohesion: 0.29
Nodes (12): hist(), plot(), plot_series(), array, Axes, qc_plot(), Plots a histogram of a timeseries., Plots multiple timeseries on the same plot. (+4 more)

### Community 82 - "test_conversion_preserves_metadata.py"
Cohesion: 0.14
Nodes (10): carrying(), fixture, Converting a series must not reset what it was carrying (issue #57).…, The conversion branch was gated on `.times` and `.data`. Only `baseTs` defines…, An empty carried history must not become a fabricated creation entry. The…, A series with every metadata value moved off its default., The ordinary path must still start from defaults, not from nothing. Nothing is…, TestAnEmptyHistoryIsAHistory (+2 more)

### Community 83 - "test_data_stamp_invalidation.py"
Cohesion: 0.19
Nodes (10): _close_figures(), filtered(), gapped(), fixture, Tests for #40: lowess_fit and outlier_indices on an object whose values…, Both producers assign the data first and the slot second. That ordering is now…, A filtered series carrying a real fit and a real outlier record., Filtered, with a pre-existing NaN the filter leaves alone (#36). (+2 more)

### Community 84 - ".bandpass_at"
Cohesion: 0.29
Nodes (4): Apply a bandpass filter to the signal at specified low-pass and high-pass…, Apply a bandpass filter between two cutoff frequencies (alias for bandpass_at).…, Apply a Butterworth bandpass filter (alias for bandpass_at). Args: hp_freq:…, bandpass_filter(low_cutoff, high_cutoff, order=4) (documented instance method)

### Community 85 - "TestHistoryNoneGuard"
Cohesion: 0.29
Nodes (4): A `history` of None must not crash the next operation (issue #22). __finalize__…, The superclass guard is hasattr-only, so None slips past it too., The guard must not discard a history that is genuinely present., TestHistoryNoneGuard

### Community 86 - ".freq"
Cohesion: 0.25
Nodes (5): setter, The sampling rate in Hz, derived from the index unless declared. An explicitly…, Declare an explicit sampling rate against the current index. The single…, String representation of TimeSeriesData., Derive the sampling frequency from the time index. Returns NaN rather than…

### Community 87 - "TestRejectionMessagesNameTheRealLimit"
Cohesion: 0.32
Nodes (4): A message that states no number sends the caller round the loop twice. At…, Pull the Nyquist figure the message quotes., Execute the remedy rather than asserting the string., TestRejectionMessagesNameTheRealLimit

### Community 88 - "shift_timeseries"
Cohesion: 0.16
Nodes (11): Shift a time series by a lag value. Args: ts: Time series object with data and…, shift_timeseries(), parametrize, One argument, one exception type. `validate_lag` raises ValidationError for…, Unchanged, and deliberately so: `idx_to_time` divides rather than truncating,…, One argument, one exception type, whichever mode it arrives in. Guarding only…, Two bad arguments must produce the same first complaint in either mode. Left to…, Coercion must not start *accepting* what validate_lag rejects: a Decimal… (+3 more)

### Community 89 - "_complete_positional_slots"
Cohesion: 0.18
Nodes (10): _complete_positional_slots(), _drop_stale_positional_metadata(), Whether `obj`'s live values are still the ones `stamp` recorded. O(n) on every…, Release a positional slot whose index or values no longer match. Runs on…, Bring a positional slot restored from a pickle up to the current shape.…, Snapshot `obj`'s values for a positional slot to be checked against. A…, Restore from a pickle, healing a blob that predates `_name`. Adding '_name' to…, _values_match() (+2 more)

### Community 90 - "TestTheDisplayBoundsAreValidatedBeforeDrawing"
Cohesion: 0.14
Nodes (7): The frequency bounds reach ax.set_xlim, which rejects NaN and Inf. An infinite…, ValueError, matching every other bound failure in this function. '30' and True…, NaN is the documented public sentinel for max_rate - not an error., min_rate has no sentinel, so NaN is simply invalid there., Pins the shared door's ndarray branch, which mutation testing found bare.…, The other half of that branch: 0-d arrays convert alike on both majors., TestTheDisplayBoundsAreValidatedBeforeDrawing

### Community 91 - "test_enhanced_methods.py"
Cohesion: 0.18
Nodes (6): Test edge cases and error handling., Test handling of empty data., Test handling of single data point., Test handling of constant data., Test invalid parameter handling., TestEdgeCases

### Community 92 - "TestEveryBandpassEntryPointRejectsABadLowerEdge"
Cohesion: 0.43
Nodes (3): The contract must hold on all three names, on the axis it is about. #28's…, Reachable at all only since #27, which was dead before it., TestEveryBandpassEntryPointRejectsABadLowerEdge

### Community 93 - "TestDuplicateLabelRefusal"
Cohesion: 0.12
Nodes (11): _Flags, The restore arm, exercised directly. Since the pre-commit check landed, no path…, A stand-in whose flag setter raises what the caller chooses., Raising pandas' real class, not a look-alike. An earlier version of this test…, An error that names a remedy is code; the remedy must run. This repo shipped an…, The remedy that was there before, and why it was wrong. `ts.data = ...`,…, A diagnosis must not become the payload. Naming every duplicated label built an…, Bounding the message must not stop it being useful. (+3 more)

### Community 94 - "TestTheGuardsAreInertOnValidInput"
Cohesion: 0.14
Nodes (8): `lag_secs=inf` used to ride out into the returned dict and the plot title,…, Pinned so a future guard cannot quietly change what a good call returns. The…, 99.99999999999999 Hz gives 49, not 50. Guarding the rate must not be mistaken…, #30's escape, one module over: validating a coerced value and then computing…, Documented, not overlooked: coercion happens before the multiply. Exact…, float() declared 0.5 s, so 0.5 s is what must be converted., _signal(), TestTheGuardsAreInertOnValidInput

### Community 96 - "TestPlotting"
Cohesion: 0.25
Nodes (4): The reported symptom, and the one plotting path with no guard., plotting.py:87 raised ValueError on mismatched first dimensions., The caller asked for a fit explicitly; silence would be worse., TestPlotting

### Community 97 - "parametrize"
Cohesion: 0.18
Nodes (8): parametrize, `band_low >= band_high` is False for NaN, so a NaN edge passed the guard. Pre-…, One ValueError for every malformed band, from two different doors. The 1- and…, One contract for the whole function, generated from a census against main.…, Newly accepted, in the opposite direction to the rest of the census. On main…, test_every_rejected_input_raises_valueerror_and_draws_nothing(), test_high_precision_bounds_are_now_accepted(), TestTheHighlightBandIsValidatedBeforeDrawing

### Community 98 - "TestNonFiniteInput"
Cohesion: 0.18
Nodes (6): statsmodels defaults to missing='drop'; return_sorted=False must re-insert NaN…, fill_input_gaps=True restores the pre-#36 behaviour., ~np.isnan does not catch inf, but statsmodels drops on isfinite. The inf…, statsmodels is_sorted=False must cope with permuted input., Real cpCST files contain one duplicate timestamp each., TestNonFiniteInput

### Community 99 - "TimeSeriesData"
Cohesion: 0.09
Nodes (13): Propagate metadata, detaching what a derived object must not share. pandas'…, Return constructor for pandas operations., Return constructor for sliced operations., Create a copy of the TimeSeriesData object with metadata preservation. Args:…, Calculate the duration of the time series. Returns: Duration in seconds (or…, Get the length of the time series (backward compatibility). Returns: Number of…, Helper method to update object flags., Display information about the time series data. (+5 more)

### Community 101 - "_degenerate_freq_ts"
Cohesion: 0.17
Nodes (12): _degenerate_freq_ts(), A series whose time base is degenerate, so freq derives to NaN.…, A NaN sampling rate raises rather than producing NaN frequencies. `nan <= 0` is…, get_frequency_content computes its own FFT and needs its own guard. It does not…, get_peak_freq inherits the guard through get_frequency_content., A NaN rate is rejected, via get_frequency_content downstream. This pins…, get_peaks scales min_dist_secs by freq; NaN must not reach int()., test_compute_fft_power_rejects_nan_freq() (+4 more)

### Community 102 - "compute_fft_power"
Cohesion: 0.20
Nodes (12): compute_fft_power(), find_closest(), NDArray, Compute the power spectrum of a time series using FFT. Args: ts: Time series…, Find the closest value in a list/array to a target value. Args: val: Target…, float64, Test find_closest function., The original zero/negative rejection is preserved. Routed through _FreqStub… (+4 more)

### Community 103 - "_DuckSeries"
Cohesion: 0.22
Nodes (6): _DuckSeries, The other route to a None: the metadata-copy fallback in series.py.…, `is_outlier_filtered` is a flag, and the fallback left it None. The defaulting…, The shape `TimeSeriesData.__init__` treats as a baseTs to convert from.…, TestFlagDefaultsAtConstruction, TestOutlierFilterDefaultAtConstruction

### Community 104 - "TestArgumentOrder"
Cohesion: 0.40
Nodes (3): statsmodels is lowess(endog, exog) = (y, x); moepy was fit(x, y). Transposing…, Same y, x stretched: the fitted values must be essentially unchanged., TestArgumentOrder

### Community 105 - "parametrize"
Cohesion: 0.22
Nodes (5): parametrize, Issue #31: a bad rate must be refused where it enters the object., baseTs(data, freq=...) with no times builds the index FROM the rate. freq=0…, baseTs' public default is freq=np.nan, so it cannot mean "invalid". Deliberate…, TestValidationAtProductionSites

### Community 106 - "TestTheStamp"
Cohesion: 0.22
Nodes (3): The wrinkle #20 documented and #40 removes., TestTheStamp, _values()

### Community 107 - "TestLabelMetadataAtConstruction"
Cohesion: 0.31
Nodes (4): The constructor kwargs are a door of their own, and one was left open.…, TypeError: can only concatenate str (not "NoneType") to str., The sibling door, already closed - here so the pair stays closed., TestLabelMetadataAtConstruction

### Community 108 - "TestTheValidatedValueIsTheOneThatGetsFiltered"
Cohesion: 0.22
Nodes (5): Validation is worthless if the filter then uses a different value. Five review…, It declared float() == 1.0, so 1.0 is what the filter must use., The value validated is the value filtered, whatever __truediv__ says., Fraction and Decimal are legitimate Reals, not adversarial ones., TestTheValidatedValueIsTheOneThatGetsFiltered

### Community 109 - "TestInplaceMethodsPreserveIdentity"
Cohesion: 0.22
Nodes (7): basets_owned_inplace_methods(), parametrize, Every public method this package defines that takes `inplace`. Restricted to…, `inplace=True` mutates the object; it must not reset its identity. This is the…, A new `inplace=` method fails here until someone classifies it. The point of…, The identity fix must not cost what already worked. These survived a re-init…, TestInplaceMethodsPreserveIdentity

### Community 110 - ".highpass_at"
Cohesion: 0.29
Nodes (5): Apply a highpass filter at the specified cutoff frequency. Args: cutoff:…, Apply a highpass filter at the specified cutoff frequency (alias for…, highpass_filter(cutoff, order=4) (documented instance method), validate_sampling_freq accepts Decimal; the caller must use its return.…, test_filters_use_the_normalised_rate()

### Community 111 - "TestTheOffsetPairStaysCoherent"
Cohesion: 0.29
Nodes (4): `has_timestamp_offset` False with a non-zero `ts_offset` was unreachable. The…, `is False` matches one object; numpy booleans are not it. `arr.any()`, a…, The coherence rule runs one way, deliberately, and this pins it. Clearing the…, TestTheOffsetPairStaysCoherent

### Community 112 - "TestTheOutcomeCensusIsComplete"
Cohesion: 0.29
Nodes (4): The CHANGELOG's census, asserted rather than described. Every earlier branch in…, The whole of #32 in one assertion: no lag, and no choice of unit, gets a…, Index mode on a degenerate base with a usable integer lag. Both returned…, TestTheOutcomeCensusIsComplete

### Community 113 - "TestLegacyPickles"
Cohesion: 0.27
Nodes (3): Every earlier slot shape loads with the fit readable. Built by editing a state…, The pre-#20 attribute accepted a tuple verbatim. A length test reads `(3, 7)`…, TestLegacyPickles

### Community 114 - "test_the_legend_label_keeps_the_callers_own_formatting"
Cohesion: 0.33
Nodes (6): Validation coerces to float; the label must not inherit that. Routing the label…, A generator band worked before; unpacking it twice broke it. An earlier…, The data-space x range of an axvspan patch, on any matplotlib. axvspan returned…, _span_x_extent(), test_a_one_shot_iterable_band_is_unpacked_exactly_once(), test_the_legend_label_keeps_the_callers_own_formatting()

### Community 115 - "_validate_display_rate"
Cohesion: 0.50
Nodes (5): Any, Coerce a frequency bound to a float matplotlib can use as an axis limit. The…, Unpack and coerce a (low, high) band, or raise ValueError naming it. Both edges…, _validate_display_rate(), _validate_highlight_band()

### Community 117 - "bad_rate_ts"
Cohesion: 0.25
Nodes (8): bad_rate_ts(), _close_figures(), good_ts(), nan_data_ts(), fixture, A series with a usable rate and finite data., The issue's own reproduction: every timestamp identical, so freq is NaN., A usable rate carrying gaps - the #28 guard's input.

### Community 118 - "TestDeclarationLifecycle"
Cohesion: 0.25
Nodes (3): An explicit rate is honoured until the index it describes changes., Guards the _freq_declaration entry in _create_new_with_data's metadata_attrs…, TestDeclarationLifecycle

### Community 119 - "TestNoWriteThrough"
Cohesion: 0.33
Nodes (3): outlier_indices is a mutable list; two objects must not share one., interpolate_gaps keeps the index and, on gap-free data, the values, so the list…, TestNoWriteThrough

### Community 120 - "zscale"
Cohesion: 0.67
Nodes (3): ndarray, Standardize data by removing the mean and scaling to unit variance., zscale()

### Community 121 - "seeded"
Cohesion: 0.31
Nodes (5): Each of these raised AttributeError: no attribute '_name'. Parametrised one…, A baseTs whose three identity fields are all at non-default values. Every field…, #39: the round-trip always worked; what came back did not. Stated precisely…, seeded(), TestUnpickledObjectIsUsable

### Community 122 - "_ExtendedForPickling"
Cohesion: 0.40
Nodes (3): _ExtendedForPickling, A subclass adding a `_metadata` name, defined at module level. Module level…, The class-level case, which must keep working either way.

### Community 123 - "_positional_property"
Cohesion: 0.67
Nodes (3): _positional_property(), Build a property that hands back `value` only while the index it was computed…, property

### Community 124 - "TestArithmeticNameFollowsPandas"
Cohesion: 0.39
Nodes (3): The one place carrying `_name` could silently diverge from pandas.…, `result.name` is pandas-resolved whichever dunder produced it., TestArithmeticNameFollowsPandas

### Community 126 - "TestInterpToHzGrid"
Cohesion: 0.29
Nodes (3): The produced grid must actually have the rate it reports. linspace(t0, t1,…, Regression: a bare floor() drops a trailing sample. (np.arange(1000)/30.0)…, TestInterpToHzGrid

### Community 127 - "TestPickleWrittenBeforeTheFix"
Cohesion: 0.26
Nodes (5): A blob already on disk must load too, and that needs more than #35. Adding…, A state dict shaped like a blob written before `_name` was added. Both edits…, The heal must survive the next operation, not just the load. Without this, a…, None, because the name genuinely is not in those bytes. Healing the object must…, TestPickleWrittenBeforeTheFix

### Community 128 - "TestNanFreqIsNotLaundered"
Cohesion: 0.38
Nodes (3): A NaN rate must not become a fabricated healthy number. Reaches a NaN rate…, A real declared rate must survive an index-preserving transform., TestNanFreqIsNotLaundered

### Community 129 - "TestInterpToHzRejections"
Cohesion: 0.29
Nodes (3): Issue #31's sharpest production site: the one place a user hands baseTs a rate…, Previously returned a length-0 series stamped with the rate. deg.interpto_hz(5)…, TestInterpToHzRejections

### Community 130 - "TestReinitHasOneDoor"
Cohesion: 0.24
Nodes (7): _calls_in_own_scope(), Yield the `ast.Call` nodes belonging to `node` itself. A flat `ast.walk`…, `super(TimeSeriesData, self).__init__` may appear in exactly one place. A…, Functions in core.py that re-initialise self through pandas. Parsed, not…, The scan must attribute a call to its *nearest* enclosing function. A flat…, Guards the scan itself against silently matching nothing. An assertion that a…, TestReinitHasOneDoor

### Community 131 - "TestInvalidationThroughCreateNewWithData"
Cohesion: 0.33
Nodes (3): _create_new_with_data copies the metadata slots outside pandas' machinery.…, Same index and same values, so both still describe the result. sg_filter was…, TestInvalidationThroughCreateNewWithData

### Community 132 - "fixture"
Cohesion: 0.29
Nodes (4): fixture, Generate diverse test data., Generate a noisy signal for filtering tests., Generate time series data for enhanced method testing.

### Community 133 - "from_df"
Cohesion: 0.14
Nodes (13): from_df(), Convert the timeseries to a pandas DataFrame. Args: set_index (bool): If True,…, Create a baseTs object from a pandas DataFrame. Args: df: Input DataFrame…, DataFrame, Integration tests for baseTs processing pipeline., Test a complete processing pipeline with multiple steps., Test creating baseTs from DataFrame and applying pipeline., Test method chaining for creating a processing pipeline. (+5 more)

### Community 134 - "TestAttrsIsolation"
Cohesion: 0.29
Nodes (4): attrs must be copied, never shared - pandas deep-copies it., A shallow dict copy passes the test above and fails this one. pandas'…, The emptiness guard must not invent a dict where none was set., TestAttrsIsolation

### Community 135 - "TestFlagsAssignmentAssumption"
Cohesion: 0.25
Nodes (4): Why `_carry_identity` may assign the flag rather than AND it. pandas 2.3.3's…, Assignment, not AND - the direction only a direct call can reach. Written…, An operation that cannot keep the declaration must change nothing. Checked…, TestFlagsAssignmentAssumption

### Community 137 - "parametrize"
Cohesion: 0.29
Nodes (4): parametrize, Memory: a stale slot would pin the parent's fit and snapshot., Its docstring says outlier_indices is left alone; detrending changes the…, TestValueChangingDerivationsDropBoth

### Community 138 - "TestTheStampIsNotLaunderable"
Cohesion: 0.33
Nodes (3): A copy must move the triple, never re-stamp it. The discriminating derivation…, The behavioural form: a re-stamping copy would look valid here., TestTheStampIsNotLaunderable

### Community 139 - "TestValuePreservingDerivationsKeepBoth"
Cohesion: 0.40
Nodes (3): The discriminating half: same index, same values, a method was called., NaN in the same place compares equal to itself., TestValuePreservingDerivationsKeepBoth

### Community 141 - "_detach_shared_metadata"
Cohesion: 0.11
Nodes (14): Get outlier filter parameters as a plain dict. A snapshot, not the live config.…, Display information about the data, times, outlier filter parameters, and…, _carry_identity(), _detach_shared_metadata(), normalise_history(), normalise_label(), Convert back to a legacy baseTs object for compatibility. Returns: baseTs…, Copy the three identity fields pandas' own __finalize__ carries. `name`,… (+6 more)

### Community 147 - "TestWindowingParamsAreGuardedLikeTheBandEdges"
Cohesion: 0.29
Nodes (4): `max(1, window_step - overlap)` is the same defect one line down (#30). The…, The worst of them: it produced output rather than an error., validate_band_params is public, so it cannot rely on its caller.…, TestWindowingParamsAreGuardedLikeTheBandEdges

### Community 149 - "TestNonScalarBandEdgesKeepTheContract"
Cohesion: 0.40
Nodes (3): An array edge escaped with numpy's ambiguity error, on main and after. `if not…, The guard must not reject the numeric types callers really pass., TestNonScalarBandEdgesKeepTheContract

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
- **61 isolated node(s):** `Global Constraints`, `Commit boundaries`, `Task 1: Index token and derivation hardening`, `Task 2: Make the legacy freq tests independent of freq storage`, `Task 3: The atomic switch — `freq` becomes a property` (+56 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

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