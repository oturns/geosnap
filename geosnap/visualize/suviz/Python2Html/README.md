<p align="center">
<img height=200 src="images/geosnap_viz.png" alt="geosnap"/>
</p>

<h2 align="center" style="margin-top:-10px">The Geospatial Neighborhood Analysis Package Visualizer</h2> 

`GEOSNAP-VIZ` has a highly interactive and dynamic user-interface that makes it easier to explore, model, analyze, and visualize the social and spatial dynamics of neighborhoods. GEOSNAP-VIZ visualizes not only data from census and American communisty survey (ACS), but also results of several spatial statistcs that help to study spatiotemporal neighborhood changes. Here is the list of sptial and statistical analyses that `GEOSNAP-VIZ` provides [1]:
 #### Neighborhood Clustering Methods
  ##### Classic (aspatial) Clustering
  	- Clustering with Affinity Propagation
  	- Clustering with Gaussian Mixture Model
  	- Clustering with Hierarchical DBSCAN
  	- K-Means clustering.
  	- spectral clustering
  	- Agglomerative clustering using Ward linkage
  ##### Spatial Clustering  
  	- AZP clustering algorithm
  	- Max-p clustering algorithm 
  	- SKATER spatial clustering algorithm.
  	- Spatially encouraged spectral clustering
  	- Agglomerative clustering using Ward linkage with a spatial connectivity
  #### Neighborhood Dynamics Methods
  	- Index of Neighborhood Change (INC): Local Indicator of Neighborhhod Change
  	- Sequence Analysis: Pairwise sequence analysis and sequence clustering

`GEOSNAP-VIZ` consists of GEOSNAP2ACM (Adaptive Choropleth Mapper) and GOESNA2NAM (Neighborhood Analysis Mapper). GEOSNAP2ACM and GEOSNAP2NAM are open source GIS software packages that support (1) querying Race/Ethnicity, Socioeconomic and Demographic variables, (2) data exploration, (3) neighborhood delineation and analysis, and (4) user-interactive and dynamic visualization.

- GEOSNAP2ACM contains modules Data Exploration – (1) Adaptive Choropleth Mapper (ACM), (2) ACM with Correlogram, (3) ACM with Scatter plot, (4) ACM with Time Series, and (5) ACM with PCP.

- GEOSNAP2NAM contains modules for Data Delineation and Neighborhood Analysis - (1) Maps of Neighborhood with a Stacked Chart, (2) Maps of INC and Neighborhoods, (3) Maps of Neighborhood with Parallel Categories Diagram, and (4) Maps of Neighborhood with Chord Diagram.

Both GEOSNAP2ACM and GEOSNAP2NAM utilize data  and  sptial and statistical analyses from GeoSpatial Neighborhood Analysis Package (GEOSNAP) which are written in Python,  and combines them with a visualization layer written in Javascript, Html and CSS. The visualization layer is made of open-source JavaScript libraries such as Leaflet, Plotly, and D3. 


### Prerequisites

 Python3 (comes with Anaconda3) and Jupyter Notebook are required to run GEOSNAP2ACM and GEOSNAP2NAM. For visualization, Firefox  or Google Chrome work best. It has not been tested in Internet Explorer (IE).

GEOSNAP must be installed in order to run GEOSNAP2ACM and GEOSNAP2NAM. The installation instruction is available at: https://github.com/spatialucr/geosnap. 

First-time users need to download LTDB data which are input for both GEOSNAP2ACM and GEONSNAP2NAM
- Download LTDB data and create the folder, “downloads” in the GEOSNAP2ACM. https://s4.ad.brown.edu/projects/diversity/Researcher/LTDB.htm
- On the webpage above, click “CLICK HERE for the download page”. Provide your email address and check for all agreements. On the next page, Two drop-down boxes “Select a file type:” and “Select a year” with a button, “Download Standard Data Files” are available. Download both “Full” and “Sample” for “All Years”. Then, you are going to have two datasets, “LTDB_Std_All_fullcount.zip” and “LTDB_Std_All_Sample.zip”. 
- Create a folder, “downloads” in the “GEOSNAP2ACM” folder you downloaded in the previous step and included the downloaded datasets in the folder “downloads”. If you run “GEOSNAP2NAM” first, create a folder, “download” in the “GEOSNAP2NAM” folder and include the datasets in the folder. 

### Getting Started

Run Jupyter notebook examples below to learn how to use GEOSNAP2ACM and GEOSNAP2NAN. Each folder has example output like below.
#### GEOSNAP2ACM 
 1. ACM_SD_ACM_only : The output of ACM_only.ipynb. 
<br />It visualizes selected variables by using Adaptive Choropleth Mapper.
<br />Video demo: http://sarasen.asuscomm.com/ACM

 2. ACM_SD_correlogram: The output of ACM_correlogram.ipynb. 
