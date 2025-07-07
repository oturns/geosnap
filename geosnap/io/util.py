import os
import pathlib
from urllib.error import HTTPError
from warnings import warn

import geopandas as gpd
import pandas as pd
import pooch
from tqdm.auto import tqdm


def get_census_gdb(years=None, geom_level="blockgroup", output_dir=".", protocol="ftp"):
    """Fetch geodatabase of ACS demographic profile from the Census bureau server.

    NOTE: Recommended to use `convert_census_gdb` to read/convert files directly from
    the Census server


    Parameters
    ----------
    years : list, optional
        set of years to download (2010 onward), defaults to 2010-2019
    geom_level : str, optional
        geographic unit to download (tract or blockgroup), by default "blockgroup"
    output_dir : str, optional
        output directory to write files, by default "."
    protocol:
        whether to download over ftp or http. ftp is generally more reliable

    Returns
    -------
    None
    """
    levels = {"blockgroup": "bg", "tract": "tract"}

    if not years:
        years = range(2010, 2020)
    for year in years:
        fn = f"ACS_{year}_5YR_{levels[geom_level].upper()}.gdb.zip"
        pth = pathlib.PurePath(output_dir, fn)

        if year in [2010, 2011]:
            if geom_level == "blockgroup":
                raise ValueError(f"blockgroup data not available for {year}") from None
            fn = f"{year}_ACS_5YR_{geom_level.capitalize()}.gdb.zip"
            out_fn = f"ACS_{year}_5YR_{levels[geom_level].upper()}.gdb.zip"
            pth = pathlib.PurePath(output_dir, out_fn)
        urls = {
            "ftp": f"ftp://ftp2.census.gov/geo/tiger/TIGER_DP/{year}ACS/{fn}",
            "https": f"https://www2.census.gov/geo/tiger/TIGER_DP/{year}ACS/{fn}",
        }
        if protocol not in urls.keys():
            raise ValueError("`protocol` must be either 'https' or 'ftp'")
        pooch.retrieve(urls[protocol], None, progressbar=True, fname=fn, path=pth)


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
    year,
    level,
    gdb_path=None,
    layers=None,
    save_intermediate=True,
    overwrite=False,
    combine=True,
    output_dir=".",
    npartitions=16,
):
    """Convert a geodatabase from Census into parquet files with standardized columns.

    Parameters
    ----------

    year : str, required
        year that the data should be named by. If none, will try to infer from the
        filename
        based on convention from the Census Bureau FTP server
    level : str, required
        geographic level of data ('bg' for blockgroups or 'tr' for tract),
        path to file geodatabase
    layers : list, optional
        set of layers to extract from geodatabase. If none (default), all layers will be
        extracted
    gdf_path: str
        path to geodatabase. If none is provided, data will be read directly from the
        Census server at <https://www2.census.gov/geo/tiger/TIGER_DP/>
    save_intermediate : bool, optional
        if true, each layer will be stored separately as a parquet file, by default True
    overwrite: bool
        whether to overwrite existing intermediate files in the output directory
        (default is False)
    combine : bool, optional
        whether to store and concatenate intermediate dataframes, default is True.
        If True, the combined file will be stored as
    output_dir : str, optional
        path to directory where parquet files will be written, by default "."

    Returns
    -------
    None
        If save_intermediate is True, parquet files will be written out for each layer in
        the output directory. If combined is True, the layers will be concatenated and
        the resulting dataframe  f"acs_demographic_profile_{year}_{level}.parquet" will
        be placed in the output directory.
    """
    try:
        import pyogrio as ogr
    except ImportError as e:
        raise Exception(
            "This function requires the `pyogrio` package\n" "`conda install pyogrio`"
        ) from e
    import dask_geopandas as dgpd

    if gdb_path is None:
        warn("No `gdb_path` given. Data will be pulled from the Census server")
        gdb_path = f"https://www2.census.gov/geo/tiger/TIGER_DP/{year}ACS/ACS_{year}_5YR_{level.upper()}.gdb.zip"
    if layers is None:  # grab them all except the metadata
        year_suffix = year[-2:]
        meta_str = f"{level.upper()}_METADATA_20{year_suffix}"
        layers = [layer[0] for layer in ogr.list_layers(gdb_path)]
        if meta_str in layers:
            layers.remove(meta_str)

    tables = list()
    existing_files = os.listdir(output_dir)
    for i in tqdm(layers):
        print(i)

        output_fn = f"acs_{year}_{i}_{level}.parquet"
        if output_fn in existing_files and overwrite is False:
            warn(
                f"layer {i} is already present in the output directory. To overwrite, pass `overwrite=True`"
            )
            if combine:
                if "ACS_" in i:  # only the geoms have the ACS prefix
                    # need to read in with geopandas to get the geoms
                    df = gpd.read_parquet(pathlib.PurePath(output_dir, output_fn))
                else:
                    df = pd.read_parquet(pathlib.PurePath(output_dir, output_fn))
                    df.index = df.index.str.replace("14000US", "")  # remove prefix
                    df.index = df.index.str.replace(
                        "15000US", ""
                    )  # remove prefix for bgs
                tables.append(df)
        else:
            df = (
                dgpd.read_file(gdb_path, layer=i, npartitions=npartitions)
                .compute()
                .set_index("GEOID")
            )
            if "ACS_" not in i:  # only the geoms have the ACS prefix
                df = df[df.columns[df.columns.str.contains("e")]]
                df.columns = pd.Series(df.columns).apply(reformat_acs_vars)
            df = df.dropna(axis=1, how="all")
            df.index = df.index.str.replace("14000US", "")  # remove prefix for tracts
            df.index = df.index.str.replace("15000US", "")  # remove prefix for bgs
            if combine:
                tables.append(df)
            if save_intermediate:
                df.to_parquet(pathlib.PurePath(output_dir, output_fn))
    if combine:
        df = pd.concat(tables, axis=1)
        df = gpd.GeoDataFrame(df)
        df.to_parquet(
            pathlib.PurePath(
                output_dir, f"acs_demographic_profile_{year}_{level}.parquet"
            )
        )


