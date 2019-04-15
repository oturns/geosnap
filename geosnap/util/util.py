import pandas as pd
from shapely import wkb, wkt
import geopandas as gpd

def convert_gdf(df):
    df = df.copy()
    df.reset_index(inplace=True, drop=True)
    if 'wkt' in df.columns.tolist():
        df['geometry'] = df.wkt.apply(wkt.loads)
        df = df.drop(columns=['wkt'])
    else:
        df['geometry'] = df.wkb.apply(lambda x: wkb.loads(x, hex=True))
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
    updated = df[columns].apply(lambda x: x * (inflator[base_year] / inflator[given_year]))
    df.update(updated)

    return df
