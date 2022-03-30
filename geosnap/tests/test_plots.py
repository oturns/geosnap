from geosnap import Community
import proplot
import numpy
import os
import shutil
import pytest
from geosnap import DataStore

try:
    import pygraphviz
    NOGRAPHVIZ=False

except ImportError:
    NOGRAPHVIZ=True

if os.path.exists('geosnap/tests/images'):
    shutil.rmtree('geosnap/tests/images')

columns = ["median_household_income", "p_poverty_rate", "p_unemployment_rate"]
reno = Community.from_census(msa_fips="39900")
reno = reno.cluster(columns=columns, method='kmeans')
reno = reno.regionalize(columns=columns, method='ward_spatial')

def test_cont_timeseries():
    p = reno.plot_timeseries(column='median_household_income', years=[2010], dpi=50)
    assert isinstance(p, proplot.gridspec.SubplotGrid)

def test_cat_timeseries():
    p = reno.plot_timeseries(column='kmeans', categorical=True, years=[2010], dpi=50)
    assert isinstance(p, proplot.gridspec.SubplotGrid)

def test_heatmaps():
    p = reno.plot_transition_matrix(cluster_col='kmeans', figsize=(2,2))
    assert isinstance(p, numpy.ndarray)

@pytest.mark.skipif(NOGRAPHVIZ, reason="pygraphviz couldn't be imported.")
def test_graphs():
    os.mkdir('geosnap/tests/images')
    reno.plot_transition_graphs(output_dir='geosnap/tests/images', cluster_col='kmeans')
    assert len(os.listdir('geosnap/tests/images')) == 7

def test_animation():
    if not os.path.exists('geosnap/tests/images'):
            os.mkdir('geosnap/tests/images')
    reno.animate_timeseries(column='kmeans', categorical=True, filename='geosnap/tests/images/animation.gif')
    assert 'animation.gif' in os.listdir('geosnap/tests/images')

def test_boundary_silplot():
    p = reno.plot_boundary_silhouette(model_name='ward_spatial', year=2010, dpi=50)
    assert isinstance(p, numpy.ndarray)

def test_path_silplot():
    p = reno.plot_path_silhouette(model_name='ward_spatial', year=2010, dpi=50)
    assert isinstance(p, numpy.ndarray)

def test_next_label_plot():
    p = reno.plot_next_best_label('kmeans')
    assert isinstance(p, numpy.ndarray)

def test_silmap_plot():
    p = reno.plot_silhouette_map('kmeans', dpi=50)
    assert isinstance(p, numpy.ndarray)
