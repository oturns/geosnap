"""Tools for creating and manipulating neighborhood datasets."""

import os
import pathlib
import zipfile
from pathlib import Path
from warnings import warn

import geopandas as gpd
import pandas as pd
import quilt3
from platformdirs import user_data_dir

from .util import adjust_inflation

script_dir = os.path.dirname(__file__)

_fipstable = pd.read_csv(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "stfipstable.csv"),
    converters={"FIPS Code": str},
)


def _make_data_dir(data_dir="auto"):
    appname = "geosnap"
    appauthor = "geosnap"

    if data_dir == "auto":
        data_dir = user_data_dir(appname, appauthor)

    if not os.path.exists(data_dir):
        pathlib.Path(data_dir).mkdir(parents=True, exist_ok=True)
    return data_dir


def store_seda(data_dir="auto", accept_eula=False):
    """Collect data from the Stanford Educational Data Archive and store as local parquet files

    Parameters
    ----------
    data_dir : str, optional
        path to desired storage location. If "auto", geosnap will use its default data
        directory provided by platformdirs, by default "auto"
    accept_eula : bool, optional
        Whether the accept the EULA from SEDA, by default False
    """

    eula = """
DATA USE AGREEMENT:

You agree not to use the data sets for commercial advantage, or in the course of for-profit activities. Commercial entities wishing to use this Service should contact Stanford University’s Office of Technology Licensing (info@otlmail.stanford.edu).

You agree that you will not use these data to identify or to otherwise infringe the privacy or confidentiality rights of individuals.

THE DATA SETS ARE PROVIDED “AS IS” AND STANFORD MAKES NO REPRESENTATIONS AND EXTENDS NO WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED. STANFORD SHALL NOT BE LIABLE FOR ANY CLAIMS OR DAMAGES WITH RESPECT TO ANY LOSS OR OTHER CLAIM BY YOU OR ANY THIRD PARTY ON ACCOUNT OF, OR ARISING FROM THE USE OF THE DATA SETS.

You agree that this Agreement and any dispute arising under it is governed by the laws of the State of California of the United States of America, applicable to agreements negotiated, executed, and performed within California.

You agree to acknowledge the Stanford Education Data Archive as the source of these data. In publications, please cite the data as:

Reardon, S. F., Ho, A. D., Shear, B. R., Fahle, E. M., Kalogrides, D., Jang, H., & Chavez, B. (2021). Stanford Education Data Archive (Version 4.1). Retrieved from http://purl.stanford.edu/xv742vh9296.

Subject to your compliance with the terms and conditions set forth in this Agreement, Stanford grants you a revocable, non-exclusive, non-transferable right to access and make use of the Data Sets.

        """
    assert accept_eula, (
        f"You must accept the EULA by passing `accept_eula=True` \n{eula}"
    )
    pth = pathlib.Path(_make_data_dir(data_dir), "seda")
    pathlib.Path(pth).mkdir(parents=True, exist_ok=True)

    for std in ["cs", "gcs"]:
        try:
            fn = f"seda_school_pool_{std}_4.1"
            print(f"Downloading {fn}")
            t = pd.read_csv(
                f"https://stacks.stanford.edu/file/druid:xv742vh9296/{fn}.csv",
                converters={"sedasch": str, "fips": str},
            )
            t.sedasch = t.sedasch.str.rjust(12, "0")
            t.fips = t.fips.str.rjust(2, "0")
        except FileNotFoundError as e:
            raise FileNotFoundError("Unable to access remote SEDA data") from e

        t.to_parquet(pathlib.Path(pth, f"{fn}.parquet"))

        for pooling in ["long", "pool"]:
            try:
                fn = f"seda_geodist_{pooling}_{std}_4.1"
                print(f"Downloading {fn}")
                t = pd.read_csv(
                    f"https://stacks.stanford.edu/file/druid:xv742vh9296/{fn}.csv",
                    converters={"sedalea": str, "fips": str},
                )
                t.sedalea = t.sedalea.str.rjust(7, "0")
                t.fips = t.fips.str.rjust(2, "0")
            except FileNotFoundError as e:
                raise FileNotFoundError("Unable to access remote SEDA data") from e

            t.to_parquet(pathlib.Path(pth, f"{fn}.parquet"))


def store_census(data_dir="auto", verbose=True):
    """Save census data to the local quilt package storage.

    Returns
    -------
    None
        Data will be available in the geosnap.data.datasets and will be used
        in place of streaming data for all census queries. The
        census/administrative package is 185 MB.

    """
    quilt3.Package.install(
        "census/tracts_cartographic", "s3://spatial-ucr", dest=_make_data_dir(data_dir)
    )
    quilt3.Package.install(
        "census/administrative", "s3://spatial-ucr", dest=_make_data_dir(data_dir)
    )
    if verbose:
        print(f"Data stored in {_make_data_dir(data_dir)}")


