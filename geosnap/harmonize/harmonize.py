"""Use spatial interpolation to standardize neighborhood boundaries over time."""

import warnings

import geopandas as gpd
import pandas as pd
from tobler.area_weighted import area_interpolate
from tobler.dasymetric import masked_area_interpolate
from tobler.util.util import _check_presence_of_crs
from tqdm.auto import tqdm


def harmonize(
    gdf,
    target_year=None,
    target_gdf=None,
    weights_method="area",
    extensive_variables=None,
    intensive_variables=None,
    allocate_total=True,
    raster=None,
    pixel_values=None,
    temporal_index="year",
    unit_index=None,
    verbose=False,
):
    r"""
    Use spatial interpolation to standardize neighborhood boundaries over time.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Long-form geodataframe with a column that holds unique time periods
        represented by `temporal_index`
    target_year : string
        The target time period whose boundaries form the target, i.e. the boundaries
        in which all other time periods should be expressed (Optional).
    unit_index : str, optional
        the column on the geodataframe that identifies unique units in the timeseries. If None, the
        geodataframe index will be used, and the unique identifier for each unit will be set to "id"
    target_gdf: geopandas.GeoDataFrame
        A geodataframe whose boundaries are the interpolation target for all time periods.
        For example to convert all time periods to a set of hexgrids, generate a set of hexagonal
        polygons using tobler <https://pysal.org/tobler/generated/tobler.util.h3fy.htm> and pass the
        resulting geodataframe as this argument. (Optional).
    weights_method : string
        The method that the harmonization will be conducted. This can be set to:
            * "area"                      : harmonization using simple area-weighted interprolation.
            * "dasymetric"                : harmonization using area-weighted interpolation with raster-based
                                            ancillary data to mask out uninhabited land.
    extensive_variables : list
        The names of variables in each dataset of gdf that contains
        extensive variables to be harmonized (see (2) in Notes).
    intensive_variables : list
        The names of variables in each dataset of gdf that contains
        intensive variables to be harmonized (see (2) in Notes).
    allocate_total : boolean
        True if total value of source area should be allocated.
        False if denominator is area of i. Note that the two cases
        would be identical when the area of the source polygon is
        exhausted by intersections. See (3) in Notes for more details.
    raster : str
        the path to a local raster image to be used as a dasymetric mask. If using
        "dasymetric" this is a required argument.
    codes : list of ints
        list of raster pixel values that should be considered as
        'populated'. Since this draw inspiration using the National Land Cover
        Database (NLCD), the default is 21 (Developed, Open Space),
        22 (Developed, Low Intensity), 23 (Developed, Medium Intensity) and
        24 (Developed, High Intensity). The description of each code can be
        found here:
        https://www.mrlc.gov/sites/default/files/metadata/landcover.html
        Ignored if not using dasymetric harmonizatiton.
    force_crs_match : bool. Default is True.
        Wheter the Coordinate Reference System (CRS) of the polygon will be
        reprojected to the CRS of the raster file. It is recommended to
        leave this argument True.
        Only taken into consideration for harmonization raster based.
    verbose: bool
        whether to print warnings (usually NaN replacement warnings) from tobler
        default is False


    Notes
    -----
    1) Each GeoDataFrame of raw_community is assumed to have a 'year' column
       Also, all GeoDataFrames must have the same Coordinate Reference System (CRS).

    2) A quick explanation of extensive and intensive variables can be found
    here: https://www.esri.com/about/newsroom/arcuser/understanding-statistical-data-for-mapping-purposes/

    3) For an extensive variable, the estimate at target polygon j (default case) is:

        v_j = \sum_i v_i w_{i,j}

        w_{i,j} = a_{i,j} / \sum_k a_{i,k}

        If the area of the source polygon is not exhausted by intersections with
        target polygons and there is reason to not allocate the complete value of
        an extensive attribute, then setting allocate_total=False will use the
        following weights:

        v_j = \sum_i v_i w_{i,j}

        w_{i,j} = a_{i,j} / a_i

        where a_i is the total area of source polygon i.

        For an intensive variable, the estimate at target polygon j is:

        v_j = \sum_i v_i w_{i,j}

        w_{i,j} = a_{i,j} / \sum_k a_{k,j}

    """

    if target_year and target_gdf:
        raise ValueError(
            "Either a target_year or a target_gdf may be specified, but not both"
        )
    assert target_year or isinstance(
        target_gdf, gpd.GeoDataFrame
    ), "must provide either a target year or a target geodataframe"
    if extensive_variables is None and intensive_variables is None:
        raise ValueError(
            "You must pass a set of extensive and/or intensive variables to interpolate"
        )

    _check_presence_of_crs(gdf)
    crs = gdf.crs
    dfs = gdf.copy()
    times = dfs[temporal_index].unique().tolist()
    interpolated_dfs = []

    if unit_index is not None:
        dfs = dfs.set_index(unit_index)

    if target_gdf is not None:
        target_df = target_gdf

    elif target_year:
        times.remove(target_year)
        target_df = dfs[dfs[temporal_index] == target_year]

    unit_index = target_df.index.name if target_df.index.name else "id"
    target_df[unit_index] = target_df.index.values

    geom_name = target_df.geometry.name
    allcols = [unit_index, temporal_index, geom_name]
    if extensive_variables is not None:
        for i in extensive_variables:
            allcols.append(i)
    if intensive_variables is not None:
        for i in intensive_variables:
            allcols.append(i)

    with tqdm(total=len(times), desc=f"Converting {len(times)} time periods") as pbar:
        for i in times:
            pbar.set_description(f"Harmonizing {i}")
            source_df = dfs[dfs[temporal_index] == i]

            if weights_method == "area":
                if verbose:
                    interpolation = area_interpolate(
                        source_df,
                        target_df.copy(),
                        extensive_variables=extensive_variables,
                        intensive_variables=intensive_variables,
                        allocate_total=allocate_total,
                    )
                else:
                    # if there are NaNs, tobler will raise lots of warnings, that it's filling
                    # with implicit 0s. Those warnings are superfluous most of the time
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        interpolation = area_interpolate(
                            source_df,
                            target_df.copy(),
                            extensive_variables=extensive_variables,
                            intensive_variables=intensive_variables,
                            allocate_total=allocate_total,
                        )

            elif weights_method == "dasymetric":
                try:
                    if verbose:
                        interpolation = masked_area_interpolate(
                            source_df,
                            target_df.copy(),
                            extensive_variables=extensive_variables,
                            intensive_variables=intensive_variables,
                            allocate_total=allocate_total,
                            pixel_values=pixel_values,
                            raster=raster,
                        )
                    else:
                        # should probably do this with a decorator..
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            interpolation = masked_area_interpolate(
                                source_df,
                                target_df.copy(),
                                extensive_variables=extensive_variables,
                                intensive_variables=intensive_variables,
                                allocate_total=allocate_total,
                                pixel_values=pixel_values,
                                raster=raster,
                            )
                except OSError as e:
                    raise OSError from e(
                        "Unable to locate raster. If using the `dasymetric` or model-based "
                        "methods. You must provide a raster file and indicate which pixel "
                        "values contain developed land"
                    )
            else:
                raise ValueError('weights_method must of one of ["area", "dasymetric"]')

            interpolation[temporal_index] = i
            interpolation[unit_index] = target_df[unit_index].values
            interpolation = interpolation.set_index(unit_index)
            interpolated_dfs.append(interpolation)

            pbar.update(1)
        pbar.set_description("Complete")
        pbar.close()
    if target_year is not None:
        interpolated_dfs.append(target_df[allcols].set_index(unit_index))

    harmonized_df = gpd.GeoDataFrame(pd.concat(interpolated_dfs), crs=crs)

    return harmonized_df.dropna(how="all")
