"""plotting for spatial Markov transition matrices."""

import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.pyplot import savefig


def plot_transitions(
    community,
    cluster_col,
    w_type,
    w_options,
    figsize=(13, 12),
    n_rows=3,
    n_cols=3,
    suptitle=None,
    title_kwds=None,
    savefig=None,
    dpi=300,
    **kwargs
):
    if not n_rows and not n_cols:
        n_cols = len(community.gdf[cluster_col].unique()) + 1
        n_rows = 1
    if not title_kwds:
        title_kwds = {"fontsize": 20, }
    sm = community.transition(cluster_col=cluster_col, w_type=w_type)
    fig, axs = plt.subplots(n_rows, n_cols, figsize=figsize)
    ls = sm.classes
    lags_all = ["Modal Neighbor - " + str(l) for l in ls]
    axs = axs.flatten()
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
        **kwargs
    )
    axs[0].set_title("Global", fontsize=14)

    for i in range(len(sm.P)):

        # Loop over data dimensions and create text annotations.
        p_temp = sm.P[i]
        im = sns.heatmap(
            p_temp,
            annot=True,
            linewidths=0.5,
            ax=axs[i + 1],
            cbar=False,
            vmin=0,
            vmax=1,
            square=True,
            **kwargs
        )

        axs[i + 1].set_title(lags_all[i], fontsize=14)

    # pop off any unused axes
    for i in range(len(axs)):
        if i > len(sm.P):
            axs[i].remove()

    if suptitle:
        plt.suptitle(suptitle, **title_kwds)
    plt.tight_layout()
    plt.subplots_adjust(top=.89)
    plt.minorticks_off()

    if savefig:
        plt.savefig(savefig, dpi=dpi)

    return axs
