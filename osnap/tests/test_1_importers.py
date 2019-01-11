import context
import os
from importlib import reload

path = os.environ['DLPATH']
read_ltdb = context.data.read_ltdb

_package_directory = os.path.dirname(os.path.abspath(__file__))


def test_read_ltdb():

    read_ltdb(
        sample=path+"/ltdb_sample.zip",
        fullcount=path+"/ltdb_full.zip",
    )

    reload(context)

    df = context.data.db.ltdb
    assert df.shape == (330388, 192)
