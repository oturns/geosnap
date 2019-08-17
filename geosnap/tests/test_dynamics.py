# from context import analyze
import numpy as np
from context import data
import os
from geosnap.analyze import sequence, transition

path = os.environ["DLPATH"]

if not os.path.exists(
    os.path.join(os.path.dirname(os.path.abspath(data.__file__)), "ltdb.parquet")
):
    data.store_ltdb(sample=path + "/ltdb_sample.zip", fullcount=path + "/ltdb_full.zip")

columbus = data.Community.from_ltdb(msa_fips="18140")
columns = ['median_household_income','p_poverty_rate',
           'p_edu_college_greater', 'p_unemployment_rate']
columbus1 = columbus.cluster(columns=['median_household_income',
                                      'p_poverty_rate',
                                      'p_edu_college_greater',
                                      'p_unemployment_rate'], method='ward')

def test_transition():
    '''
    Testing transition modeling.
    '''


    # 1. Markov modeling
    m = transition(columbus1.gdf, columbus, cluster_col="ward")
    mp = np.array([[0.79189189, 0.00540541, 0.0027027 , 0.13243243, 0.06216216,
        0.00540541],
       [0.0203252 , 0.75609756, 0.10569106, 0.11382114, 0.        ,
        0.00406504],
       [0.00917431, 0.20183486, 0.75229358, 0.01834862, 0.        ,
        0.01834862],
       [0.1959799 , 0.18341709, 0.00251256, 0.61809045, 0.        ,
        0.        ],
       [0.32307692, 0.        , 0.        , 0.        , 0.66153846,
        0.01538462],
       [0.09375   , 0.0625    , 0.        , 0.        , 0.        ,
        0.84375   ]])
    assert all([a == b for a, b in zip(m.p.flatten(),
                                       mp.flatten())])

    # 2. Spatial Markov modeling
    sm = transition(columbus1.gdf, columbus, cluster_col="ward", w_type="queen")
    smp = np.array([[0.82068966, 0.        , 0.        , 0.10689655, 0.07241379,
         0.        ],
        [0.14285714, 0.57142857, 0.14285714, 0.14285714, 0.        ,
         0.        ],
        [0.5       , 0.        , 0.5       , 0.        , 0.        ,
         0.        ],
        [0.21428571, 0.0952381 , 0.        , 0.69047619, 0.        ,
         0.        ],
        [0.22222222, 0.        , 0.        , 0.        , 0.75      ,
         0.02777778],
        [0.16666667, 0.        , 0.        , 0.        , 0.        ,
         0.83333333]])
    assert all([a == b for a, b in zip(sm.P[0].flatten(),
                                       smp.flatten())])

def test_sequence():
    '''
    Testing sequence modeling.
    '''

    # 1. Transition-orientied optimal matching
    gdf_new, df_wide, seq_dis_mat = sequence(columbus1.gdf, seq_clusters=5,
                                             dist_type="tran",
                                             cluster_col="ward")

    values = np.array([3, 3, 0, 2, 3, 2])
    assert all([a == b for a, b in zip(values, df_wide.values[0])])

    # 2. Hamming distance

    gdf_new, df_wide, seq_dis_mat = sequence(columbus1.gdf, seq_clusters=5,
                                             dist_type="hamming",
                                             cluster_col="ward")
    values = np.array([3, 3, 0, 2, 3, 4])
    assert all([a == b for a, b in zip(values, df_wide.values[0])])
