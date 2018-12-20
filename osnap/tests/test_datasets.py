from context import data

def test_dataset_from_extent():

    dc_bound = data.metros[data.metros.name.str.startswith('Washington-Arlington')]
    dc = data.Dataset(boundary=dc_bound, source='ltdb')

    assert dc.tracts.shape == (1359, 2)
    assert dc.data.shape == (6560, 192)


def test_dataset_from_cbsa():

    la = data.Dataset(cbsafips='31080', source='ltdb')

    assert la.tracts.shape == (2929, 2)
    assert la.data.shape == (14613, 192)


def test_dataset_from_stcofips():

    mn = data.Dataset(statefips='27', countyfips=['053', '055'], source='ltdb')
    assert mn.tracts.shape == (304, 2)
    assert mn.data.shape == (1515, 192)


def test_dataset_from_indices():

    chi = data.Dataset(source='ltdb', add_indices=['17031', '17019'])
    assert chi.tracts.shape == (1362, 2)
    assert chi.data.shape == (6805, 192)
