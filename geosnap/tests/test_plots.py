import os
import shutil

import numpy
#import proplot
import pytest
import matplotlib
from geosnap import DataStore
from geosnap.analyze import cluster, regionalize, transition
from geosnap.io import get_census
from geosnap.visualize import (
    animate_timeseries,
    plot_timeseries,
    plot_transition_graphs,
    plot_transition_matrix,
    plot_violins_by_cluster
)


try:
    import pygraphviz
    NOGRAPHVIZ=False

except ImportError:
    NOGRAPHVIZ=True

if os.path.exists('geosnap/tests/images'):
    shutil.rmtree('geosnap/tests/images')

columns = ["median_household_income", "p_poverty_rate", "p_unemployment_rate", 'n_total_pop']

dc_df = get_census(DataStore(), state_fips='11')
dc_df, cluster_mod = cluster(dc_df, columns=columns, method='ward', return_model=True)
dc_df, region_mod = regionalize(dc_df, columns=columns, method='ward_spatial', return_model=True)

dc_df = dc_df.dropna(subset=['ward'])



def test_cont_timeseries_pooled():
    p = plot_timeseries(dc_df, column='median_household_income', temporal_index='year', time_subset=[2010], dpi=50)
    assert isinstance(p[0], matplotlib.axes.SubplotBase)

def test_cont_timeseries_unpooled():
    p = plot_timeseries(dc_df, column='median_household_income', temporal_index='year', time_subset=[2010], dpi=50, pooled=False)
    assert isinstance(p[0], matplotlib.axes.SubplotBase  )

def test_cont_timeseries_unpooled_layout():
    p = plot_timeseries(dc_df, column='median_household_income', temporal_index='year', time_subset=[2000,2010], dpi=50, pooled=False)
    assert isinstance(p[0], matplotlib.axes.SubplotBase)

def test_cat_timeseries():
    p = plot_timeseries(dc_df,column='ward', categorical=True, temporal_index='year', time_subset=[2010],dpi=50)
    assert isinstance(p[0], matplotlib.axes.SubplotBase)

def test_heatmaps():
    t = transition(dc_df, cluster_col='ward')
    p = plot_transition_matrix(dc_df, cluster_col='ward', figsize=(5,5), transition_model=t)
    assert isinstance(p[0], matplotlib.axes.SubplotBase)

def test_heatmaps_no_model():
    p = plot_transition_matrix(dc_df, cluster_col='ward', figsize=(5,5))
    assert isinstance(p[0], matplotlib.axes.SubplotBase)


@pytest.mark.skipif(NOGRAPHVIZ, reason="pygraphviz couldn't be imported.")
def test_graphs():
    os.mkdir('geosnap/tests/images')
    plot_transition_graphs(gdf=dc_df, output_dir='geosnap/tests/images', cluster_col='ward')
    assert len(os.listdir('geosnap/tests/images')) == 6

def test_animation():
    if not os.path.exists('geosnap/tests/images'):
            os.mkdir('geosnap/tests/images')
    animate_timeseries(dc_df, column='ward', categorical=True, filename='geosnap/tests/images/animation.gif', dpi=50)
    assert 'animation.gif' in os.listdir('geosnap/tests/images')

def test_violins():
    if not os.path.exists('geosnap/tests/images'):
            os.mkdir('geosnap/tests/images')
    plot_violins_by_cluster(dc_df, cluster_col='ward', columns=columns, savefig='geosnap/tests/images/violins.png', dpi=50)
    assert 'violins.png' in os.listdir('geosnap/tests/images')

def test_boundary_silplot():
    p = region_mod[1990].plot_boundary_silhouette(dpi=50,)
    assert isinstance(p[0], matplotlib.axes.SubplotBase
)

def test_path_silplot():
    p = region_mod[1990].plot_path_silhouette(dpi=50,)
    assert isinstance(p[0], matplotlib.axes.SubplotBase
)

def test_next_label_plot():
    p = cluster_mod.plot_next_best_label()
    assert isinstance(p, numpy.ndarray
)

def test_silmap_plot():
    p = cluster_mod.plot_silhouette_map(dpi=50, )
    assert isinstance(p, numpy.ndarray
)
