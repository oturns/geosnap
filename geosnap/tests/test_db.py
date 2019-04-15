from context import data


def test_db_vars90():
    df = data.db.census_90
    assert df.shape == (61258, 162)


def test_db_vars00():
    df = data.db.census_00
    assert df.shape == (65443, 190)


def test_data_dictionary():
    df = data.dictionary
    assert df.shape == (194, 12)
