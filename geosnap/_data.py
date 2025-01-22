"""Tools for creating and manipulating neighborhood datasets."""

import os
import pathlib
from warnings import warn

import geopandas as gpd
import pandas as pd
from platformdirs import user_data_dir


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
                for k, v in arg.items():
                    self[k] = v

        if kwargs:
            for k, v in kwargs.items():
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
    """Storage for geosnap data. Currently supports data from several U.S. federal agencies and national research centers."""

    def __init__(self, data_dir="auto", disclaimer=False):
        appname = "geosnap"
        appauthor = "geosnap"

        if data_dir == "auto":
            self.data_dir = user_data_dir(appname, appauthor)
        else:
            self.data_dir = data_dir
        if disclaimer:
            warn(
                "The geosnap data storage class is provided for convenience only. The geosnap developers make no promises "
                "regarding data quality, consistency, or availability, nor are they responsible for any use/misuse of the data. "
                "The end-user is responsible for any and all analyses or applications created with the package."
            )

    def __dir__(self):
        atts = [
            "acs",
            "bea_regions",
            "blocks_2000",
            "blocks_2010",
            "blocks_2020",
            "codebook",
            "counties",
            "ejscreen",
            "ejscreen_codebook",
            "lodes_codebook",
            "ltdb",
            "msa_definitions",
            "msas",
            "naics_definitions",
            "ncdb",
            "nces",
            "nlcd_definitions",
            "seda",
            "states",
            "show_data_dir",
            "tracts_1990",
            "tracts_2000",
            "tracts_2010",
            "tracts_2020",
        ]

        return atts

    def show_data_dir(self, verbose=True):
        """Print the location of the local geosnap data storage directory.

        Returns
        -------
        string
            location of local storage directory.
        """
        if verbose:
            print(self.data_dir)
        return self.data_dir

    def lodes_codebook(self):
        """Return a table of descriptive variable names for the LODES data

        Returns
        -------
        pandas.DataFrame
            decription of variables returned with LODES/LEHD data.
        """
        return pd.read_csv(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "io/lodes.csv")
        )

    def bea_regions(self):
        """Return a table that maps states to their respective BEA regions

        Returns
        -------
        pandas.DataFrame
            BEA region table
        """
        return pd.read_csv(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "io/bea_regions.csv"
            ),
            converters={"stfips": str},
        )

    def acs(self, year=2018, level="tract", states=None):
        """American Community Survey Data (5-year estimates).

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
        local_path = pathlib.Path(self.data_dir, "acs", f"acs_{year}_{level}.parquet")
        remote_path = f"s3://spatial-ucr/census/acs/acs_{year}_{level}.parquet"
        msg = "Streaming data from S3. Use `geosnap.io.store_acs()` to store the data locally for better performance"
        t = _fetcher(local_path, remote_path, msg)
        t = t.reset_index().rename(columns={"GEOID": "geoid"})

        if states:
            t = t[t.geoid.str[:2].isin(states)]
        t["year"] = year
        return t

    def seda(
        self, level="school", pooling="pool", standardize="gcs", accept_eula=False
    ):
        """Acheievement data from the Stanford Education Data Archive (currently version 4.1).

        May be joined with geodataframes from NCES for spatial analysis

        Parameters
        ----------
        level : str
            aggregation level for achievement data. Options include `school` for school-level,
            or `geodist` for geographic school district-level. By default "school"
        pooling : str
             option to return long-form or pooled data ("pool' or 'long"). Only applicable for geodist level
            as long-form not available at the school level. By default "pool"
        standardize : str,
            which grouping method used to standardize the data. Options include
            "gcs" for grade-cohort standarization or "cs" for cohort standardization,
            by default "gcs"
        accept_eula : bool, optional
            pass True to accept the terms of the SEDA End User License Agreeement.
            The data and its agreement can be viewed at
            <https://exhibits.stanford.edu/data/catalog/db586ns4974>
        """
        eula = """
