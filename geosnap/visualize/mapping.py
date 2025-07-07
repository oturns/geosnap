"""functions for choropleth mapping timeseries data."""

import os
import re
import tempfile
from pathlib import PurePath
from warnings import warn

import contextily as ctx
import mapclassify.classifiers as classifiers
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import ArtistAnimation, PillowWriter

schemes = {}
for classifier in classifiers.CLASSIFIERS:
    schemes[classifier.lower()] = getattr(classifiers, classifier)


__all__ = [
    "animate_timeseries",
    "gif_from_path",
    "plot_timeseries",
]


def gif_from_path(
    path=None,
    figsize=(10, 10),
    fps=0.5,
    interval=500,
    repeat_delay=1000,
    filename=None,
    dpi=400,
):
    """
    Create an animated gif from a director of image files.

    Parameters
    ----------
    path : str, required
        path to directory of images
    figsize : tuple, optional
        output figure size passed to matplotlib.pyplot
    fps : float, optional
        frames per second
    interval : int, optional
        interval between frames in miliseconds, default 500
    repeat_delay : int, optional
        time before animation repeats in miliseconds, default 1000
    filename : str, required
        output file name
    dpi : int, optional
        image dpi passed to matplotlib writer
    """
    assert filename, "You must provide an output filename ending in .gif"
    imgs = os.listdir(path)
    imgs.sort(
        key=lambda var: [
            int(x) if x.isdigit() else x for x in re.findall(r"[^0-9]|[0-9]+", var)
        ]
    )

    fig, ax = plt.subplots(figsize=figsize)
    ax.axis("off")
    ims = []

    for i in imgs:
        c = plt.imread(str(PurePath(path, i)))
        im = plt.imshow(c, animated=True)
        ims.append([im])

    writer = PillowWriter(fps=fps)

    ani = ArtistAnimation(
        fig, ims, interval=interval, blit=True, repeat_delay=repeat_delay
    )

    plt.tight_layout()
    ani.save(filename, writer=writer, dpi=dpi)
    plt.clf()


