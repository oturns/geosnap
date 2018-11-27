# -*- coding: utf-8 -*-
import sys, getopt
#import csv
import cgitb, cgi, json, sys, re
import json
#import subprocess
import os
import time
import datetime
from datetime import datetime
from datetime import timedelta
#from pytz import timezone
#import pytz
#import math
from operator import itemgetter, attrgetter
#import re
import psycopg2
import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
import math

cgitb.enable()


class reg(object):
    def __init__(self, cursor, row):
        for (attr, val) in zip((d[0] for d in cursor.description), row) :
            setattr(self, attr, val)

def default(o):
    if isinstance(o, np.int64): return int(o)
    #return o
    #raise TypeError
		
def DecodeCodeYear(codeYear):
	twoDigitYear = codeYear[len(codeYear)-2:]
	year = ''
	if (twoDigitYear == '70'): year = '1970'
	if (twoDigitYear == '80'): year = '1980'
	if (twoDigitYear == '90'): year = '1990'
	if (twoDigitYear == '00'): year = '2000'
	if (twoDigitYear == '10'): year = '2010'
	code = codeYear[0:len(codeYear)-2] + 'XX'
	return code, year


def ParseInputCodes(years, params):

	#years = ['1970', '1980', '1990', '2000', '2010']
	#params = "1-01 nhwhtXX,1-14 a60blkXX,3-10 hincXX"
	
	result = {'bitstring': None, 'codes': []}
	values = params.split(',')
	#print(years)
	for year in years:
		for value in values:
			if (len(value) == 0): continue
			#groupid = value[0:1]
			#seqnumber = int(value[2:4])
			#code = value[5:]
			codeyear = value[0:len(value)-2] + year[2:]
			result['codes'].append(codeyear)
	
	bitmap = [0, 0, 0, 0]
	for value in values:
		if (len(value) == 0): continue
		groupid = value[0:1]
		seqnumber = int(value[2:4])
		code = value[5:]
		idx = int(groupid) - 1
		bitmap[idx] = bitmap[idx] | 2 ** (int(seqnumber) - 1)
	
	group1 = format(bitmap[0], 'x')
	group2 = format(bitmap[1], 'x')
	group3 = format(bitmap[2], 'x')
	group4 = format(bitmap[3], 'x')
	if group1 == '0': group1 = ''
	if group2 == '0': group2 = ''
	if group3 == '0': group3 = ''
	if group4 == '0': group4 = ''
	result['bitstring'] = 'h' + group1 + 'h' + group2 + 'h' + group3 + 'h' + group4
	
	#print result
	return result

	
