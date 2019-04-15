import context
import os

path = os.environ['DLPATH']
read_ltdb = context.data.read_ltdb
read_ncdb = context.data.read_ncdb


def test_read_ltdb():

    read_ltdb(
        sample=path+"/ltdb_sample.zip",
        fullcount=path+"/ltdb_full.zip",
    )
    from quilt.data.geosnap_data import data_store
    assert data_store.ltdb().shape == (330388, 192)


def test_read_ncdb():

    read_ncdb(path+"/ncdb.csv")
    from quilt.data.geosnap_data import data_store
    assert data_store.ncdb().shape == (328633, 77)
