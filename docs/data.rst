Built-In Datasets
========================

``geosnap`` has a lightweight installation footprint (the codebase clocks in at 174KB), but it also
has access to several large, built-in datasets transparently, thanks to `quilt <https://quiltdata.com>`_.  
We host a variety of U.S. Census, landsat imagery, and OSM road network data in our `public quilt bucket  <https://open.quiltdata.com/b/spatial-ucr/tree/>`_, 
and ``geosnap`` has convenience methods for building datasets from them. 


All built-in datasets are available as methods on the ``geosnap.DataStore`` class. For more information, see the `Getting Started <https://oturns.github.io/geosnap-guide/notebooks/01_getting_started.html>`_ tutorial

To keep its slender profile, ``geosnap`` is conservative about storing these data locally. By default, when you use built-in data, it is streamed from s3 via ``quilt``.
We store the data as efficient parquet files, and quilt provides access to them via Amazon's `open data cloud <https://registry.opendata.aws/spatial-ucr/>`_. 
This means that streaming data is relatively fast and efficient. 


If you plan to make repeated queries, or you need offline access to the data, ``geosnap`` also has functions
for caching all the data locally (see the `Getting Started <https://oturns.github.io/geosnap-guide/notebooks/01_getting_started.html>`_ tutorial). 
Since we store everything in parquet, local storage is still highly efficient, and ``geosnap`` will use `platformdirs <https://pypi.org/project/platformdirs/>`_
to determine the best place to store the data on your machine.


Tabular Data
--------------
To view the `codebook <https://github.com/oturns/geosnap/blob/main/geosnap/io/variables.csv>`_ for geosnap's builtin datasets, use 

``geosnap.datasets.codebook()``

which will return a pandas.DataFrame of variable names, definitions, formulas for intermediate variables, and translations to original sources.
All variables are collected via the U.S. Census Bureau from either the decennial census, the American Community Survey, or the `Longitudinal Employment Household Dynamics <https://lehd.ces.census.gov/data/lodes/LODES7/>`_ dataset.

Geo Data
--------------

+---------+------------------------------------------------------------+
| Data    | Source                                                     |
+=========+============================================================+
| Blocks  | https://www2.census.gov/geo/tiger/TIGER2010/TABBLOCK/2000/ |
| 2000    |                                                            |
+---------+------------------------------------------------------------+
| Blocks  | https://www2.census.gov/geo/tiger/TIGER2018/TABBLOCK/      |
| 2010    |                                                            |
+---------+------------------------------------------------------------+
| Blocks  | https://www2.census.gov/geo/tiger/TIGER2021/TABBLOCK/      |
| 2020    |                                                            |
+---------+------------------------------------------------------------+
| Tracts  | https://github.co                                          |
| 1990    | m/loganpowell/census-geojson/tree/master/GeoJSON/500k/1990 |
+---------+------------------------------------------------------------+
| Tracts  | https://github.co                                          |
| 2000    | m/loganpowell/census-geojson/tree/master/GeoJSON/500k/2000 |
+---------+------------------------------------------------------------+
| Tracts  | https://github.co                                          |
| 2010    | m/loganpowell/census-geojson/tree/master/GeoJSON/500k/2010 |
+---------+------------------------------------------------------------+
| MSA     | https:                                                     |
| Defi    | //www2.census.gov/programs-surveys/metro-micro/geographies |
| nitions | /reference-files/2018/delineation-files/list1_Sep_2018.xls |
+---------+------------------------------------------------------------+
| In      | https://www.bls.gov/cpi/research-series/allitems.xlsx      |
| flation |                                                            |
| Adj     |                                                            |
| ustment |                                                            |
+---------+------------------------------------------------------------+