def KMeansbySelectedTractid(nClusters, years, stateid, metroid, countyid, codestring, allcodestring, control):

	#codes = []      # from control[[code, numerator, denominator, formula, shortname], ...]
	codes = []       # from control[fullcode, ...]
	#dict = {}        # key: trtid10, value: [[numerator, denominator], [numerator, denominator], ...]
	
	conn = psycopg2.connect("host='localhost' dbname='LTDB' user='neighborhood' password='Tomas159'")
	curs = conn.cursor()

	curs.execute("SELECT * From result LIMIT 0")
	columnsOfResult = [desc[0] for desc in curs.description]
	#print(columnsOfResult)
	
	# set column list for query from control['codes'] in the result columns
	colList = ''
	for fullcode in control['codes']:
		# separate group and code (e.g. '1 nhwhtXX' 1 is group number and nhwhtXX is code )
		prefix = fullcode.split()[0];                      # '1-01'
		codeyear = fullcode.split()[1];                    # 'nhwhtYY'
		if codeyear in columnsOfResult:
			colList += codeyear + ', '
			#codes.append([fullcode, numerator, denominator, formula, shortname])
			codes.append(prefix + ' ' + codeyear)          # '1-01 nhwhtYY'
		#else:
		#	#error set and return
		#	output = []
		#	conn.commit()
		#	curs.close()
		#	conn.close()
		#	return output
			
	if (len(colList) >= 2): colList = colList[0:len(colList)-2]
	#print("colList: ", colList)
	
	# set condition string of query using metroid, countyid
	condition = ''
	if (countyid != "ALL"):
		condition = "substring(r.tractid,1,5) = '" + countyid + "'"
	else:
		if (metroid == "ALL"):
			condition = "substring(r.tractid,1,2) = '" + stateid + "'"
		else:
			# get geoid10_county from metro_county table by stateid || metroid
			curs.execute("SELECT geoid10_county AS countyid FROM metro_county WHERE states_msa_code = '" + stateid + "' AND geoid_msa = '" + metroid + "'")
			results = curs.fetchall()
			for row in results:
				geoid10_county = row[0]
				condition += "substring(r.tractid,1,5) = '" + geoid10_county + "' OR "
			if (len(condition) > 4): condition = condition[0:len(condition)-4]
	if (len(condition) == 0): condition = "substring(r.tractid,1,2) = '" + stateid + "'"
	#print('condition: '+condition)


	# in case of count of valid value
	if (allcodestring != ''):
		output = []
		header = ['code', 'total']
		for year in years:
			header.append(year)
		output.append(header)
		
		selectsql = ''
		selectsql += 'SELECT * FROM result AS r'
		selectsql += ' WHERE (' + condition + ')'
		#selectsql += ' ORDER BY r.tractid'
		#print('selectsql: {:s}'.format(selectsql))
		curs.execute(selectsql)
		results = curs.fetchall()
		#print(len(results))
		#print(results[0])
		#print(results[1])
		
		counts = [0 for i in range(len(columnsOfResult))]    # [3+codeYear]
		for row in results:
			tractid = row[0]
			state = row[1]
			county = row[2]
			value = row[3:]
			for idx, codeyear in enumerate(columnsOfResult):
				if idx < 3: continue
				#if (row[idx] and row[idx] != -9999):
				val = row[idx]
				if (val is None or math.isnan(val) or val == -999 or val == -9999): na_values = True
					#	codeYear = DecodeCodeYear(codeyear)
					#	code = codeYear[0]
					#	year = codeYear[1]
					#	y = years.index(year)
				else:
					counts[idx] += 1
		
		allcodes = allcodestring.split(',')
		
		summary = [[0 for y in years] for i in allcodes]    # [year][allcodes]
		for idx, codeyear in enumerate(columnsOfResult):
			if idx < 3: continue
			#print(codeyear, counts[idx])
			codeYear = DecodeCodeYear(codeyear)
			code = codeYear[0]
			year = codeYear[1]
			i = -1
			for jdx, value in enumerate(allcodes):	
				if (value.split()[1] == code):
					#print(value, code)
					i = jdx
					break
			if (i == -1): continue
			y = -1
			for ydx, value in enumerate(years):
				if (value == year):
					y = ydx
					break
			if (y == -1): continue
			summary[i][y] += counts[idx]
		
		#print(summary)
		for i, row in enumerate(summary):
			record = [allcodes[i], len(results)]
			for y, col in enumerate(row):
				#record.append(years[y]+': '+str(col*100/len(results))+'%')
				record.append(col)
			#print(record)
			output.append(record)
		
		conn.commit()
		curs.close()
		conn.close()
	
		return output, []


	# in case of KMeans result
	output = []
	header = ['tractid', 'state', 'county', 'tract', 'geojson']
	header.extend(years)
	#for fullcodeyear in codes:
	#	header.append(fullcodeyear)
	#print('header: ', header)
	output.append(header)
	
	selectsql = ''
	selectsql += 'SELECT t.tractid, t.state, t.county, t.tract, t.geojson, ' + colList
	selectsql += ' FROM result AS r, tract AS t'
	selectsql += ' WHERE (' + condition + ') AND r.tractid = t.tractid'
	selectsql += ' ORDER BY t.tractid'
	#print('selectsql: {:s}'.format(selectsql))
	curs.execute(selectsql)
	results = curs.fetchall()
	
	data = np.array([])
	index = []
	columns = codestring.split(',')
	#print columns
	vCount = [[0 for y in years] for i in columns]  # [year][columns]
	for ydx, year in enumerate(years):
		idx = -1
		for row in results:
			idx += 1
			cols = np.array([])
			na_values = False
			for jdx, val in enumerate(row):
				if (jdx < 5): continue
				#print('%s: %d' % (codes[jdx-5], val))
				twoDigitYear = codes[jdx-5][-2:]
				code = codes[jdx-5][:len(codes[jdx-5])-2] + 'XX'
				#print('%s: %d' % (codes[jdx-5]+" "+twoDigitYear, val))
				if (year[-2:] != twoDigitYear): continue
				cols = np.append(cols, val)
				if (val is None or math.isnan(val) or val == -999 or val == -9999): na_values = True
				else:
					try:
						c = columns.index(code)
						vCount[c] [ydx] += 1
					except ValueError:
						#print code, columns
						c = 0    # dummy
				#print jdx, val, type(val)
				#print('%s: %d' % (jdx, val))
			if (len(cols) != len(columns)): na_values = True
			if (na_values): continue
			index.append(year+'__'+row[0])
			if (data.size == 0): data = np.array([cols])
			else: data = np.vstack([data, cols])
	#print vCount
	validHeader = ['code','total']
	validHeader.extend(years)
	validCount = [validHeader]
	for vdx, col in enumerate(vCount):
		record = [columns[vdx], len(results)]
		for cdx, col in enumerate(col):
			record.append(col)
		validCount.append(record)
	#print validCount
	
	df = pd.DataFrame(data, index=index, columns=columns)
	#print df
	#print 'df: ', df.shape
	
	df = df.apply(lambda x: (x - x.mean()) / x.std(ddof=0))    # ?
	#print df

	clusters = KMeans(n_clusters=nClusters).fit(df)
	dfk = pd.DataFrame({'tractid': df.index.astype(str), 'cluster': clusters.labels_ })
	dfk.set_index('tractid', inplace=True)
	#print dfk
	#print 'dfk: ', dfk.shape
		
	works = {}   # key: tractid, value: [y0, y1, ...]
	for row in results:
		tractid = row[0]
		record = [-9999 for y in years]
		works[tractid] = record
		
	for idx, row in dfk.iterrows():
		#print(idx, row[0])
		year = idx[:4]
		tractid = idx[6:]
		#if tractid == "06001400100" : 
		#	print(year, tractid, row)
		if (tractid in works):
			record = works[tractid]
			y = years.index(year)
			record[y] = int(row[0])                        # type converstion from int32 to integer
	#print works
	
	oCount = 0
	for row in results:
		tractid = row[0]
		state = row[1]
		county = row[2]
		tract = row[3]
		geojson = row[4]
		
		record = [tractid, state, county, tract, geojson]
		if (tractid in works):
			record.extend(works[tractid])
		else:
			record.extend([-9999 for y in years])

		oCount += 1
		#if (oCount > 1): break
		output.append(record)
	
	#print("oCount: ", oCount)
	#print(output)
	
	conn.commit()
	curs.close()
	conn.close()
	print(output[1])
	return validCount, output


