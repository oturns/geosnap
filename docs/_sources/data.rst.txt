Datasets
===============


``geosnap`` uses `quilt <https://quiltdata.com>`_ for data storage and delivery. or more information, see our `public quilt bucket  <https://open.quiltdata.com/b/spatial-ucr/tree/>`_

Tabular Data
--------------
To view the `codebook <https://github.com/spatialucr/geosnap/blob/master/geosnap/io/variables.csv>`_ for geosnap's builtin datasets, use 

``geosnap.io.codebook()``

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
| Tracts  | https://www2.census.gov/geo/tiger/PREVGENZ/tr/tr90shp/     |
| 1990    |                                                            |
+---------+------------------------------------------------------------+
| Tracts  | https://www2.census.gov/geo/tiger/PREVGENZ/tr/tr00shp/     |
| 2000    |                                                            |
+---------+------------------------------------------------------------+
| Tracts  | https://www2.census.gov/geo/tiger/TIGER2018/TRACT/         |
| 2010    |                                                            |
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
