#!/usr/bin/env python
# coding: utf-8

import json, math, copy
import geosnap
import pandas as pd
import shapely.wkt
import shapely.geometry
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from INCS import linc


def write_INDEX_html(param):
	
	#Create a new folder where GEO_CONFIG.js GEO_JSON.js VARIABLES.js will be saved
	oDir = 'NAM_' + param['filename_suffix']
	path = Path(oDir + '/data')
	path.mkdir(parents=True, exist_ok=True)
	
	contents = []
	#open Neighborhood_Analysis_Mapper.html (the excutable file for the visualization)
	ifile = open("template/Neighborhood_Analysis_Mapper.html", "r")
	contents = ifile.read()
	
	#Replace variables based on the user's selection in each of four files below.
	contents = contents.replace("Neighborhood Analysis Mapper", param['title'])
	contents = contents.replace("data/GEO_CONFIG.js", "data/GEO_CONFIG_"+param['filename_suffix']+".js")
	contents = contents.replace("data/GEO_JSON.js", "data/GEO_JSON_"+param['filename_suffix']+".js")
	contents = contents.replace("data/GEO_VARIABLES.js", "data/GEO_VARIABLES_"+param['filename_suffix']+".js")
	
	#write new outfiles: GEO_CONFIG.js GEO_JSON.js VARIABLES.js
	ofile = open(oDir+"/index.html", "w")
	ofile.write(contents)
	ofile.close()


def write_GEO_CONFIG_js(param):
	# read GEO_CONFIG.js
	ifile = open("template/GEO_CONFIG.js", "r")
	contents = ifile.read()
	
	# perpare parameters
	NumOfMaps = len(param['years']) + 1
	InitialLayers = ["INC"]
	if (len(param['years']) <= 1): InitialLayers = []
	for i, year in enumerate(param['years']):
		InitialLayers.append(str(year))
	
	Index_of_neighborhood_change = True;
	Maps_of_neighborhood = True;               
	Distribution_INC1 = True;                  
	Distribution_period = True; 
	Distribution_cluster = True;
	Temporal_change_in_neighborhoods = True;   
	
	if ('Index_of_neighborhood_change' in param): Index_of_neighborhood_change =  param['Index_of_neighborhood_change']
	if ('Maps_of_neighborhood' in param): Maps_of_neighborhood =  param['Maps_of_neighborhood']
	if ('Distribution_INC1' in param): Distribution_INC1 =  param['Distribution_INC1']
	if ('Distribution_INC2_different_period' in param): Distribution_period =  param['Distribution_INC2_different_period']
	if ('Distribution_INC2_different_cluster' in param): Distribution_cluster =  param['Distribution_INC2_different_cluster']
	if ('Temporal_change_in_neighborhoods' in param): Temporal_change_in_neighborhoods =  param['Temporal_change_in_neighborhoods']
	
	# Automatically set Map_width, Map_height. 
	Map_width = "350px"
	Map_height = "300px"
	if (NumOfMaps <= 5):
		Map_width = "400px"
		Map_height = "400px"
	if (NumOfMaps <= 4):
		Map_width = "500px"
		Map_height = "500px"
	if (NumOfMaps <= 3):
		Map_width = "650px"
		Map_height = "650px"
	if (NumOfMaps <= 2):
		Map_width = "1000px"
		Map_height = "1000px"
		
	# replace newly computed "NumOfMaps", "InitialLayers", "Map_width", "Map_height" in CONFIG.js. See the example replacement below
	'''
		'years': [1980, 1990, 2000, 2010]            ->    'var InitialLayers = ["INC", "1980", "1990", "2000", "2010"];'
	'''
	NumOfMaps = "var NumOfMaps = " + str(NumOfMaps) + ";"
	InitialLayers = "var InitialLayers = " + json.dumps(InitialLayers) + ";"
	Index_of_neighborhood_change = "var Index_of_neighborhood_change = " + json.dumps(Index_of_neighborhood_change)+ ";"
	Maps_of_neighborhood = "var Maps_of_neighborhood = " + json.dumps(Maps_of_neighborhood)+ ";"
	Distribution_INC1 = "var Distribution_INC1 = " + json.dumps(Distribution_INC1)+ ";"
	Distribution_period = "var Distribution_INC2_different_period = " + json.dumps(Distribution_period)+ ";"
	Distribution_cluster = "var Distribution_INC2_different_cluster = " + json.dumps(Distribution_cluster)+ ";"
	Temporal_change_in_neighborhoods = "var Temporal_change_in_neighborhoods = " + json.dumps(Temporal_change_in_neighborhoods)+ ";"
	Map_width = 'var Map_width  = "' + Map_width + '";'
	Map_height = 'var Map_height = "' + Map_height + '";'
   

	contents = contents.replace("var InitialLayers = [];", InitialLayers)
	contents = contents.replace("var Index_of_neighborhood_change = true;", Index_of_neighborhood_change)
	contents = contents.replace("var Maps_of_neighborhood = true;", Maps_of_neighborhood)
	contents = contents.replace("var Distribution_INC1 = true;", Distribution_INC1)
	contents = contents.replace("var Distribution_INC2_different_period = true;", Distribution_period)
	contents = contents.replace("var Distribution_INC2_different_cluster = true;", Distribution_cluster)
	contents = contents.replace("var Temporal_change_in_neighborhoods = true;", Temporal_change_in_neighborhoods)
	contents = contents.replace('var Map_width  = "400px";', Map_width)
	contents = contents.replace('var Map_height = "400px";', Map_height)

	#Write output including the replacement above
	filename_GEO_CONFIG = "NAM_" + param['filename_suffix'] + "/data/GEO_CONFIG_"+param['filename_suffix']+".js"
	ofile = open(filename_GEO_CONFIG, 'w')
	ofile.write(contents)
	ofile.close()


