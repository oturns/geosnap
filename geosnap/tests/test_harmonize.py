from numpy.testing import assert_allclose
import os
import quilt3
from geosnap import Community

local_raster = os.path.join(os.getcwd(), "nlcd_2011.tif")    # portability
if not os.path.exists(local_raster):
    p = quilt3.Package.browse("rasters/nlcd", "s3://spatial-ucr")
    p["nlcd_2011.tif"].fetch()


def test_harmonize_area():
    la = Community.from_census(county_fips="06037")

    harmonized = la.harmonize(
        2000,
        extensive_variables=["n_total_housing_units"],
        intensive_variables=["p_vacant_housing_units"],
        raster=local_raster
    )

    assert_allclose(
        harmonized.gdf[harmonized.gdf.year == 2000].n_total_housing_units.sum(),
        3271578.974605,
        atol=600,
    )
    assert_allclose(
        harmonized.gdf[harmonized.gdf.year == 1990].n_total_housing_units.sum(),
        3163560.996240,
    )
    assert_allclose(
        harmonized.gdf[harmonized.gdf.year == 2010].n_total_housing_units.sum(),
        3441415.997327,
    )
    assert_allclose(
        harmonized.gdf.p_vacant_housing_units.sum(), 33011.58879, rtol=1e-03
    )


def test_harmonize_area_weighted():

    balt = Community.from_census(county_fips="24510")
    harmonized_nlcd_weighted = balt.harmonize(
        2000,
        extensive_variables=["n_total_housing_units"],
        intensive_variables=["p_vacant_housing_units"],
        weights_method="land_type_area",
        raster=local_raster
    )
    assert harmonized_nlcd_weighted.gdf.n_total_housing_units.sum() == 900620.0
    assert_allclose(
        harmonized_nlcd_weighted.gdf.p_vacant_housing_units.sum(), 8832.8796, rtol=1e-03
    )