DATA USE AGREEMENT:

You agree not to use the data sets for commercial advantage, or in the course of for-profit activities. Commercial entities wishing to use this Service should contact Stanford University’s Office of Technology Licensing (info@otlmail.stanford.edu).

You agree that you will not use these data to identify or to otherwise infringe the privacy or confidentiality rights of individuals.

THE DATA SETS ARE PROVIDED “AS IS” AND STANFORD MAKES NO REPRESENTATIONS AND EXTENDS NO WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED. STANFORD SHALL NOT BE LIABLE FOR ANY CLAIMS OR DAMAGES WITH RESPECT TO ANY LOSS OR OTHER CLAIM BY YOU OR ANY THIRD PARTY ON ACCOUNT OF, OR ARISING FROM THE USE OF THE DATA SETS.

You agree that this Agreement and any dispute arising under it is governed by the laws of the State of California of the United States of America, applicable to agreements negotiated, executed, and performed within California.

You agree to acknowledge the Stanford Education Data Archive as the source of these data. In publications, please cite the data as:

Reardon, S. F., Ho, A. D., Shear, B. R., Fahle, E. M., Kalogrides, D., Jang, H., & Chavez, B. (2021). Stanford Education Data Archive (Version 4.1). Retrieved from http://purl.stanford.edu/db586ns4974.