def store_blocks_2000(data_dir="auto"):
    """Save census 2000 census block data to the local quilt package storage.

    Returns
    -------
    None
        Data will be available in the geosnap.data.datasets and will be used
        in place of streaming data for all census queries.

    """
    pth = pathlib.Path(_make_data_dir(data_dir), "blocks_2000")
    pathlib.Path(pth).mkdir(parents=True, exist_ok=True)
    quilt3.Package.install("census/blocks_2000", "s3://spatial-ucr", dest=pth)


def store_blocks_2010(data_dir="auto"):
    """Save census 2010 census block data to the local quilt package storage.

    Returns
    -------
    None
        Data will be available in the geosnap.data.datasets and will be used
        in place of streaming data for all census queries.

    """
    pth = pathlib.Path(_make_data_dir(data_dir), "blocks_2010")
    pathlib.Path(pth).mkdir(parents=True, exist_ok=True)
    quilt3.Package.install("census/blocks_2010", "s3://spatial-ucr", dest=pth)


def store_blocks_2020(data_dir="auto"):
    """Save census 2020 census block data to the local quilt package storage.

    Returns
    -------
    None
        Data will be available in the geosnap.data.datasets and will be used
        in place of streaming data for all census queries.

    """
    pth = pathlib.Path(_make_data_dir(data_dir), "blocks_2020")
    pathlib.Path(pth).mkdir(parents=True, exist_ok=True)
    quilt3.Package.install("census/blocks_2020", "s3://spatial-ucr", dest=pth)


def store_ejscreen(years="all", data_dir="auto"):
    """Save EPA EJScreen data to the local geosnap storage.
       Each year is about 1GB.

     Parameters
    ----------
    years : list (optional)
        subset of years to collect. Currently 2015-2020 vintages
        are available. Pass 'all' (default) to fetch every available vintage.

    Returns
    -------
    None
        Data will be available in the geosnap.data.datasets and will be used
        in place of streaming data for all census queries.

    """
    pth = pathlib.Path(_make_data_dir(data_dir), "epa")
    pathlib.Path(pth).mkdir(parents=True, exist_ok=True)

    if years == "all":
        quilt3.Package.install("epa/ejscreen", "s3://spatial-ucr", dest=pth)

    else:
        if isinstance("years", (str, int)):
            years = [years]
        p = quilt3.Package.browse("epa/ejscreen", "s3://spatial-ucr")
        for year in years:
            p[f"ejscreen_{year}.parquet"].fetch(
                dest=pathlib.Path(pth, f"ejscreen_{year}.parquet")
            )


def store_nces(years="all", dataset="all", data_dir="auto"):
    """Save NCES data to the local geosnap storage.
       Each year is about 1GB.

     Parameters
    ----------
    years : list (optional)
        subset of years to collect. Pass 'all' (default) to fetch every available vintage.
    dataset : str in {"sabs", "districts", "schools"}
        which dataset to store. Defaults to "all" which include all three

    Returns
    -------
    None
        Data will be available in the geosnap.data.datasets and will be used
        in place of streaming data for all census queries.

    """

    datasets = ["sabs", "districts", "schools"] if dataset == "all" else [dataset]

    pth = pathlib.Path(_make_data_dir(data_dir), "nces")
    pathlib.Path(pth).mkdir(parents=True, exist_ok=True)

    for d in datasets:
        if years == "all":
            quilt3.Package.install(f"nces/{d}", "s3://spatial-ucr", dest=pth)

        else:
            if isinstance("years", (str, int)):
                years = [years]
            if d == "districts":
                p = quilt3.Package.browse(f"nces/{d}", "s3://spatial-ucr")
                for year in years:
                    p[f"school_districts_{year}.parquet"].fetch(
                        dest=pathlib.Path(
                            pth, "nces", f"school_districts_{year}.parquet"
                        )
                    )
            else:
                p = quilt3.Package.browse(f"nces/{d}", "s3://spatial-ucr")
                for year in years:
                    p[f"{d}_{year}.parquet"].fetch(
                        dest=pathlib.Path(pth, f"nces{d}_{year}.parquet")
                    )


def store_acs(years="all", level="tract", data_dir="auto"):
    """Save census American Community Survey 5-year data to the local geosnap storage.
       Each year is about 550mb for tract level and about 900mb for blockgroup level.

     Parameters
    ----------
    years : list (optional)
        subset of years to collect. Default is 'all' to fetch every available vintage.
        Currently 2012-2021 vintages are available
    level : str (optional)
        geography level to fetch. Options: {'tract', 'bg'} for tract
        or blockgroup

    Returns
    -------
    None
        Data will be available in the geosnap.data.datasets and will be used
        in place of streaming data for all census queries.

    """
    pth = pathlib.Path(_make_data_dir(data_dir), "acs")
    pathlib.Path(pth).mkdir(parents=True, exist_ok=True)

    if years == "all":
        quilt3.Package.install("census/acs", "s3://spatial-ucr", dest=pth)

    else:
        if isinstance(years, (str, int)):
            years = [years]
        p = quilt3.Package.browse("census/acs", "s3://spatial-ucr")
        for year in years:
            p[f"acs_{year}_{level}.parquet"].fetch(
                dest=pathlib.Path(pth, f"acs_{year}_{level}.parquet")
            )


