from geosnap import DataStore
from geosnap.io import get_census
from geosnap.analyze import cluster
from geosnap.harmonize import harmonize


columns = ["median_household_income", "p_poverty_rate", "p_unemployment_rate"]
reno = get_census(msa_fips="39900", datastore=DataStore())
reno = harmonize(
    reno,
    intensive_variables=columns,
    target_year=2010,
    allocate_total=True,
    extensive_variables=["n_total_pop"],
    unit_index="geoid",
).reset_index()

reno, reno_mod = cluster(
    reno,
    columns=columns,
    method="kmeans",
    n_clusters=3,
    unit_index="geoid",
    return_model=True
)

def test_single_simulation():
    simulated = reno_mod.predict_markov_labels( base_year=2010, time_steps=1
    )
    assert simulated.shape == (107, 3)


def test_multi_simulation():
    simulated = reno_mod.predict_markov_labels(base_year=2010, time_steps=3, increment=10)
    assert simulated.shape == (428, 4)
