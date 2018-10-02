from context import data



def test_boundaries():

    geoids = [ '01001020100', '01001020300' ]

    df = data.boundaries.us.get_geometries(geoids)

    assert df.shape == (2, 195 )

