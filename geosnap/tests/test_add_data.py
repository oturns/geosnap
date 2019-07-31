from context import quilter

quilter()
import context
import os
from context import data

path = os.environ["DLPATH"]
store_ltdb = context.data.store_ltdb
store_ncdb = context.data.store_ncdb


def test_store_ltdb():

    store_ltdb(sample=path + "/ltdb_sample.zip", fullcount=path + "/ltdb_full.zip")
    assert data.data_store.ltdb.shape == (330388, 192)


def test_store_ncdb():

    store_ncdb(path + "/ncdb.csv")
    assert data.data_store.ncdb.shape == (328633, 77)
