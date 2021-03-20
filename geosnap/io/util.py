import os
import pathlib
import urllib
import urllib.request
from urllib.error import HTTPError
from warnings import warn

import geopandas as gpd
import pandas as pd


def get_census_gdb(years=None, geom_level="blockgroup", output_dir=None):
    """Fetch file geodatabases of ACS demographic profile data from the Census bureau server.

    Parameters
    ----------
    years : list, optional
        set of years to download (2010 onward), defaults to 2010-2018
    geom_level : str, optional
        geographic unit to download (tract or blockgroup), by default "blockgroup"
    output_dir : str, optional
        output directory to write files, by default None
    """
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    if not output_dir:
        raise Exception("You must set an output directory")
    levels = {"blockgroup": "bg", "tract": "tract"}

    if not years:
        years = range(2010, 2018)
    for year in years:
        fn = f"ACS_{year}_5YR_{levels[geom_level].upper()}.gdb.zip"
        pth = pathlib.PurePath(output_dir, fn)

        if year in [2010, 2011]:
            if geom_level == "blockgroup":
                raise Exception(f"blockgroup data not available for {year}")
            fn = f"{year}_ACS_5YR_{geom_level.capitalize()}.gdb.zip"
            out_fn = f"ACS_{year}_5YR_{levels[geom_level].upper()}.gdb.zip"
            pth = pathlib.PurePath(output_dir, out_fn)
        url = f"https://www2.census.gov/geo/tiger/TIGER_DP/{year}ACS/{fn}"
        urllib.request.urlretrieve(url, pth)


def reformat_acs_vars(col):
    pieces = col.split("e")
    formatted = pieces[0] + "_" + pieces[1].rjust(3, "0") + "E"
    return formatted


def convert_census_gdb(
    file, layers, year=None, level="bg", save_intermediate=True, combine=True, output_dir="."
):
    """Convert file geodatabases from Census into (set of) parquet files.

    Parameters
    ----------
    file : str
        path to file geodatabase
    layers : list
        set of layers to extract from gdb
    year : str, optional
        [description], by default None
    level : str, optional
        geographic level of data ('bg' for blockgroups or 'tr' for tract), by default "bg"
    save_intermediate : bool, optional
        if true, each layer will be stored separately as a parquet file, by default True
    combine : bool
        whether to store and concatenate intermediaate dataframes
    output_dir : str, optional
        path to directory where parquet files will be written, by default "."
    """
    tables = []
    for i in layers:
        print(i)
        df = gpd.read_file(file, driver="FileGDB", layer=i).set_index("GEOID")
        if "ACS_" in i:
            df = gpd.GeoDataFrame(df)
        else:
            df = df[df.columns[df.columns.str.contains("e")]]
            df.columns = pd.Series(df.columns).apply(reformat_acs_vars)
        df = df.dropna(axis=1, how="all")
        if combine:
            tables.append(df)
        if save_intermediate:
            df.to_parquet(
                pathlib.PurePath(output_dir, f"acs_{year}_{i}_{level}.parquet")
            )
    if combine:
        df = pd.concat(tables, axis=1)
        if f"ACS_{year}_5YR_{level.upper()}" in layers:
            df = gpd.GeoDataFrame(df)
        df.to_parquet(pathlib.PurePath(output_dir, f"acs_{year}_{level}.parquet"))


def get_lehd(dataset="wac", state="dc", year=2015):
    """Grab data from the LODES FTP server as a pandas DataFrame.

    Parameters
    ----------
    dataset : str
        which LODES dataset to collect: "rac" or wac", reffering to either
        residence area characteristics or workplace area characteristics
        the default is 'wac').
    state : str
        two-digit state abbreviation for example "ca" or "OH"
    year : str
        which year to collect. First year avaialable for most states is 2002.
        Consult the LODES documentation for more details. The default is 2015.

    Returns
    -------
    pandas.DataFrame
        a pandas DataFrame with columns representing census blocks, indexed on
        the block FIPS code.

    """
    lodes_vars = pd.read_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "lodes.csv")
    )
    renamer = dict(zip(lodes_vars["variable"].tolist(), lodes_vars["name"].tolist()))

    state = state.lower()
    url = "https://lehd.ces.census.gov/data/lodes/LODES7/{state}/{dataset}/{state}_{dataset}_S000_JT00_{year}.csv.gz".format(
        dataset=dataset, state=state, year=year
    )
    try:
        df = pd.read_csv(url, converters={"w_geocode": str, "h_geocode": str})
    except HTTPError:
        raise ValueError(
            "Unable to retrieve LEHD data. Check your internet connection "
            "and that the state/year combination you specified is available"
        )
    df = df.rename({"w_geocode": "geoid", "h_geocode": "geoid"}, axis=1)
    df.rename(renamer, axis="columns", inplace=True)
    df = df.set_index("geoid")

    return df


def adjust_inflation(df, columns, given_year, base_year=2015):
    """
    Adjust currency data for inflation.

    Parameters
    ----------
    df : DataFrame
        Dataframe of historical data
    columns : list-like
        The columns of the dataframe with currency data
    given_year: int
        The year in which the data were collected; e.g. to convert data from
        the 1990 census to 2015 dollars, this value should be 1990.
    base_year: int, optional
        Constant dollar year; e.g. to convert data from the 1990
        census to constant 2015 dollars, this value should be 2015.
        Default is 2015.

    Returns
    -------
    type
        DataFrame

    """
    # get inflation adjustment table from BLS

    inflation = pd.read_parquet(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "bls_inflation.parquet"
        )
    )
    if base_year not in inflation.YEAR.unique():
        try:
            warn(
                f"Unable to find local adjustment year for {base_year}. Attempting from online data"
            )
            inflation = pd.read_excel(
                "https://www.bls.gov/cpi/research-series/allitems.xlsx", skiprows=5
            )

            assert (
                base_year in inflation.YEAR.unique()
            ), f"Unable to find adjustment values for {base_year}"
        except Exception:
            raise ValueError(f"Unable to find adjustment values for {base_year}")

    inflation.columns = inflation.columns.str.lower()
    inflation.columns = inflation.columns.str.strip(".")
    inflation = inflation.dropna(subset=["year"])
    inflator = inflation.groupby("year")["avg"].first().to_dict()
    inflator[1970] = 63.9

    df = df.copy()
    updated = df[columns].apply(
        lambda x: x * (inflator[base_year] / inflator[given_year])
    )
    df.update(updated)

    return df


if __name__ == "__main__":
    get_lehd()
    adjust_inflation()
