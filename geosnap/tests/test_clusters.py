import numpy as np
from numpy.testing import assert_array_equal

from geosnap import DataStore
from geosnap.analyze import cluster, regionalize
from geosnap.io import get_census

reno = get_census(msa_fips="39900", datastore=DataStore())
columns = [
    "median_household_income",
    "p_poverty_rate",
    "p_unemployment_rate",
]

# Aspatial Clusters


def test_gm():

    r = cluster(reno, columns=columns, method="gaussian_mixture", best_model=True)
    assert len(r.gaussian_mixture.unique()) >= 5


def test_ward():
    r = cluster(reno, columns=columns, method="ward")
    assert len(r.ward.unique()) == 7


def test_spectral():

    r = cluster(reno, columns=columns, method="spectral")
    assert len(r.spectral.unique()) == 7


def test_kmeans():

    r = cluster(reno, columns=columns, method="kmeans")
    assert len(r.kmeans.unique()) == 7


def test_aff_prop():

    r = cluster(
        reno,
        columns=columns,
        method="affinity_propagation",
        cluster_kwargs=dict(preference=-100),
    )
    assert len(r.affinity_propagation.unique()) == 3


def test_hdbscan():

    r = cluster(reno, columns=columns, method="hdbscan")
    assert len(r.hdbscan.unique()) >= 4


def test_ward_pooling_unique():
    r = cluster(
        reno,
        columns=columns,
        method="ward",
        pooling="unique",
        model_colname="ward_unique",
    )
    labels = r.ward_unique.dropna().astype(int).astype(str).values
    assert_array_equal(
        labels,
        np.array(
            [
                "5",
                "2",
                "5",
                "0",
                "0",
                "0",
                "0",
                "4",
                "4",
                "5",
                "4",
                "2",
                "0",
                "0",
                "1",
                "5",
                "2",
                "5",
                "2",
                "0",
                "0",
                "1",
                "1",
                "0",
                "2",
                "1",
                "1",
                "1",
                "0",
                "1",
                "1",
                "5",
                "5",
                "1",
                "4",
                "3",
                "3",
                "1",
                "1",
                "4",
                "1",
                "5",
                "0",
                "0",
                "4",
                "4",
                "2",
                "4",
                "0",
                "0",
                "2",
                "1",
                "0",
                "0",
                "5",
                "0",
                "1",
                "1",
                "0",
                "1",
                "0",
                "3",
                "1",
                "1",
                "5",
                "4",
                "0",
                "5",
                "0",
                "0",
                "0",
                "0",
                "1",
                "2",
                "2",
                "1",
                "0",
                "0",
                "1",
                "0",
                "4",
                "1",
                "4",
                "4",
                "4",
                "4",
                "0",
                "2",
                "1",
                "2",
                "4",
                "4",
                "4",
                "4",
                "1",
                "0",
                "4",
                "0",
                "5",
                "5",
                "5",
                "2",
                "2",
                "0",
                "2",
                "5",
                "0",
                "1",
                "1",
                "0",
                "4",
                "1",
                "0",
                "5",
                "0",
                "5",
                "5",
                "1",
                "4",
                "5",
                "0",
                "3",
                "2",
                "5",
                "1",
                "3",
                "4",
                "4",
                "1",
                "1",
                "0",
                "0",
                "2",
                "1",
                "4",
                "4",
                "3",
                "4",
                "4",
                "1",
                "2",
                "2",
                "1",
                "3",
                "4",
                "1",
                "0",
                "0",
                "1",
                "0",
                "1",
                "4",
                "4",
                "2",
                "4",
                "3",
                "5",
                "0",
                "4",
                "3",
                "5",
                "0",
                "1",
                "1",
                "1",
                "1",
                "5",
                "0",
                "1",
                "1",
                "0",
                "0",
                "5",
                "1",
                "0",
                "1",
                "1",
                "2",
                "5",
                "1",
                "4",
                "4",
                "3",
                "1",
                "3",
                "0",
                "0",
                "1",
                "3",
                "1",
                "2",
                "0",
                "0",
                "2",
                "2",
                "1",
                "4",
                "2",
                "2",
                "2",
                "4",
                "5",
                "0",
                "1",
                "1",
                "1",
                "3",
                "0",
                "1",
                "0",
                "0",
                "4",
                "3",
                "0",
                "0",
                "0",
                "4",
                "0",
                "4",
                "3",
                "1",
                "0",
                "4",
                "0",
                "3",
            ],
            dtype=object,
        ),
    )


# Spatial Clusters


def test_spenc():

    r = regionalize(reno, columns=columns, method="spenc")
    assert len(r.spenc.unique()) >= 6


def test_maxp_count():

    r = regionalize(
        reno, columns=columns, method="max_p", region_kwargs=dict(initial=10)
    )
    assert len(r.max_p.unique()) >= 8


def test_maxp_thresh():

    r = regionalize(
        reno,
        columns=columns,
        method="max_p",
        region_kwargs=dict(initial=10),
        threshold_variable="n_total_pop",
        threshold=10000,
    )
    assert len(r.max_p.unique()) >= 8


def test_ward_spatial():

    r = regionalize(reno, columns=columns, method="ward_spatial", n_clusters=7)
    assert len(r.ward_spatial.unique()) == 8


def test_skater():

    r = regionalize(reno, columns=columns, method="skater", n_clusters=10)
    assert len(r.skater.unique()) == 11


def test_azp():
    r = regionalize(reno, columns=columns, method="azp", n_clusters=7)
    assert len(r.azp.unique()) == 8


# Test seeding


def test_seed():
    # Ward is deterministic
    np.random.seed(12345)
    r = cluster(reno, columns=columns, method="ward")
    card = r.groupby("ward").count()["geoid"].values
    np.testing.assert_array_equal(card, [27, 83, 19, 51, 38, 7])


def test_random_state():

    # no seeds
    reno = get_census(msa_fips="39900", datastore=DataStore())
    r1 = cluster(reno, columns=columns, method="kmeans", n_clusters=7)
    r2 = cluster(reno, columns=columns, method="kmeans", n_clusters=7)
    card1 = r1.groupby("kmeans").count()["geoid"].values
    card1.sort()
    card2 = r2.groupby("kmeans").count()["geoid"].values
    card2.sort()
    # test that the cardinalities are different
    np.testing.assert_raises(
        AssertionError, np.testing.assert_array_equal, card1, card2
    )

    # seeds
    reno = get_census(msa_fips="39900", datastore=DataStore())
    seed = 10
    r1 = cluster(
        reno, columns=columns, method="kmeans", n_clusters=5, random_state=seed
    )
    r2 = cluster(
        reno, columns=columns, method="kmeans", n_clusters=5, random_state=seed
    )
    card1 = r1.groupby("kmeans").count()["geoid"].values
    card1.sort()
    card2 = r2.groupby("kmeans").count()["geoid"].values
    card2.sort()
    # test that the cardinalities are identical
    np.testing.assert_array_equal(card1, card2)