Subject to your compliance with the terms and conditions set forth in this Agreement, Stanford grants you a revocable, non-exclusive, non-transferable right to access and make use of the Data Sets.

        """
        if not accept_eula:
            raise ValueError(
                f"You must accept the EULA by passing `accept_eula=True` \n{eula}"
            )
        if level not in [
            "school",
            "geodist",
        ]:
            raise ValueError(
                "Supported options for the `level` argument are 'school' and 'geodist'"
            )
        if pooling not in [
            "pool",
            "long",
            "poolsub",
        ]:
            raise ValueError(
                "`pool` argument must be either 'pool', 'long', or 'poolsub'"
            )
        if standardize not in [
            "gcs",
            "cs",
        ]:
            raise ValueError(
                "`standardize` argument must be either 'cs' for cohort-standardized or 'gcs' for grade-cohort-standardized"
            )

        if pooling == "poolsub":
            fn = f"seda_{level}_{pooling}_{standardize}_5.0"
        else:
            fn = f"seda_{level}_{pooling}_{standardize}_5.0"
        if level == "geodist":
            fn += "_updated_20240319"
        local_path = pathlib.Path(self.data_dir, "seda", f"{fn}.parquet")
        remote_path = f"https://stacks.stanford.edu/file/druid:cs829jn7849/{fn}.csv"
        msg = (
            "Streaming data from SEDA archive at <https://exhibits.stanford.edu/data/catalog/db586ns4974>.\n"
            "Use `geosnap.io.store_seda()` to store the data locally for better performance"
        )
        if level == "school" and not pooling == "pool":
            raise ValueError("The school level only supports pooled data")
        try:
            t = pd.read_parquet(local_path)
        except FileNotFoundError:
            warn(msg)
            if level == "school":
                try:
                    t = pd.read_csv(
                        remote_path, converters={"sedasch": str, "fips": str}
                    )
                    t.sedasch = t.sedasch.str.rjust(12, "0")
                except FileNotFoundError as e:
                    raise FileNotFoundError from e(
                        "Unable to access local or remote SEDA data"
                    )
            elif level == "geodist":
                try:
                    t = pd.read_csv(
                        remote_path, converters={"sedalea": str, "fips": str}
                    )
                    t.sedalea = t.sedalea.str.rjust(7, "0")
                except FileNotFoundError as e:
                    raise FileNotFoundError from e(
                        "Unable to access local or remote SEDA data"
                    )
                t.fips = t.fips.str.rjust(2, "0")

        return t

    def nces(self, year=1516, dataset="sabs"):
        """National Center for Education Statistics (NCES) Data.

        Parameters
        ----------
        year : str
            vintage of NCES release formatted as a 4-character string representing
            the school year. For example the 2015-2016 academic year is '1516'
        dataset : str
            which dataset to query. Options include `sabs`, `school_districts`, and `schools`

        Returns
        -------
        geopandas.GeoDataFrame
            geodataframe of NCES data
        """
        selector = "districts" if dataset == "school_districts" else dataset
        local_path = pathlib.Path(self.data_dir, "nces", f"{dataset}_{year}.parquet")
        remote_path = f"s3://spatial-ucr/nces/{selector}/{dataset}_{year}.parquet"
        msg = "Streaming data from S3. Use `geosnap.io.store_nces()` to store the data locally for better performance"
        t = _fetcher(local_path, remote_path, msg)
        # t = t.reset_index().rename(columns={"GEOID": "geoid"})

        t["year"] = year
        return t

    def ejscreen(self, year=2018, states=None):
        """EPA EJScreen Data <https://www.epa.gov/ejscreen>.

        Parameters
        ----------
        year : str
            vingage of EJSCREEN release.
        states : list, optional
            subset of states (as 2-digit fips) to return

        Returns
        -------
        geopandas.GeoDataFrame
            geodataframe of EJSCREEN data
        """
        local_path = pathlib.Path(self.data_dir, "epa", f"ejscreen_{year}.parquet")
        remote_path = f"s3://spatial-ucr/epa/ejscreen/ejscreen_{year}.parquet"
        msg = "Streaming data from S3. Use `geosnap.io.store_ejscreen()` to store the data locally for better performance"
        t = _fetcher(local_path, remote_path, msg)
        t = t.rename(columns={"ID": "geoid"})

        if states:
            t = t[t.geoid.str[:2].isin(states)]
        t["year"] = year
        return t

    def ejscreen_codebook(self):
        """Table of variable definitions used in the EPE Environmental Justice Screening dataset

        Returns
        -------
        pandas.DataFrame
            table that stores variable names and definitions.

        """
        return pd.read_csv(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "io/ejscreen_codebook.csv"
            )
        )

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
            local = pathlib.Path(self.data_dir, "blocks_2000", f"{state}.parquet")
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
            local = pathlib.Path(self.data_dir, "blocks_2010", f"{state}.parquet")
            remote = f"s3://spatial-ucr/census/blocks_2010/{state}.parquet"
            blks[state] = _fetcher(local, remote, msg)

            if fips:
                blks[state] = blks[state][blks[state]["geoid"].str.startswith(fips)]

            blks[state]["year"] = 2010
        blocks = list(blks.values())
        blocks = gpd.GeoDataFrame(pd.concat(blocks, sort=True))

        return blocks

    def blocks_2020(self, states=None, fips=None):
        """Census blocks for 2020.

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
            "Unable to locate local census 2020 block data. Streaming instead.\n"
            "If you plan to use census data repeatedly you can store it locally "
            "with the io.store_blocks_2020 function for better performance"
        )
        if isinstance(states, (str, int)):
            states = [states]
        blks = {}
        for state in states:
            local = pathlib.Path(self.data_dir, "blocks_2020", f"{state}.parquet")
            remote = f"s3://spatial-ucr/census/blocks_2020/{state}.parquet"
            blks[state] = _fetcher(local, remote, msg)

            if fips:
                blks[state] = blks[state][blks[state]["geoid"].str.startswith(fips)]

            blks[state]["year"] = 2020
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
        local = pathlib.Path(self.data_dir, "tracts_1990_500k.parquet")
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
        geopandas.GeoDataFrame
            2000 tracts as a geodataframe

        """
        local = pathlib.Path(self.data_dir, "tracts_2000_500k.parquet")
        remote = "s3://spatial-ucr/census/tracts_cartographic/tracts_2000_500k.parquet"
        msg = "Streaming data from S3. Use `geosnap.io.store_census() to store the data locally for better performance"
        t = _fetcher(local, remote, msg)
        if states:
            t = t[t.geoid.str[:2].isin(states)]
        t["year"] = 2000

        return t

    def tracts_2010(
        self,
        states=None,
    ):
        """Nationwide Census Tracts as drawn in 2010 (cartographic 500k).

        Parameters
        ----------
        states : list-like
            list of state fips to subset the national dataframe

        Returns
        -------
        geopandas.GeoDataFrame
            2010 tracts as a geodataframe

        """
        msg = "Streaming data from S3. Use `geosnap.io.store_census() to store the data locally for better performance"
        local = pathlib.Path(self.data_dir, "tracts_2010_500k.parquet")
        remote = "s3://spatial-ucr/census/tracts_cartographic/tracts_2010_500k.parquet"
        t = _fetcher(local, remote, msg)

        if states:
            t = t[t.geoid.str[:2].isin(states)]
        t["year"] = 2010
        return t

    def tracts_2020(
        self,
        states=None,
    ):
        """Nationwide Census Tracts as drawn in 2020 (cartographic 500k).

        Parameters
        ----------
        states : list-like
            list of state fips to subset the national dataframe

        Returns
        -------
        geopandas.GeoDataFrame
            2020 tracts as a geodataframe

        """
        msg = "Streaming data from S3. Use `geosnap.io.store_census() to store the data locally for better performance"
        local = pathlib.Path(self.data_dir, "tracts_2020_500k.parquet")
        remote = "s3://spatial-ucr/census/tracts_cartographic/tracts_2020_500k.parquet"
        t = _fetcher(local, remote, msg)

        if states:
            t = t[t.geoid.str[:2].isin(states)]
        t["year"] = 2020
        return t

    def msas(self):
        """Metropolitan Statistical Areas as drawn in 2020.

        Data come from the U.S. Census Bureau's most recent TIGER/LINE files
        https://www.census.gov/cgi-bin/geo/shapefiles/index.php?year=2020&layergroup=Core+Based+Statistical+Areas


        Returns
        -------
        geopandas.GeoDataFrame
            2010 MSAs as a geodataframe

        """
        local = pathlib.Path(self.data_dir, "msas.parquet")
        remote = "s3://spatial-ucr/census/administrative/msas.parquet"
        msg = "Streaming data from S3. Use `geosnap.io.store_census() to store the data locally for better performance"
        t = _fetcher(local, remote, msg)
        t = t.sort_values(by="name")
        return t

    def states(self):
        """States.

        Returns
        -------
        geopandas.GeoDataFrame
            US States as a geodataframe

        """
        local = pathlib.Path(self.data_dir, "states.parquet")
        remote = "s3://spatial-ucr/census/administrative/states.parquet"
        msg = "Streaming data from S3. Use `geosnap.io.store_census() to store the data locally for better performance"

        t = _fetcher(local, remote, msg)
        return t

    def counties(self):
        """Nationwide counties as drawn in 2010.

        Returns
        -------
        geopandas.GeoDataFrame
            2010 counties as a geodataframe.

        """
        local = pathlib.Path(self.data_dir, "counties.parquet")
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
        return pd.read_csv(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "io/msa_definitions.csv"
            ),
            converters={"stcofips": str},
        )

    def ltdb(self):
        """Longitudinal Tract Database (LTDB).

        Returns
        -------
        pandas.DataFrame or geopandas.GeoDataFrame
            LTDB as a long-form geo/dataframe

        """
        try:
            return pd.read_parquet(pathlib.Path(self.data_dir, "ltdb.parquet"))
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
            return pd.read_parquet(pathlib.Path(self.data_dir, "ncdb.parquet"))
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

    def nlcd_definitions(self):
        """Table of NLCD land classification system definitions.

        Returns
        -------
        pandas.DataFrame
            table that stores variable names, definitions, and formulas.

        """
        return pd.read_csv(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "io/nlcd_definitions.csv"
            )
        )
