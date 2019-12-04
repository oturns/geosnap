#!/usr/bin/env python
# coding: utf-8

import json, math, copy
from geosnap.data import store_ltdb
from geosnap.data import Community
from geosnap.data import store_census
from geosnap.data import data_store
import pandas as pd
import shapely.wkt
import shapely.geometry
from datetime import datetime
from datetime import timedelta
from pathlib import Path
import urllib.parse
import webbrowser
import os
import pprint


def write_LOG(param):
	#Create a new folder where GEO_CONFIG.js GEO_JSON.js VARIABLES.js will be saved
	oDir = 'ACM_' + param['filename_suffix']
	path = Path(oDir + '/data')
	path.mkdir(parents=True, exist_ok=True)
	
	contents = pprint.pformat(param)
	#print(oDir+"/data/param.log")
	#print(contents)
	#write new outfiles: GEO_CONFIG.js GEO_JSON.js VARIABLES.js
	ofile = open(oDir+"/data/param.log", "w")
	create_at = datetime.now()
	ofile.write('%s %s\r\n' % (create_at.strftime('%Y-%m-%d'), create_at.strftime('%H:%M:%S')))
	#ofile.write('\r\n\r\n')
	ofile.write('  '+contents.replace('\n', '\n  '))
	ofile.close()


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
	
	# Automatically identify variables for "NumOfMaps" and "InitialLayers"
	'''when the user selects more than one year among 1970, 1980, 1990, 200 and 2010, "NumOfMaps" will be equal to the number of the selected years. However, when the user selects only one year among 5 years, "NumOfMaps" will be the number of variables that the user selected. (The maximum number of maps that can be visualized is 15) In this case, when the user selects more than 15 variables, the first 15 maps will be created at the initial view, and the rest of variables will be available in the dropdown box of the top of each map. In brief, there is no limit in terms of variables that the user can visualize, but the user can visualize upto 15 maps at the same time.'''
	NumOfMaps = len(param['years'])
	chart = param['chart'] if 'chart' in param else ''
	if (chart == "Scatter Plot"): NumOfMaps = 2
	InitialLayers = []
	if (NumOfMaps > 1):
		for i, year in enumerate(param['years']):
			InitialLayers.append(str(year)+' '+param['labels'][0])
	else:
		NumOfMaps = len(param['labels'])
		if ('NumOfMaps' in param): NumOfMaps = param['NumOfMaps']
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
	if (NumOfMaps <= 1):
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
	
	chart = param['chart'] if 'chart' in param else ''
	Stacked_Chart = "var Stacked_Chart = false;"
	Correlogram = "var Correlogram = false;"
	Scatter_Plot = "var Scatter_Plot = false;"
	Parallel_Coordinates_Plot = "var Parallel_Coordinates_Plot = false;"
	if (chart == "Stacked Chart"): Stacked_Chart = "var Stacked_Chart = true;"
	elif (chart == "Correlogram"): Correlogram = "var Correlogram = true;"
	elif (chart == "Scatter Plot"): Scatter_Plot = "var Scatter_Plot = true;"
	elif (chart == "Parallel Coordinates Plot"): Parallel_Coordinates_Plot = "var Parallel_Coordinates_Plot = true;"
	else: Stacked_Chart = "var Stacked_Chart = true;"

	contents = contents.replace("var Stacked_Chart = false;", Stacked_Chart)
	contents = contents.replace("var Correlogram = false;", Correlogram)
	contents = contents.replace("var Scatter_Plot = false;", Scatter_Plot)
	contents = contents.replace("var Parallel_Coordinates_Plot = false;", Parallel_Coordinates_Plot)

	#Write output including the replacement above
	filename_GEO_CONFIG = "ACM_" + param['filename_suffix'] + "/data/GEO_CONFIG_"+param['filename_suffix']+".js"
	ofile = open(filename_GEO_CONFIG, 'w')
	ofile.write(contents)
	ofile.close()


