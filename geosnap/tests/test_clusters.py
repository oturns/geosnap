from context import quilter

quilter()
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

    reno.cluster(columns=columns, method="gaussian_mixture", best_model=True)
    assert len(reno.gdf.gaussian_mixture.unique()) > 7


def test_ward():

    reno.cluster(columns=columns, method="ward")
    assert len(reno.gdf.ward.unique()) == 6


def test_spectral():

    reno.cluster(columns=columns, method="spectral")
    assert len(reno.gdf.spectral.unique()) == 6


def test_kmeans():

    reno.cluster(columns=columns, method="kmeans")
    assert len(reno.gdf.kmeans.unique()) == 6


def test_aff_prop():

    reno.cluster(columns=columns, method="affinity_propagation", preference=-100)
    assert len(reno.gdf.affinity_propagation.unique()) == 3


def test_hdbscan():

    reno.cluster(columns=columns, method="hdbscan")
    assert len(reno.gdf.hdbscan.unique()) > 27


# Spatial Clusters


def test_spenc():

    reno.cluster_spatial(columns=columns, method="spenc")
    assert len(reno.gdf.spenc.unique()) == 7


def test_maxp():

    reno.cluster_spatial(columns=columns, method="max_p", initial=10)
    assert len(reno.gdf.max_p.unique()) > 9


def test_ward_spatial():

    reno.cluster_spatial(columns=columns, method="ward_spatial")
    assert len(reno.gdf.ward_spatial.unique()) == 7


def test_skater():

    reno.cluster_spatial(columns=columns, method="skater", n_clusters=10)
    assert len(reno.gdf.skater.unique()) == 11


def test_azp():
    reno.cluster_spatial(columns=columns, method="azp")
    assert len(reno.gdf.azp.unique()) == 7
