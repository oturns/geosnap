import pandas as pd
from joblib import Parallel, delayed
from segregation import batch, dynamics


def singlegroup_tempdyn(
    gdf,
    group_pop_var=None,
    total_pop_var=None,
    time_index="year",
    n_jobs=-1,
    backend="loky",
    **index_kwargs
):
    # essentially implement a parallelized grouby-apply
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


def _prep_single(group):
    args = group[1]
    time = group[0][args["time_index"]].iloc[0]
    gdf = batch.batch_compute_singlegroup(group[0], **args)
    gdf[args["time_index"]] = time
    return gdf


def _prep_prof(group):
    args = group[1]
    time = group[0][args["time_index"]].iloc[0]
    tindex_name = args["time_index"]
    args.pop("time_index")
    args.pop("n_jobs")
    args.pop("backend")
    gdf = dynamics.compute_multiscalar_profile(group[0], **args)
    gdf = gdf.to_frame()
    gdf.columns = [time]
    return gdf


def multigroup_tempdyn(gdf, groups=None, time_index="year", index_kwargs=None):
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
    # essentially implement a parallelized grouby-apply
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
