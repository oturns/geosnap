"""
Data reader for longitudinal databases LTDB, geolytics NCDB and NHGIS
"""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import zipfile
import matplotlib.pyplot as plt
import osmnx as ox

# Variables

_package_directory = os.path.dirname(os.path.abspath(__file__))
_variables = pd.read_csv(os.path.join(_package_directory, "variables.csv"))
_geo_store = pd.HDFStore(os.path.join(_package_directory, "us_geo.h5"), "r")
_store = pd.HDFStore(os.path.join(_package_directory, "data.h5"), "a")

_states = _geo_store["states"]
_states = gpd.GeoDataFrame(_states)
_states[~_states.geoid.isin(["60", "66", "69", "72", "78"])]
_states.crs = {"init": "epsg:4326"}
#_states = _states.set_index("geoid")

_counties = _geo_store["counties"]
_counties = gpd.GeoDataFrame(_counties)
_counties.crs = {"init": "epsg:4326"}
#_counties = _counties.set_index("geoid")

_tracts = _geo_store["tracts"]
_tracts = gpd.GeoDataFrame(_tracts)
_tracts.crs = {"init": "epsg:4326"}

#_tracts = _tracts.set_index("geoid")

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
            converters={
                0: str,
                "placefp10": str
            },
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
        try:
            df = _adjust_inflation(df, inflate_cols, year)
        except:
            pass

        return df

    # read in Brown's LTDB data, both the sample and fullcount files for each
    # year population, housing units & occupied housing units appear in both
    # "sample" and "fullcount" files-- currently drop sample and keep fullcount

    sample70 = _ltdb_reader(
        sample_zip,
        "ltdb_std_all_sample/ltdb_std_1970_sample.csv",
        dropcols=["POP70SP1", "HU70SP", "OHU70SP"],
        year=1970,
    )

    fullcount70 = _ltdb_reader(
        fullcount_zip, "LTDB_Std_1970_fullcount.csv", year=1970)

    sample80 = _ltdb_reader(
        sample_zip,
        "ltdb_std_all_sample/ltdb_std_1980_sample.csv",
        dropcols=["pop80sf3", "pop80sf4", "hu80sp", "ohu80sp"],
        year=1980,
    )

    fullcount80 = _ltdb_reader(
        fullcount_zip, "LTDB_Std_1980_fullcount.csv", year=1980)

    sample90 = _ltdb_reader(
        sample_zip,
        "ltdb_std_all_sample/ltdb_std_1990_sample.csv",
        dropcols=["POP90SF3", "POP90SF4", "HU90SP", "OHU90SP"],
        year=1990,
    )

    fullcount90 = _ltdb_reader(
        fullcount_zip, "LTDB_Std_1990_fullcount.csv", year=1990)

    sample00 = _ltdb_reader(
        sample_zip,
        "ltdb_std_all_sample/ltdb_std_2000_sample.csv",
        dropcols=["POP00SF3", "HU00SP", "OHU00SP"],
        year=2000,
    )

    fullcount00 = _ltdb_reader(
        fullcount_zip, "LTDB_Std_2000_fullcount.csv", year=2000)

    sample10 = _ltdb_reader(
        sample_zip, "ltdb_std_all_sample/ltdb_std_2010_sample.csv", year=2010)

    # join the sample and fullcount variables into a single df for the year
    ltdb_1970 = sample70.drop(columns=['year']).join(
        fullcount70.iloc[:, 7:], how="left")
    ltdb_1980 = sample80.drop(columns=['year']).join(
        fullcount80.iloc[:, 7:], how="left")
    ltdb_1990 = sample90.drop(columns=['year']).join(
        fullcount90.iloc[:, 7:], how="left")
    ltdb_2000 = sample00.drop(columns=['year']).join(
        fullcount00.iloc[:, 7:], how="left")
    ltdb_2010 = sample10

    df = pd.concat(
        [ltdb_1970, ltdb_1980, ltdb_1990, ltdb_2000, ltdb_2010], sort=True)

    renamer = dict(
        zip(_variables['ltdb'].tolist(), _variables['variable'].tolist()))

    df.rename(renamer, axis="columns", inplace=True)

    # compute additional variables from lookup table
    for row in _variables['formula'].dropna().tolist():
        df.eval(row, inplace=True)

    # downcast numeric types to save memory
    df_float = df.select_dtypes(include=['float'])
    converted_float = df_float.apply(pd.to_numeric, downcast='float')

    df = df.round(0)

    keeps = df.columns[df.columns.isin(_variables['variable'].tolist())]
    df = df[keeps]

    _store["ltdb"] = df

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

    ncdb_vars = _variables["ncdb"].dropna()[1:].values

    df = pd.read_csv(
        filepath,
        na_values=["", " ", 99999, -999],
        engine='c',
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
        df, stubnames=ncdb_vars, i="GEO2010", j="year",
        suffix="(7|8|9|0|1|2)").reset_index()

    df["year"] = df["year"].replace({
        7: 1970,
        8: 1980,
        9: 1990,
        0: 2000,
        1: 2010,
        2: 2010
    })

    df = df.groupby(["GEO2010", "year"]).first()

    mapper = dict(zip(_variables.ncdb, _variables.variable))

    df.reset_index(inplace=True)

    df = df.rename(mapper, axis="columns")

    df = df.set_index("geoid")

    for row in _variables['formula'].dropna().tolist():
        df.eval(row, inplace=True)

    df = df[[_variables.variable.tolist().append('year')]]

    # downcast numeric types to save memory
    df_float = df.select_dtypes(include=['float'])
    converted_float = df_float.apply(pd.to_numeric, downcast='float')

    df = df.round(0)

    keeps = df.columns[df.columns.isin(_variables['variable'].tolist())]
    df = df[keeps]

    _store["ncdb"] = df

    return df


