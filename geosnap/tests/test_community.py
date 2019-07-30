from context import data

import os

path = os.environ["DLPATH"]

try:
    ltdb = data.data_store.ltdb
except KeyError:
    data.store_ltdb(sample=path + "/ltdb_sample.zip", fullcount=path + "/ltdb_full.zip")


def test_Community_from_cbsa():

    la = data.Community.from_ltdb(msa_fips="31080")

    assert la.tracts.shape == (2929, 2)
    assert la.census.shape == (14613, 192)


def test_Community_from_stcofips():

    mn = data.Community.from_ltdb(state_fips="27", county_fips=["053", "055"])
    assert mn.tracts.shape == (304, 2)
    assert mn.census.shape == (1515, 192)


def test_Community_from_indices():

    chi = data.Community.from_ncdb(fips=["17031", "17019"])
    assert chi.tracts.shape == (1362, 2)
    assert chi.census.shape == (6805, 192)
