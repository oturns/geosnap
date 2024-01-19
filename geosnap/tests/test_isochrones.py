from geosnap.analyze import (
    isochrones_from_id,
    isochrones_from_gdf,
)
from geosnap.io import get_acs
from geosnap import DataStore

import pandana as pdna
import geopandas as gpd
import os

if not os.path.exists("./41740.h5"):
    import quilt3 as q3

    b = q3.Bucket("s3://spatial-ucr")
    b.fetch("osm/metro_networks_8k/41740.h5", "./41740.h5")

datasets = DataStore()
sd_tracts = get_acs(datasets, county_fips="06073", years=[2018])
sd_network = pdna.Network.from_hdf5("41740.h5")
example_origin = 1985327805


def test_isos_from_ids():
    iso = isochrones_from_id(example_origin, sd_network, threshold=1600)
    assert iso.area.round(6).tolist()[0] == 0.000128


def test_isos_from_gdf():
    sd_network.nodes_df["geometry"] = gpd.points_from_xy(
        sd_network.nodes_df.x, sd_network.nodes_df.y
    )
    example_point = gpd.GeoDataFrame(
        sd_network.nodes_df.loc[example_origin]
    ).T.set_geometry("geometry")
    example_point = example_point.set_crs(4326)
    t = isochrones_from_gdf(
        origins=example_point,
        network=sd_network,
        threshold=1600,
    )
    assert t.area.round(8).tolist()[0] == 0.00012821
