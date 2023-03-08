
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
import contextlib
from importlib.metadata import PackageNotFoundError, version

from . import analyze
from . import io
from . import util
from . import visualize
from . import harmonize
from ._data import _Map, DataStore

with contextlib.suppress(PackageNotFoundError):
    __version__ = version("geosnap")