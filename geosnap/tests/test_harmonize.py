import os

import quilt3
from numpy.testing import assert_allclose

from geosnap import DataStore
from geosnap.harmonize import harmonize
from geosnap.io import get_census

def test_harmonize_area():
    la = get_census(county_fips="06037", datastore=DataStore())

    harmonized = harmonize(
        la,
        2000,
        extensive_variables=["n_total_housing_units"],
        intensive_variables=["p_vacant_housing_units"],
    )

    assert_allclose(
        harmonized[harmonized.year == 2000].n_total_housing_units.sum(),
        3271578.974605,
        atol=600,
    )
    assert_allclose(
        harmonized[harmonized.year == 1990].n_total_housing_units.sum(),
        3163560.996240,
    )
    assert_allclose(
        harmonized[harmonized.year == 2010].n_total_housing_units.sum(),
        3441415.997327,
    )
    assert_allclose(
        harmonized.p_vacant_housing_units.sum(), 33011.58879, rtol=1e-03
    )


def test_harmonize_area_weighted():

    balt = get_census(county_fips="24510", datastore=DataStore())
    harmonized_nlcd_weighted = harmonize(balt,
        2000,
        extensive_variables=["n_total_housing_units"],
        intensive_variables=["p_vacant_housing_units"],
        weights_method="dasymetric",
        raster='https://spatial-ucr.s3.amazonaws.com/nlcd/landcover/nlcd_landcover_2011.tif',
    )
    assert harmonized_nlcd_weighted.n_total_housing_units.sum().round(0) == 900620.0
    assert_allclose(
        harmonized_nlcd_weighted.p_vacant_housing_units.sum(),
        8832.8796,
        rtol=1e-03,
    )

def test_harmonize_target_gdf():

    balt = get_census(county_fips="24510", datastore=DataStore())
    tgt_gdf = balt[balt.year==2000][['geometry']]
    gdf = harmonize(balt,
        target_gdf=tgt_gdf,
        extensive_variables=["n_total_housing_units"],
        intensive_variables=["p_vacant_housing_units"],
    )
    assert gdf.n_total_housing_units.sum().round(0) == 900620.0
    assert_allclose(
        gdf.p_vacant_housing_units.sum(),
        8832.8796,
        rtol=1e-03,
    )
