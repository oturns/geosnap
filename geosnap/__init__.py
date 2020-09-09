__version__ = "0.5.0"

r"""

geosnap: Geospatial Neighborhood Analysis Package.
======================================================

Documentation
-------------
geosnap documentation is available in two forms: python docstrings and an html\
        webpage at http://geosnap.org/

Available sub-packages
----------------------

analyze
    analyze neighborhood dynamics
harmonize
    harmonize neighborhood boundaries into consistent demarcators
visualize
    plot and animate neighborhoods and their change
io
    ingest, store, and manipulate spatiotemporal neighborhood data

"""

# __version__ has to be define in the first line

from . import analyze
from . import io
from . import util
from . import visualize
from . import harmonize
from ._data import datasets, _Map
from ._community import Community
