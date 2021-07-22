import pandas as pd

from segregation import batch, dynamics

try:  # pandarallel gives parallel_apply in pandas
    from pandarallel import pandarallel

    pandarallel.initialize(verbose=1)
    USE_PARALLEL = True
except ImportError:
    USE_PARALLEL = False


def singlegroup_tempdyn(
    gdf, group_pop=None, comp_pop=None, time_index="year", **index_kwargs
):
    if not index_kwargs:
        index_kwargs = {}
    if USE_PARALLEL:
        gdf = gdf.groupby(time_index).parallel_apply(
            lambda x: batch.batch_compute_singlegroup(
                x, group_pop_var=group_pop, total_pop_var=comp_pop, **index_kwargs
            )
        )
    else:
        gdf = gdf.groupby(time_index).apply(
            lambda x: batch.batch_compute_singlegroup(
                x, group_pop_var=group_pop, total_pop_var=comp_pop, **index_kwargs
            )
        )
    gdf = gdf.unstack().T.reset_index(level=0, drop=True)

    return gdf


def multigroup_tempdyn(gdf, groups=None, time_index="year", index_kwargs=None):
    if not index_kwargs:
        index_kwargs = {}
    if not index_kwargs:
        index_kwargs = {}
    if USE_PARALLEL:
        gdf = gdf.groupby(time_index).parallel_apply(
            lambda x: batch.batch_compute_multigroup(x, groups=groups, **index_kwargs)
        )
    else:
        gdf = gdf.groupby(time_index).apply(
            lambda x: batch.batch_compute_multigroup(x, groups=groups, **index_kwargs)
        )
    gdf = gdf.unstack().T.reset_index(level=0, drop=True)

    return gdf


def spacetime_dyn(
    gdf,
    seg_stat=None,
    group_pop=None,
    total_pop=None,
    time_index="year",
    distances=None,
):
    if USE_PARALLEL:
        gdf = gdf.groupby(time_index).parallel_apply(
            lambda x: dynamics.compute_multiscalar_profile(
                x,
                segregation_index=seg_stat,
                group_pop_var=group_pop,
                total_pop_var=total_pop,
                distances=distances,
            )
        )
    else:
        gdf = gdf.groupby(time_index).apply(
            lambda x: dynamics.compute_multiscalar_profile(
                x,
                segregation_index=seg_stat,
                group_pop_var=group_pop,
                total_pop_var=total_pop,
                distances=distances,
            )
        )

    return pd.DataFrame(gdf).T  # convert back to regular DataFrame without geometry
