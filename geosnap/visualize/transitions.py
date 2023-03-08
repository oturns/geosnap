"""plotting for spatial Markov transition matrices."""

import os
from warnings import warn

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import seaborn as sns

from ..analyze.dynamics import transition

__all__ = ["plot_transition_graphs", "plot_transition_matrix"]


def plot_transition_matrix(
    gdf=None,
    cluster_col=None,
    w_type="rook",
    w_options=None,
    temporal_index="year",
    unit_index="geoid",
    permutations=0,
    figsize=(13, 12),
    n_rows=None,
    n_cols=None,
    suptitle=None,
    title_kwds=None,
    savefig=None,
    dpi=300,
    transition_model=None,
):
    """Plot global and spatially-conditioned transition matrices as heatmaps.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        a long-form geodataframe with columns for unit index, time index, and class value
    cluster_col : str
        column on the gdf containing neighborhood type labels
    temporal_index : string, optional
        Column defining time and or sequencing of the long-form data.
        Default is "year".
    unit_index : string, optional
        Column identifying the unique id of spatial units.
        Default is "geoid".
    w_type : string, optional
        Type of spatial weights type ("rook", "queen", "knn" or
        "kernel") to be used for spatial structure. Default is
        None, if non-spatial Markov transition rates are desired.
    w_options : dict
        additional options passed to a libpysal weights constructor (e.g. `k` for a KNN weights matrix)
    permutations : int, optional
        number of permutations for use in randomization based
        inference (the default is 0).
    figsize : tuple, optional
        size of the resulting figure (13, 12)
    n_rows : int, optional
        rows in the plot; n_rows * n_cols must be >= the number of neighborhood types
    n_cols : int, optional
        columns in the plot; n_rows * n_cols must be >= the number of neighborhood types
    suptitle : str, optional
        title of the figure
    title_kwds : dict, optional
        additional keyword options for formatting the title
    savefig : str, optional
        location the plot will be saved
    dpi : int, optional
        dpi of the resulting image, default is 300

    Returns
    -------
    matplotlib Axes
        the axes on which the plots are drawn
    """

    if not title_kwds:
        title_kwds = {
            "fontsize": 20,
        }
    if transition_model is None:
        warn(
            "Creating a transition model implicitly is deprecated and will be removed in future versions. "
            "please pass a giddy.Spatial_Markov instance using `giddy` or `geosnap.analyze.transition`"
        )

        sm = transition(
            gdf,
            cluster_col=cluster_col,
            temporal_index=temporal_index,
            unit_index=unit_index,
            w_type=w_type,
            permutations=permutations,
            w_options=w_options,
        )
    else:
        sm = transition_model
    if n_rows is None and n_cols is None:
        sqcols = int(np.ceil(np.sqrt(len(sm.classes) + 1)))
        n_cols = sqcols
        n_rows = sqcols
    _, axs = plt.subplots(n_rows, n_cols, figsize=figsize)
    axs = axs.flatten()

    ls = sm.classes
    lags_all = ["Modal Neighbor - " + str(l) for l in ls]

    sns.heatmap(
        sm.p,
        annot=True,
        linewidths=0.5,
        ax=axs[0],
        cbar=False,
        vmin=0,
        vmax=1,
        square=True,
        xticklabels=ls,
        yticklabels=ls,
    )
    axs[0].set_title("Global", fontsize=14)
    axs[0].tick_params(axis="x", which="minor", bottom=False)
    axs[0].tick_params(axis="y", which="minor", left=False)

    for i in range(len(sm.P)):

        # Loop over data dimensions and create text annotations.
        p_temp = sm.P[i]
        sns.heatmap(
            p_temp,
            annot=True,
            linewidths=0.5,
            ax=axs[i + 1],
            cbar=False,
            vmin=0,
            vmax=1,
            square=True,
            xticklabels=ls,
            yticklabels=ls,
        )

        axs[i + 1].set_title(lags_all[i], fontsize=14)
        axs[i + 1].tick_params(axis="x", which="minor", bottom=False)
        axs[i + 1].tick_params(axis="y", which="minor", left=False)

    # pop off any unused axes
    for i in range(len(axs)):
        if i > len(sm.P):
            axs[i].remove()

    if suptitle:
        plt.suptitle(suptitle, **title_kwds)
    plt.tight_layout()
    plt.subplots_adjust(top=0.89)

    if savefig:
        plt.savefig(savefig, dpi=dpi)

    return axs


