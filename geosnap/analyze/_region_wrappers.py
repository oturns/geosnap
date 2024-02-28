import numpy as np
from spopt.region import (
    AZP,
    MaxPHeuristic,
    RegionKMeansHeuristic,
    Skater,
    Spenc,
    WardSpatial,
)


def ward_spatial(data, columns, w, n_clusters=5, clustering_kwds=None, **kwargs):
    """Agglomerative clustering using Ward linkage with a spatial connectivity constraint.

    Parameters
    ----------
    data : geopandas.GeoDataFrame
        geodataframe to be regionalized
    w : libpysal.weights.W instance
        spatial weights matrix
    columns : list
        columns of the dataframe to be used as features in regionalization
    n_clusters : int, optional, default: 5
        The number of regions to form.
    clustering_kwds : dict
        additional keyword arguments passed to clustering algorithm

    Returns
    -------
    fitted cluster instance: sklearn.cluster.AgglomerativeClustering

    """
    if not clustering_kwds:
        clustering_kwds = {}
    model = WardSpatial(
        data,
        n_clusters=n_clusters,
        w=w,
        attrs_name=columns,
        clustering_kwds=clustering_kwds,
    )
    model.solve()
    return model


def kmeans_spatial(data, columns, w, n_clusters=5, **kwargs):
    """Kmeans clustering with a spatial connectivity constraint.

    Parameters
    ----------
    data : geopandas.GeoDataFrame
        geodataframe to be regionalized
    w : libpysal.weights.W instance
        spatial weights matrix
    columns : list
        columns of the dataframe to be used as features in regionalization
    n_clusters : int, optional, default: 5
        The number of regions to form.

    Returns
    -------
    fitted cluster instance: sklearn.cluster.AgglomerativeClustering

    """
    model = RegionKMeansHeuristic(
        data[columns].values,
        n_clusters=n_clusters,
        w=w,
    )
    model.solve()
    return model


def spenc(
    data, w, columns, n_clusters=5, gamma=1, random_state=None, n_jobs=-1, **kwargs
):
    """Spatially encouraged spectral clustering.

    :cite:`wolf2018`

    Parameters
    ----------
    data : geopandas.GeoDataFrame
        geodataframe to be regionalized
    w : libpysal.weights.W instance
        spatial weights matrix
    columns : list
        columns of the dataframe to be used as features in regionalization
    n_clusters : int, optional, default: 5
        The number of regions to form.
    gamma : int
        gamma parameter passed to pysal.spopt.spenc

    Returns
    -------
    fitted cluster instance: spenc.SPENC

    """
    model = Spenc(
        data,
        n_clusters=n_clusters,
        w=w,
        attrs_name=columns,
        gamma=gamma,
        random_state=random_state,
        n_jobs=n_jobs,
    )

    model.solve()
    return model


def skater(
    data,
    w,
    columns,
    n_clusters=5,
    floor=-np.inf,
    islands="increase",
    cluster_args=None,
    **kwargs,
):
    """SKATER spatial clustering algorithm.

    Parameters
    ----------
    data : geopandas.GeoDataFrame
        geodataframe to be regionalized
    w : libpysal.weights.W instance
        spatial weights matrix
    columns : list
        columns of the dataframe to be used as features in regionalization
    n_clusters : int, optional, default: 5
        The number of regions to form.
    floor : int
        Minimum number of units in each region. Default is -inf.
    islands : str
        how to treat islands in the skater clustering model. Default is 'increase'
    cluster_args : dict
        additional keyword arguments passed to clustering algorithm

    Returns
    -------
    fitted cluster instance: region.skater.skater.Spanning_Forest

    """
    if not cluster_args:
        cluster_args = {}
    model = Skater(
        gdf=data,
        n_clusters=n_clusters,
        w=w,
        attrs_name=columns,
        floor=floor,
        islands=islands,
        spanning_forest_kwds=cluster_args,
    )
    model.solve()
    return model


def azp(data, w, columns, n_clusters=5, **kwargs):
    """AZP clustering algorithm.

    Parameters
    ----------
    data : geopandas.GeoDataFrame
        geodataframe to be regionalized
    w : libpysal.weights.W instance
        spatial weights matrix
    columns : list
        columns of the dataframe to be used as features in regionalization
    n_clusters : int, optional, default: 5
        The number of regions to form.

    Returns
    -------
    fitted cluster instance: region.p_regions.azp.AZP

    """
    model = AZP(
        data,
        n_clusters=n_clusters,
        w=w,
        attrs_name=columns,
    )
    model.solve()
    return model


def max_p(
    data,
    w,
    columns,
    threshold_variable="count",
    threshold=10,
    max_iterations_construction=99,
    top_n=2,
    **kwargs,
):
    """Max-p clustering algorithm :cite:`Duque2012`.

    Parameters
    ----------
    data : geopandas.GeoDataFrame
        geodataframe to be regionalized
    w : libpysal.weights.W instance
        spatial weights matrix
    columns : list
        columns of the dataframe to be used as features in regionalization
    n_clusters : int, optional, default: 5
        The number of regions to form.
    threshold_variable : str, default:"count"
        attribute variable to use as floor when calculate
    threshold : int, default:10
        integer that defines the upper limit of a variable that can be grouped
        into a single region
    max_iterations_construction : int
        Max number of iterations for construction phase.
    top_n : int
        The number of top candidate regions to consider for enclave assignment.

    Returns
    -------
    fitted cluster instance: region.p_regions.heuristics.MaxPRegionsHeu

    """
    if threshold_variable == "count":
        data["_count"] = 1
        threshold_variable = "_count"
    model = MaxPHeuristic(
        gdf=data,
        w=w,
        attrs_name=columns,
        threshold_name=threshold_variable,
        threshold=threshold,
        top_n=top_n,
        max_iterations_construction=max_iterations_construction,
        verbose=False,
    )
    model.solve()
    return model
