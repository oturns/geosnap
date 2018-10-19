# osnap.data

OSNAP's `data` module can ingest data from existing longitudinal databases like the Geolytics [Neighborhood Change Database](http://geolytics.com/USCensus,Neighborhood-Change-Database-1970-2000,Products.asp) and Brown University's [Longtitudinal Tract Database](https://s4.ad.brown.edu/projects/diversity/researcher/bridging.htm), and it can download original survey and geospatial data directly from the US Census.

To facilitate multiple analyses, OSNAP provides functions to cache longitudinal databases to disk. Once they are registered with OSNAP, these databases can be queried rapidly to create datasets for analyzing neighborhood dynamics at any scale.

## Importing External Databases

### Longitudinal Tract Database (LTDB)

The [Longitudinal Tract Database
(LTDB)](https://s4.ad.brown.edu/projects/diversity/Researcher/LTDB.htm) is a
freely available dataset developed by researchers at Brown University that
provides census data harmonized to 2010 boundaries.

To import LTDB data into osnap, proceed with the following:

- Download the raw data from the LTDB [downloads
  page](https://s4.ad.brown.edu/projects/diversity/Researcher/LTBDDload/Default.aspx).
  Note that to construct the entire database you will need two archives: one
  containing the sample variables, and another containing the "full count"
  variables.
    - Use the dropdown menu called **select file type** and choose "full"; in
      the dropdown called **select a year**, choose "All Years"
    - Click the button "Download Standard Data Files"
    - Repeat the process, this time selecting "sample" in the **select file
      type** menu and "All years" in the **select a year**
- Note the location of the two zip archives you just downloaded. By default they are called `LTDB_Std_All_Sample.zip` and
  `LTDB_Std_All_fullcount.zip`. 

Finally, to load the data into osnap, call the `read_ltdb` function and pass the paths of the two zip archives you downloaded from the LTDB project page:

```
from osnap.data import read_ltdb

# if the archives were in my downloads folder, the paths might be something like this

sample = "~/downloads/LTDB_Std_All_Sample.zip"
full = "~/downlodas/LTDB_Std_All_fullcount.zip"

read_ltdb(sample=sample, fullcount=full)

```

The reader will extract the necessary data from the archives, calculate some additional variables, and store the database as an apache parquet file. It will also return a pandas DataFrame if you want to get started right way or if you want inspect the variables.


### Neighborhood Change Database



## Creating Datasets for Analysis

To perform neighborhood analyses, osnap provides the `Dataset` class which stores information about the spatial boundaries and social composition of a study area. 

Creating a set of neighborhoods is as simple as instantiating the Dataset class with a location filter and a source database. The location filter can be either a `geopandas.GeoDataFrame` that defines the total extent of a boundary area (such as an MSA), or a list of state and county FIPS codes.

To use a boundary 

```
import geopandas
import osnap

# read in a geodataframe of Virginia
va = gpd.read_file(lps.examples.get_path('virginia.shp'))

virginia = Dataset(name='Virginia', source='ltdb', boundary=va)

```

To use a list of FIPS

```
import osnap

# Maryland's fips code is 24, Baltimore City is 510 and Baltimore County is 005

baltimore = Dataset(name='Baltimore', source='ltdb', states='24', counties = ['005', '510'])

```