def plot_transition_graphs(
    gdf,
    cluster_col=None,
    output_dir=".",
    w_type="queen",
    w_options=None,
    temporal_index="year",
    unit_index="geoid",
    permutations=0,
    layout="dot",
    args="-n -Groot=0 -Goverlap=false -Gnodesep=0.01 -Gfont_size=1 -Gmindist=3.5 -Gsize=30,30!",
    transition_model=None,
):
    """Plot a network graph representation of global and spatially-conditioned transition matrices.

       This function requires pygraphviz to be installed. For linux and macos, it can be installed with
       `conda install -c conda-forge pygraphviz`. At the time of this writing there is no pygraphviz build
       available for Windows from mainstream conda channels, but it can be installed with
       `conda install -c alubbock pygraphviz`

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        long-form geodataframe with a column holding labels appropriate
        for using as input to `geosnap.analyze.transition`
    cluster_col : str
        column on the gdf containing neighborhood type labels
    output_dir : str
        the location that output images will be placed
    temporal_index : string, optional
        Column defining time and or sequencing of the long-form data.
        Default is "year".
    unit_index : string, optional
        Column identifying the unique id of spatial units.
        Default is "geoid".
    w_type : string, optional
        Type of spatial weights type ("rook", "queen", "knn" or
        "kernel") to be used for spatial structure. Default is
        None, if non-spatial Markov transition rates are desired.
    w_options : dict
        additional options passed to a libpysal weights constructor (e.g. `k` for a KNN weights matrix)
    permutations : int, optional
        number of permutations for use in randomization based
        inference (the default is 0).
    layout : str, 'dot'
        graphviz layout for plotting
    args : str, optional
        additional arguments passed to graphviz.
        default is  "-n -Groot=0 -Goverlap=false -Gnodesep=0.01 -Gfont_size=1 -Gmindist=3.5 -Gsize=30,30!"

    Returns
    ------
    None
    """
    try:
        import pygraphviz
    except ImportError:
        raise ImportError("You must have pygraphviz installed to use graph plotting")
    if transition_model is None:
        warn(
            "Creating a transition model implicitly is deprecated and will be removed in future versions. "
            "please pass a giddy.Spatial_Markov instance created using `giddy` or `geosnap.analyze.transition`"
        )

        sm = transition(
            gdf,
            cluster_col=cluster_col,
            temporal_index=temporal_index,
            unit_index=unit_index,
            w_type=w_type,
            permutations=permutations,
            w_options=w_options,
        )
    else:
        sm = transition_model

    # plot the global transition matrix
    p = sm.p
    graph = np.round(p, 2)

    dt = [("weight", float)]
    A = np.array(graph, dtype=dt)
    G = nx.DiGraph(A)
    G.edges(data=True)
    labels = nx.get_edge_attributes(G, "weight")
    for u, v, d in G.edges(data=True):
        d["label"] = d.get("weight", "")
    A = nx.nx_agraph.to_agraph(G)
    A.layout(layout, args=args)  # use either circo or dot layout
    A.draw(os.path.join(output_dir, f"{cluster_col}_transitions_global.png"))

    # then plot each of the spatially-conditioned matrices
    for i, p in enumerate(sm.P):

        graph = np.round(p, 2)

        dt = [("weight", float)]
        A = np.array(graph, dtype=dt)
        G = nx.DiGraph(A)
        G.edges(data=True)
        labels = nx.get_edge_attributes(G, "weight")
        for u, v, d in G.edges(data=True):
            d["label"] = d.get("weight", "")

        A = nx.nx_agraph.to_agraph(G)
        A.layout(layout, args=args)  # use either circo or dot layout
        A.draw(os.path.join(output_dir, f"{cluster_col}_transitions_nb{i}.png"))
