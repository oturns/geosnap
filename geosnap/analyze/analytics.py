"""Tools for the spatial analysis of neighborhood change."""

import numpy as np
import pandas as pd
from libpysal.weights import attach_islands
from libpysal.weights.contiguity import Queen, Rook
from libpysal.weights.distance import KNN
from sklearn.preprocessing import StandardScaler

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
    time_var="year",
    id_var="geoid",
    return_model=False,
    scaler=None,
    **kwargs,
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
    time_var: str
        which column on the dataframe defines time and or sequencing of the
        long-form data. Default is "year"
    id_var: str
        which column on the long-form dataframe identifies the stable units
        over time. In a wide-form dataset, this would be the unique index
    scaler: str or sklearn.preprocessing.Scaler
        a scikit-learn preprocessing class that will be used to rescale the
        data. Defaults to StandardScaler

    Returns
    -------
    pandas.DataFrame with a column of neighborhood cluster labels appended
    as a new column. Will overwrite columns of the same name.
    """
    if not columns:
        raise ValueError("You must provide a subset of columns as input")
    if not method:
        raise ValueError("You must choose a clustering algorithm to use")

    times = gdf[time_var].unique()
    gdf = gdf.set_index([time_var, id_var])

    # this is the dataset we'll operate on
    data = gdf.copy()[columns]
    data = data.dropna(how="any", subset=columns)

    # if the user doesn't specify, use the standard scalar
    if not scaler:
        scaler = StandardScaler()
    for time in times:
        data.loc[time] = scaler.fit_transform(data.loc[time].values)
    # the rescalar can create nans if a column has no variance, so fill with 0
    data = data.fillna(0)

    specification = {
        "ward": ward,
        "kmeans": kmeans,
        "affinity_propagation": affinity_propagation,
        "gaussian_mixture": gaussian_mixture,
        "spectral": spectral,
        "hdbscan": hdbscan,
    }

    # run the cluster model then join the labels back to the original data
    model = specification[method](
        data, n_clusters=n_clusters, best_model=best_model, verbose=verbose, **kwargs
    )
    labels = model.labels_.astype(str)
    data = data.reset_index()
    clusters = pd.DataFrame(
        {method: labels, time_var: data[time_var], id_var: data[id_var]}
    )
    clusters.set_index([time_var, id_var], inplace=True)
    gdf = gdf.join(clusters, how="left")
    gdf = gdf.reset_index()
    if return_model:
        return gdf, model
    return gdf


def cluster_spatial(
    gdf,
    n_clusters=6,
    spatial_weights="rook",
    method=None,
    columns=None,
    threshold_variable="count",
    threshold=10,
    time_var="year",
    id_var="geoid",
    return_model=False,
    scaler=None,
    **kwargs,
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
    columns : list-like
        subset of columns on which to apply the clustering
    threshold_variable : str
        for max-p, which variable should define `p`. The default is "count",
        which will grow regions until the threshold number of polygons have
        been aggregated
    threshold : numeric
        threshold to use for max-p clustering (the default is 10).
    time_var: str
        which column on the dataframe defines time and or sequencing of the
        long-form data. Default is "year"
    id_var: str
        which column on the long-form dataframe identifies the stable units
        over time. In a wide-form dataset, this would be the unique index
    scaler: str or sklearn.preprocessing.Scaler
        a scikit-learn preprocessing class that will be used to rescale the
        data. Defaults to StandardScaler

    Returns
    -------
    geopandas.GeoDataFrame with a column of neighborhood cluster labels
    appended as a new column. Will overwrite columns of the same name.

    """
    if not columns:
        raise ValueError("You must provide a subset of columns as input")
    if not method:
        raise ValueError("You must choose a clustering algorithm to use")

    times = gdf[time_var].unique()
    gdf = gdf.set_index([time_var, id_var])

    # this is the dataset we'll operate on
    data = gdf.copy()[columns + ["geometry"]]

    contiguity_weights = {"queen": Queen, "rook": Rook}

    if spatial_weights in contiguity_weights.keys():
        W = contiguity_weights[spatial_weights]
    else:
        W = spatial_weights

    specification = {
        "azp": azp,
        "spenc": spenc,
        "ward_spatial": ward_spatial,
        "skater": skater,
        "max_p": max_p,
    }

    # if the user doesn't specify, use the standard scalar
    if not scaler:
        scaler = StandardScaler()

    ws = {}
    clusters = []
    dfs = []
    # loop over each time period, standardize the data and build a weights matrix
    for time in times:
        df = data.loc[time].dropna(how="any", subset=columns).reset_index()
        df[time_var] = time
        df[columns] = scaler.fit_transform(df[columns].values)
        w0 = W.from_dataframe(df)
        w1 = KNN.from_dataframe(df, k=1)
        ws = [w0, w1]
        # the rescalar can create nans if a column has no variance, so fill with 0
        df = df.fillna(0)

        if threshold_variable and threshold_variable != "count":
            data[threshold_variable] = gdf[threshold_variable]
            threshold_var = data.threshold_variable.values
            ws[0] = attach_islands(ws[0], ws[1])

        elif threshold_variable == "count":
            threshold_var = np.ones(len(data.loc[time]))
            ws[0] = attach_islands(ws[0], ws[1])

        else:
            threshold_var = None

        model = specification[method](
            df[columns],
            w=ws[0],
            n_clusters=n_clusters,
            threshold_variable=threshold_var,
            threshold=threshold,
            **kwargs,
        )

        labels = model.labels_.astype(str)
        clusters = pd.DataFrame(
            {method: labels, time_var: df[time_var], id_var: df[id_var]}
        )
        clusters.set_index([time_var, id_var], inplace=True)
        dfs.append(gdf.loc[time].join(clusters, how="left"))
    gdf = pd.concat(dfs).reset_index()
    if return_model:
        return gdf, model
    return gdf
