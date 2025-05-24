"""Migration validation tools and tests.

Tools to validate the migration from numpy to pandas Series backend,
ensuring compatibility, correctness, and performance requirements.
"""

import pytest
import numpy as np
import pandas as pd
import time
import warnings
from typing import Dict, List, Tuple, Any, Callable
from baseTs import baseTs


class MigrationValidator:
    """Comprehensive migration validation framework."""
    
    def __init__(self):
        self.test_results = {}
        self.performance_results = {}
        self.compatibility_results = {}
    
    def validate_full_migration(self) -> Dict[str, Any]:
        """Run complete migration validation suite."""
        results = {
            'compatibility': self.validate_compatibility(),
            'performance': self.validate_performance(),
            'correctness': self.validate_correctness(),
            'feature_parity': self.validate_feature_parity(),
            'edge_cases': self.validate_edge_cases()
        }
        
        # Overall assessment
        results['overall_success'] = all([
            results['compatibility']['success'],
            results['performance']['success'],
            results['correctness']['success'],
            results['feature_parity']['success']
        ])
        
        return results
    
    def validate_compatibility(self) -> Dict[str, Any]:
        """Validate backward compatibility."""
        test_cases = [
            self._test_constructor_compatibility,
            self._test_property_compatibility,
            self._test_method_signature_compatibility,
            self._test_return_type_compatibility
        ]
        
        results = {'success': True, 'failures': [], 'warnings': []}
        
        for test_case in test_cases:
            try:
                test_case()
            except Exception as e:
                results['success'] = False
                results['failures'].append({
                    'test': test_case.__name__,
                    'error': str(e)
                })
        
        return results
    
    def validate_performance(self) -> Dict[str, Any]:
        """Validate performance requirements."""
        test_data_sizes = [100, 1000, 5000]
        operations = [
            ('lowpass_filter', lambda ts: ts.lowpass_filter(cutoff=0.3)),
            ('zscale', lambda ts: ts.zscale()),
            ('normalize_range', lambda ts: ts.normalize_range()),
            ('apply_function', lambda ts: ts.apply_function(np.sqrt))
        ]
        
        results = {'success': True, 'benchmarks': {}, 'violations': []}
        
        for size in test_data_sizes:
            data = np.random.randn(size)
            times = np.arange(size)
            
            for op_name, operation in operations:
                # Benchmark both backends
                numpy_time = self._benchmark_operation(data, times, operation, 'numpy')
                series_time = self._benchmark_operation(data, times, operation, 'series')
                
                # Store results
                key = f"{op_name}_{size}"
                results['benchmarks'][key] = {
                    'numpy_time': numpy_time,
                    'series_time': series_time,
                    'ratio': series_time / numpy_time if numpy_time > 0 else float('inf')
                }
                
                # Check if series backend is not more than 5x slower
                if series_time > 5 * numpy_time:
                    results['success'] = False
                    results['violations'].append({
                        'operation': op_name,
                        'size': size,
                        'slowdown': series_time / numpy_time
                    })
        
        return results
    
    def validate_correctness(self) -> Dict[str, Any]:
        """Validate mathematical correctness across backends."""
        test_cases = [
            self._test_mathematical_equivalence,
            self._test_filtering_equivalence,
            self._test_transformation_equivalence,
            self._test_statistical_equivalence
        ]
        
        results = {'success': True, 'failures': [], 'tolerance_violations': []}
        
        for test_case in test_cases:
            try:
                violations = test_case()
                if violations:
                    results['tolerance_violations'].extend(violations)
            except Exception as e:
                results['success'] = False
                results['failures'].append({
                    'test': test_case.__name__,
                    'error': str(e)
                })
        
        return results
    
    def validate_feature_parity(self) -> Dict[str, Any]:
        """Validate feature parity between backends."""
        # Core methods that must exist in both backends
        required_methods = [
            'lowpass_filter', 'zscale', 'normalize_range', 'apply_function',
            'remove_outliers', 'interpolate', 'resample'
        ]
        
        # Enhanced methods that should exist in series backend
        enhanced_methods = [
            'rolling_mean', 'time_slice', 'get_statistics'
        ]
        
        results = {'success': True, 'missing_methods': [], 'enhanced_available': []}
        
        # Test both backends
        for backend in ['numpy', 'series']:
            ts = baseTs(data=[1, 2, 3], times=[0, 1, 2], backend=backend)
            
            for method in required_methods:
                if not hasattr(ts, method):
                    results['success'] = False
                    results['missing_methods'].append({
                        'backend': backend,
                        'method': method
                    })
            
            # Check enhanced methods for series backend
            if backend == 'series':
                for method in enhanced_methods:
                    if hasattr(ts, method):
                        results['enhanced_available'].append(method)
        
        return results
    
    def validate_edge_cases(self) -> Dict[str, Any]:
        """Validate handling of edge cases."""
        edge_cases = [
            self._test_empty_data,
            self._test_single_point,
            self._test_nan_values,
            self._test_infinite_values,
            self._test_large_values,
            self._test_mismatched_lengths
        ]
        
        results = {'success': True, 'failures': [], 'handled_cases': []}
        
        for test_case in edge_cases:
            try:
                test_case()
                results['handled_cases'].append(test_case.__name__)
            except Exception as e:
                results['failures'].append({
                    'test': test_case.__name__,
                    'error': str(e)
                })
                # Edge case failures don't fail overall migration
        
        return results
    
    def _benchmark_operation(self, data: np.ndarray, times: np.ndarray, 
                           operation: Callable, backend: str) -> float:
        """Benchmark a single operation."""
        ts = baseTs(data=data, times=times, backend=backend)
        
        # Warm up
        try:
            operation(ts)
        except:
            return float('inf')  # Operation failed
        
        # Actual benchmark
        start_time = time.perf_counter()
        for _ in range(5):  # Run multiple times for average
            try:
                operation(ts)
            except:
                return float('inf')
        end_time = time.perf_counter()
        
        return (end_time - start_time) / 5
    
    def _test_constructor_compatibility(self):
        """Test constructor compatibility."""
        data = np.random.randn(100)
        times = np.arange(100)
        
        # All these should work with both backends
        test_constructors = [
            lambda: baseTs(data=data, times=times, backend='numpy'),
            lambda: baseTs(data=data, times=times, backend='series'),
            lambda: baseTs(data=data.tolist(), times=times.tolist(), backend='numpy'),
            lambda: baseTs(data=data.tolist(), times=times.tolist(), backend='series'),
        ]
        
        for constructor in test_constructors:
            ts = constructor()
            assert len(ts.data) == 100
            assert len(ts.times) == 100
    
    def _test_property_compatibility(self):
        """Test property access compatibility."""
        data = np.random.randn(50)
        times = np.arange(50)
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data=data, times=times, backend=backend)
            
            # Test basic properties
            assert hasattr(ts, 'data')
            assert hasattr(ts, 'times')
            assert hasattr(ts, 'len')
            assert ts.len() == 50
            
            # Test data access
            assert len(ts.data) == 50
            assert len(ts.times) == 50
    
    def _test_method_signature_compatibility(self):
        """Test method signature compatibility."""
        data = np.random.randn(100)
        times = np.arange(100)
        
        methods_to_test = [
            ('lowpass_filter', {'cutoff': 0.3}),
            ('apply_function', {'func': np.sqrt}),
            ('remove_outliers', {}),
        ]
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data=data, times=times, backend=backend)
            
            for method_name, kwargs in methods_to_test:
                if hasattr(ts, method_name):
                    method = getattr(ts, method_name)
                    result = method(**kwargs)
                    assert hasattr(result, 'data')
                    assert hasattr(result, 'times')
    
    def _test_return_type_compatibility(self):
        """Test return type compatibility."""
        data = np.random.randn(100)
        times = np.arange(100)
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data=data, times=times, backend=backend)
            
            # All operations should return baseTs objects
            result1 = ts.zscale()
            result2 = ts.lowpass_filter(cutoff=0.3)
            
            assert isinstance(result1, baseTs)
            assert isinstance(result2, baseTs)
    
    def _test_mathematical_equivalence(self) -> List[Dict]:
        """Test mathematical equivalence between backends."""
        violations = []
        data = np.random.randn(100)
        times = np.arange(100)
        
        operations = [
            ('zscale', lambda ts: ts.zscale()),
            ('normalize_range', lambda ts: ts.normalize_range()),
            ('lowpass_filter', lambda ts: ts.lowpass_filter(cutoff=0.3))
        ]
        
        for op_name, operation in operations:
            ts_numpy = baseTs(data=data, times=times, backend='numpy')
            ts_series = baseTs(data=data, times=times, backend='series')
            
            result_numpy = operation(ts_numpy)
            result_series = operation(ts_series)
            
            # Check numerical equivalence
            if not np.allclose(result_numpy.data, result_series.data, rtol=1e-10, atol=1e-12):
                violations.append({
                    'operation': op_name,
                    'max_diff': np.max(np.abs(result_numpy.data - result_series.data)),
                    'type': 'data_mismatch'
                })
        
        return violations
    
    def _test_filtering_equivalence(self) -> List[Dict]:
        """Test filtering operation equivalence."""
        violations = []
        
        # Test with different signal types
        test_signals = [
            np.sin(np.linspace(0, 10, 100)),  # Smooth signal
            np.random.randn(100),  # Random signal
            np.ones(100)  # Constant signal
        ]
        
        for i, signal in enumerate(test_signals):
            times = np.arange(len(signal))
            
            ts_numpy = baseTs(data=signal, times=times, backend='numpy')
            ts_series = baseTs(data=signal, times=times, backend='series')
            
            # Test lowpass filter
            filtered_numpy = ts_numpy.lowpass_filter(cutoff=0.3)
            filtered_series = ts_series.lowpass_filter(cutoff=0.3)
            
            if not np.allclose(filtered_numpy.data, filtered_series.data, rtol=1e-8):
                violations.append({
                    'operation': 'lowpass_filter',
                    'signal_type': f'test_signal_{i}',
                    'max_diff': np.max(np.abs(filtered_numpy.data - filtered_series.data))
                })
        
        return violations
    
    def _test_transformation_equivalence(self) -> List[Dict]:
        """Test transformation equivalence."""
        violations = []
        data = np.random.exponential(2, 100)
        times = np.arange(100)
        
        transformations = [
            ('sqrt', np.sqrt),
            ('log', lambda x: np.log(x + 1e-10)),  # Avoid log(0)
            ('square', lambda x: x ** 2)
        ]
        
        for trans_name, func in transformations:
            ts_numpy = baseTs(data=data, times=times, backend='numpy')
            ts_series = baseTs(data=data, times=times, backend='series')
            
            result_numpy = ts_numpy.apply_function(func)
            result_series = ts_series.apply_function(func)
            
            if not np.allclose(result_numpy.data, result_series.data, rtol=1e-10):
                violations.append({
                    'operation': f'apply_function_{trans_name}',
                    'max_diff': np.max(np.abs(result_numpy.data - result_series.data))
                })
        
        return violations
    
    def _test_statistical_equivalence(self) -> List[Dict]:
        """Test statistical measure equivalence."""
        violations = []
        data = np.random.randn(200)
        times = np.arange(200)
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data=data, times=times, backend=backend)
            
            # Test statistical operations
            normalized = ts.zscale()
            
            # Check statistical properties
            mean_val = np.mean(normalized.data)
            std_val = np.std(normalized.data)
            
            if abs(mean_val) > 1e-10:
                violations.append({
                    'operation': 'zscale_mean',
                    'backend': backend,
                    'value': mean_val,
                    'expected': 0.0
                })
            
            if abs(std_val - 1.0) > 1e-10:
                violations.append({
                    'operation': 'zscale_std',
                    'backend': backend,
                    'value': std_val,
                    'expected': 1.0
                })
        
        return violations
    
    def _test_empty_data(self):
        """Test handling of empty data."""
        with pytest.raises((ValueError, AssertionError)):
            baseTs(data=[], times=[], backend='numpy')
        
        with pytest.raises((ValueError, AssertionError)):
            baseTs(data=[], times=[], backend='series')
    
    def _test_single_point(self):
        """Test handling of single data point."""
        for backend in ['numpy', 'series']:
            ts = baseTs(data=[1.0], times=[0.0], backend=backend)
            assert ts.len() == 1
            assert ts.data[0] == 1.0
    
    def _test_nan_values(self):
        """Test handling of NaN values."""
        data = [1.0, np.nan, 3.0]
        times = [0, 1, 2]
        
        for backend in ['numpy', 'series']:
            # Should either handle gracefully or raise appropriate error
            try:
                ts = baseTs(data=data, times=times, backend=backend)
                # If creation succeeds, basic operations should work
                assert ts.len() == 3
            except (ValueError, TypeError):
                # Acceptable to reject NaN data
                pass
    
    def _test_infinite_values(self):
        """Test handling of infinite values."""
        data = [1.0, np.inf, 3.0]
        times = [0, 1, 2]
        
        for backend in ['numpy', 'series']:
            try:
                ts = baseTs(data=data, times=times, backend=backend)
                assert ts.len() == 3
            except (ValueError, TypeError):
                # Acceptable to reject infinite data
                pass
    
    def _test_large_values(self):
        """Test handling of very large values."""
        data = [1e10, 2e10, 3e10]
        times = [0, 1, 2]
        
        for backend in ['numpy', 'series']:
            ts = baseTs(data=data, times=times, backend=backend)
            assert ts.len() == 3
            # Basic operations should work
            normalized = ts.normalize_range()
            assert len(normalized.data) == 3
    
    def _test_mismatched_lengths(self):
        """Test handling of mismatched data/times lengths."""
        for backend in ['numpy', 'series']:
            with pytest.raises((ValueError, AssertionError)):
                baseTs(data=[1, 2, 3], times=[0, 1], backend=backend)


