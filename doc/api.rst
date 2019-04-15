.. _api_ref:

.. currentmodule:: geosnap

API reference
=============

.. _data_api:

Data Module
--------------
.. autosummary::
   :toctree: generated/
   
    geosnap.data.db
    geosnap.data.metros
    geosnap.data.read_ltdb
    geosnap.data.read_ncdb
    geosnap.data.Community

.. _analyze_api:

Analyze Module
----------------

Neighborhood Clustering Methods
``````````````````````````````````
Model neighborhood differentiation using multivariate clustering algorithms

.. autosummary::
   :toctree: generated/
   
    geosnap.analyze.cluster
    geosnap.analyze.cluster_spatial

Clustering algorithms
'''''''''''''''''''''''
The following algorithms may be passed to `geosnap.analyze.cluster` or `geosnap.analyze.cluster_spatial` but they should not be called directly

Classic (aspatial) Clustering
""""""""""""""""""""""""""""""

.. currentmodule:: geosnap.analyze.analytics

.. autosummary::
   :toctree: generated/

    affinity_propagation
    gaussian_mixture
    hdbscan
    kmeans
    spectral
    ward

Spatial Clustering
""""""""""""""""""

.. currentmodule:: geosnap.analyze.analytics

.. autosummary::
   :toctree: generated/

    azp
    max_p
    skater
    spenc
    ward_spatial    

    
Neighborhod Dynamics Methods
````````````````````````````````
Model neighborhood change using optimal-matching algorithms or spatial discrete markov chains

.. currentmodule:: geosnap

.. autosummary::
   :toctree: generated/
   
   geosnap.analyze.linc
   geosnap.analyze.Sequence
   geosnap.analyze.Transition

Harmonize Module
----------------

Visualize Module
----------------
