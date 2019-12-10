import os

from geosnap import datasets, io

path = os.environ["DLPATH"]
store_ltdb = io.store_ltdb
store_ncdb = io.store_ncdb


def test_store_ltdb():

    store_ltdb(sample=path + "/ltdb_sample.zip", fullcount=path + "/ltdb_full.zip")
    assert datasets.ltdb.shape == (330388, 192)


def test_store_ncdb():

    store_ncdb(path + "/ncdb.csv")
    assert datasets.ncdb.shape == (328633, 77)


def test_get_lehd():

    wac = io.get_lehd()
    rac = io.get_lehd("rac")

    assert wac.shape == (3074, 52)
    assert rac.shape == (4382, 42)
