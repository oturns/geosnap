import context
import os
import pytest

path = os.environ['DLPATH']
read_ltdb = context.data.read_ltdb

osnap_pth = os.path.abspath(context.data.__file__)

#@pytest.mark.run(order=1)
def test_read_ltdb():

    read_ltdb(
        sample=path+"/ltdb_sample.zip",
        fullcount=path+"/ltdb_full.zip",
    )

    assert os.path.exists(os.path.join(os.path.dirname(os.path.abspath(context.data.__file__)), "ltdb.parquet.gzip"))