def plot_timeseries(
    gdf,
    column,
    title="",
    temporal_index="year",
    time_subset=None,
    scheme="quantiles",
    k=5,
    pooled=True,
    cmap=None,
    legend=True,
    categorical=False,
    save_fig=None,
    dpi=200,
    legend_kwds="default",
    missing_kwds="default",
    figsize=None,
    ncols=None,
    nrows=None,
    ctxmap="default",
    alpha=0.7,
    web_mercator=True,
):
    """Plot an attribute from a geodataframe arranged as a timeseries with consistent colorscaling.

    Parameters
    ----------
    df : pandas.DataFrame
        pandas dataframe with
    column : str
        column to be graphed in a time series
    title : str, optional
        desired title of figure
    temporal_index  : str, required
        name of column on dataframe that holds unique time periods
        default is every year in dataframe.
    scheme : string,optional
        matplotlib scheme to be used to create choropleth bins
        default is 'quantiles'
    k : int, optional
        number of bins to graph. k may be ignored
        or unnecessary for some schemes, like headtailbreaks, maxp, and maximum_breaks
        Default is 5.
    pooled : bool, optional
        whether the classification should be pooled across time periods or unique to each.
        E.g. with a 'quantile' scheme, pooled=True indicates that quantiles should be identified
        on the entire time series, whereas pooled=False indicates that they should be calculated
        independently for each time period
    legend : bool, optional
        whether to display a legend on the plot
    categorical : bool, optional
        whether the data should be plotted as categorical as opposed to continuous
    save_fig : str, optional
        path to save figure if desired.
    dpi : int, optional
        dpi of the saved image if save_fig=True
        default is 500
    legend_kwds  : dictionary, optional
        parameters for the legend
    missing_kwds : dictionary, optional
        parameters for the plotting missing data
        Default is 1 column on the bottom of the graph.
    ncols : int, optional
        number of columns in the figure
        if passing ncols, nrows must also be passed
        default is None
    nrows : int, optional
        number of rows in the figure
        if passing nrows, ncols must also be passed
        default is None
    figsize : tuple, optional
        the desired size of the matplotlib figure
    ctxmap : contextily map provider, optional
        contextily basemap. Set to False for no basemap.
        Default is CartoDB.Positron
    alpha : int (optional)
        Transparency parameter passed to matplotlib
    web_mercator : bool, optional
        whether to reproject the data into web mercator (epsg 3857)
    """
    try:
        import proplot as plot

        HAS_PROPLOT = True
        f, axs = plot.subplots(ncols=ncols, nrows=nrows, figsize=figsize, share=False)

    except ImportError:
        warn("`proplot` is not installed.  Falling back to matplotlib")
        import matplotlib.pyplot as plot

        HAS_PROPLOT = False

    # proplot needs to be used as a function-level import,
    # as it influences all figures when imported at the top of the file

    if ctxmap == "default":
        ctxmap = ctx.providers.CartoDB.Positron
    if categorical:  # there's no pooled classification for categorical
        pooled = False

    df = gdf.copy()
    if web_mercator:
        assert df.crs, (
            "Unable to reproject because geodataframe has no CRS "
            "Please set a coordinate system or pass `web_mercator=False`"
        )
        if not df.crs.equals(3857):
            df = df.to_crs(3857)
    if categorical and not cmap:
        cmap = "Accent"
    elif not cmap:
        cmap = "Blues"
    if legend_kwds == "default":
        legend_kwds = {"ncols": 1, "loc": "b"} if HAS_PROPLOT else None
    if missing_kwds == "default":
        missing_kwds = {
            "color": "lightgrey",
            "edgecolor": "red",
            "hatch": "///",
            "label": "Missing values",
        }

    if time_subset is None:
        time_subset = df[temporal_index].unique()

    if pooled:
        # if pooling the classifier, create one from scratch and pass to user defined
        classifier = schemes[scheme](df[column].dropna().values, k=k)

    if nrows is None and ncols is None:
        sqcols = int(np.ceil(np.sqrt(len(time_subset))))
        ncols = sqcols
        nrows = sqcols

    if HAS_PROPLOT is True:
        f, axs = plot.subplots(ncols=ncols, nrows=nrows, figsize=figsize, share=False)
    else:
        f, axs = plot.subplots(ncols=ncols, nrows=nrows, figsize=figsize)
        axs = [axs] if not hasattr(axs, "shape") else axs.flatten()

    for i, time in enumerate(sorted(time_subset)):
        # sort to prevent graphing out of order
        if categorical:
            df.query(f"{temporal_index}=={time}").plot(
                column=column,
                ax=axs[i],
                categorical=True,
                cmap=cmap,
                legend=legend,
                legend_kwds=legend_kwds,
                # missing_kwds=missing_kwds,
                alpha=alpha,
            )
        else:
            if pooled:
                df.query(f"{temporal_index}=={time}").plot(
                    column=column,
                    ax=axs[i],
                    scheme="userdefined",
                    classification_kwds={"bins": classifier.bins},
                    k=k,
                    cmap=cmap,
                    legend=legend,
                    legend_kwds=legend_kwds,
                    alpha=alpha,
                )
            else:
                df.query(f"{temporal_index}=={time}").plot(
                    column=column,
                    ax=axs[i],
                    scheme=scheme,
                    k=k,
                    cmap=cmap,
                    legend=legend,
                    legend_kwds=legend_kwds,
                    alpha=alpha,
                )
        if ctxmap:  # need set basemap of each graph
            ctx.add_basemap(axs[i], source=ctxmap, crs=df.crs.to_string())
        axs[i].set_title(time)
        axs[i].axis("off")
    if HAS_PROPLOT:
        if not title:  # only use title when passed
            axs.format(suptitle=column)
        else:
            axs.format(suptitle=title)
    else:
        if title:
            plt.suptitle(title)

    if save_fig:
        f.savefig(save_fig, dpi=dpi, bbox_inches="tight")
    return axs