def write_GEO_JSON_js(community, param):
	# query geometry for each tract
	tracts = community.tracts
	geoid = tracts.columns[0]
	
	# open GEO_JSON.js write heading for geojson format
	filename_GEO_JSON = "NAM_" + param['filename_suffix'] + "/data/GEO_JSON_"+param['filename_suffix']+".js"
	ofile = open(filename_GEO_JSON, 'w')
	ofile.write('var GEO_JSON =\n')
	ofile.write('{"type":"FeatureCollection", "features": [\n')
	
	#Convert geometry in GEOJSONP to geojson format
	for tract in tracts.itertuples():
		feature = {"type":"Feature"}
		feature["geometry"] = shapely.geometry.mapping(tract.geometry)
		#feature["properties"] = {geoid: tract.__getattribute__(geoid), "tractID": tract.__getattribute__(geoid)}
		feature["properties"] = {geoid: tract.__getattribute__(geoid)}
		ofile.write(json.dumps(feature)+',\n')
	# complete the geojosn format by adding parenthesis at the end.	
	ofile.write(']}\n')
	ofile.close()


def write_GEO_VARIABLES_js(community, param):
	#print(param)
	geoid     = community.tracts.columns[0]
	method    = param['method']
	nClusters = param['nClusters']
	years     = param['years']
	variables = param['variables']
	
	# filtering by years
	community.census = community.census[community.census.year.isin(years)]
	
	# clustering by method, nClusters with filtering by variables
	clusters = geosnap.analyze.cluster(community, method=method, n_clusters=nClusters, columns=variables)
	df = clusters.census[['year', method]]
	
	# pivot by year column
	df_pivot = df.reset_index().pivot(geoid, "year", method)
	
	if (len(years) > 1):
		# convert df_pivot to list for INCS.linc
		yearList = []
		for year in df_pivot.columns:
			aYearList = df_pivot[year].values.tolist()
			aYearList = list(map(float, aYearList)) 
			yearList.append(aYearList)
		# calculate INC
		incs = linc(yearList)
		# insert INC to first column of df_pivot
		df_pivot.insert(loc=0, column='INC', value=incs)
	
	# write df_pivot to GEO_VARIABLES.js
	filename_GEO_VARIABLES = "NAM_" + param['filename_suffix'] + "/data/GEO_VARIABLES_"+param['filename_suffix']+".js"
	ofile = open(filename_GEO_VARIABLES, 'w')
	ofile.write('var GEO_VARIABLES =\n')
	ofile.write('[\n')
	heading = [geoid, 'INC']
	if (len(years) <= 1): heading = [geoid]
	heading.extend(list(map(str, years)))
	ofile.write('  '+json.dumps(heading)+',\n')
	for i, row in df_pivot.reset_index().iterrows():
		aLine = row.tolist()
		for j, col in enumerate(aLine[2:], 2):
			try:
				aLine[j] = int(col)                                  # convert float to int
			except ValueError:
				aLine[j] = -9999                                     # if Nan, set -9999
		ofile.write('  '+json.dumps(aLine)+',\n')
	ofile.write(']\n')
	ofile.close()


