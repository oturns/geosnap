"""Tools for creating and manipulating neighborhood datasets."""

import os
import pathlib
import zipfile
from warnings import warn

from appdirs import user_data_dir

import geopandas as gpd
import pandas as pd
import quilt3

from .._data import datasets
from .util import adjust_inflation, convert_gdf

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
    storage = quilt3.Package.browse("geosnap_data/storage")
except FileNotFoundError:
    storage = quilt3.Package()


def store_census():
    """Save census data to the local quilt package storage.

    Returns
    -------
    None
        Data will be available in the geosnap.data.datasets and will be used
        in place of streaming data for all census queries. The raster package
        is 3.05 GB.

    """
    quilt3.Package.install("census/tracts_cartographic", "s3://spatial-ucr")
    quilt3.Package.install("census/administrative", "s3://spatial-ucr")


def store_blocks_2000():
    """Save census 2000 census block data to the local quilt package storage.

    Returns
    -------
    None
        Data will be available in the geosnap.data.datasets and will be used
        in place of streaming data for all census queries.

    """
    quilt3.Package.install("census/blocks_2000", "s3://spatial-ucr")


def store_blocks_2010():
    """Save census 2010 census block data to the local quilt package storage.

    Returns
    -------
    None
        Data will be available in the geosnap.data.datasets and will be used
        in place of streaming data for all census queries.

    """
    quilt3.Package.install("census/blocks_2010", "s3://spatial-ucr")


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
        zip(datasets.codebook()["ltdb"].tolist(), datasets.codebook()["variable"].tolist())
    )

    df.rename(renamer, axis="columns", inplace=True)

    # compute additional variables from lookup table
    for row in datasets.codebook()["formula"].dropna().tolist():
        df.eval(row, inplace=True)

    keeps = df.columns[
        df.columns.isin(datasets.codebook()["variable"].tolist() + ["year"])
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
    ncdb_vars = datasets.codebook()["ncdb"].dropna()[1:].values

    names = []
    for name in ncdb_vars:
        for suffix in ["7", "8", "9", "0", "1", "2"]:
            names.append(name + suffix)
    names.append("GEO2010")

    c = pd.read_csv(filepath, nrows=1).columns
    c = pd.Series(c.values)

    keep = []
    for _, col in c.items():
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

    mapper = dict(zip(datasets.codebook().ncdb, datasets.codebook().variable))

    df.reset_index(inplace=True)

    df = df.rename(mapper, axis="columns")

    df = df.set_index("geoid")

    for row in datasets.codebook()["formula"].dropna().tolist():
        try:
            df.eval(row, inplace=True)
        except:
            warn("Unable to compute " + str(row))

    keeps = df.columns[
        df.columns.isin(datasets.codebook()["variable"].tolist() + ["year"])
    ]

    df = df[keeps]

    df = df.loc[df.n_total_pop != 0]

    df.to_parquet(os.path.join(data_dir, "ncdb.parquet"), compression="brotli")
    storage.set("ncdb", os.path.join(data_dir, "ncdb.parquet"))
    storage.build("geosnap_data/storage")


def _fips_filter(
    state_fips=None, county_fips=None, msa_fips=None, fips=None, data=None
):
    data = data.copy()

    fips_list = []
    for each in [state_fips, county_fips, fips]:
        if isinstance(each, (str,)):
            each = [each]
        if isinstance(each, (list,)):
            fips_list += each

    if msa_fips:
        fips_list += datasets.msa_definitions()[
            datasets.msa_definitions()["CBSA Code"] == msa_fips
        ]["stcofips"].tolist()

    df = data[data.geoid.str.startswith(tuple(fips_list))]

    return df


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
    tracts = datasets.tracts_2010(convert=False)
    tracts = tracts[["geoid", "wkb"]]
    tracts = tracts[tracts.geoid.isin(df.geoid)]
    tracts = convert_gdf(tracts)

    gdf = df.merge(tracts, on="geoid", how="left").set_index("geoid")
    gdf = gpd.GeoDataFrame(gdf)
    return gdf
