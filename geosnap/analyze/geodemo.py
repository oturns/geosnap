"""Functions for clustering and regionalization with spatiotemporal data"""

import geopandas as gpd
import numpy as np
import pandas as pd
from libpysal.weights.contiguity import Queen, Rook, Voronoi
from libpysal.weights.distance import KNN, DistanceBand
from sklearn.preprocessing import StandardScaler
from spopt.region.base import form_single_component
from tqdm.auto import tqdm

from .._data import _Map
from ._cluster_wrappers import (
    affinity_propagation,
    gaussian_mixture,
    hdbscan,
    kmeans,
    spectral,
    ward,
)
from ._model_results import ModelResults
from ._region_wrappers import azp, kmeans_spatial, max_p, skater, spenc, ward_spatial

np.seterr(divide="ignore", invalid="ignore")

Ws = {
    "queen": Queen,
    "rook": Rook,
    "voronoi": Voronoi,
    "knn": KNN,
    "distanceband": DistanceBand,
}


def cluster(
    gdf,
    n_clusters=6,
    method=None,
    best_model=False,
    columns=None,
    verbose=False,
    temporal_index="year",
    unit_index="geoid",
    scaler="std",
    pooling="fixed",
    random_state=None,
    cluster_kwargs=None,
    model_colname=None,
    return_model=False,
):
    """Create a geodemographic typology by running a cluster analysis on the study area's neighborhood attributes.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame, required
        long-form GeoDataFrame containing neighborhood attributes
    n_clusters : int, required
        the number of clusters to model. The default is 6).
    method : str in ['kmeans', 'ward', 'affinity_propagation', 'spectral','gaussian_mixture', 'hdbscan'], required
        the clustering algorithm used to identify neighborhood types
    best_model : bool, optional
        if using a gaussian mixture model, use BIC to choose the best
        n_clusters. (the default is False).
    columns : list-like, required
        subset of columns on which to apply the clustering
    verbose : bool, optional
        whether to print warning messages (the default is False).
    temporal_index : str, required
        which column on the dataframe defines time and or sequencing of the
        long-form data. Default is "year"
    unit_index : str, required
        which column on the long-form dataframe identifies the stable units
        over time. In a wide-form dataset, this would be the unique index
    scaler : None or scaler from sklearn.preprocessing, optional
        a scikit-learn preprocessing class that will be used to rescale the
        data. Defaults to sklearn.preprocessing.StandardScaler
    pooling : ["fixed", "pooled", "unique"], optional (default='fixed')
        How to treat temporal data when applying scaling. Options include:

        * fixed : scaling is fixed to each time period
        * pooled : data are pooled across all time periods
        * unique : if scaling, apply the scaler to each time period, then generate
          clusters unique to each time period.
    cluster_kwargs: dict
        additional keyword arguments passed to the clustering instance
    model_colname : str
        column name for storing cluster labels on the output dataframe. If no name is provided,
        the colun will be named after the clustering method. If there is already a column
        named after the clustering method, the name will be incremented with a number
    return_model: bool
        if True, return the clustering model for further inspection (default is False)

    Returns
    -------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame with a column (model_colname) of neighborhood cluster labels
        appended as a new column. If model_colname exists as a column on the DataFrame
        then the column will be incremented.

    model : named tuple
        A tuple with attributes X, columns, labels, instance, W, which store the
        input matrix, column labels, fitted model instance, and spatial weights matrix

    """
    assert temporal_index in gdf.columns, (
        "The column given as temporal_index:, "
        f"{temporal_index} was not found in the geodataframe. ",
        "If you need only a single time period, you can create a dummy "
        "column with `gdf['_time'])=1` and pass `_time` as temporal_index",
    )

    assert unit_index in gdf.columns, (
        "The column given as unit_index: "
        f"({unit_index}) was not found in the geodataframe. ",
        "If you need only a single time period, you can pass " "`unit_index=gdf.index`",
    )
    if not cluster_kwargs:
        cluster_kwargs = dict()

    specification = {
        "ward": ward,
        "kmeans": kmeans,
        "affinity_propagation": affinity_propagation,
        "gaussian_mixture": gaussian_mixture,
        "spectral": spectral,
        "hdbscan": hdbscan,
    }

    if scaler == "std":
        scaler = StandardScaler()

    if method not in specification:
        raise ValueError(
            "`method` must of one of ['kmeans', 'ward', 'affinity_propagation', 'spectral', 'gaussian_mixture', 'hdbscan']"
        )
    if model_colname is None:
        # if we already have a column named after the clustering method, then increment it.
        if method in gdf.columns.tolist():
            model_colname = method + str(
                len(gdf.columns[gdf.columns.str.startswith(method)])
            )
        else:
            model_colname = method

    if not columns:
        raise ValueError("You must provide a subset of columns as input")

    gdf = gdf.copy()

    times = gdf[temporal_index].unique()
    gdf = gdf.set_index([temporal_index, unit_index])

    # this is the dataset we'll operate on
    data = gdf.copy()[columns]
    data = data.dropna(how="any", subset=columns)

    if scaler:
        if pooling in ["fixed", "unique"]:
            # if fixed (or unique), scale within each time period
            for time in times:
                data.loc[time] = scaler.fit_transform(data.loc[time].values)

        elif pooling == "pooled":
            # if pooled, scale the whole series at once
            data.loc[:, columns] = scaler.fit_transform(data.values)

    # the rescalar can create nans if a column has no variance, so fill with 0
    data = data.fillna(0)

    if pooling != "unique":

        # run the cluster model then join the labels back to the original data
        model = specification[method](
            data,
            n_clusters=n_clusters,
            best_model=best_model,
            verbose=verbose,
            random_state=random_state,
            **cluster_kwargs,
        )
        labels = model.labels_
        data = data.reset_index()
        clusters = pd.DataFrame(
            {
                model_colname: labels,
                temporal_index: data[temporal_index],
                unit_index: data[unit_index],
            }
        )
        clusters.set_index([temporal_index, unit_index], inplace=True)
        clusters = clusters[~clusters.index.duplicated(keep="first")]
        gdf = gdf.join(clusters, how="left")
        gdf = gdf.reset_index()
        model_data = gdf[
            columns + [temporal_index, unit_index, model_colname, gdf.geometry.name]
        ].dropna()
        results = ModelResults(
            df=model_data,
            columns=columns,
            labels=model.labels_,
            instance=model,
            W=None,
            name=model_colname,
            temporal_index=temporal_index,
            unit_index=unit_index,
            scaler=scaler,
            pooling=pooling,
        )
        if return_model:
            return gdf, results
        return gdf

    elif pooling == "unique":
        models = _Map()
        data = data.reset_index()
        gdf[model_colname] = np.nan

        for time in times:
            df = data.query(f"{temporal_index}=={time}").reset_index(drop=True)

            model = specification[method](
                df[columns],
                n_clusters=n_clusters,
                best_model=best_model,
                verbose=verbose,
                **cluster_kwargs,
            )

            labels = pd.Series(model.labels_, name=model_colname)
            clusters = pd.DataFrame(
                {
                    model_colname: labels,
                    temporal_index: df[temporal_index],
                    unit_index: df[unit_index],
                }
            )
            clusters = clusters.drop_duplicates(subset=[unit_index])
            clusters.set_index([temporal_index, unit_index], inplace=True)
            gdf.update(clusters)
            clusters = gpd.GeoDataFrame(
                clusters.join(gdf.drop(columns=[model_colname]), how="left"),
                crs=gdf.crs,
            ).reset_index()
            results = ModelResults(
                df=clusters,
                columns=columns,
                labels=model.labels_,
                instance=model,
                W=None,
                name=model_colname,
                temporal_index=temporal_index,
                unit_index=unit_index,
                scaler=scaler,
                pooling=pooling,
            )
            models[time] = results
        if return_model:
            return gdf.reset_index(), models
        return gdf.reset_index()


