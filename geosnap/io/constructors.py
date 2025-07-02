import contextlib
from warnings import warn

import geopandas as gpd
import pandas as pd

from .storage import _fips_filter, _fipstable, _from_db, adjust_inflation
from .util import get_lehd

__all__ = [
    "get_acs",
    "get_census",
    "get_ejscreen",
    "get_lodes",
    "get_ltdb",
    "get_ncdb",
    "get_nces",
]


def get_nces(datastore, years="1516", dataset="sabs"):
    """Extract a subset of data from the National Center for Educational Statistics as a long-form geodataframe.

    Parameters
    ----------
    datastore : geosnap.DataStore
        an instantiated DataStore object
    years : str, optional
        set of academic years to return formatted as a 4-digit string representing the two years
        from a single period of the academic calendar. For example, the 2015-2016 academic year
        is represented as "1516". Defaults to "1516"
    dataset : str, optional
        which NCES dataset to query. Options include `sabs`, `districts`, or `schools`
        Defaults to 'sabs'

    Returns
    -------
    geopandas.GeoDataFrame
        long-form geodataframe with 'year' column representing each time period

    """
    if isinstance(years, (str,)):
        years = [int(years)]
    elif isinstance(years, (int,)):
        years = [years]

    dflist = []
    for year in years:
        df = datastore.nces(year=year, dataset=dataset)
        dflist.append(df)
    gdf = pd.concat(dflist)
    return gdf.reset_index(drop=True)


def get_ejscreen(
    datastore,
    state_fips=None,
    county_fips=None,
    msa_fips=None,
    fips=None,
    years="all",
):
    """Extract a subset of data from the EPA EJSCREEN as a long-form geodataframe.

    Parameters
    ----------
    datastore : geosnap.DataStore
        an instantiated DataStore object
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
        string or list of strings of fips codes (any length) defining
        census units to include in the study area.
    years : str, optional
        list of years to include in the extract. Following Census convention, years
        are named by the conclusion of the 5-year period. For example the 2011-2015
        sample is represented as `2015`. Defaults to "all" which includes every dataset
        available (curently 2012-2019)

    Returns
    -------
    geopandas.GeoDataFrame
        long-form geodataframe with 'year' column representing each time period
    """
    if years == "all":
        years = list(range(2015, 2021))

    elif isinstance(years, (str,)):
        years = [int(years)]
    elif isinstance(years, (int,)):
        years = [years]

    msa_counties = _msa_to_county(datastore, msa_fips)

    states, allfips = _fips_to_states(state_fips, county_fips, msa_counties, fips)

    dflist = []
    for year in years:
        df = datastore.ejscreen(
            states=states,
            year=year,
        )
        df = _fips_filter(
            state_fips=state_fips,
            county_fips=county_fips,
            msa_fips=msa_fips,
            fips=fips,
            data=df,
        )
        dflist.append(df)
    gdf = pd.concat(dflist)
    return gdf.reset_index(drop=True)


def get_acs(
    datastore,
    level="bg",
    state_fips=None,
    county_fips=None,
    msa_fips=None,
    fips=None,
    years="all",
    constant_dollars=True,
    currency_year=None,
):
    """Extract a subset of data from the American Community Survey (ACS).

    Parameters
    ----------
    datastore : geosnap.DataStore
        an instantiated DataStore object
    level : str
        string denoting which geographic level of data to collect: `bg` for
        census blockgroups or `tract` for census tracts
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
    geopandas.GeoDataFrame
        long-form geodataframe with 'year' column representing each time period
    """
    inflate_cols = [
        "median_home_value",
        "median_contract_rent",
        "per_capita_income",
        "median_household_income",
    ]
    _levs = ["bg", "tract"]
    if level not in _levs:
        raise ValueError(
            f"the `level` parameter must be one of {_levs} but {level} was passed"
        )
    if years == "all":
        years = list(range(2012, 2022))

    elif isinstance(years, (str,)):
        years = [int(years)]
    elif isinstance(years, (int,)):
        years = [years]

    if currency_year is None:
        currency_year = max(years)
        if len(years) > 1:  # if there's only one year, then no adjustment happens
            warn(
                "`constant_dollars` is True, but no `currency_year` was specified. "
                f"Resorting to max value of {currency_year}",
                stacklevel=1,
            )
    msa_counties = _msa_to_county(datastore, msa_fips)

    states, allfips = _fips_to_states(state_fips, county_fips, msa_counties, fips)

    dflist = []
    for year in years:
        df = datastore.acs(
            level=level,
            states=states,
            year=year,
        )
        df = _fips_filter(
            state_fips=state_fips,
            county_fips=county_fips,
            msa_fips=msa_fips,
            fips=fips,
            data=df,
        )
        if constant_dollars:
            try:
                df = adjust_inflation(df, inflate_cols, year, currency_year)
            except:
                warn(
                    "Currency columns unavailable at this resolution; not adjusting for inflation"
                )
        dflist.append(df)
    gdf = pd.concat(dflist)
    return gdf.reset_index(drop=True)


