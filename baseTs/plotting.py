# -*- coding: utf-8 -*-
"""
Created on Oct 19 2024
@author: stan@sympaticog.com
"""

import math

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from typing import Any, Union, Optional, Tuple

# local imports
#sys.path.append('/Users/stan/Projects/cpCST_MoBI/baseTs')
from .utils import coerce_real_scalar, shift_timeseries

def zscale(x: np.ndarray) -> np.ndarray:
    """Standardize data by removing the mean and scaling to unit variance."""
    return (x - np.mean(x)) / np.std(x)

def setup_plot(ax: Optional[plt.Axes] = None, 
               figsize: Tuple[float, float] = (9, 3),
               title: Optional[str] = None,
               xlabel: Optional[str] = None,
               ylabel: Optional[str] = None,
               show: bool = False) -> Tuple[plt.Figure, plt.Axes]:
    """
    Common setup function for creating and configuring plots.
    
    Args:
        ax: Optional axes to plot on. If None, creates new figure and axes.
        figsize: Tuple of (width, height) in inches.
        title: Optional plot title.
        xlabel: Optional x-axis label.
        ylabel: Optional y-axis label.
        show: Whether to display the plot.
        
    Returns:
        Tuple of (figure, axes)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure
        
    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.grid(True)
    
    if show:
        plt.show()
        
    return fig, ax

def qc_plot(ts,
            filt_data: np.array,
            filt_times: Optional[np.array] = None,
            ax: Optional[plt.Axes] = None,
            title: Optional[str] = None,
            xlabel: Optional[str] = None,
            ylabel: Optional[str] = None,
            show_lowess: bool = True,
            show: bool = False) -> plt.Axes:
    """
    Plots a quality control plot for a timeseries.
    """
    if title is None:
        title = f"QC Plot for {ts.signal_name}"
    if xlabel is None:
        xlabel = "Time"
    if ylabel is None:
        ylabel = ts.signal_name + " " + ts.last_process
    if filt_times is None:
        filt_times = ts.times

    _, ax = setup_plot(ax=ax, title=title, xlabel=xlabel, ylabel=ylabel, show=False)

    ax.plot(ts.times, ts.data, label='Original')
    ax.plot(filt_times, filt_data, label='Filtered')
    # Gate on the fit itself, not on is_outlier_filtered: that flag means "a
    # filter has been configured", so it is True before any fit exists and
    # False after lowess_detrend, which produces a fit without filtering.
    if show_lowess and ts.lowess_fit is not None:
        ax.plot(ts.times, ts.lowess_fit, label='Lowess Fit')
    ax.legend()
    
    if show:
        plt.show()
        
    return ax

def hist(ts,
         ax: Optional[plt.Axes] = None,
         title: Optional[str] = None,
         xlabel: Optional[str] = None,
         show: bool = False,
         bins: int = -1,
         kde: bool = False) -> plt.Axes:
    """
    Plots a histogram of a timeseries.
    """
    if xlabel is None:
        xlabel = ts.signal_name + " " + ts.last_process
    if bins == -1:
        bins = 'auto'
    
    plotkind = "KDE" if kde else "Histogram"
    ylabel = "Density" if kde else "Frequency"
    if title is None:
        title = f"{plotkind} of {ts.signal_name} {ts.last_process}"
        
    _, ax = setup_plot(ax=ax, title=title, xlabel=xlabel, ylabel=ylabel, show=False)
        
    # Plot histogram
    ax.hist(ts.data, bins=bins, density=kde, edgecolor='black', label='Histogram', alpha=0.6)
    
    if kde:
        # Calculate KDE
        kde_obj = gaussian_kde(ts.data)
        x = np.linspace(min(ts.data), max(ts.data), 150)
        y = kde_obj(x)
        # Plot KDE
        ax.plot(x, y, label='KDE')
        ax.legend()
        
    if show:
        plt.show()
        
    return ax

def plot(ts,
         ax: Optional[plt.Axes] = None,
         title: Optional[str] = None,
         xlabel: Optional[str] = None,
         ylabel: Optional[str] = None, 
         show: bool = False,
         lowess: bool = False,
         start_idx: int = 0,
         end_idx: int = -1) -> plt.Axes: 
    """
    Plots a timeseries.
    """
    from baseTs import baseTs  # Import inside the function to avoid circular import
    
    if not isinstance(ts, baseTs):
        raise TypeError("ts must be an instance of baseTs")
    
    if title is None:
        title = f"{ts.signal_name} by time."
    if xlabel is None:
        xlabel = "Time in seconds."
    if ylabel is None:
        ylabel = ts.signal_name + " " + ts.last_process
        
    _, ax = setup_plot(ax=ax, title=title, xlabel=xlabel, ylabel=ylabel, show=False)
        
    ax.plot(ts.times[start_idx:end_idx], ts.data[start_idx:end_idx], 
            label=ts.signal_name + ts.last_process)
    if lowess:
        # Raise rather than skip, unlike qc_plot: there the fit is an optional
        # extra on a plot that stands without it, here the caller asked for it
        # by name. A derived object has no fit of its own - filter_outliers or
        # lowess_detrend produce one, and it does not survive an index change.
        if ts.lowess_fit is None:
            raise ValueError(
                "lowess=True but this object has no lowess_fit. Run "
                "filter_outliers() or lowess_detrend() on it first; a fit does "
                "not carry over to an object with a different index."
            )
        ax.plot(ts.times[start_idx:end_idx], ts.lowess_fit[start_idx:end_idx],
                label='Lowess Fit')
        ax.legend()
        
    if show:
        plt.show()
        
    return ax

def plot_series(base_ts,
                series_list: list,
                ax: Optional[plt.Axes] = None,
                title: Optional[str] = None,
                xlabel: Optional[str] = None,
                ylabel: Optional[str] = None, 
                show: bool = False,
                start_idx: int = 0,
                end_idx: int = -1) -> plt.Axes: 
    """
    Plots multiple timeseries on the same plot.
    """
    from baseTs import baseTs  # Import inside the function to avoid circular import
    
    if not isinstance(base_ts, baseTs):
        raise TypeError("base_ts must be an instance of baseTs")
    
    if title is None:
        title = f"{base_ts.signal_name} by time."
    if xlabel is None:
        xlabel = "Time in seconds."
    if ylabel is None:
        ylabel = base_ts.signal_name + " " + base_ts.last_process
        
    _, ax = setup_plot(ax=ax, title=title, xlabel=xlabel, ylabel=ylabel, show=False)
        
    ax.plot(base_ts.times[start_idx:end_idx], base_ts.data[start_idx:end_idx], 
            label=base_ts.signal_name)
    
    for series in series_list:
        ax.plot(series.times[start_idx:end_idx], series.data[start_idx:end_idx], 
                label=f"{series.signal_name} {series.last_process}")
    ax.legend()
    
    if show:
        plt.show()
        
    return ax

def _validate_display_rate(value: Any, name: str,
                           nan_means_default: bool = False) -> float:
    """Coerce a frequency bound to a float matplotlib can use as an axis limit.

    The type rules are delegated to utils.coerce_real_scalar, shared with
    validate_sampling_freq: a display bound and a sampling rate disagree about
    which *values* are acceptable, but not about what counts as a number, and
    a second copy of the latter would drift (#28).

    Args:
        value: The bound as the caller passed it
        name: The parameter's name, for the error message
        nan_means_default: If True, NaN is passed through as the caller's
            "use the default" sentinel rather than rejected

    Returns:
        The bound as a plain float, NaN only when `nan_means_default`

    Raises:
        ValueError: If the bound is not a real scalar, or is not finite
    """
    rate = coerce_real_scalar(value, f"Invalid {name}")
    if math.isnan(rate) and nan_means_default:
        return rate
    if not math.isfinite(rate):
        # Deliberately not worded as "axis limits cannot be NaN or Inf": this
        # is shared with the highlight_band edges, which are not axis limits.
        raise ValueError(
            f"Invalid {name}: {value!r} is not a finite frequency in Hz."
        )
    return rate


def _validate_highlight_band(
    highlight_band: Any,
) -> Tuple[Tuple[Any, Any], Tuple[float, float]]:
    """Unpack and coerce a (low, high) band, or raise ValueError naming it.

    Both edges go through the same door as the display bounds, which closes a
    hole the ordering check could not: `band_low >= band_high` is False when
    either edge is NaN, since every comparison against NaN is False - so
    (nan, 0.5) was silently shaded and legended as though it were a valid
    band. The same shape of defect as #30, where `max(hp_hz, lp_hz)` let
    argument position decide which edge got checked.

    Args:
        highlight_band: The band as the caller passed it

    Returns:
        `((low, high), (low_hz, high_hz))` - the caller's own edge objects
        first, then the validated floats.

        Both are returned so that the band is unpacked exactly once. An earlier
        revision returned only the floats and re-unpacked the original at draw
        time to build the legend label; that turned a one-shot iterable - a
        generator, `iter([...])` - from a working band on the previous release
        into a ValueError naming nothing the caller could act on, because the
        first unpack had already exhausted it.

        Draw with the floats: validating one object and drawing with another is
        what #30 found in the filter family. Label with the originals, so an
        integer band still reads "1-2 Hz" rather than "1.0-2.0 Hz". Geometry
        uses what was checked; presentation does not silently reformat what the
        caller wrote.

    Raises:
        ValueError: If the band is not a pair, or either edge is not a finite
            real scalar
    """
    try:
        band_low, band_high = highlight_band
    except (TypeError, ValueError) as exc:
        # Unpacking raises TypeError for a non-iterable and ValueError for the
        # wrong length; both are the same caller mistake and both are outside
        # the ValueError contract this function's docstring promises.
        raise ValueError(
            f"highlight_band must be a (low, high) pair of frequencies in Hz, "
            f"got {highlight_band!r}"
        ) from exc
    return ((band_low, band_high),
            (_validate_display_rate(band_low, "highlight_band's lower edge"),
             _validate_display_rate(band_high, "highlight_band's upper edge")))


def plot_fft_power(ts,
                   max_rate: float = np.nan,
                   min_rate: float = 0.0,
                   window: str = None,
                   ax: Optional[plt.Axes] = None,
                   title: Optional[str] = None,
                   xlabel: Optional[str] = None,
                   ylabel: Optional[str] = None, 
                   show: bool = False,
                   scale_power: bool = False,
                   highlight_band: Optional[Tuple[float, float]] = None) -> plt.Axes:
    """
    Plots the power spectrum of a timeseries signal using enhanced FFT with windowing.

    Args:
        ts: Time series object
        max_rate: Maximum frequency to display (defaults to Nyquist frequency)
        min_rate: Minimum frequency to display (defaults to 0.0)
        window: Window function to apply ('hann', 'hamming', 'blackman', None)
        ax: Matplotlib axes to plot on
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        show: Whether to show the plot
        scale_power: Whether to normalize power spectrum
        highlight_band: Optional (low_freq, high_freq) tuple in Hz to shade,
            e.g. (0.01, 0.1) to mark the default relative_band_power()
            band

    Returns:
        Matplotlib axes object

    Raises:
        TypeError: If `ts` is not a baseTs
        ValueError: For every other rejected input, so that one `except
            ValueError` covers the whole function:

            - the sampling rate is unusable (NaN, zero or negative)
            - the data is complex (pass `.real`, `.imag` or `np.abs` of it)
            - the data contains NaN or Inf (fill gaps first, e.g. with
              `interpolate_gaps()`)
            - `window` names an unknown window function
            - `min_rate` or `max_rate` is not a real finite scalar; `max_rate`
              additionally accepts NaN, its documented "use Nyquist" sentinel
            - [min_rate, max_rate] selects no frequency bins
            - `highlight_band` is not a pair of real finite frequencies, or is
              not strictly increasing

        ZeroDivisionError: If the series is empty. Pre-existing and not
            specific to plotting - `get_frequency_content`, `get_peak_freq`,
            `relative_band_power` and `falff` all divide by a zero-length
            index, while only `compute_fft_power` guards it (issue #62). It is
            listed here rather than guarded here because the fix belongs in
            the shared spectral door, not in one of its five callers.

    The bounds are validated before the series, so a call that is wrong in both
    ways reports the bound first. That is deliberate: the bounds are arguments
    the caller can fix immediately, and checking them is far cheaper than the
    FFT that would otherwise run before the complaint.

    A rejected call draws nothing: no figure is created, and a caller-supplied
    `ax` is returned to them untouched.
    """
    from baseTs import baseTs  # Import inside the function to avoid circular import

    if not isinstance(ts, baseTs):
        raise TypeError("ts must be an instance of baseTs")

    # Compute first, draw second (issue #34). Everything that can fail on the
    # caller's input runs before setup_plot, so a rejected call has built
    # nothing: no figure is minted and a caller-supplied `ax` is untouched.
    #
    # This replaces a bare `except Exception` that rendered the message as text
    # on the axes and returned a normal Axes, which neutralised every rate and
    # data guard #24 and #28 added and handed batch pipelines a bogus figure
    # with a success exit code. Narrowing that except would not have been
    # enough - setup_plot ran above it, so each rejected call still leaked a
    # figure into pyplot's registry.
    #
    # The display bounds are checked here rather than left to matplotlib
    # because they end up in ax.set_xlim, which rejects NaN and Inf. set_xlim
    # raises eagerly, not at draw time - but it is called below, once the axes
    # already exist, so leaving the check to it would still mint a figure and
    # title a caller-supplied ax before failing. An infinite max_rate passes
    # the frequency mask below (the mask is non-empty), so nothing else would
    # stop it first, and the guarantee above would be false for exactly one
    # input.
    min_rate = _validate_display_rate(min_rate, 'min_rate')
    # NaN is max_rate's documented public sentinel for "use Nyquist", so it is
    # the one non-finite value allowed through; it is resolved below, once
    # there is a spectrum to take the top bin from.
    max_rate = _validate_display_rate(max_rate, 'max_rate', nan_means_default=True)

    if highlight_band is not None:
        # Unpacked once, here: highlight_band may be a one-shot iterable.
        (label_low, label_high), (band_low, band_high) = \
            _validate_highlight_band(highlight_band)
        if band_low >= band_high:
            raise ValueError(
                f"highlight_band low ({band_low} Hz) must be less than "
                f"high ({band_high} Hz)"
            )

    # Use the enhanced get_frequency_content method
    freqs, power = ts.get_frequency_content(window=window)

    # Pre-existing, and it has no reachable trigger: get_frequency_content
    # returns at least the DC bin for any n >= 1 (measured: n=1 -> 1 bin,
    # n=2 -> 1, n=3 -> 2, n=4 -> 2), and n == 0 raises ZeroDivisionError inside
    # np.fft.fftfreq before reaching here (issue #62). Kept as defence in depth
    # rather than deleted, but deliberately left out of the docstring's Raises
    # list: documenting an unreachable branch as a contract invites callers to
    # write handling for something that cannot happen.
    if len(freqs) == 0 or len(power) == 0:
        raise ValueError("FFT computation resulted in empty frequency or power arrays")

    # Apply frequency range filtering
    if np.isnan(max_rate):
        max_rate = np.max(freqs)  # Use Nyquist frequency as default

    # Create frequency mask for the specified range
    freq_mask = (freqs >= min_rate) & (freqs <= max_rate)
    freqs_filtered = freqs[freq_mask]
    power_filtered = power[freq_mask]

    if len(freqs_filtered) == 0:
        raise ValueError(f"No frequencies found in range [{min_rate}, {max_rate}] Hz")

    # Apply power scaling if requested
    if scale_power:
        power_max = np.max(power_filtered)
        if power_max > 0:
            power_filtered = power_filtered / power_max

    # Set up title with window information
    window_str = f" ({window} window)" if window else ""
    if title is None:
        title = f"Power Spectrum of {ts.signal_name}{ts.last_process}{window_str}"
    if xlabel is None:
        xlabel = "Frequency (Hz)"
    if ylabel is None:
        ylabel = "Power"
    if scale_power:
        ylabel = "Scaled " + ylabel

    _, ax = setup_plot(ax=ax, title=title, xlabel=xlabel, ylabel=ylabel, show=False)

    # Plotting
    ax.plot(freqs_filtered, power_filtered, linewidth=1.2)
    ax.set_xlim(min_rate, max_rate)

    # Shade the band of interest, if requested
    if highlight_band is not None:
        # The span is drawn from the validated floats and the label from the
        # caller's originals, both unpacked once above. Drawing with
        # unvalidated originals is the hole #30 found in the filter family;
        # here it is a principle rather than an observable difference, since
        # matplotlib coerces the span through float() itself. Labelling with
        # the floats, on the other hand, is observable: it turned
        # highlight_band=(1, 2) into a legend reading "1.0-2.0 Hz" where it
        # had always read "1-2 Hz".
        ax.axvspan(band_low, band_high, alpha=0.15, color='tab:orange',
                   label=f"{label_low}-{label_high} Hz")
        ax.legend()

    # Add grid for better readability
    ax.grid(True, alpha=0.3)

    # Set y-axis to start at 0 for power spectra
    ax.set_ylim(bottom=0)

    if show:
        plt.show()

    return ax

def lag_plot(ts,
            lag: Union[int, float], 
            lag_unit: str = "index",
            ax: Optional[plt.Axes] = None,
            show: bool = False) -> plt.Axes:
    """
    Generate a lag plot for a given timeseries object and lag.
    """
    res = shift_timeseries(ts, lag, lag_unit, drop_nan=False)
    lagged_data = res['lagged_data']
    lag_secs = res['lag_secs']
    lag_idx = res['lag_idx']
    
    try:
        sig_name = ts.signal_name.upper()
    except Exception as e:
        print(f"An error occurred: {e}")
        sig_name = "Signal"

    title = f'{sig_name} Lag Plot at {lag_secs} seconds ({lag_idx}items)'
    xlabel = f'Original {sig_name} Data'
    ylabel = f'{sig_name} Data lagged at {lag_secs}second ({lag_idx}items)'
    
    _, ax = setup_plot(ax=ax, title=title, xlabel=xlabel, ylabel=ylabel, show=False)
    
    ax.scatter(ts.data[lag_idx:], lagged_data[lag_idx:], s=3)  # Skip the NaN values for plotting
    
    if show:
        plt.show()
        
    return ax
