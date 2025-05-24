# -*- coding: utf-8 -*-
"""
Performance benchmarking for Phase 3 methods.
Compares performance between numpy and Series backends for all operations.
"""

import pytest
import time
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Callable, Any
import matplotlib.pyplot as plt
from baseTs import baseTs, BackendManager


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""
    method_name: str
    data_size: int
    numpy_time: float
    series_time: float
    numpy_memory: float = 0.0
    series_memory: float = 0.0
    
    @property
    def speedup_ratio(self) -> float:
        """Calculate speedup ratio (positive = Series faster)."""
        if self.numpy_time > 0:
            return (self.numpy_time - self.series_time) / self.numpy_time
        return 0.0
    
    @property
    def memory_ratio(self) -> float:
        """Calculate memory ratio (Series / NumPy)."""
        if self.numpy_memory > 0:
            return self.series_memory / self.numpy_memory
        return 0.0


class Phase3PerformanceBenchmark:
    """Performance benchmarking framework for Phase 3 methods."""
    
    def __init__(self, data_sizes: List[int] = None, n_repeats: int = 5):
        """
        Initialize benchmark framework.
        
        Args:
            data_sizes: List of data sizes to test
            n_repeats: Number of repetitions for timing
        """
        self.data_sizes = data_sizes or [100, 500, 1000, 5000, 10000]
        self.n_repeats = n_repeats
        self.results: List[BenchmarkResult] = []
    
    def generate_test_data(self, size: int, freq: float = 100.0) -> tuple:
        """
        Generate test data for benchmarking.
        
        Args:
            size: Number of data points
            freq: Sampling frequency
            
        Returns:
            Tuple of (data, times)
        """
        times = np.arange(size) / freq
        # Create realistic multi-component signal
        data = (
            np.sin(2 * np.pi * 0.5 * times) +
            0.5 * np.sin(2 * np.pi * 2.0 * times) +
            0.3 * np.sin(2 * np.pi * 5.0 * times) +
            0.1 * np.random.randn(size)
        )
        return data, times
    
    def time_function(self, func: Callable, n_repeats: int = None) -> float:
        """
        Time a function execution with multiple repeats.
        
        Args:
            func: Function to time
            n_repeats: Number of repetitions (uses self.n_repeats if None)
            
        Returns:
            Average execution time in seconds
        """
        if n_repeats is None:
            n_repeats = self.n_repeats
            
        times = []
        for _ in range(n_repeats):
            start_time = time.perf_counter()
            result = func()
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        return np.mean(times)
    
    def estimate_memory_usage(self, obj: Any) -> float:
        """
        Estimate memory usage of an object in MB.
        
        Args:
            obj: Object to measure
            
        Returns:
            Memory usage in MB
        """
        try:
            import sys
            if hasattr(obj, 'data') and hasattr(obj, 'times'):
                # baseTs object
                return (sys.getsizeof(obj.data) + sys.getsizeof(obj.times)) / 1024 / 1024
            else:
                return sys.getsizeof(obj) / 1024 / 1024
        except:
            return 0.0
    
    def benchmark_mathematical_operations(self) -> List[BenchmarkResult]:
        """Benchmark mathematical operations."""
        results = []
        
        operations = [
            ('zscale', lambda ts: ts.zscale()),
            ('normalize_range', lambda ts: ts.normalize_range()),
            ('center', lambda ts: ts.center()),
            ('scale', lambda ts: ts.scale(2.0)),
            ('abs', lambda ts: ts.abs()),
        ]
        
        for size in self.data_sizes:
            data, times = self.generate_test_data(size)
            
            for op_name, op_func in operations:
                print(f"  Benchmarking {op_name} with {size} points...")
                
                # Create test objects
                ts_numpy = baseTs(data.copy(), times.copy(), freq=100.0, backend='numpy')
                ts_series = baseTs(data.copy(), times.copy(), freq=100.0, backend='series')
                
                # Benchmark numpy backend
                numpy_time = self.time_function(lambda: op_func(ts_numpy))
                
                # Benchmark Series backend
                series_time = self.time_function(lambda: op_func(ts_series))
                
                # Memory usage
                result_numpy = op_func(ts_numpy)
                result_series = op_func(ts_series)
                numpy_memory = self.estimate_memory_usage(result_numpy)
                series_memory = self.estimate_memory_usage(result_series)
                
                result = BenchmarkResult(
                    method_name=op_name,
                    data_size=size,
                    numpy_time=numpy_time,
                    series_time=series_time,
                    numpy_memory=numpy_memory,
                    series_memory=series_memory
                )
                results.append(result)
                
                print(f"    {op_name}: NumPy {numpy_time:.4f}s, Series {series_time:.4f}s, "
                      f"Speedup: {result.speedup_ratio:.2%}")
        
        return results
    
    def benchmark_filtering_operations(self) -> List[BenchmarkResult]:
        """Benchmark filtering operations."""
        results = []
        
        # Use smaller set for filtering (more computationally expensive)
        filter_sizes = [size for size in self.data_sizes if size <= 5000]
        
        operations = [
            ('lowpass_at', lambda ts: ts.lowpass_at(5.0, order=3)),
            ('highpass_at', lambda ts: ts.highpass_at(1.0, order=3)),
            ('bandpass_at', lambda ts: ts.bandpass_at(hp_hz=1.0, lp_hz=10.0)),
            ('gauss_filter', lambda ts: ts.gauss_filter(sigma=2.0)),
            ('sg_filter', lambda ts: ts.sg_filter(window_length=11, polyorder=2)),
        ]
        
        for size in filter_sizes:
            data, times = self.generate_test_data(size, freq=100.0)
            
            for op_name, op_func in operations:
                print(f"  Benchmarking {op_name} with {size} points...")
                
                # Create test objects
                ts_numpy = baseTs(data.copy(), times.copy(), freq=100.0, backend='numpy')
                ts_series = baseTs(data.copy(), times.copy(), freq=100.0, backend='series')
                
                try:
                    # Benchmark numpy backend
                    numpy_time = self.time_function(lambda: op_func(ts_numpy), n_repeats=3)
                    
                    # Benchmark Series backend
                    series_time = self.time_function(lambda: op_func(ts_series), n_repeats=3)
                    
                    result = BenchmarkResult(
                        method_name=f"filter_{op_name}",
                        data_size=size,
                        numpy_time=numpy_time,
                        series_time=series_time
                    )
                    results.append(result)
                    
                    print(f"    {op_name}: NumPy {numpy_time:.4f}s, Series {series_time:.4f}s, "
                          f"Speedup: {result.speedup_ratio:.2%}")
                
                except Exception as e:
                    print(f"    {op_name}: Failed with error: {e}")
                    continue
        
        return results
    
    def benchmark_enhanced_methods(self) -> List[BenchmarkResult]:
        """Benchmark new pandas-enhanced methods."""
        results = []
        
        operations = [
            ('rolling_mean', lambda ts: ts.rolling_mean(window=min(50, ts.len()//4))),
            ('time_slice', lambda ts: ts.time_slice(start_time=ts.times[0] + 0.2*ts.duration(), 
                                                   end_time=ts.times[0] + 0.8*ts.duration())),
            ('get_statistics', lambda ts: ts.get_statistics()),
        ]
        
        for size in self.data_sizes:
            data, times = self.generate_test_data(size)
            
            for op_name, op_func in operations:
                print(f"  Benchmarking {op_name} with {size} points...")
                
                # Create test objects
                ts_numpy = baseTs(data.copy(), times.copy(), freq=100.0, backend='numpy')
                ts_series = baseTs(data.copy(), times.copy(), freq=100.0, backend='series')
                
                try:
                    # Benchmark numpy backend
                    numpy_time = self.time_function(lambda: op_func(ts_numpy))
                    
                    # Benchmark Series backend
                    series_time = self.time_function(lambda: op_func(ts_series))
                    
                    result = BenchmarkResult(
                        method_name=f"enhanced_{op_name}",
                        data_size=size,
                        numpy_time=numpy_time,
                        series_time=series_time
                    )
                    results.append(result)
                    
                    print(f"    {op_name}: NumPy {numpy_time:.4f}s, Series {series_time:.4f}s, "
                          f"Speedup: {result.speedup_ratio:.2%}")
                
                except Exception as e:
                    print(f"    {op_name}: Failed with error: {e}")
                    continue
        
        return results
    
    def benchmark_operation_chaining(self) -> List[BenchmarkResult]:
        """Benchmark chained operations."""
        results = []
        
        # Define operation chains
        chains = [
            ('simple_chain', lambda ts: ts.center().scale(2.0).normalize_range()),
            ('math_chain', lambda ts: ts.zscale().abs().normalize_range()),
            ('filter_chain', lambda ts: ts.lowpass_at(10.0).gauss_filter(sigma=1.0)),
        ]
        
        # Use subset of sizes for chaining (can be expensive)
        chain_sizes = [size for size in self.data_sizes if size <= 2000]
        
        for size in chain_sizes:
            data, times = self.generate_test_data(size, freq=100.0)
            
            for chain_name, chain_func in chains:
                print(f"  Benchmarking {chain_name} with {size} points...")
                
                # Create test objects
                ts_numpy = baseTs(data.copy(), times.copy(), freq=100.0, backend='numpy')
                ts_series = baseTs(data.copy(), times.copy(), freq=100.0, backend='series')
                
                try:
                    # Benchmark numpy backend
                    numpy_time = self.time_function(lambda: chain_func(ts_numpy), n_repeats=3)
                    
                    # Benchmark Series backend
                    series_time = self.time_function(lambda: chain_func(ts_series), n_repeats=3)
                    
                    result = BenchmarkResult(
                        method_name=f"chain_{chain_name}",
                        data_size=size,
                        numpy_time=numpy_time,
                        series_time=series_time
                    )
                    results.append(result)
                    
                    print(f"    {chain_name}: NumPy {numpy_time:.4f}s, Series {series_time:.4f}s, "
                          f"Speedup: {result.speedup_ratio:.2%}")
                
                except Exception as e:
                    print(f"    {chain_name}: Failed with error: {e}")
                    continue
        
        return results
    
    def run_all_benchmarks(self) -> Dict[str, List[BenchmarkResult]]:
        """Run all benchmark suites."""
        print("Running Phase 3 Performance Benchmarks")
        print("=" * 50)
        
        all_results = {}
        
        print(f"\n1. Mathematical Operations:")
        print("-" * 30)
        all_results['mathematical'] = self.benchmark_mathematical_operations()
        
        print(f"\n2. Filtering Operations:")
        print("-" * 30)
        all_results['filtering'] = self.benchmark_filtering_operations()
        
        print(f"\n3. Enhanced Methods:")
        print("-" * 30)
        all_results['enhanced'] = self.benchmark_enhanced_methods()
        
        print(f"\n4. Operation Chaining:")
        print("-" * 30)
        all_results['chaining'] = self.benchmark_operation_chaining()
        
        # Store all results
        for category_results in all_results.values():
            self.results.extend(category_results)
        
        return all_results
    
    def generate_report(self) -> str:
        """Generate a comprehensive performance report."""
        if not self.results:
            return "No benchmark results available."
        
        report = ["Phase 3 Performance Benchmark Report", "=" * 40, ""]
        
        # Group results by category
        categories = {}
        for result in self.results:
            category = result.method_name.split('_')[0] if '_' in result.method_name else 'other'
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        # Overall statistics
        overall_speedup = np.mean([r.speedup_ratio for r in self.results])
        faster_count = sum(1 for r in self.results if r.speedup_ratio > 0)
        slower_count = sum(1 for r in self.results if r.speedup_ratio < 0)
        
        report.extend([
            "Overall Summary:",
            "-" * 15,
            f"Total benchmarks: {len(self.results)}",
            f"Series faster: {faster_count} ({faster_count/len(self.results)*100:.1f}%)",
            f"Series slower: {slower_count} ({slower_count/len(self.results)*100:.1f}%)",
            f"Average speedup: {overall_speedup:.2%}",
            ""
        ])
        
        # Category-specific analysis
        for category, results in categories.items():
            if not results:
                continue
                
            report.append(f"{category.capitalize()} Operations:")
            report.append("-" * 25)
            
            avg_speedup = np.mean([r.speedup_ratio for r in results])
            category_faster = sum(1 for r in results if r.speedup_ratio > 0)
            
            report.extend([
                f"Average speedup: {avg_speedup:.2%}",
                f"Series faster in: {category_faster}/{len(results)} cases",
                ""
            ])
            
            # Top performers
            sorted_results = sorted(results, key=lambda x: x.speedup_ratio, reverse=True)
            if sorted_results:
                best = sorted_results[0]
                worst = sorted_results[-1]
                report.extend([
                    f"Best performer: {best.method_name} ({best.speedup_ratio:.2%} speedup)",
                    f"Worst performer: {worst.method_name} ({worst.speedup_ratio:.2%} speedup)",
                    ""
                ])
        
        # Performance trends by data size
        report.extend([
            "Performance by Data Size:",
            "-" * 25
        ])
        
        for size in sorted(set(r.data_size for r in self.results)):
            size_results = [r for r in self.results if r.data_size == size]
            if size_results:
                avg_speedup = np.mean([r.speedup_ratio for r in size_results])
                report.append(f"Size {size:5d}: {avg_speedup:+6.2%} average speedup")
        
        report.append("")
        
        # Recommendations
        report.extend([
            "Recommendations:",
            "-" * 15
        ])
        
        if overall_speedup > 0.1:
            report.append("✅ Series backend shows significant performance benefits")
        elif overall_speedup > 0:
            report.append("✅ Series backend shows modest performance benefits")
        elif overall_speedup > -0.1:
            report.append("⚠️  Series backend shows comparable performance")
        else:
            report.append("❌ Series backend shows performance regression")
        
        report.extend([
            "",
            f"Consider Series backend for: {', '.join([cat for cat, results in categories.items() if np.mean([r.speedup_ratio for r in results]) > 0.05])}",
            f"Use NumPy backend for: {', '.join([cat for cat, results in categories.items() if np.mean([r.speedup_ratio for r in results]) < -0.05])}"
        ])
        
        return "\n".join(report)
    
    def plot_results(self, results: Dict[str, List[BenchmarkResult]], save_path: str = None):
        """
        Plot benchmark results.
        
        Args:
            results: Dictionary of benchmark results
            save_path: Optional path to save the plot
        """
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            # Plot 1: Speedup by method
            all_results = []
            for category_results in results.values():
                all_results.extend(category_results)
            
            methods = list(set(r.method_name for r in all_results))
            method_speedups = []
            
            for method in methods:
                method_results = [r for r in all_results if r.method_name == method]
                avg_speedup = np.mean([r.speedup_ratio for r in method_results]) * 100
                method_speedups.append(avg_speedup)
            
            colors = ['green' if s > 0 else 'red' for s in method_speedups]
            bars = ax1.bar(range(len(methods)), method_speedups, color=colors, alpha=0.7)
            ax1.set_xlabel('Methods')
            ax1.set_ylabel('Average Speedup (%)')
            ax1.set_title('Performance: Series vs NumPy Backend')
            ax1.set_xticks(range(len(methods)))
            ax1.set_xticklabels(methods, rotation=45, ha='right')
            ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax1.grid(True, alpha=0.3)
            
            # Plot 2: Performance by data size
            sizes = sorted(set(r.data_size for r in all_results))
            size_speedups = []
            
            for size in sizes:
                size_results = [r for r in all_results if r.data_size == size]
                avg_speedup = np.mean([r.speedup_ratio for r in size_results]) * 100
                size_speedups.append(avg_speedup)
            
            ax2.plot(sizes, size_speedups, 'o-', linewidth=2, markersize=6)
            ax2.set_xlabel('Data Size (points)')
            ax2.set_ylabel('Average Speedup (%)')
            ax2.set_title('Performance vs Data Size')
            ax2.set_xscale('log')
            ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
            ax2.grid(True, alpha=0.3)
            
            # Plot 3: Execution time comparison
            for category, category_results in results.items():
                if not category_results:
                    continue
                sizes = [r.data_size for r in category_results]
                numpy_times = [r.numpy_time for r in category_results]
                series_times = [r.series_time for r in category_results]
                
                ax3.loglog(sizes, numpy_times, 'o-', label=f'{category} (NumPy)', alpha=0.7)
                ax3.loglog(sizes, series_times, 's-', label=f'{category} (Series)', alpha=0.7)
            
            ax3.set_xlabel('Data Size (points)')
            ax3.set_ylabel('Execution Time (seconds)')
            ax3.set_title('Absolute Performance Comparison')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            # Plot 4: Distribution of speedups
            speedups = [r.speedup_ratio * 100 for r in all_results]
            ax4.hist(speedups, bins=20, alpha=0.7, edgecolor='black')
            ax4.set_xlabel('Speedup (%)')
            ax4.set_ylabel('Number of Methods')
            ax4.set_title('Distribution of Performance Gains')
            ax4.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='No change')
            ax4.axvline(x=np.mean(speedups), color='blue', linestyle='-', alpha=0.7, label='Average')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"\nBenchmark plots saved to '{save_path}'")
            else:
                plt.show()
                
        except Exception as e:
            print(f"Could not generate plots: {e}")


def run_phase3_benchmarks():
    """Main function to run Phase 3 performance benchmarks."""
    # Use smaller data sizes for faster testing
    benchmark = Phase3PerformanceBenchmark(
        data_sizes=[100, 500, 1000, 2000], 
        n_repeats=3
    )
    
    results = benchmark.run_all_benchmarks()
    
    print("\n" + "=" * 50)
    print("PHASE 3 BENCHMARK SUMMARY")
    print("=" * 50)
    print(benchmark.generate_report())
    
    # Plot results
    try:
        benchmark.plot_results(results, save_path='phase3_benchmark_results.png')
    except Exception as e:
        print(f"\nCould not generate plots: {e}")
    
    return results


if __name__ == "__main__":
    run_phase3_benchmarks()