from context import data
import os

path = os.environ['DLPATH']
read_ltdb = data.read_ltdb


def test_read_ltdb():

    read_ltdb(
        sample=path+"/ltdb_sample.zip",
        fullcount=path+"/ltdb_full.zip",
    )
    df = data.db.ltdb
    assert df.shape == (330388, 192)
