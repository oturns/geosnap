from context import analyze, data
import matplotlib
import pytest
#matplotlib.use('agg')

from matplotlib.testing.decorators import image_comparison
import matplotlib.pyplot as plt

@pytest.mark.mpl_image_compare
def test_plot():
    fig, ax = plt.subplots()
    sd = data.Community(name='sd', source='ltdb', cbsafips='41740')
    sd_clusters = analyze.cluster(sd, columns=['median_household_income', 'p_poverty_rate', 'p_edu_college_greater', 'p_unemployment_rate'], method='kmeans')
    sd_clusters.plot(column='kmeans', ax=ax)
    return fig
