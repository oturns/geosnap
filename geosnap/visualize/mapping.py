"""functions for choropleth mapping timeseries data."""

import os
import re
import tempfile
from pathlib import PurePath

import contextily as ctx
import mapclassify.classifiers as classifiers
import matplotlib.pyplot as plt
from matplotlib.animation import ArtistAnimation, PillowWriter

schemes = {}
for classifier in classifiers.CLASSIFIERS:
    schemes[classifier.lower()] = getattr(classifiers, classifier)


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
    path :str, required
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
    **kwargs,
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
        Default is Stamen.TonerLite
    alpha : int (optional)
        Transparency parameter passed to matplotlib
    web_mercator : bool, optional
        whether to reproject the data into web mercator (epsg 3857)
    """
    # proplot needs to be used as a function-level import,
    # as it influences all figures when imported at the top of the file
    import proplot as plot

    if ctxmap == "default":
        ctxmap = ctx.providers.Stamen.TonerLite
    if categorical:  # there's no pooled classification for categorical
        pooled = False

    df = gdf.copy()
    if web_mercator:
        assert df.crs, ("Unable to reproject because geodataframe has no CRS "
        "Please set a coordinate system or pass `web_mercator=False`")
        if not df.crs.equals(3857):
            df = df.to_crs(3857)
    if categorical and not cmap:
        cmap = "Accent"
    elif not cmap:
        cmap = "Blues"
    if legend_kwds == "default":
        legend_kwds = {"ncols": 1, "loc": "b"}
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
        f, axs = plot.subplots(ncols=len(time_subset), figsize=figsize,share=False)
    else:
        f, axs = plot.subplots(ncols=ncols, nrows=nrows, figsize=figsize,share=False)

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
                #missing_kwds=missing_kwds,
                alpha=alpha,
            )
        else:
            if pooled:
                df.query(f"{temporal_index}=={time}").plot(
                    column=column,
                    ax=axs[i],
                    scheme="user_defined",
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

    if not title:  # only use title when passed
        axs.format(suptitle=column)
    else:
        axs.format(suptitle=title)

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
):
    """Create an animated gif from a Community timeseries.

    Parameters
    ----------
    column       : str
                    column to be graphed in a time series
    filename     : str, required
                    output file name
    title        : str, optional
                    desired title of figure
    temporal_index     : str, required
                    column on the Community.gdf that stores time periods
    time_periods:  list, optional
                    subset of time periods to include in the animation. If None, then all times will be used
    scheme       : string, optional
                    matplotlib scheme to be used
                    default is 'quantiles'
    k            : int, optional
                    number of bins to graph. k may be ignored
                    or unnecessary for some schemes, like headtailbreaks, maxp, and maximum_breaks
                    Default is 5.
    legend       : bool, optional
                    whether to display a legend on the plot
    categorical  : bool, optional
                    whether the data should be plotted as categorical as opposed to continuous
    alpha:       : float, optional
                    transparency parameter passed to matplotlib
    dpi          : int, optional
                    dpi of the saved image if save_fig=True
                    default is 500
    figsize      : tuple, optional
                    the desired size of the matplotlib figure
    ctxmap       : contextily map provider, optional
                    contextily basemap. Set to False for no basemap.
    figsize      : tuple, optional
                    output figure size passed to matplotlib.pyplot
    fps          : float, optional
                    frames per second, used to speed up or slow down animation
    interval     : int, optional
                    interval between frames in miliseconds, default 500
    repeat_delay : int, optional
                    time before animation repeats in miliseconds, default 1000
    """
    if ctxmap == "default":
        ctxmap = ctx.providers.Stamen.TonerLite
    gdf = gdf.copy()
    if categorical and not cmap:
        cmap = "Accent"
    elif not cmap:
        cmap = "Blues"
    if not gdf.crs == 3857:
        gdf = gdf.to_crs(3857)
    if not time_periods:
        time_periods = list(gdf[temporal_index].unique())
    time_periods = sorted(time_periods)
    with tempfile.TemporaryDirectory() as tmpdirname:
        for i, time in enumerate(time_periods):
            fig, ax = plt.subplots(figsize=figsize)
            outpath = PurePath(tmpdirname, f"file_{i}.png")
            if categorical:
                gdf[gdf[temporal_index] == time].plot(
                    column,
                    categorical=True,
                    ax=ax,
                    alpha=alpha,
                    legend=legend,
                    cmap=cmap,
                )
            else:
                classifier = schemes[scheme](gdf[column].dropna().values, k=k)
                gdf[gdf[temporal_index] == time].plot(
                    column,
                    scheme="user_defined",
                    classification_kwds={"bins": classifier.bins},
                    k=k,
                    ax=ax,
                    alpha=alpha,
                    legend=legend,
                    cmap=cmap,
                )
            ctx.add_basemap(ax=ax, source=ctxmap)
            ax.axis("off")
            ax.set_title(f"{time}", fontsize=subtitle_fontsize)
            fig.suptitle(f"{title}", fontsize=title_fontsize)

            plt.tight_layout()
            plt.savefig(outpath, dpi=dpi)

        gif_from_path(
            tmpdirname,
            interval=interval,
            repeat_delay=repeat_delay,
            filename=filename,
            fps=fps,
            dpi=dpi,
        )
