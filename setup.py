from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="baseTs",
    version="0.3.0",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "numpy>=1.19.0",
        "scipy>=1.5.0",
        "pandas>=2.0.0",
        "matplotlib>=3.0.0",
        "statsmodels>=0.14",  # For LOWESS fitting
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "hypothesis>=6.0",
            "psutil>=5.0",
            "black>=22.0",
            "isort>=5.0",
            "mypy>=0.910",
            "flake8>=4.0",
        ],
    },
    author="Stan Colcombe",
    author_email="stan@sympaticog.com",
    description="A Python library for time series analysis, filtering, and outlier detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="time series, filtering, outlier detection, FFT, signal processing",
    url="https://github.com/SympatiCog/baseTs",
    project_urls={
        "Bug Reports": "https://github.com/SympatiCog/baseTs/issues",
        "Source": "https://github.com/SympatiCog/baseTs",
        "Documentation": "https://github.com/SympatiCog/baseTs/blob/main/docs/",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
)