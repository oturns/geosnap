import os

import pytest
from geosnap import DataStore, io

try:
    LTDB = os.environ["LTDB_SAMPLE"]
    NCDB = os.environ["NCDB"]
except:
    LTDB = None
    NCDB = None

import sys

store = DataStore()


def test_nces_schools():
    schools = io.get_nces(store, dataset="schools")
    assert schools.shape == (102209, 26)


def test_nces_school_dists():
    dists = io.get_nces(store, dataset="school_districts")
    assert dists.shape == (13352, 18)


def test_ejscreen():
    if sys.platform.startswith("win"):
        pytest.skip(
            "skipping test on windows due to mem failure", allow_module_level=True
        )

    else:
        ej = io.get_ejscreen(store, years=[2018], fips=["11"])
        assert ej.shape == (450, 369)


def test_nces_sabs():
    if sys.platform.startswith("win"):
        pytest.skip(
            "skipping test on windows due to mem failure", allow_module_level=True
        )
    else:
        sabs = io.get_nces(store, dataset="sabs")
        assert sabs.shape == (75128, 15)


def test_acs():
    acs = io.get_acs(store, fips="11", years=[2018], level="tract")
    assert acs.shape == (179, 157)


@pytest.mark.skipif(not LTDB, reason="unable to locate LTDB data")
def test_ltdb_from_boundary():
    gdf = io.get_acs(store, state_fips="11", years=[2018], level="tract")
    gdf90 = io.get_ltdb(store, boundary=gdf, years=[1990])
    assert gdf90.shape == (179, 194)


@pytest.mark.skipif(not NCDB, reason="unable to locate NCDB data")
def test_ncdb_from_boundary():
    gdf = io.get_acs(store, state_fips="11", years=[2018], level="tract")
    gdf90 = io.get_ncdb(store, boundary=gdf, years=[1990])
    assert gdf90.shape == (179, 79)