def write_GEO_JSON_js(community, param):
	# query geometry for each tract
	geoid = community.gdf.columns[0]
	tracts = community.gdf[[geoid, 'geometry']].copy()
	tracts.drop_duplicates(subset=geoid, inplace=True)					# get unique geoid
	#print(tracts)
	
	# open GEO_JSON.js write heading for geojson format
	filename_GEO_JSON = "ACM_" + param['filename_suffix'] + "/data/GEO_JSON_"+param['filename_suffix']+".js"
	ofile = open(filename_GEO_JSON, 'w')
	ofile.write('var GEO_JSON =\n')
	ofile.write('{"type":"FeatureCollection", "features": [\n')
	
	#Convert geometry in GEOJSONP to geojson format
	for tract in tracts.itertuples():
		feature = {"type":"Feature"}
		if (type(tract.geometry) is float):								# check is NaN?
			#print(tract.geometry)
			continue
		feature["geometry"] = shapely.geometry.mapping(tract.geometry)
		#feature["properties"] = {geoid: tract.__getattribute__(geoid), "tractID": tract.__getattribute__(geoid)}
		feature["properties"] = {geoid: tract.__getattribute__(geoid)}
		ofile.write(json.dumps(feature)+',\n')
	# complete the geojosn format by adding parenthesis at the end.	
	ofile.write(']}\n')
	ofile.close()


def write_GEO_VARIABLES_js(community, param):
	#print(param)
	geoid        =  community.gdf.columns[0]
	years        =  param['years']
	variables    =  param['variables']
	
	## filtering by years
	#community.gdf = community.gdf[community.gdf.year.isin(years)]
	#print(community.gdf)
	#selectedCommunity = community.gdf[variables]
	#print(community.gdf)
	#return
	
	#make heading: community.gdf.columns[0] has "geoid" (string)
	heading = [geoid]
	for i, year in enumerate(years):
		for j, variable in enumerate(param['labels']):
			heading.append(str(year)+' '+variable)
	
	#Make Dictionary
	mydictionary = {}    # key: geoid, value: variables by heading
	h = -1
	selectedColumns = [geoid]
	selectedColumns.extend(variables)
	#print("selectedColumns:", type(selectedColumns), selectedColumns)
	for i, year in enumerate(years):
		aYearDF = community.gdf[community.gdf.year==year][selectedColumns]
		#print(year, type(aYearDF), aYearDF)
		for j, variable in enumerate(variables):
			h += 1
			for index, row in aYearDF.iterrows():
				#print(index, row)
				key = row[geoid]
				val = row[variable]
				if (math.isnan(val)): #converts Nan in GEOSNAP data to -9999
					#print(i, j, key, year, val)
					val = -9999
				if (key in mydictionary):
					value = mydictionary[key]
					value[h] = val
				else:
					value = [-9999] * (len(heading) - 1)                
					value[h] = val
				mydictionary[key] = value
				
	#Select keys in the Dictionary and sort
	keys = list(mydictionary.keys())
	keys.sort()
	# use Keys and Dictionary created above and write them GEO_VARIABLES.js
	filename_GEO_VARIABLES = "ACM_" + param['filename_suffix'] + "/data/GEO_VARIABLES_"+param['filename_suffix']+".js"
	ofile = open(filename_GEO_VARIABLES, 'w')
	ofile.write('var GEO_VARIABLES =\n')
	ofile.write('[\n')
	ofile.write('  '+json.dumps(heading)+',\n')
	for i, key in enumerate(keys):
		values = mydictionary[key]
		values.insert(0, key)
		#print(key, values)
		ofile.write('  '+json.dumps(values)+',\n')
	ofile.write(']\n')
	ofile.close()


