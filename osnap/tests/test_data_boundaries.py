from context import data

from quilt.data.spatialucr import census
from quilt.data.spatialucr import census_cartographic


def test_metros():

    mets = data.metros
    assert mets.shape == (945, 4)


def test_tracts():

    assert census.tracts_1990().shape == (61332, 3)
    assert census.tracts_2000().shape == (65506, 2)
    assert census.tracts_2010().shape == (73056, 2)

    assert census_cartographic.tracts_1990().shape == (61693, 2)
    assert census_cartographic.tracts_2000().shape == (66688, 2)
