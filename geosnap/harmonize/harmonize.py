"""Use spatial interpolation to standardize neighborhood boundaries over time."""

import geopandas as gpd
import pandas as pd
from tobler.area_weighted import area_interpolate
from tobler.dasymetric import masked_area_interpolate
from tobler.util.util import _check_presence_of_crs


def harmonize(
    raw_community,
    target_year=None,
    weights_method="area",
    extensive_variables=None,
    intensive_variables=None,
    allocate_total=True,
    raster=None,
    codes=[21, 22, 23, 24],
    force_crs_match=True,
    index="geoid",
    time_col="year",
):
    r"""
    Use spatial interpolation to standardize neighborhood boundaries over time.

    Parameters
    ----------
    raw_community : list of geopandas.GeoDataFrames
        Multiple GeoDataFrames given by a list (see (1) in Notes).

    target_year : string
        The target year that represents the bondaries of all datasets generated
        in the harmonization. Could be, for example '2010'.

    weights_method : string
        The method that the harmonization will be conducted. This can be set to:
            * "area"                      : harmonization using simple area-weighted interprolation.
            * "dasymetric"                : harmonization using area-weighted interpolation with raster-based
                                            ancillary data to mask out uninhabited land.

    extensive_variables : list
        The names of variables in each dataset of raw_community that contains
        extensive variables to be harmonized (see (2) in Notes).

    intensive_variables : list
        The names of variables in each dataset of raw_community that contains
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


    Notes
    -----
    1) Each GeoDataFrame of raw_community is assumed to have a 'year' column
       Also, all GeoDataFrames must have the same Coordinate Reference System (CRS).

    2) A quick explanation of extensive and intensive variables can be found
    here: http://ibis.geog.ubc.ca/courses/geob370/notes/intensive_extensive.htm

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
    if extensive_variables is None and intensive_variables is None:
        raise ValueError(
            "You must pass a set of extensive and/or intensive variables to interpolate"
        )
    if not extensive_variables:
        extensive_variables = []
    if not intensive_variables:
        intensive_variables = []
    all_vars = extensive_variables + intensive_variables

    _check_presence_of_crs(raw_community)
    dfs = raw_community.copy()
    times = dfs[time_col].unique()

    target_df = dfs[dfs[time_col] == target_year].reset_index()

    interpolated_dfs = {}
    interpolated_dfs[target_year] = target_df.copy()

    for i in times:
        source_df = dfs[dfs[time_col] == i]

        if weights_method == "area":

            # In area_interpolate, the resulting variable has same lenght as target_df
            interpolation = area_interpolate(
                source_df,
                target_df.copy(),
                extensive_variables=extensive_variables,
                intensive_variables=intensive_variables,
                allocate_total=allocate_total,
            )

        elif weights_method == "dasymetric":
            try:
                # In area_interpolate, the resulting variable has same lenght as target_df
                interpolation = masked_area_interpolate(
                    source_df,
                    target_df.copy(),
                    extensive_variables=extensive_variables,
                    intensive_variables=intensive_variables,
                    allocate_total=allocate_total,
                    raster=raster,
                )
            except IOError:
                raise IOError(
                    "Unable to locate raster. If using the `dasymetric` or model-based methods. You"
                    "must provide a raster file and indicate which pixel values contain developed land"
                )
        else:
            raise ValueError('weights_method must of one of ["area", "dasymetric"]')

        profiles = []
        profile = interpolation[all_vars]
        profiles.append(profile)

        profile["geometry"] = target_df["geometry"]
        profile[index] = target_df[index]
        profile[time_col] = i

        interpolated_dfs[i] = profile

    harmonized_df = gpd.GeoDataFrame(
        pd.concat(list(interpolated_dfs.values()), sort=True)
    )

    return harmonized_df
