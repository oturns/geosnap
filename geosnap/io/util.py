import os
from warnings import warn
from urllib.error import HTTPError

import pandas as pd
from shapely import wkb, wkt

from .._data import _convert_gdf as convert_gdf


def _deserialize_wkb(str):
    return wkb.loads(str, hex=True)


def _deserialize_wkt(str):
    return wkt.loads(str)


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
    try:
        remote = pd.read_excel(
            "https://www.bls.gov/cpi/research-series/allitems.xlsx", skiprows=5
        )

        if not inflation.equals(remote):
            warn(
                "Warning: local inflation adjustment table does not match remote copy from BLS!"
            )
    except Exception:
        warn(
            "Unable to read inflation adjustment table from BLS. Falling back to local copy"
        )

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
