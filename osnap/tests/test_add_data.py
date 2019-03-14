import context
import os

path = os.environ['DLPATH']
read_ltdb = context.data.read_ltdb


def test_read_ltdb():

    read_ltdb(
        sample=path+"/ltdb_sample.zip",
        fullcount=path+"/ltdb_full.zip",
    )
    from quilt.data.osnap_data import data_store
    assert data_store.ltdb().shape == (330388, 192)
