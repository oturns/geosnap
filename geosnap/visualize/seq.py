"""
Visualization methods for neighborhood sequences.
"""

__author__ = "Wei Kang <weikang9009@gmail.com>"

__all__ = ["indexplot_seq"]

import copy

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import ListedColormap


def indexplot_seq(
    df_traj,
    clustering,
    years=["1970", "1980", "1990", "2000", "2010"],
    k=None,
    ncols=3,
    palette="Set1",
    save_fig=None,
    dpi=500,
):
    """
    Function for index plot of neighborhood sequences within each cluster.

    Parameters
    ----------
    df_traj      : dataframe
                   dataframe of trajectories
    clustering   : str
                   column name of the sequence clustering to plot.
    years        : list, optional
                   column names of cross sections of the neighborhood
                   classifications. Default is decennial census years 1970-2010.
    k            : int, optional
                   Number of neighborhood types. If None, k is obtained
                   by inspecting unique values in "years".
                   Default is None.
    ncols        : int, optional
                   number of subplots per row. Default is 3.
    palette      : None, string, or sequence, optional
                   Name of palette or None to return current palette.
                   If a sequence, input colors are used but possibly
                   cycled and desaturated. Default is "Set1".
    save_fig     : str, optional
                   path to save figure if desired
    dpi          : int, optional
                   the dpi of the saved figure. Deafult is 500

    Examples
    --------
    >>> import pandas as pd
    >>> from geosnap.visualize import indexplot_seq
    >>> import matplotlib.pyplot as plt
    >>> df_LA = pd.read_csv("../../examples/data/LA_sequences.csv", converters={'GEO2010': lambda x: str(x)})
    >>> indexplot_seq(df_LA, clustering="seqC1", palette="pastel", ncols=3)
    >>> plt.show()
    """

    df_traj.columns = df_traj.columns
    years = list(np.array(years))
    n_years = len(years)
    if k is None:
        k = len(np.unique(df_traj[years].values))

    neighborhood = np.sort(np.unique(df_traj[years].values))
    traj_label = np.sort(df_traj[clustering].unique())
    m = len(traj_label)
    nrows = int(np.ceil(m / ncols))

    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(15, 5 * nrows))
    # years_all = list(map(str, range(1970, 2020, 10)))

    traj = df_traj[years + [clustering]]
    size_traj_clusters = traj.groupby(clustering).size()
    max_cluster = size_traj_clusters.max()
    dtype = list(zip(years, [int] * n_years))
    color_cluster = sns.color_palette(palette, n_colors=k)
    color = copy.copy(color_cluster)
    color.append((1, 1, 1))
    cluster_cmap = ListedColormap(color_cluster)
    my_cmap = ListedColormap(color)

    for p in range(nrows):
        for q in range(ncols):
            ax = axes[q] if nrows == 1 else axes[p, q]
            i = p * ncols + q
            if i >= m:
                ax.set_axis_off()
                continue
            ax.set_title(
                "Neighborhood Sequence Cluster " + str(traj_label[i]), fontsize=15
            )
            cluster_i = traj[traj[clustering] == traj_label[i]][years].values
            cluster_i_temp = np.array(list(map(tuple, cluster_i)), dtype=dtype)
            cluster_i_temp_sort = np.sort(cluster_i_temp, order=years)
            cluster_i_temp_sort = np.array(list(map(list, cluster_i_temp_sort)))
            if not cluster_i_temp_sort.shape[0]:
                ax.set_axis_off()
                continue
            elif cluster_i_temp_sort.shape[0] < max_cluster:
                diff_n = max_cluster - cluster_i_temp_sort.shape[0]
                bigger = np.unique(cluster_i_temp_sort).max() + 1
                cluster_i_temp_sort = np.append(
                    cluster_i_temp_sort,
                    np.zeros((diff_n, cluster_i_temp_sort.shape[1])) + bigger,
                    axis=0,
                )
            df_cluster_i_temp_sort = pd.DataFrame(cluster_i_temp_sort, columns=years)

            if cluster_i_temp.shape[0] == max_cluster:
                cbar_ax = fig.add_axes([0.3, -0.02, 0.42, 0.02])
                ax = sns.heatmap(
                    df_cluster_i_temp_sort,
                    ax=ax,
                    cmap=cluster_cmap,
                    cbar_kws={"orientation": "horizontal"},
                    cbar_ax=cbar_ax,
                )
                colorbar = ax.collections[0].colorbar
                colorbar.set_ticks(
                    np.linspace(min(neighborhood) + 0.5, max(neighborhood) - 0.5, k)
                )
                colorbar.set_ticklabels(neighborhood)
            else:
                ax = sns.heatmap(
                    df_cluster_i_temp_sort, ax=ax, cmap=my_cmap, cbar=False
                )

    plt.tight_layout()
    # fig.tight_layout(rect=[0, 0, .9, 1])
    if save_fig:
        fig.savefig(save_fig, dpi=dpi, bbox_inches="tight")