<br />It visualizes the matrix of scatter plots.
<br />Video demo: http://osnap.cloud/~suhan/videos/ACM_SD_correlogram_1
<br />Advanced options: http://osnap.cloud/~suhan/videos/ACM_SD_correlogram_2

 3. ACM_SD_Scatter : The output of  ACM_ScatterPlot.ipynb. 
<br />It visualizes only two scatter plots, but it has more interactive features than ACM_correlogram.
<br />Video demo: http://osnap.cloud/~suhan/videos/ACM_SD_Scatter_1

 4. ACM_SD_TimeSeries : The output of ACM_TimeSeries.ipynb
<br />It visualizes the temporal change of the selected variables. 
<br />Video demo:

 5. ACM_SD_ParallelCoordinates : The output of  ACM_ParallelCoordinates.ipynb
<br />It visualizes the relationships among multiple variables.
<br />Video demo:

#### GEOSNAP2NAM


 1. NAM_SD_eveything : The output of GEOSNAP2NAM.ipynb 
<br />This example visualizes all charts and maps including the result of sequence analysis (Just like an image above). Visualizing everything like this creates too many maps and charts. So it is hard to understand what is what. From this reason, charts and maps are divided into the four examples of output visualization below
<br />Video demo: http://osnap.cloud/~suhan/videos/NAM_SD_everything

 2. NAM_US_0_INC: The output of GEOSNAP2NAM0_INC_whole.ipynb 
<br />This example computes INC value of all metro areas in the US and visualize the result using the Adaptive Choropleth Mapper (ACM). Please note that metro id is displayed on the top right corner of the map. The metro id can be used to create each of map visualization below from #3 to #6. Note: This is computing intensive. Once you run it, you will see the program bar -0.1%, which means that it is querying the data (takes 2 - 3 minutes). Once the querying is done, the progress bar shows how much percent the computatino is done.

 3. NAM_SD_1_neighborhood : The output of  GEOSNAP2NAM1_neighborhood.ipynb 
<br />This example visualizes the spatiotemporal change of neighborhood (clustering result)
<br />Video demo: http://osnap.cloud/~suhan/videos/NAM_SD_1_neighborhood

 4. NAM_SD_2_INC_neighborhood : The output of GEOSNAP2NAM2_INC_neighborhood.ipynb
<br />This example visualizes a map of the index of neighborhood change with maps showing the spatiotemporal change of neighborhood.
<br /> Video demo: http://osnap.cloud/~suhan/videos/NAM_SD_2_INC_neighborhood

 5. NAM_SD_3_sequence_neighborhood_categoriesDiagram : The output of  GEOSNAP2NAM3_sequence_neighborhood_categoriesDiagram.ipynb
<br />This example visualizes the parallel categorical diagram with maps showing the spatiotemporal change of neighborhood.
<br />Video demo: http://osnap.cloud/~suhan/videos/NAM_SD_3_sequence_neighborhood_categoriesDiagram

 6. NAM_SD_4_sequence_neighborhood_chordDiagram : The output of GEOSNAP2NAM4_sequence_neighborhood_chordDiagram.ipynb
<br />This example visualizes the chord diagram with maps showing the spatiotemporal change of neighborhood. 
<br /> Video demo: http://osnap.cloud/~suhan/videos/NAM_SD_4_sequence_neighborhood_chordDiagram

 
In the source code, the lines below should be executed only for the first run to write LTDB data downloaded in the previous step to your disk. The lines below are commented out. Remove # in each of the lines and comment out again after the first run. This process takes about 10 - 15 minutes. But you do not need to repeat it from the second run.
```
sample = "downloads/LTDB_Std_All_Sample.zip"
full = "downloads/LTDB_Std_All_fullcount.zip"
store_ltdb(sample=sample, fullcount=full)
store_census()
```

When “Adaptive_Choropleth_Mapper_viz(param)” is executed in each of the examples above, the web-browser automatically opens and shows the visualization result. The web-browser is supposed to open automatically. However, if you cannot find the browser opened, run the visualization output by drag and drop ACM_XXXX/index.html or NAM_XXXX/index.html on your browser.

Click [here](https://docs.google.com/document/d/1ifBeubg0RKBr4Dh9pUONq7GZ8c_9ZnxgwIbBjkRQRmU/edit?usp=sharing) to see User's Manual

### Refernces

[1] geosnap API reference. URL: https://spatialucr.github.io/geosnap/api.html

## Built With

* [GEOSNAP](https://github.com/spatialucr/geosnap) - Data and Analysis Layer were used
* [Leaflet](https://leafletjs.com) - Used to make maps
* [PlotlyJS](https://plot.ly/javascript/) - Used to make charts
* [D3](https://d3js.org/) - Used to make charts


## Authors

GEOSNAP2ACM and GEOSNAP2NAM have been developed by Su Yeon Han, Sergio Rey, Elijah Knaap, Wei Kang and other members at Center for Geospatial Sciences at University of California, Riverside

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Funding

<img src="images/nsf_logo.jpg" width=100 /> This project is supported by NSF Award #1733705,
[Neighborhoods in Space-Time Contexts](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1733705&HistoricalAwards=false)

