"""'
Data reader for longitudinal databases LTDB, geolytics NCDB and NHGIS
"""

import os
import numpy as np
import pandas as pd
import warnings
import geopandas as gpd
import glob
import zipfile
from shapely.geometry import Point, LineString, MultiLineString


# LTDB importer


def read_ltdb(sample, fullcount):
    """
    Read data from Brown's Longitudinal Tract Database (LTDB) and store it for later use.

    Parameters
    ----------
    sample : str
        file path of the zip file containing the standard Sample CSV files downloaded from
        https://s4.ad.brown.edu/projects/diversity/Researcher/LTBDDload/Default.aspx

    fullcount: str
        file path of the zip file containing the standard Fullcount CSV files downloaded from
        https://s4.ad.brown.edu/projects/diversity/Researcher/LTBDDload/Default.aspx

    Returns
    -------
    DataFrame

    """
    sample_zip = zipfile.ZipFile(sample)
    fullcount_zip = zipfile.ZipFile(fullcount)

    def _ltdb_reader(path, file, year, dropcols=None):

        df = pd.read_csv(
            path.open(file),
            na_values=["", " ", 99999, -999],
            converters={0: str, "placefp10": str},
            low_memory=False,
            encoding="latin1",
        )

        if dropcols:
            df.drop(dropcols, axis=1, inplace=True)
        df.columns = df.columns.str.lower()
        names = df.columns.values.tolist()
        names[0] = "geoid"
        newlist = []

        # ignoring the first 4 columns, remove year suffix from column names
        for name in names[4:]:
            newlist.append(name[:-2])
        colnames = names[:4] + newlist
        df.columns = colnames

        # prepend a 0 when FIPS is too short
        df["geoid"] = df["geoid"].str.rjust(11, "0")
        df.set_index("geoid", inplace=True)

        df["year"] = year

        inflate_cols = ["mhmval", "mrent", "hinc"]
        df = _adjust_inflation(df, inflate_cols, year)

        return df

    # read in Brown's LTDB data, both the sample and fullcount files for each
    # year population, housing units & occupied housing units appear in both
    # "sample" and "fullcount" files-- currently drop sample and keep fullcount

    sample70 = (
        _ltdb_reader(
            sample_zip,
            "ltdb_std_1970_sample.csv",
            dropcols=["POP70SP1", "HU70SP", "OHU70SP"],
            year=1970,
        ),
    )

    fullcount70 = (
        _ltdb_reader(fullcount_zip, "LTDB_Std_1970_fullcount.csv", year=1970),
    )

    sample80 = (
        _ltdb_reader(
            sample_zip,
            "ltdb_std_1980_sample.csv",
            dropcols=["pop80sf3", "pop80sf4", "hu80sp", "ohu80sp"],
            year=1980,
        ),
    )

    fullcount80 = (
        _ltdb_reader(fullcount_zip, "LTDB_Std_1980_fullcount.csv", year=1980),
    )

    sample90 = (
        _ltdb_reader(
            sample_zip,
            "ltdb_std_1990_sample.csv",
            dropcols=["POP90SF3", "POP90SF4", "HU90SP", "OHU90SP"],
            year=1990,
        ),
    )

    fullcount90 = (
        _ltdb_reader(fullcount_zip, "LTDB_Std_1990_fullcount.csv", year=1990),
    )

    sample00 = (
        _ltdb_reader(
            sample_zip,
            "ltdb_std_2000_sample.csv",
            dropcols=["POP00SF3", "HU00SP", "OHU00SP"],
            year=2000,
        ),
    )

    fullcount00 = (
        _ltdb_reader(fullcount_zip, "LTDB_Std_2000_fullcount.csv", year=2000),
    )

    sample10 = _ltdb_reader(sample_zip, "ltdb_std_2010_sample.csv", year=2010)

    # join the sample and fullcount variables into a single df for the year
    ltdb_1970 = sample70.join(fullcount70.iloc[:, 7:], how="left")
    ltdb_1980 = sample80.join(fullcount80.iloc[:, 7:], how="left")
    ltdb_1990 = sample90.join(fullcount90.iloc[:, 7:], how="left")
    ltdb_2000 = sample00.join(fullcount00.iloc[:, 7:], how="left")
    ltdb_2010 = sample10

    # the 2010 file doesnt have CBSA info, so grab it from the 2000 df
    ltdb_2010["cbsa"] = np.nan
    ltdb_2010.update(other=ltdb_2000["cbsa"], overwrite=True)

    df = pd.concat([ltdb_1970, ltdb_1980, ltdb_1990, ltdb_2000, ltdb_2010], sort=True)

    df = df.set_index("geoid")

    store = pd.HDFStore(os.path.join(package_directory, "data.h5"), "w")
    store["ltdb"] = df

    store.close()

    return df


