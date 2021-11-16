"""Tools for creating and manipulating neighborhood datasets."""

import os
import pathlib
from warnings import warn

import geopandas as gpd
import pandas as pd
from appdirs import user_data_dir

appname = "geosnap"
appauthor = "geosnap"
data_dir = user_data_dir(appname, appauthor)

def _fetcher(local_path, remote_path, warning_msg):
    try:
        t = gpd.read_parquet(local_path)
    except FileNotFoundError:
        warn(warning_msg)
        t = gpd.read_parquet(remote_path, storage_options={"anon": True})

    return t


class _Map(dict):
    """tabbable dict."""

    def __init__(self, *args, **kwargs):
        super(_Map, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.iteritems():
                    self[k] = v

        if kwargs:
            for k, v in kwargs.iteritems():
                self[k] = v

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(_Map, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(_Map, self).__delitem__(key)
        del self.__dict__[key]


class DataStore:
    """Storage for geosnap data. Currently supports US Census data.

        Unless otherwise noted, data are collected from the U.S. Census Bureau's TIGER/LINE Files
        https://www.census.gov/cgi-bin/geo/shapefiles/index.php?year=2018 and converted to
        parquet files.

    """

    def __init__(self):
        self

    def __dir__(self):

        atts = [
            "acs",
            "blocks_2000",
            "blocks_2010",
            "codebook",
            "counties",
            "ltdb",
            "msa_definitions",
            "msas",
            "ncdb",
            "states",
            "show_data_dir",
            "tracts_1990",
            "tracts_2000",
            "tracts_2010",
        ]

        return atts

    def show_data_dir(self):
        """Print the location of the local geosnap data storage directory.

        Returns
        -------
        string
            location of local storage directory.
        """
        print(data_dir)
        return data_dir

    def acs(self, year=2018, level="tract", states=None):
        """American Community Survey Data.

        Parameters
        ----------
        year : str
            vingage of ACS release.
        level : str
            geographic level
        states : list, optional
            subset of states (as 2-digit fips) to return 

        Returns
        -------
        geopandas.GeoDataFrame
            geodataframe of ACS data indexed by FIPS code
        """
        local_path = pathlib.Path(data_dir, "acs", f"acs_{year}_{level}.parquet")
        remote_path = f"s3://spatial-ucr/census/acs/acs_{year}_{level}.parquet"
        msg = "Streaming data from S3. Use `geosnap.io.store_acs()` to store the data locally for better performance"
        t = _fetcher(local_path, remote_path, msg)
        t = t.reset_index().rename(columns={"GEOID": "geoid"})

        if states:
            t = t[t.geoid.str[:2].isin(states)]
        t["year"] = year
        return t

    def blocks_2000(self, states=None, fips=None):
        """Census blocks for 2000.

        Parameters
        ----------
        states : list-like
            list of state fips codes to return as a datafrrame.

        Returns
        -------
        type
        pandas.DataFrame or geopandas.GeoDataFrame
            2000 blocks as a geodataframe or as a dataframe with geometry
            stored as well-known binary on the 'wkb' column.

        """
        msg = (
            "Unable to locate local census 2010 block data. Streaming instead.\n"
            "If you plan to use census data repeatedly you can store it locally "
            "with the io.store_blocks_2010 function for better performance"
        )
        if isinstance(states, (str, int)):
            states = [states]
        blks = {}
        for state in states:
            local = pathlib.Path(data_dir, "blocks_2000", f"{state}.parquet")
            remote = f"s3://spatial-ucr/census/blocks_2000/{state}.parquet"
            blks[state] = _fetcher(local, remote, msg)

            if fips:
                blks[state] = blks[state][blks[state]["geoid"].str.startswith(fips)]

            blks[state]["year"] = 2000
        blocks = list(blks.values())
        blocks = gpd.GeoDataFrame(pd.concat(blocks, sort=True))

        return blocks

    def blocks_2010(self, states=None, fips=None):
        """Census blocks for 2010.

        Parameters
        ----------
        states : list-like
            list of state fips codes to return as a datafrrame.

        Returns
        -------
        type
        pandas.DataFrame or geopandas.GeoDataFrame
            2010 blocks as a geodataframe or as a dataframe with geometry
            stored as well-known binary on the 'wkb' column.

        """
        msg = (
            "Unable to locate local census 2010 block data. Streaming instead.\n"
            "If you plan to use census data repeatedly you can store it locally "
            "with the io.store_blocks_2010 function for better performance"
        )
        if isinstance(states, (str, int)):
            states = [states]
        blks = {}
        for state in states:
            local = pathlib.Path(data_dir, "blocks_2010", f"{state}.parquet")
            remote = f"s3://spatial-ucr/census/blocks_2010/{state}.parquet"
            blks[state] = _fetcher(local, remote, msg)

            if fips:
                blks[state] = blks[state][blks[state]["geoid"].str.startswith(fips)]

            blks[state]["year"] = 2010
        blocks = list(blks.values())
        blocks = gpd.GeoDataFrame(pd.concat(blocks, sort=True))

        return blocks

    def tracts_1990(self, states=None):
        """Nationwide Census Tracts as drawn in 1990 (cartographic 500k).

        Parameters
        ----------
        states : list-like
            list of state fips to subset the national dataframe

        Returns
        -------
        pandas.DataFrame or geopandas.GeoDataFrame
            1990 tracts as a geodataframe or as a dataframe with geometry
            stored as well-known binary on the 'wkb' column.

        """
        msg = "Streaming data from S3. Use `geosnap.io.store_census() to store the data locally for better performance"
        local = pathlib.Path(data_dir, "tracts_1990_500k.parquet")
        remote = "s3://spatial-ucr/census/tracts_cartographic/tracts_1990_500k.parquet"
        t = _fetcher(local, remote, msg)
        if states:
            t = t[t.geoid.str[:2].isin(states)]
        t["year"] = 1990

        return t

    def tracts_2000(self, states=None):
        """Nationwide Census Tracts as drawn in 2000 (cartographic 500k).

        Parameters
        ----------
        states : list-like
            list of state fips to subset the national dataframe

        Returns
        -------
        pandas.DataFrame or geopandas.GeoDataFrame
            2000 tracts as a geodataframe or as a dataframe with geometry
            stored as well-known binary on the 'wkb' column.

        """
        local = pathlib.Path(data_dir, "tracts_2000_500k.parquet")
        remote = "s3://spatial-ucr/census/tracts_cartographic/tracts_2000_500k.parquet"
        msg = "Streaming data from S3. Use `geosnap.io.store_census() to store the data locally for better performance"
        t = _fetcher(local, remote, msg)
        if states:
            t = t[t.geoid.str[:2].isin(states)]
        t["year"] = 2000

        return t

    def tracts_2010(
        self, states=None,
    ):
        """Nationwide Census Tracts as drawn in 2010 (cartographic 500k).

        Parameters
        ----------
        states : list-like
            list of state fips to subset the national dataframe

        Returns
        -------
        pandas.DataFrame or geopandas.GeoDataFrame
            2010 tracts as a geodataframe or as a dataframe with geometry
            stored as well-known binary on the 'wkb' column.

        """
        msg = "Streaming data from S3. Use `geosnap.io.store_census() to store the data locally for better performance"
        local = pathlib.Path(data_dir, "tracts_2010_500k.parquet")
        remote = "s3://spatial-ucr/census/tracts_cartographic/tracts_2010_500k.parquet"
        t = _fetcher(local, remote, msg)

        if states:
            t = t[t.geoid.str[:2].isin(states)]
        t["year"] = 2010
        return t

    def msas(self):
        """Metropolitan Statistical Areas as drawn in 2020.

        Data come from the U.S. Census Bureau's most recent TIGER/LINE files
        https://www.census.gov/cgi-bin/geo/shapefiles/index.php?year=2020&layergroup=Core+Based+Statistical+Areas


        Returns
        -------
        pandas.DataFrame or geopandas.GeoDataFrame
            2010 MSAs as a geodataframe or as a dataframe with geometry
            stored as well-known binary on the 'wkb' column.

        """
        local = pathlib.Path(data_dir, "msas.parquet")
        remote = "s3://spatial-ucr/census/administrative/msas.parquet"
        msg = "Streaming data from S3. Use `geosnap.io.store_census() to store the data locally for better performance"
        t = _fetcher(local, remote, msg)
        t = t.sort_values(by="name")
        return t

    def states(self):
        """States.

        Returns
        -------
        pandas.DataFrame or geopandas.GeoDataFrame
            US States as a geodataframe or as a dataframe with geometry
            stored as well-known binary on the 'wkb' column.

        """
        local = pathlib.Path(data_dir, "states.parquet")
        remote = "s3://spatial-ucr/census/administrative/states.parquet"
        msg = "Streaming data from S3. Use `geosnap.io.store_census() to store the data locally for better performance"

        t = _fetcher(local, remote, msg)
        return t

    def counties(self):
        """Nationwide counties as drawn in 2010.

        Parameters
        ----------
        convert : bool
            if True, return geodataframe, else return dataframe (the default is True).

        Returns
        -------
        geopandas.GeoDataFrame
            2010 counties as a geodataframe or as a dataframe with geometry
            stored as well-known binary on the 'wkb' column.

        """
        local= pathlib.Path(data_dir, "counties.parquet")
        remote = "s3://spatial-ucr/census/administrative/counties.parquet"
        msg = "Streaming data from S3. Use `geosnap.io.store_census() to store the data locally for better performance"
        t = _fetcher(local, remote, msg)
        return t

    def msa_definitions(self):
        """2010 Metropolitan Statistical Area definitions.

        Data come from the U.S. Census Bureau's most recent delineation files, available at
        https://www.census.gov/geographies/reference-files/time-series/demo/metro-micro/delineation-files.html

        Returns
        -------
        pandas.DataFrame.
            dataframe that stores state/county --> MSA crosswalk definitions.

        """
        local = pathlib.Path(data_dir, "msa_definitions.parquet")
        remote = "s3://spatial-ucr/census/administrative/msa_definitions.parquet"
        msg = "Streaming data from S3. Use `geosnap.io.store_census() to store the data locally for better performance"
        try:
            t = pd.read_parquet(local)
        except FileNotFoundError:
            warn(msg)
            t = pd.read_parquet(remote, storage_options={"anon": True})

        return t

    def ltdb(self):
        """Longitudinal Tract Database (LTDB).

        Returns
        -------
        pandas.DataFrame or geopandas.GeoDataFrame
            LTDB as a long-form geo/dataframe

        """
        try:
            return pd.read_parquet(pathlib.Path(data_dir, "ltdb.parquet"))
        except KeyError:
            print(
                "Unable to locate LTDB data. Try saving the data again "
                "using the `store_ltdb` function"
            )

    def ncdb(self):
        """Geolytics Neighborhood Change Database (NCDB).

        Returns
        -------
        pandas.DataFrarme
            NCDB as a long-form dataframe

        """
        try:
            return pd.read_parquet(pathlib.Path(data_dir, "ncdb.parquet"))
        except KeyError:
            print(
                "Unable to locate NCDB data. Try saving the data again "
                "using the `store_ncdb` function"
            )

    def codebook(self):
        """Codebook.

        Returns
        -------
        pandas.DataFrame
            codebook that stores variable names, definitions, and formulas.

        """
        return pd.read_csv(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "io/variables.csv")
        )


datasets = DataStore()
