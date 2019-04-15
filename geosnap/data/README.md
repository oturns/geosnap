# Data

geosnap's `data` module can ingest data from existing longitudinal databases like the Geolytics [Neighborhood Change Database](http://geolytics.com/USCensus,Neighborhood-Change-Database-1970-2000,Products.asp) and Brown University's [Longtitudinal Tract Database](https://s4.ad.brown.edu/projects/diversity/researcher/bridging.htm), and it can download original survey and geospatial data directly from the US Census.

To facilitate multiple analyses, geosnap provides functions to cache longitudinal databases to disk. Once they are registered with geosnap, these databases can be queried rapidly to create datasets for analyzing neighborhood dynamics at any scale.


## Importing External Databases

### Longitudinal Tract Database (LTDB)

The [Longitudinal Tract Database
(LTDB)](https://s4.ad.brown.edu/projects/diversity/Researcher/LTDB.htm) is a
freely available dataset developed by researchers at Brown University that
provides census data harmonized to 2010 boundaries.

To import LTDB data into geosnap, proceed with the following:

1. Download the raw data from the LTDB [downloads
  page](https://s4.ad.brown.edu/projects/diversity/Researcher/LTBDDload/Default.aspx).
  Note that to construct the entire database you will need two archives: one
  containing the sample variables, and another containing the "full count"
  variables.
    - Use the dropdown menu called **select file type** and choose "full"; in
      the dropdown called **select a year**, choose "All Years"
    - Click the button "Download Standard Data Files"
    - Repeat the process, this time selecting "sample" in the **select file
      type** menu and "All years" in the **select a year** dropdown
2. Note the location of the two zip archives you downloaded. By default they are called 
    - `LTDB_Std_All_Sample.zip` and
    - `LTDB_Std_All_fullcount.zip`

3. Start ipython/jupyter, import geosnap, and call the `read_ltdb` function with the paths of the two zip archives you downloaded from the LTDB project page:

```python
from geosnap.data import read_ltdb

# if the archives were in my downloads folder, the paths might be something like this
sample = "~/downloads/LTDB_Std_All_Sample.zip"
full = "~/downlodas/LTDB_Std_All_fullcount.zip"

read_ltdb(sample=sample, fullcount=full)

```

The reader will extract the necessary data from the archives, calculate some additional variables, and store the database as an apache parquet file. It will also return a pandas DataFrame if you want to get started right way or if you want inspect the variables.


### Geolytics Neighborhood Change Database

1. Open the Geolytics application
2. Choose "New Request": ![Choose "New Request"](geolytics/geolytics_interface1.PNG)
3. Select CSV or DBF
4. Make the following Selections:
    - **year**: all years in 2010 boundaries
    - **area**: all census tracts in the entire united states
    - **counts**: [right click] Check All Sibling Nodes

![](geolytics/geolytics_interface2.PNG)

5. Click `Run Report`

6. Note the name and location of the CSV you created

7. Start ipython/jupyter, import geosnap, and call the `read_ncdb` function with the path of the CSV:

```python
from geosnap.data import read_ncdb

ncdb = "geolytics_full.csv"

read_ncdb(ncdb)
```


## Metropolitan Area Boundaries
Since a common use-case is analyzing neighborhood dynamics at the metropolitan scale, geosnap makes available a set of core-based statistical area (CBSA) geographic [boundaries](ftp://ftp2.census.gov/geo/tiger/TIGER2018/CBSA/tl_2018_us_cbsa.zip) that can be passed to `geosnap.data.Dataset` as a [set of] clipping feature(s) to quickly generate metro-scale extracts. The boundaries are provided as a GeoDataFrame available under the `geosnap.metros` attribute

```python
In [1]: from geosnap import metros
In [2]: metros.head()
Out[2]:
GEOID              NAME                     NAMELSAD                                           geometry
0  40340     Rochester, MN     Rochester, MN Metro Area  POLYGON ((-92.67871699999999 44.195516, -92.67...
1  39580       Raleigh, NC       Raleigh, NC Metro Area  POLYGON ((-78.546414 36.021826, -78.5464059999...
2  39660    Rapid City, SD    Rapid City, SD Metro Area  POLYGON ((-103.452453 44.140772, -103.452465 4...
3  40380     Rochester, NY     Rochester, NY Metro Area  POLYGON ((-77.99728999999999 43.132981, -77.99...
4  39700  Raymondville, TX  Raymondville, TX Micro Area  POLYGON ((-97.872384 26.433535, -97.875276 26....
```


## Creating Datasets for Analysis

To perform neighborhood analyses, geosnap provides the `Dataset` class which stores information about the spatial boundaries and social composition of a study area. 

Creating a set of neighborhoods is as simple as instantiating the Dataset class with a location filter and a source database. The location filter can be either a `geopandas.GeoDataFrame` that defines the total extent of a study area (such as an MSA), or a list of state and county FIPS codes.

To use a boundary:

```python
import geopandas
from geosnap import metros
from geosnap.data import Dataset
import libpysal

# read in a geodataframe of Virginia an instantiate the Dataset class with it
va = gpd.read_file(libpysal.examples.get_path('virginia.shp'))
virginia = Dataset(name='Virginia', source='ltdb', boundary=va)

# To use a metropolitan boundary, first select the appropriate area of interest with pandas conventions
dc_metro = metros[metros.NAME.str.startswith('Washintgon-Arlington')]
wash_dc = Dataset(name='Washington DC Metro', source='ltdb', boundary=dc_metro)

```

To use a list of FIPS:

```python
from geosnap.data import Dataset

# Maryland's fips code is 24, Baltimore City is 510 and Baltimore County is 005
baltimore = Dataset(name='Baltimore', source='ltdb', states='24', counties = ['005', '510'])

```
