"""
baseTs - A Python library for time series analysis
"""

from .core import baseTs, from_df
from .series import TimeSeriesData
from .version import __version__

__all__ = ['baseTs', 'from_df', 'TimeSeriesData']