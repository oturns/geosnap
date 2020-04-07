import os
import pytest 
from geosnap import datasets, io

path = os.environ["DLPATH"]
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

    store_ltdb(sample=path + "/ltdb_sample.zip", fullcount=path + "/ltdb_full.zip")
    assert datasets.ltdb().shape == (330388, 192)

@pytest.mark.skipif(not NCDB, reason="unable to locate Geolytics data")
def test_store_ncdb():

    store_ncdb(path + "/ncdb.csv")
    assert datasets.ncdb().shape == (328633, 77)


def test_get_lehd():

    wac = io.get_lehd()
    rac = io.get_lehd("rac")

    assert wac.shape == (3074, 52)
    assert rac.shape == (4382, 42)
