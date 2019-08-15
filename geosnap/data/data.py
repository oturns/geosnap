"""Tools for creating and manipulating neighborhood datasets."""

import os
import zipfile
from warnings import warn
from appdirs import user_data_dir
import pandas as pd
import quilt3
import geopandas as gpd
import numpy as np
import sys
import pathlib
from requests.exceptions import Timeout

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyze import cluster as _cluster, cluster_spatial as _cluster_spatial
from harmonize import harmonize as _harmonize
from .util import adjust_inflation, convert_gdf, get_lehd

_fipstable = pd.read_csv(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "stfipstable.csv"),
    converters={"FIPS Code": str},
)

appname = "geosnap"
appauthor = "geosnap"
data_dir = user_data_dir(appname, appauthor)
if not os.path.exists(data_dir):
    pathlib.Path(data_dir).mkdir(parents=True, exist_ok=True)

# look for local storage and create if missing
try:
    from quilt3.data.geosnap_data import storage
except ImportError:
    storage = quilt3.Package()


class DataStore(object):
    """Storage for geosnap data. Currently supports US Census data."""

    def __init__(self):
        """Instantiate a new DataStore object."""
        try:  # if any of these aren't found, stream them insteead
            from quilt3.data.census import tracts_cartographic, administrative
        except ImportError:
            warn(
                "Unable to locate local census data. Streaming instead.\n"
                "If you plan to use census data repeatedly you can store it locally "
                "with the data.store_census function for better performance"
            )
            try:
                tracts_cartographic = quilt3.Package.browse(
                    "census/tracts_cartographic", "s3://quilt-cgs"
                )
                administrative = quilt3.Package.browse(
                    "census/administrative", "s3://quilt-cgs"
                )

            except Timeout:
                warn(
                    "Unable to locate local census data and unable to reach s3 bucket."
                    "You will be unable to use built-in data during this session. "
                    "If you need these data, please try downloading a local copy "
                    "with the data.store_census function, then restart your "
                    "python kernel and try again."
                )
        self.tracts_cartographic = tracts_cartographic
        self.administrative = administrative

    def __dir__(self):

        atts = [
            "blocks_2000",
            "blocks_2010",
            "codebook",
            "counties",
            "ltdb",
            "msa_definitions",
            "msas",
            "ncdb",
            "states",
            "tracts_1990",
            "tracts_2000",
            "tracts_2010",
        ]

        return atts

    def blocks_2000(self, states=None, convert=True):
        """Census blocks for 2000.

        Parameters
        ----------
        states : list-like
            list of state fips codes to return as a datafrrame.
        convert : bool
        if True, return geodataframe, else return dataframe (the default is True).

        Returns
        -------
        type
        pandas.DataFrame or geopandas.GeoDataFrame.
            2000 blocks as a geodataframe or as a dataframe with geometry
            stored as well-known binary on the 'wkb' column.

        """

        try:  # if any of these aren't found, stream them insteead
            from quilt3.data.census import blocks_2000
        except ImportError:
            warn(
                "Unable to locate local census 2000 block data. Streaming instead.\n"
                "If you plan to use census data repeatedly you can store it locally "
                "with the data.store_blocks_2000 function for better performance"
            )
            try:
                blocks_2000 = quilt3.Package.browse(
                    "census/blocks_2000", "s3://quilt-cgs"
                )

            except Timeout:
                warn(
                    "Unable to locate local census data and unable to reach s3 bucket."
                    "You will be unable to use built-in data during this session. "
                    "Try downloading a local copy with the data.store_blocks_2000 function,"
                    "then restart your python kernel and try again."
                )

        if isinstance(states, (str,)):
            states = [states]
        if isinstance(states, (int,)):
            states = [states]
        blks = {}
        for state in states:
            blks[state] = blocks_2000["{state}.parquet".format(state=state)]()
            blks[state]["year"] = 2000
        blocks = list(blks.values())
        blocks = pd.concat(blocks, sort=True)
        if convert:
            return convert_gdf(blocks)
        return blocks

    def blocks_2010(self, states=None, convert=True):
        """Census blocks for 2010.

        Parameters
        ----------
        states : list-like
            list of state fips codes to return as a datafrrame.
        convert : bool
        if True, return geodataframe, else return dataframe (the default is True).

        Returns
        -------
        type
        pandas.DataFrame or geopandas.GeoDataFrame.
            2010 blocks as a geodataframe or as a dataframe with geometry
            stored as well-known binary on the 'wkb' column.

        """
        try:  # if any of these aren't found, stream them insteead
            from quilt3.data.census import blocks_2010
        except ImportError:
            warn(
                "Unable to locate local census 2010 block data. Streaming instead.\n"
                "If you plan to use census data repeatedly you can store it locally "
                "with the data.store_blocks_2010 function for better performance"
            )
            try:
                blocks_2010 = quilt3.Package.browse(
                    "census/blocks_2010", "s3://quilt-cgs"
                )

            except Timeout:
                warn(
                    "Unable to locate local census data and unable to reach s3 bucket."
                    "You will be unable to use built-in data during this session. "
                    "If you need these data, please try downloading a local copy "
                    "with the data.store_blocks_2010 function, then restart your "
                    "python kernel and try again."
                )

        if isinstance(states, (str, int)):
            states = [states]
        blks = {}
        for state in states:
            blks[state] = blocks_2010["{state}.parquet".format(state=state)]()
            blks[state]["year"] = 2010
        blocks = list(blks.values())
        blocks = pd.concat(blocks, sort=True)
        if convert:
            return convert_gdf(blocks)
        return blocks

    def tracts_1990(self, states=None, convert=True):
        """Nationwide Census Tracts as drawn in 1990 (cartographic 500k).

        Parameters
        ----------
        states : list-like
            list of state fips to subset the national dataframe
        convert : bool
            if True, return geodataframe, else return dataframe (the default is True).

        Returns
        -------
        pandas.DataFrame or geopandas.GeoDataFrame.
            1990 tracts as a geodataframe or as a dataframe with geometry
            stored as well-known binary on the 'wkb' column.

        """
        t = self.tracts_cartographic["tracts_1990_500k.parquet"]()
        if states:
            t = t[t.geoid.str[:2].isin(states)]
        t["year"] = 1990
        if convert:
            return convert_gdf(t)
        else:
            return t

    def tracts_2000(self, states=None, convert=True):
        """Nationwide Census Tracts as drawn in 2000 (cartographic 500k).

        Parameters
        ----------
        states : list-like
            list of state fips to subset the national dataframe
        convert : bool
            if True, return geodataframe, else return dataframe (the default is True).

        Returns
        -------
        pandas.DataFrame.
            2000 tracts as a geodataframe or as a dataframe with geometry
            stored as well-known binary on the 'wkb' column.

        """
        t = self.tracts_cartographic["tracts_2000_500k.parquet"]()
        if states:
            t = t[t.geoid.str[:2].isin(states)]
        t["year"] = 2000
        if convert:
            return convert_gdf(t)
        else:
            return t

    def tracts_2010(self, states=None, convert=True):
        """Nationwide Census Tracts as drawn in 2010 (cartographic 500k).

        Parameters
        ----------
        states : list-like
            list of state fips to subset the national dataframe
        convert : bool
            if True, return geodataframe, else return dataframe (the default is True).

        Returns
        -------
        pandas.DataFrame.
            2010 tracts as a geodataframe or as a dataframe with geometry
            stored as well-known binary on the 'wkb' column.

        """
        t = self.tracts_cartographic["tracts_2010_500k.parquet"]()
        if states:
            t = t[t.geoid.str[:2].isin(states)]
        t["year"] = 2010
        if convert:
            return convert_gdf(t)
        else:
            return t

    def msas(self, convert=True):
        """Metropolitan Statistical Areas as drawn in 2010.

        Parameters
        ----------
        convert : bool
            if True, return geodataframe, else return dataframe (the default is True).

        Returns
        -------
        geopandas.GeoDataFrame.
            2010 MSAs as a geodataframe or as a dataframe with geometry
            stored as well-known binary on the 'wkb' column.

        """
        if convert:
            return convert_gdf(
                self.administrative["msas.parquet"]().sort_values(by="name")
            )
        else:
            return self.administrative["msas.parquet"]().sort_values(by="name")

    def states(self, convert=True):
        """States.

        Parameters
        ----------
        convert : bool
            if True, return geodataframe, else return dataframe (the default is True).

        Returns
        -------
        geopandas.GeoDataFrame.
            US States as a geodataframe or as a dataframe with geometry
            stored as well-known binary on the 'wkb' column.

        """
        if convert:
            return convert_gdf(self.administrative["states.parquet"]())
        else:
            return self.administrative["states.parquet"]()

    def counties(self, convert=True):
        """Nationwide counties as drawn in 2010.

        Parameters
        ----------
        convert : bool
            if True, return geodataframe, else return dataframe (the default is True).

        Returns
        -------
        geopandas.GeoDataFrame.
            2010 counties as a geodataframe or as a dataframe with geometry
            stored as well-known binary on the 'wkb' column.

        """
        return convert_gdf(self.administrative["counties.parquet"]())

    @property
    def msa_definitions(self):
        """2010 Metropolitan Statistical Area definitions.

        Returns
        -------
        pandas.DataFrame.
            dataframe that stores state/county --> MSA crosswalk definitions.

        """
        return self.administrative["msa_definitions.parquet"]()

    @property
    def ltdb(self):
        """Longitudinal Tract Database (LTDB).

        Returns
        -------
        pandas.DataFrame or geopandas.GeoDataFrame
            LTDB as a long-form geo/dataframe

        """
        try:
            return storage["ltdb"]()
        except KeyError:
            print(
                "Unable to locate LTDB data. Try saving the data again "
                "using the `store_ltdb` function"
            )

    @property
    def ncdb(self):
        """Geolytics Neighborhood Change Database (NCDB).

        Returns
        -------
        pandas.DataFrarme
            NCDB as a long-form dataframe

        """
        try:
            return storage["ncdb"]()
        except KeyError:
            print(
                "Unable to locate NCDB data. Try saving the data again "
                "using the `store_ncdb` function"
            )

    @property
    def codebook(self):
        """Codebook.

        Returns
        -------
        pandas.DataFrame.
            codebook that stores variable names, definitions, and formulas.

        """
        return pd.read_csv(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "variables.csv")
        )


