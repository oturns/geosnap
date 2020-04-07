from geosnap import datasets
import pytest

def test_tracts90():
    df = datasets.tracts_1990()
    assert df.shape == (60658, 164)


def test_tracts00():
    df = datasets.tracts_2000(convert=False)
    assert df.shape == (65677, 192)


def test_tracts10():
    df = datasets.tracts_2010(convert=False)
    assert df.shape == (72832, 194)


def test_counties():
    assert datasets.counties().shape == (3233, 2)


def test_states():
    assert datasets.states(convert=False).shape == (51, 3)


def test_msas():
    df = datasets.msas(convert=False)
    assert df.shape == (945, 4)


def test_msa_defs():
    df = datasets.msa_definitions()
    assert df.shape == (1915, 13)


def test_codebook():
    df = datasets.codebook()
    assert df.shape == (194, 12)

@pytest.mark.xfail(reason="not testing proprietary datasets")
def test_ltdb():
    assert datasets.ltdb().shape == (330388, 192)

@pytest.mark.xfail(reason="not testing proprietary datasets")
def test_ncdb():
    assert datasets.ncdb().shape == (328633, 77)