def get_lehd(dataset="wac", state="dc", year=2015, version=8):
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
    version : int
        which version of LODES to query. Options include 5,7 and 8, which are keyed
        to census 2000, 2010, and 2020 blocks respectively

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
    url = f"https://lehd.ces.census.gov/data/lodes/LODES{version}/{state}/{dataset}/{state}_{dataset}_S000_JT00_{year}.csv.gz"
    try:
        df = pd.read_csv(url, converters={"w_geocode": str, "h_geocode": str})
    except HTTPError as e:
        raise ValueError(
            "Unable to retrieve LEHD data. Check your internet connection "
            "and that the state/year combination you specified is available"
        ) from e
    df = df.rename({"w_geocode": "geoid", "h_geocode": "geoid"}, axis=1)
    df.rename(renamer, axis="columns", inplace=True)
    df = df.set_index("geoid")

    return df


def adjust_inflation(df, columns, given_year, base_year):
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
    try:
        inflation = pd.read_csv(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "inflation.csv")
        )
    except FileNotFoundError:
        warn("Unable to read local inflation adjustment file. Streaming from BLS")
        inflation = pd.read_excel(
            "https://www.bls.gov/cpi/research-series/allitems.xlsx", skiprows=5
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
        except Exception as e:
            raise ValueError(f"Unable to find adjustment values for {base_year}") from e

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


def process_acs(df):
    """Calculate variables from the geosnap codebook to match the LTDB veriable set.

    This function expects a massive input dataframe generated by downloading all
    necessary varibales from the geosnap codebook. The best way to get all these
    variables is to use the `geosnap.io.process_census_gdb` function. Note that
    calling this function on the full dataset requires *a lot* of memory.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame contining raw census data (as processed by `fetch_acs`).
        (expects GEOID as a column, not as index)

    Returns
    -------
    geopandas.GeoDataFrame
        a geodataframe holding
    """
    from .._data import DataStore

    geoms = df["geometry"].copy()

    _variables = pd.read_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "variables.csv")
    )

    evalcols = [_normalize_relation(rel) for rel in _variables["acs"].dropna().tolist()]
    varnames = _variables.dropna(subset=["acs"])["variable"]
    evals = [parts[0] + "=" + parts[1] for parts in zip(varnames, evalcols)]

    tempkeeps = [col for col in df.columns if col in evalcols]
    df = df[tempkeeps + ["geometry", "GEOID"]]
    df.set_index("GEOID", inplace=True)
    df = df.apply(lambda x: pd.to_numeric(x, errors="coerce"), axis=1)
    # compute additional variables from lookup table
    for row in tqdm(evals):
        try:
            df.eval(row, inplace=True)
        except Exception as e:
            print(row + " " + str(e))
    for row in _variables["formula"].dropna().tolist():
        try:
            df.eval(row, inplace=True, engine="python")
        except Exception as e:
            print(str(row) + " " + str(e))
    keeps = [col for col in df.columns if col in _variables.variable.tolist()]
    df = df[keeps]
    df["geometry"] = geoms.values
    df = gpd.GeoDataFrame(df)
    return df


def _process_columns(input_columns):
    # prepare by taking all sum-of-columns as lists
    outcols_processing = [s.replace("+", ",") for s in input_columns]
    outcols = []
    while outcols_processing:  # stack
        col = outcols_processing.pop()
        col = col.replace("-", ",").replace("(", "").replace(")", "")
        col = [c.strip() for c in col.split(",")]  # get each part
        if len(col) > 1:  # if there are many parts
            col, *rest = col  # put the rest back
            for r in rest:
                outcols_processing.insert(0, r)
        else:
            col = col[0]
        if ":" in col:  # if a part is a range
            start, stop = col.split(":")  # split the range
            stem = start[:-3]
            start = int(start[-3:])
            stop = int(stop)
            # and expand the range
            cols = [stem + str(col).rjust(3, "0") for col in range(start, stop + 1)]
            outcols.extend(cols)
        else:
            outcols.append(col)
    return outcols


def _normalize_relation(relation):
    parts = relation.split("+")
    if len(parts) == 1:
        if ":" not in relation:
            return relation
        else:
            relation = parts[0]
    else:
        relation = "+".join([_normalize_relation(rel.strip()) for rel in parts])
    if ":" in relation:
        start, stop = relation.split(":")
        stem = start[:-3]
        start = int(start[-3:])
        stop = int(stop)
        # and expand the range
        cols = [stem + str(col).rjust(3, "0") for col in range(start, stop + 1)]
        return "+".join(cols)
    return relation


if __name__ == "__main__":
    get_lehd()
    adjust_inflation()
