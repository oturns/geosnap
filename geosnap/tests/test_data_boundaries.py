from geosnap import DataStore

datasets = DataStore()


def test_metros():

    mets = datasets.msas()
    assert mets.shape == (939, 4)


def test_tracts():

    assert datasets.tracts_1990().shape[0] == 60658
    assert datasets.tracts_2000().shape == (65677, 192)
    assert datasets.tracts_2010().shape == (72832, 194)
