.. _api_ref:

.. currentmodule:: osnap

API reference
=============

.. _data_api:

Data Module
--------------
.. autosummary::
   :toctree: generated/
   
    osnap.data.db
    osnap.data.metros
    osnap.data.read_ltdb
    osnap.data.read_ncdb
    osnap.data.Community

.. _analyze_api:

Analyze Module
----------------

Neighborhood Clustering Methods
``````````````````````````````````
Model neighborhood differentiation using multivariate clustering algorithms

.. autosummary::
   :toctree: generated/
   
    osnap.analyze.cluster
    osnap.analyze.cluster_spatial

Clustering algorithms
'''''''''''''''''''''''
The following algorithms may be passed to `osnap.analyze.cluster` or `osnap.analyze.cluster_spatial` but they should not be called directly

Classic (aspatial) Clustering
""""""""""""""""""""""""""""""

.. currentmodule:: osnap.analyze.analytics

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

.. currentmodule:: osnap.analyze.analytics

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

.. currentmodule:: osnap

.. autosummary::
   :toctree: generated/
   
   osnap.analyze.linc
   osnap.analyze.Sequence
   osnap.analyze.Transition

Harmonize Module
----------------

Visualize Module
----------------
