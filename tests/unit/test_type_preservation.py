"""
Tests that pandas operations preserve the baseTs type and its metadata.

Before this, TimeSeriesData._constructor was inherited unchanged, so every
native pandas operation returned a TimeSeriesData and silently dropped all
baseTs methods - meaning the documented method chaining did not actually work.
"""
import numpy as np
import pytest

from baseTs import baseTs
from baseTs.series import TimeSeriesData
from baseTs.LowessOutlierFilter import LowessOutlierFilter


PANDAS_OPS = [
    "iloc[0:10]", "loc[0.0:1.0]", "head(5)", "tail(5)", "dropna()", "abs()",
    "cumsum()", "diff()", "rolling(3).mean()", "shift(1)", "round(2)",
    "clip(0, 10)", "fillna(0)", "sort_values()", "astype(float)",
    "interpolate()", "ffill()", "bfill()", "expanding().mean()",
    "pct_change()", "rank()", "nlargest(3)", "copy()",
]

#: Operations that hand back a filter reset to defaults rather than the
#: parent's config. Not a sharing problem - see #14.
DROPS_FILTER_CONFIG = {"rolling(3).mean()", "expanding().mean()", "nlargest(3)"}

#: Arithmetic returns through _wrap_result_as_basets, not through __finalize__,
#: so it needs its own coverage - PANDAS_OPS contains no arithmetic.
ARITHMETIC_OPS = ["ts + 1", "ts - 1", "ts * 2", "ts / 2", "ts ** 2",
                  "1 + ts", "1 - ts", "2 * ts", "ts.add(1)", "ts.mul(2)"]


@pytest.fixture
def ts():
    return baseTs(np.arange(50, dtype=float), np.arange(50) / 10.0,
                  freq=10.0, signal_name="probe")


class TestTypePreservation:

    @pytest.mark.parametrize("op", PANDAS_OPS)
    def test_operation_returns_basets(self, ts, op):
        result = eval(f"ts.{op}")
        assert isinstance(result, baseTs), f"ts.{op} downgraded to {type(result).__name__}"

    @pytest.mark.parametrize("op", PANDAS_OPS)
    def test_result_keeps_basets_methods(self, ts, op):
        """The point of preserving the type is keeping the domain methods."""
        result = eval(f"ts.{op}")
        for method in ("lowpass_at", "detect_outliers", "get_frequency_content"):
            assert hasattr(result, method), f"ts.{op} lost .{method}()"

    def test_chaining_pandas_into_basets(self, ts):
        """The documented pattern: a pandas op followed by a baseTs op."""
        result = ts.iloc[0:40].lowpass_at(1.0).zscale()
        assert isinstance(result, baseTs)
        assert len(result) == 40

    def test_constructor_accepts_pandas_convention(self):
        """pandas builds subclasses as _constructor(values, index=...)."""
        obj = baseTs(np.arange(5, dtype=float), index=np.arange(5) / 10.0)
        assert isinstance(obj, baseTs)
        assert np.allclose(obj.times, np.arange(5) / 10.0)

    def test_constructor_sliced_is_a_property(self):
        """pandas looks this up on the class; a plain method breaks that."""
        assert isinstance(
            type(TimeSeriesData.__dict__['_constructor_sliced']), type(property)
        ) or isinstance(TimeSeriesData.__dict__['_constructor_sliced'], property)


