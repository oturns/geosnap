.. _api_ref:

.. currentmodule:: osnap

API reference
=============

.. _data_api:

Data Module
--------------
.. autosummary::
   :toctree: generated/

    osnap.data.read_ltdb
    osnap.data.read_ncdb
    osnap.data.Community
    osnap.data.Community.plot
    osnap.data.Community.to_crs


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

    
Neighborhod Dynamics Methods
````````````````````````````````
Model neighborhood change using optimal-matching algorithms or spatial discrete markov chains

.. autosummary::
   :toctree: generated/
   
   osnap.analyze.linc
   osnap.analyze.Sequence
   osnap.analyze.Transition

Harmonize Module
----------------

Visualize Module
----------------
