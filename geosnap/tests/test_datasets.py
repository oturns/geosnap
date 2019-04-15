from context import data

import os
path = os.environ['DLPATH']

if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(data.__file__)), "ltdb.parquet")):
    data.read_ltdb(
        sample=path+"/ltdb_sample.zip",
        fullcount=path+"/ltdb_full.zip",
    )


def test_Community_from_boundary():

    dc_bound = data.metros[data.metros.name.str.startswith('Washington-Arlington')]
    dc_bound = dc_bound.to_crs(epsg=2248)
    dc = data.Community(boundary=dc_bound, source='ltdb')
    dc = dc.to_crs(epsg=4326)

    assert dc.tracts.shape == (1359, 2)
    assert dc.census.shape == (6560, 192)


def test_Community_from_cbsa():

    la = data.Community(cbsafips='31080', source='ltdb')

    assert la.tracts.shape == (2929, 2)
    assert la.census.shape == (14613, 192)


def test_Community_from_stcofips():

    mn = data.Community(statefips='27', countyfips=['053', '055'], source='ltdb')
    assert mn.tracts.shape == (304, 2)
    assert mn.census.shape == (1515, 192)


def test_Community_from_indices():

    chi = data.Community(source='ltdb', add_indices=['17031', '17019'])
    assert chi.tracts.shape == (1362, 2)
    assert chi.census.shape == (6805, 192)
