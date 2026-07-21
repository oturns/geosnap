from warnings import warn

import geopandas as gpd
import ibis

from .storage import _fips_filter, _fipstable
from .util import _get_inflate_coef, get_lehd

__all__ = [
    "get_acs",
    "get_census",
    "get_ejscreen",
    "get_lodes",
    "get_ltdb",
    "get_ncdb",
    "get_nces",
]


def _normalize_boundary(boundary):
    if boundary is None:
        return None
    if boundary.crs.equals(4326):
        return boundary
    return boundary.copy().to_crs(4326)


def _materialize_geotable(table):
    return table.to_pandas().set_crs(4326)


def _filter_tracts_by_boundary(datastore, boundary):
    boundary = _normalize_boundary(boundary)
    tracts = datastore.tracts_2010(execute=False)
    tracts = tracts.filter(tracts.geometry.centroid().intersects(boundary.union_all()))
    tracts = tracts.select("geoid", "geometry")
    return _materialize_geotable(tracts)


def _build_local_panel_query(
    datastore,
    data,
    state_fips=None,
    county_fips=None,
    msa_fips=None,
    fips=None,
    years=None,
):
    panel = ibis.memtable(data.reset_index())
    panel = panel.filter(panel.year.isin(years))
    panel = _fips_filter(
        state_fips=state_fips,
        county_fips=county_fips,
        msa_fips=msa_fips,
        fips=fips,
        data=panel,
    )

    tracts = datastore.tracts_2010(execute=False)
    tracts = tracts.select("geoid", "geometry")
    panel = panel.join(tracts, [panel.geoid == tracts.geoid], how="left")
    panel = panel.drop("geoid_right")
    return panel


def _build_acs_query(
    datastore,
    level="bg",
    state_fips=None,
    county_fips=None,
    msa_fips=None,
    fips=None,
    years="all",
    constant_dollars=True,
    currency_year=None,
    boundary=None,
):
    _levs = ["bg", "tract"]
    if level not in _levs:
        raise ValueError(
            f"the `level` parameter must be one of {_levs} but {level} was passed"
        )
    inflate_cols = [
        "median_home_value",
        "median_contract_rent",
        "per_capita_income",
        "median_household_income",
    ]
    if level == "tract":
        inflate_cols = inflate_cols + [
            "median_income_whitehh",
            "median_income_blackhh",
            "median_income_hispanichh",
        ]
    if years == "all":
        years = list(range(2012, 2022))
    elif isinstance(years, (str,)):
        years = [int(years)]
    elif isinstance(years, (int,)):
        years = [years]

    if currency_year is None:
        currency_year = max(years)
        if len(years) > 1:
            warn(
                "`constant_dollars` is True, but no `currency_year` was specified. "
                f"Resorting to max value of {currency_year}",
                stacklevel=1,
            )
    msa_counties = _msa_to_county(datastore, msa_fips)
    states, _ = _fips_to_states(state_fips, county_fips, msa_counties, fips)
    boundary = _normalize_boundary(boundary)

    common_cols = []
    dflist = []
    for year in years:
        df = datastore.acs(level=level, states=states, year=year, execute=False)

        if boundary is not None:
            df = df.filter(df.geometry.centroid().intersects(boundary.union_all()))
        else:
            df = _fips_filter(
                state_fips=state_fips,
                county_fips=county_fips,
                msa_fips=msa_fips,
                fips=fips,
                data=df,
            )

        if constant_dollars:
            coef = _get_inflate_coef(year, currency_year)
            for col in inflate_cols:
                if col not in df.columns:
                    warn(
                        f"Currency column {col} not present in dataframe",
                        stacklevel=2,
                    )
                else:
                    newcol = (df[col] * coef).round(0).cast("float64")
                    df = df.mutate(newcol.name(col))
        common_cols.append(set(df.columns))
        dflist.append(df)

    common_cols = set.intersection(*common_cols)
    dflist = [df.select(common_cols) for df in dflist]
    gdf = ibis.union(*dflist, distinct=True)
    return gdf.distinct(on=["geoid", "year"])


