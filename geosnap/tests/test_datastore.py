from geosnap import DataStore

datasets = DataStore()


def test_data_dir():
    loc = datasets.show_data_dir()
    assert len(loc) > 5


def test_acs():
    df = datasets.acs(year=2012, states=["11"])
    assert df.shape == (179, 104)


def test_tracts90():
    df = datasets.tracts_1990(states=["11"])
    assert df.shape == (192, 164)


def test_tracts00():
    df = datasets.tracts_2000(states=["11"])
    assert df.shape == (188, 192)


def test_tracts10():
    df = datasets.tracts_2010(states=["11"])
    assert df.shape == (179, 194)


def test_tracts20():
    df = datasets.tracts_2020(states=["11"])
    assert df.shape == (206, 15)


def test_counties():
    assert datasets.counties().shape == (3233, 2)


def test_states():
    assert datasets.states().shape == (51, 3)


def test_msas():
    df = datasets.msas()
    assert df.shape == (939, 4)


def test_msa_defs():
    df = datasets.msa_definitions()
    assert df.shape == (1916, 13)


def test_codebook():
    df = datasets.codebook()
    assert df.shape == (194, 12)


def test_bea():
    df = datasets.bea_regions()
    assert df.shape == (51, 4)


def test_blocks_2000():
    df = datasets.blocks_2000(states=["11"])
    assert df.shape == (5674, 3)


def test_blocks_2010():
    df = datasets.blocks_2010(states=["11"])
    assert df.shape == (6507, 5)


def test_blocks_2020():
    df = datasets.blocks_2020(states=["11"])
    assert df.shape == (6012, 7)


def test_lodes_codebook():
    df = datasets.lodes_codebook()
    assert df.shape == (42, 4)

def test_ej_codebook():
    df = datasets.ejscreen_codebook()
    assert df.shape == (142, 2)
