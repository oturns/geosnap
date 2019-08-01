from context import data


def test_metros():

    mets = data.data_store.msas()
    assert mets.shape == (945, 4)


def test_tracts():

    assert data.data_store.tracts_1990(convert=False).shape[0] == 60658
    assert data.data_store.tracts_2000(convert=False).shape == (65506, 192)
    assert data.data_store.tracts_2010(convert=False).shape == (72832, 194)
