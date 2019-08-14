from context import data
import os

path = os.environ["DLPATH"]

if not os.path.exists(
    os.path.join(os.path.dirname(os.path.abspath(data.__file__)), "ltdb.parquet")
):
    data.store_ltdb(sample=path + "/ltdb_sample.zip", fullcount=path + "/ltdb_full.zip")

reno = data.Community.from_ltdb(msa_fips="39900")
columns = ["median_household_income", "p_poverty_rate", "p_unemployment_rate"]

# Aspatial Clusters


def test_gm():

    r = reno.cluster(columns=columns, method="gaussian_mixture", best_model=True)
    assert len(r.gdf.gaussian_mixture.unique()) >= 6


def test_ward():

    r = reno.cluster(columns=columns, method="ward")
    assert len(r.gdf.ward.unique()) == 6


def test_spectral():

    r = reno.cluster(columns=columns, method="spectral")
    assert len(r.gdf.spectral.unique()) == 6


def test_kmeans():

    r = reno.cluster(columns=columns, method="kmeans")
    assert len(r.gdf.kmeans.unique()) == 6


def test_aff_prop():

    r = reno.cluster(columns=columns, method="affinity_propagation", preference=-100)
    assert len(r.gdf.affinity_propagation.unique()) == 3


def test_hdbscan():

    r = reno.cluster(columns=columns, method="hdbscan")
    assert len(r.gdf.hdbscan.unique()) > 27


# Spatial Clusters


def test_spenc():

    r = reno.cluster_spatial(columns=columns, method="spenc")
    assert len(r.gdf.spenc.unique()) == 6


def test_maxp():

    r = reno.cluster_spatial(columns=columns, method="max_p", initial=10)
    assert len(r.gdf.max_p.unique()) > 9


def test_ward_spatial():

    r = reno.cluster_spatial(columns=columns, method="ward_spatial", n_clusters=7)
    assert len(r.gdf.ward_spatial.unique()) == 7


def test_skater():

    r = reno.cluster_spatial(columns=columns, method="skater", n_clusters=10)
    assert len(r.gdf.skater.unique()) == 10


def test_azp():
    r = reno.cluster_spatial(columns=columns, method="azp", n_clusters=7)
    assert len(r.gdf.azp.unique()) == 7
