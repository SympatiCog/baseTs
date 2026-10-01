# Graph Report - baseTs  (2026-09-17)

## Corpus Check
- 93 files · ~256,234 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3570 nodes · 6686 edges · 194 communities (179 shown, 15 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 319 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `85977aad`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- TestRelativeBandPower
- test_frame_average_rules.py
- LowessOutlierFilter
- test_exception_hierarchy.py
- AdaptiveLowessFilter
- .__init__
- baseTs API Documentation
- bandpass_filter
- seeded
- conftest.py
- TestInvalidationOnDerivation
- exgaussian.py
- test_file_io.py
- TestRealWorldWorkflows
- series.py
- TestButterpassAt
- TestMathematicalOperations
- _gapped
- time_to_idx
- TestFilteringOperations
- TestTheConstructorConvertsAStampedIndex
- test_pandas_compat.py
- test_integer_parameter_policy.py
- test_conversion_preserves_metadata.py
- TestWindowGuard
- TestNoInterpolationAcrossAGap
- Derived `freq` Implementation Plan
- test_gap_preservation.py
- TestPandasEnhancedMethods
- TestBaseTsTransformations
- TestReadIsPureAndDerivationReleases
- test_frame_broadcast_equals_series.py
- test_figures.py
- parametrize
- figures.py
- test_frame_review_findings.py
- TestBaseTsConversionPreservesMetadata
- Design
- test_plot_accessor.py
- validate_finite_data
- TestMetadataPropagation
- ._enhanced_process_with_flags
- .__init__
- shift_timeseries
- TestEffectiveFrequency
- ._wrap_result_as_basets
- stamped
- frame.py
- baseDf API Documentation
- baseDf
- TestDuplicateLabelRefusal
- TestNoWriteThrough
- test_qc_plot.py
- TestHistoryNoneSurvivesRealOperations
- _degenerate
- TestFiltersRejectNanFreq
- test_is_interpolated_means_one_thing.py
- File Structure
- Carrying pandas' identity fields across derivation (#35, #39)
- test_derived_lowess_invalidation.py
- _crash_session
- Any
- TestLowessDetrend
- test_frame_measurements.py
- _apply_duplicate_label_declaration
- TestLabelMetadataSurvivesDerivation
- baseTs
- TestBaseTsInitialization
- Design: `baseDf` — many time series on one shared index
- Derived `freq`: closing #29, #31 and #23
- TestDeepCopyIndependence
- TestTheInvalidParameterContractIsComplete
- epoch_seconds
- coerce_numeric_data
- InvalidParameterError
- plot_fft_power
- test_user_guide_examples.py
- core.py
- TestOutlierFilterSurvivesDerivation
- test_data_stamp_invalidation.py
- _ts
- TestInvalidationOnInPlaceIndexChange
- test_type_preservation.py
- TestTheOriginDescribesTheIndexItWasRecordedAgainst
- parametrize
- _FinalizingWindow
- TestTheDisplayBoundsAreValidatedBeforeDrawing
- parametrize
- TestEveryBandpassEntryPointRejectsABadLowerEdge
- Axes
- get_lags
- TestLabelMetadataAtConstruction
- test_spectral_empty_series.py
- TestHistoryNoneGuard
- test_docs_fenced_blocks.py
- TimeSeriesData
- test_frame_correlation.py
- _ts
- ._data
- _named
- TestArgumentOrder
- TestTheSingleCutoffFiltersUseTheValidatedValue
- TestTheStamp
- requirements.txt
- _ts
- TestBaseTsFiltering
- parametrize
- test_lag_plot_labels.py
- TestTheNaNRemedyClearsAnEdgeGap
- TestLegacyPickles
- TestDerivationPathsAgree
- _freq_token
- TestInPlaceValueWrites
- bad_rate_ts
- _one_sample
- _all_four_entry_points
- baseTs Test Suite README
- TestInheritedPandasInplaceMethods
- TestFiltersRefuseIndexGaps
- baseTs
- test_pipeline.py
- TestValuesEquality
- test_gaps.py
- TestPickleWrittenBeforeTheFix
- BandPowerResult
- _origin_timestamp
- TestReinitHasOneDoor
- test_datetime_index_converts_at_the_constructor.py
- test_frame_copy.py
- baseTs
- TestStaircaseTrapFigure
- TestDespikingFigure
- TestBandPowerFigure
- parametrize
- TestTheStampIsNotLaunderable
- TestValuePreservingDerivationsKeepBoth
- TestPlotting
- TestTheICCImplementation
- .test_the_stale_fit_is_not_drawn
- parametrize
- test_frame_consensus_review_findings.py
- TestTimeSliceTakesCalendarBounds
- TestGapOrderFigure
- TestIndexMutationsWithNoHookAtAll
- test_frame_entry_points.py
- TestTheStampIsNotLaunderable
- TestTheStampNarrowsToEachDerivation
- .freq
- TestSetTimestampOffsetRecordsTheOrigin
- TestGaps
- baseTs Development Guide
- TestDerivationHardening
- test_frame_indexing_keeps_col_meta.py
- test_identity_propagation.py
- TestTestRetestFigure
- TestNumFitsDeprecation
- _DuckSeries
- TestFlagsAssignmentAssumption
- .test_copy_configuring_does_not_reach_the_original
- .test_get_outlier_filter_params_is_a_snapshot
- TestPandasIntegration
- Handoff: #100 — convert a DatetimeIndex to seconds at the constructor
- built
- .test_outlier_indices_is_reachable_after_slicing
- TestNanFreqIsNotLaundered
- seeded
- test_the_legend_label_keeps_the_callers_own_formatting
- TestArithmeticNameFollowsPandas
- FilterConfig
- averaged_row
- TestAttrsIsolation
- ValidationError
- TestATimezoneAwareIndexIsAnInstant
- .test_augmented_assignment_is_still_in_place
- TestMetadataRegistry
- _PlotAccessor
- parametrize
- baseTs
- .test_invalid_parameter_type_raises_valueerror
- TestDeepcopyOfAName
- TestInvalidationThroughCreateNewWithData
- TestDeclarationLifecycle
- _validate_display_rate
- _ExtendedForPickling
- TestInterpToHzGrid
- test_series_freq.py
- TestOutlierDetection
- basets_owned_inplace_methods
- test_utils.py
- zscale

## God Nodes (most connected - your core abstractions)
1. `baseTs` - 499 edges
2. `TimeSeriesData` - 149 edges
3. `ValidationError` - 112 edges
4. `LowessOutlierFilter` - 101 edges
5. `baseDf` - 100 edges
6. `InvalidParameterError` - 71 edges
7. `FilterConfig` - 63 edges
8. `shift_timeseries()` - 53 edges
9. `bandpass_filter()` - 41 edges
10. `plot_fft_power()` - 40 edges

## Surprising Connections (you probably didn't know these)
- `notch_filter(freq, quality=30) (documented instance method)` --conceptually_related_to--> `notch_filter()`  [AMBIGUOUS]
  docs/API.md → baseTs/filters.py
- `highpass_filter(cutoff, order=4) (documented instance method)` --conceptually_related_to--> `highpass_filter()`  [AMBIGUOUS]
  docs/API.md → baseTs/filters.py
- `bandpass_filter(low_cutoff, high_cutoff, order=4) (documented instance method)` --conceptually_related_to--> `bandpass_filter()`  [AMBIGUOUS]
  docs/API.md → baseTs/filters.py
- `Design Principle: API Stability` --rationale_for--> `baseTs`  [EXTRACTED]
  CLAUDE.md → baseTs/core.py
- `Design Principle: Metadata Preservation` --rationale_for--> `baseTs`  [EXTRACTED]
  CLAUDE.md → baseTs/core.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **baseTs Documentation Suite** — readme_doc, docs_user_guide_doc, docs_api_doc, docs_api_series_doc, docs_examples_doc, docs_changelog_doc, claude_devguide [EXTRACTED 1.00]
- **LOWESS Despiking Workflow** — basets_core_basets_set_outlier_filter, basets_core_basets_filter_outliers, lowess_outlier_detection, basets_lowessoutlierfilter [EXTRACTED 1.00]
- **Enhanced Pandas Series Methods (v2.0.0 Migration)** — basets_core_basets_resample, basets_core_basets_interpolate_gaps, basets_core_basets_align_with, basets_core_basets_correlation_with, basets_core_basets_detect_outliers, basets_core_basets_rolling_mean, basets_core_basets_time_slice, basets_core_basets_get_statistics, basets_core_basets_get_frequency_content, basets_core_basets_shift_time [EXTRACTED 1.00]

## Communities (194 total, 15 thin omitted)

### Community 0 - "TestRelativeBandPower"
Cohesion: 0.13
Nodes (12): Tests for the relative_band_power / falff methods., Slow 0.05 Hz signal long enough to resolve the 0.01-0.1 Hz band., Method delegates correctly and returns a builtin float., The headline robustness property: an undetrended mean offset must not move the…, The documented pipeline produces the same answer., falff() defaults to the amplitude convention., details=True carries the white-noise null alongside the ratio., The window argument reaches get_frequency_content. (+4 more)

### Community 1 - "test_frame_average_rules.py"
Cohesion: 0.13
Nodes (26): common_prefix(), operation_head(), The part of a history entry that names the operation and its parameters. A…, The leading steps every history shares. Entries are compared by…, _frame(), Averaging columns: which flags survive, what history says, and NaN policy., Entries differing only after '; ' are one operation with per-input outcomes…, skipna is a parameter, so it lives before the '; ' - an average of averages… (+18 more)

### Community 2 - "LowessOutlierFilter"
Cohesion: 0.13
Nodes (15): LowessOutlierFilter, baseTs, ndarray, Apply LOWESS smoothing and outlier detection to the data. Parameters ----------…, Reject configurations whose local window is too small to smooth. LOWESS fits a…, Apply LOWESS smoothing to the data. Uses statsmodels' Cleveland LOWESS. Note…, Process a single iteration of outlier detection., Validate and convert input data to a NumPy array. (+7 more)

### Community 3 - "test_exception_hierarchy.py"
Cohesion: 0.08
Nodes (20): FilterError, Exception, Base exception for filter-related errors., Exception, Base exception for time series related errors., TimeSeriesError, _degenerate(), The domain exceptions are also ValueErrors. Both validating families raise a… (+12 more)

### Community 4 - "AdaptiveLowessFilter"
Cohesion: 0.11
Nodes (18): AdaptiveLowessFilter, demo_adaptive_lowess(), LowessConfig, ndarray, Calculate optimal segment length based on dominant frequency content., Configuration parameters for adaptive LOWESS filtering., Calculate overlap ratio based on signal complexity., Calculate LOWESS fraction based on frequency content and noise. (+10 more)

### Community 5 - ".__init__"
Cohesion: 0.09
Nodes (15): Origin the index seconds are counted from, in epoch seconds., _carries_metadata(), normalise_label(), Initialize TimeSeriesData object. A `DatetimeIndex` or `TimedeltaIndex` -…, Give the pair the origin the installed index brought, if any. The rule every…, Initialize default metadata values., Propagate metadata, detaching what a derived object must not share. pandas'…, Calculate the duration of the time series. Returns: Duration in seconds (or… (+7 more)

### Community 6 - "baseTs API Documentation"
Cohesion: 0.07
Nodes (38): Apply a lowpass filter at the specified cutoff frequency. Args: cutoff: Lowpass…, Apply a lowpass filter to the data. Args: cutoff: Lowpass cutoff frequency in…, Apply a bandpass filter to the signal at specified low-pass and high-pass…, Set outlier filter parameters. Parameters ---------- params : dict, optional…, Apply the outlier filter to the signal. Args: inplace (bool, optional): If…, Apply a rolling mean to the data. Args: window: Size of the rolling window…, Apply a rolling standard deviation to the data., Apply a rolling median to the data. (+30 more)

### Community 7 - "bandpass_filter"
Cohesion: 0.08
Nodes (17): bandpass_filter(), Apply a symmetric bandpass filter to the input data. Args: data: Input data…, The guard must not disturb an ordinary call., `max(1, window_step - overlap)` is the same defect one line down (#30). The…, `window_step=10**400` raised a bare OverflowError on main, through `sample_Hz /…, `overlap=10**400` raised under #30 only because the float coercion overflowed;…, Since #78 the guard is the integer one, so the message names that rule rather…, The worst of them: it produced output rather than an error. (+9 more)

### Community 8 - "seeded"
Cohesion: 0.06
Nodes (36): add_constant(), dediff(), diff(), Add a constant to a time series. Args: ts: Source baseTs. constant: Value added…, First difference of a time series. Args: ts: Source baseTs. zeropad: If True,…, Cumulative sum of a time series. Undoes `diff(zeropad=True)` up to the level…, parametrize, utils.diff and diff_ts refuse a series with fewer than two samples (#89).… (+28 more)

### Community 9 - "conftest.py"
Cohesion: 0.15
Nodes (18): data_with_outliers(), noisy_baseTsObj(), noisy_data(), outlier_baseTsObj(), fixture, Pytest configuration and fixtures., Sine with two large, unambiguous spikes. Returns (data, times) rather than a…, Generate a simple sine wave dataset for testing. (+10 more)

### Community 10 - "TestInvalidationOnDerivation"
Cohesion: 0.14
Nodes (6): rolling() routes through _FinalizingWindow, not __finalize__ directly. A window…, A different index means neither attribute describes the object., Stricter than the `freq` token, deliberately. `_freq_token` is (len, first,…, Invalidation is about the index, not about deriving at all. `+ 0.0` rather than…, The rule is index equality, not "was a slicing method called"., TestInvalidationOnDerivation

### Community 11 - "exgaussian.py"
Cohesion: 0.19
Nodes (20): calculate_aic(), calculate_bic(), chi_square_test(), exg_initial_guess(), ExGaussianFit, FitStatistics, get_exg_fits(), iterative_exgaussian_fit() (+12 more)

### Community 12 - "test_file_io.py"
Cohesion: 0.13
Nodes (12): from_csv(), from_parquet(), Create a baseTs object from a CSV file. Thin wrapper: ``pd.read_csv(path,…, Create a baseTs object from a Parquet file. Thin wrapper:…, _long(), DataFrame, Loading baseTs / baseDf objects from CSV and Parquet files., TestBaseDfFromCsv (+4 more)

### Community 13 - "TestRealWorldWorkflows"
Cohesion: 0.12
Nodes (9): Test batch processing multiple time series., Test realistic time series analysis workflows., Test data consistency across operations., Test complete signal processing workflow., Test workflow with larger datasets., Test scientific analysis workflow., Test outlier detection and removal workflow., Test complex data transformation workflow. (+1 more)

### Community 14 - "series.py"
Cohesion: 0.07
Nodes (31): baseTs - A Python library for time series analysis, _complete_positional_slots(), _drawn_from(), _drop_stale_positional_metadata(), _holds_calendar_datetimes(), _label_property(), _origin_problem(), _positional_property() (+23 more)

### Community 15 - "TestButterpassAt"
Cohesion: 0.06
Nodes (25): parametrize, Every metadata slot must come out where bandpass_at puts it. Asserted against…, Delegation is deliberate: the entry reads bandpass, not butterworth. No caller…, history is always a list" must hold on every derivation path. An earlier…, copy(deep=True) is the default path; deepcopy(None) is None., list('note') would give four single-character entries., zscale() routes through _create_new_with_data's list(...) call., No .iloc first - that would normalise before the helper runs. The earlier… (+17 more)

### Community 16 - "TestMathematicalOperations"
Cohesion: 0.08
Nodes (14): fixture, Test absolute value operations., Test method chaining works correctly., Test that arithmetic operations return baseTs objects., Test mathematical operations with pandas Series foundation., Generate diverse test data., Generate a noisy signal for filtering tests., Generate time series data for enhanced method testing. (+6 more)

### Community 17 - "_gapped"
Cohesion: 0.09
Nodes (15): _gapped(), baseTs, parametrize, interp_to_uniform_grid: fill_value pads outside the data, max_gap refuses to…, A grid point landing exactly on a sample is data, not a bridge., Parameters go before '; ' so averaging treats equal calls as one step and…, Ten trials of different lengths, one call each, then average., A trial of n samples at 1/dt Hz, data == time so interpolation is exact. (+7 more)

### Community 18 - "time_to_idx"
Cohesion: 0.04
Nodes (46): Multiplication operation returning a baseTs object., _coerce_lag(), idx_to_time(), Convert a lag to a float, or say which argument is wrong. validate_lag is the…, Convert an index to a time value. Args: lag_idx: Index to convert freq:…, Convert a time value to the nearest whole number of samples. Args: lag_secs:…, time_to_idx(), Existing code that names the domain type must be unaffected. (+38 more)

### Community 19 - "TestFilteringOperations"
Cohesion: 0.08
Nodes (14): Test filtering operations., Test lowpass filtering., Test highpass filtering., Test bandpass filtering., Test Savitzky-Golay filtering., Test Gaussian filtering., Test chaining multiple filters., Test edge cases and error handling. (+6 more)

### Community 20 - "TestTheConstructorConvertsAStampedIndex"
Cohesion: 0.13
Nodes (5): TimeSeriesData is the door; baseTs only rides through it., Seconds are counted from index[0]; an unsorted index goes negative. The rule is…, Parity with the numeric index, which admits NaN., The origin has to be a stamp; NaT would make every second NaN and the offset…, TestTheConstructorConvertsAStampedIndex

### Community 21 - "test_pandas_compat.py"
Cohesion: 0.06
Nodes (20): fixture, parametrize, Regression tests for pandas API removals. Each test here corresponds to an API…, baseTs.duration() shadowed the guarded TimeSeriesData.duration()., get_statistics() calls duration(), so it inherited the crash., `freq is np.nan` only matched the one np.nan object., Previously this silently produced an all-NaN time index instead of raising,…, Deriving freq from the times array must still work. NB: the derived value is… (+12 more)

### Community 22 - "test_integer_parameter_policy.py"
Cohesion: 0.06
Nodes (27): Apply a Savitzky-Golay filter to the input data. Args: data: Input data array…, sg_filter(), int, _bandpass(), _data(), _IntegralThatRefuses, fixture, parametrize (+19 more)

### Community 23 - "test_conversion_preserves_metadata.py"
Cohesion: 0.14
Nodes (10): carrying(), fixture, Converting a series must not reset what it was carrying (issue #57).…, The conversion branch was gated on `.times` and `.data`. Only `baseTs` defines…, An empty carried history must not become a fabricated creation entry. The…, A series with every metadata value moved off its default., The ordinary path must still start from defaults, not from nothing. Nothing is…, TestAnEmptyHistoryIsAHistory (+2 more)

### Community 24 - "TestWindowGuard"
Cohesion: 0.11
Nodes (9): parametrize, A window of <= 3 points makes LOWESS interpolate the data exactly. The fit is…, The same default frac that is fine at n=500 is degenerate at n=20., The suggested frac must actually satisfy the guard., k == 4 must be allowed: the guard rejects degenerate, not merely small., A run starting at exactly k == 4 falls to k == 3 after one removal. The loop…, NaNs do not count towards the window: 500 slots, 10 real points., The issue was reported through lowess_detrend, which returned all-zero… (+1 more)

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

### Community 31 - "test_frame_broadcast_equals_series.py"
Cohesion: 0.21
Nodes (14): _columns(), _frame(), _lone(), baseTs, parametrize, A broadcast column must equal the same call made on a lone baseTs. This is the…, A transform added later without a frame test fails here, rather than being…, State the rule, don't maintain a carve-out list: TRANSFORMS is every baseTs… (+6 more)

### Community 32 - "test_figures.py"
Cohesion: 0.22
Nodes (10): _load_figures_module(), parametrize, The figures in `imgs/` are claims, so they are tested like claims.…, Every PNG in imgs/ comes from a builder. No strays, no leftovers., A figure nothing displays is a figure nothing keeps honest., `examples/` is deliberately not a package - it must not be installed., test_every_figure_builds_without_warning(), test_every_figure_is_referenced_by_the_docs() (+2 more)

### Community 33 - "parametrize"
Cohesion: 0.18
Nodes (9): parametrize, Four NaN samples in, six hundred NaN out, silently (#48). filtfilt's…, Same guard, same exception type; since #81 the Inf half of the message names…, filtfilt handles complex input correctly - it filters the real and imaginary…, A bad call is a bug in the call; bad data is a property of the input. The cheap…, validate_band_params checks hp_hz and the ordering *after* the delegated…, Executed, not just named: #28's first attempt recommended a remedy that…, sg_filter and gauss_filter are convolutions, not bidirectional IIR passes: a… (+1 more)

### Community 34 - "figures.py"
Cohesion: 0.13
Nodes (21): fig_band_power(), fig_despiking(), fig_gap_order(), fig_staircase_trap(), fig_test_retest(), icc2_1(), _long_signal(), The figures in `imgs/`, generated from the library rather than drawn by hand.… (+13 more)

### Community 35 - "test_frame_review_findings.py"
Cohesion: 0.19
Nodes (16): _frame(), parametrize, Regressions from Phase 3 adversarial review of the baseDf implementation. Two…, test_average_by_col_meta_flags_stay_python_bool(), test_average_by_refuses_a_column_with_no_grouping_key(), test_average_by_refuses_grouping_by_a_non_scalar_field(), test_average_by_refuses_rather_than_crashes_when_every_key_is_missing(), test_broadcast_col_meta_flags_stay_python_bool() (+8 more)

### Community 36 - "TestBaseTsConversionPreservesMetadata"
Cohesion: 0.09
Nodes (12): parametrize, The conversion branch takes its index from the source, so a `times` argument…, Preserving what was not passed must not ignore what was. The fix distinguishes…, `history=None` is the documented way to ask for a fresh entry. Folding it into…, `baseTs(ts)` is a conversion, not a reset., The sharpest edge: a converted object claimed to be freshly made. Verbatim, not…, #15's guard, which was the only name that already worked., Assigned through the public properties, these were cleared to None. Read back… (+4 more)

### Community 37 - "Design"
Cohesion: 0.11
Nodes (18): Behaviour changes, Deep copy and detachment, Design, Documentation, Eager release on derivation, Order of checks, Pickles written before this change, Problem (+10 more)

### Community 38 - "test_plot_accessor.py"
Cohesion: 0.10
Nodes (11): close_figures(), fixture, parametrize, Tests for the hybrid baseTs.plot accessor. `plot` was a plain alias for…, The historical spelling must be unchanged., The accessor is a property, so it must follow the preserved type., Each accessor plots its own data, not the parent's., TestAccessorSurvivesOperations (+3 more)

### Community 39 - "validate_finite_data"
Cohesion: 0.06
Nodes (31): Reject sample values an FFT cannot produce a meaningful spectrum from. The…, validate_finite_data(), #77 keyed the hint on a leading NaN so as not to name a second remedy that does…, Executed, not just named: the issue's own example, then the leading-Inf variant…, TestTheInfHalfOfTheRemedy, pandas' default limit_direction='forward' fills nothing before the first valid…, While #81 was open the hint keyed on a leading NaN only: interpolate_gaps()…, The alternative to the edge fill is to drop what precedes the first valid… (+23 more)

### Community 40 - "TestMetadataPropagation"
Cohesion: 0.09
Nodes (11): The __finalize__ concat special-case exists for nlargest/nsmallest's internal…, pandas' default __finalize__ assigns metadata by reference, so parent and child…, pandas' _inplace_method reindexes the result back to self before adopting it.…, TimeSeriesData never set outlier_filter despite declaring it in _metadata, so a…, baseTs(ts) takes the conversion branch in TimeSeriesData.__init__, which…, Every parameter used to carry a real default, so naming frac also set…, The whole design rests on this: a frozen config plus a rebinding…, Two series built from one list would cross-contaminate. (+3 more)

### Community 41 - "._enhanced_process_with_flags"
Cohesion: 0.08
Nodes (15): Refuse, or warn about, a gapped index before a filter runs. The NaN guard in…, Apply a notch filter at the specified frequency. The stopped band is `cutoff_hz…, Apply a notch filter at the specified frequency (alias for notch_at). Args:…, Apply a highpass filter at the specified cutoff frequency. Args: cutoff:…, Apply a highpass filter at the specified cutoff frequency (alias for…, Apply a Gaussian filter to the data. Args: sigma: Standard deviation for…, Apply a Savitzky-Golay filter to the signal. Args: window_length: Length of the…, Helper method to update object flags. (+7 more)

### Community 42 - ".__init__"
Cohesion: 0.06
Nodes (28): _median_interval(), Any, array, DataFrame, ndarray, setter, Interpolate data to a uniform sampling grid. If new_grid is not specified, use…, Set to NaN, in place, the grid points bridging a gap wider than max_gap. A grid… (+20 more)

### Community 43 - "shift_timeseries"
Cohesion: 0.06
Nodes (33): _blank_head(), Validate lag parameters. Args: lag: Lag value lag_idx: Lag index lag_unit: Unit…, Return a copy of `arr` whose first `k` entries are the dtype's missing value.…, Shift a time series by a lag value. Args: ts: Time series object with data and…, shift_timeseries(), validate_lag(), _closed(), _five() (+25 more)

### Community 44 - "TestEffectiveFrequency"
Cohesion: 0.09
Nodes (12): n samples span n-1 intervals., rolling() does not call __finalize__, so freq is recomputed from the index - it…, nlargest(3) is excluded from the op list above - it is the one op there that…, #19: resample changes the time base, so the carried freq described the old…, An explicitly supplied freq may legitimately disagree with the times it was…, #19: arithmetic on two different time bases must derive from the union index…, #19: interpto_samples assigned n/duration over the corrected derivation., #19: same n/duration error as interpto_samples. (+4 more)

### Community 45 - "._wrap_result_as_basets"
Cohesion: 0.10
Nodes (13): The source span the two resamplers spread their grid across. Shared by…, Interpolate the times to a new length. Args: new_len (int): The desired new…, Compute the cumulative sum of the timeseries., Create a copy of the baseTs object. Args: deep: Whether to make a deep copy…, Detrend the data by subtracting a robust LOWESS fit. The trend is the LOWESS…, Resample onto a uniform grid at exactly new_freq. The grid is built from the…, _carry_identity(), _detach_shared_metadata() (+5 more)

### Community 46 - "stamped"
Cohesion: 0.13
Nodes (8): numeric_twin(), Same data on the same seconds: bit-identical results., The seconds index is what is resampled, so a series starting at 08:00 has day…, `_update_series_data`'s no-span shrink slices the index it has; on `main` that…, stamped(), TestTheFourMethodsThatRaisedNowAgreeWithTheNumericTwin, TestTheOriginSurvivesEveryDerivation, TestTheTimesSetterIsTheOtherDoor

### Community 47 - "frame.py"
Cohesion: 0.09
Nodes (35): The warnings.warn stacklevel that lands on the first caller outside this…, _stacklevel_outside_package(), _make_broadcast_method(), default_col_meta_row(), harvest_col_meta(), hydrate_column(), _IndexMeta, Any (+27 more)

### Community 48 - "baseDf API Documentation"
Cohesion: 0.08
Nodes (25): `average_by(by, select=None, where=None, skipna=False, min_count=None)`, `average(select=None, where=None, skipna=False, min_count=None, name=None)`, Averaging, `baseDf`, baseDf API Documentation, `baseDf.from_csv(path, time_col="time", value_cols=None, freq=np.nan, ts_offset=np.nan, col_meta=None, **read_csv_kwargs)`, `baseDf.from_df(df, time_col="time", value_cols=None, freq=np.nan, ts_offset=np.nan, col_meta=None)`, `baseDf.from_parquet(path, time_col="time", value_cols=None, freq=np.nan, ts_offset=np.nan, col_meta=None, **read_parquet_kwargs)` (+17 more)

### Community 49 - "baseDf"
Cohesion: 0.13
Nodes (18): baseDf, Span of the shared index in seconds. Returns: float: The duration, which is a…, The values as a plain DataFrame - the escape hatch to pandas., One row of metadata per column., The shared index, in seconds., A set of time series sharing one index. Attributes: df: The values, as a plain…, _frame_df(), DataFrame (+10 more)

### Community 54 - "TestDuplicateLabelRefusal"
Cohesion: 0.17
Nodes (7): The restore arm, exercised directly. Since the pre-commit check landed, no path…, An error that names a remedy is code; the remedy must run. This repo shipped an…, The remedy that was there before, and why it was wrong. `ts.data = ...`,…, A diagnosis must not become the payload. Naming every duplicated label built an…, Bounding the message must not stop it being useful., The check must hand back what it built, not drain the caller's. Building a…, TestDuplicateLabelRefusal

### Community 55 - "TestNoWriteThrough"
Cohesion: 0.33
Nodes (3): outlier_indices is a mutable list; two objects must not share one., interpolate_gaps keeps the index and, on gap-free data, the values, so the list…, TestNoWriteThrough

### Community 56 - "test_qc_plot.py"
Cohesion: 0.20
Nodes (13): _close_figures(), fixture, parametrize, Tests for filter_outliers(qcplot=True). The QC plot exists to show the filter's…, The plotting path must not become a second route to the #6 bug., Asking for a plot must not change what the filter returns., spiked_ts(), test_lowess_fit_trace_is_present() (+5 more)

### Community 57 - "TestHistoryNoneSurvivesRealOperations"
Cohesion: 0.26
Nodes (5): The None-history guard must hold on the paths users actually take. Guarding…, zscale() dies in _create_new_with_data's history.copy()., info() iterates history; None raised TypeError., __finalize__ turns a propagated None into a list., TestHistoryNoneSurvivesRealOperations

### Community 58 - "_degenerate"
Cohesion: 0.17
Nodes (8): _degenerate(), Index mode on a degenerate base with a usable integer lag. Both returned…, Every timestamp identical, so the derived rate is NaN. This is the object from…, The rate must be rejected where it enters the conversion. Each of these fails…, The silent half of #32. On main this returns successfully with `lag_secs=nan`:…, Index mode is `lag_plot`'s default, and on main it draws a plot titled "nan…, `baseTs.lag_plot` delegates, so it must not need its own check., TestADegenerateTimeBaseIsDiagnosed

### Community 59 - "TestFiltersRejectNanFreq"
Cohesion: 0.27
Nodes (4): A degenerate time base must not filter to silent all-NaN output.…, butterpass_at was absent from this family because it never ran (#27). It…, The guard must not disturb an ordinary series., TestFiltersRejectNanFreq

### Community 60 - "test_is_interpolated_means_one_thing.py"
Cohesion: 0.07
Nodes (22): Interpolate missing values in the data. Linear interpolation across every NaN,…, interpolate_missing_values(), baseTs, Interpolate missing values in a time series. Args: ts: Time series object…, _clean(), _gappy(), parametrize, `is_interpolated` means one thing, and every producer follows it (#90). The… (+14 more)

### Community 61 - "File Structure"
Cohesion: 0.13
Nodes (14): baseDf Multichannel Container Implementation Plan, File Structure, Global Constraints, Self-Review Notes, Task 10: Full-suite verification, Task 1: Metadata split — `frame_meta.py`, Task 2: The container — state, invariants, refusals, Task 3: Entry points — `from_df` and `from_series` (+6 more)

### Community 62 - "Carrying pandas' identity fields across derivation (#35, #39)"
Cohesion: 0.10
Nodes (19): Carrying pandas' identity fields across derivation (#35, #39), Decisions taken, Deliberately not in scope, Design, Half A — `_name` joins `_metadata`, Half B, Group 1 — one door for the identity triple, Half B, Group 2 — collapse three doors into one, Making a tenth site fail loudly (+11 more)

### Community 63 - "test_derived_lowess_invalidation.py"
Cohesion: 0.13
Nodes (10): _close_figures(), filtered(), fixture, parametrize, Tests for #20: lowess_fit and outlier_indices on derived objects. `lowess_fit`…, A filtered series carrying a real fit and a real outlier record., The operator dunders do not route through __finalize__. `__add__` and friends…, A scalar cannot change the index, so the index rule must not fire. Zero, so the… (+2 more)

### Community 64 - "_crash_session"
Cohesion: 0.20
Nodes (5): _crash_session(), A 30 Hz session with n_gaps holes, each `missing` frames wide. Built in frame…, Every column shares one index, so the gap warning is the same for all of them;…, TestSegments, TestWarningIdentity

### Community 65 - "Any"
Cohesion: 0.13
Nodes (14): _deepcopy_if_mutable(), Any, Deep-copy a mutable metadata value, sharing everything else. Used by…, Run one baseTs measurement on every column and collect the results. Args: name:…, fALFF per column. See ``baseTs.falff``. Returns: pd.Series: One value per…, Relative band power per column. See ``baseTs.relative_band_power``. Returns:…, Summary statistics per column. See ``baseTs.get_statistics``. Returns:…, Outlier mask per column. See ``baseTs.detect_outliers``. Returns: pd.DataFrame:… (+6 more)

### Community 66 - "TestLowessDetrend"
Cohesion: 0.16
Nodes (9): Tests for lowess_detrend, centred on its inplace=False purity contract., Guard for the purity tests below. They assert that self.data survives…, Issue #6: the caller's object must survive a non-inplace detrend., Issue #6: detrending must not rewrite the caller's filter config.…, The inplace path removes the trend and reports the fit it used., Detrending subtracts a robust trend from the *original* data. The spikes are…, Regression guard for the is_outlier_filtered decoupling. lowess_detrend…, frac is a LOWESS bandwidth in (0, 1] and is rejected up front. statsmodels… (+1 more)

### Community 67 - "test_frame_measurements.py"
Cohesion: 0.30
Nodes (11): _frame(), Measuring a frame gives one value per column, keyed by column label., test_a_mapping_measure_gives_a_dataframe(), test_a_per_sample_measure_gives_a_frame_shaped_result(), test_a_scalar_measure_gives_a_series_keyed_by_column(), test_a_scalar_measure_matches_the_lone_series(), test_a_shared_axis_measure_returns_the_axis_once(), test_an_object_measure_gives_a_series_of_objects() (+3 more)

### Community 68 - "_apply_duplicate_label_declaration"
Cohesion: 0.16
Nodes (8): _apply_duplicate_label_declaration(), Carry `allows_duplicate_labels`, diagnosing pandas' refusal. Setting the flag…, _Flags, Only a *stale* shadow is dropped, not any shadow. Deleting unconditionally also…, A stand-in whose flag setter raises what the caller chooses., Raising pandas' real class, not a look-alike. An earlier version of this test…, Not everything the setter can raise is a duplicate-label refusal. Converting…, _RefusingTarget

### Community 69 - "TestLabelMetadataSurvivesDerivation"
Cohesion: 0.20
Nodes (8): parametrize, signal_name and last_process are always strings" - same defect class. Issue #33…, A number is as fatal to `name + " " + process` as a None is. On the…, The live crash: TypeError: unsupported operand 'NoneType' + 'str'., Restoring a default must not rewrite a name someone chose. Deliberately already…, The normaliser must restore a default, never impose one. A fix that assigned…, TestAConfiguredFilterIsNotReplaced, TestLabelMetadataSurvivesDerivation

### Community 70 - "baseTs"
Cohesion: 0.14
Nodes (10): baseTs, Findings from adversarial review of the first cut., searchsorted on the start value found the first copy, putting the gap inside…, A NaN in the index made the median NaN, every comparison False, and the filters…, Half the steps zero-width drove the median to 0, so every normal step became a…, All timestamps equal breaks the duplicate rule too, but the existing contract…, median_dt was computed outside the validated path, so a decreasing index showed…, np.rint rounds half to even, so 2.5 and 3.5 frames went opposite ways. (+2 more)

### Community 71 - "TestBaseTsInitialization"
Cohesion: 0.17
Nodes (7): Tests for baseTs initialization and basic properties., Test initializing baseTs with data and times., Test initializing baseTs with data and frequency., Test initialization validation requirements., Test length and duration calculations., Test creating baseTs from DataFrame., TestBaseTsInitialization

### Community 72 - "Design: `baseDf` — many time series on one shared index"
Cohesion: 0.12
Nodes (16): Construction, Correlation, Decision 1 (Stan, 2026-09-13): DataFrame-backed, not DataFrame-subclassed, Decision 2 (Stan, 2026-09-13): flat columns now, MultiIndex-tolerant, Design: `baseDf` — many time series on one shared index, Error handling, Indexing, Intent (+8 more)

### Community 73 - "Derived `freq`: closing #29, #31 and #23"
Cohesion: 0.14
Nodes (13): 1. The `freq` property, 2. Propagation, 3. Validation at production sites (#31), 4. `interpto_hz` (#23), 5. Deletions, 6. Edge cases, Approach, Consequences (+5 more)

### Community 74 - "TestDeepCopyIndependence"
Cohesion: 0.29
Nodes (3): `copy(deep=True)` must hand back arrays the parent does not share. Both copy…, The constructor types this as np.array, so a list check is not enough., TestDeepCopyIndependence

### Community 75 - "TestTheInvalidParameterContractIsComplete"
Cohesion: 0.27
Nodes (5): Every known bad input raises InvalidParameterError, enumerated. The CHANGELOG…, Every known bad input raises, with the message its own guard makes., The number in the prose is asserted against the table. Adding a case without…, A fragment true of another case's message pins nothing. Three fragments were…, TestTheInvalidParameterContractIsComplete

### Community 76 - "epoch_seconds"
Cohesion: 0.13
Nodes (10): epoch_seconds(), Two series of one origin on interleaved grids align onto their union, which…, The common case: same grid, so the union is the grid itself., Review round 1 (consensus panel, codex + agy): the first cut converted in…, `reindex` builds through the constructor and then `__finalize__` copies the…, The stamp is set where the origin is, in `_set_axis`, so a later replacement of…, The hardcoded copy list overwrote the fresh origin with the parent's: 2024…, No package path hands a stamped index here; pinned directly. (+2 more)

### Community 77 - "coerce_numeric_data"
Cohesion: 0.08
Nodes (22): coerce_numeric_data(), _complex_data_message(), The rejection text for complex sample values (issue #43). `what` describes the…, Return `data` as an array with a dtype numeric code can loop over. The dtype…, _as_object(), parametrize, Object-dtype data reaching numeric code, and the Inf half of the NaN remedy.…, Classified by what the elements *are*, not by whether a float() parse would… (+14 more)

### Community 78 - "InvalidParameterError"
Cohesion: 0.09
Nodes (39): ArrayLike, _as_filterable(), _as_real_float(), FilterConfig, highpass_filter(), InvalidParameterError, lowpass_filter(), _notch_bounds_hz() (+31 more)

### Community 79 - "plot_fft_power"
Cohesion: 0.09
Nodes (31): plot_fft_power(), Plots the power spectrum of a timeseries signal using enhanced FFT with…, Tests for issue #34: plot_fft_power must raise, not draw the error.…, ts.plot_fft_power() is the path users actually call., setup_plot used to run before the guard, so every failure left a figure. In a…, A caller passing ax= gets it back as they left it, not titled and annotated., The band check ran after the spectrum was already plotted. Ordering matters for…, The consequence users actually meet, and the fix the docs name. Since #36… (+23 more)

### Community 80 - "test_user_guide_examples.py"
Cohesion: 0.29
Nodes (9): fenced_python_under(), Executable pins on the worked examples in docs/USER_GUIDE.md. The example is…, The first ```python block after the given markdown heading line., Execute a doc block and return its namespace. The guide's opening block does…, Issue #44: a self-referential dict literal and a cutoff at Nyquist. The Nyquist…, The `quality_score < 0.95` branch, which the example's own data never takes.…, run_example(), test_example_4_enhanced_cleaning_branch_completes() (+1 more)

### Community 81 - "core.py"
Cohesion: 0.18
Nodes (19): _is_unset(), True if a numeric argument was not supplied. The constructor uses np.nan as its…, hist(), lag_plot(), plot(), plot_series(), array, Axes (+11 more)

### Community 82 - "TestOutlierFilterSurvivesDerivation"
Cohesion: 0.16
Nodes (9): _cleared_filter(), A series whose filter has been cleared - the state issue #33 reports., outlier_filter is always a filter" must hold on every derived object. Without…, __finalize__ copies the parent's None; the chokepoint must fix it., zscale() routes through _create_new_with_data, not __finalize__., info() reads outlier_filter.config to print the filter block., The filter itself is read off the object, so it died here too. Long enough for…, The deliberate boundary of a chokepoint fix, pinned so it is visible.… (+1 more)

### Community 83 - "test_data_stamp_invalidation.py"
Cohesion: 0.19
Nodes (10): _close_figures(), filtered(), gapped(), fixture, Tests for #40: lowess_fit and outlier_indices on an object whose values…, Both producers assign the data first and the slot second. That ordering is now…, A filtered series carrying a real fit and a real outlier record., Filtered, with a pre-existing NaN the filter leaves alone (#36). (+2 more)

### Community 84 - "_ts"
Cohesion: 0.11
Nodes (22): _as_object(), parametrize, Object-dtype data reaching the spectral family and gauss_filter (#93). The same…, The constancy threshold (`np.std(data) < 1e-15`) was always taken on a float64…, compute_fft_power demeans in place on the array it computes with. The guard…, `astype(float, copy=False)` hands a float64 series' own array back, so…, #93 dropped get_frequency_content's copy on the strength of "nothing below…, For the spectral family this held before #93 (the guard ran, its result was… (+14 more)

### Community 85 - "TestInvalidationOnInPlaceIndexChange"
Cohesion: 0.15
Nodes (6): The index can change without any derivation at all., `.index` is pandas' own setter, and `.times` is not the only door., The inplace branch calls pd.Series.__init__ directly, bypassing…, The data setter rebuilds the index when the length changes., Same length keeps the index; equal values keep the fit (#40). Assigning zeros…, TestInvalidationOnInPlaceIndexChange

### Community 86 - "test_type_preservation.py"
Cohesion: 0.18
Nodes (7): fixture, Tests that pandas operations preserve the baseTs type and its metadata. Before…, The documented pattern: a pandas op followed by a baseTs op., pandas builds subclasses as _constructor(values, index=...)., pandas looks this up on the class; a plain method breaks that., TestTypePreservation, ts()

### Community 87 - "TestTheOriginDescribesTheIndexItWasRecordedAgainst"
Cohesion: 0.11
Nodes (12): The case the healing made permanent: the pair survived an index replacement…, The remedy names a value, and on a pre-#100 object the stored one is the wrong…, It cannot say which index its offset described., The offsets agreed, so the arm re-stamped the merged index and read the stale…, Review round 2 (consensus panel, codex + agy): the pair rode along through…, `_update_inplace` swaps the manager without `__finalize__`; the read-time check…, The package's door asserts the base; pandas' door does not., `ts.index = ...` is the door `reset_index(inplace=True)` uses to install… (+4 more)

### Community 88 - "parametrize"
Cohesion: 0.11
Nodes (9): parametrize, pandas supports `for window in ts.rolling(3): ...`, yielding each window as its…, The contract is behavioural, not identity. FilterConfig is frozen and…, Independence must not cost the config: the values still carry over., Arithmetic returns via _wrap_result_as_basets, which assigned every metadata…, pandas implements `ts += 1` by calling __add__ and keeping only the values,…, _create_new_with_data omitted outlier_filter from the attributes it carries, so…, ts is uniformly sampled, so every op here should agree with it. (+1 more)

### Community 89 - "_FinalizingWindow"
Cohesion: 0.12
Nodes (11): deepcopy_metadata_value(), _FinalizingWindow, Any, Wraps a pandas window object (Rolling/Expanding/ExponentialMovingWindow) so its…, Python looks up dunder methods on the type, bypassing __getattr__, so this…, See _FinalizingWindow: rolling()/expanding()/ewm() never call __finalize__., Rolling window whose aggregations propagate metadata - see _FinalizingWindow., Expanding window whose aggregations propagate metadata - see _FinalizingWindow. (+3 more)

### Community 90 - "TestTheDisplayBoundsAreValidatedBeforeDrawing"
Cohesion: 0.17
Nodes (6): The frequency bounds reach ax.set_xlim, which rejects NaN and Inf. An infinite…, NaN is the documented public sentinel for max_rate - not an error., min_rate has no sentinel, so NaN is simply invalid there., Pins the shared door's ndarray branch, which mutation testing found bare.…, The other half of that branch: 0-d arrays convert alike on both majors., TestTheDisplayBoundsAreValidatedBeforeDrawing

### Community 91 - "parametrize"
Cohesion: 0.15
Nodes (9): parametrize, ValueError, matching every other bound failure in this function. '30' and True…, `band_low >= band_high` is False for NaN, so a NaN edge passed the guard. Pre-…, One ValueError for every malformed band, from two different doors. The 1- and…, One contract for the whole function, generated from a census against main.…, Newly accepted, in the opposite direction to the rest of the census. On main…, test_every_rejected_input_raises_valueerror_and_draws_nothing(), test_high_precision_bounds_are_now_accepted() (+1 more)

### Community 92 - "TestEveryBandpassEntryPointRejectsABadLowerEdge"
Cohesion: 0.43
Nodes (3): The contract must hold on all three names, on the axis it is about. #28's…, Reachable at all only since #27, which was dead before it., TestEveryBandpassEntryPointRejectsABadLowerEdge

### Community 93 - "Axes"
Cohesion: 0.29
Nodes (4): Axes, Plot this timeseries against one or more other timeseries. e.g. for QC,…, Plot a histogram of the timeseries., Plot a lag plot of the timeseries.

### Community 94 - "get_lags"
Cohesion: 0.06
Nodes (25): get_lags(), Get lag values in both seconds and indices. Args: lag: Lag value lag_unit: Unit…, _declared(), _derived(), parametrize, Every length from 100 to 2000 at a nominal 100 Hz, three lags. The issue…, The tie rule is Python's, stated so it is not mistaken for drift. A lag that…, `round()` on a float returns int; `validate_lag` insists on it. (+17 more)

### Community 95 - "TestLabelMetadataAtConstruction"
Cohesion: 0.31
Nodes (4): The constructor kwargs are a door of their own, and one was left open.…, TypeError: can only concatenate str (not "NoneType") to str., The sibling door, already closed - here so the pair stays closed., TestLabelMetadataAtConstruction

### Community 96 - "test_spectral_empty_series.py"
Cohesion: 0.19
Nodes (12): _empty(), parametrize, An empty series is rejected by every spectral entry point, from one door (#62).…, Precedence for a series wrong in both ways: empty, and no usable rate. The door…, `utils.validate_non_empty` is the one definition., Emptiness only: a NaN is `validate_finite_data`'s to reject, and a 0-d array…, The whole family, not just the one sibling that already checked. `match` pins…, No RuntimeWarning on the way to the error. `relative_band_power` takes `np.std`… (+4 more)

### Community 97 - "TestHistoryNoneGuard"
Cohesion: 0.29
Nodes (4): A `history` of None must not crash the next operation (issue #22). __finalize__…, The superclass guard is hasattr-only, so None slips past it too., The guard must not discard a history that is genuinely present., TestHistoryNoneGuard

### Community 98 - "test_docs_fenced_blocks.py"
Cohesion: 0.09
Nodes (26): Block, blocks_in(), _execute(), _literal_default(), outcome(), parametrize, python_fences(), Every fenced Python block in docs/ runs (#69). The document is the source of… (+18 more)

### Community 99 - "TimeSeriesData"
Cohesion: 0.06
Nodes (19): Pandas Series subclass optimized for time series analysis. This class extends…, pandas' in-place door: swap the manager, then narrow the stamp.…, Return constructor for pandas operations., Return constructor for sliced operations., Get the length of the time series (backward compatibility). Returns: Number of…, Helper method to update object flags., Addition operation returning a baseTs object., Right addition operation returning a baseTs object. (+11 more)

### Community 100 - "test_frame_correlation.py"
Cohesion: 0.30
Nodes (13): _left(), baseTs, parametrize, Correlating a frame: one seed against every column, or frame against frame., _right(), _seed(), test_a_frame_passed_to_correlation_with_is_refused(), test_a_seed_gives_one_value_per_column() (+5 more)

### Community 101 - "_ts"
Cohesion: 0.12
Nodes (15): _close_figures(), fixture, parametrize, `signal_name` and `last_process` are always strings, in place too (#61). #33…, The public names stay in `_metadata`; propagation runs the setter., A blob written before this change can hold `None` under the public name - #33…, The getter defaults rather than raising: pandas can build a subclass instance…, The half #33 left open: the object you mutate, not the one you derive. (+7 more)

### Community 102 - "._data"
Cohesion: 0.08
Nodes (20): notch_filter(), Apply a symmetric notch filter to the input data. The stopped band is…, #76: notch_filter validated `cutoff_hz` against (0, Nyquist) and then stopped…, One message for every out-of-range cutoff, so the limits it quotes are the…, Drift guard for the stated rule. The stopped band is `cutoff +/- 1% of…, The parameter rule before the O(n) data scan, the #48 ordering: a mistyped…, The limits a retry has to meet, in Hz, both of them. Review found the first cut…, All of these must raise; four of the seven previously did not. The negative,… (+12 more)

### Community 103 - "_named"
Cohesion: 0.13
Nodes (12): _named(), parametrize, The signal name's case follows one rule on every derivation (issue #56). The…, A name the caller passes is a constructor argument, not an inheritance, so it…, Distinct from the mixed case: `.title()` or `.capitalize()` in place of a…, The live symptom: the same series titled two ways., The name was never part of the metadata that flag withholds., Copying the name verbatim must not reopen what #33 closed: the constructor used… (+4 more)

### Community 104 - "TestArgumentOrder"
Cohesion: 0.17
Nodes (14): _assert_same_spectrum(), parametrize, compute_fft_power computes on a float64 copy of the validated data (#96). The…, The review of #93 built a float32 series the two precisions disagree on:…, numpy 2.x takes the FFT of a float32 array in float32 and returns a float32…, The demeaning is still an in-place subtraction, so the float64 copy is load-…, #93's rule, which the object-array-of-floats tests cannot pin: `np.array(obj,…, `demean=True` on an integer or bool series raised numpy's bare `UFuncTypeError`… (+6 more)

### Community 105 - "TestTheSingleCutoffFiltersUseTheValidatedValue"
Cohesion: 0.08
Nodes (15): _DeclaresOneHz, _LiesAboutDivision, register, Registers as a Real but cannot become one. numbers.Real is a registrable ABC,…, A Real that converts to 1.0 and supports nothing else. Registers, coerces,…, Validation is worthless if the filter then uses a different value. Five review…, It declared float() == 1.0, so 1.0 is what the filter must use., The value validated is the value filtered, whatever __truediv__ says. (+7 more)

### Community 106 - "TestTheStamp"
Cohesion: 0.22
Nodes (3): The wrinkle #20 documented and #40 removes., TestTheStamp, _values()

### Community 107 - "requirements.txt"
Cohesion: 0.20
Nodes (10): Python Package CI Workflow, hypothesis, Matplotlib, moepy, NumPy, Pandas, psutil, pytest (+2 more)

### Community 108 - "_ts"
Cohesion: 0.16
Nodes (10): parametrize, compute_fft_power's constant-signal branch reports the FFT branch's DC bin…, Observed and not changed: a different function, not divided by n., The number the FFT branch would have produced for the same array, computed here…, 600 samples of 3.0, and the same with every other sample raised by 1e-13: std 0…, Under the default scale_power=True the DC bin is the only non-zero one on…, Review round 1: `n * mean**2` reimplements the FFT branch's DC bin rather than…, TestTheConstantBranchReportsTheFftBranchsDcBin (+2 more)

### Community 109 - "TestBaseTsFiltering"
Cohesion: 0.22
Nodes (5): Tests for baseTs filtering functionality., Test highpass filter., Test bandpass filter., Test Savitzky-Golay filter., TestBaseTsFiltering

### Community 110 - "parametrize"
Cohesion: 0.20
Nodes (5): parametrize, Issue #31: a bad rate must be refused where it enters the object., baseTs(data, freq=...) with no times builds the index FROM the rate. freq=0…, baseTs' public default is freq=np.nan, so it cannot mean "invalid". Deliberate…, TestValidationAtProductionSites

### Community 111 - "test_lag_plot_labels.py"
Cohesion: 0.14
Nodes (15): _close_figures(), _labels(), fixture, `lag_plot` labels the plot with the name the series has, and nothing else…, The issue's reproduction, both halves: stdout stays empty, and the placeholder…, `normalise_label`'s rule: a caller who set a number meant it to show., The last re-casing site. `plot()` titles "Heart Rate by time."; the lag plot…, Unchanged for the common path: the constructor upper-cases its own argument… (+7 more)

### Community 112 - "TestTheNaNRemedyClearsAnEdgeGap"
Cohesion: 0.22
Nodes (6): Two paths the hint's caller may be on (review, round 3): the in-place form of…, #77: the NaN message names `interpolate_gaps()`, which forwards pandas' default…, Executed, not just named - the whole point of #77., The asymmetry the hint is built on, pinned: pandas' forward fill extends the…, `limit` is the caller's own constraint and it applies to the edge fill like any…, TestTheNaNRemedyClearsAnEdgeGap

### Community 113 - "TestLegacyPickles"
Cohesion: 0.27
Nodes (3): Every earlier slot shape loads with the fit readable. Built by editing a state…, The pre-#20 attribute accepted a tuple verbatim. A length test reads `(3, 7)`…, TestLegacyPickles

### Community 114 - "TestDerivationPathsAgree"
Cohesion: 0.17
Nodes (4): fixture, A value-sorted series has a non-monotonic index and no honest rate. The carried…, Issue #29's acceptance test. The same index change had two answers depending on…, TestDerivationPathsAgree

### Community 115 - "_freq_token"
Cohesion: 0.29
Nodes (5): _freq_token(), Fingerprint an index for the purpose of sampling-rate derivation. Deliberately…, The token must be exactly the inputs _calculate_effective_frequency reads. That…, And must not: the derived rate is unchanged, so the token is right.…, TestFreqToken

### Community 117 - "bad_rate_ts"
Cohesion: 0.25
Nodes (8): bad_rate_ts(), _close_figures(), good_ts(), nan_data_ts(), fixture, A series with a usable rate and finite data., The issue's own reproduction: every timestamp identical, so freq is NaN., A usable rate carrying gaps - the #28 guard's input.

### Community 118 - "_one_sample"
Cohesion: 0.21
Nodes (8): filterwarnings, _one_sample(), Only the empty series is rejected by the door. One sample is not. A 1-sample…, A confident 0.0 for a spectrum with no peak in it - observed and left as…, The constant-data branch, which runs before the FFT: one sample has a standard…, matplotlib warns about a singular x-range for one point; that is the draw's,…, Its threshold is its own contract and is not the door's., TestTheOneSampleDecision

### Community 119 - "_all_four_entry_points"
Cohesion: 0.12
Nodes (16): _all_four_entry_points(), _analytic_ts(), _leading_gap_ts(), The _gappy_ts sine with the gap at sample 0 instead of sample 100., The spectral family shares the message with the filters, so it shares the trap:…, Executed, not just named: 0.16 Hz is the peak of the gap-free series., The four public ways into an FFT, as zero-argument callables., All four spectral entry points give the same actionable error. They drifted… (+8 more)

### Community 120 - "baseTs Test Suite README"
Cohesion: 0.18
Nodes (7): baseTs Test Suite README, Integration tests for real-world time series workflows. Tests complete end-to-…, Test compatibility across different workflow scenarios., Test workflows mixing different types of operations., Test workflows with conditional logic., Test iterative processing workflows., TestWorkflowCompatibility

### Community 121 - "TestInheritedPandasInplaceMethods"
Cohesion: 0.18
Nodes (5): `inplace=True` on an inherited pandas method swaps the block manager. pandas…, The reported crash, reachable without any baseTs method at all., The silent variant: same length, every position moved., These keep the positions, so the index rule must not fire. On this fixture they…, TestInheritedPandasInplaceMethods

### Community 122 - "TestFiltersRefuseIndexGaps"
Cohesion: 0.16
Nodes (4): parametrize, TestDocstrings, TestFiltersRefuseIndexGaps, _uniform()

### Community 123 - "baseTs"
Cohesion: 0.05
Nodes (27): empty(), one_sample(), baseTs, parametrize, A length-changing `ts.data = x` resamples over the span it has (#65). The rule.…, `except ValueError` is the family's promised catch., An error that names a remedy is code; the remedy must run., Pinned because a mutant that resampled the same-length path too survived every… (+19 more)

### Community 124 - "test_pipeline.py"
Cohesion: 0.20
Nodes (9): Integration tests for baseTs processing pipeline., Test a complete processing pipeline with multiple steps., Test creating baseTs from DataFrame and applying pipeline., Test method chaining for creating a processing pipeline., Test conversions between baseTs and pandas DataFrame., test_complete_processing_pipeline(), test_dataframe_conversions(), test_from_df_to_pipeline() (+1 more)

### Community 126 - "test_gaps.py"
Cohesion: 0.22
Nodes (4): _dropped_frames(), Index gaps: gaps() finds them, segments() splits at them, the filters refuse or…, The mean rate is dragged down by the holes themselves; the median interval is…, TestReporting

### Community 127 - "TestPickleWrittenBeforeTheFix"
Cohesion: 0.26
Nodes (5): A blob already on disk must load too, and that needs more than #35. Adding…, A state dict shaped like a blob written before `_name` was added. Both edits…, The heal must survive the next operation, not just the load. Without this, a…, None, because the name genuinely is not in those bytes. Healing the object must…, TestPickleWrittenBeforeTheFix

### Community 128 - "BandPowerResult"
Cohesion: 0.24
Nodes (10): Compute the relative power (or amplitude) in a frequency band. This is the…, Fractional amplitude of low-frequency fluctuations (fALFF). Convenience wrapper…, BandPowerResult, Detailed breakdown of a relative band power computation. Attributes: ratio: The…, baseTs Changelog, Unreleased: Relative Band Power / fALFF, baseTs 1.0.0 Release (NumPy backend), Keep a Changelog (+2 more)

### Community 129 - "_origin_timestamp"
Cohesion: 0.32
Nodes (7): _origin_timestamp(), The index as calendar stamps: the origin plus each second. The index itself is…, The origin `ts_offset` names, rebuilt at microsecond resolution. A float64…, origin + seconds, as a DatetimeIndex, at the precision the float holds. A…, _stamps_from_seconds(), DatetimeIndex, Timestamp

### Community 130 - "TestReinitHasOneDoor"
Cohesion: 0.24
Nodes (7): _calls_in_own_scope(), Yield the `ast.Call` nodes belonging to `node` itself. A flat `ast.walk`…, `super(TimeSeriesData, self).__init__` may appear in exactly one place. A…, Functions in core.py that re-initialise self through pandas. Parsed, not…, The scan must attribute a call to its *nearest* enclosing function. A flat…, Guards the scan itself against silently matching nothing. An assertion that a…, TestReinitHasOneDoor

### Community 131 - "test_datetime_index_converts_at_the_constructor.py"
Cohesion: 0.17
Nodes (8): from_df(), Create a baseTs object from a pandas DataFrame. Args: df: Input DataFrame…, A DatetimeIndex becomes seconds since its first stamp at the constructor…, A caller asking for relative seconds only. Coherent, so allowed., seconds_since_first(), TestAnExplicitOffsetAlongsideAStampedIndex, TestFromDfAcceptsADatetimeColumn, two_tone()

### Community 132 - "test_frame_copy.py"
Cohesion: 0.53
Nodes (5): _frame(), baseDf.copy(): an independent frame, not a view. Added after Task 9 review:…, test_a_deep_copy_is_independent_of_the_original(), test_a_shallow_copy_shares_the_underlying_frames(), test_copy_is_a_baseDf_with_equal_values_and_col_meta()

### Community 133 - "baseTs"
Cohesion: 0.04
Nodes (36): baseTs, Trims the data between specified timepoints. Args: start_val (float, optional):…, Apply a bandpass filter between two cutoff frequencies (alias for bandpass_at).…, Apply a Butterworth bandpass filter (alias for bandpass_at). Args: hp_freq:…, Compute the first difference of the timeseries. Args: zeropad: If True, the…, A time_slice bound as seconds on the index. A number is seconds on the index,…, Basic data class to hold a timeseries and data. Built on pandas Series…, Compute the FFT power of the timeseries. Computed on a float64 copy of the… (+28 more)

### Community 134 - "TestStaircaseTrapFigure"
Cohesion: 0.25
Nodes (3): CHANGELOG 0.3.0: 141 of 262 real cpCST series hit the residual-scale floor at…, The caption says so, because it is the counter-intuitive part: widening a…, TestStaircaseTrapFigure

### Community 135 - "TestDespikingFigure"
Cohesion: 0.25
Nodes (4): filter_outliers() flags, then replaces. Both halves are drawn., The caption's central claim: nothing is dropped, nothing goes NaN., The distinction the zoom panel is drawn to make, and the one an earlier draft…, TestDespikingFigure

### Community 136 - "TestBandPowerFigure"
Cohesion: 0.33
Nodes (3): A band ratio is only readable against its null., The first draft ran on the 10 s signal, whose 0.1 Hz bins drew the peaks as…, TestBandPowerFigure

### Community 137 - "parametrize"
Cohesion: 0.29
Nodes (4): parametrize, Memory: a stale slot would pin the parent's fit and snapshot., Its docstring says outlier_indices is left alone; detrending changes the…, TestValueChangingDerivationsDropBoth

### Community 138 - "TestTheStampIsNotLaunderable"
Cohesion: 0.33
Nodes (3): A copy must move the triple, never re-stamp it. The discriminating derivation…, The behavioural form: a re-stamping copy would look valid here., TestTheStampIsNotLaunderable

### Community 139 - "TestValuePreservingDerivationsKeepBoth"
Cohesion: 0.40
Nodes (3): The discriminating half: same index, same values, a method was called., NaN in the same place compares equal to itself., TestValuePreservingDerivationsKeepBoth

### Community 140 - "TestPlotting"
Cohesion: 0.25
Nodes (4): The reported symptom, and the one plotting path with no guard., plotting.py:87 raised ValueError on mismatched first dimensions., The caller asked for a fit explicitly; silence would be worse., TestPlotting

### Community 141 - "TestTheICCImplementation"
Cohesion: 0.33
Nodes (3): `icc2_1` is hand-rolled, so it is pinned to a published worked example rather…, Shrout & Fleiss report ICC(2,1) = 0.290 for this table., TestTheICCImplementation

### Community 143 - "parametrize"
Cohesion: 0.09
Nodes (11): parametrize, `pd.Timestamp(2592000)` is 2.592 ms into 1970; the rule is `numbers.Real`,…, The load-bearing agreement between the two conversions: the index comes from…, A series built from seconds must come out byte-for-byte as before. The pair's…, The TypeError arm in the rate derivation used to be described as the…, `Decimal` registers under `numbers.Number`, not `numbers.Real`; `main` compared…, A microsecond index from 1700 to 2200 is a valid DatetimeIndex (unit us),…, The remaining keyword combination of the pinned pair table. (+3 more)

### Community 144 - "test_frame_consensus_review_findings.py"
Cohesion: 0.17
Nodes (19): _frame(), Regressions from Phase 3 Round 3: a non-Anthropic consensus review. Two…, test_a_genuine_tuple_selector_still_selects_two_columns(), test_a_tuple_column_label_from_average_by_is_indexable(), test_a_zero_column_dataframe_is_refused(), test_an_empty_mapping_is_refused(), test_average_by_keeps_every_grouping_key_for_a_multi_key_group(), test_average_by_keeps_the_grouping_key_in_the_result() (+11 more)

### Community 145 - "TestTimeSliceTakesCalendarBounds"
Cohesion: 0.12
Nodes (5): fixture, The bound is turned into seconds the way the index was, so a bound that names a…, `Timedelta.total_seconds()` rounds to the microsecond; the bound is placed as…, Whatever the string says: the origin check runs before parsing., TestTimeSliceTakesCalendarBounds

### Community 147 - "TestIndexMutationsWithNoHookAtAll"
Cohesion: 0.22
Nodes (3): The doors that defeated the write-side design. These reach past `__finalize__`,…, The third `pd.Series.__init__` site, and the one an explicit audit for that…, TestIndexMutationsWithNoHookAtAll

### Community 148 - "test_frame_entry_points.py"
Cohesion: 0.20
Nodes (11): DataFrame, Getting into a frame from a wide table or from existing baseTs objects., test_from_df_honours_an_explicit_value_cols(), test_from_df_names_the_non_numeric_columns_it_refuses(), test_from_df_refuses_a_missing_time_column(), test_from_df_sorts_by_time_when_the_table_is_out_of_order(), test_from_df_takes_every_numeric_column_but_the_time_column(), test_from_series_carries_each_series_own_metadata() (+3 more)

### Community 149 - "TestTheStampIsNotLaunderable"
Cohesion: 0.22
Nodes (5): A copy must move the (value, index) pair, never re-stamp it. Any path that…, The discriminating case for laundering. interpolate_gaps routes through…, Memory, not correctness: the getter already reads a slice as None. Without this…, The behavioural form of the laundering check. Starting from a *valid* fit is…, TestTheStampIsNotLaunderable

### Community 150 - "TestTheStampNarrowsToEachDerivation"
Cohesion: 0.20
Nodes (6): Review round 3 (quick-review, a different harness): the subset test is by…, `dropna(inplace=True)` swaps the manager through `_update_inplace`, which…, Positions 0..n-1 of a series whose own seconds are exactly those values read as…, A two-key groupby's MultiIndex cannot be compared with seconds; `Index.isin`…, The one index `_set_axis` could narrow against is a same-length permutation,…, TestTheStampNarrowsToEachDerivation

### Community 151 - ".freq"
Cohesion: 0.25
Nodes (5): setter, Derive the sampling frequency from the time index. Returns NaN rather than…, The sampling rate in Hz, derived from the index unless declared. An explicitly…, Declare an explicit sampling rate against the current index. The single…, String representation of TimeSeriesData.

### Community 152 - "TestSetTimestampOffsetRecordsTheOrigin"
Cohesion: 0.25
Nodes (3): It used to move the index by the offset and record it; the index stays put now.…, Nothing about the index changes, so the declaration's token holds., TestSetTimestampOffsetRecordsTheOrigin

### Community 154 - "baseTs Development Guide"
Cohesion: 0.33
Nodes (7): baseTs Development Guide, Direct Pandas Series Inheritance Architecture, Dual Backend Architecture (removed in v2.0.0), Design Principle: API Stability, Design Principle: Metadata Preservation, Design Principle: Performance, Design Principle: Series-First

### Community 156 - "test_frame_indexing_keeps_col_meta.py"
Cohesion: 0.39
Nodes (8): _frame(), Selecting columns must carry each column's metadata with it., test_a_boolean_mask_selects_columns(), test_a_list_gives_a_frame_and_keeps_the_user_attributes(), test_a_scalar_label_gives_a_real_baseTs(), test_a_selection_matching_nothing_is_refused(), test_an_unknown_label_is_refused_by_name(), test_selection_by_query_uses_the_user_attributes()

### Community 157 - "test_identity_propagation.py"
Cohesion: 0.21
Nodes (7): identity_of(), The three identity fields pandas owns must survive derivation (#35, #39). A…, The bar is pandas' own behaviour, not an invented one. If a future pandas stops…, The three fields as one comparable tuple., `ts += 1` keeps the target's own identity, as stock pandas does. Pinned because…, TestIdentitySurvivesDerivation, TestInplaceArithmeticIsUnaffected

### Community 160 - "_DuckSeries"
Cohesion: 0.22
Nodes (6): _DuckSeries, The other route to a None: the metadata-copy fallback in series.py.…, `is_outlier_filtered` is a flag, and the fallback left it None. The defaulting…, The shape `TimeSeriesData.__init__` treats as a baseTs to convert from.…, TestFlagDefaultsAtConstruction, TestOutlierFilterDefaultAtConstruction

### Community 161 - "TestFlagsAssignmentAssumption"
Cohesion: 0.17
Nodes (7): baseTs, The emptiness guard must not invent a dict where none was set., Why `_carry_identity` may assign the flag rather than AND it. pandas 2.3.3's…, `_copy_metadata_from_basetseries` accepts anything with `.times`/`.data`, so a…, Assignment, not AND - the direction only a direct call can reach. Written…, An operation that cannot keep the declaration must change nothing. Checked…, TestFlagsAssignmentAssumption

### Community 164 - "TestPandasIntegration"
Cohesion: 0.25
Nodes (5): Test direct pandas integration features., Test direct access to pandas methods., Test pandas-style indexing., Test that metadata is preserved through pandas operations., TestPandasIntegration

### Community 165 - "Handoff: #100 — convert a DatetimeIndex to seconds at the constructor"
Cohesion: 0.22
Nodes (8): Decisions taken while implementing (2026-09-05), Design, Docs to update (they currently work around #100 and say so), Handoff: #100 — convert a DatetimeIndex to seconds at the constructor, Tests to write first (TDD; the harness must be red before the code), The task, What is true on `main` at 0cbffcb (all measured, pandas 3.0.1 / numpy 2.5.2), Working rules this arc has settled on (see the memory files for the why)

### Community 166 - "built"
Cohesion: 0.50
Nodes (4): built(), _close_figures(), fixture, Every figure, built once. A build that warns is a build that fails.

### Community 168 - "TestNanFreqIsNotLaundered"
Cohesion: 0.38
Nodes (3): A NaN rate must not become a fabricated healthy number. Reaches a NaN rate…, A real declared rate must survive an index-preserving transform., TestNanFreqIsNotLaundered

### Community 169 - "seeded"
Cohesion: 0.19
Nodes (9): parametrize, Each of these raised AttributeError: no attribute '_name'. Parametrised one…, `inplace=True` mutates the object; it must not reset its identity. This is the…, A baseTs whose three identity fields are all at non-default values. Every field…, The identity fix must not cost what already worked. These survived a re-init…, #39: the round-trip always worked; what came back did not. Stated precisely…, seeded(), TestInplaceMethodsPreserveIdentity (+1 more)

### Community 170 - "test_the_legend_label_keeps_the_callers_own_formatting"
Cohesion: 0.33
Nodes (6): Validation coerces to float; the label must not inherit that. Routing the label…, A generator band worked before; unpacking it twice broke it. An earlier…, The data-space x range of an axvspan patch, on any matplotlib. axvspan returned…, _span_x_extent(), test_a_one_shot_iterable_band_is_unpacked_exactly_once(), test_the_legend_label_keeps_the_callers_own_formatting()

### Community 171 - "TestArithmeticNameFollowsPandas"
Cohesion: 0.39
Nodes (3): The one place carrying `_name` could silently diverge from pandas.…, `result.name` is pandas-resolved whichever dunder produced it., TestArithmeticNameFollowsPandas

### Community 172 - "FilterConfig"
Cohesion: 0.06
Nodes (29): FilterConfig, Created on Oct 19 2024 @author: stan@sympaticog.com, Enum for specifying which tails to process in outlier detection., Configuration parameters for the LowessOutlierFilter. Attributes ----------…, Initialize the LowessOutlierFilter with filtering parameters. Parameters…, TailType, Enum, np.asarray drops a mask and exposes the payload underneath. (+21 more)

### Community 173 - "averaged_row"
Cohesion: 0.29
Nodes (6): averaged_row(), Any, DataFrame, Hashable, The metadata an averaged series is entitled to. Args: col_meta: The frame's…, Average a selection of columns into one series. Args: select: Labels, or a…

### Community 174 - "TestAttrsIsolation"
Cohesion: 0.40
Nodes (3): attrs must be copied, never shared - pandas deep-copies it., A shallow dict copy passes the test above and fails this one. pandas'…, TestAttrsIsolation

### Community 175 - "ValidationError"
Cohesion: 0.09
Nodes (24): _is_listlike(), DataFrame, Hashable, Index, ndarray, Correlate every column against every column of another frame. Never implicit:…, Mean across the chosen columns, and how many timepoints lost contributors., Average columns within each group, giving one column per group. Args: by:… (+16 more)

### Community 178 - "TestMetadataRegistry"
Cohesion: 0.40
Nodes (3): `_metadata` must extend pandas' list rather than replace it., Every name pandas declares must still be carried. Asserted against…, TestMetadataRegistry

### Community 179 - "_PlotAccessor"
Cohesion: 0.20
Nodes (4): _PlotAccessor, Callable proxy backing ``baseTs.plot``. ``plot`` used to be a plain alias for…, Plot the timeseries as a line plot. Quick and dirty visualization., Line plot, or the pandas plotting accessor. Calling it is the historical baseTs…

### Community 180 - "parametrize"
Cohesion: 0.07
Nodes (31): _FreqStub, _gappy_ts(), parametrize, The original zero/negative rejection is preserved. Routed through _FreqStub…, A 0.16 Hz sine over 500 samples with `n_bad` samples replaced by `bad`., The production site raises instead of returning an all-NaN spectrum.…, The headline defect: no confident wrong answer on gappy data. Pins behaviour,…, The guard rejects bad values, not unfamiliar dtypes - and since #75 hands back… (+23 more)

### Community 183 - "TestDeepcopyOfAName"
Cohesion: 0.40
Nodes (3): `_name` now reaches deepcopy_metadata_value; it must pass through., Which is why the isinstance gate in that helper never matches it. Recorded as a…, TestDeepcopyOfAName

### Community 184 - "TestInvalidationThroughCreateNewWithData"
Cohesion: 0.33
Nodes (3): _create_new_with_data copies the metadata slots outside pandas' machinery.…, Same index and same values, so both still describe the result. sg_filter was…, TestInvalidationThroughCreateNewWithData

### Community 185 - "TestDeclarationLifecycle"
Cohesion: 0.25
Nodes (3): An explicit rate is honoured until the index it describes changes., Guards the _freq_declaration entry in _create_new_with_data's metadata_attrs…, TestDeclarationLifecycle

### Community 186 - "_validate_display_rate"
Cohesion: 0.50
Nodes (5): Any, Coerce a frequency bound to a float matplotlib can use as an axis limit. The…, Unpack and coerce a (low, high) band, or raise ValueError naming it. Both edges…, _validate_display_rate(), _validate_highlight_band()

### Community 188 - "_ExtendedForPickling"
Cohesion: 0.40
Nodes (3): _ExtendedForPickling, A subclass adding a `_metadata` name, defined at module level. Module level…, The class-level case, which must keep working either way.

### Community 189 - "TestInterpToHzGrid"
Cohesion: 0.29
Nodes (3): The produced grid must actually have the rate it reports. linspace(t0, t1,…, Regression: a bare floor() drops a trailing sample. (np.arange(1000)/30.0)…, TestInterpToHzGrid

### Community 190 - "test_series_freq.py"
Cohesion: 0.33
Nodes (3): Issue #31's sharpest production site: the one place a user hands baseTs a rate…, Previously returned a length-0 series stamped with the rate. deg.interpto_hz(5)…, TestInterpToHzRejections

### Community 191 - "TestOutlierDetection"
Cohesion: 0.33
Nodes (4): Tests for outlier detection functionality., Test setting outlier filter parameters., Test outlier filtering., TestOutlierDetection

### Community 193 - "basets_owned_inplace_methods"
Cohesion: 0.50
Nodes (3): basets_owned_inplace_methods(), Every public method this package defines that takes `inplace`. Restricted to…, A new `inplace=` method fails here until someone classifies it. The point of…

### Community 195 - "test_utils.py"
Cohesion: 0.03
Nodes (100): Find the closest time in the timeseries to a target time in seconds. Args: sec:…, ClosestMatch, coerce_real_scalar(), compute_fft_power(), _describe(), falff(), find_closest(), find_closest_time() (+92 more)

### Community 197 - "zscale"
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
- **112 isolated node(s):** `baseTs`, `Table of Contents`, ``baseDf``, ``baseDf.__init__(data, times=None, freq=np.nan, ts_offset=np.nan, col_meta=None)``, ``baseDf.from_df(df, time_col="time", value_cols=None, freq=np.nan, ts_offset=np.nan, col_meta=None)`` (+107 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

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