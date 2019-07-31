"""Tools for the spatial analysis of neighborhood change."""

import numpy as np
import pandas as pd
from libpysal.weights import attach_islands
from libpysal.weights.contiguity import Queen, Rook
from libpysal.weights.distance import KNN

from .cluster import (
    azp,
    affinity_propagation,
    gaussian_mixture,
    hdbscan,
    kmeans,
    max_p,
    skater,
    spectral,
    spenc,
    ward,
    ward_spatial,
)


def cluster(
    gdf,
    n_clusters=6,
    method=None,
    best_model=False,
    columns=None,
    verbose=False,
    **kwargs
):
    """Create a geodemographic typology by running a cluster analysis on the
       study area's neighborhood attributes

    Parameters
    ----------
    gdf : pandas.DataFrame
        long-form (geo)DataFrame containing neighborhood attributes
    n_clusters : int
        the number of clusters to model. The default is 6).
    method : str
        the clustering algorithm used to identify neighborhood types
    best_model : bool
        if using a gaussian mixture model, use BIC to choose the best
        n_clusters. (the default is False).
    columns : list-like
        subset of columns on which to apply the clustering
    verbose : bool
        whether to print warning messages (the default is False).
    **kwargs

    Returns
    -------
    pandas.DataFrame with a column of neighborhood cluster labels appended
    as a new column. Will overwrite columns of the same name.
    """
    assert columns, "You must provide a subset of columns as input"
    assert method, "You must choose a clustering algorithm to use"
    gdf = gdf.copy().reset_index()
    allcols = columns + ["year"]
    gdf = gdf.dropna(how="any", subset=columns)
    opset = gdf.copy()
    opset = opset[allcols]
    opset[columns] = opset.groupby("year")[columns].apply(
        lambda x: (x - x.mean()) / x.std(ddof=0)
    )
    # option to autoscale the data w/ mix-max or zscore?
    specification = {
        "ward": ward,
        "kmeans": kmeans,
        "affinity_propagation": affinity_propagation,
        "gaussian_mixture": gaussian_mixture,
        "spectral": spectral,
        "hdbscan": hdbscan,
    }
    model = specification[method](
        opset[columns],
        n_clusters=n_clusters,
        best_model=best_model,
        verbose=verbose,
        **kwargs
    )
    labels = model.labels_.astype(str)
    clusters = pd.DataFrame(
        {method: labels, "year": gdf.year.astype(str), "geoid": gdf.geoid}
    )
    clusters["key"] = clusters.geoid + clusters.year
    clusters = clusters.drop(columns="year")
    # geoid = gdf.index.copy()
    gdf["key"] = gdf.geoid + gdf.year.astype(str)
    gdf = gdf.merge(clusters.drop(columns=["geoid"]), on="key", how="left")
    gdf.drop(columns="key", inplace=True)
    gdf.set_index("geoid", inplace=True)
    return gdf


def cluster_spatial(
    gdf,
    n_clusters=6,
    weights_type="rook",
    method=None,
    best_model=False,
    columns=None,
    threshold_variable="count",
    threshold=10,
    **kwargs
):
    """Create a *spatial* geodemographic typology by running a cluster
    analysis on the metro area's neighborhood attributes and including a
    contiguity constraint.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        long-form geodataframe holding neighborhood attribute and geometry data.
    n_clusters : int
        the number of clusters to model. The default is 6).
    weights_type : str 'queen' or 'rook'
        spatial weights matrix specification` (the default is "rook").
    method : str
        the clustering algorithm used to identify neighborhood types
    best_model : type
        Description of parameter `best_model` (the default is False).
    columns : list-like
        subset of columns on which to apply the clustering
    threshold_variable : str
        for max-p, which variable should define `p`. The default is "count",
        which will grow regions until the threshold number of polygons have
        been aggregated
    threshold : numeric
        threshold to use for max-p clustering (the default is 10).
    **kwargs


    Returns
    -------
    geopandas.GeoDataFrame with a column of neighborhood cluster labels
    appended as a new column. Will overwrite columns of the same name.

    """
    assert columns, "You must provide a subset of columns as input"
    assert method, "You must choose a clustering algorithm to use"
    gdf = gdf.copy().reset_index()
    cols = ["year", "geoid", "geometry"]

    if threshold_variable == "count":
        allcols = columns + cols
        data = gdf[allcols].copy()
        data = data.dropna(how="any")
        data[columns] = data.groupby("year")[columns].apply(
            lambda x: (x - x.mean()) / x.std(ddof=0)
        )

    elif threshold_variable is not None:
        threshold_var = data[threshold_variable]
        allcols = list(columns).remove(threshold_variable) + cols
        data = gdf[allcols].copy()
        data = data.dropna(how="any")
        data[columns] = data.groupby("year")[columns].apply(
            lambda x: (x - x.mean()) / x.std(ddof=0)
        )

    else:
        allcols = columns + cols
        data = gdf[allcols].copy()
        data = data.dropna(how="any")
        data[columns] = data.groupby("year")[columns].apply(
            lambda x: (x - x.mean()) / x.std(ddof=0)
        )

    def _build_data(data, year, weights_type):
        df = data.loc[data.year == year].copy().dropna(how="any")
        weights = {"queen": Queen, "rook": Rook}
        w = weights[weights_type].from_dataframe(df, idVariable="geoid")
        knnw = KNN.from_dataframe(df, k=1, ids=df.geoid.tolist())

        return df, w, knnw

    years = [1980, 1990, 2000, 2010]
    annual = []
    for year in years:
        df, w, knnw = _build_data(data, year, weights_type)
        annual.append([df, w, knnw])

    datasets = dict(zip(years, annual))

    specification = {
        "azp": azp,
        "spenc": spenc,
        "ward_spatial": ward_spatial,
        "skater": skater,
        "max_p": max_p,
    }

    clusters = []
    for _, val in datasets.items():
        if threshold_variable == "count":
            threshold_var = np.ones(len(val[0]))
            val[1] = attach_islands(val[1], val[2])

        elif threshold_variable:
            threshold_var = threshold_var[threshold.index.isin(val[0].geoid)].values
            try:
                val[1] = attach_islands(val[1], val[2])
            except:
                pass
        else:
            threshold_var = None
        model = specification[method](
            val[0][columns],
            w=val[1],
            n_clusters=n_clusters,
            threshold_variable=threshold_var,
            threshold=threshold,
            **kwargs
        )
        labels = model.labels_.astype(str)
        labels = pd.DataFrame(
            {method: labels, "year": val[0].year, "geoid": val[0].geoid}
        )
        clusters.append(labels)

    clusters = pd.concat(clusters)
    clusters.set_index("geoid")
    clusters["joinkey"] = clusters.geoid + clusters.year.astype(str)
    clusters = clusters.drop(columns="year")
    gdf["joinkey"] = gdf.geoid + gdf.year.astype(str)
    if method in gdf.columns:
        gdf.drop(columns=method, inplace=True)
    gdf = gdf.merge(clusters.drop(columns=["geoid"]), on="joinkey", how="left")
    gdf.set_index("geoid", inplace=True)

    return gdf
