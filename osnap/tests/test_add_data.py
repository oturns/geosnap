import context
import os

path = os.environ['DLPATH']
read_ltdb = context.data.read_ltdb


def test_read_ltdb():

    read_ltdb(
        sample=path+"/ltdb_sample.zip",
        fullcount=path+"/ltdb_full.zip",
    )
