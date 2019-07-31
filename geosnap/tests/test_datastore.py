from context import quilter

quilter()
from context import data


def test_tracts90():
    df = data.data_store.tracts_1990()
    assert df.shape == (60658, 164)


def test_tracts00():
    df = data.data_store.tracts_2000(convert=False)
    assert df.shape == (65506, 192)


def test_tracts10():
    df = data.data_store.tracts_2010(convert=False)
    assert df.shape == (72832, 194)


def test_counties():
    assert data.data_store.counties(convert=False).shape == (3233, 2)


def test_states():
    assert data.data_store.states(convert=False).shape == (51, 3)


def test_msas():
    df = data.data_store.msas(convert=False)
    assert df.shape == (945, 4)


def test_msa_defs():
    df = data.data_store.msa_definitions(convert=False)
    assert df.shape == (1915, 13)


def test_codebook():
    df = data.data_store.codebook
    assert df.shape == (194, 12)


def test_ltdb():
    assert data.data_store.ltdb.shape == (330388, 192)


def test_ncdb():
    assert data.data_store.ncdb.shape == (328633, 77)
