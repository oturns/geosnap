import geopandas as gpd
import pandas as pd
from .storage import _fips_filter, _fipstable, _from_db, adjust_inflation
from .util import get_lehd
from warnings import warn


def get_ltdb(
    datastore,
    state_fips=None,
    county_fips=None,
    msa_fips=None,
    fips=None,
    boundary=None,
    years="all",
):
    """Create a new Community from LTDB data.

        Instiantiate a new Community from pre-harmonized LTDB data. To use
        you must first download and register LTDB data with geosnap using
        the `store_ltdb` function. Pass lists of states, counties, or any
        arbitrary FIPS codes to create a community. All fips code arguments
        are additive, so geosnap will include the largest unique set.
        Alternatively, you may provide a boundary to use as a clipping
        feature.

    Parameters
    ----------
    state_fips : list or str
        string or list of strings of two-digit fips codes defining states
        to include in the study area.
    county_fips : list or str
        string or list of strings of five-digit fips codes defining
        counties to include in the study area.
    msa_fips : list or str
        string or list of strings of fips codes defining
        MSAs to include in the study area.
    fips : list or str
        string or list of strings of five-digit fips codes defining
        counties to include in the study area.
    boundary : geopandas.GeoDataFrame
        geodataframe that defines the total extent of the study area.
        This will be used to clip tracts lazily by selecting all
        `GeoDataFrame.representative_point()`s that intersect the
        boundary gdf
    years : list of ints
        list of years (decades) to include in the study data
        (the default "all" is [1970, 1980, 1990, 2000, 2010]).

    Returns
    -------
    geopandas.GeoDataFrame
        long-form geodataframe (with repeated geometries for each time period)


    """
    if years == "all":
        years = [1970, 1980, 1990, 2000, 2010]
    if isinstance(boundary, gpd.GeoDataFrame):
        tracts = datastore.tracts_2010()[["geoid", "geometry"]]
        ltdb = datastore.ltdb().reset_index()
        if boundary.crs != tracts.crs:
            warn(
                "Unable to determine whether boundary CRS is WGS84 "
                "if this produces unexpected results, try reprojecting"
            )
        tracts = tracts[tracts.representative_point().intersects(boundary.unary_union)]
        gdf = ltdb[ltdb["geoid"].isin(tracts["geoid"])]
        gdf = gpd.GeoDataFrame(gdf.merge(tracts, on="geoid", how="left"), crs=4326)

    else:
        gdf = _from_db(
            data=datastore.ltdb(),
            state_fips=state_fips,
            county_fips=county_fips,
            msa_fips=msa_fips,
            fips=fips,
            years=years,
        )
    return gdf.reset_index()


def get_ncdb(
    datastore,
    state_fips=None,
    county_fips=None,
    msa_fips=None,
    fips=None,
    boundary=None,
    years="all",
):
    """Create a new Community from NCDB data.

        Instiantiate a new Community from pre-harmonized NCDB data. To use
        you must first download and register LTDB data with geosnap using
        the `store_ncdb` function. Pass lists of states, counties, or any
        arbitrary FIPS codes to create a community. All fips code arguments
        are additive, so geosnap will include the largest unique set.
        Alternatively, you may provide a boundary to use as a clipping
        feature.

    Parameters
    ----------
    state_fips : list or str
        string or list of strings of two-digit fips codes defining states
        to include in the study area.
    county_fips : list or str
        string or list of strings of five-digit fips codes defining
        counties to include in the study area.
    msa_fips : list or str
        string or list of strings of fips codes defining
        MSAs to include in the study area.
    fips : list or str
        string or list of strings of five-digit fips codes defining
        counties to include in the study area.
    boundary : geopandas.GeoDataFrame
        geodataframe that defines the total extent of the study area.
        This will be used to clip tracts lazily by selecting all
        `GeoDataFrame.representative_point()`s that intersect the
        boundary gdf
    years : list of ints
        list of years (decades) to include in the study data
        (the default is all available [1970, 1980, 1990, 2000, 2010]).

    Returns
    -------
    Community
        Community with NCDB data

    """
    if years == "all":
        years = [1970, 1980, 1990, 2000, 2010]
    if isinstance(boundary, gpd.GeoDataFrame):
        tracts = datastore.tracts_2010()[["geoid", "geometry"]]
        ncdb = datastore.ncdb().reset_index()
        if boundary.crs != tracts.crs:
            warn(
                "Unable to determine whether boundary CRS is WGS84 "
                "if this produces unexpected results, try reprojecting"
            )
        tracts = tracts[tracts.representative_point().intersects(boundary.unary_union)]
        gdf = ncdb[ncdb["geoid"].isin(tracts["geoid"])]
        gdf = gpd.GeoDataFrame(gdf.merge(tracts, on="geoid", how="left"), crs=4326)

    else:
        gdf = _from_db(
            data=datastore.ncdb(),
            state_fips=state_fips,
            county_fips=county_fips,
            msa_fips=msa_fips,
            fips=fips,
            years=years,
        )

    return gdf.reset_index()