# TODO NHGIS reader


class Dataset(object):
    """
    Container for storing neighborhood data and analytics for a study
    region
    """

    def __init__(self,
                 name,
                 source,
                 states=None,
                 counties=None,
                 boundary=None,
                 **kwargs):

        # If a boundary is passed, use it to clip out the appropriate tracts
        self.name = name
        if boundary is not None:

            self.boundary = boundary
            self.tracts = _tracts[_tracts.set_geometry("point").within(
                self.boundary.unary_union)]
            self.tracts = ox.project_gdf(self.tracts)
            self.counties = ox.project_gdf(_counties[_counties.geoid.isin(
                self.tracts.geoid.str[0:5])])
            self.states = ox.project_gdf(_states[_states.geoid.isin(
                self.tracts.geoid.str[0:2])])

        # If county and state lists are passed, first filter tracts by state, then by county
        else:
            assert states
            statelist = []
            if isinstance(states, (list, )):
                statelist.extend(states)
            else:
                statelist.append(states)
            countylist = []
            if isinstance(counties, (list, )): countylist.extend(counties)
            else: countylist.append(counties)
            geo_filter = {'state': statelist, 'county': countylist}
            fips = []
            for state in geo_filter['state']:
                if counties is not None:
                    for county in geo_filter['county']:
                        fips.append(state + county)
                else:
                    fips.append(state)
            self.fips = fips
            self.states = _states[_states.index.isin(statelist)]
            self.counties = _counties[_counties.geoid.isin(countylist)]
            if counties is not None:
                self.tracts = _tracts[_tracts.geoid.str[:5].isin(fips)]
            else:
                self.tracts = _tracts[_tracts.geoid.str[:2].isin(fips)]

        if source in ["ltdb", "ncdb", "nhgis"]:
            _df = _store[source]
        elif source == "external":
            _df = data
        else:
            raise ValueError(
                "source must be one of 'ltdb', 'ncdb', 'nhgis', 'external'")

        self.data = _df[_df.index.isin(self.tracts.index)]

    def plot(self,
             column=None,
             year=2015,
             ax=None,
             plot_counties=True,
             **kwargs):
        """
        convenience function for plotting tracts in the metro area
        """
        if ax is not None:
            ax = ax
        else:
            fig, ax = plt.subplots(figsize=(15, 15))
            colname = column.replace("_", " ")
            colname = colname.title()
            plt.title(
                self.name + ": " + colname + ", " + str(year), fontsize=20)
            plt.axis("off")

        ax.set_aspect("equal")
        plotme = self.tracts.join(
            self.data[self.data.year == year], how="left")
        plotme = plotme.dropna(subset=[column])
        plotme.plot(column=column, alpha=0.8, ax=ax, **kwargs)

        if plot_counties is True:
            self.counties.plot(
                edgecolor="#5c5353",
                linewidth=0.8,
                facecolor="none",
                ax=ax,
                **kwargs)

        return ax


# Utilities


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
        "https://www.bls.gov/cpi/research-series/allitems.xlsx", skiprows=6)
    inflation.columns = inflation.columns.str.lower()
    inflation.columns = inflation.columns.str.strip(".")
    inflation = inflation.dropna(subset=["year"])

    inflator = {
        2015: inflation[inflation.year == 2015]["avg"].values[0],
        2010: inflation[inflation.year == 2010]["avg"].values[0],
        2000: inflation[inflation.year == 2000]["avg"].values[0],
        1990: inflation[inflation.year == 1990]["avg"].values[0],
        1980: inflation[inflation.year == 1980]["avg"].values[0],
        1970:
        63.9,  # https://www2.census.gov/programs-surveys/demo/tables/p60/249/CPI-U-RS-Index-2013.pdf
    }

    df = df.copy()
    df[columns].apply(lambda x: x * (inflator[2015] / inflator[base_year]))

    return df
