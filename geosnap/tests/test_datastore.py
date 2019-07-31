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


def test_codebook():
    df = data.data_store.codebook
    assert df.shape == (194, 12)
