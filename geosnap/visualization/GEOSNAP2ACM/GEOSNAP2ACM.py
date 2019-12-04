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


def write_INDEX_html(param):
	
	#Create a new folder where GEO_CONFIG.js GEO_JSON.js VARIABLES.js will be saved
	oDir = 'ACM_' + param['filename_suffix']
	path = Path(oDir + '/data')
	path.mkdir(parents=True, exist_ok=True)
	
	contents = []
	#open Adaptive_Choropleth_Mapper.html (the excutable file for the visualization)
	ifile = open("template/Adaptive_Choropleth_Mapper.html", "r")
	contents = ifile.read()
	
	#Replace variables based on the user's selection in each of four files below.
	contents = contents.replace("Adaptive Choropleth Mapper", param['title'])
	contents = contents.replace("GEO_CONFIG.js", "data/GEO_CONFIG_"+param['filename_suffix']+".js")
	contents = contents.replace("GEO_JSON.js", "data/GEO_JSON_"+param['filename_suffix']+".js")
	contents = contents.replace("GEO_VARIABLES.js", "data/GEO_VARIABLES_"+param['filename_suffix']+".js")
	
	#write new outfiles: GEO_CONFIG.js GEO_JSON.js VARIABLES.js
	ofile = open(oDir+"/index.html", "w")
	ofile.write(contents)
	ofile.close()


