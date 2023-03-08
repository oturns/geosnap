.. _api_ref:

.. currentmodule:: geosnap

API reference
=============

.. _data_api:

IO Module
--------------

Accessing Datasets
'''''''''''''''''''''

The DataStore class provides access to a fast and efficient database of neighborhood
indicators for the United States.  The DataStore can read information directly over the
web, or it can cache the datasets locally for (shared) repeated use. Large datasets are
available quickly with no configuration by accessing methods on the class.

.. currentmodule:: geosnap

.. autosummary::
   :toctree: generated/
   
    DataStore
    DataStore.acs
    DataStore.blocks_2000
    DataStore.blocks_2010
    DataStore.codebook
    DataStore.counties
    DataStore.ejscreen
    DataStore.ltdb
    DataStore.msa_definitions
    DataStore.msas
    DataStore.ncdb
    DataStore.nces
    DataStore.show_data_dir
    DataStore.states
    DataStore.tracts_1990
    DataStore.tracts_2000
    DataStore.tracts_2010


Storing data
'''''''''''''''

To store the datasets locally for repeated use, or to register an external dataset with geosnap, such as
the Longitudinal Tract Database (LTDB) or the Neighborhood Change Database (NCDB), the `io` module includes
functions for caching data on your local machine. When you instantiate a DataStore class, it will use local
files instead of streaming over the web.

.. currentmodule:: geosnap

.. autosummary::
   :toctree: generated/

    io.store_acs
    io.store_census
    io.store_blocks_2000
    io.store_blocks_2010
    io.store_ejscreen
    io.store_ltdb
    io.store_ncdb
    io.store_nces


Querying datasets
''''''''''''''''''''
.. autosummary::
   :toctree: generated/

    io.get_acs
    io.get_census
    io.get_ejscreen
    io.get_gadm
    io.get_lodes
    io.get_ltdb
    io.get_nces
    io.get_ncdb


Analyze Module
----------------

Neighborhood Clustering Methods
'''''''''''''''''''''''''''''''''''''''''''''

Model neighborhood differentiation using multivariate clustering algorithms

.. currentmodule:: geosnap

.. autosummary::
   :toctree: generated/
   
    analyze.cluster
    analyze.find_k
    analyze.find_region_k
    analyze.regionalize
    
Neighborhood Dynamics Methods
'''''''''''''''''''''''''''''''''''''''''''''

Model neighborhood change using optimal-matching algorithms or spatial discrete Markov chains

.. currentmodule:: geosnap

.. autosummary::
   :toctree: generated/
   
   analyze.linc
   analyze.lincs_from_gdf
   analyze.predict_markov_labels
   analyze.sequence
   analyze.transition

Segregation Dynamics Methods
'''''''''''''''''''''''''''''''''''''''''''''

Rapidly compute and compare changes in segregation measures over time and across space

.. currentmodule:: geosnap

.. autosummary::
   :toctree: generated/
   
    analyze.segdyn.singlegroup_tempdyn
    analyze.segdyn.multigroup_tempdyn
    analyze.segdyn.spacetime_dyn


Network Analysis Methods
'''''''''''''''''''''''''''''''''''''''''''''

Compute shortest path distance along a network using pandana, and visualize travel time isochrones from local data

.. currentmodule:: geosnap

.. autosummary::
   :toctree: generated/

   analyze.compute_travel_cost_adjlist
   analyze.isochrone
   analyze.isocrones

The ModelResults Class
'''''''''''''''''''''''''''''''''''''''''''''

Many of geosnap's analytics methods can return a ModelResults class that
stores additional statistics, diagnostics, and plotting methods for inspection


.. currentmodule:: geosnap.analyze

.. autosummary::
   :toctree: generated/
   
   ModelResults.boundary_silhouette
   ModelResults.lincs
   ModelResults.path_silhouette
   ModelResults.silhouette_scores
   ModelResults.plot_boundary_silhouette
   ModelResults.plot_next_best_label
   ModelResults.plot_silhouette
   ModelResults.plot_silhouette_map
   ModelResults.plot_path_silhouette
   ModelResults.plot_transition_matrix
   ModelResults.plot_transition_graphs
   ModelResults.predict_markov_labels

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

   visualize.animate_timeseries
   visualize.gif_from_path
   visualize.indexplot_seq
   visualize.plot_timeseries
   visualize.plot_transition_matrix
   visualize.plot_transition_graphs
   visualize.plot_violins_by_cluster

.. _util_api:

Util Module
--------------
.. autosummary::
   :toctree: generated/

   util.fetch_acs
   util.process_acs

