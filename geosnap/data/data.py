"""Tools for creating and manipulating neighborhood datasets."""

import os
import zipfile
from warnings import warn

import matplotlib.pyplot as plt
import pandas as pd
import quilt

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from util import adjust_inflation, convert_gdf


try:
    from quilt.data.spatialucr import census
except ImportError:
    warn("Fetching data. This should only happen once")
    quilt.install("spatialucr/census")
    quilt.install("spatialucr/census_cartographic")
    from quilt.data.spatialucr import census
try:
    from quilt.data.geosnap_data import data_store
except ImportError:
    quilt.build("geosnap_data/data_store")
    from quilt.data.geosnap_data import data_store


class Bunch(dict):
    """A dict with attribute-access."""

    def __getattr__(self, key):
        try:
            return self.__getitem__(key)
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __dir__(self):
        return self.keys()


_package_directory = os.path.dirname(os.path.abspath(__file__))
_cbsa = pd.read_parquet(os.path.join(_package_directory, 'cbsas.parquet'))

dictionary = pd.read_csv(os.path.join(_package_directory, "variables.csv"))

states = census.states()
counties = census.counties()
tracts = census.tracts_2010
metros = convert_gdf(census.msas())


def _db_checker(database):

    try:
        if database == 'ltdb':
            df = data_store.ltdb()
        else:
            df = data_store.ncdb()
    except AttributeError:
        df = ''

    return df


#: A dict containing tabular data available to geosnap
db = Bunch(census_90=census.variables_1990(),
           census_00=census.variables_2000(),
           ltdb=_db_checker('ltdb'),
           ncdb=_db_checker('ncdb')
           )


# LTDB importer


def read_ltdb(sample, fullcount):
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

        inflate_cols = ["mhmval", "mrent", "incpc",
                        "hinc", "hincw", "hincb", "hinch", "hinca"]

        inflate_available = list(set(df.columns).intersection(set(
            inflate_cols)))

        if len(inflate_available):
        # try:
            df = adjust_inflation(df, inflate_available, year)
        # except KeyError:  # half the dfs don't have these variables
        #     pass
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
        zip(dictionary['ltdb'].tolist(), dictionary['variable'].tolist()))

    df.rename(renamer, axis="columns", inplace=True)

    # compute additional variables from lookup table
    for row in dictionary['formula'].dropna().tolist():
        df.eval(row, inplace=True)

    keeps = df.columns[df.columns.isin(dictionary['variable'].tolist() + ['year'])]
    df = df[keeps]

    data_store._set(['ltdb'], df)
    quilt.build("geosnap_data/data_store", data_store)


def read_ncdb(filepath):
    """
    Read & store data from Geolytics's Neighborhood Change Database.

    Parameters
    ----------
    filepath : str
        location of the input CSV file extracted from your Geolytics DVD

    Returns
    -------
    pandas.DataFrame

    """
    ncdb_vars = dictionary["ncdb"].dropna()[1:].values

    names = []
    for name in ncdb_vars:
        for suffix in ['7', '8', '9', '0', '1', '2']:
            names.append(name + suffix)
    names.append('GEO2010')

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
        engine='c',
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

    mapper = dict(zip(dictionary.ncdb, dictionary.variable))

    df.reset_index(inplace=True)

    df = df.rename(mapper, axis="columns")

    df = df.set_index("geoid")

    for row in dictionary['formula'].dropna().tolist():
        try:
            df.eval(row, inplace=True)
        except:
            warn('Unable to compute ' + str(row))

    df = df.round(0)

    keeps = df.columns[df.columns.isin(dictionary['variable'].tolist() + ['year'])]

    df = df[keeps]

    df = df.loc[df.n_total_pop != 0]

    data_store._set(['ncdb'], df)
    quilt.build("geosnap_data/data_store", data_store)


