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
import INCS
import csv

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

	
def GetStatenameMetronameCountyname(stateid, metroid, countyid):
	statename = "All"
	metroname = "All"
	countyame = "All"
	
	conn = psycopg2.connect("host='localhost' dbname='LTDB' user='neighborhood' password='Tomas159'")
	curs = conn.cursor()

	if (stateid != "ALL"):
		curs.execute("SELECT state, statename FROM state WHERE stateid = '" + stateid + "'")
		results = curs.fetchall()
		#print(stateid, results)
		if (len(results) > 0): statename = results[0][1]
		
	if (stateid != "ALL" and metroid != "ALL"):
		curs.execute("SELECT state, mertoname FROM metro WHERE stateid = '" + stateid + "' AND metroid = '" + metroid + "'")
		results = curs.fetchall()
		#print(metroid, results)
		if (len(results) > 0): metroname = results[0][1]
		
	if (countyid != "ALL"):
		curs.execute("SELECT state, countyname FROM county WHERE countyid = '" + countyid + "'")
		results = curs.fetchall()
		#print(countyid, results)
		if (len(results) > 0): countyame = results[0][1]

	conn.commit()
	curs.close()
	conn.close()
	
	return statename, metroname, countyame	
	
	
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
	header = ['tractid', 'state', 'county', 'tract', 'geojson', 'INC']
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
	#print(df)
	#print('df: ', df.shape)
	
	df = df.apply(lambda x: (x - x.mean()) / x.std(ddof=0))    # ?
	#print(df)

	clusters = KMeans(n_clusters=nClusters).fit(df)
	dfk = pd.DataFrame({'tractid': df.index.astype(str), 'cluster': clusters.labels_ })
	dfk.set_index('tractid', inplace=True)
	#print(dfk)
	#print('dfk: ', dfk.shape)
		
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
	#print(works)

	workKeys = works.keys()
	yearData = [[-9999 for i in workKeys] for y in years]
	#print(workKeys)
	#print(yearData)
	for y, year in enumerate(years):
		for k, key in enumerate(workKeys):
			#print(y, k, key, works[key])
			yearData[y][k] = works[key][y]
	#print(yearData)
	
	incs = INCS.linc(yearData)
	#print("incs", incs)
	
	for k, key in enumerate(workKeys):
		workData = works[key]
		workData.insert(0, incs[k])
		#works[key] = workData
	#for k, key in enumerate(workKeys):
	#	print(works[key])

	oCount = 0
	for row in results:
		tractid = row[0]
		state = row[1]
		county = row[2]
		tract = row[3]
		geojson = row[4]
		#geojson = ''
		
		record = [tractid, state, county, tract, geojson]
		if (tractid in works):
			record.extend(works[tractid])
		else:
			record.extend([-9999 for y in range(len(years)+1)])

		oCount += 1
		#if (oCount > 1): break
		output.append(record)
	
	#print("oCount: ", oCount)
	#print(output)
	
	conn.commit()
	curs.close()
	conn.close()
	#print(output[1])
	return validCount, output


