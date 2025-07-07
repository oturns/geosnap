from geosnap.io import get_census
from geosnap import DataStore
from geosnap.analyze import find_k, find_region_k, cluster, regionalize
from numpy.testing import assert_array_equal, assert_array_almost_equal

reno = get_census(msa_fips="39900", datastore=DataStore(), years=[2010])
columns = [
    "median_household_income",
    "p_poverty_rate",
    "p_unemployment_rate",
]


def test_find_k():
    ks = find_k(
        reno,
        columns=columns,
        method="ward",
        max_k=8,
    )
    # Aspatial Clusters

    assert_array_almost_equal(ks.T.values[0], [2, 2, 2])


def test_find_region_k():
    ks = find_region_k(
        reno,
        columns=columns,
        method="ward_spatial",
        max_k=8,
    )
    # Aspatial Clusters

    assert_array_almost_equal(ks.values[0], [2.0, 2.0, 2.0, 2.0, 2.0])


def test_cluster_diagnostics():
    ward, ward_mod = cluster(
        reno, columns=columns, method="ward", n_clusters=5, return_model=True
    )
    assert round(ward_mod.silhouette_score,4) == 0.2991
    assert round(ward_mod.davies_bouldin_score,4) == 1.0336
    assert round(ward_mod.calinski_harabasz_score,4) == 88.6627


def test_region_diagnostics():
    ward, ward_mod = regionalize(
        reno, columns=columns, method="ward_spatial", n_clusters=5, return_model=True
    )
    assert round(ward_mod[2010].boundary_silhouette.boundary_silhouette.mean(),4) ==  0.2076
    assert round(ward_mod[2010].path_silhouette.path_silhouette.mean(),4) ==  -0.0801
    assert round(ward_mod[2010].silhouette_scores.silhouette_score.mean(),4) ==0.063
    assert ward_mod[2010].nearest_label.nearest_label.head().tolist() == [1, 2, 0, 2, 4]

