"""
baseTs - A Python library for time series analysis
"""

from .core import baseTs, from_df
from .series import TimeSeriesData
from .compat import BackendManager, convert_to_series, convert_to_basetseries
from .version import __version__

__all__ = ['baseTs', 'from_df', 'TimeSeriesData', 'BackendManager', 
           'convert_to_series', 'convert_to_basetseries']