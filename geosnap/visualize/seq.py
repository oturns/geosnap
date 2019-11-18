"""
Visualization methods for neighborhood sequences.
"""

__author__ = "Wei Kang <weikang9009@gmail.com>"

__all__ = ["indexplot_seq"]

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import seaborn as sns
import copy
from os import path, mkdir
import pandas as pd

def indexplot_seq(df_traj, clustering,
                  years=["1970", "1980", "1990", "2000", "2010"],
                  k=None, ncols=3, palette= "Set1",
                  save_fig=False, fig_suffix="LA",
                  neighborhood_types=None, separate=True):
    """
    Function for index plot of neighborhood sequences within each cluster.

    Arguments
    ---------
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
    save_fig     : boolean, optional
                   whether to save figure. Default is False.
    fig_suffix   : str, optional
                   suffix of the saved figure name. Default is "LA".

    Examples
    --------
    >>> import pandas as pd
    >>> from geosnap.visualize import indexplot_seq
    >>> import matplotlib.pyplot as plt
    >>> df_LA = pd.read_csv("../../examples/data/LA_sequences.csv", converters={'GEO2010': lambda x: str(x)})
    >>> indexplot_seq(df_LA, clustering="seqC1", palette="pastel", ncols=3)
    >>> plt.show()
    """

    df_traj.columns = df_traj.columns.astype(str)
    years = list(np.array(years).astype(str))
    n_years = len(years)
    neighbor_unique = np.unique(df_traj[years].values)
    if k is None:
        k = len(neighbor_unique)

    neighborhood = np.sort(np.unique(df_traj[years].values))
    traj_label = np.sort(df_traj[clustering].unique())
    m = len(traj_label)
    nrows = int(np.ceil(m / ncols))

    if not separate:
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(15, 5 * nrows))
    # years_all = list(map(str, range(1970, 2020, 10)))

    traj = df_traj[years + [clustering]]
    N = len(traj)
    size_traj_clusters = traj.groupby(clustering).size()
    max_cluster = size_traj_clusters.max()
    dtype = list(zip(years, [int] * n_years))
    color_cluster = sns.color_palette(palette, n_colors=k)
    cluster_cmap = ListedColormap(color_cluster)

    for p in range(nrows):
        for q in range(ncols):
            i = p * ncols + q
            if separate:
                if i >= m:
                    continue
                else:
                    fig, ax = plt.subplots(nrows=1, ncols=1)
            else:
                if nrows == 1:
                    ax = axes[q]
                else:
                    ax = axes[p, q]
                if i >= m:
                    ax.set_axis_off()
                    continue
                ax.set_title("Neighborhood Sequence Cluster " + str(traj_label[i]),
                             fontsize=15)
            cluster_i = traj[traj[clustering] == traj_label[i]][years].values
            n = len(cluster_i)

            cluster_i_temp = np.array(list(map(tuple, cluster_i)), dtype=dtype)
            cluster_i_temp_sort = np.sort(cluster_i_temp, order=years)
            cluster_i_temp_sort = np.array(list(map(list, cluster_i_temp_sort)))
            if not cluster_i_temp_sort.shape[0]:
                ax.set_axis_off()
                continue
            elif cluster_i_temp_sort.shape[0] < max_cluster:
                if not separate:
                    diff_n = max_cluster - cluster_i_temp_sort.shape[0]
                    cluster_i_temp_sort = np.append(cluster_i_temp_sort, np.zeros(
                        (diff_n, cluster_i_temp_sort.shape[1]))+ cluster_i.min()-1, axis=0)
            df_cluster_i_temp_sort = pd.DataFrame(cluster_i_temp_sort,
                                                  columns=years)

            if separate:
                dict_index = dict(zip(np.unique(cluster_i_temp_sort), range(len(np.unique(cluster_i_temp_sort)))))
                cluster_i_temp_sort_index = []
                for row_i in cluster_i_temp_sort:
                    temp = []
                    for j in row_i:
                        temp.append(dict_index[j])
                    cluster_i_temp_sort_index.append(temp)
                df_cluster_i_temp_sort[years] = np.array(cluster_i_temp_sort_index)
                temp_values = np.unique(cluster_i)
                color = []
                neighbor_temp = []
                for v in temp_values:
                    index = np.argwhere(neighbor_unique == v)[0][0]
                    color.append(color_cluster[index])
                    neighbor_temp.append(neighborhood_types[index])

                ax = sns.heatmap(df_cluster_i_temp_sort, ax=ax, cmap=ListedColormap(color),
                                 yticklabels=False)
                colorbar = ax.collections[0].colorbar
                r = colorbar.vmax - colorbar.vmin
                colorbar.set_ticks([colorbar.vmin + r / len(temp_values) * (0.5 + tv)
                                    for tv in range(len(temp_values))])
                # colorbar.set_ticks(np.linspace(min(neighborhood) + 0.5, max(neighborhood) - 0.5, k))
                colorbar.set_ticklabels(neighbor_temp)
                ax.set_ylabel("n=%d("%n + "{:.0%}".format(n/N)+")")

                if save_fig:
                    dirName = "figures/%s"%clustering
                    if not path.exists(dirName):
                        mkdir(dirName)
                    fig.savefig(dirName + "/%s.png" % traj_label[i],
                                dpi=500, bbox_inches='tight')
            else:
                if cluster_i_temp.shape[0] == max_cluster:
                    cbar_ax = fig.add_axes([0.3, -0.02, 0.42, 0.02])
                    ax = sns.heatmap(df_cluster_i_temp_sort, ax=ax, cmap=cluster_cmap,
                                 cbar_kws={"orientation": "horizontal"},
                                 cbar_ax=cbar_ax)
                    colorbar = ax.collections[0].colorbar
                    colorbar.set_ticks(np.linspace(min(neighborhood) + 0.5, max(neighborhood) - 0.5, k))
                    colorbar.set_ticklabels(neighborhood)
                else:
                    dict_index = dict(zip(np.unique(cluster_i_temp_sort), range(len(np.unique(cluster_i_temp_sort)))))
                    cluster_i_temp_sort_index = []
                    for i in cluster_i_temp_sort:
                        temp = []
                        for j in i:
                            temp.append(dict_index[j])
                        cluster_i_temp_sort_index.append(temp)
                    df_cluster_i_temp_sort[years] = np.array(cluster_i_temp_sort_index)
                    temp_values = np.unique(cluster_i)
                    color = [(1, 1, 1)]
                    for i in temp_values:
                        color.append(color_cluster[np.argwhere(neighbor_unique == i)[0][0]])
                    sns.heatmap(df_cluster_i_temp_sort, ax=ax, cmap=ListedColormap(color),
                                cbar=False)

    # plt.tight_layout()
    if not separate:
        if save_fig:
            dirName = "figures"
            if not path.exists(dirName):
                mkdir(dirName)
            fig.savefig(dirName+"/%s_%s.png" % (clustering,fig_suffix),
                        dpi=500, bbox_inches='tight')