def getParameter(argv):
	year = '1970,1980,1990,2000,2010'
	possibleYear = year.split(',')
	inputfile = ''
	
	try:
		opts, args = getopt.getopt(argv, "hy:i:", ["year=", "inputfile="])
	except getopt.GetoptError:
		print("KMeansbySelectedTractid.py -y <year> -i <inputfile>")
		sys.exit(2)
	for opt, arg in opts:
		if opt == "-h":
			print("KMeansbySelectedTractid.py -y <year> -i <inputfile>")
			sys.exit()
		elif opt in ("-y", "--year"):
			year = arg
		elif opt in ("-i", "--inputfile"):
			inputfile = arg

	#print "year       is : ", year
	#print "Input file is : ", inputfile
	
	years = year.split(',')
	for var in years:
		if var not in possibleYear:
			print("Impossible year found in --year parameter.")
			sys.exit("year parameter error!")
	
	return {'year': year, 'years': years, 'inputfile': inputfile}
    
            
if __name__ == '__main__':

# KMeansbySelectedTractid.py -y 1980 -i "C:\Users\Administrator\Documents\2018-01-30 LTDB setup\LongitudinalNeighborhoodAnalysis_SelectedVariableList.txt"

	#started_datetime = datetime.now()
	#dateYYMMDD = started_datetime.strftime('%Y%m%d')
	#timeHHMMSS = started_datetime.strftime('%H%M%S')
	#print 'KMeansbySelectedTractid start at %s %s' % (started_datetime.strftime('%Y-%m-%d'), started_datetime.strftime('%H:%M:%S'))
	
	# Get parameter from console
	parameter = getParameter(sys.argv[1:])
	year     = parameter['year']
	years    = parameter['years']
	#inputfile = parameter['inputfile']
	
	# Get parameter from client
	fields = cgi.FieldStorage()

	nClusters = "8"
	years = "1970,1980,1990,2000,2010"
	state = "06 CA"
	metro = "ALL"
	#metro = "31080"
	county = "ALL"
	codes = "1-01 nhwhtXX,1-14 a60blkXX,3-10 hincXX"    # nhwhtXX, nhblkXX, hispXX, hincXX, mrentXX
	allcodestring = "1-01 nhwhtXX,1-14 a60blkXX,3-10 hincXX"
	allcodestring = ""
	statename = ""
	metroname = ""
	countyame = ""
	'''
	years = "1980,1990,2000,2010"
	state = "01 AL"
	metro = "10700"
	county = "ALL"
	codes = "1-01 nhwhtXX,1-02 nhblkXX"
	allcodestring = "1-01 nhwhtXX,1-02 nhblkXX"
	#allcodestring = ""
	statename = "ALABAMA"
	metroname = "Albertville"
	countyame = "All"
	'''
	if "nClusters"  in fields: nClusters  = fields['nClusters'].value
	if "years"  in fields: years  = fields['years'].value
	if "state"  in fields: state  = fields['state'].value
	if "metro"  in fields: metro  = fields['metro'].value
	if "county"  in fields: county  = fields['county'].value
	if "codes" in fields: codes = fields['codes'].value
	if "allcodestring" in fields: allcodestring = fields['allcodestring'].value
	if "statename"  in fields: statename  = fields['statename'].value
	if "metroname"  in fields: metroname  = fields['metroname'].value
	if "countyame"  in fields: countyame  = fields['countyame'].value
	
	# Convert nClusters to int
	nClusters = int(nClusters)

	# Convert years, string to array
	years = years.split(',')
	
	# Parse input codes and create bitstring for outputfileName and codes list
	control = ParseInputCodes(years, codes)
	#print(control)

	# Read codebook table and select
	#for year in years:
	#	KMeansbySelectedTractid(year, control)
	counts, result = KMeansbySelectedTractid(nClusters, years, state[0:2], metro, county, codes, allcodestring, control)
	
	filename = year + '_' + state[3:5]
	if (metro != "ALL"): filename += '_' + metroname.split('-')[0].replace(' ', '-')
	if (county != "ALL"): filename += '_' + countyame.replace(' ', '-')
	filename += '_' + control['bitstring'] + '.csv'
	out_data = {'filename': filename, 'size': len(json.dumps(result)), 'counts': counts, 'result': result}
	#out_data = {'filename': filename+'__'+year+'__'+state+'__'+metro+'__'+county+'__'+codes, 'result': result}
	#out_data = {'filename': filename, 'result': ''}
	time.sleep(0)
	print("Content-Type: text/html\n")
	print(json.dumps(out_data))

	#ended_datetime = datetime.now()
	#elapsed = ended_datetime - started_datetime
	#total_seconds = int(elapsed.total_seconds())
	#hours, remainder = divmod(total_seconds,60*60)
	#minutes, seconds = divmod(remainder,60)	
	#print 'KMeansbySelectedTractid ended at %s %s    Elapsed %02d:%02d:%02d' % (ended_datetime.strftime('%Y-%m-%d'), ended_datetime.strftime('%H:%M:%S'), hours, minutes, seconds)
