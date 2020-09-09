"""plotting for spatial Markov transition matrices."""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import networkx as nx


def plot_transition_matrix(
    community,
    cluster_col=None,
    w_type="queen",
    w_options=None,
    figsize=(13, 12),
    n_rows=3,
    n_cols=3,
    suptitle=None,
    title_kwds=None,
    savefig=None,
    dpi=300,
    **kwargs,
):
    """Plot global and spatially-conditioned transition matrices as heatmaps.

     Parameters
     ----------
     community : geosnap.Community
         a geosnap Community instance
     cluster_col : str
         column on the Community.gdf containing neighborhood type labels
     w_type : str {'queen', 'rook'}
         which type of libpysal spatial weights objects to encode connectivity
     w_options : dict
         additional options passed to a libpysal weights constructor (e.g. `k` for a KNN weights matrix)
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
    if not n_rows and not n_cols:
        n_cols = len(community.gdf[cluster_col].unique()) + 1
        n_rows = 1
    if not title_kwds:
        title_kwds = {
            "fontsize": 20,
        }

    sm = community.transition(cluster_col=cluster_col, w_type=w_type)

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
        **kwargs,
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
            **kwargs,
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
    community,
    cluster_col=None,
    output_dir=".",
    w_type="queen",
    layout="dot",
    args="-n -Groot=0 -Goverlap=false -Gnodesep=0.01 -Gfont_size=1 -Gmindist=3.5 -Gsize=30,30!",
):
    """Plot a network graph representation of global and spatially-conditioned transition matrices.

       This function requires pygraphviz to be installed. For linux and macos, it can be installed with
       `conda install -c conda-forge pygraphviz`. At the time of this writing there is no pygraphviz build
       available for Windows from mainstream conda channels, but it can be installed with
       `conda install -c alubbock pygraphviz`

    Parameters
    ----------
    community : geosnap.Community
        a geosnap Community instance
    cluster_col : str
        column on the Community.gdf containing neighborhood type labels
    output_dir : str
        the location that output images will be placed
    w_type : str {'queen', 'rook'}
        which type of libpysal spatial weights objects to encode connectivity
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
    sm = community.transition(cluster_col=cluster_col, w_type=w_type)

    # plot the global transition matrix
    p = sm.p
    graph = np.round(p, 2)

    dt = [("weight", float)]
    A = np.matrix(graph, dtype=dt)
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
        A = np.matrix(graph, dtype=dt)
        G = nx.DiGraph(A)
        G.edges(data=True)
        labels = nx.get_edge_attributes(G, "weight")
        for u, v, d in G.edges(data=True):
            d["label"] = d.get("weight", "")

        A = nx.nx_agraph.to_agraph(G)
        A.layout(layout, args=args)  # use either circo or dot layout
        A.draw(os.path.join(output_dir, f"{cluster_col}_transitions_nb{i}.png"))
