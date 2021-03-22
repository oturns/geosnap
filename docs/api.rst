.. _api_ref:

.. currentmodule:: geosnap

API reference
=============

.. _data_api:

IO Module
--------------

Storing data
'''''''''''''''

geosnap's `io` module provides functions for collecting and storing a variety of datasets
including U.S. Census data from 1990-2010, LEHD data from any vintage, and external longitudinal databases.

.. currentmodule:: geosnap

.. autosummary::
   :toctree: generated/

    io.store_acs
    io.store_census
    io.store_blocks_2000
    io.store_blocks_2010
    io.store_ltdb
    io.store_ncdb
    io.get_lehd

Accessing Stored Datasets
'''''''''''''''''''''''''''''''

It also provides a storage container `datasets` that provides access to datasets that have been imported with the functions above

.. currentmodule:: geosnap

.. autosummary::
   :toctree: generated/
   
    datasets
    datasets.acs
    datasets.blocks_2000
    datasets.blocks_2010
    datasets.codebook
    datasets.counties
    datasets.ltdb
    datasets.msa_definitions
    datasets.msas
    datasets.ncdb
    datasets.states
    datasets.tracts_1990
    datasets.tracts_2000
    datasets.tracts_2010


The Community Class
-----------------------

The `Community` is the central construct in geonap used to hold spatiotemporal neighborhood data.
The most common way to interact with geosnap is by instantiating a Community using a constructor method,
then using analytical methods upon the community

.. currentmodule:: geosnap

.. autosummary::
   :toctree: generated/
   
   Community
   
Community Constructors
''''''''''''''''''''''''''''
.. currentmodule:: geosnap

.. autosummary::
   :toctree: generated/
  
   Community.from_census
   Community.from_geodataframes
   Community.from_lodes
   Community.from_ltdb
   Community.from_ncdb
  
.. _analyze_api:


Community Analytics
'''''''''''''''''''''''''
.. currentmodule:: geosnap

.. autosummary::
   :toctree: generated/
   
   Community.cluster
   Community.harmonize
   Community.regionalize
   Community.sequence
   Community.simulate
   Community.transition

Community Visualization
'''''''''''''''''''''''''
.. currentmodule:: geosnap

.. autosummary::
   :toctree: generated/

   Community.animate_timeseries
   Community.plot_boundary_silhouette
   Community.plot_next_best_label
   Community.plot_silhouette
   Community.plot_silhouette_map
   Community.plot_path_silhouette
   Community.plot_timeseries
   Community.plot_transition_matrix
   Community.plot_transition_graphs

   
Analyze Module
----------------
.. currentmodule:: geosnap

.. autosummary::
   :toctree: generated/
   
   analyze.ModelResults

Neighborhood Clustering Methods
'''''''''''''''''''''''''''''''''''''''''''''

Model neighborhood differentiation using multivariate clustering algorithms

.. currentmodule:: geosnap

.. autosummary::
   :toctree: generated/
   
    analyze.cluster
    analyze.regionalize

Clustering algorithms
``````````````````````````````````
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
    kmeans_spatial
    max_p
    skater
    spenc
    ward_spatial

    
Neighborhood Dynamics Methods
'''''''''''''''''''''''''''''''''''''''''''''

Model neighborhood change using optimal-matching algorithms or spatial discrete Markov chains

.. currentmodule:: geosnap

.. autosummary::
   :toctree: generated/
   
   analyze.linc
   analyze.sequence
   analyze.transition

.. _harmonize_api:

Harmonize Module
----------------
.. currentmodule:: geosnap

.. autosummary::
   :toctree: generated/

   harmonize.harmonize

.. _visualize_api:

Visualize Module
----------------

.. currentmodule:: geosnap

.. autosummary::
   :toctree: generated/

   visualize.indexplot_seq
   visualize.explore

.. _util_api:

Util Module
--------------
.. autosummary::
   :toctree: generated/

   util.gif_from_path
   util.fetch_acs
   util.process_acs