def _ltdb_reader(path, year, dropcols=None, currency_year=None):
    df = pd.read_csv(
        path,
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
        df = adjust_inflation(df, inflate_available, year, base_year=currency_year)
    return df


def store_ltdb(
    sample_zip=None,
    fullcount_zip=None,
    sample_paths=None,
    fullcount_paths=None,
    data_dir="auto",
    currency_year=2010,
):
    """
    Read & store data from Brown's Longitudinal Tract Database (LTDB).

    Parameters
    ----------
    sample_zip : str
        file path of the zip file containing the standard Sample CSV files
        downloaded from
        https://s4.ad.brown.edu/projects/diversity/Researcher/LTBDDload/Default.aspx
    fullcount_zip: str
        file path of the zip file containing the standard Fullcount CSV files
        downloaded from
        https://s4.ad.brown.edu/projects/diversity/Researcher/LTBDDload/Default.aspx
    sample_paths: dict
        dictionary of CSV files (e.g. if manually unzipping the archive from LTDB). The
        dict should be formatted using `sample_{year}` as the key, with the value storing
        the path to the given csv, as in {'sample_1970': 'path/to/sample_1970.csv',}
    fullcount_paths: dict
        dictionary of CSV files (e.g. if manually unzipping the archive from LTDB). The
        dict should be formatted using `fullcount_{year}` as the key, with the value storing
        the path to the given csv, as in {'fullcount_1970': 'path/to/fullcount_1970.csv',}
    data_dir: str
        directory to store the resulting parquet file. If 'auto' (default) the default
        geosnap data directory will be used (via the `platformdirs` package)
    currency_year : int
        year used to express common dollar values. Default is 2010 meaning all currency
        variables (e.g. median income) will be expressed in real 2010 values.

    Returns
    -------
    None

    """
    codebook = pd.read_csv(Path(script_dir, "variables.csv"))

    if sample_zip is None and sample_paths is None:
        raise ValueError(
            "No Sample Data Found. You must pass either a zip archive of "
            "LTDB data or a dict of csv paths from the unpacked archive "
            "using `sample_{year}` format for the dictionary keys"
        )
    elif sample_paths is None:
        sample_base = "ltdb_std_all_sample/ltdb_std_all_sample/"
        sample_zip = zipfile.ZipFile(sample_zip)
        sample_paths = {
            "sample_1970": sample_zip.open(f"{sample_base}ltdb_std_1970_sample.csv"),
            "sample_1980": sample_zip.open(f"{sample_base}ltdb_std_1980_sample.csv"),
            "sample_1990": sample_zip.open(f"{sample_base}ltdb_std_1990_sample.csv"),
            "sample_2000": sample_zip.open(f"{sample_base}LTDB_Std_ 2000_ Sample.csv"),
            "sample_2010": sample_zip.open(f"{sample_base}LTDB_std_200812_Sample.csv"),
        }

    if fullcount_zip is None and fullcount_paths is None:
        raise ValueError(
            "No Fullcount Data Found. You must pass either a zip archive of "
            "LTDB data or a dict of csv paths from the unpacked archive "
            "using `fullcount_{year}` format for the dictionary keys"
        )
    elif fullcount_paths is None:
        fullcount_base = "ltdb_std_all_fullcount/ltdb_std_all_fullcount/"
        fullcount_zip = zipfile.ZipFile(fullcount_zip)
        fullcount_paths = {
            "fullcount_1970": fullcount_zip.open(
                f"{fullcount_base}LTDB_Std_1970_fullcount.csv"
            ),
            "fullcount_1980": fullcount_zip.open(
                f"{fullcount_base}LTDB_Std_1980_fullcount.csv"
            ),
            "fullcount_1990": fullcount_zip.open(
                f"{fullcount_base}LTDB_Std_1990_fullcount.csv"
            ),
            "fullcount_2000": fullcount_zip.open(
                f"{fullcount_base}LTDB_Std_2000_fullcount.csv"
            ),
        }

    # read in Brown's LTDB data, both the sample and fullcount files for each
    # year population, housing units & occupied housing units appear in both
    # "sample" and "fullcount" files-- currently drop sample and keep fullcount

    # read all samples
    sample70 = _ltdb_reader(
        sample_paths["sample_1970"],
        dropcols=["POP70SP1", "HU70SP", "OHU70SP"],
        year=1970,
        currency_year=currency_year,
    )
    sample80 = _ltdb_reader(
        sample_paths["sample_1980"],
        dropcols=["pop80sf3", "pop80sf4", "hu80sp", "ohu80sp"],
        year=1980,
        currency_year=currency_year,
    )
    sample90 = _ltdb_reader(
        sample_paths["sample_1990"],
        dropcols=["POP90SF3", "POP90SF4", "HU90SP", "OHU90SP"],
        year=1990,
        currency_year=currency_year,
    )
    sample00 = _ltdb_reader(
        sample_paths["sample_2000"],
        dropcols=["POP00SF3", "HU00SP", "OHU00SP"],
        year=2000,
        currency_year=currency_year,
    )
    sample10 = _ltdb_reader(
        sample_paths["sample_2010"], year=2010, currency_year=currency_year
    )

    # read all fullcount files
    fullcount70 = _ltdb_reader(
        fullcount_paths["fullcount_1970"], year=1970, currency_year=currency_year
    )
    fullcount80 = _ltdb_reader(
        fullcount_paths["fullcount_1980"], year=1980, currency_year=currency_year
    )
    fullcount90 = _ltdb_reader(
        fullcount_paths["fullcount_1990"], year=1990, currency_year=currency_year
    )
    fullcount00 = _ltdb_reader(
        fullcount_paths["fullcount_2000"], year=2000, currency_year=currency_year
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
            codebook["ltdb"].tolist(),
            codebook["variable"].tolist(),
        )
    )

    df.rename(renamer, axis="columns", inplace=True)

    # compute additional variables from lookup table
    for row in codebook["formula"].dropna().tolist():
        df.eval(row, inplace=True)

    keeps = df.columns[df.columns.isin(codebook["variable"].tolist() + ["year"])]
    df = df[keeps]

    df.to_parquet(
        os.path.join(_make_data_dir(data_dir), "ltdb.parquet"), compression="brotli"
    )