def Adaptive_Choropleth_Mapper_viz(param):
	write_LOG(param)
	
	# convert year, variable to years, variables in the param
	if ('years' not in param and 'year' in param): param['years'] = [param['year']]
	if ('variables' not in param and 'variable' in param): param['variables'] = [param['variable']]
	#print(param)
	
	# select community by state_fips, msa_fips, county_fips
	if ('msa_fips' in param and param['msa_fips']):
		community = Community.from_ltdb(years=param['years'], msa_fips=param['msa_fips'])
		#community = Community.from_ltdb(msa_fips=param['msa_fips'])
	elif ('county_fips' in param and param['county_fips']):
		community = Community.from_ltdb(years=param['years'], county_fips=param['county_fips'])
	elif ('state_fips' in param and param['state_fips']):
		community = Community.from_ltdb(years=param['years'], state_fips=param['state_fips'])
	#print(community.gdf)
	
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
	
	local_dir = os.path.dirname(os.path.realpath(__file__))
	fname =urllib.parse.quote('index.html')
	template_dir = os.path.join(local_dir, 'ACM_' + param['filename_suffix'])
	url = 'file:' + os.path.join(template_dir, fname)
	webbrowser.open(url)
	
	print('Please run ' + '"ACM_' + param['filename_suffix']+'/index.html"'+' to your web browser.')
	print('Advanced options are available in ' + '"ACM_' + param['filename_suffix']+'/data/GEO_CONFIG.js"')


def Adaptive_Choropleth_Mapper_log():
	# build array of logs from directory of 'ACM_'
	logs = []
	dirname = os.getcwd()
	subnames = os.listdir(dirname)
	for subname in subnames:
		fullpath = os.path.join(dirname, subname)
		if (not os.path.isdir(fullpath)): continue
		if (not subname.startswith('ACM_')): continue
		#print(os.path.join(fullpath, 'index.html'))
		indexfile = os.path.join(fullpath, 'index.html')
		logfile = os.path.join(fullpath, 'data/param.log')
		if (not os.path.exists(indexfile)): continue
		if (not os.path.exists(logfile)): continue
		#print(fullpath, logfile)
		# read param.log
		ifile = open(logfile, "r")
		wholetext = ifile.read()
		contents = wholetext.split('\n', maxsplit=1)
		if (len(contents) != 2): continue
		create_at = contents[0]
		param     = contents[1]
		#print(create_at)
		#print(param)
		logs.append({'indexfile': os.path.join(subname, 'index.html'), 'create_at': create_at, 'param': param})
	logs = sorted(logs, key=lambda k: k['create_at']) 
	#print(logs)
	
	#Write output to log.html
	filename_LOG = "log.html"
	ofile = open(filename_LOG, 'w')
	ofile.write('<!DOCTYPE html>\n')
	ofile.write('<html>\n')
	ofile.write('<head>\n')
	ofile.write('  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>\n')
	ofile.write('  <title>Adaptive Choropleth Mapper Logging</title>\n')
	ofile.write('</head>\n')
	ofile.write('<body>\n')
	ofile.write('  <header>\n')
	ofile.write('    <h1>Adaptive Choropleth Mapper Logging</h1>\n')
	ofile.write('  </header>\n')
	
	for idx, val in enumerate(logs):
		params = val['param'].split('\n')
		html = '\n'
		html += '<div style="margin:10px; float:left; border: 1px solid #99CCFF; border-radius: 5px;">\n'
		html += '  <table>\n'
		html += '    <tr>\n'
		html += '      <td>\n'
		html += '        <button id="global_submit" type="button" style="margin:0px 20px 0px 5px;" onclick="window.open(\'' + val['indexfile'] + '\')">' + str(idx+1) + '. Show This</button>\n'
		html += '        ' + val['create_at'] + '\n'
		html += '      </td>\n'
		html += '    </tr>\n'
		html += '    <tr>\n'
		html += '      <td>\n'
		html += '<pre>\n'
		for param in params:
			html += param + '\n'
		html += '</pre>\n'
		html += '      </td>\n'
		html += '    </tr>\n'
		html += '  </table>\n'
		html += '</div>\n'
		ofile.write(html)
	
	ofile.write('</body>\n')
	ofile.write('</html>')
	ofile.close()
	
	local_dir = os.path.dirname(os.path.realpath(__file__))
	fname =urllib.parse.quote(filename_LOG)
	url = 'file:' + os.path.join(local_dir, fname)
	webbrowser.open(url)
	

