import os
from pathlib import PurePath

import pytest

from geosnap import DataStore, io

datasets = DataStore()

try:
    path = os.environ["GITHUB_WORKSPACE"]
except Exception:
    path = os.getcwd()


try:
    LTDB = os.environ["LTDB_SAMPLE"]
    NCDB = os.environ["NCDB"]
except:
    LTDB = None
    NCDB = None
store_ltdb = io.store_ltdb
store_ncdb = io.store_ncdb


@pytest.mark.skipif(not LTDB, reason="unable to locate LTDB data")
def test_store_ltdb():

    store_ltdb(
        sample=PurePath(path, "ltdb_sample.zip"),
        fullcount=PurePath(path, "ltdb_full.zip"),
    )
    assert datasets.ltdb().shape == (330388, 191)


@pytest.mark.skipif(not NCDB, reason="unable to locate Geolytics data")
def test_store_ncdb():

    store_ncdb(PurePath(path, "ncdb.csv"))
    assert datasets.ncdb().shape == (328633, 76)


def test_get_lodes_wac_v7():
    wac = io.get_lodes(datasets, state_fips=['11'], years=[2015], version=7)
    assert wac.shape == (6507, 57)

def test_get_lodes_rac_v7():
    rac = io.get_lodes(datasets, dataset="rac", state_fips=['11'], years=[2015], version=7)
    assert rac.shape == (6507, 47)

def test_get_lodes_wac_v8():
    wac = io.get_lodes(datasets, state_fips=['11'], years=[2015], version=7)
    assert wac.shape == (6507, 57)

def test_get_lodes_rac_v8():
    rac = io.get_lodes(datasets, dataset="rac", state_fips=['11'], years=[2015], version=8)
    assert rac.shape == (6012, 49)


def test_store_acs():
    io.store_acs(2012)
    assert os.path.exists(PurePath(datasets.show_data_dir(), "acs", "acs_2012_tract.parquet"))
