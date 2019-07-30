from context import data

import os

path = os.environ["DLPATH"]

try:
    ltdb = data.data_store.ltdb
except KeyError:
    data.store_ltdb(sample=path + "/ltdb_sample.zip", fullcount=path + "/ltdb_full.zip")


def test_Community_from_cbsa():

    la = data.Community.from_ltdb(msa_fips="31080")
    assert la.gdf.shape == (14617, 193)


def test_Community_from_stcofips():

    mn = data.Community.from_ltdb(state_fips="27", county_fips=["053", "055"])
    assert mn.gdf.shape == (5719, 193)


def test_Community_from_indices():

    chi = data.Community.from_ncdb(fips=["17031", "17019"])
    assert chi.gdf.shape == (6805, 193)