def get_census(
    datastore,
    state_fips=None,
    county_fips=None,
    msa_fips=None,
    fips=None,
    boundary=None,
    years="all",
    constant_dollars=True,
    currency_year=2015,
):
    """Create a new Community from original vintage US Census data.

        Instiantiate a new Community from . To use
        you must first download and register census data with geosnap using
        the `store_census` function. Pass lists of states, counties, or any
        arbitrary FIPS codes to create a community. All fips code arguments
        are additive, so geosnap will include the largest unique set.
        Alternatively, you may provide a boundary to use as a clipping
        feature.

    Parameters
    ----------
    state_fips : list or str, optional
        string or list of strings of two-digit fips codes defining states
        to include in the study area.
    county_fips : list or str, optional
        string or list of strings of five-digit fips codes defining
        counties to include in the study area.
    msa_fips : list or str, optional
        string or list of strings of fips codes defining
        MSAs to include in the study area.
    fips : list or str, optional
        string or list of strings of five-digit fips codes defining
        counties to include in the study area.
    boundary : geopandas.GeoDataFrame, optional
        geodataframe that defines the total extent of the study area.
        This will be used to clip tracts lazily by selecting all
        `GeoDataFrame.representative_point()`s that intersect the
        boundary gdf
    years : list of ints, required
        list of years to include in the study data
        (the default is [1990, 2000, 2010]).
    constant_dollars : bool, optional
        whether to standardize currency columns to constant dollars. If true,
        each year will be expressed in dollars set by the `currency_year` parameter
    currency_year : int, optional
        If adjusting for inflation, this parameter sets the year in which dollar values will
        be expressed

    Returns
    -------
    Community
        Community with unharmonized census data

    """
    if years == "all":
        years = [1990, 2000, 2010]
    if isinstance(years, (str, int)):
        years = [years]

    msa_states = []
    if msa_fips:
        pr_metros = set(
            datastore.msa_definitions()[
                datastore.msa_definitions()["CBSA Title"].str.contains("PR")
            ]["CBSA Code"].tolist()
        )
        if msa_fips in pr_metros:
            raise Exception(
                "geosnap does not yet include built-in data for Puerto Rico"
            )
        msa_states += datastore.msa_definitions()[
            datastore.msa_definitions()["CBSA Code"] == msa_fips
        ]["stcofips"].tolist()
    msa_states = [i[:2] for i in msa_states]

    # build a list of states in the dataset
    allfips = []
    for i in [state_fips, county_fips, fips, msa_states]:
        if i:
            if isinstance(i, (str,)):
                i = [i]
            for each in i:
                allfips.append(each[:2])
    states = list(set(allfips))

    # if using a boundary there will be no fips, so reset states to None
    if len(states) == 0:
        states = None

    df_dict = {
        1990: datastore.tracts_1990,
        2000: datastore.tracts_2000,
        2010: datastore.tracts_2010,
    }

    tracts = []
    for year in years:
        tracts.append(df_dict[year](states=states))
    tracts = pd.concat(tracts, sort=False)

    if isinstance(boundary, gpd.GeoDataFrame):
        if boundary.crs != tracts.crs:
            warn(
                "Unable to determine whether boundary CRS is WGS84 "
                "if this produces unexpected results, try reprojecting"
            )
        tracts = tracts[tracts.representative_point().intersects(boundary.unary_union)]
        gdf = tracts.copy()

    else:

        gdf = _fips_filter(
            state_fips=state_fips,
            county_fips=county_fips,
            msa_fips=msa_fips,
            fips=fips,
            data=tracts,
        )

    # adjust for inflation if necessary
    if constant_dollars:
        newtracts = []
        inflate_cols = [
            "median_home_value",
            "median_contract_rent",
            "per_capita_income",
            "median_household_income",
        ]

        for year in years:
            df = gdf[gdf.year == year]
            df = adjust_inflation(df, inflate_cols, year, currency_year)
            newtracts.append(df)
        gdf = pd.concat(newtracts)

    return gdf