if __name__ == '__main__':
	started_datetime = datetime.now()
	dateYYMMDD = started_datetime.strftime('%Y%m%d')
	timeHHMMSS = started_datetime.strftime('%H%M%S')
	print('GEOSNAP2ACM start at %s %s' % (started_datetime.strftime('%Y-%m-%d'), started_datetime.strftime('%H:%M:%S')))
	
	#sample = "downloads/LTDB_Std_All_Sample.zip"
	#full = "downloads/LTDB_Std_All_fullcount.zip"
	#store_ltdb(sample=sample, fullcount=full)
	#store_census()
	
	param = {
		'title': "Adaptive Choropleth Mapper",
		'filename_suffix': "SD",
		#'database': "ltdb",
		#'state_fips': None,
		'msa_fips': "41740",
		#'county_fips': None,
		
		#'chart': "Stacked Chart",
		#'years': [1980, 1990, 2000, 2010],
		#'variables': [
		#	"p_nonhisp_white_persons",
		#	"p_nonhisp_black_persons", 
		#	"p_hispanic_persons", 
		#],
		
		#'chart': "Correlogram",
		#'year': 2000,
		#'variables': [
		#	"p_other_language",
		#	"p_female_headed_families", 
		#	"median_income_blackhh", 
		#	"median_income_hispanichh", 
		#	"median_income_asianhh",
		#	"per_capita_income",
		#],
		
		#'chart': "Scatter Plot",
		#'year': 2010,
		#'variables': [
		#	"p_nonhisp_white_persons",
		#	"p_nonhisp_black_persons", 
		#	"p_hispanic_persons", 
		#	"p_native_persons", 
		#	"p_asian_persons",
		#	"p_hawaiian_persons",
		#	"p_asian_indian_persons",
		#	"p_chinese_persons",
		#	"p_filipino_persons",
		#	"p_japanese_persons",
		#	"p_korean_persons",
		#	"p_vietnamese_persons",
		#	"median_household_income",
		#	"median_income_whitehh",
		#	"median_income_blackhh",
		#	"median_income_hispanichh",
		#	"median_income_asianhh",
		#	"per_capita_income",
		#],
		
		## Parallel Coordinates Plot time
		#'chart': "Parallel Coordinates Plot",
		#'years': [1980,1990,2000,2010],
		#'variable': "p_nonhisp_white_persons",
		
		# Parallel Coordinates Plot
		'chart': "Parallel Coordinates Plot",
		'year': 2000,
		'NumOfMaps': 6,
		'variables': [
			"p_nonhisp_white_persons",
			"p_nonhisp_black_persons", 
			"p_hispanic_persons", 
			"p_native_persons", 
			"p_asian_persons",
			"p_hawaiian_persons",
			"median_household_income",
			"median_income_whitehh",
			"median_income_blackhh",
			"median_income_hispanichh",
			"median_income_asianhh",
		],
		
		'label': "short_name",                                       # variable, short_name or full_name
	}
	
	Adaptive_Choropleth_Mapper_viz(param)
	Adaptive_Choropleth_Mapper_log()
	
	ended_datetime = datetime.now()
	elapsed = ended_datetime - started_datetime
	total_seconds = int(elapsed.total_seconds())
	hours, remainder = divmod(total_seconds,60*60)
	minutes, seconds = divmod(remainder,60)	
	print('GEOSNAP2ACM ended at %s %s    Elapsed %02d:%02d:%02d' % (ended_datetime.strftime('%Y-%m-%d'), ended_datetime.strftime('%H:%M:%S'), hours, minutes, seconds))
	
