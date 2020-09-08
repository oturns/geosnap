from geosnap import Community
import numpy as np
np.seterr(divide='ignore', invalid='ignore')


columns = ["median_household_income", "p_poverty_rate", "p_unemployment_rate"]
reno = Community.from_ltdb(msa_fips="39900")
reno = reno.cluster(columns=columns, method='kmeans', k=3)


def test_single_simulation():
    simulated = reno.simulate(model_name='kmeans', base_year=2010, time_steps=1)
    assert simulated.shape == (107, 3)

def test_multi_simulation():
    simulated = reno.simulate(model_name='kmeans', base_year=2010)
    assert simulated.gdf.shape == (428, 5)

