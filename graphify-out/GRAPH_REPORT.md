# Graph Report - baseTs  (2026-09-05)

## Corpus Check
- 72 files · ~214,289 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3015 nodes · 5575 edges · 177 communities (166 shown, 11 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 273 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7341accd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- TestRelativeBandPower
- utils.py
- LowessOutlierFilter
- TestOutlierFilterSurvivesDerivation
- AdaptiveLowessFilter
- .falff
- baseTs API Documentation
- TestBaseTsInitialization
- seeded
- conftest.py
- TestInvalidationOnDerivation
- exgaussian.py
- _PlotAccessor
- baseTs
- parametrize
- TestHistoryInvariantHoldsEverywhere
- TestMathematicalOperations
- TestButterpassAt
- TestLabelMetadataSurvivesDerivation
- TestFilteringOperations
- .__init__
- test_pandas_compat.py
- test_integer_parameter_policy.py
- parametrize
- _degenerate
- TestNoInterpolationAcrossAGap
- Derived `freq` Implementation Plan
- test_gap_preservation.py
- TestPandasEnhancedMethods
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
- test_utils.py
- TestMetadataPropagation
- ._enhanced_process_with_flags
- FilterConfig
- test_lag_shift_bounds.py
- TestEffectiveFrequency
- TestInvalidationOnInPlaceIndexChange
- TestTheOffsetPairStaysCoherent
- normalise_history
- TestMetadataRegistry
- _FinalizingWindow
- TestArithmeticOperators
- test_qc_plot.py
- TestHistoryNoneSurvivesRealOperations
- TestDerivationPathsAgree
- TestFiltersRejectNanFreq
- test_is_interpolated_means_one_thing.py
- test_identity_propagation.py
- Carrying pandas' identity fields across derivation (#35, #39)
- TestANonFiniteLagIsDiagnosed
- test_filters.py
- TestTheDomainTypesAreAlsoValueErrors
- TestTypePreservation
- TestIndexMutationsWithNoHookAtAll
- TestTheStampIsNotLaunderable
- TestDeepcopyOfAName
- TestBaseTsFiltering
- _freq_token
- ValidationError
- Derived `freq`: closing #29, #31 and #23
- TestDeepCopyIndependence
- TestTheInvalidParameterContractIsComplete
- stamped
- coerce_numeric_data
- InvalidParameterError
- plot_fft_power
- test_user_guide_examples.py
- plotting.py
- test_conversion_preserves_metadata.py
- test_data_stamp_invalidation.py
- _ts
- TestHistoryNoneGuard
- .freq
- TestTheOriginDescribesTheIndexItWasRecordedAgainst
- _uniform
- series.py
- TestTheDisplayBoundsAreValidatedBeforeDrawing
- validate_finite_data
- TestEveryBandpassEntryPointRejectsABadLowerEdge
- TestDuplicateLabelRefusal
- get_lags
- .test_augmented_assignment_is_still_in_place
- test_spectral_empty_series.py
- parametrize
- test_docs_fenced_blocks.py
- TimeSeriesData
- .test_invalid_parameter_type_raises_valueerror
- _ts
- ._data
- _named
- TestArgumentOrder
- parametrize
- TestTheStamp
- TestLabelMetadataAtConstruction
- _ts
- basets_owned_inplace_methods
- TestADerivedRateShiftsByTheSampleAsked
- test_lag_plot_labels.py
- TestTheNaNRemedyClearsAnEdgeGap
- TestLegacyPickles
- test_the_legend_label_keeps_the_callers_own_formatting
- TestWhatIsStillAllowed
- TestInPlaceValueWrites
- bad_rate_ts
- TestDeclarationLifecycle
- TestNoWriteThrough
- one_sample
- seeded
- _ExtendedForPickling
- TestTheTwoStepRouteStillWorks
- TestArithmeticNameFollowsPandas
- TestValuesEquality
- TestInterpToHzGrid
- TestPickleWrittenBeforeTheFix
- TestNanFreqIsNotLaundered
- test_series_freq.py
- TestReinitHasOneDoor
- TestInvalidationThroughCreateNewWithData
- requirements.txt
- baseTs
- TestAttrsIsolation
- TestFlagsAssignmentAssumption
- TestSetOutlierFilterIntegerFields
- parametrize
- TestTheStampIsNotLaunderable
- TestValuePreservingDerivationsKeepBoth
- from_df
- .plot_fft_power
- .test_the_stale_fit_is_not_drawn
- parametrize
- TestTheDatetimesAccessor
- TestTimeSliceTakesCalendarBounds
- core.py
- shift_timeseries
- TestTheConstructorConvertsAStampedIndex
- parametrize
- TestTheStampNarrowsToEachDerivation
- TestOutlierDetection
- test_data_setter_span.py
- parametrize
- TestAnExplicitArgumentStillWins
- TestAConfiguredFilterIsNotReplaced
- .test_copy_configuring_does_not_reach_the_original
- .test_get_outlier_filter_params_is_a_snapshot
- .test_outlier_indices_is_reachable_after_slicing
- _one_sample
- TestWindowingParamsAreGuardedLikeTheBandEdges
- TestInheritedPandasInplaceMethods
- _DuckSeries
- test_pipeline.py
- TestBaseTsConversionPreservesMetadata
- Handoff: #100 — convert a DatetimeIndex to seconds at the constructor
- _origin_timestamp
- TestSetTimestampOffsetRecordsTheOrigin
- TestNaNSentinel
- test_derived_lowess_invalidation.py
- .__mul__
- TestATimedeltaIndexIsDurations
- _validate_display_rate
- TestArgumentOrder
- .len
- zscale
- .test_a_declared_rate_does_not_change_the_answer

## God Nodes (most connected - your core abstractions)
1. `baseTs` - 485 edges
2. `TimeSeriesData` - 149 edges
3. `LowessOutlierFilter` - 96 edges
4. `ValidationError` - 64 edges
5. `FilterConfig` - 63 edges
6. `InvalidParameterError` - 60 edges
7. `shift_timeseries()` - 53 edges
8. `bandpass_filter()` - 41 edges
9. `plot_fft_power()` - 40 edges
10. `validate_finite_data()` - 38 edges

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

## Communities (177 total, 11 thin omitted)

### Community 0 - "TestRelativeBandPower"
Cohesion: 0.13
Nodes (12): Tests for the relative_band_power / falff methods., Slow 0.05 Hz signal long enough to resolve the 0.01-0.1 Hz band., Method delegates correctly and returns a builtin float., The headline robustness property: an undetrended mean offset must not move the…, The documented pipeline produces the same answer., falff() defaults to the amplitude convention., details=True carries the white-noise null alongside the ratio., The window argument reaches get_frequency_content. (+4 more)

### Community 1 - "utils.py"
Cohesion: 0.07
Nodes (42): Compute the cumulative sum of the timeseries., Resample onto a uniform grid at exactly new_freq. The grid is built from the…, BandPowerResult, _blank_head(), coerce_real_scalar(), dediff(), _describe(), falff() (+34 more)

### Community 2 - "LowessOutlierFilter"
Cohesion: 0.10
Nodes (18): LowessOutlierFilter, ndarray, Apply LOWESS smoothing and outlier detection to the data. Parameters ----------…, Reject configurations whose local window is too small to smooth. LOWESS fits a…, Apply LOWESS smoothing to the data. Uses statsmodels' Cleveland LOWESS. Note…, Process a single iteration of outlier detection., Validate and convert input data to a NumPy array., Validate and obtain the time index. (+10 more)

### Community 3 - "TestOutlierFilterSurvivesDerivation"
Cohesion: 0.16
Nodes (9): _cleared_filter(), A series whose filter has been cleared - the state issue #33 reports., outlier_filter is always a filter" must hold on every derived object. Without…, __finalize__ copies the parent's None; the chokepoint must fix it., zscale() routes through _create_new_with_data, not __finalize__., info() reads outlier_filter.config to print the filter block., The filter itself is read off the object, so it died here too. Long enough for…, The deliberate boundary of a chokepoint fix, pinned so it is visible.… (+1 more)

### Community 4 - "AdaptiveLowessFilter"
Cohesion: 0.11
Nodes (18): AdaptiveLowessFilter, demo_adaptive_lowess(), LowessConfig, ndarray, Calculate optimal segment length based on dominant frequency content., Configuration parameters for adaptive LOWESS filtering., Calculate overlap ratio based on signal complexity., Calculate LOWESS fraction based on frequency content and noise. (+10 more)

### Community 5 - ".falff"
Cohesion: 0.27
Nodes (8): Compute the relative power (or amplitude) in a frequency band. This is the…, Fractional amplitude of low-frequency fluctuations (fALFF). Convenience wrapper…, baseTs Changelog, Unreleased: Relative Band Power / fALFF, baseTs 1.0.0 Release (NumPy backend), Keep a Changelog, Semantic Versioning, Zou et al. 2008, J Neurosci Methods 172(1):137-141 (fALFF)

### Community 6 - "baseTs API Documentation"
Cohesion: 0.08
Nodes (36): Apply a lowpass filter at the specified cutoff frequency. Args: cutoff: Lowpass…, Apply a lowpass filter to the data. Args: cutoff: Lowpass cutoff frequency in…, Apply a bandpass filter to the signal at specified low-pass and high-pass…, Set outlier filter parameters. Parameters ---------- params : dict, optional…, Apply the outlier filter to the signal. Args: inplace (bool, optional): If…, Apply a rolling mean to the data. Args: window: Size of the rolling window…, Apply a rolling standard deviation to the data., Apply a rolling median to the data. (+28 more)

### Community 7 - "TestBaseTsInitialization"
Cohesion: 0.17
Nodes (7): Tests for baseTs initialization and basic properties., Test initializing baseTs with data and times., Test initializing baseTs with data and frequency., Test initialization validation requirements., Test length and duration calculations., Test creating baseTs from DataFrame., TestBaseTsInitialization

### Community 8 - "seeded"
Cohesion: 0.06
Nodes (32): add_constant(), diff(), Add a constant to a time series. Args: ts: Source baseTs. constant: Value added…, First difference of a time series. Args: ts: Source baseTs. zeropad: If True,…, parametrize, TestDediffIsUntouched, TestFewerThanTwoSamplesIsRefused, TestTwoSamplesIsTheBoundary (+24 more)

### Community 9 - "conftest.py"
Cohesion: 0.15
Nodes (18): data_with_outliers(), noisy_baseTsObj(), noisy_data(), outlier_baseTsObj(), fixture, Pytest configuration and fixtures., Sine with two large, unambiguous spikes. Returns (data, times) rather than a…, Generate a simple sine wave dataset for testing. (+10 more)

### Community 10 - "TestInvalidationOnDerivation"
Cohesion: 0.14
Nodes (6): rolling() routes through _FinalizingWindow, not __finalize__ directly. A window…, A different index means neither attribute describes the object., Stricter than the `freq` token, deliberately. `_freq_token` is (len, first,…, Invalidation is about the index, not about deriving at all. `+ 0.0` rather than…, The rule is index equality, not "was a slicing method called"., TestInvalidationOnDerivation

### Community 11 - "exgaussian.py"
Cohesion: 0.19
Nodes (20): calculate_aic(), calculate_bic(), chi_square_test(), exg_initial_guess(), ExGaussianFit, FitStatistics, get_exg_fits(), iterative_exgaussian_fit() (+12 more)

### Community 12 - "_PlotAccessor"
Cohesion: 0.20
Nodes (4): _PlotAccessor, Callable proxy backing ``baseTs.plot``. ``plot`` used to be a plain alias for…, Plot the timeseries as a line plot. Quick and dirty visualization., Line plot, or the pandas plotting accessor. Calling it is the historical baseTs…

### Community 13 - "baseTs"
Cohesion: 0.08
Nodes (15): Integration tests for real-world time series workflows. Tests complete end-to-…, Test batch processing multiple time series., Test realistic time series analysis workflows., Test data consistency across operations., Test complete signal processing workflow., Test workflow with larger datasets., Test scientific analysis workflow., Test compatibility across different workflow scenarios. (+7 more)

### Community 14 - "parametrize"
Cohesion: 0.10
Nodes (21): _FreqStub, parametrize, The original zero/negative rejection is preserved. Routed through _FreqStub…, The guard rejects bad values, not unfamiliar dtypes - and since #75 hands back…, Complex is a dtype rejection, made before the finiteness check. Issue #43. The…, The complex message is for complex numbers, not for strings complex() parses.…, NaT must not slip through the float cast. This is the one dtype family where…, Non-finite and non-positive rates alike. (+13 more)

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
Cohesion: 0.27
Nodes (6): parametrize, signal_name and last_process are always strings" - same defect class. Issue #33…, A number is as fatal to `name + " " + process` as a None is. On the…, The live crash: TypeError: unsupported operand 'NoneType' + 'str'., Restoring a default must not rewrite a name someone chose. Deliberately already…, TestLabelMetadataSurvivesDerivation

### Community 19 - "TestFilteringOperations"
Cohesion: 0.08
Nodes (14): Test filtering operations., Test lowpass filtering., Test highpass filtering., Test bandpass filtering., Test Savitzky-Golay filtering., Test Gaussian filtering., Test chaining multiple filters., Test edge cases and error handling. (+6 more)

### Community 20 - ".__init__"
Cohesion: 0.13
Nodes (12): array, ndarray, setter, Interpolate data to a uniform sampling grid. If new_grid is not specified, use…, Initialize baseTs object as pandas Series with time-series metadata. Args:…, Set specific indices to NaN and interpolate the missing values. Args: indices:…, Get the data values as numpy array (backward compatibility)., Set the data values (backward compatibility). (+4 more)

### Community 21 - "test_pandas_compat.py"
Cohesion: 0.07
Nodes (16): fixture, parametrize, Regression tests for pandas 2.x/3.x compatibility. Each test here corresponds…, baseTs.duration() shadowed the guarded TimeSeriesData.duration()., get_statistics() calls duration(), so it inherited the crash., 5000 normal samples with one unmistakable spike at index 100., pandas 3.0 removed fillna(method=...)., Series.interpolate() does not fill leading/trailing NaN, so this path always… (+8 more)

### Community 22 - "test_integer_parameter_policy.py"
Cohesion: 0.11
Nodes (16): Apply a Savitzky-Golay filter to the input data. Args: data: Input data array…, sg_filter(), int, _data(), _IntegralThatRefuses, register, One policy for integer parameters (#78). #49 gave `order` a strict rule: a non-…, A window longer than the data is still shortened, and an even one still made… (+8 more)

### Community 23 - "parametrize"
Cohesion: 0.11
Nodes (9): parametrize, pandas supports `for window in ts.rolling(3): ...`, yielding each window as its…, The contract is behavioural, not identity. FilterConfig is frozen and…, Independence must not cost the config: the values still carry over., Arithmetic returns via _wrap_result_as_basets, which assigned every metadata…, pandas implements `ts += 1` by calling __add__ and keeping only the values,…, _create_new_with_data omitted outlier_filter from the attributes it carries, so…, ts is uniformly sampled, so every op here should agree with it. (+1 more)

### Community 24 - "_degenerate"
Cohesion: 0.17
Nodes (8): _degenerate(), Index mode on a degenerate base with a usable integer lag. Both returned…, Every timestamp identical, so the derived rate is NaN. This is the object from…, The rate must be rejected where it enters the conversion. Each of these fails…, The silent half of #32. On main this returns successfully with `lag_secs=nan`:…, Index mode is `lag_plot`'s default, and on main it draws a plot titled "nan…, `baseTs.lag_plot` delegates, so it must not need its own check., TestADegenerateTimeBaseIsDiagnosed

### Community 25 - "TestNoInterpolationAcrossAGap"
Cohesion: 0.32
Nodes (4): An input gap is a boundary, not something to interpolate through. Filling the…, It must not be pulled toward the first valid sample after the gap., Two gaps, three segments; an outlier in each must stay local., TestNoInterpolationAcrossAGap

### Community 26 - "Derived `freq` Implementation Plan"
Cohesion: 0.18
Nodes (10): Before opening the PR, Commit boundaries, Derived `freq` Implementation Plan, Global Constraints, Task 1: Index token and derivation hardening, Task 2: Make the legacy freq tests independent of freq storage, Task 3: The atomic switch — `freq` becomes a property, Task 4: Fix the `interpto_hz` grid (+2 more)

### Community 27 - "test_gap_preservation.py"
Cohesion: 0.09
Nodes (22): _gappy(), _nan_mask(), fixture, parametrize, _quiet(), Tests for issue #36: filter_outliers must not invent data in pre-existing gaps.…, The old fill-everything behaviour stays reachable for anyone relying on it., Silent is the failure mode; the history entry should carry the count. (+14 more)

### Community 28 - "TestPandasEnhancedMethods"
Cohesion: 0.11
Nodes (10): Test new pandas-enhanced methods., Test pandas-powered rolling mean., Test rolling standard deviation., Test time-based slicing., Test pandas resampling., Test cross-correlation between time series., Test outlier detection., Test gap interpolation. (+2 more)

### Community 29 - "TestBaseTsTransformations"
Cohesion: 0.17
Nodes (7): Test data normalization functions., Test detrending functionality., Test trimming functionality., Tests for baseTs data transformations., Test interpolation to specified number of samples., Test interpolation to specified frequency., TestBaseTsTransformations

### Community 30 - "TestReadIsPureAndDerivationReleases"
Cohesion: 0.19
Nodes (7): Two halves of one contract, neither depending on who read what. Reading is a…, The asymmetry that clearing-on-read introduced., Specified, not accidental. Within this property's scope - do the samples still…, The other half: derivation destroys, so a revert cannot undo it., Memory: a slice must not pin the parent's full-length array., Every derived object gets a new Index, so a first read is O(n). Re-stamping…, TestReadIsPureAndDerivationReleases

### Community 31 - "TestPandasIntegration"
Cohesion: 0.12
Nodes (10): fixture, Generate diverse test data., Generate a noisy signal for filtering tests., Generate time series data for enhanced method testing., Test direct pandas integration features., Create sample time series., Test direct access to pandas methods., Test pandas-style indexing. (+2 more)

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
Cohesion: 0.09
Nodes (15): bandpass_filter(), Apply a symmetric bandpass filter to the input data. Args: data: Input data…, All of these must raise; four of the seven previously did not. The negative,…, A message about ordering is useless without the two values in it., The asymmetry that made this bug position-dependent. `max(0.1, nan)` returns…, Nyquist must come from the effective rate, not the declared one. The filter…, Pins that the check above is about the effective rate. Without this, the…, The guard must not disturb an ordinary call. (+7 more)

### Community 36 - "TailType"
Cohesion: 0.08
Nodes (16): Created on Oct 19 2024 @author: stan@sympaticog.com, Enum for specifying which tails to process in outlier detection., TailType, baseTs Package README, Enum, LOWESS Outlier Detection & Despiking, Tests for the statsmodels LOWESS backend of LowessOutlierFilter. Covers the…, The unslotted dataclass must not resurrect the attribute. (+8 more)

### Community 37 - "Design"
Cohesion: 0.11
Nodes (18): Behaviour changes, Deep copy and detachment, Design, Documentation, Eager release on derivation, Order of checks, Pickles written before this change, Problem (+10 more)

### Community 38 - "test_plot_accessor.py"
Cohesion: 0.10
Nodes (11): close_figures(), fixture, parametrize, Tests for the hybrid baseTs.plot accessor. `plot` was a plain alias for…, The historical spelling must be unchanged., The accessor is a property, so it must follow the preserved type., Each accessor plots its own data, not the parent's., TestAccessorSurvivesOperations (+3 more)

### Community 39 - "test_utils.py"
Cohesion: 0.03
Nodes (76): _all_four_entry_points(), _analytic_ts(), _degenerate_freq_ts(), _gappy_ts(), _leading_gap_ts(), lf_baseTsObj(), fixture, Unit tests for baseTs utility functions. (+68 more)

### Community 40 - "TestMetadataPropagation"
Cohesion: 0.09
Nodes (11): The __finalize__ concat special-case exists for nlargest/nsmallest's internal…, pandas' default __finalize__ assigns metadata by reference, so parent and child…, pandas' _inplace_method reindexes the result back to self before adopting it.…, TimeSeriesData never set outlier_filter despite declaring it in _metadata, so a…, baseTs(ts) takes the conversion branch in TimeSeriesData.__init__, which…, Every parameter used to carry a real default, so naming frac also set…, The whole design rests on this: a frozen config plus a rebinding…, Two series built from one list would cross-contaminate. (+3 more)

### Community 41 - "._enhanced_process_with_flags"
Cohesion: 0.08
Nodes (13): Apply a notch filter at the specified frequency. The stopped band is `cutoff_hz…, Apply a notch filter at the specified frequency (alias for notch_at). Args:…, Apply a highpass filter at the specified cutoff frequency. Args: cutoff:…, Apply a highpass filter at the specified cutoff frequency (alias for…, Apply a Gaussian filter to the data. Args: sigma: Standard deviation for…, Apply a Savitzky-Golay filter to the signal. Args: window_length: Length of the…, Helper method to update object flags., Enhanced processing method that handles both data and time modifications. Args:… (+5 more)

### Community 42 - "FilterConfig"
Cohesion: 0.08
Nodes (19): FilterConfig, Configuration parameters for the LowessOutlierFilter. Attributes ----------…, Initialize the LowessOutlierFilter with filtering parameters. Parameters…, np.asarray drops a mask and exposes the payload underneath., TestMaskedArrayGapsAreSeen, parametrize, A perfectly-fit signal drives MAD to zero; z_threshold then means nothing, so…, A window of <= 3 points makes LOWESS interpolate the data exactly. The fit is… (+11 more)

### Community 43 - "test_lag_shift_bounds.py"
Cohesion: 0.07
Nodes (24): lag_plot(), Generate a lag plot for a given timeseries object and lag., _closed(), _declared(), _five(), _five_int(), The lag that is applied is the lag that is reported (#51-#54). Four defects in…, `Lag Plot at 0.5 seconds (49items)` was the issue's example. (+16 more)

### Community 44 - "TestEffectiveFrequency"
Cohesion: 0.09
Nodes (12): n samples span n-1 intervals., rolling() does not call __finalize__, so freq is recomputed from the index - it…, nlargest(3) is excluded from the op list above - it is the one op there that…, #19: resample changes the time base, so the carried freq described the old…, An explicitly supplied freq may legitimately disagree with the times it was…, #19: arithmetic on two different time bases must derive from the union index…, #19: interpto_samples assigned n/duration over the corrected derivation., #19: same n/duration error as interpto_samples. (+4 more)

### Community 45 - "TestInvalidationOnInPlaceIndexChange"
Cohesion: 0.15
Nodes (6): The index can change without any derivation at all., `.index` is pandas' own setter, and `.times` is not the only door., The inplace branch calls pd.Series.__init__ directly, bypassing…, The data setter rebuilds the index when the length changes., Same length keeps the index; equal values keep the fit (#40). Assigning zeros…, TestInvalidationOnInPlaceIndexChange

### Community 46 - "TestTheOffsetPairStaysCoherent"
Cohesion: 0.29
Nodes (4): `has_timestamp_offset` False with a non-zero `ts_offset` was unreachable. The…, `is False` matches one object; numpy booleans are not it. `arr.any()`, a…, The coherence rule runs one way, deliberately, and this pins it. Clearing the…, TestTheOffsetPairStaysCoherent

### Community 47 - "normalise_history"
Cohesion: 0.22
Nodes (7): Display information about the data, times, outlier filter parameters, and…, normalise_history(), Helper method to update history and last_process. Normalises rather than…, Display information about the time series data., Coerce any history value to a fresh list. The single definition of the "history…, Round a float to a specified number of decimal places, or return the value…, round_values()

### Community 48 - "TestMetadataRegistry"
Cohesion: 0.40
Nodes (3): `_metadata` must extend pandas' list rather than replace it., Every name pandas declares must still be carried. Asserted against…, TestMetadataRegistry

### Community 54 - "_FinalizingWindow"
Cohesion: 0.16
Nodes (7): _FinalizingWindow, Wraps a pandas window object (Rolling/Expanding/ExponentialMovingWindow) so its…, Python looks up dunder methods on the type, bypassing __getattr__, so this…, See _FinalizingWindow: rolling()/expanding()/ewm() never call __finalize__., Rolling window whose aggregations propagate metadata - see _FinalizingWindow., Expanding window whose aggregations propagate metadata - see _FinalizingWindow., EWM window whose aggregations propagate metadata - see _FinalizingWindow.

### Community 55 - "TestArithmeticOperators"
Cohesion: 0.20
Nodes (5): parametrize, The operator dunders do not route through __finalize__. `__add__` and friends…, A scalar cannot change the index, so the index rule must not fire. Zero, so the…, `ts += x` cannot change ts's index, so the index rule never fires.…, TestArithmeticOperators

### Community 56 - "test_qc_plot.py"
Cohesion: 0.20
Nodes (13): _close_figures(), fixture, parametrize, Tests for filter_outliers(qcplot=True). The QC plot exists to show the filter's…, The plotting path must not become a second route to the #6 bug., Asking for a plot must not change what the filter returns., spiked_ts(), test_lowess_fit_trace_is_present() (+5 more)

### Community 57 - "TestHistoryNoneSurvivesRealOperations"
Cohesion: 0.26
Nodes (5): The None-history guard must hold on the paths users actually take. Guarding…, zscale() dies in _create_new_with_data's history.copy()., info() iterates history; None raised TypeError., __finalize__ turns a propagated None into a list., TestHistoryNoneSurvivesRealOperations

### Community 58 - "TestDerivationPathsAgree"
Cohesion: 0.17
Nodes (4): fixture, A value-sorted series has a non-monotonic index and no honest rate. The carried…, Issue #29's acceptance test. The same index change had two answers depending on…, TestDerivationPathsAgree

### Community 59 - "TestFiltersRejectNanFreq"
Cohesion: 0.27
Nodes (4): A degenerate time base must not filter to silent all-NaN output.…, butterpass_at was absent from this family because it never ran (#27). It…, The guard must not disturb an ordinary series., TestFiltersRejectNanFreq

### Community 60 - "test_is_interpolated_means_one_thing.py"
Cohesion: 0.07
Nodes (22): Interpolate missing values in the data. Linear interpolation across every NaN,…, interpolate_missing_values(), ValueError, Interpolate missing values in a time series. Args: ts: Time series object…, _clean(), _gappy(), parametrize, `is_interpolated` means one thing, and every producer follows it (#90). The… (+14 more)

### Community 61 - "test_identity_propagation.py"
Cohesion: 0.21
Nodes (7): identity_of(), The three identity fields pandas owns must survive derivation (#35, #39). A…, The bar is pandas' own behaviour, not an invented one. If a future pandas stops…, The three fields as one comparable tuple., `ts += 1` keeps the target's own identity, as stock pandas does. Pinned because…, TestIdentitySurvivesDerivation, TestInplaceArithmeticIsUnaffected

### Community 62 - "Carrying pandas' identity fields across derivation (#35, #39)"
Cohesion: 0.10
Nodes (19): Carrying pandas' identity fields across derivation (#35, #39), Decisions taken, Deliberately not in scope, Design, Half A — `_name` joins `_metadata`, Half B, Group 1 — one door for the identity triple, Half B, Group 2 — collapse three doors into one, Making a tenth site fail loudly (+11 more)

### Community 63 - "TestANonFiniteLagIsDiagnosed"
Cohesion: 0.09
Nodes (14): parametrize, `validate_lag` never gets to speak, because `get_lags` converts first. The rate…, A string lag dies on main with `can't multiply sequence by non-int`. It must…, float(10**400) raises OverflowError, which is neither TypeError nor ValueError…, It is a perfectly good real number; it is out of float's range. Collapsing…, `{lag!r}` on a large object builds a megabyte-long exception. A 200k-element…, The str/bytes exclusion is load-bearing for both, not just str. `float(b"0.5")`…, One argument, one exception type, whichever mode it arrives in. Guarding only… (+6 more)

### Community 64 - "test_filters.py"
Cohesion: 0.08
Nodes (15): _DeclaresOneHz, _LiesAboutDivision, register, Registers as a Real but cannot become one. numbers.Real is a registrable ABC,…, A Real that converts to 1.0 and supports nothing else. Registers, coerces,…, Validation is worthless if the filter then uses a different value. Five review…, It declared float() == 1.0, so 1.0 is what the filter must use., The value validated is the value filtered, whatever __truediv__ says. (+7 more)

### Community 65 - "TestTheDomainTypesAreAlsoValueErrors"
Cohesion: 0.08
Nodes (16): Exception, Base exception for time series related errors., TimeSeriesError, _degenerate(), The same site inside validate_filter_params, reached by the three single-cutoff…, #48 added a translation site of the same shape, around validate_finite_data.…, `_calculate_effective_frequency` catches (TypeError, ValueError) to fall back…, The identity is added, never swapped. (+8 more)

### Community 66 - "TestTypePreservation"
Cohesion: 0.18
Nodes (7): fixture, Tests that pandas operations preserve the baseTs type and its metadata. Before…, The documented pattern: a pandas op followed by a baseTs op., pandas builds subclasses as _constructor(values, index=...)., pandas looks this up on the class; a plain method breaks that., TestTypePreservation, ts()

### Community 67 - "TestIndexMutationsWithNoHookAtAll"
Cohesion: 0.22
Nodes (3): The doors that defeated the write-side design. These reach past `__finalize__`,…, The third `pd.Series.__init__` site, and the one an explicit audit for that…, TestIndexMutationsWithNoHookAtAll

### Community 68 - "TestTheStampIsNotLaunderable"
Cohesion: 0.22
Nodes (5): A copy must move the (value, index) pair, never re-stamp it. Any path that…, The discriminating case for laundering. interpolate_gaps routes through…, Memory, not correctness: the getter already reads a slice as None. Without this…, The behavioural form of the laundering check. Starting from a *valid* fit is…, TestTheStampIsNotLaunderable

### Community 69 - "TestDeepcopyOfAName"
Cohesion: 0.40
Nodes (3): `_name` now reaches deepcopy_metadata_value; it must pass through., Which is why the isinstance gate in that helper never matches it. Recorded as a…, TestDeepcopyOfAName

### Community 70 - "TestBaseTsFiltering"
Cohesion: 0.22
Nodes (5): Tests for baseTs filtering functionality., Test highpass filter., Test bandpass filter., Test Savitzky-Golay filter., TestBaseTsFiltering

### Community 71 - "_freq_token"
Cohesion: 0.29
Nodes (5): _freq_token(), Fingerprint an index for the purpose of sampling-rate derivation. Deliberately…, The token must be exactly the inputs _calculate_effective_frequency reads. That…, And must not: the derived rate is unchanged, so the token is right.…, TestFreqToken

### Community 72 - "ValidationError"
Cohesion: 0.10
Nodes (19): _coerce_lag(), idx_to_time(), Convert a lag to a float, or say which argument is wrong. validate_lag is the…, Convert an index to a time value. Args: lag_idx: Index to convert freq:…, Convert a time value to the nearest whole number of samples. Args: lag_secs:…, Exception raised for validation errors. Also a ValueError, because a rejected…, time_to_idx(), ValidationError (+11 more)

### Community 73 - "Derived `freq`: closing #29, #31 and #23"
Cohesion: 0.14
Nodes (13): 1. The `freq` property, 2. Propagation, 3. Validation at production sites (#31), 4. `interpto_hz` (#23), 5. Deletions, 6. Edge cases, Approach, Consequences (+5 more)

### Community 74 - "TestDeepCopyIndependence"
Cohesion: 0.29
Nodes (3): `copy(deep=True)` must hand back arrays the parent does not share. Both copy…, The constructor types this as np.array, so a list check is not enough., TestDeepCopyIndependence

### Community 75 - "TestTheInvalidParameterContractIsComplete"
Cohesion: 0.27
Nodes (5): Every known bad input raises InvalidParameterError, enumerated. The CHANGELOG…, Every known bad input raises, with the message its own guard makes., The number in the prose is asserted against the table. Adding a case without…, A fragment true of another case's message pins nothing. Three fragments were…, TestTheInvalidParameterContractIsComplete

### Community 76 - "stamped"
Cohesion: 0.08
Nodes (17): epoch_seconds(), numeric_twin(), A DatetimeIndex becomes seconds since its first stamp at the constructor…, Same data on the same seconds: bit-identical results., The seconds index is what is resampled, so a series starting at 08:00 has day…, `_update_series_data`'s no-span shrink slices the index it has; on `main` that…, Review round 1 (consensus panel, codex + agy): the first cut converted in…, `reindex` builds through the constructor and then `__finalize__` copies the… (+9 more)

### Community 77 - "coerce_numeric_data"
Cohesion: 0.08
Nodes (22): coerce_numeric_data(), _complex_data_message(), The rejection text for complex sample values (issue #43). `what` describes the…, Return `data` as an array with a dtype numeric code can loop over. The dtype…, _as_object(), parametrize, Classified by what the elements *are*, not by whether a float() parse would…, numbers.Real is a registrable ABC; membership does not imply a working… (+14 more)

### Community 78 - "InvalidParameterError"
Cohesion: 0.09
Nodes (41): ArrayLike, _as_filterable(), _as_real_float(), FilterConfig, FilterError, highpass_filter(), InvalidParameterError, lowpass_filter() (+33 more)

### Community 79 - "plot_fft_power"
Cohesion: 0.09
Nodes (31): plot_fft_power(), Plots the power spectrum of a timeseries signal using enhanced FFT with…, Tests for issue #34: plot_fft_power must raise, not draw the error.…, ts.plot_fft_power() is the path users actually call., setup_plot used to run before the guard, so every failure left a figure. In a…, A caller passing ax= gets it back as they left it, not titled and annotated., The band check ran after the spectrum was already plotted. Ordering matters for…, The consequence users actually meet, and the fix the docs name. Since #36… (+23 more)

### Community 80 - "test_user_guide_examples.py"
Cohesion: 0.29
Nodes (9): fenced_python_under(), Executable pins on the worked examples in docs/USER_GUIDE.md. The example is…, The first ```python block after the given markdown heading line., Execute a doc block and return its namespace. The guide's opening block does…, Issue #44: a self-referential dict literal and a cutoff at Nyquist. The Nyquist…, The `quality_score < 0.95` branch, which the example's own data never takes.…, run_example(), test_example_4_enhanced_cleaning_branch_completes() (+1 more)

### Community 81 - "plotting.py"
Cohesion: 0.16
Nodes (16): hist(), plot(), plot_series(), array, Axes, qc_plot(), Plots a histogram of a timeseries., Plots multiple timeseries on the same plot. (+8 more)

### Community 82 - "test_conversion_preserves_metadata.py"
Cohesion: 0.14
Nodes (10): carrying(), fixture, Converting a series must not reset what it was carrying (issue #57).…, The conversion branch was gated on `.times` and `.data`. Only `baseTs` defines…, An empty carried history must not become a fabricated creation entry. The…, A series with every metadata value moved off its default., The ordinary path must still start from defaults, not from nothing. Nothing is…, TestAnEmptyHistoryIsAHistory (+2 more)

### Community 83 - "test_data_stamp_invalidation.py"
Cohesion: 0.19
Nodes (10): _close_figures(), filtered(), gapped(), fixture, Tests for #40: lowess_fit and outlier_indices on an object whose values…, Both producers assign the data first and the slot second. That ordering is now…, A filtered series carrying a real fit and a real outlier record., Filtered, with a pre-existing NaN the filter leaves alone (#36). (+2 more)

### Community 84 - "_ts"
Cohesion: 0.11
Nodes (22): _as_object(), parametrize, Object-dtype data reaching the spectral family and gauss_filter (#93). The same…, The constancy threshold (`np.std(data) < 1e-15`) was always taken on a float64…, compute_fft_power demeans in place on the array it computes with. The guard…, `astype(float, copy=False)` hands a float64 series' own array back, so…, #93 dropped get_frequency_content's copy on the strength of "nothing below…, For the spectral family this held before #93 (the guard ran, its result was… (+14 more)

### Community 85 - "TestHistoryNoneGuard"
Cohesion: 0.29
Nodes (4): A `history` of None must not crash the next operation (issue #22). __finalize__…, The superclass guard is hasattr-only, so None slips past it too., The guard must not discard a history that is genuinely present., TestHistoryNoneGuard

### Community 86 - ".freq"
Cohesion: 0.25
Nodes (5): setter, Derive the sampling frequency from the time index. Returns NaN rather than…, The sampling rate in Hz, derived from the index unless declared. An explicitly…, Declare an explicit sampling rate against the current index. The single…, String representation of TimeSeriesData.

### Community 87 - "TestTheOriginDescribesTheIndexItWasRecordedAgainst"
Cohesion: 0.09
Nodes (14): The case the healing made permanent: the pair survived an index replacement…, The remedy names a value, and on a pre-#100 object the stored one is the wrong…, It cannot say which index its offset described., The offsets agreed, so the arm re-stamped the merged index and read the stale…, Two series of one origin on interleaved grids align onto their union, which…, The common case: same grid, so the union is the grid itself., Review round 2 (consensus panel, codex + agy): the pair rode along through…, `_update_inplace` swaps the manager without `__finalize__`; the read-time check… (+6 more)

### Community 88 - "_uniform"
Cohesion: 0.10
Nodes (12): One argument, one exception type. `validate_lag` raises ValidationError for…, Unchanged, and deliberately so: `idx_to_time` divides rather than truncating,…, Coercion must not start *accepting* what validate_lag rejects: a Decimal…, `lag_secs=inf` used to ride out into the returned dict and the plot title,…, Pinned so a future guard cannot quietly change what a good call returns. The…, Guarding the rate must not be mistaken for normalising it: the rate stays…, #30's escape, one module over: validating a coerced value and then computing…, Documented, not overlooked: coercion happens before the multiply. Accepting… (+4 more)

### Community 89 - "series.py"
Cohesion: 0.05
Nodes (53): Create a copy of the baseTs object. Args: deep: Whether to make a deep copy…, _apply_duplicate_label_declaration(), _carries_metadata(), _carry_identity(), _complete_positional_slots(), deepcopy_metadata_value(), _detach_shared_metadata(), _drawn_from() (+45 more)

### Community 90 - "TestTheDisplayBoundsAreValidatedBeforeDrawing"
Cohesion: 0.17
Nodes (6): The frequency bounds reach ax.set_xlim, which rejects NaN and Inf. An infinite…, NaN is the documented public sentinel for max_rate - not an error., min_rate has no sentinel, so NaN is simply invalid there., Pins the shared door's ndarray branch, which mutation testing found bare.…, The other half of that branch: 0-d arrays convert alike on both majors., TestTheDisplayBoundsAreValidatedBeforeDrawing

### Community 91 - "validate_finite_data"
Cohesion: 0.06
Nodes (30): Reject sample values an FFT cannot produce a meaningful spectrum from. The…, validate_finite_data(), #77 keyed the hint on a leading NaN so as not to name a second remedy that does…, TestTheInfHalfOfTheRemedy, pandas' default limit_direction='forward' fills nothing before the first valid…, While #81 was open the hint keyed on a leading NaN only: interpolate_gaps()…, The alternative to the edge fill is to drop what precedes the first valid…, Extend the first valid value back over the edge" presupposes a first valid… (+22 more)

### Community 92 - "TestEveryBandpassEntryPointRejectsABadLowerEdge"
Cohesion: 0.43
Nodes (3): The contract must hold on all three names, on the axis it is about. #28's…, Reachable at all only since #27, which was dead before it., TestEveryBandpassEntryPointRejectsABadLowerEdge

### Community 93 - "TestDuplicateLabelRefusal"
Cohesion: 0.09
Nodes (13): _Flags, Only a *stale* shadow is dropped, not any shadow. Deleting unconditionally also…, The restore arm, exercised directly. Since the pre-commit check landed, no path…, A stand-in whose flag setter raises what the caller chooses., Raising pandas' real class, not a look-alike. An earlier version of this test…, An error that names a remedy is code; the remedy must run. This repo shipped an…, The remedy that was there before, and why it was wrong. `ts.data = ...`,…, A diagnosis must not become the payload. Naming every duplicated label built an… (+5 more)

### Community 94 - "get_lags"
Cohesion: 0.09
Nodes (14): get_lags(), Get lag values in both seconds and indices. Args: lag: Lag value lag_unit: Unit…, parametrize, `lag_secs` was the caller's argument echoed back. Now it is derived from…, 0.3 s at 7 Hz is 2.1 samples. Rounding alone would make the two values agree in…, Nothing changes for the caller who was already getting the right answer: 50 /…, Accepted, and pinned so it is not re-raised: review round 1 found a call that…, A Decimal or a bool used to be echoed back as itself. (+6 more)

### Community 96 - "test_spectral_empty_series.py"
Cohesion: 0.19
Nodes (12): _empty(), parametrize, An empty series is rejected by every spectral entry point, from one door (#62).…, Precedence for a series wrong in both ways: empty, and no usable rate. The door…, `utils.validate_non_empty` is the one definition., Emptiness only: a NaN is `validate_finite_data`'s to reject, and a 0-d array…, The whole family, not just the one sibling that already checked. `match` pins…, No RuntimeWarning on the way to the error. `relative_band_power` takes `np.std`… (+4 more)

### Community 97 - "parametrize"
Cohesion: 0.15
Nodes (9): parametrize, ValueError, matching every other bound failure in this function. '30' and True…, `band_low >= band_high` is False for NaN, so a NaN edge passed the guard. Pre-…, One ValueError for every malformed band, from two different doors. The 1- and…, One contract for the whole function, generated from a census against main.…, Newly accepted, in the opposite direction to the rest of the census. On main…, test_every_rejected_input_raises_valueerror_and_draws_nothing(), test_high_precision_bounds_are_now_accepted() (+1 more)

### Community 98 - "test_docs_fenced_blocks.py"
Cohesion: 0.10
Nodes (24): Block, blocks_in(), _execute(), _literal_default(), outcome(), parametrize, python_fences(), Every fenced Python block in docs/ runs (#69). The document is the source of… (+16 more)

### Community 99 - "TimeSeriesData"
Cohesion: 0.05
Nodes (23): Pandas Series subclass optimized for time series analysis. This class extends…, Restore from a pickle, healing a blob that predates `_name`. Adding '_name' to…, Install an index, converting a stamped one to seconds (#100). This is the one…, pandas' in-place door: swap the manager, then narrow the stamp.…, Initialize default metadata values., Return constructor for pandas operations., Return constructor for sliced operations., Calculate the duration of the time series. Returns: Duration in seconds (or… (+15 more)

### Community 101 - "_ts"
Cohesion: 0.12
Nodes (15): _close_figures(), fixture, parametrize, `signal_name` and `last_process` are always strings, in place too (#61). #33…, The public names stay in `_metadata`; propagation runs the setter., A blob written before this change can hold `None` under the public name - #33…, The getter defaults rather than raising: pandas can build a subclass instance…, The half #33 left open: the object you mutate, not the one you derive. (+7 more)

### Community 102 - "._data"
Cohesion: 0.12
Nodes (14): notch_filter(), Apply a symmetric notch filter to the input data. The stopped band is…, #76: notch_filter validated `cutoff_hz` against (0, Nyquist) and then stopped…, One message for every out-of-range cutoff, so the limits it quotes are the…, Drift guard for the stated rule. The stopped band is `cutoff +/- 1% of…, The parameter rule before the O(n) data scan, the #48 ordering: a mistyped…, The limits a retry has to meet, in Hz, both of them. Review found the first cut…, The check is scipy's, on the normalised band; the message speaks Hz.… (+6 more)

### Community 103 - "_named"
Cohesion: 0.13
Nodes (12): _named(), parametrize, The signal name's case follows one rule on every derivation (issue #56). The…, A name the caller passes is a constructor argument, not an inheritance, so it…, Distinct from the mixed case: `.title()` or `.capitalize()` in place of a…, The live symptom: the same series titled two ways., The name was never part of the metadata that flag withholds., Copying the name verbatim must not reopen what #33 closed: the constructor used… (+4 more)

### Community 104 - "TestArgumentOrder"
Cohesion: 0.17
Nodes (14): _assert_same_spectrum(), parametrize, compute_fft_power computes on a float64 copy of the validated data (#96). The…, The review of #93 built a float32 series the two precisions disagree on:…, numpy 2.x takes the FFT of a float32 array in float32 and returns a float32…, The demeaning is still an in-place subtraction, so the float64 copy is load-…, #93's rule, which the object-array-of-floats tests cannot pin: `np.array(obj,…, `demean=True` on an integer or bool series raised numpy's bare `UFuncTypeError`… (+6 more)

### Community 105 - "parametrize"
Cohesion: 0.20
Nodes (5): parametrize, Issue #31: a bad rate must be refused where it enters the object., baseTs(data, freq=...) with no times builds the index FROM the rate. freq=0…, baseTs' public default is freq=np.nan, so it cannot mean "invalid". Deliberate…, TestValidationAtProductionSites

### Community 106 - "TestTheStamp"
Cohesion: 0.22
Nodes (3): The wrinkle #20 documented and #40 removes., TestTheStamp, _values()

### Community 107 - "TestLabelMetadataAtConstruction"
Cohesion: 0.31
Nodes (4): The constructor kwargs are a door of their own, and one was left open.…, TypeError: can only concatenate str (not "NoneType") to str., The sibling door, already closed - here so the pair stays closed., TestLabelMetadataAtConstruction

### Community 108 - "_ts"
Cohesion: 0.16
Nodes (10): parametrize, compute_fft_power's constant-signal branch reports the FFT branch's DC bin…, Observed and not changed: a different function, not divided by n., The number the FFT branch would have produced for the same array, computed here…, 600 samples of 3.0, and the same with every other sample raised by 1e-13: std 0…, Under the default scale_power=True the DC bin is the only non-zero one on…, Review round 1: `n * mean**2` reimplements the FFT branch's DC bin rather than…, TestTheConstantBranchReportsTheFftBranchsDcBin (+2 more)

### Community 109 - "basets_owned_inplace_methods"
Cohesion: 0.50
Nodes (3): basets_owned_inplace_methods(), Every public method this package defines that takes `inplace`. Restricted to…, A new `inplace=` method fails here until someone classifies it. The point of…

### Community 110 - "TestADerivedRateShiftsByTheSampleAsked"
Cohesion: 0.14
Nodes (8): _derived(), Every length from 100 to 2000 at a nominal 100 Hz, three lags. The issue…, The tie rule is Python's, stated so it is not mistaken for drift. A lag that…, `round()` on a float returns int; `validate_lag` insists on it., Rounding must not start inventing a one-sample shift for a lag that is nearer…, A nominal 100 Hz series with the rate *derived*, which is the default. The…, `int(0.5 * 99.99999999999999)` is 49. The caller asked for 50., TestADerivedRateShiftsByTheSampleAsked

### Community 111 - "test_lag_plot_labels.py"
Cohesion: 0.14
Nodes (15): _close_figures(), _labels(), fixture, `lag_plot` labels the plot with the name the series has, and nothing else…, The issue's reproduction, both halves: stdout stays empty, and the placeholder…, `normalise_label`'s rule: a caller who set a number meant it to show., The last re-casing site. `plot()` titles "Heart Rate by time."; the lag plot…, Unchanged for the common path: the constructor upper-cases its own argument… (+7 more)

### Community 112 - "TestTheNaNRemedyClearsAnEdgeGap"
Cohesion: 0.22
Nodes (6): Two paths the hint's caller may be on (review, round 3): the in-place form of…, #77: the NaN message names `interpolate_gaps()`, which forwards pandas' default…, Executed, not just named - the whole point of #77., The asymmetry the hint is built on, pinned: pandas' forward fill extends the…, `limit` is the caller's own constraint and it applies to the edge fill like any…, TestTheNaNRemedyClearsAnEdgeGap

### Community 113 - "TestLegacyPickles"
Cohesion: 0.27
Nodes (3): Every earlier slot shape loads with the fit readable. Built by editing a state…, The pre-#20 attribute accepted a tuple verbatim. A length test reads `(3, 7)`…, TestLegacyPickles

### Community 114 - "test_the_legend_label_keeps_the_callers_own_formatting"
Cohesion: 0.33
Nodes (6): Validation coerces to float; the label must not inherit that. Routing the label…, A generator band worked before; unpacking it twice broke it. An earlier…, The data-space x range of an axvspan patch, on any matplotlib. axvspan returned…, _span_x_extent(), test_a_one_shot_iterable_band_is_unpacked_exactly_once(), test_the_legend_label_keeps_the_callers_own_formatting()

### Community 115 - "TestWhatIsStillAllowed"
Cohesion: 0.15
Nodes (5): Pinned because a mutant that resampled the same-length path too survived every…, A no-span index cannot grow; it can shrink, and what it keeps are labels it…, Incidental: on `main` this crashed inside numpy (`linspace` on `Timestamp`…, As everywhere since #38: the token no longer matches, so it derives., TestWhatIsStillAllowed

### Community 117 - "bad_rate_ts"
Cohesion: 0.25
Nodes (8): bad_rate_ts(), _close_figures(), good_ts(), nan_data_ts(), fixture, A series with a usable rate and finite data., The issue's own reproduction: every timestamp identical, so freq is NaN., A usable rate carrying gaps - the #28 guard's input.

### Community 118 - "TestDeclarationLifecycle"
Cohesion: 0.25
Nodes (3): An explicit rate is honoured until the index it describes changes., Guards the _freq_declaration entry in _create_new_with_data's metadata_attrs…, TestDeclarationLifecycle

### Community 119 - "TestNoWriteThrough"
Cohesion: 0.33
Nodes (3): outlier_indices is a mutable list; two objects must not share one., interpolate_gaps keeps the index and, on gap-free data, the values, so the list…, TestNoWriteThrough

### Community 120 - "one_sample"
Cohesion: 0.17
Nodes (6): one_sample(), `except ValueError` is the family's promised catch., An error that names a remedy is code; the remedy must run., The rule is about the span, and sample count was only its proxy. Review round 1…, `nan == nan` is False, so an equality test alone let a NaN endpoint through to…, TestGrowingASeriesWithNoSpanIsRefused

### Community 121 - "seeded"
Cohesion: 0.19
Nodes (9): parametrize, Each of these raised AttributeError: no attribute '_name'. Parametrised one…, `inplace=True` mutates the object; it must not reset its identity. This is the…, A baseTs whose three identity fields are all at non-default values. Every field…, The identity fix must not cost what already worked. These survived a re-init…, #39: the round-trip always worked; what came back did not. Stated precisely…, seeded(), TestInplaceMethodsPreserveIdentity (+1 more)

### Community 122 - "_ExtendedForPickling"
Cohesion: 0.40
Nodes (3): _ExtendedForPickling, A subclass adding a `_metadata` name, defined at module level. Module level…, The class-level case, which must keep working either way.

### Community 123 - "TestTheTwoStepRouteStillWorks"
Cohesion: 0.12
Nodes (7): Package methods assign data then times; the transient must not bite., The shrinker round 2 (glm) caught: `main` gave `[3.0] @ [5.0]`., Until #89 this pinned an empty result - the shrink-to-empty leg of the route. A…, The shrink-to-empty leg of the route, which the diff_ts pin used to carry (#89…, One check, two consequences; the wordings must not be swapped., The one package route that could keep the transient. `apply_function` never…, TestTheTwoStepRouteStillWorks

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

### Community 129 - "test_series_freq.py"
Cohesion: 0.33
Nodes (3): Issue #31's sharpest production site: the one place a user hands baseTs a rate…, Previously returned a length-0 series stamped with the rate. deg.interpto_hz(5)…, TestInterpToHzRejections

### Community 130 - "TestReinitHasOneDoor"
Cohesion: 0.24
Nodes (7): _calls_in_own_scope(), Yield the `ast.Call` nodes belonging to `node` itself. A flat `ast.walk`…, `super(TimeSeriesData, self).__init__` may appear in exactly one place. A…, Functions in core.py that re-initialise self through pandas. Parsed, not…, The scan must attribute a call to its *nearest* enclosing function. A flat…, Guards the scan itself against silently matching nothing. An assertion that a…, TestReinitHasOneDoor

### Community 131 - "TestInvalidationThroughCreateNewWithData"
Cohesion: 0.33
Nodes (3): _create_new_with_data copies the metadata slots outside pandas' machinery.…, Same index and same values, so both still describe the result. sg_filter was…, TestInvalidationThroughCreateNewWithData

### Community 132 - "requirements.txt"
Cohesion: 0.20
Nodes (10): Python Package CI Workflow, hypothesis, Matplotlib, moepy, NumPy, Pandas, psutil, pytest (+2 more)

### Community 133 - "baseTs"
Cohesion: 0.04
Nodes (31): baseTs, Apply a bandpass filter between two cutoff frequencies (alias for bandpass_at).…, Apply a Butterworth bandpass filter (alias for bandpass_at). Args: hp_freq:…, Get outlier filter parameters as a plain dict. A snapshot, not the live config.…, Compute the first difference of the timeseries. Args: zeropad: If True, the…, Basic data class to hold a timeseries and data. Built on pandas Series…, A time_slice bound as seconds on the index. A number is seconds on the index,…, Compute the FFT power of the timeseries. Computed on a float64 copy of the… (+23 more)

### Community 134 - "TestAttrsIsolation"
Cohesion: 0.29
Nodes (4): attrs must be copied, never shared - pandas deep-copies it., A shallow dict copy passes the test above and fails this one. pandas'…, The emptiness guard must not invent a dict where none was set., TestAttrsIsolation

### Community 135 - "TestFlagsAssignmentAssumption"
Cohesion: 0.20
Nodes (5): Why `_carry_identity` may assign the flag rather than AND it. pandas 2.3.3's…, `_copy_metadata_from_basetseries` accepts anything with `.times`/`.data`, so a…, Assignment, not AND - the direction only a direct call can reach. Written…, An operation that cannot keep the declaration must change nothing. Checked…, TestFlagsAssignmentAssumption

### Community 136 - "TestSetOutlierFilterIntegerFields"
Cohesion: 0.10
Nodes (11): _bandpass(), fixture, parametrize, `max_iterations`, `order` and `it` are the filter config's integer fields.…, One exception type across the package; `except ValueError` still catches it, as…, `window_step` and `overlap` are annotated int and documented as a step and an…, An overlap of zero is the default. A negative one would inflate the effective…, validate_band_params is public and cannot rely on its caller. (+3 more)

### Community 137 - "parametrize"
Cohesion: 0.29
Nodes (4): parametrize, Memory: a stale slot would pin the parent's fit and snapshot., Its docstring says outlier_indices is left alone; detrending changes the…, TestValueChangingDerivationsDropBoth

### Community 138 - "TestTheStampIsNotLaunderable"
Cohesion: 0.33
Nodes (3): A copy must move the triple, never re-stamp it. The discriminating derivation…, The behavioural form: a re-stamping copy would look valid here., TestTheStampIsNotLaunderable

### Community 139 - "TestValuePreservingDerivationsKeepBoth"
Cohesion: 0.40
Nodes (3): The discriminating half: same index, same values, a method was called., NaN in the same place compares equal to itself., TestValuePreservingDerivationsKeepBoth

### Community 140 - "from_df"
Cohesion: 0.15
Nodes (9): from_df(), Convert the timeseries to a pandas DataFrame. Args: set_index (bool): If True,…, Create a baseTs object from a pandas DataFrame. Args: df: Input DataFrame…, DataFrame, A caller asking for relative seconds only. Coherent, so allowed., seconds_since_first(), TestAnExplicitOffsetAlongsideAStampedIndex, TestFromDfAcceptsADatetimeColumn (+1 more)

### Community 141 - ".plot_fft_power"
Cohesion: 0.14
Nodes (10): Axes, Plot this timeseries against one or more other timeseries. e.g. for QC,…, Plot a histogram of the timeseries., Plot the power spectrum of the timeseries using enhanced frequency analysis.…, Plot a lag plot of the timeseries., Direct Pandas Series Inheritance Architecture, baseTs 2.0.0 Release (Pandas Series Foundation), Dual Backend Architecture (removed in v2.0.0) (+2 more)

### Community 143 - "parametrize"
Cohesion: 0.10
Nodes (11): parametrize, `pd.Timestamp(2592000)` is 2.592 ms into 1970; the rule is `numbers.Real`,…, The load-bearing agreement between the two conversions: the index comes from…, A series built from seconds must come out byte-for-byte as before. The pair's…, The TypeError arm in the rate derivation used to be described as the…, `Decimal` registers under `numbers.Number`, not `numbers.Real`; `main` compared…, A microsecond index from 1700 to 2200 is a valid DatetimeIndex (unit us),…, The remaining keyword combination of the pinned pair table. (+3 more)

### Community 144 - "TestTheDatetimesAccessor"
Cohesion: 0.11
Nodes (8): Exact whenever the first stamp lies on a microsecond and each later stamp is at…, 2.11e-7 s, the number the CHANGELOG quotes, asserted rather than bounded: the…, Mutation found `floor` and `trunc` splits agree on every stamp (whole…, Past 2**23 s a float64 second's ulp exceeds a nanosecond, so the nanosecond…, The int64 nanosecond product wrapped silently: 9.5e9 s came back as a date in…, `has_timestamp_offset=True` with `ts_offset` 0 is a caller's own assertion…, A property raising AttributeError is invisible to hasattr and would fall into…, TestTheDatetimesAccessor

### Community 145 - "TestTimeSliceTakesCalendarBounds"
Cohesion: 0.12
Nodes (5): fixture, The bound is turned into seconds the way the index was, so a bound that names a…, `Timedelta.total_seconds()` rounds to the microsecond; the bound is placed as…, Whatever the string says: the origin check runs before parsing., TestTimeSliceTakesCalendarBounds

### Community 146 - "core.py"
Cohesion: 0.09
Nodes (22): _is_unset(), True if a numeric argument was not supplied. The constructor uses np.nan as its…, Find the closest time in the timeseries to a target time in seconds. Args: sec:…, baseTs - A Python library for time series analysis, ClosestMatch, compute_fft_power(), find_closest(), find_closest_time() (+14 more)

### Community 147 - "shift_timeseries"
Cohesion: 0.13
Nodes (10): Shift a time series by a lag value. Args: ts: Time series object with data and…, shift_timeseries(), A datetime index derived no rate, so these needed a declared one to reach the…, Its times are seconds since the first stamp now (#100)., The dtype's own missing value where it has one; float64 where it has none.…, Review round 2 (codex): widening the whole array to float64 for the sake of two…, A bytes array has no missing value, and it is not numeric, so there is nothing…, Review round 1 (codex): an outcome-based fallback - try `astype(float)`, refuse… (+2 more)

### Community 148 - "TestTheConstructorConvertsAStampedIndex"
Cohesion: 0.13
Nodes (5): TimeSeriesData is the door; baseTs only rides through it., Seconds are counted from index[0]; an unsorted index goes negative. The rule is…, Parity with the numeric index, which admits NaN., The origin has to be a stamp; NaT would make every second NaN and the offset…, TestTheConstructorConvertsAStampedIndex

### Community 149 - "parametrize"
Cohesion: 0.12
Nodes (12): parametrize, An array edge escaped with numpy's ambiguity error, on main and after. `if not…, The guard must not reject the numeric types callers really pass., Four NaN samples in, six hundred NaN out, silently (#48). filtfilt's…, Same guard, same exception type; since #81 the Inf half of the message names…, filtfilt handles complex input correctly - it filters the real and imaginary…, A bad call is a bug in the call; bad data is a property of the input. The cheap…, validate_band_params checks hp_hz and the ordering *after* the delegated… (+4 more)

### Community 150 - "TestTheStampNarrowsToEachDerivation"
Cohesion: 0.20
Nodes (6): Review round 3 (quick-review, a different harness): the subset test is by…, `dropna(inplace=True)` swaps the manager through `_update_inplace`, which…, Positions 0..n-1 of a series whose own seconds are exactly those values read as…, A two-key groupby's MultiIndex cannot be compared with seconds; `Index.isin`…, The one index `_set_axis` could narrow against is a same-length permutation,…, TestTheStampNarrowsToEachDerivation

### Community 151 - "TestOutlierDetection"
Cohesion: 0.33
Nodes (4): Tests for outlier detection functionality., Test setting outlier filter parameters., Test outlier filtering., TestOutlierDetection

### Community 152 - "test_data_setter_span.py"
Cohesion: 0.33
Nodes (3): empty(), A length-changing `ts.data = x` resamples over the span it has (#65). The rule.…, One sample still has to be placed somewhere.

### Community 153 - "parametrize"
Cohesion: 0.33
Nodes (3): parametrize, Regression guard over spanning sources: true on `main` too. The no-span cases…, The one package method that grew a no-span source. Review round 1 (codex +…

### Community 154 - "TestAnExplicitArgumentStillWins"
Cohesion: 0.17
Nodes (6): parametrize, The conversion branch takes its index from the source, so a `times` argument…, Preserving what was not passed must not ignore what was. The fix distinguishes…, `history=None` is the documented way to ask for a fresh entry. Folding it into…, TestAnExplicitArgumentStillWins, TestAnIgnoredIndexIsRefused

### Community 159 - "_one_sample"
Cohesion: 0.21
Nodes (8): filterwarnings, _one_sample(), Only the empty series is rejected by the door. One sample is not. A 1-sample…, A confident 0.0 for a spectrum with no peak in it - observed and left as…, The constant-data branch, which runs before the FFT: one sample has a standard…, matplotlib warns about a singular x-range for one point; that is the draw's,…, Its threshold is its own contract and is not the door's., TestTheOneSampleDecision

### Community 160 - "TestWindowingParamsAreGuardedLikeTheBandEdges"
Cohesion: 0.15
Nodes (7): `max(1, window_step - overlap)` is the same defect one line down (#30). The…, `window_step=10**400` raised a bare OverflowError on main, through `sample_Hz /…, `overlap=10**400` raised under #30 only because the float coercion overflowed;…, Since #78 the guard is the integer one, so the message names that rule rather…, The worst of them: it produced output rather than an error., validate_band_params is public, so it cannot rely on its caller.…, TestWindowingParamsAreGuardedLikeTheBandEdges

### Community 161 - "TestInheritedPandasInplaceMethods"
Cohesion: 0.18
Nodes (5): `inplace=True` on an inherited pandas method swaps the block manager. pandas…, The reported crash, reachable without any baseTs method at all., The silent variant: same length, every position moved., These keep the positions, so the index rule must not fire. On this fixture they…, TestInheritedPandasInplaceMethods

### Community 162 - "_DuckSeries"
Cohesion: 0.22
Nodes (6): _DuckSeries, The other route to a None: the metadata-copy fallback in series.py.…, `is_outlier_filtered` is a flag, and the fallback left it None. The defaulting…, The shape `TimeSeriesData.__init__` treats as a baseTs to convert from.…, TestFlagDefaultsAtConstruction, TestOutlierFilterDefaultAtConstruction

### Community 163 - "test_pipeline.py"
Cohesion: 0.20
Nodes (9): Integration tests for baseTs processing pipeline., Test a complete processing pipeline with multiple steps., Test creating baseTs from DataFrame and applying pipeline., Test method chaining for creating a processing pipeline., Test conversions between baseTs and pandas DataFrame., test_complete_processing_pipeline(), test_dataframe_conversions(), test_from_df_to_pipeline() (+1 more)

### Community 164 - "TestBaseTsConversionPreservesMetadata"
Cohesion: 0.20
Nodes (6): `baseTs(ts)` is a conversion, not a reset., The sharpest edge: a converted object claimed to be freshly made. Verbatim, not…, #15's guard, which was the only name that already worked., Assigned through the public properties, these were cleared to None. Read back…, The whole list, so a name added later cannot quietly drop out., TestBaseTsConversionPreservesMetadata

### Community 165 - "Handoff: #100 — convert a DatetimeIndex to seconds at the constructor"
Cohesion: 0.22
Nodes (8): Decisions taken while implementing (2026-09-05), Design, Docs to update (they currently work around #100 and say so), Handoff: #100 — convert a DatetimeIndex to seconds at the constructor, Tests to write first (TDD; the harness must be red before the code), The task, What is true on `main` at 0cbffcb (all measured, pandas 3.0.1 / numpy 2.5.2), Working rules this arc has settled on (see the memory files for the why)

### Community 166 - "_origin_timestamp"
Cohesion: 0.32
Nodes (7): _origin_timestamp(), The index as calendar stamps: the origin plus each second. The index itself is…, The origin `ts_offset` names, rebuilt at microsecond resolution. A float64…, origin + seconds, as a DatetimeIndex, at the precision the float holds. A…, _stamps_from_seconds(), DatetimeIndex, Timestamp

### Community 167 - "TestSetTimestampOffsetRecordsTheOrigin"
Cohesion: 0.25
Nodes (3): It used to move the index by the offset and record it; the index stays put now.…, Nothing about the index changes, so the declaration's token holds., TestSetTimestampOffsetRecordsTheOrigin

### Community 168 - "TestNaNSentinel"
Cohesion: 0.25
Nodes (4): `freq is np.nan` only matched the one np.nan object., Previously this silently produced an all-NaN time index instead of raising,…, Deriving freq from the times array must still work. NB: the derived value is…, TestNaNSentinel

### Community 169 - "test_derived_lowess_invalidation.py"
Cohesion: 0.33
Nodes (5): _close_figures(), filtered(), fixture, Tests for #20: lowess_fit and outlier_indices on derived objects. `lowess_fit`…, A filtered series carrying a real fit and a real outlier record.

### Community 170 - ".__mul__"
Cohesion: 0.33
Nodes (3): Multiplication operation returning a baseTs object., A deliberate narrowing, pinned so it is not mistaken for a bug. `lag * rate`…, float() declared 0.5 s, so 0.5 s is what must be converted.

### Community 171 - "TestATimedeltaIndexIsDurations"
Cohesion: 0.33
Nodes (3): Durations carry no origin, so a caller may name one., Seconds are the durations themselves, not durations since the first., TestATimedeltaIndexIsDurations

### Community 172 - "_validate_display_rate"
Cohesion: 0.50
Nodes (5): Any, Coerce a frequency bound to a float matplotlib can use as an axis limit. The…, Unpack and coerce a (low, high) band, or raise ValueError naming it. Both edges…, _validate_display_rate(), _validate_highlight_band()

### Community 173 - "TestArgumentOrder"
Cohesion: 0.40
Nodes (3): statsmodels is lowess(endog, exog) = (y, x); moepy was fit(x, y). Transposing…, Same y, x stretched: the fitted values must be essentially unchanged., TestArgumentOrder

### Community 175 - "zscale"
Cohesion: 0.67
Nodes (3): ndarray, Standardize data by removing the mean and scaling to unit variance., zscale()

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
- **68 isolated node(s):** `Global Constraints`, `Commit boundaries`, `Task 1: Index token and derivation hardening`, `Task 2: Make the legacy freq tests independent of freq storage`, `Task 3: The atomic switch — `freq` becomes a property` (+63 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

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