def _build_census_query(
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
    if years == "all":
        years = [1990, 2000, 2010]
    if isinstance(years, (str, int)):
        years = [years]
    if currency_year is None:
        currency_year = max(years)
        if len(years) > 1:
            warn(
                "`constant_dollars` is True, but no `currency_year` was specified. "
                f"Resorting to max value of {currency_year}",
                stacklevel=2,
            )

    msa_counties = _msa_to_county(datastore, msa_fips)
    states, _ = _fips_to_states(state_fips, county_fips, msa_counties, fips)
    if len(states) == 0:
        states = None
    boundary = _normalize_boundary(boundary)

    df_dict = {
        1990: datastore.tracts_1990,
        2000: datastore.tracts_2000,
        2010: datastore.tracts_2010,
    }

    tracts = []
    common_cols = []
    for year in years:
        if year < 2020:
            df = df_dict[year](states=states, execute=False)
        else:
            df = datastore.acs(
                year=2021,
                states=states,
                execute=False,
                level="tract",
            )
        tracts.append(df)
        common_cols.append(set(df.columns))

    common_cols = set.intersection(*common_cols)
    tracts = [df.select(common_cols) for df in tracts]
    tracts = ibis.union(*tracts, distinct=True)

    if boundary is not None:
        gdf = tracts.filter(tracts.geometry.centroid().intersects(boundary.union_all()))
    else:
        gdf = _fips_filter(
            state_fips=state_fips,
            county_fips=county_fips,
            msa_fips=msa_fips,
            fips=fips,
            data=tracts,
        )

    if constant_dollars:
        newtracts = []
        inflate_cols = [
            "median_home_value",
            "median_contract_rent",
            "per_capita_income",
            "median_household_income",
        ]

        for year in years:
            filter_year = year + 1 if year == 2020 else year
            df = gdf.filter(gdf.year == filter_year)
            coef = _get_inflate_coef(filter_year, currency_year)
            for col in inflate_cols:
                if col not in df.columns:
                    warn(
                        f"Currency column {col} not present in dataframe",
                        stacklevel=2,
                    )
                else:
                    newcol = (df[col] * coef).round(0).cast("float64")
                    df = df.mutate(newcol.name(col))
            newtracts.append(df)
        if newtracts:
            gdf = ibis.union(*newtracts, distinct=True)

    return gdf.distinct(on=["geoid", "year"])


def _build_lodes_query(
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
    if isinstance(years, (str,)):
        years = int(years)
    if isinstance(years, (int,)):
        years = [years]
    years = list(set(years))

    msa_counties = _msa_to_county(datastore, msa_fips)
    states, allfips = _fips_to_states(state_fips, county_fips, msa_counties, fips)
    boundary = _normalize_boundary(boundary)

    if boundary is not None and len(states) == 0:
        states = datastore.states(execute=False).geoid.to_pandas().values
        warn(
            "No state fips found; searching all states. When using a boundary "
            + "in this function it is recommended to pass state FIPS if possible",
            stacklevel=2,
        )
    if version == 5:
        gdf = datastore.blocks_2000(states=states, fips=tuple(allfips), execute=False)
    elif version == 7:
        gdf = datastore.blocks_2010(states=states, fips=tuple(allfips), execute=False)
    elif version == 8:
        gdf = datastore.blocks_2020(states=states, fips=tuple(allfips), execute=False)
    else:
        raise ValueError("version must be one of 5, 7, or 8")

    gdf = gdf.drop("year")

    if boundary is not None:
        gdf = gdf.filter(gdf.geometry.centroid().intersects(boundary.union_all()))
        # LEHD files are fetched per state, so this concrete list is required.
        states = gdf.geoid.substr(0, 2).to_pandas().unique()
    else:
        gdf = _fips_filter(
            state_fips=state_fips,
            county_fips=county_fips,
            msa_fips=msa_fips,
            fips=fips,
            data=gdf,
        )

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
            if name == "PR":
                raise ValueError("LODES does not yet include data for Puerto Rico")
            try:
                df = ibis.memtable(
                    get_lehd(
                        dataset=dataset,
                        year=year,
                        state=name,
                        version=version,
                    ).reset_index()
                )
                df = gdf.join(df, "geoid", how="left").drop("geoid_right")
                df = df.mutate(year=year)
                dfs.append(df)
            except ValueError:
                warn(f"{name.upper()} {year} not found!", stacklevel=2)

    out = ibis.union(*dfs, distinct=True)
    return out.distinct(on=["geoid", "year"])


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
        df = datastore.nces(year=year, dataset=dataset, execute=False)
        dflist.append(df)
    gdf = ibis.union(*dflist, distinct=True)
    return gdf.to_pandas().set_crs(4326)


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
        df = datastore.ejscreen(states=states, year=year, execute=False)
        df = _fips_filter(
            state_fips=state_fips,
            county_fips=county_fips,
            msa_fips=msa_fips,
            fips=fips,
            data=df,
        )
        dflist.append(df)
    gdf = ibis.union(*dflist, distinct=True)
    gdf = gdf.distinct(on=["geoid", "year"])

    return gdf.to_pandas()


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
    boundary=None,
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
    boundary : geopandas.GeoDataFrame
        geodataframe that defines the total extent of the study area.
        This will be used to clip tracts lazily by selecting all
        `GeoDataFrame.centroid()`s that intersect the
        boundary gdf

    Returns
    -------
    geopandas.GeoDataFrame
        long-form geodataframe with 'year' column representing each time period
    """
    gdf = _build_acs_query(
        datastore=datastore,
        level=level,
        state_fips=state_fips,
        county_fips=county_fips,
        msa_fips=msa_fips,
        fips=fips,
        years=years,
        constant_dollars=constant_dollars,
        currency_year=currency_year,
        boundary=boundary,
    )
    return _materialize_geotable(gdf)


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
        tracts = _filter_tracts_by_boundary(datastore, boundary)
        ltdb = datastore.ltdb().reset_index()
        gdf = ltdb[ltdb["geoid"].isin(tracts["geoid"])]
        gdf = gpd.GeoDataFrame(gdf.merge(tracts, on="geoid", how="left"), crs=4326)
        gdf = gdf[gdf["year"].isin(years)]

    else:
        gdf = _build_local_panel_query(
            datastore,
            data=datastore.ltdb(),
            state_fips=state_fips,
            county_fips=county_fips,
            msa_fips=msa_fips,
            fips=fips,
            years=years,
        )
        gdf = _materialize_geotable(gdf)
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
        tracts = _filter_tracts_by_boundary(datastore, boundary)
        ncdb = datastore.ncdb().reset_index()
        gdf = ncdb[ncdb["geoid"].isin(tracts["geoid"])]
        gdf = gpd.GeoDataFrame(gdf.merge(tracts, on="geoid", how="left"), crs=4326)
        gdf = gdf[gdf["year"].isin(years)]

    else:
        gdf = _build_local_panel_query(
            datastore,
            data=datastore.ncdb(),
            state_fips=state_fips,
            county_fips=county_fips,
            msa_fips=msa_fips,
            fips=fips,
            years=years,
        )
        gdf = _materialize_geotable(gdf)

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
    gdf = _build_census_query(
        datastore=datastore,
        state_fips=state_fips,
        county_fips=county_fips,
        msa_fips=msa_fips,
        fips=fips,
        boundary=boundary,
        years=years,
        constant_dollars=constant_dollars,
        currency_year=currency_year,
    )
    return _materialize_geotable(gdf)


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
    out = _build_lodes_query(
        datastore=datastore,
        state_fips=state_fips,
        county_fips=county_fips,
        msa_fips=msa_fips,
        fips=fips,
        boundary=boundary,
        years=years,
        dataset=dataset,
        version=version,
    )
    return _materialize_geotable(out)


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
    states = []
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