def animate_timeseries(
    gdf,
    column=None,
    filename=None,
    title="",
    temporal_index="year",
    time_periods=None,
    scheme="quantiles",
    k=5,
    cmap=None,
    legend=True,
    alpha=0.6,
    categorical=False,
    dpi=200,
    fps=0.5,
    interval=500,
    repeat_delay=1000,
    title_fontsize=40,
    subtitle_fontsize=38,
    figsize=(20, 20),
    ctxmap="default",
    plot_kwargs=None,
    color_col=None,
):
    """Create an animated gif from a long-form geodataframe timeseries.

    Parameters
    ----------
    column : str
        column to be graphed in a time series
    filename : str, required
        output file name
    title : str, optional
        desired title of figure
    temporal_index : str, required
        column on the gdf that stores time periods
    time_periods:  list, optional
        subset of time periods to include in the animation. If None, then all
        times will be used
    scheme : string, optional
        matplotlib scheme to be used
        default is 'quantiles'
    k : int, optional
        number of bins to graph. k may be ignored
        or unnecessary for some schemes, like headtailbreaks, maxp, and maximum_breaks
        Default is 5.
    legend : bool, optional
        whether to display a legend on the plot
    categorical : bool, optional
        whether the data should be plotted as categorical as opposed to continuous
    alpha : float, optional
        transparency parameter passed to matplotlib
    dpi : int, optional
        dpi of the saved image if save_fig=True
        default is 500
    figsize : tuple, optional
        the desired size of the matplotlib figure
    ctxmap : contextily map provider, optional
        contextily basemap. Set to False for no basemap.
    figsize : tuple, optional
        output figure size passed to matplotlib.pyplot
    fps : float, optional
        frames per second, used to speed up or slow down animation
    interval : int, optional
        interval between frames in miliseconds, default 500
    repeat_delay : int, optional
        time before animation repeats in miliseconds, default 1000
    plot_kwargs: dict, optional
        additional keyword arguments passed to geopandas.DataFrame.plot
    color_col: str, optional
        A column on the geodataframe holding hex coodes used to color each
        observation. I.e. to create a categorical color-mapping manually
    """
    classification_kwds = {}
    if plot_kwargs is None:
        plot_kwargs = dict()

    if ctxmap == "default":
        ctxmap = ctx.providers.CartoDB.Positron

    if color_col is not None and categorical is True:
        raise ValueError("When passing a color column, use `categorical=False`")

    if color_col is not None and cmap is not None:
        raise ValueError("Only `color_col` or `cmap` can be used, but not both")

    gdf = gdf.copy()
    if not gdf.crs.equals(3857):
        gdf = gdf.to_crs(3857)

    if not time_periods:
        time_periods = list(gdf[temporal_index].unique())
    time_periods = sorted(time_periods)

    with tempfile.TemporaryDirectory() as tmpdirname:
        for i, time in enumerate(time_periods):
            fig, ax = plt.subplots(figsize=figsize)
            outpath = PurePath(tmpdirname, f"file_{i}.png")

            temp = gdf[gdf[temporal_index] == time]
            colors = temp[color_col] if color_col is not None else None

            if categorical:
                temp.plot(
                    column,
                    categorical=True,
                    ax=ax,
                    alpha=alpha,
                    legend=legend,
                    cmap=cmap,
                    **plot_kwargs,
                )
            else:
                if colors is not None:
                    classification_kwds = None
                    scheme = None
                    k = None
                else:
                    if scheme == "userdefined":
                        classifier = schemes[scheme](
                            gdf[column].dropna().values,
                            bins=classification_kwds["bins"],
                        )
                    else:
                        classifier = schemes[scheme](gdf[column].dropna().values, k=k)
                    classification_kwds = {"bins": classifier.bins}
                    scheme = "userdefined"
                temp.plot(
                    column,
                    scheme=scheme,
                    classification_kwds=classification_kwds,
                    k=k,
                    ax=ax,
                    alpha=alpha,
                    legend=legend,
                    cmap=cmap,
                    color=colors,
                    **plot_kwargs,
                )
            ctx.add_basemap(ax=ax, source=ctxmap)
            ax.axis("off")
            ax.set_title(f"{time}", fontsize=subtitle_fontsize, backgroundcolor="white")
            fig.suptitle(f"{title}", fontsize=title_fontsize)

            plt.tight_layout()
            plt.savefig(outpath, dpi=dpi)
            plt.clf()

        gif_from_path(
            tmpdirname,
            interval=interval,
            repeat_delay=repeat_delay,
            filename=filename,
            fps=fps,
            dpi=dpi,
        )
