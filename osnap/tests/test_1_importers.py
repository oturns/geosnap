from context import data
import os

path = os.environ['DLPATH']
read_ltdb = data.read_ltdb


def test_read_ltdb():

    df = read_ltdb(
        sample=path+"/ltdb_sample.zip",
        fullcount=path+"/ltdb_full.zip",
    )
    assert df.shape == (330388, 192)