class TestMetadataPropagation:

    def test_outlier_indices_survives_slicing(self, ts):
        """
        outlier_indices was absent from _metadata, so this raised
        AttributeError after any pandas operation.
        """
        ts.outlier_indices = np.array([3, 4, 5])
        assert np.array_equal(ts.iloc[0:20].outlier_indices, np.array([3, 4, 5]))

    def test_declared_metadata_is_actually_reachable(self, ts):
        """Every name in _metadata must exist on a constructed object."""
        for name in TimeSeriesData._metadata:
            assert hasattr(ts, name), f"_metadata declares {name!r} but it is unset"

    def test_signal_name_and_flags_survive(self, ts):
        ts.is_filtered = True
        sliced = ts.iloc[0:20]
        assert sliced.signal_name == ts.signal_name
        assert sliced.is_filtered is True

    def test_history_is_copied_not_shared(self, ts):
        """
        pandas' default __finalize__ assigns metadata by reference, so parent
        and child would share one history list.
        """
        child = ts.iloc[0:20]
        assert child.history is not ts.history

        child.history.append("child-only")
        assert "child-only" not in ts.history

    @pytest.mark.parametrize("op", PANDAS_OPS)
    def test_configuring_a_derived_object_leaves_the_parent_alone(self, ts, op):
        """
        The contract is behavioural, not identity.

        FilterConfig is frozen and set_outlier_filter rebinds the filter, so
        two objects may share one safely - what must never happen is a write
        through the derived object reaching the parent.

        Note that rolling/expanding/nlargest (see DROPS_FILTER_CONFIG) satisfy
        this trivially: they propagate no metadata at all, so their result was
        never wired to the parent. test_filter_config_survives_the_copy is
        where that gap is recorded.
        """
        ts.set_outlier_filter(z_threshold=4.2)
        derived = eval(f"ts.{op}")

        derived.set_outlier_filter(z_threshold=1.5)

        assert ts.get_outlier_filter_params()["z_threshold"] == 4.2
        assert derived.get_outlier_filter_params()["z_threshold"] == 1.5

    @pytest.mark.parametrize("op", [
        pytest.param(op, marks=pytest.mark.xfail(
            reason="#14: op resets the filter config to defaults", strict=True))
        if op in DROPS_FILTER_CONFIG else op
        for op in PANDAS_OPS
    ])
    def test_filter_config_survives_the_copy(self, ts, op):
        """
        Independence must not cost the config: the values still carry over.

        The three operations in DROPS_FILTER_CONFIG fail this today for
        reasons unrelated to sharing - see #14. They are xfailed rather than
        dropped from the matrix so the gap stays visible. strict=True means
        fixing #14 turns them into failures that name this test, rather than
        letting a stale marker sit here unnoticed.
        """
        ts.set_outlier_filter(z_threshold=4.2, frac=0.11)
        derived = eval(f"ts.{op}")

        assert derived.get_outlier_filter_params()["z_threshold"] == 4.2
        assert derived.get_outlier_filter_params()["frac"] == 0.11

    @pytest.mark.parametrize("op", ARITHMETIC_OPS)
    def test_arithmetic_does_not_share_metadata(self, ts, op):
        """
        Arithmetic returns via _wrap_result_as_basets, which assigned every
        metadata attribute by reference - bypassing __finalize__ entirely.
        """
        ts.set_outlier_filter(z_threshold=4.2)
        history_before = list(ts.history)

        derived = eval(op)

        assert derived.history is not ts.history
        # The "Applied ... operation" entry belongs to the result alone.
        assert ts.history == history_before

        derived.set_outlier_filter(z_threshold=1.5)
        assert ts.get_outlier_filter_params()["z_threshold"] == 4.2

    @pytest.mark.parametrize("op", ["ts += 1", "ts -= 1", "ts *= 2",
                                    "ts /= 2", "ts **= 2"])
    def test_augmented_assignment_records_its_history(self, ts, op):
        """
        pandas implements `ts += 1` by calling __add__ and keeping only the
        values, discarding the wrapper - so an entry appended to the result
        vanishes. The entry has to land on the object the caller still holds.
        """
        before = len(ts.history)
        exec(op, {"ts": ts})

        assert len(ts.history) == before + 1

    def test_augmented_assignment_keeps_its_own_index(self, ts):
        """
        pandas' _inplace_method reindexes the result back to self before
        adopting it. Skipping that let `ts += other` grow the object to the
        union of the two indexes - 10 elements becoming 19.
        """
        other = baseTs(np.ones(len(ts)), ts.times / 10.0)
        length_before = len(ts)

        ts += other

        assert len(ts) == length_before

    def test_augmented_assignment_is_still_in_place(self, ts):
        """Other references to the series must observe the update."""
        alias = ts
        first_before = float(np.asarray(ts.data, dtype=float)[0])

        ts += 1

        assert alias is ts
        assert float(np.asarray(alias.data, dtype=float)[0]) == first_before + 1

    @pytest.mark.parametrize("method", ["zscale()", "rolling_mean(5)", "detrend()"])
    def test_domain_methods_carry_the_filter_config(self, ts, method):
        """
        _create_new_with_data omitted outlier_filter from the attributes it
        carries, so every non-inplace domain method handed back a filter reset
        to FilterConfig's defaults rather than the caller's.
        """
        ts.set_outlier_filter(z_threshold=4.2, frac=0.11)
        derived = eval(f"ts.{method}")

        assert derived.get_outlier_filter_params()["z_threshold"] == 4.2
        assert derived.get_outlier_filter_params()["frac"] == 0.11

        derived.set_outlier_filter(z_threshold=1.5)
        assert ts.get_outlier_filter_params()["z_threshold"] == 4.2

    def test_to_basetseries_carries_a_usable_filter(self, ts):
        """
        TimeSeriesData never set outlier_filter despite declaring it in
        _metadata, so a converted object carried None and the next
        filter_outliers() raised AttributeError.
        """
        base = TimeSeriesData(np.arange(20.), index=np.arange(20.) / 10.0)
        converted = base.iloc[:16].to_basetseries()

        assert converted.outlier_filter is not None
        converted.set_outlier_filter(z_threshold=4.2)
        assert converted.get_outlier_filter_params()["z_threshold"] == 4.2

    def test_copy_configuring_does_not_reach_the_original(self, ts):
        """Issue #11: the reported path, copy() rather than a pandas op."""
        ts.set_outlier_filter(z_threshold=4.2)
        c = ts.copy()

        c.set_outlier_filter(z_threshold=1.5)

        assert ts.get_outlier_filter_params()["z_threshold"] == 4.2
        assert c.get_outlier_filter_params()["z_threshold"] == 1.5

    def test_get_outlier_filter_params_is_a_snapshot(self, ts):
        """
        The accessor must not hand out the live config.

        Derived objects share one filter, which is safe only because nothing
        mutates a config in place. Returning the real __dict__ made a write
        through it reach every sharing object - frozen=True blocks setattr,
        not __dict__ assignment.
        """
        ts.set_outlier_filter(z_threshold=4.2, frac=0.11)
        derived = ts.copy()

        derived.get_outlier_filter_params()["frac"] = 0.9

        assert ts.get_outlier_filter_params()["frac"] == 0.11
        assert derived.get_outlier_filter_params()["frac"] == 0.11

    def test_constructing_a_basets_from_a_basets_keeps_its_filter(self, ts):
        """
        baseTs(ts) takes the conversion branch in TimeSeriesData.__init__,
        which carries the source's filter - and __init__ then overwrote it
        with a fresh default.
        """
        ts.set_outlier_filter(z_threshold=4.2)

        assert baseTs(ts).get_outlier_filter_params()["z_threshold"] == 4.2

    def test_naming_one_parameter_leaves_the_others_alone(self, ts):
        """
        Every parameter used to carry a real default, so naming frac also set
        z_threshold to 7 and max_iterations to 10 behind the caller's back.
        """
        ts.set_outlier_filter(z_threshold=4.2)
        ts.set_outlier_filter(frac=0.11)

        params = ts.get_outlier_filter_params()
        assert params["z_threshold"] == 4.2
        assert params["frac"] == 0.11

    def test_invalid_parameter_type_raises_valueerror(self, ts):
        """A container argument used to escape coercion as a raw TypeError."""
        with pytest.raises(ValueError):
            ts.set_outlier_filter(order=[1, 2])

    def test_filter_config_is_frozen(self):
        """
        The whole design rests on this: a frozen config plus a rebinding
        set_outlier_filter is what makes a shared filter safe, and is why no
        deepcopy runs in __finalize__.
        """
        with pytest.raises(Exception):
            LowessOutlierFilter().config.z_threshold = 99

    def test_history_argument_is_not_stored_by_reference(self):
        """Two series built from one list would cross-contaminate."""
        seed = ["seed"]
        a = baseTs(np.arange(10.), np.arange(10) / 10.0, history=seed)

        a.zscale(inplace=True)

        assert seed == ["seed"]



