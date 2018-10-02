import os
from context import data
from zipfile import ZipFile

read_ltdb = data.read_ltdb


def test_read_ltdb():

    state = "AL"
    df = read_ltdb(
        sample=os.path.join(os.getcwd(), "ltdb_test.zip"),
        fullcount=os.path.join(os.getcwd(), "ltdb_test.zip"),
    )
    assert df.state[1] == state