def regionalize(
    gdf,
    n_clusters=6,
    spatial_weights="rook",
    method=None,
    columns=None,
    threshold_variable="count",
    threshold=10,
    temporal_index="year",
    unit_index="geoid",
    scaler="std",
    weights_kwargs=None,
    region_kwargs=None,
    model_colname=None,
    return_model=False,
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
    spatial_weights : ['queen', 'rook'] or libpysal.weights.W object
        spatial weights matrix specification`. By default, geosnap will calculate Rook
        weights, but you can also pass a libpysal.weights.W object for more control
        over the specification.
    method : str in ['ward_spatial', 'kmeans_spatial', 'spenc', 'skater', 'azp', 'max_p']
        the clustering algorithm used to identify neighborhood types
    columns : array-like
        subset of columns on which to apply the clustering
    threshold_variable : str
        for max-p, which variable should define `p`. The default is "count",
        which will grow regions until the threshold number of polygons have
        been aggregated
    threshold : numeric
        threshold to use for max-p clustering (the default is 10).
    temporal_index : str
        which column on the dataframe defines time and or sequencing of the
        long-form data. Default is "year"
    unit_index : str
        which column on the long-form dataframe identifies the stable units
        over time. In a wide-form dataset, this would be the unique index
    weights_kwargs : dict
        If passing a libpysal.weights.W instance to spatial_weights, these additional
        keyword arguments that will be passed to the weights constructor
    region_kwargs: dict
        additional keyword arguments passed to the regionalization algorithm
    scaler : None or scaler class from sklearn.preprocessing
        a scikit-learn preprocessing class that will be used to rescale the
        data. Defaults to sklearn.preprocessing.StandardScaler
    model_colname : str
        column name for storing cluster labels on the output dataframe. If no name is provided,
        the colun will be named after the clustering method. If there is already a column
        named after the clustering method, the name will be incremented with a number
    return_model: bool
        If True, also retun a dictional of fitted classes from the regionalization provider

    Returns
    -------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame with a column of neighborhood cluster labels
        appended as a new column. If cluster method exists as a column on the DataFrame
        then the column will be incremented.

    models : dict of named tuples (only returned if `return_model` is True)
        tab-completable dictionary of named tuples keyed on the Community's time variable
        (e.g. year). The tuples store model results and have attributes X, columns, labels,
        instance, W, which store the input matrix, column labels, fitted model instance,
        and spatial weights matrix

    """
    assert temporal_index in gdf.columns, (
        "The column given as temporal_index:, "
        f"{temporal_index} was not found in the geodataframe. ",
        "If you need only a single time period, you can create a dummy "
        "column with `gdf['_time'])=1` and pass `_time` as temporal_index",
    )

    assert unit_index in gdf.columns, (
        "The column given as unit_index:, "
        f"{unit_index} was not found in the geodataframe. ",
        "If you need only a single time period, you can pass " "`unit_index=gdf.index`",
    )
    if not region_kwargs:
        region_kwargs = dict()

    specification = {
        "azp": azp,
        "spenc": spenc,
        "ward_spatial": ward_spatial,
        "skater": skater,
        "max_p": max_p,
        "kmeans_spatial": kmeans_spatial,
    }

    if method not in specification:
        raise ValueError(f"`method` must be one of {specification.keys()}")
    if model_colname is None:
        if method in gdf.columns.tolist():
            model_colname = method + str(
                len(gdf.columns[gdf.columns.str.startswith(method)])
            )
        else:
            model_colname = method
    else:
        model_colname = method
    if not columns:
        raise ValueError("You must provide a subset of columns as input")
    if not method:
        raise ValueError("You must choose a clustering algorithm to use")
    if scaler == "std":
        scaler = StandardScaler()
    if not weights_kwargs:
        weights_kwargs = {}
    gdf = gdf.copy()
    times = gdf[temporal_index].unique()
    gdf = gdf.set_index([temporal_index, unit_index])

    # this is the dataset we'll operate on
    allcols = columns + ["geometry"]
    if threshold_variable != "count":
        allcols = allcols + [threshold_variable]
    data = gdf.copy()[allcols]

    contiguity_weights = {"queen": Queen, "rook": Rook}

    W = contiguity_weights.get(spatial_weights, spatial_weights)

    models = _Map()
    clusters = []
    gdf[model_colname] = np.nan

    # loop over each time period, standardize the data and build a weights matrix
    for time in times:
        df = data.loc[time].dropna(how="any", subset=columns).reset_index()
        df[temporal_index] = time

        if scaler:
            df[columns] = scaler.fit_transform(df[columns].values)

        w0 = W.from_dataframe(df, **weights_kwargs)
        w0 = form_single_component(df, w0, linkage="single")

        model = specification[method](
            df,
            columns=columns,
            w=w0,
            n_clusters=n_clusters,
            threshold_variable=threshold_variable,
            threshold=threshold,
            **region_kwargs,
        )

        labels = pd.Series(model.labels_)
        clusters = pd.DataFrame(
            {
                model_colname: labels,
                temporal_index: df[temporal_index],
                unit_index: df[unit_index],
            }
        )
        clusters = clusters.drop_duplicates(subset=[unit_index])
        clusters.set_index([temporal_index, unit_index], inplace=True)
        gdf.update(clusters)
        clusters = gpd.GeoDataFrame(
            clusters.join(gdf.drop(columns=[model_colname]), how="left"), crs=gdf.crs
        ).reset_index()

        results = ModelResults(
            df=clusters,
            columns=columns,
            labels=model.labels_,
            instance=model,
            W=w0,
            name=model_colname,
            temporal_index=temporal_index,
            unit_index=unit_index,
            scaler=scaler,
            pooling=None,
        )
        models[time] = results

    if return_model:
        return gdf.reset_index(), models

    return gdf.reset_index()


def find_k(
    gdf,
    method=None,
    columns=None,
    temporal_index="year",
    unit_index="geoid",
    scaler="std",
    pooling="fixed",
    random_state=None,
    cluster_kwargs=None,
    min_k=2,
    max_k=10,
    return_table=False,
):
    """Brute-forse search through cluster fit metrics to determine the optimal number of `k` clusters

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame, required
        long-form GeoDataFrame containing neighborhood attributes
    method : str in ['kmeans', 'ward',  'spectral','gaussian_mixture'], required
        the clustering algorithm used to identify neighborhood types
    columns : list-like, required
        subset of columns on which to apply the clustering
    temporal_index : str, optional
        which column on the dataframe defines time and or sequencing of the
        long-form data. Default is "year"
    unit_index : str, optional
        which column on the long-form dataframe identifies the stable units
        over time. In a wide-form dataset, this would be the unique index
    scaler : None or scaler from sklearn.preprocessing, optional
        a scikit-learn preprocessing class that will be used to rescale the
        data. Defaults to sklearn.preprocessing.StandardScaler
    pooling : ["fixed", "pooled", "unique"], optional (default='fixed')
        How to treat temporal data when applying scaling. Options include:

        * fixed : scaling is fixed to each time period
        * pooled : data are pooled across all time periods
        * unique : if scaling, apply the scaler to each time period, then generate
          clusters unique to each time period.
    cluster_kwargs : dict, optional
        additional keyword arguments passed to the clustering algorithm
    min_k : int, optional
        minimum number of clusters to test, by default 2
    max_k : int, optional
        maximum number of clusters to test, by default 10
    return_table : bool, optional
        if True, return the table of fit metrics for each combination
        of k and cluster method, by default False

    Returns
    -------
    pandas.DataFrame
        if return_table==False (default), returns a pandas dataframe with a single column that holds
        the optimal number of clusters according to each fit metric (row index).

        if return_table==True, returns a table of fit coefficients for each k between min_k and max_k
    """
    assert method != "affinity_propagation", (
        "Affinity propagation finds `k` endogenously, "
        "and is incompatible with this function. To "
        "change the number of clusters using affinity propagation "
        "change the `damping` and `preference` arguments"
    )

    output = dict()

    for i in tqdm(range(min_k, max_k + 1), total=max_k - min_k + 1):
        #  create a model_results class
        results = cluster(
            gdf.copy(),
            n_clusters=i,
            method=method,
            best_model=False,
            columns=columns,
            verbose=False,
            temporal_index=temporal_index,
            unit_index=unit_index,
            scaler=scaler,
            pooling=pooling,
            random_state=random_state,
            cluster_kwargs=cluster_kwargs,
            return_model=True,
        )[1]

        results = pd.Series(
            {
                "silhouette_score": results.silhouette_score,
                "calinski_harabasz_score": results.calinski_harabasz_score,
                "davies_bouldin_score": results.davies_bouldin_score,
            },
        )
        output[i] = results
    output = pd.DataFrame(output).T
    summary = output.agg(
        {
            "silhouette_score": "idxmax",
            "calinski_harabasz_score": "idxmax",
            "davies_bouldin_score": "idxmin",  # min score is better here
        }
    ).to_frame(name="best_k")

    if return_table:
        return summary, output
    return summary


def find_region_k(
    gdf,
    method=None,
    columns=None,
    spatial_weights="rook",
    temporal_index="year",
    unit_index="geoid",
    scaler="std",
    weights_kwargs=None,
    region_kwargs=None,
    min_k=2,
    max_k=10,
    return_table=False,
):
    """Brute force through cluster fit metrics to determine the optimal number of `k` regions

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        a long-form geodataframe
    method : string, optional
        the clustering method to use, by default None
    columns : list, optional
        a list of columns in `gdf` to use in the clustering algorithm, by default None
    spatial_weights : ['queen', 'rook'] or libpysal.weights.W object
        spatial weights matrix specification`. By default, geosnap will calculate Rook
        weights, but you can also pass a libpysal.weights.W object for more control
        over the specification.
    temporal_index : str, optional
        column that uniquely identifies time periods, by default "year"
    unit_index : str, optional
        column that uniquely identifies geographic units, by default "geoid"
    scaler : None or scaler from sklearn.preprocessing, optional
        a scikit-learn preprocessing class that will be used to rescale the
        data. Defaults to sklearn.preprocessing.StandardScaler
    cluster_kwargs : dict, optional
        additional kwargs passed to the clustering function in `geosnap.analyze.regionalize`
    max_k : int, optional
        maximum number of clusters to test, by default 10
    return_table : bool, optional
        if True, return the table of fit metrics for each combination
        of k and cluster method, by default False

    Returns
    -------
    pandas.DataFrame
        if return_table==False (default), returns a pandas dataframe with a single column that holds
        the optimal number of clusters according to each fit metric (row index).

        if return_table==True, also returns a table of fit coefficients for each k between min_k and max_k
    """

    output = list()

    for i in tqdm(range(min_k, max_k + 1), total=max_k - min_k + 1):
        #  create a model_results class
        _, results = regionalize(
            gdf.copy(),
            n_clusters=i,
            method=method,
            columns=columns,
            spatial_weights=spatial_weights,
            temporal_index=temporal_index,
            unit_index=unit_index,
            scaler=scaler,
            weights_kwargs=weights_kwargs,
            region_kwargs=region_kwargs,
            return_model=True,
        )

        times = list()
        for time_period in results:

            res = pd.Series(
                {
                    "silhouette_score": results[time_period].silhouette_score,
                    "calinski_harabasz_score": results[
                        time_period
                    ].calinski_harabasz_score,
                    "davies_bouldin_score": results[time_period].davies_bouldin_score,
                    "path_silhouette": results[
                        time_period
                    ].path_silhouette.path_silhouette.mean(),
                    "boundary_silhouette": results[time_period]
                    .boundary_silhouette[
                        results[time_period].boundary_silhouette.boundary_silhouette
                        != 0
                    ]
                    .boundary_silhouette.mean(),  # average of non-zero boundary-silhouettes,
                    "time_period": time_period,
                    "k": i,
                },
            )
            times.append(pd.DataFrame(res).T)
        output.append(pd.concat(times).set_index("k"))
    output = pd.concat(output)

    summary = output.groupby("time_period").agg(
        {
            "silhouette_score": "idxmax",
            "calinski_harabasz_score": "idxmax",
            "path_silhouette": "idxmax",
            "boundary_silhouette": "idxmax",
            "davies_bouldin_score": "idxmin",  # min score is better here
        }
    )
    if return_table:
        return summary, output
    return summary