def get_ltdb(
    datastore,
    state_fips=None,
    county_fips=None,
    msa_fips=None,
    fips=None,
    boundary=None,
    years="all",
):
    """Extract a subset of data from the Longitudinal Tract Database (LTDB) as a long-form geodataframe.

    Parameters
    ----------
    datastore : geosnap.DataStore
        an instantiated DataStore object
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
        long-form geodataframe with 'year' column representing each time period
    """
    if years == "all":
        years = [1970, 1980, 1990, 2000, 2010]
    if isinstance(boundary, gpd.GeoDataFrame):
        tracts = datastore.tracts_2010()[["geoid", "geometry"]]
        ltdb = datastore.ltdb().reset_index()
        if not boundary.crs.equals(4326):
            boundary = boundary.copy().to_crs(4326)
        tracts = tracts[tracts.representative_point().intersects(boundary.union_all())]
        gdf = ltdb[ltdb["geoid"].isin(tracts["geoid"])]
        gdf = gpd.GeoDataFrame(gdf.merge(tracts, on="geoid", how="left"), crs=4326)
        gdf = gdf[gdf["year"].isin(years)]

    else:
        gdf = _from_db(
            datastore,
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
    """Extract a subset of data from the Neighborhood Change Database (NCDB).

    Parameters
    ----------
    datastore : geosnap.DataStore
        an instantiated DataStore object
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
        long-form geodataframe with 'year' column representing each time period
    """
    if years == "all":
        years = [1970, 1980, 1990, 2000, 2010]
    if isinstance(boundary, gpd.GeoDataFrame):
        tracts = datastore.tracts_2010()[["geoid", "geometry"]]
        ncdb = datastore.ncdb().reset_index()
        if not boundary.crs.equals(4326):
            boundary = boundary.copy().to_crs(4326)
        tracts = tracts[tracts.representative_point().intersects(boundary.union_all())]
        gdf = ncdb[ncdb["geoid"].isin(tracts["geoid"])]
        gdf = gpd.GeoDataFrame(gdf.merge(tracts, on="geoid", how="left"), crs=4326)
        gdf = gdf[gdf["year"].isin(years)]

    else:
        gdf = _from_db(
            datastore,
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
    currency_year=None,
):
    """Extract a subset of data from the decennial U.S. Census as a long-form geodataframe.

    Parameters
    ----------
    datastore : geosnap.DataStore
        an instantiated DataStore object
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
    geopandas.GeoDataFrame
        long-form geodataframe with 'year' column representing each time period

    """

    if years == "all":
        years = [1990, 2000, 2010]
    if isinstance(years, (str, int)):
        years = [years]
    if currency_year is None:
        currency_year = max(years)
        if len(years) > 1:  # if there's only one year, then no adjustment happens
            warn(
                "`constant_dollars` is True, but no `currency_year` was specified. "
                f"Resorting to max value of {currency_year}"
            )
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
        if not boundary.crs.equals(4326):
            boundary = boundary.copy().to_crs(4326)
        tracts = tracts[tracts.representative_point().intersects(boundary.union_all())]
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

    return gdf.reset_index(drop=True)


def get_lodes(
    datastore,
    state_fips=None,
    county_fips=None,
    msa_fips=None,
    fips=None,
    boundary=None,
    years=2015,
    dataset="wac",
    version=8,
):
    """Extract a subset of data from Census LEHD/LODES .


    Parameters
    ----------
    datastore : geosnap.DataStore
        an instantiated DataStore object
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
    version : int
        which version of LODES to query. Options include 5, 7 and 8, which
        are keyed to census 2000, 2010, and 2020 blocks respectively

    Returns
    -------
    geopandas.GeoDataFrame
        long-form geodataframe with 'year' column representing each time period

    """
    if isinstance(years, (str,)):
        years = int(years)
    if isinstance(years, (int,)):
        years = [years]
    years = list(set(years))

    msa_counties = _msa_to_county(datastore, msa_fips)

    states, allfips = _fips_to_states(state_fips, county_fips, msa_counties, fips)
    if boundary and not boundary.crs.equals(4326):
        boundary = boundary.copy().to_crs(4326)
    if version == 5:
        gdf = datastore.blocks_2000(states=states, fips=(tuple(allfips)))
    elif version == 7:
        gdf = datastore.blocks_2010(states=states, fips=(tuple(allfips)))
    elif version == 8:
        gdf = datastore.blocks_2020(states=states, fips=(tuple(allfips)))

    gdf = gdf.drop(columns=["year"])
    gdf = _fips_filter(
        state_fips=state_fips,
        county_fips=county_fips,
        msa_fips=msa_fips,
        fips=allfips,
        data=gdf,
    )
    if isinstance(boundary, gpd.GeoDataFrame):
        if boundary.crs != gdf.crs:
            warn(
                "Unable to determine whether boundary CRS is WGS84 "
                "if this produces unexpected results, try reprojecting",
                stacklevel=2,
            )
        gdf = gdf[gdf.representative_point().intersects(boundary.union_all())]

    # grab state abbreviations
    names = (
        _fipstable[_fipstable["FIPS Code"].isin(states)]["State Abbreviation"]
        .str.lower()
        .tolist()
    )
    if isinstance(names, str):
        names = [names]

    dfs = []
    for year in years:
        for name in names:
            merged_year = []
            if name == "PR":
                raise ValueError("LODES does not yet include data for Puerto Rico")
            try:
                df = get_lehd(dataset=dataset, year=year, state=name, version=version)
                df = gdf.merge(df, right_index=True, left_on="geoid", how="left")
                df["year"] = year
                merged_year.append(df)
            except ValueError:
                warn(f"{name.upper()} {year} not found!", stacklevel=2)
                pass
            with contextlib.suppress(ValueError):
                dfs.append(pd.concat(merged_year))
    out = pd.concat(dfs, sort=True)
    out = out.groupby(["geoid", "year"]).first().reset_index()
    out.crs = 4326
    return out


def _msa_to_county(datastore, msa_fips):
    if msa_fips is None:
        return 0  # dummy integer guaranteed to return no slice from `msa_defs`
    msa_defs = datastore.msa_definitions()
    pr_metros = set(
        msa_defs[msa_defs["CBSA Title"].str.contains("PR")]["CBSA Code"].tolist()
    )
    if msa_fips in pr_metros:
        raise Exception("geosnap does not yet include built-in data for Puerto Rico")
    msa_counties = msa_defs[msa_defs["CBSA Code"] == int(msa_fips)]["stcofips"].tolist()

    return msa_counties


def _fips_to_states(state_fips, county_fips, msa_counties, fips):
    # build a list of states in the dataset
    allfips = []
    stateset = []
    for i in [state_fips, county_fips, msa_counties, fips]:
        if i:
            if isinstance(i, str):
                i = [i]
            elif isinstance(i, int):
                i = [str(i)]
            for each in i:
                allfips.append(each)
                stateset.append(each[:2])
        states = list(set(stateset))
    return states, allfips