# TODO NHGIS reader


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
    name : str
            name or title of dataset.
    source : str
            database from which to query attribute data.
            Must of one of ['ltdb', 'ncdb', 'census', 'external'].
    statefips : list-like
            list of two-digit State FIPS codes that define a study region.
            These will be used to select tracts or blocks that fall within
            the region.
    countyfips : list-like
            list of three-digit County FIPS codes that define a study
            region. These will be used to select tracts or blocks that
            fall within the region.
    cbsafips : str
            CBSA fips code that defines a study region. This is used to
            select tracts or blocks that fall within the metropolitan region
    add_indices : list-like
            list of additional indices that should be included in the region.
            This is likely a list of additional tracts that are relevant to the
            study area but do not fall inside the passed boundary
    boundary : GeoDataFrame
            A GeoDataFrame that defines the extent of the boundary in question.
            If a boundary is passed, it will be used to clip the tracts or
            blocks that fall within it and the state and county lists will
            be ignored

    Attributes
    ----------
    census : Pandas DataFrame
            long-form dataframe containing attribute variables for each unit
            of analysis.
    name : str
            name or title of dataset
    boundary : GeoDataFrame
            outer boundary of the study area
    tracts
            GeoDataFrame containing tract boundaries
    counties
            GeoDataFrame containing County boundaries
    states
            GeoDataFrame containing State boundaries

    """

    def __init__(self,
                 source,
                 statefips=None,
                 countyfips=None,
                 cbsafips=None,
                 add_indices=None,
                 boundary=None,
                 name=''):
        """Instantiate a Community."""
        # If a boundary is passed, use it to clip out the appropriate tracts
        tracts = census.tracts_2010().copy()
        tracts.columns = tracts.columns.str.lower()
        self.name = name
        self.states = states.copy()
        self.tracts = tracts.copy()
        self.cbsa = metros.copy()[metros.copy().geoid == cbsafips]
        self.counties = counties.copy()
        if boundary is not None:
            self.tracts = convert_gdf(self.tracts)
            self.boundary = boundary
            if boundary.crs != self.tracts.crs:
                if not boundary.crs:
                    raise('Boundary must have a CRS to ensure valid spatial \
                    selection')
                self.tracts = self.tracts.to_crs(boundary.crs)

            self.tracts = self.tracts[self.tracts.representative_point()
                                      .within(self.boundary.unary_union)]
            self.counties = convert_gdf(self.counties[counties.geoid.isin(
                self.tracts.geoid.str[0:5])])
            self.states = convert_gdf(self.states[states.geoid.isin(
                self.tracts.geoid.str[0:2])])
            self.counties = self.counties.to_crs(boundary.crs)
            self.states = self.states.to_crs(boundary.crs)

        # If county and state lists are passed, use them to filter
        # based on geoid
        else:
            assert statefips or countyfips or cbsafips or add_indices

            statelist = []
            if isinstance(statefips, (list, )):
                statelist.extend(statefips)
            else:
                statelist.append(statefips)

            countylist = []
            if isinstance(countyfips, (list, )):
                countylist.extend(countyfips)
            else:
                countylist.append(countyfips)

            geo_filter = {'state': statelist, 'county': countylist}
            fips = []
            for state in geo_filter['state']:
                if countyfips is not None:
                    for county in geo_filter['county']:
                        fips.append(state + county)
                else:
                    fips.append(state)

            self.states = self.states[states.geoid.isin(statelist)]
            if countyfips is not None:
                self.counties = self.counties[self.counties.geoid.str[:5].isin(
                    fips)]
                self.tracts = self.tracts[self.tracts.geoid.str[:5].isin(fips)]
            else:
                self.counties = self.counties[self.counties.geoid.str[:2].isin(
                    fips)]
                self.tracts = self.tracts[self.tracts.geoid.str[:2].isin(fips)]

            self.tracts = convert_gdf(self.tracts)
            self.counties = convert_gdf(self.counties)
            self.states = convert_gdf(self.states)
        if source in ['ltdb', 'ncdb']:
            _df = _db_checker(source)
            if len(_df) == 0:
                raise ValueError("Unable to locate {source} data. Please import the database with the `read_{source}` function".format(source=source))
        elif source == "external":
            _df = data
        else:
            raise ValueError(
                "source must be one of 'ltdb', 'ncdb', 'census', 'external'")

        if cbsafips:
            if not add_indices:
                add_indices = []
            add_indices += _cbsa[_cbsa['CBSA Code'] == cbsafips][
                'stcofips'].tolist()
        if add_indices:
            for index in add_indices:

                self.tracts = self.tracts.append(
                    convert_gdf(tracts[tracts.geoid.str.startswith(index)]))
                self.counties = self.counties.append(
                    convert_gdf(counties[counties.geoid.str.startswith(
                        index[0:5])]))
        self.tracts = self.tracts[~self.tracts.geoid.duplicated(keep='first')]
        self.counties = self.counties[
            ~self.counties.geoid.duplicated(keep='first')]
        self.census = _df[_df.index.isin(self.tracts.geoid)]

    def plot(self,
             column=None,
             year=2010,
             ax=None,
             plot_counties=True,
             title=None,
             **kwargs):
        """Conveniently plot a choropleth of the Community.

        Parameters
        ----------
        column : str
            The column to be plotted (the default is None).
        year : str
            The decennial census year to be plotted (the default is 2010).
        ax : type
            matplotlib.axes on which to plot.
        plot_counties : bool
            Whether the plot should include county boundaries
            (the default is True).
        title: str
            Title of figure passed to matplotlib.pyplot.title()
        **kwargs

        Returns
        -------
        type
            Description of returned object.

        """
        assert column, "You must choose a column to plot"
        colname = '%s' % column
        if ax is not None:
            ax = ax
        else:
            fig, ax = plt.subplots(figsize=(15, 15))
            if colname.startswith('n_'):
                colname = colname[1:]
            elif colname.startswith('p_'):
                colname = colname[1:]
                colname = colname + ' (%)'
            colname = colname.replace("_", " ")
            colname = colname.title()

            if title:
                plt.title(title, fontsize=20)
            else:
                if self.name:
                    plt.title(
                        self.name + " " + str(year) + '\n' +
                        colname, fontsize=20)
                else:
                    plt.title(colname + " " + str(year), fontsize=20)
            plt.axis("off")

        ax.set_aspect("equal")
        plotme = self.tracts.merge(
            self.census[self.census.year == year],
            left_on="geoid",
            right_index=True)
        plotme = plotme.dropna(subset=[column])
        plotme.plot(column=column, alpha=0.8, ax=ax, **kwargs)

        if plot_counties is True:
            self.counties.plot(
                edgecolor="#5c5353",
                linewidth=0.8,
                facecolor="none",
                ax=ax)

        return ax

    def to_crs(self, crs=None, epsg=None, inplace=False):
        """Transform all geometries to a new coordinate reference system.

            Parameters
            ----------
            crs : dict or str
                Output projection parameters as string or in dictionary form.
            epsg : int
                EPSG code specifying output projection.
            inplace : bool, optional, default: False
                Whether to return a new GeoDataFrame or do the transformation
                in place.

        """
        if inplace:
            self.tracts = self.tracts
            self.counties = self.counties
            self.states = self.states
        else:
            self.tracts = self.tracts.copy()
            self.counties = self.counties.copy()
            self.states = self.states.copy()

        self.tracts = self.tracts.to_crs(crs=crs, epsg=epsg)
        self.states = self.states.to_crs(crs=crs, epsg=epsg)
        self.counties = self.counties.to_crs(crs=crs, epsg=epsg)
        if not inplace:
            return self
