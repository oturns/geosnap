"""Utility functions."""
import pandas as pd
from shapely import wkb, wkt
import geopandas as gpd
import multiprocessing


def _deserialize_wkb(str):
    return wkb.loads(str, hex=True)


def _deserialize_wkt(str):
    return wkt.loads(str)


def convert_gdf(df):
    """Convert DataFrame to GeoDataFrame.

    DataFrame to GeoDataFrame by converting wkt/wkb geometry representation
    back to Shapely object.

    Parameters
    ----------
    df : pandas.DataFrame
        dataframe with column named either "wkt" or "wkb" that stores
        geometric information as well-known text or well-known binary,
        (hex encoded) respectively.

    Returns
    -------
    gpd.GeoDataFrame
        geodataframe with converted `geometry` column.

    """
    df = df.copy()
    df.reset_index(inplace=True, drop=True)

    if 'wkt' in df.columns.tolist():
        with multiprocessing.Pool() as P:
            df['geometry'] = P.map(_deserialize_wkt, df['wkt'])
        df = df.drop(columns=['wkt'])

    else:
        with multiprocessing.Pool() as P:
            df['geometry'] = P.map(_deserialize_wkb, df['wkb'])
        df = df.drop(columns=['wkb'])

    df = gpd.GeoDataFrame(df)
    df.crs = {"init": "epsg:4326"}

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
    inflation = pd.read_excel(
        "https://www.bls.gov/cpi/research-series/allitems.xlsx", skiprows=6)
    inflation.columns = inflation.columns.str.lower()
    inflation.columns = inflation.columns.str.strip(".")
    inflation = inflation.dropna(subset=["year"])
    inflator = inflation.groupby('year')['avg'].first().to_dict()
    inflator[1970] = 63.9

    df = df.copy()
    updated = df[columns].apply(lambda x: x * (inflator[base_year] / inflator[
        given_year]))
    df.update(updated)

    return df
