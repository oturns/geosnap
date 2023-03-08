import numpy as np
import os
from geosnap import DataStore
from geosnap.io import get_ltdb
from geosnap.analyze import sequence, transition, cluster

RTOL = 0.00001

import pytest 

try:
    LTDB = os.environ["LTDB_SAMPLE"]
except:
    LTDB=None


@pytest.mark.skipif(not LTDB, reason="unable to locate LTDB data")
def test_transition():
    """
    Testing transition modeling.
    """
    columbus = get_ltdb(DataStore(), msa_fips="18140")
    columns = [
        "median_household_income",
        "p_poverty_rate",
        "p_edu_college_greater",
        "p_unemployment_rate",
    ]
    columbus1 = cluster(columbus,
        columns=[
            "median_household_income",
            "p_poverty_rate",
            "p_edu_college_greater",
            "p_unemployment_rate",
        ],
        method="ward",
    )

    # 1. Markov modeling
    m = transition(columbus1, cluster_col="ward")
    mp = np.array(
        [
            [0.79189189, 0.00540541, 0.0027027, 0.13243243, 0.06216216, 0.00540541],
            [0.0203252, 0.75609756, 0.10569106, 0.11382114, 0.0, 0.00406504],
            [0.00917431, 0.20183486, 0.75229358, 0.01834862, 0.0, 0.01834862],
            [0.1959799, 0.18341709, 0.00251256, 0.61809045, 0.0, 0.0],
            [0.32307692, 0.0, 0.0, 0.0, 0.66153846, 0.01538462],
            [0.09375, 0.0625, 0.0, 0.0, 0.0, 0.84375],
        ]
    )
    np.testing.assert_allclose(m.p, mp, RTOL)

    # 2. Spatial Markov modeling
    np.random.seed(5)
    sm = transition(columbus1, cluster_col="ward", w_type="queen")
    smp = np.array(
        [
            [0.82413793, 0.0, 0.0, 0.10689655, 0.06896552, 0.0],
            [0.25, 0.5, 0.125, 0.125, 0.0, 0.0],
            [0.5, 0.0, 0.5, 0.0, 0.0, 0.0],
            [0.23809524, 0.0952381, 0.0, 0.66666667, 0.0, 0.0],
            [0.21621622, 0.0, 0.0, 0.0, 0.75675676, 0.02702703],
            [0.16666667, 0.0, 0.0, 0.0, 0.0, 0.83333333],
        ]
    )
    np.testing.assert_allclose(sm.P[0], smp, RTOL)

@pytest.mark.skipif(not LTDB, reason="unable to locate LTDB data")
def test_sequence():
    """
    Testing sequence modeling.
    """

    columbus = get_ltdb(DataStore(), msa_fips="18140")
    columns = [
        "median_household_income",
        "p_poverty_rate",
        "p_edu_college_greater",
        "p_unemployment_rate",
    ]
    columbus1 = cluster(columbus,
        columns=[
            "median_household_income",
            "p_poverty_rate",
            "p_edu_college_greater",
            "p_unemployment_rate",
        ],
        method="ward",
    )

    # 1. Transition-orientied optimal matching
    output = sequence(
        columbus1, seq_clusters=5, dist_type="tran", cluster_col="ward"
    )

    values = np.array([3, 3, 0, 2, 3, 1])
    np.testing.assert_allclose(output[1].values[0], values, RTOL)

    # 2. Hamming distance

    output = sequence(
        columbus1, seq_clusters=5, dist_type="hamming", cluster_col="ward"
    )
    values = np.array([3, 3, 0, 2, 3, 2])
    np.testing.assert_allclose(output[1].values[0], values, RTOL)
