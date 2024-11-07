"""Utilities for fetching data from GADM."""

import geopandas as gpd


def get_gadm(code, level=0):
    """Collect data from GADM as a geodataframe.

    Parameters
    ----------
    code : str
        three character ISO code for a country
    level : int, optional
        which geometry level to collect, by default 0

    Returns
    -------
    geopandas.GeoDataFrame
        geodataframe containing GADM data

    Notes
    -------
    If not using the fsspec package, this function uses fiona's syntax to read a geodataframe directly with
    geopandas `read_file` function. Unfortunately, sometimes the operation fails
    before the read is complete resulting in an error--or occasionally, a
    geodataframe with missing rows. Repeating the call sometimes helps.

    When using fsspec, the function doesn't suffer these issues, but requires an additional dependency.
    If fsspec is available, this function its syntax to store a temporary file which is then
    read in by geopandas. In theory, the file could be read into fsspec directly
    without storing it in a temporary directory, but when reading a bytestream of GPKG,
    geopandas does not allow the specification of a particular layer (so reading GPKG
    with this method would always returns the layer with index 0 in the geopackage file).
    """
    code = code.upper()

    gdf = gpd.read_file(
        f"https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_{code}.gpkg",
        layer=f"ADM_ADM_{level}",
    )
    return gdf
