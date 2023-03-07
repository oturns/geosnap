"""Tools for describing and exploring cluster/class composition."""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


def plot_violins_by_cluster(
    df,
    columns,
    cluster_col,
    violin_kwargs=None,
    figsize=(12, 8),
    nrows=None,
    ncols=None,
    titles=None,
    savefig=None,
    dpi=200
):
    """Create matrix of violin plots categorized by a discrete class variable

    Parameters
    ----------
    df : pandas.DataFrame or geopandas.GeoDataFrame
        datafrme with columns to plot as violins and a colunn of class labels
    columns : list-like
        list of columns to plot as violins
    cluster_col : str
        name of the column in the dataframe that holds class labels
    violin_kwargs : dict, optional
        additional keyword arguments passed to seaborn.violinplot
    figsize : tuple, optional
        size of output figure, by default (12, 8)
    nrows : int, optional
        number of rows in the violin (nrows * ncols must equal len(columns)), by default None
    ncols : int, optional
        number of columns in the violin (nrows * ncols must equal len(columns)), by default None
        If both ncols and nrows are none, they will be set to the miminmum bounding square
    titles : list, optional
        list of titles to set on each subplot. If None (default) the title of each axes
        will be set to the name of the column being plotted
    savefig : str, optional
        If provided, the figure will be saved at this path
    dpi : int, optional
        dpi of resulting figure when using `savefig`, by default 200

    Returns
    -------
    matplotlib.axes.Axes
        a matplotlib Axes object with a subplot for each column
    """    
    if nrows is None and ncols is None:
        sqcols = int(np.ceil(np.sqrt(len(columns))))
        ncols = sqcols
        nrows = sqcols
    if violin_kwargs is None:
        violin_kwargs = dict()
    fig, ax = plt.subplots(nrows, ncols, figsize=figsize)
    ax = ax.flatten()
    for i, col in enumerate(columns):
        sns.violinplot(data=df, y=col, x=df[cluster_col], ax=ax[i], **violin_kwargs)
        if titles:
            ax[i].set_title(titles[i])
        else:
            ax[i].set_title(col)
    # pop off any unused axes
    for i in range(len(ax)):
        if i > len(columns):
            ax[i].remove()
    plt.tight_layout()
    if savefig:
        plt.savefig(savefig, dpi=dpi)
    return ax