def KMeansbyAllMetro(nClusters, years, codestring, allcodestring, control):

	path = 'C:/inetpub/wwwroot/LNCE/cache/metro_' + \
		str(nClusters) + '_' + '_'.join(year for year in years) + '_' + control['bitstring']
	#if os.path.exists(path): shutil.rmtree(path)
	
	codes = []           # from control[fullcode, ...]
	stateDic = {}        # key: stateid,  value: {'state':  'statename':  'metroids': [metroid1, ....]}
	metroDic = {}        # key: metroid,  value: ('stateid':  'state':  'metroname':  'geojson':  'countyids': [...]}
	mCountyDic = {}      # key: countyid, value: [sIdx, eIdx]
	countyDic = {}       # key: countyid,  value: ('state':  'countyname': }
	resultArray = []     # [tractid, state, county, nhwht70 ....]

	conn = psycopg2.connect("host='localhost' dbname='LTDB' user='neighborhood' password='Tomas159'")
	curs = conn.cursor()

	curs.execute("SELECT stateid, state, statename FROM state ORDER BY stateid")
	results = curs.fetchall()
	for row in results:
		stateid   = row[0]
		state     = row[1]
		statename = row[2]
		stateDic[stateid] = {'state': state, 'statename': statename, 'metroids': []}
	#print(stateDic)
	
	#curs.execute("SELECT * FROM metro ORDER BY stateid, metroid")
	curs.execute("SELECT m.stateid, m.metroid, m.state, m.mertoname, j.geojson FROM metro AS m, metro_geojson AS j Where m.metroid = j.metroid ORDER BY m.stateid, m.metroid")
	results = curs.fetchall()
	for row in results:
		stateid   = row[0]
		metroid   = row[1]
		state     = row[2]
		metroname = row[3]
		geojson   = row[4]
		#if (geojson == None):
		#	print("geojson in metro_geojson table not exits", row)
		if (metroid not in metroDic):
			metroDic[metroid] = {'stateid': stateid, 'state': state, 'metroname': metroname, 'geojson': geojson, 'countyids': []}
		if (stateid in stateDic):
			value = stateDic[stateid]
			value['metroids'].append(metroid)
		#else:
		#	print("The stateid of the metro table not found in the state table", row)
		#	return
	#print(stateDic)
	#print(metroDic)
	
	curs.execute("SELECT DISTINCT geoid_msa, geoid10_county FROM metro_county ORDER BY geoid_msa, geoid10_county")
	results = curs.fetchall()
	for row in results:
		metroid   = row[0]
		countyid  = row[1]
		if (metroid in metroDic):
			value = metroDic[metroid]
			value['countyids'].append(countyid)
		#else:
		#	print("The metroid of the metro_county table not found in the metro table", row)
		#	return
		if (countyid not in mCountyDic):
			mCountyDic[countyid] = [999999, -999999]
		#else:
		#	print("The countyid of the metro_county table is Duplicate", row)
		#	return
	#print(metroDic)
	#print(mCountyDic)
	
	curs.execute("SELECT countyid, state, countyname FROM county ORDER BY countyid")
	results = curs.fetchall()
	for row in results:
		countyid   = row[0]
		state      = row[1]
		countyname = row[2]
		countyDic[countyid] = {'state': state, 'countyname': countyname}
	#print(countyDic)
	
	stateKeys  = sorted(stateDic)
	metroKeys  = sorted(metroDic)
	mCountyKeys = sorted(mCountyDic)
	countyKeys = sorted(countyDic)
	#print('stateKeys:',  len(stateKeys))                             #     52
	#print('metroKeys:',  len(metroKeys))                             #    929
	#print('mCountyKeys:', len(mCountyKeys))                          #  1,882
	#print('countyKeys:', len(countyKeys))                            #  3,221
	
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
	
	
	# in case of count of valid value
	if (allcodestring != ''):
		output = []
		header = ['code', 'total']
		for year in years:
			header.append(year)
		output.append(header)
		
		selectsql = ''
		#selectsql += 'SELECT * FROM result ORDER BY tractid LIMIT 1000'
		selectsql += 'SELECT * FROM result ORDER BY tractid'
		#print('selectsql: {:s}'.format(selectsql))
		curs.execute(selectsql)                                      # Elapsed 00:01:17
		results = curs.fetchall()
		
		cIdx = -1
		for row in results:
			tractid   = row[0]
			countyid  = row[0][0:5]
			#print(countyid)
			if (countyid in mCountyDic):
				value = mCountyDic[countyid]
				cIdx += 1
				if (value[0] > cIdx): value[0] = cIdx
				if (value[1] < cIdx): value[1] = cIdx
				resultArray.append(row)
		#print(0, resultArray[0])
		#print(1, resultArray[1])
		#print(2, resultArray[2])
		#print(len(resultArray)-2, resultArray[len(resultArray)-2])
		#print(len(resultArray)-1, resultArray[len(resultArray)-1])
		#print(mCountyDic)
		#print('resultArray:', len(resultArray))                      # 68,499 / 74,022
		
		#nResults = 0
		#for cdx, cKey in enumerate(mCountyKeys):
		#	if (cdx < 3 or cdx > len(mCountyKeys) - 3):
		#		print(cdx, cKey, mCountyDic[cKey])
		#	ft = mCountyDic[cKey]
		#	if (ft[0] > ft[1]): continue
		#	nResults += ft[1] - ft[0] + 1
		#print('nResults:', nResults)                                 # 68,499 / 74,022
		
		counts = [0 for i in range(len(columnsOfResult))]            # [3+codeYear]
		for mdx, mKey in enumerate(metroKeys):
			#if (metroDic[mKey]['stateid'] != '72'): continue
			countyids = metroDic[mKey]['countyids']
			for cdx, cKey in enumerate(countyids):
				ft = mCountyDic[cKey]
				if (ft[0] > ft[1]): continue
				for tdx in range(ft[0], ft[1]+1):
					row = resultArray[tdx]
					tractid = row[0]
					state   = row[1]
					county  = row[2]
					value   = row[3:]
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
		#print('counts:', counts)
							
		allcodes = allcodestring.split(',')

		summary = [[0 for y in years] for i in allcodes]             # [year][allcodes]
		for idx, codeyear in enumerate(columnsOfResult):
			if idx < 3: continue
			#print(codeyear, counts[idx])
			codeYear = DecodeCodeYear(codeyear)
			code = codeYear[0]
			year = codeYear[1]
			i = -1
			for jdx, value in enumerate(allcodes):
				#print('value:', value)
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
			record = [allcodes[i], len(resultArray)]
			for y, col in enumerate(row):
				#record.append(years[y]+': '+str(col*100/len(resultArray))+'%')
				record.append(col)
			#print(record)
			output.append(record)

		conn.commit()
		curs.close()
		conn.close()
		
		return output, []	
	
	
	
	
	
	#curs.execute("SELECT * FROM result ORDER BY tractid")            # 74,022
	selectsql = ''
	selectsql += 'SELECT tractid, ' + colList
	selectsql += ' FROM result'
	selectsql += ' ORDER BY tractid'
	curs.execute(selectsql)
	results = curs.fetchall()
	cIdx = -1
	for row in results:
		tractid   = row[0]
		countyid  = row[0][0:5]
		#print(countyid)
		if (countyid in mCountyDic):
			value = mCountyDic[countyid]
			cIdx += 1
			if (value[0] > cIdx): value[0] = cIdx
			if (value[1] < cIdx): value[1] = cIdx
			resultArray.append(row)
	#print(0, resultArray[0])
	#print(1, resultArray[1])
	#print(2, resultArray[2])
	#print(len(resultArray)-2, resultArray[len(resultArray)-2])
	#print(len(resultArray)-1, resultArray[len(resultArray)-1])
	#print(mCountyDic)
	#print('resultArray:', len(resultArray))                          # 68,499 / 74,022
	
	#nResults = 0
	#for cdx, cKey in enumerate(mCountyKeys):
	#	if (cdx < 3 or cdx > len(mCountyKeys) - 3):
	#		print(cdx, cKey, mCountyDic[cKey])
	#	ft = mCountyDic[cKey]
	#	if (ft[0] > ft[1]): continue
	#	nResults += ft[1] - ft[0] + 1
	#print('nResults:', nResults)                                     # 68,499 / 74,022

	
	# in case of KMeans result
	if (not os.path.exists(path)): os.mkdir(path)
	outputfileName = path + '/byTract.csv'
	csvOutputfile = open(outputfileName, 'wt', newline='')
	csvwriter = csv.writer(csvOutputfile)
	header = ['metroid', 'countyid', 'tractid', 'INC']
	header.extend(years)
	csvwriter.writerow(header)
	oCount = 0
	
	#for sdx, sKey in enumerate(stateKeys):                           # CALIFORNIA
	#	if (sKey != '72'): continue
	#	metroids = stateDic[sKey]['metroids']
	#	
	#	for mdx, mKey in enumerate(metroids):
	
	#metroDic = {}        # key: metroid,  value: ('stateid':  'state':  'metroname':  'geojson':  'countyids': [...]}
	for mdx, mKey in enumerate(metroKeys):
			#if (mKey != '10260' and mKey != '10380'): continue
			#if (mKey != '10260'): continue
			#if (metroDic[mKey]['stateid'] != '72'): continue
			countyids = metroDic[mKey]['countyids']
			
			nResults = 0
			data = np.array([])
			index = []
			columns = codestring.split(',')
			#print columns
			vCount = [[0 for y in years] for i in columns]  # [year][columns]
			
			for cdx, cKey in enumerate(countyids):
				ft = mCountyDic[cKey]
				if (ft[0] > ft[1]): continue
				for tdx in range(ft[0], ft[1]+1):
					nResults += 1
					row = resultArray[tdx]
					for ydx, year in enumerate(years):
						cols = np.array([])
						na_values = False
						for jdx, val in enumerate(row):
							if (jdx < 1): continue
							#print('%s: %d' % (codes[jdx-5], val))
							twoDigitYear = codes[jdx-1][-2:]
							code = codes[jdx-1][:len(codes[jdx-5])-2] + 'XX'
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
			
			#print("metorid:", mKey)
			#print("data:", data.shape)
			#print("index:", len(index))
			#print(vCount)
			validHeader = ['code','total']
			validHeader.extend(years)
			validCount = [validHeader]
			for vdx, col in enumerate(vCount):
				record = [columns[vdx], nResults]
				for cdx, col in enumerate(col):
					record.append(col)
				validCount.append(record)
			#print(validCount)
			
			try:
				df = pd.DataFrame(data, index=index, columns=columns)
			except ValueError:
				#print('ValueError in DataFrame.  metro: %s  %s  %s' % (mKey, metroDic[mKey]['state'], metroDic[mKey]['metroname']))
				continue
			#print(df)
			#print('df: ', df.shape)

			df = df.apply(lambda x: (x - x.mean()) / x.std(ddof=0))    # ?
			#print(df)

			try:
				clusters = KMeans(n_clusters=nClusters).fit(df)
			except ValueError:
				#print('ValueError in KMeans.  metro: %s  %s  %s' % (mKey, metroDic[mKey]['state'], metroDic[mKey]['metroname']))
				continue
			
			dfk = pd.DataFrame({'tractid': df.index.astype(str), 'cluster': clusters.labels_ })
			dfk.set_index('tractid', inplace=True)
			#print(dfk)
			#print('dfk: ', dfk.shape)

			works = {}   # key: tractid, value: [y0, y1, ...]
			#for cdx, cKey in enumerate(countyids):
			#	ft = mCountyDic[cKey]
			#	if (ft[0] > ft[1]): continue
			#	for tdx in range(ft[0], ft[1]+1):
			#		row = resultArray[tdx]
			#		tractid = row[0]
			#		record = [-9999 for y in years]
			#		works[tractid] = record
			#	
			#for idx, row in dfk.iterrows():
			#	#print(idx, row[0])
			#	year = idx[:4]
			#	tractid = idx[6:]
			#	#if tractid == "06001400100" : 
			#	#	print(year, tractid, row)
			#	if (tractid in works):
			#		record = works[tractid]
			#		y = years.index(year)
			#		record[y] = int(row[0])                        # type converstion from int32 to integer
			for idx, row in dfk.iterrows():
				year = idx[:4]
				tractid = idx[6:]
				if (tractid not in works):
					record = [-9999 for y in years]
					works[tractid] = record
				record = works[tractid]
				y = years.index(year)
				record[y] = int(row[0])                        # type converstion from int32 to integer
			#print("works:", len(works))
			#print(works)

			workKeys = works.keys()
			yearData = [[-9999 for i in workKeys] for y in years]
			#print(workKeys)
			#print(yearData)
			for y, year in enumerate(years):
				for k, key in enumerate(workKeys):
					#print(y, k, key, works[key])
					yearData[y][k] = works[key][y]
			#print("yearData:", len(yearData))
			#print(yearData)
			
			incs = INCS.linc(yearData)
			#print("incs", incs)
			
			for k, key in enumerate(workKeys):
				workData = works[key]
				workData.insert(0, incs[k])
				#works[key] = workData
			
			#print("works:", len(workKeys))
			#for k, key in enumerate(workKeys):
			#	print(key, works[key])

			output = []
			# metroDic  ->  key: metroid,  value: ('stateid': 'state': 'metroname': 'geojson': 'countyids': [...]}
			# countyDic ->  key: countyid,  value: ('state':  'countyname': }
			for cdx, cKey in enumerate(countyids):
				ft = mCountyDic[cKey]
				if (ft[0] > ft[1]): continue
				for tdx in range(ft[0], ft[1]+1):
					row = resultArray[tdx]
					tractid = row[0]
					record = [mKey, cKey, tractid]
					if (tractid in works and works[tractid][0] != -9999):
						record.extend(works[tractid])
					else:
						#record.extend([-9999 for y in years])
						continue
					output.append(record)

			for odx, record in enumerate(output):
				oCount += 1
				#if (oCount > 1): break
				csvwriter.writerow(record)
			
			nTract = 0
			incSUM = 0
			incAve = 0
			for odx, record in enumerate(output):
				nTract += 1
				incSUM += record[3]
			
			#if ('nTract' in metroDic[mKey]):
			#	print('metro %s  ave: %.2f  sum: %.2f  nTract: %d  %s  %s' % (mKey, metroDic[mKey]['incAve'], metroDic[mKey]['incSum'], metroDic[mKey]['nTract'], metroDic[mKey]['state'], metroDic[mKey]['metroname']))
			#	print('             ave: %.2f  sum: %.2f  nTract: %d  %s  %s' % ((incSUM / nTract if (nTract != 0) else -9999), incSUM, nTract, stateDic[sKey]['state'], metroDic[mKey]['metroname']))
			
			metroDic[mKey]['nTract'] = nTract
			metroDic[mKey]['incSum'] = incSUM
			metroDic[mKey]['incAve'] = incSUM / nTract if (nTract != 0) else -9999

			#print('metro %s  ave: %.2f  sum: %.2f  nTract: %d  %s  %s' % (mKey, metroDic[mKey]['incAve'], metroDic[mKey]['incSum'], metroDic[mKey]['nTract'], metroDic[mKey]['state'], metroDic[mKey]['metroname']))
	csvOutputfile.close()
	#print("oCount: ", oCount)
			
	outputfileName = path + '/byMetro' + '.csv'
	csvOutputfile = open(outputfileName, 'wt', newline='')
	csvwriter = csv.writer(csvOutputfile)
	header = ('metroid', 'INC ave', 'INC sum', 'nTract', 'state', 'metroname')
	csvwriter.writerow(header)
	# metroDic  ->  key: metroid,  value: ('stateid': 'state': 'metroname': 'geojson': 'countyids': [...]}
	for mdx, mKey in enumerate(metroKeys):
		if ('nTract' not in metroDic[mKey]): continue
		state     = metroDic[mKey]['state'];
		metroname = metroDic[mKey]['metroname'];
		nTract 	  = metroDic[mKey]['nTract']; 
		incSUM 	  = metroDic[mKey]['incSum']; 
		incAve 	  = metroDic[mKey]['incAve'];
		record = (mKey, incAve, incSUM, nTract, state, metroname)
		csvwriter.writerow(record)
	csvOutputfile.close()
	
	oCount = 0
	output = []
	#header = ['metorid', 'metroname', 'geojson', 'INC']
	header = ['metorid', 'state', 'metroname', '', 'geojson', 'INC']
	output.append(header)
	for mdx, mKey in enumerate(metroKeys):
		if ('nTract' not in metroDic[mKey]): continue
		stateid   = metroDic[mKey]['stateid'];
		state     = metroDic[mKey]['state'];
		metroname = metroDic[mKey]['metroname'];
		geojson   = metroDic[mKey]['geojson'];
		incAve 	  = metroDic[mKey]['incAve'];
		record = (mKey, stateid+' '+state, metroname, '', geojson, incAve)
		oCount += 1
		#if (oCount > 5): break
		output.append(record)
	
	#print("oCount: ", oCount)
	#print(output)
	
	
	conn.commit()
	curs.close()
	conn.close()
	#print(output[1])
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
	years = "1980,1990,2000,2010"
	sOpt = "metros"
	state = "06 CA"
	#metro = "ALL"
	metro = "31080"
	county = "ALL"
	#codes = "1-01 nhwhtXX,1-14 a60blkXX,3-10 hincXX"    # nhwhtXX, nhblkXX, hispXX, hincXX, mrentXX
	codes = "1-01 nhwhtXX,1-02 nhblkXX"
	#allcodestring = "1-01 nhwhtXX,1-14 a60blkXX,3-10 hincXX"
	#allcodestring = "1-01 nhwhtXX,1-02 nhblkXX,1-03 hispXX,1-04 ntvXX,1-05 asianXX,1-06 hawXX,1-07 indiaXX,1-08 chinaXX,1-09 filipXX,1-10 japanXX,1-11 koreaXX,1-12 vietXX,1-13 a15blkXX,1-14 a60blkXX,1-15 a15hspXX,1-16 a60hspXX,1-17 a15ntvXX,1-18 a60ntvXX,1-19 a15asnXX,1-20 a60asnXX,2-01 mexXX,2-02 cubanXX,2-03 prXX,2-04 ruancXX,2-05 itancXX,2-06 geancXX,2-07 irancXX,2-08 scancXX,2-09 fbXX,2-10 n10immXX,2-11 natXX,2-12 olangXX,2-13 lepXX,2-14 rufbXX,2-15 itfbXX,2-16 gefbXX,2-17 irfbXX,2-18 scfbXX,3-01 hsXX,3-02 colXX,3-03 unempXX,3-04 flabfXX,3-05 profXX,3-06 manufXX,3-07 sempXX,3-08 vetXX,3-09 disXX,3-10 hincXX,3-11 hincwXX,3-12 hincbXX,3-13 hinchXX,3-14 hincaXX,3-15 incpcXX,3-16 npovXX,3-17 n65povXX,3-18 nfmpovXX,3-19 nwpovXX,3-20 nbpovXX,3-21 nhpovXX,3-22 nnapovXX,3-23 napovXX,4-01 vacXX,4-02 ownXX,4-03 multiXX,4-04 mhmvalXX,4-05 mrentXX,4-06 h30oldXX,4-07 h10yrsXX,4-08 a18undXX,4-09 a60upXX,4-10 a75upXX,4-11 marXX,4-12 wdsXX,4-13 fhhXX"
	allcodestring = ""
	'''
	years = "1980,1990,2000,2010"
	sOpt = "metros"
	state = "01 AL"
	metro = "10700"
	county = "ALL"
	codes = "1-01 nhwhtXX,1-02 nhblkXX"
	allcodestring = "1-01 nhwhtXX,1-02 nhblkXX"
	allcodestring = ""
	'''
	if "nClusters"  in fields: nClusters  = fields['nClusters'].value
	if "years"  in fields: years  = fields['years'].value
	if "sOpt"  in fields: sOpt  = fields['sOpt'].value
	if "state"  in fields: state  = fields['state'].value
	if "metro"  in fields: metro  = fields['metro'].value
	if "county"  in fields: county  = fields['county'].value
	if "codes" in fields: codes = fields['codes'].value
	if "allcodestring" in fields: allcodestring = fields['allcodestring'].value
	
	# Convert nClusters to int
	nClusters = int(nClusters)

	# Convert years, string to array
	years = years.split(',')
	
	# Parse input codes and create bitstring for outputfileName and codes list
	control = ParseInputCodes(years, codes)
	#print(control)
	
	# Get statename, metroname, countyame
	statename, metroname, countyame = GetStatenameMetronameCountyname(state[0:2], metro, county)
	#print(state[0:2], metro, county)
	#print(statename, metroname, countyame)

	# Read codebook table and select
	#for year in years:
	#	KMeansbySelectedTractid(year, control)
	if (sOpt == 'selected'):
		counts, result = KMeansbySelectedTractid(nClusters, years, state[0:2], metro, county, codes, allcodestring, control)
		filename = '_'.join(years) + '_' + state[3:]
		if (metro != "ALL"): filename += '_' + metroname.split('-')[0].replace(' ', '-')
		if (county != "ALL"): filename += '_' + countyame.replace(' ', '-')
		filename += '_' + control['bitstring'] + '.js'
		out_data = {'filename': filename, 'size': len(json.dumps(result)), 'counts': counts, 'result': result}
		out_dump = json.dumps(out_data)
		
	if (sOpt == 'metros'):
		path = 'C:/inetpub/wwwroot/LNCE/cache/metro_'
		if (allcodestring != ''): path += '0' + '_' + '_'.join(year for year in years)
		else:          path += str(nClusters) + '_' + '_'.join(year for year in years) + '_' + control['bitstring']
		jsonfileName = path + '/byMetro' + '.json'
		if (os.path.isfile(jsonfileName)):
			f = open(jsonfileName, 'r')
			out_dump = f.read()
			f.close()
		else:
			counts, result = KMeansbyAllMetro(nClusters, years, codes, allcodestring, control)
			#filename = '_'.join(years) + '_' + state[3:]
			#if (metro != "ALL"): filename += '_' + metroname.split('-')[0].replace(' ', '-')
			#if (county != "ALL"): filename += '_' + countyame.replace(' ', '-')
			filename = '_'.join(years)
			filename += '_' + control['bitstring'] + '.js'
			out_data = {'filename': filename, 'size': len(json.dumps(result)), 'counts': counts, 'result': result}
			out_dump = json.dumps(out_data)
			if (not os.path.exists(path)): os.mkdir(path)
			f = open(jsonfileName, 'w')
			f.write(out_dump)
			f.close()
	
	time.sleep(0)

	#f = open(filename, 'w')
	#f.write('var GEO_VARIABLES =\n')
	#f.write('[\n')
	#row = result[0]    # Title
	#r = '  ['
	#r += '"' + row[0] + '", '
	#for col in row[5:]:
	#	r += '"' + str(col) + '", '
	#r += '],\n'
	#f.write(r)
	#for row in result[1:]:
	#	r = '  ['
	#	r += '"' + row[0] + '", '
	#	for col in row[5:]:
	#		#r += str(col) + ','
	#		#print(type(col), col)
	#		if (type(col) == int): r += str(col) + ', '
	#		else: r += '{:.2f}'.format(col) + ', '
	#	r += '],\n'
	#	f.write(r)
	#f.write(']\n')
	#f.close()
	
	print("Content-Type: text/html\n")
	print(out_dump)

	#            0, 1, 2, 3, 4, 5, 6, 7, 8, 9
	#labels_0 = [1, 1, 1, 1, 2, 2, 3, 3, 4, 4] 
	#labels_1 = [1, 1, 1, 1, 1, 2, 3, 3, 3, 4]
	#print("res = ", INCS.linc([labels_0, labels_1]))
	
	#for row in result:
	#	print(row)
	
	#ended_datetime = datetime.now()
	#elapsed = ended_datetime - started_datetime
	#total_seconds = int(elapsed.total_seconds())
	#hours, remainder = divmod(total_seconds,60*60)
	#minutes, seconds = divmod(remainder,60)	
	#print 'KMeansbySelectedTractid ended at %s %s    Elapsed %02d:%02d:%02d' % (ended_datetime.strftime('%Y-%m-%d'), ended_datetime.strftime('%H:%M:%S'), hours, minutes, seconds)
