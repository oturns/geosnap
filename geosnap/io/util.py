import os
import pathlib
from urllib.error import HTTPError
from warnings import warn

import geopandas as gpd
import pandas as pd


def get_census_gdb(years=None, geom_level="blockgroup", output_dir="."):
    """Fetch file geodatabases of ACS demographic profile data from the Census bureau server.

    Parameters
    ----------
    years : list, optional
        set of years to download (2010 onward), defaults to 2010-2019
    geom_level : str, optional
        geographic unit to download (tract or blockgroup), by default "blockgroup"
    output_dir : str, optional
        output directory to write files, by default "."
    """
    try:
        from download import download
    except ImportError:
        raise ImportError(
            "this function requires choldgraf's `download` package\n"
            "`pip install git+https://github.com/choldgraf/download`"
        )
    levels = {"blockgroup": "bg", "tract": "tract"}

    if not years:
        years = range(2010, 2020)
    for year in years:
        fn = f"ACS_{year}_5YR_{levels[geom_level].upper()}.gdb.zip"
        pth = pathlib.PurePath(output_dir, fn)

        if year in [2010, 2011]:
            if geom_level == "blockgroup":
                raise Exception(f"blockgroup data not available for {year}")
            fn = f"{year}_ACS_5YR_{geom_level.capitalize()}.gdb.zip"
            out_fn = f"ACS_{year}_5YR_{levels[geom_level].upper()}.gdb.zip"
            pth = pathlib.PurePath(output_dir, out_fn)
        url = f"ftp://ftp2.census.gov/geo/tiger/TIGER_DP/{year}ACS/{fn}"
        download(url, pth)


def reformat_acs_vars(col):
    """Convert variable names to the same format used by the Census Detailed Tables API.

    See <https://api.census.gov/data/2019/acs/acs5/variables.html> for variable descriptions


    Parameters
    ----------
    col : str
        column name to adjust

    Returns
    -------
    str
        reformatted column name
    """
    pieces = col.split("e")
    formatted = pieces[0] + "_" + pieces[1].rjust(3, "0") + "E"
    return formatted


def convert_census_gdb(
    file,
    year=None,
    layers=None,
    level="bg",
    save_intermediate=True,
    combine=True,
    output_dir=".",
):
    """Convert file geodatabases from Census into (set of) parquet files.

    Parameters
    ----------
    file : str
        path to file geodatabase
    year : str
        year that the data should be named by. If none, will try to infer from the filename
        based on convention from the Census Bureau FTP server
    layers : list, optional
        set of layers to extract from geodatabase. If none (default), all layers will be extracted
    level : str, optional
        geographic level of data ('bg' for blockgroups or 'tr' for tract), by default "bg"
    save_intermediate : bool, optional
        if true, each layer will be stored separately as a parquet file, by default True
    combine : bool, optional
        whether to store and concatenate intermediate dataframes, default is True
    output_dir : str, optional
        path to directory where parquet files will be written, by default "."
    """
    try:
        import pyogrio as ogr
    except ImportError:
        raise ImportError(
            "this function requires the `pyogrio` package\n" "`conda install pyogrio`"
        )
    if not layers:  # grab them all except the metadata
        year_suffix = file.split(".")[0].split("_")[1][-2:]
        meta_str = f"{level.upper()}_METADATA_20{year_suffix}"
        layers = [layer[0] for layer in ogr.list_layers(file)]
        if meta_str in layers:
            layers.remove(meta_str)
    if (
        not year
    ):  # make a strong assumption about the name of the file coming from census
        year = file.split("_")[1]
    tables = []
    for i in layers:
        print(i)
        df = ogr.read_dataframe(file, layer=i).set_index("GEOID")
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

    inflation = pd.read_csv(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "bls.csv"
        )
    )
    if base_year not in inflation.YEAR.unique():
        warn(
            f"Unable to find local adjustment year for {base_year}. Attempting from online data"
        )
        try:
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
