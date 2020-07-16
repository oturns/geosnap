"""
Visualization method for time series plots.
"""

import proplot as plot
from os import path, mkdir

__all__ = ["tsplot"]

"""
Function for plotting timeseries data from community objects.

Parameters
----------
community    : community object
               community object
column       : str
               column to be graphed in a time series
title        : str, optional
               desired title of figure
years        : list, optional
               years to be graphed
               default is every year in dataframe.
scheme       : string,optional
               matplotlib scheme to be used
               default is 'quantiles'
k            : int, optional
               number of bins to graph.
               Default is 5.
save_fig     : boolean, optional
               whether to save figure. Default is False.
"""


def tsplot(community, column, title='',
           years=[], scheme='quantiles',
           k=5,save_fig=False, **kwargs):
    if not years:
        f, axs = plot.subplots(ncols=len(community.gdf.year.unique()))
        for i, year in enumerate(sorted(community.gdf.year.unique())):  # sort to prevent graphing out of order
            community.gdf[community.gdf.year == year].plot(column=column, ax=axs[i], scheme=scheme, k=k, **kwargs,
                                                           legend=True, legend_kwds={'ncols': 1, "loc": "b"})
            axs[i].format(title=year)
    else:
        f, axs = plot.subplots(ncols=len(years))
        for i, year in enumerate(years):  # display in whatever order list is passed in
            community.gdf[community.gdf.year == year].plot(column=column, ax=axs[i], scheme=scheme, k=k, **kwargs,
                                                           legend=True, legend_kwds={'ncols': 1, "loc": "b"})
            axs[i].format(title=year)
    if not title:  # only use title when passed
        axs.format(suptitle=column)
    else:
        axs.format(suptitle=title)
    axs.axis('off')

    if save_fig:
        dirName = "figures"
        if not path.exists(dirName):
            mkdir(dirName)
        f.savefig(dirName+"/tsplot_%s.png" % (column),
                    dpi=500, bbox_inches='tight')
