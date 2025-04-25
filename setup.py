from setuptools import setup, find_packages

setup(
    name="baseTs",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "scipy",
        "pandas",
        "matplotlib",
        "moepy",  # For LOWESS fitting
    ],
    author="Stan Colcombe",
    author_email="stan@sympaticog.com",
    description="A Python library for time series analysis, filtering, and outlier detection",
    keywords="time series, filtering, outlier detection, FFT",
    url="https://github.com/sympaticog/baseTs",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.6",
)