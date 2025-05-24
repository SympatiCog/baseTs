# -*- coding: utf-8 -*-
"""
Benchmarking framework for baseTs pandas migration.
Compare performance between numpy and Series backends.
"""

import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Callable, Any, Tuple
from dataclasses import dataclass
from baseTs import baseTs
from baseTs.series import TimeSeriesData
from baseTs.compat import convert_to_series, convert_to_basetseries


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""
    name: str
    numpy_time: float
    series_time: float
    data_size: int
    memory_numpy: float = 0.0
    memory_series: float = 0.0
    
    @property
    def speedup_ratio(self) -> float:
        """Calculate speedup ratio (positive = Series faster)."""
        return (self.numpy_time - self.series_time) / self.numpy_time
    
    @property
    def memory_ratio(self) -> float:
        """Calculate memory ratio (Series / NumPy)."""
        if self.memory_numpy > 0:
            return self.memory_series / self.memory_numpy
        return 0.0


class MigrationBenchmark:
    """Benchmarking framework for migration performance analysis."""
    
    def __init__(self, data_sizes: List[int] = None):
        """
        Initialize benchmark framework.
        
        Args:
            data_sizes: List of data sizes to test (default: [100, 1000, 10000])
        """
        self.data_sizes = data_sizes or [100, 1000, 10000, 50000]
        self.results: List[BenchmarkResult] = []
    
    def generate_test_data(self, size: int, freq: float = 100.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate test data for benchmarking.
        
        Args:
            size: Number of data points
            freq: Sampling frequency
            
        Returns:
            Tuple of (data, times) arrays
        """
        times = np.arange(size) / freq
        # Create realistic signal with multiple components
        data = (
            np.sin(2 * np.pi * 0.5 * times) +
            0.5 * np.sin(2 * np.pi * 2.0 * times) +
            0.1 * np.random.randn(size)
        )
        return data, times
    
    def time_function(self, func: Callable, *args, **kwargs) -> float:
        """
        Time a function execution.
        
        Args:
            func: Function to time
            *args, **kwargs: Arguments for the function
            
        Returns:
            Execution time in seconds
        """
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        return end_time - start_time
    
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
            elif hasattr(obj, 'values') and hasattr(obj, 'index'):
                # Series object
                return (sys.getsizeof(obj.values) + sys.getsizeof(obj.index)) / 1024 / 1024
            else:
                return sys.getsizeof(obj) / 1024 / 1024
        except:
            return 0.0
    
    def benchmark_creation(self) -> List[BenchmarkResult]:
        """Benchmark object creation performance."""
        results = []
        
        for size in self.data_sizes:
            data, times = self.generate_test_data(size)
            
            # Benchmark NumPy backend (baseTs)
            numpy_time = self.time_function(
                lambda: baseTs(data.copy(), times.copy(), freq=100.0)
            )
            base_ts = baseTs(data, times, freq=100.0)
            memory_numpy = self.estimate_memory_usage(base_ts)
            
            # Benchmark Series backend (TimeSeriesData)
            series_time = self.time_function(
                lambda: TimeSeriesData(data.copy(), index=times.copy(), freq=100.0)
            )
            ts_data = TimeSeriesData(data, index=times, freq=100.0)
            memory_series = self.estimate_memory_usage(ts_data)
            
            result = BenchmarkResult(
                name=f"creation_{size}",
                numpy_time=numpy_time,
                series_time=series_time,
                data_size=size,
                memory_numpy=memory_numpy,
                memory_series=memory_series
            )
            results.append(result)
            print(f"Creation {size:6d} points: NumPy {numpy_time:.4f}s, Series {series_time:.4f}s, "
                  f"Speedup: {result.speedup_ratio:.2%}")
        
        return results
    
    def benchmark_copy_operations(self) -> List[BenchmarkResult]:
        """Benchmark copy operation performance."""
        results = []
        
        for size in self.data_sizes:
            data, times = self.generate_test_data(size)
            
            # Create objects
            base_ts = baseTs(data, times, freq=100.0)
            ts_data = TimeSeriesData(data, index=times, freq=100.0)
            
            # Benchmark copy operations
            numpy_time = self.time_function(lambda: base_ts.copy())
            series_time = self.time_function(lambda: ts_data.copy())
            
            result = BenchmarkResult(
                name=f"copy_{size}",
                numpy_time=numpy_time,
                series_time=series_time,
                data_size=size
            )
            results.append(result)
            print(f"Copy     {size:6d} points: NumPy {numpy_time:.4f}s, Series {series_time:.4f}s, "
                  f"Speedup: {result.speedup_ratio:.2%}")
        
        return results
    
    def benchmark_conversion(self) -> List[BenchmarkResult]:
        """Benchmark conversion between backends."""
        results = []
        
        for size in self.data_sizes:
            data, times = self.generate_test_data(size)
            base_ts = baseTs(data, times, freq=100.0)
            
            # Benchmark conversion from baseTs to TimeSeriesData
            to_series_time = self.time_function(lambda: convert_to_series(base_ts))
            
            # Create TimeSeriesData for reverse conversion
            ts_data = TimeSeriesData(data, index=times, freq=100.0)
            
            # Benchmark conversion from TimeSeriesData to baseTs
            to_numpy_time = self.time_function(lambda: convert_to_basetseries(ts_data))
            
            result = BenchmarkResult(
                name=f"conversion_{size}",
                numpy_time=to_numpy_time,
                series_time=to_series_time,
                data_size=size
            )
            results.append(result)
            print(f"Convert  {size:6d} points: To Series {to_series_time:.4f}s, To NumPy {to_numpy_time:.4f}s")
        
        return results
    
    def benchmark_mathematical_operations(self) -> List[BenchmarkResult]:
        """Benchmark basic mathematical operations."""
        results = []
        
        for size in self.data_sizes:
            data, times = self.generate_test_data(size)
            
            base_ts = baseTs(data, times, freq=100.0)
            ts_data = TimeSeriesData(data, index=times, freq=100.0)
            
            # Benchmark mathematical operations
            def numpy_math():
                return base_ts.data.mean(), base_ts.data.std(), base_ts.data.min(), base_ts.data.max()
            
            def series_math():
                return ts_data.values.mean(), ts_data.values.std(), ts_data.values.min(), ts_data.values.max()
            
            numpy_time = self.time_function(numpy_math)
            series_time = self.time_function(series_math)
            
            result = BenchmarkResult(
                name=f"math_{size}",
                numpy_time=numpy_time,
                series_time=series_time,
                data_size=size
            )
            results.append(result)
            print(f"Math     {size:6d} points: NumPy {numpy_time:.4f}s, Series {series_time:.4f}s, "
                  f"Speedup: {result.speedup_ratio:.2%}")
        
        return results
    
    def run_all_benchmarks(self) -> Dict[str, List[BenchmarkResult]]:
        """Run all benchmark suites."""
        print("Running Migration Performance Benchmarks")
        print("=" * 50)
        
        benchmarks = {
            'creation': self.benchmark_creation,
            'copy': self.benchmark_copy_operations,
            'conversion': self.benchmark_conversion,
            'math': self.benchmark_mathematical_operations
        }
        
        all_results = {}
        for name, benchmark_func in benchmarks.items():
            print(f"\n{name.capitalize()} Benchmark:")
            print("-" * 30)
            all_results[name] = benchmark_func()
            self.results.extend(all_results[name])
        
        return all_results
    
    def plot_results(self, results: Dict[str, List[BenchmarkResult]], save_path: str = None):
        """
        Plot benchmark results.
        
        Args:
            results: Dictionary of benchmark results
            save_path: Optional path to save the plot
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Plot 1: Execution time comparison
        for benchmark_name, benchmark_results in results.items():
            sizes = [r.data_size for r in benchmark_results]
            numpy_times = [r.numpy_time for r in benchmark_results]
            series_times = [r.series_time for r in benchmark_results]
            
            ax1.loglog(sizes, numpy_times, 'o-', label=f'{benchmark_name} (NumPy)')
            ax1.loglog(sizes, series_times, 's-', label=f'{benchmark_name} (Series)')
        
        ax1.set_xlabel('Data Size (points)')
        ax1.set_ylabel('Execution Time (seconds)')
        ax1.set_title('Performance Comparison: NumPy vs Series')
        ax1.legend()
        ax1.grid(True)
        
        # Plot 2: Speedup ratios
        for benchmark_name, benchmark_results in results.items():
            sizes = [r.data_size for r in benchmark_results]
            speedups = [r.speedup_ratio * 100 for r in benchmark_results]
            
            ax2.semilogx(sizes, speedups, 'o-', label=benchmark_name)
        
        ax2.set_xlabel('Data Size (points)')
        ax2.set_ylabel('Speedup (%)')
        ax2.set_title('Series vs NumPy Speedup')
        ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
        ax2.legend()
        ax2.grid(True)
        
        # Plot 3: Memory usage comparison (creation only)
        if 'creation' in results:
            creation_results = results['creation']
            sizes = [r.data_size for r in creation_results]
            numpy_memory = [r.memory_numpy for r in creation_results]
            series_memory = [r.memory_series for r in creation_results]
            
            ax3.loglog(sizes, numpy_memory, 'o-', label='NumPy Memory')
            ax3.loglog(sizes, series_memory, 's-', label='Series Memory')
            ax3.set_xlabel('Data Size (points)')
            ax3.set_ylabel('Memory Usage (MB)')
            ax3.set_title('Memory Usage Comparison')
            ax3.legend()
            ax3.grid(True)
        
        # Plot 4: Memory ratio
        if 'creation' in results:
            creation_results = results['creation']
            sizes = [r.data_size for r in creation_results]
            memory_ratios = [r.memory_ratio for r in creation_results if r.memory_ratio > 0]
            sizes_filtered = [sizes[i] for i in range(len(sizes)) if creation_results[i].memory_ratio > 0]
            
            if memory_ratios:
                ax4.semilogx(sizes_filtered, memory_ratios, 'o-', label='Series/NumPy Ratio')
                ax4.axhline(y=1.0, color='k', linestyle='--', alpha=0.5, label='Equal Memory')
                ax4.set_xlabel('Data Size (points)')
                ax4.set_ylabel('Memory Ratio (Series/NumPy)')
                ax4.set_title('Memory Overhead')
                ax4.legend()
                ax4.grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_report(self) -> str:
        """Generate a summary report of benchmark results."""
        if not self.results:
            return "No benchmark results available."
        
        report = ["Migration Performance Benchmark Report", "=" * 40, ""]
        
        # Group results by benchmark type
        by_type = {}
        for result in self.results:
            benchmark_type = result.name.split('_')[0]
            if benchmark_type not in by_type:
                by_type[benchmark_type] = []
            by_type[benchmark_type].append(result)
        
        for benchmark_type, results in by_type.items():
            report.append(f"{benchmark_type.capitalize()} Benchmark Summary:")
            report.append("-" * 30)
            
            avg_speedup = np.mean([r.speedup_ratio for r in results])
            report.append(f"Average speedup: {avg_speedup:.2%}")
            
            if any(r.memory_ratio > 0 for r in results):
                avg_memory_ratio = np.mean([r.memory_ratio for r in results if r.memory_ratio > 0])
                report.append(f"Average memory ratio: {avg_memory_ratio:.2f}x")
            
            report.append("")
        
        # Overall summary
        overall_speedup = np.mean([r.speedup_ratio for r in self.results])
        report.extend([
            "Overall Summary:",
            "-" * 15,
            f"Total benchmarks run: {len(self.results)}",
            f"Average speedup: {overall_speedup:.2%}",
            f"Data sizes tested: {self.data_sizes}",
            ""
        ])
        
        if overall_speedup > 0:
            report.append("✅ Series backend shows performance improvements")
        elif overall_speedup > -0.1:
            report.append("⚠️  Series backend shows comparable performance")
        else:
            report.append("❌ Series backend shows performance regression")
        
        return "\n".join(report)


def run_migration_benchmarks():
    """Main function to run migration benchmarks."""
    benchmark = MigrationBenchmark()
    results = benchmark.run_all_benchmarks()
    
    print("\n" + "=" * 50)
    print("BENCHMARK SUMMARY")
    print("=" * 50)
    print(benchmark.generate_report())
    
    # Plot results
    try:
        benchmark.plot_results(results, save_path='migration_benchmark_results.png')
        print("\nBenchmark plots saved to 'migration_benchmark_results.png'")
    except Exception as e:
        print(f"\nCould not generate plots: {e}")
    
    return results


if __name__ == "__main__":
    run_migration_benchmarks()