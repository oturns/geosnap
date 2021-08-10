"""Tools for analyzing changes in segregation over time and space."""

import pandas as pd
from joblib import Parallel, delayed
from segregation import batch, dynamics


def _prep_single(group):
    """Private function for parallel batch computation of single-group measures.

    Parameters
    ----------
    group : tuple
        arguments passed to batch_compute_singlegroup

    Returns
    -------
    geodataframe
    """
    args = group[1]
    time = group[0][args["time_index"]].iloc[0]
    gdf = batch.batch_compute_singlegroup(group[0], **args)
    gdf[args["time_index"]] = time
    return gdf


def _prep_prof(group):
    """Private function for parallel computation of multiscalar profiles.

    Parameters
    ----------
    group : tuple
        arguments passed to multiscalar profile function

    Returns
    -------
    geodataframe
    """
    args = group[1]
    time = group[0][args["time_index"]].iloc[0]
    args.pop("time_index")
    args.pop("n_jobs")
    args.pop("backend")
    gdf = dynamics.compute_multiscalar_profile(group[0], **args)
    gdf = gdf.to_frame()
    gdf.columns = [time]
    return gdf


def singlegroup_tempdyn(
    gdf,
    group_pop_var=None,
    total_pop_var=None,
    time_index="year",
    n_jobs=-1,
    backend="loky",
    **index_kwargs
):
    """Batch compute singlegroup segregation indices for each time period in parallel.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        geodataframe formatted as a long-form timeseries
    group_pop_var : str
        name of column on gdf containing population counts for the group of interest
    total_pop_var : str
        name of column on gdf containing total population counts for the unit
    time_index : str
        column on the dataframe that denotes unique time periods, by default "year"
    n_jobs : int, optional
        number of cores to use for computation. If -1, all available cores will be
        used, by default -1
    backend : str, optional
        computation backend passed to joblib. One of {'multiprocessing', 'loky',
        'threading'}, by default "loky"

    Returns
    -------
    geopandas.GeoDataFrame
        dataframe with unique segregation indices as rows and estimates for each
        time period as columns
    """
    # essentially implement a parallelized grouby-apply
    gdf = gdf.copy()
    input_args = locals()
    input_args.pop("gdf")
    input_args[
        "backend"
    ] = "multiprocessing"  # threading backend fails for modified gini and dissim
    # Create a tuple of (df, arguments) for each unique time period to pass to the parallel function
    dataframes = tuple([[group, input_args] for _, group in gdf.groupby(time_index)])
    estimates = Parallel(n_jobs=n_jobs, backend=backend)(
        delayed(_prep_single)(i) for i in dataframes
    )
    gdf = pd.concat(estimates)
    gdf = gdf.pivot(columns=time_index)
    gdf = gdf.T.reset_index(level=0, drop=True).T  # don't want a multiindex
    return gdf


def multigroup_tempdyn(gdf, groups=None, time_index="year", index_kwargs=None):
    """Batch compute multigroup segregation indices for each time period.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        geodataframe formatted as a long-form timeseries
    groups : list
        list of columns on gdf containing population counts for each group of interest
    time_index : str
        column on the dataframe that denotes unique time periods, by default "year"
    index_kwargs : dict
        dictionary of additional keyword arguments passed to
        segregation.batch.batch_compute_multigroup

    Returns
    -------
    geopandas.GeoDataFrame
        dataframe with unique segregation indices as rows and estimates for each
        time period as columns
    """
    gdf = gdf.copy()
    # could parallelize this, but the indices are fast enough it's not clearly worth it
    if not index_kwargs:
        index_kwargs = {}
    gdf = gdf.groupby(time_index).apply(
        lambda x: batch.batch_compute_multigroup(x, groups=groups, **index_kwargs)
    )
    gdf = gdf.unstack().T.reset_index(level=0, drop=True)

    return gdf


def spacetime_dyn(
    gdf,
    segregation_index=None,
    group_pop_var=None,
    total_pop_var=None,
    groups=None,
    time_index="year",
    distances=None,
    n_jobs=-1,
    backend="loky",
):
    """Batch compute multiscalar segregation profiles for each time period in parallel.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        geodataframe formatted as a long-form timeseries
    segregation_index : segregation.singlegroup or segregation.multigroup class
        a segregation index class from the pysal `segregation` package
    group_pop_var : str
        name of column on gdf containing population counts for the group of interest
    total_pop_var : str
        name of column on gdf containing total population counts for the unit
    groups : list
        list of columns on gdf containing population counts for each group of interest
        (for multigroup indices)
    distances : list
        list of distances used to define the radius of the egohood at each step of the profile
    time_index : str
        column on the dataframe that denotes unique time periods, by default "year"
    n_jobs : int, optional
        number of cores to use for computation. If -1, all available cores will be
        used, by default -1
    backend : str, optional
        computation backend passed to joblib. One of {'multiprocessing', 'loky',
        'threading'}, by default "loky"

    Returns
    -------
    geopandas.GeoDataFrame
        dataframe with unique time periods as rows and estimates for each
        spatial extent as columns
    """
    gdf = gdf.copy()
    # essentially implement a parallelized grouby-apply
    assert distances, "You must supply a list of distances"
    input_args = locals()
    input_args.pop("gdf")
    input_args[
        "backend"
    ] = "multiprocessing"  # threading backend fails for modified gini and dissim
    # Create a tuple of (df, arguments) for each unique time period to pass to the parallel function
    dataframes = tuple([[group, input_args] for _, group in gdf.groupby(time_index)])
    estimates = Parallel(n_jobs=n_jobs, backend=backend)(
        delayed(_prep_prof)(i) for i in dataframes
    )
    gdf = pd.concat(estimates, axis=1)

    return gdf