def write_GEO_CONFIG_js(param):
	# read GEO_CONFIG.js
	ifile = open("template/GEO_CONFIG.js", "r")
	contents = ifile.read()
	
	# Automatically identify variables for "NumOfMaps" and "InitialLayers"
	'''when the user selects more than one year among 1970, 1980, 1990, 200 and 2010, "NumOfMaps" will be equal to the number of the selected years. However, when the user selects only one year among 5 years, "NumOfMaps" will be the number of variables that the user selected. (The maximum number of maps that can be visualized is 15) In this case, when the user selects more than 15 variables, the first 15 maps will be created at the initial view, and the rest of variables will be available in the dropdown box of the top of each map. In brief, there is no limit in terms of variables that the user can visualize, but the user can visualize upto 15 maps at the same time.'''
	NumOfMaps = len(param['years'])
	InitialLayers = []
	if (NumOfMaps > 1):
		for i, year in enumerate(param['years']):
			InitialLayers.append(str(year)+' '+param['labels'][0])
	else:
		NumOfMaps = len(param['labels'])
		if (NumOfMaps > 15): NumOfMaps = 15
		for i, variable in enumerate(param['labels']):
			InitialLayers.append(str(param['years'][0])+' '+variable)
	
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
		NumOfMaps  :    4                ->    'var NumOfMaps = 4;'
		InitialLayers   :    [ … ]            ->    'var InitialLayers = ["1980 p_nonhisp_white_persons", "1980 p_nonhisp_black_persons", "1980 p_hispanic_persons", … ];'
		Map_width    :    "400px"    ->    'var Map_width = "400px";'
		Map_height   :    "400px"    ->    'var Map_height = "400px";'
	'''
	NumOfMaps = "var NumOfMaps = " + str(NumOfMaps) + ";"
	InitialLayers = "var InitialLayers = " + json.dumps(InitialLayers) + ";"
	Map_width = 'var Map_width  = "' + Map_width + '";'
	Map_height = 'var Map_height  = "' + Map_height + '";'
   
	contents = contents.replace("var NumOfMaps = 1;", NumOfMaps)
	contents = contents.replace("var InitialLayers = [];", InitialLayers)
	contents = contents.replace('var Map_width  = "400px";', Map_width)
	contents = contents.replace('var Map_height = "400px";', Map_height)

	#Write output including the replacement above
	filename_GEO_CONFIG = "ACM_" + param['filename_suffix'] + "/data/GEO_CONFIG_"+param['filename_suffix']+".js"
	ofile = open(filename_GEO_CONFIG, 'w')
	ofile.write(contents)
	ofile.close()


def write_GEO_JSON_js(community, param):
	# query geometry for each tract
	tracts = community.tracts
	geoid = tracts.columns[0]
	
	# open GEO_JSON.js write heading for geojson format
	filename_GEO_JSON = "ACM_" + param['filename_suffix'] + "/data/GEO_JSON_"+param['filename_suffix']+".js"
	ofile = open(filename_GEO_JSON, 'w')
	ofile.write('var GEO_JSON =\n')
	ofile.write('{"type":"FeatureCollection", "features": [\n')
	
	#Convert geometry in GEOJSONP to geojson format
	for tract in tracts.itertuples():
		feature = {"type":"Feature"}
		feature["geometry"] = shapely.geometry.mapping(tract.geometry)
		feature["properties"] = {geoid: tract.__getattribute__(geoid), "tractID": tract.__getattribute__(geoid)}
		ofile.write(json.dumps(feature)+',\n')
	# complete the geojosn format by adding parenthesis at the end.	
	ofile.write(']}\n')
	ofile.close()


def write_GEO_VARIABLES_js(community, param):
	#print(param)
	#make heading: community.tracts.columns[0] has "geoid" (string)
	heading = [community.tracts.columns[0]]
	for i, year in enumerate(param['years']):
		for j, variable in enumerate(param['labels']):
			heading.append(str(year)+' '+variable)
	
	#Make Dictionary
	mydictionary = {}    # key: geoid, value: variables by heading
	h = -1
	for i, year in enumerate(param['years']):
		for j, variable in enumerate(param['variables']):
			h += 1
			selectedSeries = community.census[community.census.year==year][variable]
			for geoid, val in selectedSeries.iteritems():
				#print(geoid, value)
				if (math.isnan(val)): #converts Nan in GEOSNAP data to -9999
					#print(i, j, geoid, year, val)
					val = -9999
				if (geoid in mydictionary):
					value = mydictionary[geoid]
					value[h] = val
				else:
					value = [-9999] * (len(heading) - 1)                
					value[h] = val
				mydictionary[geoid] = value
				
	#Select keys in the Dictionary and sort
	keys = list(mydictionary.keys())
	keys.sort()
	# Uuse Keys and Dictionary created above and write them GEO_VARIABLES.js
	filename_GEO_VARIABLES = "ACM_" + param['filename_suffix'] + "/data/GEO_VARIABLES_"+param['filename_suffix']+".js"
	ofile = open(filename_GEO_VARIABLES, 'w')
	ofile.write('var GEO_VARIABLES =\n')
	ofile.write('[\n')
	ofile.write('  '+json.dumps(heading)+',\n')
	for i, geoid in enumerate(keys):
		values = mydictionary[geoid]
		values.insert(0, geoid)
		#print(geoid, values)
		ofile.write('  '+json.dumps(values)+',\n')
	ofile.write(']\n')
	ofile.close()


def create_ACMfiles(geosnap, param):
	community = geosnap.data.Community(source=param['database'],cbsafips=param['cbsafips'])
	
	codebook = pd.read_csv('template/conversion_table_codebook.csv')
	codebook.set_index(keys='variable', inplace=True)
	labels = copy.deepcopy(param['variables'])
	label = 'short_name'                                             # default
	if (param['label'] == 'variable'): label = 'variable'
	if (param['label'] == 'full_name'): label = 'full_name'
	if (param['label'] == 'short_name'): label = 'short_name'
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
	print('Please run ' + '"ACM_' + param['filename_suffix']+'/index.html"'+' to your web browser.')
	

if __name__ == '__main__':
	started_datetime = datetime.now()
	dateYYMMDD = started_datetime.strftime('%Y%m%d')
	timeHHMMSS = started_datetime.strftime('%H%M%S')
	print('GEOSNAP2ACM start at %s %s' % (started_datetime.strftime('%Y-%m-%d'), started_datetime.strftime('%H:%M:%S')))
	
	sample = "downloads/LTDB_Std_All_Sample.zip"
	full = "downloads/LTDB_Std_All_fullcount.zip"
	geosnap.data.read_ltdb(sample=sample, fullcount=full)
	
	param = {
		'title': "Adaptive Choropleth Mapper",
		'filename_suffix': "Albertville",
		'database': "ltdb",
		'statefips': None,
		'cbsafips': "10700",
		'countyfips': None,
		'years': [1980, 1990, 2000, 2010],
		'variables': ["p_nonhisp_white_persons", 
					  "p_nonhisp_black_persons", 
					  "p_hispanic_persons", 
					  "p_native_persons", 
					  "p_asian_persons",
					 ],
		'label': "short_name",                                       # variable, short_name or full_name
	}
	
	#community = geosnap.data.Community(source=param['database'],cbsafips=param['cbsafips'])
	#write_INDEX_html(param)
	#write_GEO_CONFIG_js(param)
	#write_GEO_VARIABLES_js(community, param)
	#write_GEO_JSON_js(community, param)
	
	create_ACMfiles(geosnap, param)
	
	ended_datetime = datetime.now()
	elapsed = ended_datetime - started_datetime
	total_seconds = int(elapsed.total_seconds())
	hours, remainder = divmod(total_seconds,60*60)
	minutes, seconds = divmod(remainder,60)	
	print('GEOSNAP2ACM ended at %s %s    Elapsed %02d:%02d:%02d' % (ended_datetime.strftime('%Y-%m-%d'), ended_datetime.strftime('%H:%M:%S'), hours, minutes, seconds))
	
