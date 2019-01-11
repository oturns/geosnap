from context import data
import os
import pandas as pd

path = os.environ['DLPATH']
read_ltdb = data.read_ltdb

_package_directory = os.path.dirname(os.path.abspath(__file__))

def test_read_ltdb():

    read_ltdb(
        sample=path+"/ltdb_sample.zip",
        fullcount=path+"/ltdb_full.zip",
    )

    df = pd.read_parquet(os.path.join(
        _package_directory, "ltdb.parquet.gzip"))
    df = data.db.ltdb
    assert df.shape == (330388, 192)