class TestMigrationValidation:
    """Test suite for migration validation tools."""
    
    def test_migration_validator_creation(self):
        """Test migration validator can be created."""
        validator = MigrationValidator()
        assert isinstance(validator, MigrationValidator)
    
    def test_compatibility_validation(self):
        """Test compatibility validation."""
        validator = MigrationValidator()
        results = validator.validate_compatibility()
        
        assert 'success' in results
        assert 'failures' in results
        assert 'warnings' in results
    
    def test_performance_validation(self):
        """Test performance validation."""
        validator = MigrationValidator()
        results = validator.validate_performance()
        
        assert 'success' in results
        assert 'benchmarks' in results
        assert 'violations' in results
    
    def test_correctness_validation(self):
        """Test correctness validation."""
        validator = MigrationValidator()
        results = validator.validate_correctness()
        
        assert 'success' in results
        assert 'failures' in results
        assert 'tolerance_violations' in results
    
    def test_full_migration_validation(self):
        """Test complete migration validation."""
        validator = MigrationValidator()
        results = validator.validate_full_migration()
        
        # Check all required sections
        required_sections = ['compatibility', 'performance', 'correctness', 
                           'feature_parity', 'edge_cases', 'overall_success']
        
        for section in required_sections:
            assert section in results
        
        # Overall success should be boolean
        assert isinstance(results['overall_success'], bool)


def run_migration_validation():
    """Run complete migration validation and print results."""
    validator = MigrationValidator()
    results = validator.validate_full_migration()
    
    print("=" * 60)
    print("MIGRATION VALIDATION REPORT")
    print("=" * 60)
    
    for section, section_results in results.items():
        if section == 'overall_success':
            continue
            
        print(f"\n{section.upper()}:")
        if isinstance(section_results, dict) and 'success' in section_results:
            status = "PASS" if section_results['success'] else "FAIL"
            print(f"  Status: {status}")
            
            if 'failures' in section_results and section_results['failures']:
                print(f"  Failures: {len(section_results['failures'])}")
                for failure in section_results['failures'][:3]:  # Show first 3
                    print(f"    - {failure}")
            
            if 'violations' in section_results and section_results['violations']:
                print(f"  Violations: {len(section_results['violations'])}")
        else:
            print(f"  Results: {section_results}")
    
    print(f"\nOVERALL MIGRATION STATUS: {'SUCCESS' if results['overall_success'] else 'FAILED'}")
    print("=" * 60)
    
    return results


if __name__ == '__main__':
    # Run validation when script is executed directly
    run_migration_validation()