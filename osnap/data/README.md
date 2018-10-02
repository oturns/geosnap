# Data Layer

## Importing Data from External Databases

OSLNAP provides import functions for popular databases that provide harmonized
Census boundaries. **You must provide your own copy of the external database**.
The importers can be accessed via the `data` module

### Longitudinal Tract Database (LTDB)

The [Longitudinal Tract Database
(LTDB)](https://s4.ad.brown.edu/projects/diversity/Researcher/LTDB.htm) is a
freely available dataset developed by researchers at Brown University that
provides census data harmonized to 2010 boundaries.

To import LTDB into OSLNAP, proceed with the following:

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
- in your file browser, navigate to the two zip archives you just downloaded. By
  default they are called `LTDB_Std_All_Sample.zip` and
  `LTDB_Std_All_fullcount.zip`. Extract both of these zip archives into a single
  directory containing all CSV files:

[placeholder image]

Finally, to load the data into oslnap, call the `import_ltdb` function and pass the path of the directory containing the LTDB CSV files

```
from oslnap.data import import_ltdb
import_ltdb("~/ltdb_data")

```
    




### Geolytics Neighborhood Change Database (NCDB)

#### Datasets from Geolytics NCDB

Can be downloaded [here](https://drive.google.com/file/d/1QornB-VPWGwqiEmM4_np_hrJ4IbY31UW/view?usp=sharing)

#### Metadata and data dictionary

* Metadata purchased from Geolytics can be downloaded [here](https://drive.google.com/file/d/1QornB-VPWGwqiEmM4_np_hrJ4IbY31UW/view?usp=sharing)
* Data dictionary downloaded from Geolytics website can be found [here](geolytics/materials/user-guide/Appendix-E.pdf)


#### Data processing
* 14 variables for sensitivity analysis
    * Python code for processing Geolytics NCDB data and extract 14 variables: [geolytics/geolytics_processing_14.py](geolytics/geolytics_processing_14.py)
    * The extracted datasets (one csv file per year) are living [here](https://drive.google.com/drive/folders/1_ieUSrHUErrG7RuTUMVF_7MUnlO4iBol?usp=sharing)
    and should be ready for further analysis.
        * There are two csv data files per year. The only difference lies in the variable names:
            * files with names starting with "geolytics" (for example "geolytics_14_1970") use geolytics variable names
            * files with names starting with "newName" (for example "newName_geolytics_14_1970") use ["new" names](https://docs.google.com/spreadsheets/u/1/d/1ywu3sNY1gBGPyu_2XWL7ps1b9VCOR7z5Ba9stachQbs/edit?ouid=102330163499148373088&usp=sheets_home&ths=true)
        * Since geolytics does not provide variables relevant to *Median value of owner-occupied housing units* (variable **MDVALHSy**) for 1970 and 1980. The current csv files 1970 and 1980 are missing this variable.

## Census and ACS data (original)
