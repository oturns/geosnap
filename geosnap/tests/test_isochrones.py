from geosnap.analyze import (
    isochrones_from_id,
    isochrones_from_gdf,
)

import pandana as pdna
import geopandas as gpd
import os
import pytest
import sys
from numpy.testing import assert_almost_equal


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
    iso = isochrones_from_id(example_origin, sd_network, threshold=1600)
    assert_almost_equal(iso.area.round(6).astype(float).tolist()[0], 0.000128)


@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="skipping test on windows because of dtype issue",
)
@pytest.mark.xdist_group(name="group1")
def test_isos_from_gdf():
    example_origin, sd_network = get_data()
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
    assert_almost_equal(t.area.astype(float).round(8).tolist()[0], 0.00012821)