def get_lodes(
    datastore,
    state_fips=None,
    county_fips=None,
    msa_fips=None,
    fips=None,
    boundary=None,
    years=2015,
    dataset="wac",
):
    """Create a new Community from Census LEHD/LODES data.

        Instantiate a new Community from LODES data.
        Pass lists of states, counties, or any
        arbitrary FIPS codes to create a community. All fips code arguments
        are additive, so geosnap will include the largest unique set.
        Alternatively, you may provide a boundary to use as a clipping
        feature.

    Parameters
    ----------
    state_fips : list or str, optional
        string or list of strings of two-digit fips codes defining states
        to include in the study area.
    county_fips : list or str, optional
        string or list of strings of five-digit fips codes defining
        counties to include in the study area.
    msa_fips : list or str, optional
        string or list of strings of fips codes defining
        MSAs to include in the study area.
    fips : list or str, optional
        string or list of strings of five-digit fips codes defining
        counties to include in the study area.
    boundary : geopandas.GeoDataFrame, optional
        geodataframe that defines the total extent of the study area.
        This will be used to clip tracts lazily by selecting all
        `GeoDataFrame.representative_point()`s that intersect the
        boundary gdf
    years : list of ints, required
        list of years to include in the study data
        (the default is 2015).
    dataset : str, required
        which LODES dataset should be used to create the Community.
        Options are 'wac' for workplace area characteristics or 'rac' for
        residence area characteristics. The default is "wac" for workplace.

    Returns
    -------
    Community
        Community with LODES data

    """
    if isinstance(years, (str,)):
        years = int(years)
    if isinstance(years, (int,)):
        years = [years]
    years = list(set(years))

    msa_counties = _msa_to_county(datastore, msa_fips)

    states, allfips = _fips_to_states(state_fips, county_fips, msa_counties, fips)

    if any(year < 2010 for year in years):
        gdf00 = datastore.blocks_2000(states=states, fips=(tuple(allfips)))
        gdf00 = gdf00.drop(columns=["year"])
        gdf00 = _fips_filter(
            state_fips=state_fips,
            county_fips=county_fips,
            msa_fips=msa_fips,
            fips=fips,
            data=gdf00,
        )
        if isinstance(boundary, gpd.GeoDataFrame):
            if boundary.crs != gdf00.crs:
                warn(
                    "Unable to determine whether boundary CRS is WGS84 "
                    "if this produces unexpected results, try reprojecting"
                )
            gdf00 = gdf00[gdf00.representative_point().intersects(boundary.unary_union)]

    gdf = datastore.blocks_2010(states=states, fips=(tuple(allfips)))
    gdf = gdf.drop(columns=["year"])
    gdf = _fips_filter(
        state_fips=state_fips,
        county_fips=county_fips,
        msa_fips=msa_fips,
        fips=fips,
        data=gdf,
    )
    if isinstance(boundary, gpd.GeoDataFrame):
        if boundary.crs != gdf.crs:
            warn(
                "Unable to determine whether boundary CRS is WGS84 "
                "if this produces unexpected results, try reprojecting"
            )
        gdf = gdf[gdf.representative_point().intersects(boundary.unary_union)]

    # grab state abbreviations
    names = (
        _fipstable[_fipstable["FIPS Code"].isin(states)]["State Abbreviation"]
        .str.lower()
        .tolist()
    )
    if isinstance(names, str):
        names = [names]

    dfs = []
    for name in names:
        if name == "PR":
            raise Exception("does not yet include built-in data for Puerto Rico")
        for year in years:
            try:
                df = get_lehd(dataset=dataset, year=year, state=name)
                if year < 2010:
                    df = gdf00.merge(df, right_index=True, left_on="geoid", how="left")
                else:
                    df = gdf.merge(df, right_index=True, left_on="geoid", how="left")
                df["year"] = year
                df = df.reset_index().set_index(["geoid", "year"])
                dfs.append(df)
            except ValueError:
                warn(f"{name.upper()} {year} not found!")
                pass
    out = pd.concat(dfs, sort=True)
    out = out[~out.index.duplicated(keep="first")]
    out = out.reset_index()

    return out


def _msa_to_county(datastore, msa_fips):
    if msa_fips:
        pr_metros = set(
            datastore.msa_definitions()[
                datastore.msa_definitions()["CBSA Title"].str.contains("PR")
            ]["CBSA Code"].tolist()
        )
        if msa_fips in pr_metros:
            raise Exception(
                "geosnap does not yet include built-in data for Puerto Rico"
            )
        msa_counties = datastore.msa_definitions()[
            datastore.msa_definitions()["CBSA Code"] == msa_fips
        ]["stcofips"].tolist()

    else:
        msa_counties = None
    return msa_counties


def _fips_to_states(state_fips, county_fips, msa_counties, fips):
    # build a list of states in the dataset
    allfips = []
    stateset = []
    for i in [state_fips, county_fips, msa_counties, fips]:
        if i:
            if isinstance(i, (str,)):
                i = [i]
            for each in i:
                allfips.append(each)
                stateset.append(each[:2])
        states = list(set(stateset))
    return states, allfips
