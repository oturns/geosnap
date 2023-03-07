import numpy as np
from numpy.testing import assert_array_almost_equal
from segregation.singlegroup import Entropy

from geosnap import DataStore
from geosnap.analyze.segdyn import *
from geosnap.io import get_census

reno = get_census(msa_fips="39900", datastore=DataStore())
groups = [
    "n_nonhisp_black_persons",
    "n_nonhisp_white_persons",
    "n_hispanic_persons",
    "n_asian_persons",
]
gdf = reno.to_crs(reno.estimate_utm_crs())
gdf = gdf.fillna(0)


def test_multigroup_tempdyn():
    np.seterr(divide="ignore", invalid="ignore")
    df = multigroup_tempdyn(gdf.copy(), groups=groups)
    assert_array_almost_equal(
        df.values,
        np.array(
            [
                [0.4288, 1.0986, 1.8137],
                [0.2887, 0.3492, 0.3639],
                [0.039, 0.0802, 0.1172],
                [0.5663, 0.725, 0.8488],
                [0.3893, 0.4691, 0.4984],
                [0.0689, 0.1107, 0.1381],
                [0.0662, 0.127, 0.1509],
                [0.052, 0.1151, 0.1395],
                [0.0295, 0.0563, 0.0775],
                [0.7303, 0.6154, 0.5307],
                [0.2697, 0.3846, 0.4693],
            ]
        ),
        decimal=2,
    )


def test_singlegroup_tempdyn():

    df = singlegroup_tempdyn(
        gdf.copy(), group_pop_var="n_nonhisp_black_persons", total_pop_var="n_total_pop"
    )
    assert_array_almost_equal(
        df.values,
        np.array(
            [
                [0.9727, 0.9803, 0.9715],
                [0.0147, 0.0077, 0.017],
                [0.9912, 0.9934, 0.9809],
                [0.1817, 0.1315, 0.3124],
                [0.329, 0.2763, 0.4114],
                [0.3197, 0.2687, 0.387],
                [0.0247, 0.0156, 0.0323],
                [0.0209, 0.0116, 0.0283],
                [0.9492, 0.9387, 0.9544],
                [0.3158, 0.2752, 0.3246],
                [0.3304, 0.2786, 0.4128],
                [0.9711, 0.9741, 0.9733],
                [0.0373, 0.0279, 0.0408],
                [0.0768, 0.0526, 0.1147],
                [0.4602, 0.3918, 0.5623],
                [0.9584, 0.9689, 0.9495],
                [0.0416, 0.0311, 0.0505],
                [0.4967, 0.4357, 0.5844],
                [0.305, 0.2493, 0.3874],
                [0.4307, 0.3559, 0.5352],
                [0.3299, 0.2767, 0.4083],
                [0.2272, 0.2951, 0.2304],
                [1.0345, 0.7278, 1.2996],
                [0.7205, 0.775, 0.5045],
                [0.3172, 0.2676, 0.3878],
                [0.0557, 0.046, 0.0485],
                [1.0136, 1.0067, 1.016],
            ]
        ),
        decimal=2,
    )


def test_spacetime_dyn():

    df = spacetime_dyn(
        gdf.copy(),
        segregation_index=Entropy,
        group_pop_var="n_nonhisp_black_persons",
        total_pop_var="n_total_pop",
        distances=range(1000, 2000, 1000),
    )
    assert_array_almost_equal(
        df.values,
        np.array(
            [[0.07684793, 0.05255198, 0.11470159], [0.07635796, 0.05217017, 0.10912089]]
        ),
        decimal=2,
    )
