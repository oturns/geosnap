from geosnap.io import get_census
from geosnap import DataStore
from geosnap.analyze import find_k, find_region_k
from numpy.testing import assert_array_equal, assert_array_almost_equal


def test_find_k():
    reno = get_census(msa_fips="39900", datastore=DataStore(), years=[2010])
    columns = [
        "median_household_income",
        "p_poverty_rate",
        "p_unemployment_rate",
    ]

    ks = find_k(
        reno,
        columns=columns,
        method="ward",
        max_k=8,
    )
    # Aspatial Clusters

    assert_array_almost_equal( ks.T.values[0], [2,2,2])
    
def test_find_region_k():
    
    reno = get_census(msa_fips="39900", datastore=DataStore(), years=[2010])
    columns = [
        "median_household_income",
        "p_poverty_rate",
        "p_unemployment_rate",
    ]

    ks = find_region_k(
        reno,
        columns=columns,
        method="ward_spatial",
        max_k=8,
    )
    # Aspatial Clusters

    assert_array_almost_equal( ks.values[0],[2.,2.,2.,2.,2.])