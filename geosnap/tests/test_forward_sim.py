from geosnap import DataStore
from geosnap.io import get_acs
from geosnap.analyze import cluster, predict_markov_labels
from geosnap.harmonize import harmonize

columns = ["median_household_income", "p_poverty_rate", "p_unemployment_rate"]


def test_single_simulation():
    dc = get_acs(state_fips="11", datastore=DataStore(), years=[2015, 2016, 2017], level='tract')
    dc, dc_mod = cluster(
        dc,
        columns=columns,
        method="kmeans",
        n_clusters=3,
        unit_index="geoid",
        return_model=True
    )

    #simulated = dc_mod.predict_markov_labels( base_year=2010, time_steps=1

    simulated = predict_markov_labels(dc, cluster_col='kmeans', w_type='rook', base_year=2017, time_steps=1)  
    assert simulated.shape == (177, 3)


def test_multi_simulation():
    dc = get_acs(state_fips="11", datastore=DataStore(), years=[2015, 2016, 2017], level='tract')

    dc, dc_mod = cluster(
        dc,
        columns=columns,
        method="kmeans",
        n_clusters=3,
        unit_index="geoid",
        return_model=True
    )

    simulated = dc_mod.predict_markov_labels(base_year=2017, time_steps=3, increment=1)
    assert simulated.shape == (708, 4)
