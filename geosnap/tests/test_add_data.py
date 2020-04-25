import os
import pytest 
from geosnap import datasets, io
from pathlib import PurePath

try:
    path = os.environ["GITHUB_WORKSPACE"]
except Exception: 
    path = os.getcwd()


try:
    LTDB = os.environ["LTDB_SAMPLE"]
    NCDB = os.environ["NCDB"]
except:
    LTDB=None
    NCDB=None
store_ltdb = io.store_ltdb
store_ncdb = io.store_ncdb

@pytest.mark.skipif(not LTDB, reason="unable to locate LTDB data")
def test_store_ltdb():

    store_ltdb(sample=PurePath(path, "ltdb_sample.zip"), fullcount=PurePath(path, "ltdb_full.zip"))
    assert datasets.ltdb().shape == (330388, 191)

@pytest.mark.skipif(not NCDB, reason="unable to locate Geolytics data")
def test_store_ncdb():

    store_ncdb(PurePath(path, "ncdb.csv"))
    assert datasets.ncdb().shape == (328633, 76)


def test_get_lehd():

    wac = io.get_lehd()
    rac = io.get_lehd("rac")

    assert wac.shape == (3074, 52)
    assert rac.shape == (4382, 42)