def store_ncdb(filepath, data_dir="auto"):
    """
    Read & store data from Geolytics's Neighborhood Change Database.

    Parameters
    ----------
    filepath : str
        location of the input CSV file extracted from your Geolytics DVD

    """
    codebook = pd.read_csv(Path(script_dir, "variables.csv"))
    ncdb_vars = codebook["ncdb"].dropna()[1:].values

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
        if col.endswith("D") or col.endswith("N") or col.endswith("1A"):
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

    mapper = dict(zip(codebook().ncdb, codebook().variable))

    df.reset_index(inplace=True)

    df = df.rename(mapper, axis="columns")

    df = df.set_index("geoid")

    for row in codebook["formula"].dropna().tolist():
        try:
            df.eval(row, inplace=True)
        except Exception as e:
            warn(f"Unable to compute {row} with {e}", stacklevel=2)

    keeps = df.columns[df.columns.isin(codebook["variable"].tolist() + ["year"])]

    df = df[keeps]

    df = df.loc[df.n_total_pop != 0]

    df.to_parquet(
        os.path.join(_make_data_dir(data_dir), "ncdb.parquet"), compression="brotli"
    )


def _fips_filter(
    state_fips=None, county_fips=None, msa_fips=None, fips=None, data=None
):
    data = data.copy()
    msa_definitions = pd.read_csv(
        Path(script_dir, "msa_definitions.csv"),
        converters={"stcofips": str, "CBSA Code": str},
    )

    fips_list = []
    for each in [state_fips, county_fips, fips]:
        if isinstance(each, (str,)):
            each = [each]
        if isinstance(each, (list,)):
            fips_list += each
        if any(i.startswith("72") for i in fips_list):
            raise Exception(
                "geosnap does not yet include built-in data for Puerto Rico"
            )
    if msa_fips:
        pr_metros = set(
            msa_definitions[msa_definitions["CBSA Title"].str.contains("PR")][
                "CBSA Code"
            ].tolist()
        )
        if msa_fips in pr_metros:
            raise Exception(
                "geosnap does not yet include built-in data for Puerto Rico"
            )
        fips_list += msa_definitions[msa_definitions["CBSA Code"] == msa_fips][
            "stcofips"
        ].tolist()

    df = data[data.geoid.str.startswith(tuple(fips_list))]

    return df


def _from_db(
    datastore,
    data,
    state_fips=None,
    county_fips=None,
    msa_fips=None,
    fips=None,
    years=None,
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
    tracts = datastore.tracts_2010()
    tracts = tracts[["geoid", "geometry"]]
    tracts = tracts[tracts.geoid.isin(df.geoid)]

    gdf = df.merge(tracts, on="geoid", how="left").set_index("geoid")
    gdf = gpd.GeoDataFrame(gdf)
    return gdf
