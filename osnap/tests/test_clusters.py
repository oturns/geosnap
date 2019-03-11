from context import analyze, data
import os
path = os.environ['DLPATH']

if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(data.__file__)), "ltdb.parquet")):
    data.read_ltdb(
        sample=path+"/ltdb_sample.zip",
        fullcount=path+"/ltdb_full.zip",
    )


reno = data.Community(source='ltdb', cbsafips='39900')
columns = ['median_household_income', 'p_poverty_rate', 'p_unemployment_rate']

# Aspatial Clusters

def test_gm():

    gm = analyze.cluster(reno, columns=columns, method='gaussian_mixture', best_model=True)
    assert len(gm.census.gaussian_mixture.unique()) > 7


def test_ward():

    ward = analyze.cluster(reno, columns=columns, method='ward')
    assert len(ward.census.ward.unique()) == 6


def test_spectral():

    spectral = analyze.cluster(reno, columns=columns, method='spectral')
    assert len(spectral.census.spectral.unique()) == 6


def test_kmeans():

    kmeans = analyze.cluster(reno, columns=columns, method='kmeans')
    assert len(kmeans.census.kmeans.unique()) == 6


def test_aff_prop():

    aff_prop = analyze.cluster(reno, columns=columns, method='affinity_propagation',
                               preference=-100)
    assert len(aff_prop.census.affinity_propagation.unique()) == 3


def test_hdbscan():

    hdbscan = analyze.cluster(reno, columns=columns, method='hdbscan')
    assert len(hdbscan.census.hdbscan.unique()) > 27


# Spatial Clusters

def test_spenc():

    spenc = analyze.cluster_spatial(reno, columns=columns, method='spenc')
    assert len(spenc.census.spenc.unique()) == 7


def test_maxp():

    maxp = analyze.cluster_spatial(reno, columns=columns, method='max_p',
                                   initial=10)
    assert len(maxp.census.max_p.unique()) > 9


def test_ward_spatial():

    ward_spatial = analyze.cluster_spatial(reno, columns=columns,
                                           method='ward_spatial')
    assert len(ward_spatial.census.ward_spatial.unique()) == 7


def test_skater():

    skater = analyze.cluster_spatial(reno, columns=columns, method='skater',
                                     n_clusters=10)
    assert len(skater.census.skater.unique()) == 11


def test_azp():
    azp = analyze.cluster_spatial(reno, columns=columns, method='azp')
    assert len(azp.census.azp.unique()) == 7