def Aspatial_Clustering_viz(geosnap, param):
	# select community by statefips, cbsafips, countyfips
	if ('cbsafips' in param and param['cbsafips']):
		community = geosnap.data.Community(source=param['database'],cbsafips=param['cbsafips'])
	elif ('statefips' in param and param['statefips'] and 'countyfips' in param and param['countyfips']):
		community = geosnap.data.Community(source=param['database'],statefips=param['statefips'],countyfips=param['countyfips'])
	elif ('statefips' in param and param['statefips']):
		community = geosnap.data.Community(source=param['database'],statefips=param['statefips'])
	
	codebook = pd.read_csv('template/conversion_table_codebook.csv')
	codebook.set_index(keys='variable', inplace=True)
	labels = copy.deepcopy(param['variables'])
	label = 'short_name'                                             # default
	if ('label' in param and param['label'] == 'variable'): label = 'variable'
	if ('label' in param and param['label'] == 'full_name'): label = 'full_name'
	if ('label' in param and param['label'] == 'short_name'): label = 'short_name'
	if (label != 'variable'):
		for idx, variable in enumerate(param['variables']):
			try:
				codeRec = codebook.loc[variable]
				labels[idx] = codeRec[label]
			except:
				print("variable not found in codebook.  variable:", variable)
	param['labels'] = labels
	
	write_INDEX_html(param)
	write_GEO_CONFIG_js(param)
	write_GEO_VARIABLES_js(community, param)
	write_GEO_JSON_js(community, param)
	print('Please run ' + '"NAM_' + param['filename_suffix']+'/index.html"'+' to your web browser.')
	print('Advanced options are available in ' + '"NAM_' + param['filename_suffix']+'/data/GEO_CONFIG.js"')
	

if __name__ == '__main__':
	started_datetime = datetime.now()
	dateYYMMDD = started_datetime.strftime('%Y%m%d')
	timeHHMMSS = started_datetime.strftime('%H%M%S')
	print('GEOSNAP2NAM start at %s %s' % (started_datetime.strftime('%Y-%m-%d'), started_datetime.strftime('%H:%M:%S')))
	
	param = {
		'title': "Neighborhood Analysis: Kmeans, Albertville",
		'filename_suffix': "Albertville",
		'database': "ltdb",
		'statefips': None,
		'cbsafips': "10700",
		'countyfips': None,
		'years': [1980, 1990, 2000, 2010],           # Available years: 1970, 1980, 1990, 2000 and 2010
		'method': "kmeans",                          # affinity_propagation, gaussian_mixture, hdbscan, kmeans, spectral, ward   
		'nClusters': 8,                              # This option should be commented out for affinity_propagation and hdbscan
		'variables': ["p_nonhisp_white_persons", 
					  "p_nonhisp_black_persons", 
					  "p_hispanic_persons", 
					  "p_native_persons", 
					  "p_asian_persons",
					 ],
		# optional visualization below.
		'Index_of_neighborhood_change': True,        #choropleth map: Maps representing index of neighborhood Change
		'Maps_of_neighborhood': True,                #choropleth map: Maps representing clustering result		
		'Distribution_INC1': True,                   #density chart: INC changes as the map extent changes 
		'Distribution_INC2_different_period': True,  #density chart: INC changes by different years
		'Distribution_INC2_different_cluster': True, #density chart: INC changes by different clusters
		'Temporal_change_in_neighborhoods': True,    #stacked chart: Temporal Change in Neighborhoods over years
	}
	
	
	Aspatial_Clustering_viz(geosnap, param)
	
	ended_datetime = datetime.now()
	elapsed = ended_datetime - started_datetime
	total_seconds = int(elapsed.total_seconds())
	hours, remainder = divmod(total_seconds,60*60)
	minutes, seconds = divmod(remainder,60)	
	print('GEOSNAP2NAM ended at %s %s    Elapsed %02d:%02d:%02d' % (ended_datetime.strftime('%Y-%m-%d'), ended_datetime.strftime('%H:%M:%S'), hours, minutes, seconds))
	
