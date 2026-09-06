# Graph Report - baseTs  (2026-09-06)

## Corpus Check
- 72 files · ~214,979 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3018 nodes · 5576 edges · 165 communities (151 shown, 14 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 274 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `41d09964`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- TestRelativeBandPower
- .copy
- LowessOutlierFilter
- TestOutlierFilterSurvivesDerivation
- AdaptiveLowessFilter
- BandPowerResult
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
- test_core.py
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
- shift_timeseries
- TestEffectiveFrequency
- TestInvalidationOnInPlaceIndexChange
- TestTheOffsetPairStaysCoherent
- epoch_seconds
- TestMetadataRegistry
- _FinalizingWindow
- TestArithmeticOperators
- test_qc_plot.py
- TestHistoryNoneSurvivesRealOperations
- TestDerivationPathsAgree
- TestFiltersRejectNanFreq
- test_is_interpolated_means_one_thing.py
- identity_of
- Carrying pandas' identity fields across derivation (#35, #39)
- TestANonFiniteLagIsDiagnosed
- test_filters.py
- _all_four_entry_points
- TestTypePreservation
- TestIndexMutationsWithNoHookAtAll
- TestTheStampIsNotLaunderable
- TestDeepcopyOfAName
- .__init__
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
- TestRejectionMessagesNameTheRealLimit
- validate_lag
- TestTheOriginDescribesTheIndexItWasRecordedAgainst
- TestDerivationHardening
- core.py
- TestTheDisplayBoundsAreValidatedBeforeDrawing
- validate_finite_data
- TestEveryBandpassEntryPointRejectsABadLowerEdge
- TestDuplicateLabelRefusal
- test_lag_shift_bounds.py
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
- TestInplaceMethodsPreserveIdentity
- TestPlotting
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
- _complete_positional_slots
- _label_property
- baseTs
- TestAttrsIsolation
- TestFlagsAssignmentAssumption
- TestSetOutlierFilterIntegerFields
- parametrize
- TestTheStampIsNotLaunderable
- TestValuePreservingDerivationsKeepBoth
- test_datetime_index_converts_at_the_constructor.py
- Axes
- .test_the_stale_fit_is_not_drawn
- parametrize
- TestInplaceArithmeticIsUnaffected
- TestTimeSliceTakesCalendarBounds
- test_label_normalising_property.py
- lf_baseTsObj
- TestTheConstructorConvertsAStampedIndex
- parametrize
- TestTheStampNarrowsToEachDerivation
- parametrize
- empty
- parametrize
- .test_copy_configuring_does_not_reach_the_original
- .test_get_outlier_filter_params_is_a_snapshot
- .test_outlier_indices_is_reachable_after_slicing
- _one_sample
- TestInheritedPandasInplaceMethods
- Handoff: #100 — convert a DatetimeIndex to seconds at the constructor
- _origin_timestamp
- TestSetTimestampOffsetRecordsTheOrigin
- test_derived_lowess_invalidation.py
- .len
- .test_a_declared_rate_does_not_change_the_answer

## God Nodes (most connected - your core abstractions)
1. `baseTs` - 484 edges
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

## Communities (165 total, 14 thin omitted)

### Community 0 - "TestRelativeBandPower"
Cohesion: 0.13
Nodes (12): Tests for the relative_band_power / falff methods., Slow 0.05 Hz signal long enough to resolve the 0.01-0.1 Hz band., Method delegates correctly and returns a builtin float., The headline robustness property: an undetrended mean offset must not move the…, The documented pipeline produces the same answer., falff() defaults to the amplitude convention., details=True carries the white-noise null alongside the ratio., The window argument reaches get_frequency_content. (+4 more)

### Community 1 - ".copy"
Cohesion: 0.17
Nodes (6): Compute the cumulative sum of the timeseries., Create a copy of the baseTs object. Args: deep: Whether to make a deep copy…, Detrend the data by subtracting a robust LOWESS fit. The trend is the LOWESS…, Resample onto a uniform grid at exactly new_freq. The grid is built from the…, The source span the two resamplers spread their grid across. Shared by…, Interpolate the times to a new length. Args: new_len (int): The desired new…

### Community 2 - "LowessOutlierFilter"
Cohesion: 0.10
Nodes (18): LowessOutlierFilter, ndarray, Apply LOWESS smoothing and outlier detection to the data. Parameters ----------…, Reject configurations whose local window is too small to smooth. LOWESS fits a…, Apply LOWESS smoothing to the data. Uses statsmodels' Cleveland LOWESS. Note…, Process a single iteration of outlier detection., Validate and convert input data to a NumPy array., Validate and obtain the time index. (+10 more)

### Community 3 - "TestOutlierFilterSurvivesDerivation"
Cohesion: 0.16
Nodes (9): _cleared_filter(), A series whose filter has been cleared - the state issue #33 reports., outlier_filter is always a filter" must hold on every derived object. Without…, __finalize__ copies the parent's None; the chokepoint must fix it., zscale() routes through _create_new_with_data, not __finalize__., info() reads outlier_filter.config to print the filter block., The filter itself is read off the object, so it died here too. Long enough for…, The deliberate boundary of a chokepoint fix, pinned so it is visible.… (+1 more)

### Community 4 - "AdaptiveLowessFilter"
Cohesion: 0.11
Nodes (18): AdaptiveLowessFilter, demo_adaptive_lowess(), LowessConfig, ndarray, Calculate optimal segment length based on dominant frequency content., Configuration parameters for adaptive LOWESS filtering., Calculate overlap ratio based on signal complexity., Calculate LOWESS fraction based on frequency content and noise. (+10 more)

### Community 5 - "BandPowerResult"
Cohesion: 0.24
Nodes (10): Compute the relative power (or amplitude) in a frequency band. This is the…, Fractional amplitude of low-frequency fluctuations (fALFF). Convenience wrapper…, BandPowerResult, Detailed breakdown of a relative band power computation. Attributes: ratio: The…, baseTs Changelog, Unreleased: Relative Band Power / fALFF, baseTs 1.0.0 Release (NumPy backend), Keep a Changelog (+2 more)

### Community 6 - "baseTs API Documentation"
Cohesion: 0.08
Nodes (37): Apply a lowpass filter at the specified cutoff frequency. Args: cutoff: Lowpass…, Apply a lowpass filter to the data. Args: cutoff: Lowpass cutoff frequency in…, Apply a bandpass filter to the signal at specified low-pass and high-pass…, Set outlier filter parameters. Parameters ---------- params : dict, optional…, Apply the outlier filter to the signal. Args: inplace (bool, optional): If…, Apply a rolling mean to the data. Args: window: Size of the rolling window…, Apply a rolling standard deviation to the data., Apply a rolling median to the data. (+29 more)

### Community 7 - "TestBaseTsInitialization"
Cohesion: 0.20
Nodes (6): Tests for baseTs initialization and basic properties., Test initializing baseTs with data and times., Test initializing baseTs with data and frequency., Test initialization validation requirements., Test length and duration calculations., TestBaseTsInitialization

### Community 8 - "seeded"
Cohesion: 0.06
Nodes (35): add_constant(), dediff(), diff(), Add a constant to a time series. Args: ts: Source baseTs. constant: Value added…, First difference of a time series. Args: ts: Source baseTs. zeropad: If True,…, Cumulative sum of a time series. Undoes `diff(zeropad=True)` up to the level…, parametrize, utils.diff and diff_ts refuse a series with fewer than two samples (#89).… (+27 more)

### Community 9 - "conftest.py"
Cohesion: 0.06
Nodes (38): Python Package CI Workflow, hypothesis, Matplotlib, moepy, NumPy, Pandas, psutil, pytest (+30 more)

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
Cohesion: 0.07
Nodes (31): _FreqStub, _gappy_ts(), parametrize, The original zero/negative rejection is preserved. Routed through _FreqStub…, A 0.16 Hz sine over 500 samples with `n_bad` samples replaced by `bad`., The production site raises instead of returning an all-NaN spectrum.…, The headline defect: no confident wrong answer on gappy data. Pins behaviour,…, The guard rejects bad values, not unfamiliar dtypes - and since #75 hands back… (+23 more)

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
Cohesion: 0.08
Nodes (14): Test filtering operations., Test lowpass filtering., Test highpass filtering., Test bandpass filtering., Test Savitzky-Golay filtering., Test Gaussian filtering., Test chaining multiple filters., Test edge cases and error handling. (+6 more)

### Community 20 - ".__init__"
Cohesion: 0.13
Nodes (12): array, ndarray, setter, Interpolate data to a uniform sampling grid. If new_grid is not specified, use…, Initialize baseTs object as pandas Series with time-series metadata. Args:…, Set specific indices to NaN and interpolate the missing values. Args: indices:…, Get the data values as numpy array (backward compatibility)., Set the data values (backward compatibility). (+4 more)

### Community 21 - "test_pandas_compat.py"
Cohesion: 0.06
Nodes (20): fixture, parametrize, Regression tests for pandas 2.x/3.x compatibility. Each test here corresponds…, baseTs.duration() shadowed the guarded TimeSeriesData.duration()., get_statistics() calls duration(), so it inherited the crash., `freq is np.nan` only matched the one np.nan object., Previously this silently produced an all-NaN time index instead of raising,…, Deriving freq from the times array must still work. NB: the derived value is… (+12 more)

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

### Community 29 - "test_core.py"
Cohesion: 0.06
Nodes (21): Unit tests for baseTs core functionality., Test data normalization functions., Test detrending functionality., Test trimming functionality., Tests for baseTs filtering functionality., Test highpass filter., Test bandpass filter., Test Savitzky-Golay filter. (+13 more)

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
Cohesion: 0.06
Nodes (20): bandpass_filter(), Apply a symmetric bandpass filter to the input data. Args: data: Input data…, #48 added a translation site of the same shape, around validate_finite_data.…, `except ValueError -> raise InvalidParameterError` in filters now has a self-…, All of these must raise; four of the seven previously did not. The negative,…, A message about ordering is useless without the two values in it., The asymmetry that made this bug position-dependent. `max(0.1, nan)` returns…, Nyquist must come from the effective rate, not the declared one. The filter… (+12 more)

### Community 36 - "TailType"
Cohesion: 0.08
Nodes (15): Enum for specifying which tails to process in outlier detection., TailType, Enum, Tests for the statsmodels LOWESS backend of LowessOutlierFilter. Covers the…, The unslotted dataclass must not resurrect the attribute., The filter must work with moepy made unimportable., statsmodels is lowess(endog, exog) = (y, x); moepy was fit(x, y). Transposing…, Same y, x stretched: the fitted values must be essentially unchanged. (+7 more)

### Community 37 - "Design"
Cohesion: 0.11
Nodes (18): Behaviour changes, Deep copy and detachment, Design, Documentation, Eager release on derivation, Order of checks, Pickles written before this change, Problem (+10 more)

### Community 38 - "test_plot_accessor.py"
Cohesion: 0.10
Nodes (11): close_figures(), fixture, parametrize, Tests for the hybrid baseTs.plot accessor. `plot` was a plain alias for…, The historical spelling must be unchanged., The accessor is a property, so it must follow the preserved type., Each accessor plots its own data, not the parent's., TestAccessorSurvivesOperations (+3 more)

### Community 39 - "test_utils.py"
Cohesion: 0.03
Nodes (99): Find the closest time in the timeseries to a target time in seconds. Args: sec:…, _blank_head(), ClosestMatch, _coerce_lag(), coerce_real_scalar(), compute_fft_power(), _describe(), falff() (+91 more)

### Community 40 - "TestMetadataPropagation"
Cohesion: 0.09
Nodes (11): The __finalize__ concat special-case exists for nlargest/nsmallest's internal…, pandas' default __finalize__ assigns metadata by reference, so parent and child…, pandas' _inplace_method reindexes the result back to self before adopting it.…, TimeSeriesData never set outlier_filter despite declaring it in _metadata, so a…, baseTs(ts) takes the conversion branch in TimeSeriesData.__init__, which…, Every parameter used to carry a real default, so naming frac also set…, The whole design rests on this: a frozen config plus a rebinding…, Two series built from one list would cross-contaminate. (+3 more)

### Community 41 - "._enhanced_process_with_flags"
Cohesion: 0.08
Nodes (14): Apply a notch filter at the specified frequency. The stopped band is `cutoff_hz…, Apply a notch filter at the specified frequency (alias for notch_at). Args:…, Apply a highpass filter at the specified cutoff frequency. Args: cutoff:…, Apply a highpass filter at the specified cutoff frequency (alias for…, Apply a Gaussian filter to the data. Args: sigma: Standard deviation for…, Apply a Savitzky-Golay filter to the signal. Args: window_length: Length of the…, Helper method to update object flags., Enhanced processing method that handles both data and time modifications. Args:… (+6 more)

### Community 42 - "FilterConfig"
Cohesion: 0.08
Nodes (19): FilterConfig, Configuration parameters for the LowessOutlierFilter. Attributes ----------…, Initialize the LowessOutlierFilter with filtering parameters. Parameters…, np.asarray drops a mask and exposes the payload underneath., TestMaskedArrayGapsAreSeen, parametrize, A perfectly-fit signal drives MAD to zero; z_threshold then means nothing, so…, A window of <= 3 points makes LOWESS interpolate the data exactly. The fit is… (+11 more)

### Community 43 - "shift_timeseries"
Cohesion: 0.06
Nodes (26): Shift a time series by a lag value. Args: ts: Time series object with data and…, shift_timeseries(), _closed(), _five(), _five_int(), `lagged_data[:lag_idx] = np.nan` on int64 raised the very message #32 is named…, With `drop_nan=True` the blanked samples are sliced off anyway; widening to…, The caller asked for NaN placeholders, and NaN is a float. This is what… (+18 more)

### Community 44 - "TestEffectiveFrequency"
Cohesion: 0.09
Nodes (12): n samples span n-1 intervals., rolling() does not call __finalize__, so freq is recomputed from the index - it…, nlargest(3) is excluded from the op list above - it is the one op there that…, #19: resample changes the time base, so the carried freq described the old…, An explicitly supplied freq may legitimately disagree with the times it was…, #19: arithmetic on two different time bases must derive from the union index…, #19: interpto_samples assigned n/duration over the corrected derivation., #19: same n/duration error as interpto_samples. (+4 more)

### Community 45 - "TestInvalidationOnInPlaceIndexChange"
Cohesion: 0.15
Nodes (6): The index can change without any derivation at all., `.index` is pandas' own setter, and `.times` is not the only door., The inplace branch calls pd.Series.__init__ directly, bypassing…, The data setter rebuilds the index when the length changes., Same length keeps the index; equal values keep the fit (#40). Assigning zeros…, TestInvalidationOnInPlaceIndexChange

### Community 46 - "TestTheOffsetPairStaysCoherent"
Cohesion: 0.29
Nodes (4): `has_timestamp_offset` False with a non-zero `ts_offset` was unreachable. The…, `is False` matches one object; numpy booleans are not it. `arr.any()`, a…, The coherence rule runs one way, deliberately, and this pins it. Clearing the…, TestTheOffsetPairStaysCoherent

### Community 47 - "epoch_seconds"
Cohesion: 0.13
Nodes (10): epoch_seconds(), Two series of one origin on interleaved grids align onto their union, which…, The common case: same grid, so the union is the grid itself., Review round 1 (consensus panel, codex + agy): the first cut converted in…, `reindex` builds through the constructor and then `__finalize__` copies the…, The stamp is set where the origin is, in `_set_axis`, so a later replacement of…, The hardcoded copy list overwrote the fresh origin with the parent's: 2024…, No package path hands a stamped index here; pinned directly. (+2 more)

### Community 48 - "TestMetadataRegistry"
Cohesion: 0.40
Nodes (3): `_metadata` must extend pandas' list rather than replace it., Every name pandas declares must still be carried. Asserted against…, TestMetadataRegistry

### Community 54 - "_FinalizingWindow"
Cohesion: 0.10
Nodes (13): _FinalizingWindow, Any, setter, Wraps a pandas window object (Rolling/Expanding/ExponentialMovingWindow) so its…, Python looks up dunder methods on the type, bypassing __getattr__, so this…, Derive the sampling frequency from the time index. Returns NaN rather than…, The sampling rate in Hz, derived from the index unless declared. An explicitly…, Declare an explicit sampling rate against the current index. The single… (+5 more)

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

### Community 61 - "identity_of"
Cohesion: 0.18
Nodes (6): identity_of(), parametrize, The bar is pandas' own behaviour, not an invented one. If a future pandas stops…, The identity fix must not cost what already worked. These survived a re-init…, The three fields as one comparable tuple., The check must hand back what it built, not drain the caller's. Building a…

### Community 62 - "Carrying pandas' identity fields across derivation (#35, #39)"
Cohesion: 0.10
Nodes (19): Carrying pandas' identity fields across derivation (#35, #39), Decisions taken, Deliberately not in scope, Design, Half A — `_name` joins `_metadata`, Half B, Group 1 — one door for the identity triple, Half B, Group 2 — collapse three doors into one, Making a tenth site fail loudly (+11 more)

### Community 63 - "TestANonFiniteLagIsDiagnosed"
Cohesion: 0.05
Nodes (28): parametrize, `validate_lag` never gets to speak, because `get_lags` converts first. The rate…, A string lag dies on main with `can't multiply sequence by non-int`. It must…, One argument, one exception type. `validate_lag` raises ValidationError for…, float(10**400) raises OverflowError, which is neither TypeError nor ValueError…, It is a perfectly good real number; it is out of float's range. Collapsing…, `{lag!r}` on a large object builds a megabyte-long exception. A 200k-element…, A deliberate narrowing, pinned so it is not mistaken for a bug. `lag * rate`… (+20 more)

### Community 64 - "test_filters.py"
Cohesion: 0.08
Nodes (15): _DeclaresOneHz, _LiesAboutDivision, register, Registers as a Real but cannot become one. numbers.Real is a registrable ABC,…, A Real that converts to 1.0 and supports nothing else. Registers, coerces,…, Validation is worthless if the filter then uses a different value. Five review…, It declared float() == 1.0, so 1.0 is what the filter must use., The value validated is the value filtered, whatever __truediv__ says. (+7 more)

### Community 65 - "_all_four_entry_points"
Cohesion: 0.12
Nodes (16): _all_four_entry_points(), _analytic_ts(), _leading_gap_ts(), The _gappy_ts sine with the gap at sample 0 instead of sample 100., The spectral family shares the message with the filters, so it shares the trap:…, Executed, not just named: 0.16 Hz is the peak of the gap-free series., The four public ways into an FFT, as zero-argument callables., All four spectral entry points give the same actionable error. They drifted… (+8 more)

### Community 66 - "TestTypePreservation"
Cohesion: 0.29
Nodes (4): The documented pattern: a pandas op followed by a baseTs op., pandas builds subclasses as _constructor(values, index=...)., pandas looks this up on the class; a plain method breaks that., TestTypePreservation

### Community 67 - "TestIndexMutationsWithNoHookAtAll"
Cohesion: 0.22
Nodes (3): The doors that defeated the write-side design. These reach past `__finalize__`,…, The third `pd.Series.__init__` site, and the one an explicit audit for that…, TestIndexMutationsWithNoHookAtAll

### Community 68 - "TestTheStampIsNotLaunderable"
Cohesion: 0.22
Nodes (5): A copy must move the (value, index) pair, never re-stamp it. Any path that…, The discriminating case for laundering. interpolate_gaps routes through…, Memory, not correctness: the getter already reads a slice as None. Without this…, The behavioural form of the laundering check. Starting from a *valid* fit is…, TestTheStampIsNotLaunderable

### Community 69 - "TestDeepcopyOfAName"
Cohesion: 0.40
Nodes (3): `_name` now reaches deepcopy_metadata_value; it must pass through., Which is why the isinstance gate in that helper never matches it. Recorded as a…, TestDeepcopyOfAName

### Community 70 - ".__init__"
Cohesion: 0.13
Nodes (10): normalise_label(), Initialize TimeSeriesData object. A `DatetimeIndex` or `TimedeltaIndex` -…, Give the pair the origin the installed index brought, if any. The rule every…, Initialize default metadata values., Copy metadata from a baseTs object, without sharing its mutables., The type of `_UNSET`. Distinct so it can be annotated and matched., Coerce a label attribute (`signal_name`, `last_process`) to a string. The…, Stamp a just-declared origin with the index it was declared against. Only where… (+2 more)

### Community 71 - "_freq_token"
Cohesion: 0.29
Nodes (5): _freq_token(), Fingerprint an index for the purpose of sampling-rate derivation. Deliberately…, The token must be exactly the inputs _calculate_effective_frequency reads. That…, And must not: the derived rate is unchanged, so the token is right.…, TestFreqToken

### Community 72 - "ValidationError"
Cohesion: 0.06
Nodes (35): FilterError, Exception, Base exception for filter-related errors., idx_to_time(), Exception, Convert an index to a time value. Args: lag_idx: Index to convert freq:…, Convert a time value to the nearest whole number of samples. Args: lag_secs:…, Base exception for time series related errors. (+27 more)

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
Cohesion: 0.13
Nodes (8): numeric_twin(), Same data on the same seconds: bit-identical results., The seconds index is what is resampled, so a series starting at 08:00 has day…, `_update_series_data`'s no-span shrink slices the index it has; on `main` that…, stamped(), TestTheFourMethodsThatRaisedNowAgreeWithTheNumericTwin, TestTheOriginSurvivesEveryDerivation, TestTheTimesSetterIsTheOtherDoor

### Community 77 - "coerce_numeric_data"
Cohesion: 0.08
Nodes (23): coerce_numeric_data(), _complex_data_message(), The rejection text for complex sample values (issue #43). `what` describes the…, Return `data` as an array with a dtype numeric code can loop over. The dtype…, _as_object(), parametrize, Object-dtype data reaching numeric code, and the Inf half of the NaN remedy.…, Classified by what the elements *are*, not by whether a float() parse would… (+15 more)

### Community 78 - "InvalidParameterError"
Cohesion: 0.11
Nodes (37): ArrayLike, _as_filterable(), _as_real_float(), FilterConfig, highpass_filter(), InvalidParameterError, lowpass_filter(), _notch_bounds_hz() (+29 more)

### Community 79 - "plot_fft_power"
Cohesion: 0.09
Nodes (31): plot_fft_power(), Plots the power spectrum of a timeseries signal using enhanced FFT with…, Tests for issue #34: plot_fft_power must raise, not draw the error.…, ts.plot_fft_power() is the path users actually call., setup_plot used to run before the guard, so every failure left a figure. In a…, A caller passing ax= gets it back as they left it, not titled and annotated., The band check ran after the spectrum was already plotted. Ordering matters for…, The consequence users actually meet, and the fix the docs name. Since #36… (+23 more)

### Community 80 - "test_user_guide_examples.py"
Cohesion: 0.29
Nodes (9): fenced_python_under(), Executable pins on the worked examples in docs/USER_GUIDE.md. The example is…, The first ```python block after the given markdown heading line., Execute a doc block and return its namespace. The guide's opening block does…, Issue #44: a self-referential dict literal and a cutoff at Nyquist. The Nyquist…, The `quality_score < 0.95` branch, which the example's own data never takes.…, run_example(), test_example_4_enhanced_cleaning_branch_completes() (+1 more)

### Community 81 - "plotting.py"
Cohesion: 0.14
Nodes (22): hist(), lag_plot(), plot(), plot_series(), Any, array, Axes, ndarray (+14 more)

### Community 82 - "test_conversion_preserves_metadata.py"
Cohesion: 0.05
Nodes (24): carrying(), fixture, parametrize, Converting a series must not reset what it was carrying (issue #57).…, The conversion branch was gated on `.times` and `.data`. Only `baseTs` defines…, An empty carried history must not become a fabricated creation entry. The…, The conversion branch takes its index from the source, so a `times` argument…, Preserving what was not passed must not ignore what was. The fix distinguishes… (+16 more)

### Community 83 - "test_data_stamp_invalidation.py"
Cohesion: 0.19
Nodes (10): _close_figures(), filtered(), gapped(), fixture, Tests for #40: lowess_fit and outlier_indices on an object whose values…, Both producers assign the data first and the slot second. That ordering is now…, A filtered series carrying a real fit and a real outlier record., Filtered, with a pre-existing NaN the filter leaves alone (#36). (+2 more)

### Community 84 - "_ts"
Cohesion: 0.11
Nodes (22): _as_object(), parametrize, Object-dtype data reaching the spectral family and gauss_filter (#93). The same…, The constancy threshold (`np.std(data) < 1e-15`) was always taken on a float64…, compute_fft_power demeans in place on the array it computes with. The guard…, `astype(float, copy=False)` hands a float64 series' own array back, so…, #93 dropped get_frequency_content's copy on the strength of "nothing below…, For the spectral family this held before #93 (the guard ran, its result was… (+14 more)

### Community 85 - "TestRejectionMessagesNameTheRealLimit"
Cohesion: 0.31
Nodes (4): A message that states no number sends the caller round the loop twice. At…, Pull the Nyquist figure the message quotes., Execute the remedy rather than asserting the string., TestRejectionMessagesNameTheRealLimit

### Community 86 - "validate_lag"
Cohesion: 0.25
Nodes (5): Validate lag parameters. Args: lag: Lag value lag_idx: Lag index lag_unit: Unit…, validate_lag(), The bound lives with the other lag rules. Without the keyword the validator is…, An index that is both non-integer and past the bound gets the integer rule. A…, Its else-branch produced the index-mode message for any unknown unit - the same…

### Community 87 - "TestTheOriginDescribesTheIndexItWasRecordedAgainst"
Cohesion: 0.11
Nodes (12): The case the healing made permanent: the pair survived an index replacement…, The remedy names a value, and on a pre-#100 object the stored one is the wrong…, It cannot say which index its offset described., The offsets agreed, so the arm re-stamped the merged index and read the stale…, Review round 2 (consensus panel, codex + agy): the pair rode along through…, `_update_inplace` swaps the manager without `__finalize__`; the read-time check…, The package's door asserts the base; pandas' door does not., `ts.index = ...` is the door `reset_index(inplace=True)` uses to install… (+4 more)

### Community 89 - "core.py"
Cohesion: 0.05
Nodes (50): _is_unset(), True if a numeric argument was not supplied. The constructor uses np.nan as its…, Display information about the data, times, outlier filter parameters, and…, baseTs - A Python library for time series analysis, Created on Oct 19 2024 @author: stan@sympaticog.com, baseTs Package README, _apply_duplicate_label_declaration(), _carries_metadata() (+42 more)

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
Cohesion: 0.16
Nodes (9): _Flags, The restore arm, exercised directly. Since the pre-commit check landed, no path…, A stand-in whose flag setter raises what the caller chooses., Raising pandas' real class, not a look-alike. An earlier version of this test…, A diagnosis must not become the payload. Naming every duplicated label built an…, Bounding the message must not stop it being useful., Not everything the setter can raise is a duplicate-label refusal. Converting…, _RefusingTarget (+1 more)

### Community 94 - "test_lag_shift_bounds.py"
Cohesion: 0.06
Nodes (25): get_lags(), Get lag values in both seconds and indices. Args: lag: Lag value lag_unit: Unit…, _declared(), _derived(), parametrize, The lag that is applied is the lag that is reported (#51-#54). Four defects in…, Every length from 100 to 2000 at a nominal 100 Hz, three lags. The issue…, The tie rule is Python's, stated so it is not mistaken for drift. A lag that… (+17 more)

### Community 96 - "test_spectral_empty_series.py"
Cohesion: 0.19
Nodes (12): _empty(), parametrize, An empty series is rejected by every spectral entry point, from one door (#62).…, Precedence for a series wrong in both ways: empty, and no usable rate. The door…, `utils.validate_non_empty` is the one definition., Emptiness only: a NaN is `validate_finite_data`'s to reject, and a 0-d array…, The whole family, not just the one sibling that already checked. `match` pins…, No RuntimeWarning on the way to the error. `relative_band_power` takes `np.std`… (+4 more)

### Community 97 - "parametrize"
Cohesion: 0.15
Nodes (9): parametrize, ValueError, matching every other bound failure in this function. '30' and True…, `band_low >= band_high` is False for NaN, so a NaN edge passed the guard. Pre-…, One ValueError for every malformed band, from two different doors. The 1- and…, One contract for the whole function, generated from a census against main.…, Newly accepted, in the opposite direction to the rest of the census. On main…, test_every_rejected_input_raises_valueerror_and_draws_nothing(), test_high_precision_bounds_are_now_accepted() (+1 more)

### Community 98 - "test_docs_fenced_blocks.py"
Cohesion: 0.09
Nodes (26): parametrize, Block, blocks_in(), _execute(), _literal_default(), outcome(), python_fences(), Every fenced Python block in docs/ runs (#69). The document is the source of… (+18 more)

### Community 99 - "TimeSeriesData"
Cohesion: 0.05
Nodes (28): Pandas Series subclass optimized for time series analysis. This class extends…, Install an index, converting a stamped one to seconds (#100). This is the one…, pandas' in-place door: swap the manager, then narrow the stamp.…, Return constructor for pandas operations., Return constructor for sliced operations., Calculate the duration of the time series. Returns: Duration in seconds (or…, Get the length of the time series (backward compatibility). Returns: Number of…, Helper method to update history and last_process. Normalises rather than… (+20 more)

### Community 101 - "_ts"
Cohesion: 0.14
Nodes (12): parametrize, The public names stay in `_metadata`; propagation runs the setter., A blob written before this change can hold `None` under the public name - #33…, The getter defaults rather than raising: pandas can build a subclass instance…, The half #33 left open: the object you mutate, not the one you derive., The property lives on the base class, so the pandas-level object gets it…, #33's live crash, on the object that was mutated rather than on a derivation of…, One more door. A plain attribute could be deleted, after which the next read… (+4 more)

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

### Community 109 - "TestInplaceMethodsPreserveIdentity"
Cohesion: 0.33
Nodes (5): basets_owned_inplace_methods(), Every public method this package defines that takes `inplace`. Restricted to…, `inplace=True` mutates the object; it must not reset its identity. This is the…, A new `inplace=` method fails here until someone classifies it. The point of…, TestInplaceMethodsPreserveIdentity

### Community 110 - "TestPlotting"
Cohesion: 0.29
Nodes (4): The reported symptom, and the one plotting path with no guard., plotting.py:87 raised ValueError on mismatched first dimensions., The caller asked for a fit explicitly; silence would be worse., TestPlotting

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
Cohesion: 0.15
Nodes (8): Each of these raised AttributeError: no attribute '_name'. Parametrised one…, Only a *stale* shadow is dropped, not any shadow. Deleting unconditionally also…, A baseTs whose three identity fields are all at non-default values. Every field…, An error that names a remedy is code; the remedy must run. This repo shipped an…, The remedy that was there before, and why it was wrong. `ts.data = ...`,…, #39: the round-trip always worked; what came back did not. Stated precisely…, seeded(), TestUnpickledObjectIsUsable

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

### Community 131 - "_complete_positional_slots"
Cohesion: 0.33
Nodes (5): _complete_positional_slots(), Restore from a pickle, healing a blob that predates `_name`. Adding '_name' to…, Bring a positional slot restored from a pickle up to the current shape.…, Snapshot `obj`'s values for a positional slot to be checked against. A…, _values_stamp()

### Community 132 - "_label_property"
Cohesion: 0.40
Nodes (5): _label_property(), _positional_property(), Build a label attribute that is always a string. `signal_name` and…, Build a property that hands back `value` only while the index it was computed…, property

### Community 133 - "baseTs"
Cohesion: 0.03
Nodes (41): baseTs, Apply a bandpass filter between two cutoff frequencies (alias for bandpass_at).…, Apply a Butterworth bandpass filter (alias for bandpass_at). Args: hp_freq:…, Get outlier filter parameters as a plain dict. A snapshot, not the live config.…, Compute the first difference of the timeseries. Args: zeropad: If True, the…, Basic data class to hold a timeseries and data. Built on pandas Series…, A time_slice bound as seconds on the index. A number is seconds on the index,…, Compute the FFT power of the timeseries. Computed on a float64 copy of the… (+33 more)

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

### Community 140 - "test_datetime_index_converts_at_the_constructor.py"
Cohesion: 0.13
Nodes (11): from_df(), Convert the timeseries to a pandas DataFrame. Args: set_index (bool): If True,…, Create a baseTs object from a pandas DataFrame. Args: df: Input DataFrame…, DataFrame, Test creating baseTs from DataFrame., A DatetimeIndex becomes seconds since its first stamp at the constructor…, A caller asking for relative seconds only. Coherent, so allowed., seconds_since_first() (+3 more)

### Community 141 - "Axes"
Cohesion: 0.29
Nodes (4): Axes, Plot this timeseries against one or more other timeseries. e.g. for QC,…, Plot a histogram of the timeseries., Plot a lag plot of the timeseries.

### Community 143 - "parametrize"
Cohesion: 0.09
Nodes (11): parametrize, `pd.Timestamp(2592000)` is 2.592 ms into 1970; the rule is `numbers.Real`,…, The load-bearing agreement between the two conversions: the index comes from…, A series built from seconds must come out byte-for-byte as before. The pair's…, The TypeError arm in the rate derivation used to be described as the…, `Decimal` registers under `numbers.Number`, not `numbers.Real`; `main` compared…, A microsecond index from 1700 to 2200 is a valid DatetimeIndex (unit us),…, The remaining keyword combination of the pinned pair table. (+3 more)

### Community 145 - "TestTimeSliceTakesCalendarBounds"
Cohesion: 0.12
Nodes (5): fixture, The bound is turned into seconds the way the index was, so a bound that names a…, `Timedelta.total_seconds()` rounds to the microsecond; the bound is placed as…, Whatever the string says: the origin check runs before parsing., TestTimeSliceTakesCalendarBounds

### Community 146 - "test_label_normalising_property.py"
Cohesion: 0.50
Nodes (3): _close_figures(), fixture, `signal_name` and `last_process` are always strings, in place too (#61). #33…

### Community 147 - "lf_baseTsObj"
Cohesion: 0.67
Nodes (3): lf_baseTsObj(), fixture, Long, slowly-varying signal suitable for 0.01-0.1 Hz band analysis. 600 s at 2…

### Community 148 - "TestTheConstructorConvertsAStampedIndex"
Cohesion: 0.13
Nodes (5): TimeSeriesData is the door; baseTs only rides through it., Seconds are counted from index[0]; an unsorted index goes negative. The rule is…, Parity with the numeric index, which admits NaN., The origin has to be a stamp; NaT would make every second NaN and the offset…, TestTheConstructorConvertsAStampedIndex

### Community 149 - "parametrize"
Cohesion: 0.12
Nodes (12): parametrize, An array edge escaped with numpy's ambiguity error, on main and after. `if not…, The guard must not reject the numeric types callers really pass., Four NaN samples in, six hundred NaN out, silently (#48). filtfilt's…, Same guard, same exception type; since #81 the Inf half of the message names…, filtfilt handles complex input correctly - it filters the real and imaginary…, A bad call is a bug in the call; bad data is a property of the input. The cheap…, validate_band_params checks hp_hz and the ordering *after* the delegated… (+4 more)

### Community 150 - "TestTheStampNarrowsToEachDerivation"
Cohesion: 0.20
Nodes (6): Review round 3 (quick-review, a different harness): the subset test is by…, `dropna(inplace=True)` swaps the manager through `_update_inplace`, which…, Positions 0..n-1 of a series whose own seconds are exactly those values read as…, A two-key groupby's MultiIndex cannot be compared with seconds; `Index.isin`…, The one index `_set_axis` could narrow against is a same-length permutation,…, TestTheStampNarrowsToEachDerivation

### Community 153 - "parametrize"
Cohesion: 0.33
Nodes (3): parametrize, Regression guard over spanning sources: true on `main` too. The no-span cases…, The one package method that grew a no-span source. Review round 1 (codex +…

### Community 159 - "_one_sample"
Cohesion: 0.21
Nodes (8): filterwarnings, _one_sample(), Only the empty series is rejected by the door. One sample is not. A 1-sample…, A confident 0.0 for a spectrum with no peak in it - observed and left as…, The constant-data branch, which runs before the FFT: one sample has a standard…, matplotlib warns about a singular x-range for one point; that is the draw's,…, Its threshold is its own contract and is not the door's., TestTheOneSampleDecision

### Community 161 - "TestInheritedPandasInplaceMethods"
Cohesion: 0.18
Nodes (5): `inplace=True` on an inherited pandas method swaps the block manager. pandas…, The reported crash, reachable without any baseTs method at all., The silent variant: same length, every position moved., These keep the positions, so the index rule must not fire. On this fixture they…, TestInheritedPandasInplaceMethods

### Community 165 - "Handoff: #100 — convert a DatetimeIndex to seconds at the constructor"
Cohesion: 0.22
Nodes (8): Decisions taken while implementing (2026-09-05), Design, Docs to update (they currently work around #100 and say so), Handoff: #100 — convert a DatetimeIndex to seconds at the constructor, Tests to write first (TDD; the harness must be red before the code), The task, What is true on `main` at 0cbffcb (all measured, pandas 3.0.1 / numpy 2.5.2), Working rules this arc has settled on (see the memory files for the why)

### Community 166 - "_origin_timestamp"
Cohesion: 0.32
Nodes (7): _origin_timestamp(), The index as calendar stamps: the origin plus each second. The index itself is…, The origin `ts_offset` names, rebuilt at microsecond resolution. A float64…, origin + seconds, as a DatetimeIndex, at the precision the float holds. A…, _stamps_from_seconds(), DatetimeIndex, Timestamp

### Community 167 - "TestSetTimestampOffsetRecordsTheOrigin"
Cohesion: 0.25
Nodes (3): It used to move the index by the offset and record it; the index stays put now.…, Nothing about the index changes, so the declaration's token holds., TestSetTimestampOffsetRecordsTheOrigin

### Community 169 - "test_derived_lowess_invalidation.py"
Cohesion: 0.17
Nodes (8): _close_figures(), filtered(), fixture, Tests for #20: lowess_fit and outlier_indices on derived objects. `lowess_fit`…, A filtered series carrying a real fit and a real outlier record., _create_new_with_data copies the metadata slots outside pandas' machinery.…, Same index and same values, so both still describe the result. sg_filter was…, TestInvalidationThroughCreateNewWithData

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
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

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