data_store = DataStore()


def store_census():
    """Save census data to the local quilt package storage.

    Returns
    -------
    None
        Data will be available in the geosnap.data.data_store and will be used
        in place of streaming data for all census queries.

    """
    quilt3.Package.install("census/tracts_cartographic", "s3://quilt-cgs")
    quilt3.Package.install("census/administrative", "s3://quilt-cgs")


def store_blocks_2000():
    """Save census 2000 census block data to the local quilt package storage.

    Returns
    -------
    None
        Data will be available in the geosnap.data.data_store and will be used
        in place of streaming data for all census queries.

    """
    quilt3.Package.install("census/blocks_2000", "s3://quilt-cgs")


def store_blocks_2010():
    """Save census 2010 census block data to the local quilt package storage.

    Returns
    -------
    None
        Data will be available in the geosnap.data.data_store and will be used
        in place of streaming data for all census queries.

    """
    quilt3.Package.install("census/blocks_2010", "s3://quilt-cgs")


def store_ltdb(sample, fullcount):
    """
    Read & store data from Brown's Longitudinal Tract Database (LTDB).

    Parameters
    ----------
    sample : str
        file path of the zip file containing the standard Sample CSV files
        downloaded from
        https://s4.ad.brown.edu/projects/diversity/Researcher/LTBDDload/Default.aspx

    fullcount: str
        file path of the zip file containing the standard Fullcount CSV files
        downloaded from
        https://s4.ad.brown.edu/projects/diversity/Researcher/LTBDDload/Default.aspx

    Returns
    -------
    pandas.DataFrame

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

        inflate_cols = [
            "mhmval",
            "mrent",
            "incpc",
            "hinc",
            "hincw",
            "hincb",
            "hinch",
            "hinca",
        ]

        inflate_available = list(set(df.columns).intersection(set(inflate_cols)))

        if len(inflate_available):
            df = adjust_inflation(df, inflate_available, year)
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

    fullcount70 = _ltdb_reader(fullcount_zip, "LTDB_Std_1970_fullcount.csv", year=1970)

    sample80 = _ltdb_reader(
        sample_zip,
        "ltdb_std_all_sample/ltdb_std_1980_sample.csv",
        dropcols=["pop80sf3", "pop80sf4", "hu80sp", "ohu80sp"],
        year=1980,
    )

    fullcount80 = _ltdb_reader(fullcount_zip, "LTDB_Std_1980_fullcount.csv", year=1980)

    sample90 = _ltdb_reader(
        sample_zip,
        "ltdb_std_all_sample/ltdb_std_1990_sample.csv",
        dropcols=["POP90SF3", "POP90SF4", "HU90SP", "OHU90SP"],
        year=1990,
    )

    fullcount90 = _ltdb_reader(fullcount_zip, "LTDB_Std_1990_fullcount.csv", year=1990)

    sample00 = _ltdb_reader(
        sample_zip,
        "ltdb_std_all_sample/ltdb_std_2000_sample.csv",
        dropcols=["POP00SF3", "HU00SP", "OHU00SP"],
        year=2000,
    )

    fullcount00 = _ltdb_reader(fullcount_zip, "LTDB_Std_2000_fullcount.csv", year=2000)

    sample10 = _ltdb_reader(
        sample_zip, "ltdb_std_all_sample/ltdb_std_2010_sample.csv", year=2010
    )

    # join the sample and fullcount variables into a single df for the year
    ltdb_1970 = sample70.drop(columns=["year"]).join(
        fullcount70.iloc[:, 7:], how="left"
    )
    ltdb_1980 = sample80.drop(columns=["year"]).join(
        fullcount80.iloc[:, 7:], how="left"
    )
    ltdb_1990 = sample90.drop(columns=["year"]).join(
        fullcount90.iloc[:, 7:], how="left"
    )
    ltdb_2000 = sample00.drop(columns=["year"]).join(
        fullcount00.iloc[:, 7:], how="left"
    )
    ltdb_2010 = sample10

    df = pd.concat([ltdb_1970, ltdb_1980, ltdb_1990, ltdb_2000, ltdb_2010], sort=True)

    renamer = dict(
        zip(
            data_store.codebook["ltdb"].tolist(),
            data_store.codebook["variable"].tolist(),
        )
    )

    df.rename(renamer, axis="columns", inplace=True)

    # compute additional variables from lookup table
    for row in data_store.codebook["formula"].dropna().tolist():
        df.eval(row, inplace=True)

    keeps = df.columns[
        df.columns.isin(data_store.codebook["variable"].tolist() + ["year"])
    ]
    df = df[keeps]

    df.to_parquet(os.path.join(data_dir, "ltdb.parquet"), compression="brotli")
    storage.set("ltdb", os.path.join(data_dir, "ltdb.parquet"))
    storage.build("geosnap_data/storage")


def store_ncdb(filepath):
    """
    Read & store data from Geolytics's Neighborhood Change Database.

    Parameters
    ----------
    filepath : str
        location of the input CSV file extracted from your Geolytics DVD

    """
    ncdb_vars = data_store.codebook["ncdb"].dropna()[1:].values

    names = []
    for name in ncdb_vars:
        for suffix in ["7", "8", "9", "0", "1", "2"]:
            names.append(name + suffix)
    names.append("GEO2010")

    c = pd.read_csv(filepath, nrows=1).columns
    c = pd.Series(c.values)

    keep = []
    for i, col in c.items():
        for name in names:
            if col.startswith(name):
                keep.append(col)

    df = pd.read_csv(
        filepath,
        usecols=keep,
        engine="c",
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

    renamer = dict(zip(orig, fixed))
    df.rename(renamer, axis="columns", inplace=True)

    df = df[df.columns[df.columns.isin(names)]]

    df = pd.wide_to_long(
        df, stubnames=ncdb_vars, i="GEO2010", j="year", suffix="(7|8|9|0|1|2)"
    ).reset_index()

    df["year"] = df["year"].replace(
        {7: 1970, 8: 1980, 9: 1990, 0: 2000, 1: 2010, 2: 2010}
    )
    df = df.groupby(["GEO2010", "year"]).first()

    mapper = dict(zip(data_store.codebook.ncdb, data_store.codebook.variable))

    df.reset_index(inplace=True)

    df = df.rename(mapper, axis="columns")

    df = df.set_index("geoid")

    for row in data_store.codebook["formula"].dropna().tolist():
        try:
            df.eval(row, inplace=True)
        except:
            warn("Unable to compute " + str(row))

    keeps = df.columns[
        df.columns.isin(data_store.codebook["variable"].tolist() + ["year"])
    ]

    df = df[keeps]

    df = df.loc[df.n_total_pop != 0]

    df.to_parquet(os.path.join(data_dir, "ncdb.parquet"), compression="brotli")
    storage.set("ncdb", os.path.join(data_dir, "ncdb.parquet"))
    storage.build("geosnap_data/storage")


def _fips_filter(
    state_fips=None, county_fips=None, msa_fips=None, fips=None, data=None
):

    if isinstance(state_fips, (str,)):
        state_fips = [state_fips]
    if isinstance(county_fips, (str,)):
        county_fips = [county_fips]
    if isinstance(fips, (str,)):
        fips = [fips]

    # if counties already present in states, ignore them
    if county_fips:
        for i in county_fips:
            if state_fips and i[:2] in county_fips:
                county_fips.remove(i)
    # if any fips present in state or counties, ignore them too
    if fips:
        for i in fips:
            if state_fips and i[:2] in state_fips:
                fips.remove(i)
            if county_fips and i[:5] in county_fips:
                fips.remove(i)

    fips_list = []
    if fips:
        fips_list += fips
    if county_fips:
        fips_list += county_fips
    if state_fips:
        fips_list += state_fips

    if msa_fips:
        fips_list += data_store.msa_definitions[
            data_store.msa_definitions["CBSA Code"] == msa_fips
        ]["stcofips"].tolist()

    dfs = []
    for index in fips_list:
        dfs.append(data[data.geoid.str.startswith(index)])

    return pd.concat(dfs)


def _from_db(
    data, state_fips=None, county_fips=None, msa_fips=None, fips=None, years=None
):

    data = data[data.year.isin(years)]
    data = data.reset_index()

    df = _fips_filter(
        state_fips=state_fips,
        county_fips=county_fips,
        msa_fips=msa_fips,
        fips=fips,
        data=data,
    )

    # we know we're using 2010, need to drop the year column so no conficts
    tracts = data_store.tracts_2010(convert=False)
    tracts = tracts[["geoid", "wkb"]]
    tracts = tracts[tracts.geoid.isin(df.geoid)]
    tracts = convert_gdf(tracts)

    gdf = df.merge(tracts, on="geoid", how="left").set_index("geoid")
    gdf = gpd.GeoDataFrame(gdf)
    return gdf


class Community(object):
    """Spatial and tabular data for a collection of "neighborhoods".

       A community is a collection of "neighborhoods" represented by spatial
       boundaries (e.g. census tracts, or blocks in the US), and tabular data
       which describe the composition of each neighborhood (e.g. data from
       surveys, sensors, or geocoded misc.). A Community can be large (e.g. a
       metropolitan region), or small (e.g. a handfull of census tracts) and
       may have data pertaining to multiple discrete points in time.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        long-form geodataframe that holds spatial and tabular data.
    harmonized : bool
        Whether neighborhood boundaries have been harmonized into a set of
        time-consistent units
    **kwargs


    Attributes
    ----------
    gdf : geopandas.GeoDataFrame
        long-form geodataframe that stores neighborhood-level attributes
        and geometries for one or more time periods
    harmonized : bool
        Whether neighborhood boundaries have been harmonized into
        consistent units over time

    """

    def __init__(self, gdf=None, harmonized=None, **kwargs):
        """Initialize a new Community.

        Parameters
        ----------
        gdf : geopandas.GeoDataFrame
            long-form geodataframe that stores neighborhood-level attributes
            and geometries for one or more time periods
        harmonized : bool
            Whether neighborhood boundaries have been harmonized into
            consistent units over time
        **kwargs : kwargs
            extra keyword arguments `**kwargs`.

        """
        self.gdf = gdf
        self.harmonized = harmonized

    def harmonize(
        self,
        target_year_of_reference,
        weights_method="area",
        extensive_variables=[],
        intensive_variables=[],
        allocate_total=True,
        raster_path=None,
        codes=[21, 22, 23, 24],
        force_crs_match=True,
    ):
        """Short summary.

        Parameters
        ----------
        target_year: int
            Polygons from this year will become the target boundaries for
            spatial interpolation.
        weights_method : string
            The method that the harmonization will be conducted. This can be
            set to:
                "area"                          : harmonization according to
                                                  area weights.
                "land_type_area"                : harmonization according to
                                                  the Land Types considered
                                                  'populated' areas.
                "land_type_Poisson_regression"  : NOT YET INTRODUCED.
                "land_type_Gaussian_regression" : NOT YET INTRODUCED.
        extensive_variables : list
            extensive variables to be used in interpolation.
        intensive_variables : type
            intensive variables to be used in interpolation.
        allocate_total : boolean
            True if total value of source area should be allocated.
            False if denominator is area of i. Note that the two cases
            would be identical when the area of the source polygon is
            exhausted by intersections. See (3) in Notes for more details
        raster_path : str
            path to the raster image that has the types of each pixel in the
            spatial context. Only taken into consideration for harmonization
            raster based.
        codes : list
            pixel values that should be included in the regression (the default is [21, 22, 23, 24]).
        force_crs_match : bool
            whether source and target dataframes should be reprojected to match (the default is True).

        Returns
        -------
        None
            New data are added to the input Community

        """
        # convert the long-form into a list of dataframes
        data = [x[1] for x in self.gdf.groupby("year")]

        gdf = _harmonize(
            data,
            target_year_of_reference,
            weights_method=weights_method,
            extensive_variables=extensive_variables,
            intensive_variables=intensive_variables,
            allocate_total=allocate_total,
            raster_path=raster_path,
            codes=codes,
            force_crs_match=force_crs_match,
        )
        return Community(gdf, harmonized=True)

    def cluster(
        self,
        n_clusters=6,
        method=None,
        best_model=False,
        columns=None,
        verbose=False,
        return_model=False,
        **kwargs
    ):
        """Create a geodemographic typology by running a cluster analysis on
        the study area's neighborhood attributes

        Parameters
        ----------
        gdf : pandas.DataFrame
            long-form (geo)DataFrame containing neighborhood attributes
        n_clusters : int
            the number of clusters to model. The default is 6).
        method : str
            the clustering algorithm used to identify neighborhood types
        best_model : bool
            if using a gaussian mixture model, use BIC to choose the best
            n_clusters. (the default is False).
        columns : list-like
            subset of columns on which to apply the clustering
        verbose : bool
            whether to print warning messages (the default is False).
        return_model : bool
            whether to return the underlying cluster model instance for further
            analysis

        Returns
        -------
        pandas.DataFrame with a column of neighborhood cluster labels appended
        as a new column. Will overwrite columns of the same name.
        """
        harmonized = self.harmonized
        if return_model:
            gdf, model = _cluster(
                gdf=self.gdf.copy(),
                n_clusters=n_clusters,
                method=method,
                best_model=best_model,
                columns=columns,
                verbose=verbose,
                return_model=return_model,
                **kwargs
            )
            return Community(gdf, harmonized=harmonized), model
        else:
            gdf = _cluster(
                gdf=self.gdf.copy(),
                n_clusters=n_clusters,
                method=method,
                best_model=best_model,
                columns=columns,
                verbose=verbose,
                return_model=return_model,
                **kwargs
            )
            return Community(gdf, harmonized=harmonized)

    def cluster_spatial(
        self,
        n_clusters=6,
        spatial_weights="rook",
        method=None,
        best_model=False,
        columns=None,
        threshold_variable="count",
        threshold=10,
        return_model=False,
        scaler=None,
        **kwargs
    ):
        """Create a *spatial* geodemographic typology by running a cluster
        analysis on the metro area's neighborhood attributes and including a
        contiguity constraint.

        Parameters
        ----------
        gdf : geopandas.GeoDataFrame
            long-form geodataframe holding neighborhood attribute and geometry data.
        n_clusters : int
            the number of clusters to model. The default is 6).
        weights_type : str 'queen' or 'rook'
            spatial weights matrix specification` (the default is "rook").
        method : str
            the clustering algorithm used to identify neighborhood types
        best_model : type
            Description of parameter `best_model` (the default is False).
        columns : list-like
            subset of columns on which to apply the clustering
        threshold_variable : str
            for max-p, which variable should define `p`. The default is "count",
            which will grow regions until the threshold number of polygons have
            been aggregated
        threshold : numeric
            threshold to use for max-p clustering (the default is 10).
        return_model : bool
            whether to return the underlying cluster model instance for further
            analysis

        Returns
        -------
        geopandas.GeoDataFrame with a column of neighborhood cluster labels
        appended as a new column. Will overwrite columns of the same name.
        """
        harmonized = self.harmonized

        if return_model:
            gdf, model = _cluster_spatial(
                gdf=self.gdf.copy(),
                n_clusters=n_clusters,
                spatial_weights=spatial_weights,
                method=method,
                best_model=best_model,
                columns=columns,
                threshold_variable=threshold_variable,
                threshold=threshold,
                return_model=return_model,
                **kwargs
            )
            return Community(gdf, harmonized=True), model
        else:
            gdf = _cluster_spatial(
                gdf=self.gdf.copy(),
                n_clusters=n_clusters,
                spatial_weights=spatial_weights,
                method=method,
                best_model=best_model,
                columns=columns,
                threshold_variable=threshold_variable,
                threshold=threshold,
                return_model=return_model,
                **kwargs
            )
            return Community(gdf, harmonized=harmonized)

    @classmethod
    def from_ltdb(
        cls,
        state_fips=None,
        county_fips=None,
        msa_fips=None,
        fips=None,
        boundary=None,
        years=[1970, 1980, 1990, 2000, 2010],
    ):
        """Create a new Community from LTDB data.

           Instiantiate a new Community from pre-harmonized LTDB data. To use
           you must first download and register LTDB data with geosnap using
           the `store_ltdb` function. Pass lists of states, counties, or any
           arbitrary FIPS codes to create a community. All fips code arguments
           are additive, so geosnap will include the largest unique set.
           Alternatively, you may provide a boundary to use as a clipping
           feature.

        Parameters
        ----------
        state_fips : list or str
            string or list of strings of two-digit fips codes defining states
            to include in the study area.
        county_fips : list or str
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        msa_fips : type
            string or list of strings of fips codes defining
            MSAs to include in the study area.
        fips : type
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        boundary: geopandas.GeoDataFrame
            geodataframe that defines the total extent of the study area.
            This will be used to clip tracts lazily by selecting all
            `GeoDataFrame.representative_point()`s that intersect the
            boundary gdf
        years : list
            list of years (decades) to include in the study data
            (the default is [1970, 1980, 1990, 2000, 2010]).

        Returns
        -------
        Community
            Community with LTDB data


        """
        if isinstance(boundary, gpd.GeoDataFrame):
            tracts = data_store.tracts_2010()[["geoid", "geometry"]]
            ltdb = data_store.ltdb.reset_index()
            if boundary.crs != tracts.crs:
                warn(
                    "Unable to determine whether boundary CRS is WGS84 "
                    "if this produces unexpected results, try reprojecting"
                )
            tracts = tracts[
                tracts.representative_point().intersects(boundary.unary_union)
            ]
            gdf = ltdb[ltdb["geoid"].isin(tracts["geoid"])]
            gdf = gpd.GeoDataFrame(gdf.merge(tracts, on="geoid", how="left"))

        else:
            gdf = _from_db(
                data=data_store.ltdb,
                state_fips=state_fips,
                county_fips=county_fips,
                msa_fips=msa_fips,
                fips=fips,
                years=years,
            )

        return cls(gdf=gdf, harmonized=True)

    @classmethod
    def from_ncdb(
        cls,
        state_fips=None,
        county_fips=None,
        msa_fips=None,
        fips=None,
        boundary=None,
        years=[1970, 1980, 1990, 2000, 2010],
    ):
        """Create a new Community from NCDB data.

           Instiantiate a new Community from pre-harmonized NCDB data. To use
           you must first download and register LTDB data with geosnap using
           the `store_ncdb` function. Pass lists of states, counties, or any
           arbitrary FIPS codes to create a community. All fips code arguments
           are additive, so geosnap will include the largest unique set.
           Alternatively, you may provide a boundary to use as a clipping
           feature.

        Parameters
        ----------
        state_fips : list or str
            string or list of strings of two-digit fips codes defining states
            to include in the study area.
        county_fips : list or str
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        msa_fips : type
            string or list of strings of fips codes defining
            MSAs to include in the study area.
        fips : type
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        boundary: geopandas.GeoDataFrame
            geodataframe that defines the total extent of the study area.
            This will be used to clip tracts lazily by selecting all
            `GeoDataFrame.representative_point()`s that intersect the
            boundary gdf
        years : list
            list of years (decades) to include in the study data
            (the default is [1970, 1980, 1990, 2000, 2010]).

        Returns
        -------
        Community
            Community with NCDB data

        """
        if isinstance(boundary, gpd.GeoDataFrame):
            tracts = data_store.tracts_2010()[["geoid", "geometry"]]
            ncdb = data_store.ncdb.reset_index()
            if boundary.crs != tracts.crs:
                warn(
                    "Unable to determine whether boundary CRS is WGS84 "
                    "if this produces unexpected results, try reprojecting"
                )
            tracts = tracts[
                tracts.representative_point().intersects(boundary.unary_union)
            ]
            gdf = ncdb[ncdb["geoid"].isin(tracts["geoid"])]
            gdf = gpd.GeoDataFrame(gdf.merge(tracts, on="geoid", how="left"))

        else:
            gdf = _from_db(
                data=data_store.ncdb,
                state_fips=state_fips,
                county_fips=county_fips,
                msa_fips=msa_fips,
                fips=fips,
                years=years,
            )

        return cls(gdf=gdf, harmonized=True)

    @classmethod
    def from_census(
        cls,
        state_fips=None,
        county_fips=None,
        msa_fips=None,
        fips=None,
        boundary=None,
        years=[1990, 2000, 2010],
    ):
        """Create a new Community from original vintage US Census data.

           Instiantiate a new Community from . To use
           you must first download and register census data with geosnap using
           the `store_census` function. Pass lists of states, counties, or any
           arbitrary FIPS codes to create a community. All fips code arguments
           are additive, so geosnap will include the largest unique set.
           Alternatively, you may provide a boundary to use as a clipping
           feature.

        Parameters
        ----------
        state_fips : list or str
            string or list of strings of two-digit fips codes defining states
            to include in the study area.
        county_fips : list or str
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        msa_fips : type
            string or list of strings of fips codes defining
            MSAs to include in the study area.
        fips : type
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        boundary: geopandas.GeoDataFrame
            geodataframe that defines the total extent of the study area.
            This will be used to clip tracts lazily by selecting all
            `GeoDataFrame.representative_point()`s that intersect the
            boundary gdf
        years : list
            list of years to include in the study data
            (the default is [1990, 2000, 2010]).

        Returns
        -------
        Community
            Community with unharmonized census data

        """
        if isinstance(years, (str, int)):
            years = [years]

        msa_states = []
        if msa_fips:
            msa_states += data_store.msa_definitions[
                data_store.msa_definitions["CBSA Code"] == msa_fips
            ]["stcofips"].tolist()
        msa_states = [i[:2] for i in msa_states]

        # build a list of states in the dataset
        allfips = []
        for i in [state_fips, county_fips, fips, msa_states]:
            if i:
                allfips.append(i[:2])
        states = np.unique(allfips)

        # if using a boundary there will be no fips, so reset states to None
        if len(states) == 0:
            states = None

        df_dict = {
            1990: data_store.tracts_1990(states=states),
            2000: data_store.tracts_2000(states=states),
            2010: data_store.tracts_2010(states=states),
        }

        tracts = []
        for year in years:
            tracts.append(df_dict[year])
        tracts = pd.concat(tracts, sort=False)

        if isinstance(boundary, gpd.GeoDataFrame):
            if boundary.crs != tracts.crs:
                warn(
                    "Unable to determine whether boundary CRS is WGS84 "
                    "if this produces unexpected results, try reprojecting"
                )
            tracts = tracts[
                tracts.representative_point().intersects(boundary.unary_union)
            ]

        else:

            gdf = _fips_filter(
                state_fips=state_fips,
                county_fips=county_fips,
                msa_fips=msa_fips,
                fips=fips,
                data=tracts,
            )

        return cls(gdf=gdf, harmonized=False)

    @classmethod
    def from_lodes(
        cls,
        state_fips=None,
        county_fips=None,
        msa_fips=None,
        fips=None,
        boundary=None,
        years=2015,
        dataset="wac",
    ):
        """Create a new Community from Census LEHD/LODES data.

           Instiantiate a new Community from LODES data.
           Pass lists of states, counties, or any
           arbitrary FIPS codes to create a community. All fips code arguments
           are additive, so geosnap will include the largest unique set.
           Alternatively, you may provide a boundary to use as a clipping
           feature.

        Parameters
        ----------
        state_fips : list or str
            string or list of strings of two-digit fips codes defining states
            to include in the study area.
        county_fips : list or str
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        msa_fips : type
            string or list of strings of fips codes defining
            MSAs to include in the study area.
        fips : type
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        boundary: geopandas.GeoDataFrame
            geodataframe that defines the total extent of the study area.
            This will be used to clip tracts lazily by selecting all
            `GeoDataFrame.representative_point()`s that intersect the
            boundary gdf
        years : list
            list of years to include in the study data
            (the default is [1990, 2000, 2010]).
        dataset: str
            which LODES dataset should be used to create the Community.
            Options are 'wac' for workplace area characteristics or 'rac' for
            residence area characteristics.

        Returns
        -------
        Community
            Community with LODES data

        """
        if isinstance(years, (str, int)):
            years = [years]

        msa_states = []
        if msa_fips:
            msa_states += data_store.msa_definitions[
                data_store.msa_definitions["CBSA Code"] == msa_fips
            ]["stcofips"].tolist()
        msa_states = [i[:2] for i in msa_states]

        # build a list of states in the dataset
        allfips = []
        for i in [state_fips, county_fips, fips, msa_states]:
            if i:
                allfips.append(i[:2])
        states = np.unique(allfips)
        # states = np.unique([i[:2] for i in allfips])

        if any(years) < 2010:
            gdf00 = data_store.blocks_2000(states=states)
            gdf00 = gdf00.drop(columns=["year"])
        gdf = data_store.blocks_2010(states=states)
        gdf = gdf.drop(columns=["year"])

        # grab state abbreviations
        names = (
            _fipstable[_fipstable["FIPS Code"].isin(states)]["State Abbreviation"]
            .str.lower()
            .tolist()
        )

        dfs = []
        if isinstance(names, str):
            names = [names]
        for name in names:
            for year in years:
                df = get_lehd(dataset=dataset, year=year, state=name)
                if year < 2010:
                    df = gdf00.merge(df, on="geoid", how="left")
                else:
                    df = gdf.merge(df, on="geoid", how="left")
                df["year"] = year
                dfs.append(df)
        gdf = pd.concat(dfs)

        if isinstance(boundary, gpd.GeoDataFrame):
            if boundary.crs != gdf.crs:
                warn(
                    "Unable to determine whether boundary CRS is WGS84 "
                    "if this produces unexpected results, try reprojecting"
                )
            gdf = gdf[gdf.representative_point().intersects(boundary.unary_union)]

        else:

            gdf = _fips_filter(
                state_fips=state_fips,
                county_fips=county_fips,
                msa_fips=msa_fips,
                fips=fips,
                data=gdf,
            )

        return cls(gdf=gdf, harmonized=False)

    @classmethod
    def from_geodataframes(cls, gdfs=None):
        """Create a new Community from a list of geodataframes.

        Parameters
        ----------
        gdfs : list-like
            list of geodataframes that hold attribute and geometry data for
            a study area. Each geodataframe must have neighborhood
            attribute data, geometry data, and a time column that defines
            how the geodataframes are sequenced. The geometries may be
            stable over time (in which case the dataset is harmonized) or
            may be unique for each time. If the data are harmonized, the
            dataframes must also have an ID variable that indexes
            neighborhood units over time.

        """

        gdf = pd.concat(gdfs, sort=True)
        return cls(gdf=gdf)