class TestEffectiveFrequency:
    """n samples span n-1 intervals."""

    @pytest.mark.parametrize("n,fs", [(5, 2.0), (10, 10.0), (100, 10.0), (1000, 100.0)])
    def test_derived_frequency_is_exact(self, n, fs):
        ts = baseTs(np.zeros(n), np.arange(n) / fs)
        assert np.isclose(ts.freq, fs), f"n={n}: got {ts.freq}, want {fs}"

    def test_frequency_stable_across_operations(self, ts):
        """
        rolling() does not call __finalize__, so freq is recomputed from the
        index - it must agree with the parent.
        """
        for op in ("iloc[0:20]", "rolling(3).mean()", "dropna()", "abs()"):
            assert np.isclose(eval(f"ts.{op}").freq, ts.freq), f"ts.{op} changed freq"

    def test_short_series_has_no_frequency(self):
        assert np.isnan(baseTs(np.zeros(1), np.zeros(1), freq=1.0)._calculate_effective_frequency())

    def test_nyquist_boundary_is_exact(self):
        """A 1 Hz series must reject a cutoff at exactly 0.5 Hz."""
        ts = baseTs(np.random.randn(100), np.arange(100, dtype=float))
        assert np.isclose(ts.freq, 1.0)
        with pytest.raises(Exception):
            ts.lowpass_filter(cutoff=0.5)
        assert isinstance(ts.lowpass_filter(cutoff=0.4), baseTs)
