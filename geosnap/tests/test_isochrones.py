from geosnap.analyze import (
    isochrones_from_id,
    isochrones_from_gdf,
)
from geosnap import DataStore
from geosnap.io import get_acs, get_network_from_gdf, project_network
import pandana as pdna
import geopandas as gpd
import os
import pytest
import sys
from numpy.testing import assert_almost_equal
import osmnx as ox

def get_data():
    if not os.path.exists("./41740.h5"):
        import quilt3 as q3

        b = q3.Bucket("s3://spatial-ucr")
        b.fetch("osm/metro_networks_8k/41740.h5", "./41740.h5")
    sd_network = pdna.Network.from_hdf5("41740.h5")
    example_origin = 1985327805

    return example_origin, sd_network


@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="skipping test on windows because of dtype issue",
)
@pytest.mark.xdist_group(name="group1")
def test_isos_from_ids():
    example_origin, sd_network = get_data()
    iso = isochrones_from_id(example_origin, sd_network, threshold=1600, hull='libpysal')
    assert_almost_equal(iso.area.round(6).astype(float).tolist()[0], 0.000128)


@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="skipping test on windows because of dtype issue",
)
@pytest.mark.xdist_group(name="group1")
def test_isos_from_gdf_pysal():
    example_origin, sd_network = get_data()
    sd_network.nodes_df["geometry"] = gpd.points_from_xy(
        sd_network.nodes_df.x, sd_network.nodes_df.y
    )
    example_point = gpd.GeoDataFrame(
        sd_network.nodes_df.loc[[example_origin]]
    )
    example_point = example_point.set_crs(4326)
    t = isochrones_from_gdf(
        origins=example_point,
        network=sd_network,
        threshold=1600,
        hull='libpysal'
    )
    assert_almost_equal(t.area.astype(float).round(8).tolist()[0], 0.00012821)

@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="skipping test on windows because of dtype issue",
)
@pytest.mark.xdist_group(name="group1")
def test_isos_from_gdf_shapely():
    example_origin, sd_network = get_data()
    sd_network.nodes_df["geometry"] = gpd.points_from_xy(
        sd_network.nodes_df.x, sd_network.nodes_df.y
    )
    example_point = gpd.GeoDataFrame(
        sd_network.nodes_df.loc[[example_origin]]
    )
    example_point = example_point.set_crs(4326)
    t = isochrones_from_gdf(
        origins=example_point,
        network=sd_network,
        threshold=1600,
    )
    assert_almost_equal(t.area.astype(float).round(8).tolist()[0], 0.00012474)

@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="skipping test on windows because of dtype issue",
)
def test_network_constructor():
    tracts = get_acs(DataStore(), county_fips='48301', level='tract', years=2015)
    walk_net = get_network_from_gdf(tracts)
    # this will grow depending on the size of the OSM network when tested...
    assert walk_net.edges_df.shape[0] > 6000

@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="skipping test on windows because of dtype issue",
)
def test_isos_with_edges():
    tracts = get_acs(DataStore(), county_fips='48301', level='tract', years=2015)
    walk_net = get_network_from_gdf(tracts)
    type(walk_net)
    facilities = ox.features.features_from_polygon(
    tracts.union_all(), {"amenity": "fuel"}
)
    #facilities = facilities[facilities.geometry.type == "Point"]
    alpha = isochrones_from_gdf(
    facilities, network=walk_net, threshold=2000, use_edges=True
)
    print(alpha.area.round(8))
    # this will grow depending on the size of the OSM network when tested...
    assert alpha.area.round(8).iloc[0] >= 0.00036433

@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="skipping test on windows because of dtype issue",
)
def test_project_network():   
    tracts = get_acs(DataStore(), county_fips='48301', level='tract', years=2015)
    walk_net = get_network_from_gdf(tracts)
    # this will grow depending on the size of the OSM network when tested...
    tracts = tracts.to_crs(tracts.estimate_utm_crs())
    walk_net = project_network(walk_net, output_crs=tracts.crs)
    nodes = walk_net.get_node_ids(tracts.centroid.x, tracts.centroid.y)
    print(nodes)
    assert nodes[0] == 7876436325