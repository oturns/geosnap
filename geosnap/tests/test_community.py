import os

from geosnap import Community, datasets, io

path = os.environ["DLPATH"]

try:
    ltdb = datasets.ltdb
except KeyError:
    io.store_ltdb(sample=path + "/ltdb_sample.zip", fullcount=path + "/ltdb_full.zip")


def test_Community_from_cbsa():

    la = Community.from_ltdb(msa_fips="31080")
    assert la.gdf.shape == (14617, 194)


def test_Community_from_stcofips():

    mn = Community.from_ltdb(state_fips="27", county_fips=["053", "055"])
    assert mn.gdf.shape == (5719, 194)


def test_Community_from_indices():

    chi = Community.from_ncdb(fips=["17031", "17019"])
    assert chi.gdf.shape == (6797, 79)


def test_Community_from_boundary():
    msas = datasets.msas()

    reno = msas[msas["geoid"] == "39900"]
    rn = Community.from_ltdb(boundary=reno)
    assert rn.gdf.shape == (555, 195)


def test_Community_from_census():
    assert Community.from_census(state_fips="24").gdf.shape == (3759, 195)


def test_Community_from_gdfs():

    t90 = datasets.tracts_1990()
    t90 = t90[t90.geoid.str.startswith("11")]
    t00 = datasets.tracts_2000()
    t00 = t00[t00.geoid.str.startswith("11")]

    assert Community.from_geodataframes([t90, t00]).gdf.shape == (380, 192)


def test_Community_from_lodes():
    dc = Community.from_lodes(state_fips="11", years=[2010, 2015])
    assert dc.gdf.shape == (13014, 57)
