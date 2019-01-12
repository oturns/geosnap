import context
import os

path = os.environ['DLPATH']
read_ltdb = context.data.read_ltdb


def test_read_ltdb():

    read_ltdb(
        sample=path+"/ltdb_sample.zip",
        fullcount=path+"/ltdb_full.zip",
    )

    assert os.path.exists(os.path.join(os.path.dirname(os.path.abspath(context.data.__file__)), "ltdb.parquet.gzip"))
