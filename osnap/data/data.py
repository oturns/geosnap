"""'
Data reader for longitudinal databases LTDB, geolytics NCDB and NHGIS
"""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import zipfile
from warnings import warn
from gdal import osr, ogr

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


def tiger_to_tract(infile):

    # Modified from original at
    # https://svn.osgeo.org/gdal/tags/1.4.3/gdal/pymod/samples/tigerpoly.py

    class Module:
        def __init__(self):
            self.lines = {}
            self.poly_line_links = {}

    outfile = 'poly.shp'

    # Open the datasource to operate on.

    ds = ogr.Open(infile, update=0)
    poly_layer = ds.GetLayerByName('Polygon')

    # Create output file for the composed polygons.

    nad83 = osr.SpatialReference()
    nad83.SetFromUserInput('NAD83')

    shp_driver = ogr.GetDriverByName('ESRI Shapefile')
    shp_driver.DeleteDataSource(outfile)

    shp_ds = shp_driver.CreateDataSource(outfile)

    shp_layer = shp_ds.CreateLayer('out', geom_type=ogr.wkbPolygon, srs=nad83)

    src_defn = poly_layer.GetLayerDefn()
    poly_field_count = src_defn.GetFieldCount()

    for fld_index in range(poly_field_count):
        src_fd = src_defn.GetFieldDefn(fld_index)

        fd = ogr.FieldDefn(src_fd.GetName(), src_fd.GetType())
        fd.SetWidth(src_fd.GetWidth())
        fd.SetPrecision(src_fd.GetPrecision())
        shp_layer.CreateField(fd)

    # Read all features in the line layer, holding just the geometry in a hash
    # for fast lookup by TLID.

    line_layer = ds.GetLayerByName('CompleteChain')
    line_count = 0

    modules_hash = {}

    feat = line_layer.GetNextFeature()
    geom_id_field = feat.GetFieldIndex('TLID')
    tile_ref_field = feat.GetFieldIndex('MODULE')
    while feat is not None:
        geom_id = feat.GetField(geom_id_field)
        tile_ref = feat.GetField(tile_ref_field)

        try:
            module = modules_hash[tile_ref]
        except:
            module = Module()
            modules_hash[tile_ref] = module

        module.lines[geom_id] = feat.GetGeometryRef().Clone()
        line_count = line_count + 1

        feat.Destroy()

        feat = line_layer.GetNextFeature()

    # Read all polygon/chain links and build a hash keyed by POLY_ID listing
    # the chains (by TLID) attached to it.

    link_layer = ds.GetLayerByName('PolyChainLink')

    feat = link_layer.GetNextFeature()
    geom_id_field = feat.GetFieldIndex('TLID')
    tile_ref_field = feat.GetFieldIndex('MODULE')
    lpoly_field = feat.GetFieldIndex('POLYIDL')
    rpoly_field = feat.GetFieldIndex('POLYIDR')

    link_count = 0

    while feat is not None:
        module = modules_hash[feat.GetField(tile_ref_field)]

        tlid = feat.GetField(geom_id_field)

        lpoly_id = feat.GetField(lpoly_field)
        rpoly_id = feat.GetField(rpoly_field)

        if lpoly_id == rpoly_id:
            feat.Destroy()
            feat = link_layer.GetNextFeature()
            continue

        try:
            module.poly_line_links[lpoly_id].append(tlid)
        except:
            module.poly_line_links[lpoly_id] = [tlid]

        try:
            module.poly_line_links[rpoly_id].append(tlid)
        except:
            module.poly_line_links[rpoly_id] = [tlid]

        link_count = link_count + 1

        feat.Destroy()

        feat = link_layer.GetNextFeature()

    # Process all polygon features.

    feat = poly_layer.GetNextFeature()
    tile_ref_field = feat.GetFieldIndex('MODULE')
    polyid_field = feat.GetFieldIndex('POLYID')

    poly_count = 0
    degenerate_count = 0

    while feat is not None:
        module = modules_hash[feat.GetField(tile_ref_field)]
        polyid = feat.GetField(polyid_field)

        tlid_list = module.poly_line_links[polyid]

        link_coll = ogr.Geometry(type=ogr.wkbGeometryCollection)
        for tlid in tlid_list:
            geom = module.lines[tlid]
            link_coll.AddGeometry(geom)

        try:
            poly = ogr.BuildPolygonFromEdges(link_coll)

            if poly.GetGeometryRef(0).GetPointCount() < 4:
                degenerate_count = degenerate_count + 1
                poly.Destroy()
                feat.Destroy()
                feat = poly_layer.GetNextFeature()
                continue

            # print poly.ExportToWkt()
            # feat.SetGeometryDirectly( poly )

            feat2 = ogr.Feature(feature_def=shp_layer.GetLayerDefn())

            for fld_index in range(poly_field_count):
                feat2.SetField(fld_index, feat.GetField(fld_index))

            feat2.SetGeometryDirectly(poly)

            shp_layer.CreateFeature(feat2)
            feat2.Destroy()

            poly_count = poly_count + 1
        except:
            warn('BuildPolygonFromEdges failed.')

        feat.Destroy()

        feat = poly_layer.GetNextFeature()

    if degenerate_count:
        warn('Discarded %d degenerate polygons.' % degenerate_count)

    print('Built %d polygons.' % poly_count)

    # Cleanup

    shp_ds.Destroy()
    ds.Destroy()

    # build a fully-qualified fips code and dissolve on it to create tract geographies
    gdf = gpd.read_file(outfile)

    if "CTBNA90" in gdf.columns:

        gdf = gdf.rename(columns={"CTBNA90": 'TRACT'})

    gdf['STATE'] = gdf['STATE'].astype(str).str.rjust(2, "0")

    gdf['COUNTY'] = gdf['COUNTY'].astype(str).str.rjust(3, "0")

    gdf['TRACT'] = gdf['TRACT'].astype(str).str.rjust(4, "0")

    gdf['fips'] = gdf.STATE + gdf.COUNTY + gdf.TRACT + '00'

    gdf = gdf.dropna(subset=['fips'])

    gdf.geometry = gdf.buffer(0)

    gdf = gdf.dissolve(by='fips')

    gdf.reset_index(inplace=True)

    gdf.to_file(outfile)

    return gdf
