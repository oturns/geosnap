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


def test_get_lehd_v7():

    wac = io.get_lehd(version=7)
    rac = io.get_lehd("rac", version=7)

    assert wac.shape == (3074, 52)
    assert rac.shape == (4382, 42)

def test_get_lehd_v8():

    wac = io.get_lehd(version=8)
    rac = io.get_lehd("rac", version=8)

    assert wac.shape == (3269, 52)
    assert rac.shape == (4553, 42)



def test_store_acs():
    io.store_acs(2012)