def read_ncdb(filepath):
    """
    Read data from Geolytics's Neighborhood Change Database (NCDB) and store it for later use.

    Parameters
    ----------
    input_dir : str
        location of the input CSV file extracted from your Geolytics DVD

    Returns
    -------
    DataFrame

    """

    ncdb_vars = variables["ncdb"].dropna()[1:].values

    df = pd.read_csv(
        filepath,
        low_memory=False,
        na_values=["", " ", 99999, -999],
        converters={
            "GEO2010": str,
            "COUNTY": str,
            "COUSUB": str,
            "DIVISION": str,
            "REGION": str,
            "STATE": str,
        },
    )

    cols = df.columns
    fixed = []
    for col in cols:
        if col.endswith("D"):
            fixed.append("D" + col[:-1])
        elif col.endswith("N"):
            fixed.append("N" + col[:-1])
        elif col.endswith("1A"):
            fixed.append(col[:-2] + "2")

    orig = []
    for col in cols:
        if col.endswith("D"):
            orig.append(col)
        elif col.endswith("N"):
            orig.append(col)
        elif col.endswith("1A"):
            orig.append(col)

    df.rename(dict(zip(orig, fixed)), axis="columns", inplace=True)

    df = pd.wide_to_long(
        df, stubnames=ncdb_vars, i="GEO2010", j="year", suffix="(7|8|9|0|1|2)"
    ).reset_index()

    df["year"] = df["year"].replace(
        {7: 1970, 8: 1980, 9: 1990, 0: 2000, 1: 2010, 2: 2010}
    )
    df = df.groupby(["GEO2010", "year"]).first()

    mapper = dict(zip(variables.ncdb, variables.ltdb))

    df.reset_index(inplace=True)

    df = df.rename(mapper, axis="columns")

    df = df.set_index("geoid")

    store = pd.HDFStore(os.path.join(package_directory, "data.h5"), "w")
    store["ncdb"] = df

    store.close()

    return df


# TODO NHGIS reader


# Utilities

package_directory = os.path.dirname(os.path.abspath(__file__))

variables = pd.read_csv(os.path.join(package_directory, "variables.csv"))


def _adjust_inflation(df, columns, base_year):
    """
    Adjust currency data for inflation. Currently, this function generates
    output in 2015 dollars, but this could be parameterized later

    Parameters
    ----------
    df : DataFrame
        Dataframe of historical data
    columns : list-like
        The columns of the dataframe with currency data
    base_year: int
        Base year the data were collected; e.g. to convert data from the 1990
        census to 2015 dollars, this value should be 1990

    Returns
    -------
    type
        DataFrame

    """
    # adjust for inflation
    # get inflation adjustment table from BLS
    inflation = pd.read_excel(
        "https://www.bls.gov/cpi/research-series/allitems.xlsx", skiprows=6
    )
    inflation.columns = inflation.columns.str.lower()
    inflation.columns = inflation.columns.str.strip(".")
    inflation = inflation.dropna(subset=["year"])

    inflator = {
        2015: inflation[inflation.year == 2015]["avg"].values[0],
        2010: inflation[inflation.year == 2010]["avg"].values[0],
        2000: inflation[inflation.year == 2000]["avg"].values[0],
        1990: inflation[inflation.year == 1990]["avg"].values[0],
        1980: inflation[inflation.year == 1980]["avg"].values[0],
        1970: 63.9,  # https://www2.census.gov/programs-surveys/demo/tables/p60/249/CPI-U-RS-Index-2013.pdf
    }

    df = df.copy()
    df[columns].apply(lambda x: x * (inflator[2015] / inflator[base_year]))

    return df


def legacy_to_shapefile(path, year):

    if year == 2000:
        ext = "*.RT"
    elif year == 1990:
        ext = "*.F5"

    # split the point
    def splitPoint(point):
        value = []
        value.append(float(point[:9]) / 1000000)
        value.append(float(point[9:]) / 1000000)
        return value

    # read data from RT2 file and store in dictionary. RT2 file stored the turning point of the lines in RT1
    # key: numbers start with 7;
    # value: geo location
    def readRT2toDic(path):
        fn = glob.glob(os.path.join(path, ext + "2"))[0]
        f = open(fn, "r")
        RT2_dic = {}
        for line in f:
            line = line.strip()
            columns = line.split()
            tps = []
            for index, col in enumerate(columns):
                if index == 1:
                    key = col
                elif index > 2:
                    turningPoint = col[:18]
                    value = splitPoint(turningPoint)  # split the turning point
                    tps.append(value)
            RT2_dic[key] = tps
            return RT2_dic

    # read data from RT1 file and store in an array. RT1 file stores the types, starting coordination, and ending coordination of lines

    def readRT1toArray(path):

        # load RT2 to dictionary
        RT2_dic = readRT2toDic(path)
        fn = glob.glob(os.path.join(path, ext + "1"))[0]
        # fn = '*'+ext+'1'
        f = open(fn, "r")
        feature_info = []
        fips_codes = []
        for line in f:
            line = line.strip()
            columns = line.split()
            linetype = line[55:58]
            fips = line[130:150]
            startPoint = columns[-2]
            endPoint = columns[-1]
            ref = columns[1]  # number starts with 7

            # if road name starts with 'A'
            # if linetype[0] == "A":
            temp = []
            # add start point
            a = splitPoint(startPoint)
            temp.append(a)

            # add turning points if turning points exist
            if ref in RT2_dic:
                tps = RT2_dic[ref]
                temp += tps

            # add end point
            b = splitPoint(endPoint)
            temp.append(b)

            feature_info.append(temp)

            fips_codes.append(fips)

            # feats = {"geometry": feature_info, "fips": fips_codes}

            # gdf = gpd.GeoDataFrame(feats)
        return feature_info, fips_codes

    # A list of features and coordinate pairs
    # A list that will hold each of the Polyline objects
    features, fips_codes = readRT1toArray(path)
    polys = []
    lines = []
    for feature in features:
        lines.append(LineString(feature))
    #     polys.append(MultiLineString(lines))

    feats = {"geometry": lines, "fips": fips_codes}

    gdf = gpd.GeoDataFrame(feats)
    # gs = gpd.GeoSeries(lines)
    # Persist a copy of the Polyline objects using CopyFeatures

    return gdf
