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

cgitb.enable()


class reg(object):
    def __init__(self, cursor, row):
        for (attr, val) in zip((d[0] for d in cursor.description), row) :
            setattr(self, attr, val)


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

	
def LongitudinalNeighborhoodAnalysis(year, stateid, metroid, countyid, control):

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
	
	output = []
	header = ['tractid', 'state', 'county', 'tract', 'geojson']
	for fullcodeyear in codes:
		header.append(fullcodeyear)
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
	
	oCount = 0
	for row in results:
		tractid = row[0]
		state = row[1]
		county = row[2]
		tract = row[3]
		geojson = row[4]
		
		# read tract table, get state, county, tract, geojson
		#curs.execute("SELECT * From tract WHERE tractid = '" + tractid + "'")
		#results = curs.fetchall()
		#if len(results) != 0:
		#	row = results[0]
		#	r = reg(curs, row)
		#	state = r.state
		#	county = r.county
		#	tract = r.tract
		#	geojson = r.geojson
		
		record = [tractid, state, county, tract, geojson]
		for idx, v in enumerate(row):
			if (idx < 5): continue
			#val = v if v else -9999
			val = v if (v is not None) else -9999
			record.append(val)
			
		oCount += 1
		#if (oCount > 1): break
		output.append(record)
	
	#print("oCount: ", oCount)
	#print(output)
	
	'''
	for val in control['codes']:
		
		#  separate group and code (e.g. '1 nhwhtXX' 1 is group number and nhwhtXX is code )
		group = int(val.split()[0]);                       # 1
		code = val.split()[1];                             # nhwhtXX
		
		#  Check if the code is unqiue in codebook table. 
		curs.execute("SELECT * From codebook WHERE code = '" + code + "'")
		results = curs.fetchall()
		if len(results) != 1:
			#print "Ignore '{:s}' because codebook record count={:d}".format(val, len(results))
			continue
		# Even if the same code exisits in codebook table, skip if group code is different.
		row = results[0]
		r = reg(curs, row)
		if r.groupid != group:
			#print "Ignore '{:s}' because codebook group={:d}".format(val, r.groupid)
			continue
		
		# Utilize year and find numerator and demoninator and make the equation
		numerators = {'1970': r.year1970, '1980': r.year1980, '1990': r.year1990, '2000': r.year2000, '2010': r.year2010, '2012': r.year2012}
		denominators = {'1970': r.denominator1970, '1980': r.denominator1980, '1990': r.denominator1990, '2000': r.denominator2000, '2010': r.denominator2010, '2012': r.denominator2012}
		numerator = numerators[year].strip() if numerators[year] else ""
		denominator = denominators[year].strip() if denominators[year] else ""
		formula = '('+numerator+'/'+denominator+')'
		if denominator == "": formula = '('+numerator+')'
		shortname = r.description_short_name
		#print "{:8s}{:15s}{:30s}{:s}  ".format(year, val, formula, shortname)
		
		# Skip if both numerator and denominator do not exisit
		if (numerator == "" and denominator == ""):
			#print "Ignore '{:s}' because both of numerator and denominator are not found.".format(val)
			#print 'All columns of codebook =', row
			continue
		
		# Check if the selected column exisit in the table where the numerator exisits.
		if (numerator != ""):
			table1 = 'std_' + year + '_fullcount'              # std_1980_fullcount
			column1 = numerator                                # NHWHT80
			if (numerator.endswith('_s') or numerator.endswith('_S')): 
				table1 = 'std_' + year + '_sample'             # std_1980_sample
				if (year == "2012"): table1 = 'std_2010_sample'
				column1 = numerator[0:len(numerator)-2]        # take off surfix _s if it exisits
			column1 = column1.lower()
			curs.execute("SELECT * FROM " + table1 + " LIMIT 0")
			colnames = [desc[0] for desc in curs.description]
			if column1 not in colnames:
				#print "Ignore '{:s}' because numerator '{:s}' is not found in {:s}".format(val, column1, table1)
				#print 'All columns of ' + table1 + ' =', colnames
				continue

		#  Check if the selected column exisit in the table where the denominator exisits.
		if (denominator != ""):
			table2 = 'std_' + year + '_fullcount'              # std_1980_fullcount
			column2 = denominator                              # pop80
			if (denominator.endswith('_s') or denominator.endswith('_S')): 
				table2 = 'std_' + year + '_sample'             # std_1980_sample
				if (year == "2012"): table2 = 'std_2010_sample'
				column2 = denominator[0:len(denominator)-2]    # take off surfix _s if it exisits
			column2 = column2.lower()
			curs.execute("SELECT * FROM " + table2 + " LIMIT 0")
			colnames = [desc[0] for desc in curs.description]
			if column2 not in colnames:
				#print "Ignore '{:s}' because denominator '{:s}' is not found in {:s}".format(val, column2, table2)
				#print 'All columns of ' + table2 + ' =', colnames
				continue
		
		# Ready to register in the codes array
		codes.append([code, numerator, denominator, formula, shortname])
		#p = len(codes) - 1                                 # array position to be saved in the value of dictionary
		
		# read a numerator part of the table and save in the dictionary 
		if (numerator != ""):
			#curs.execute("SELECT trtid10, " + column1 + " FROM " + table1 + " ORDER BY trtid10")
			#curs.execute("SELECT trtid10, " + column1 + " FROM " + table1 + " WHERE trtid10 BETWEEN '" + stateid + "' AND '" + stateid + "999999999" + "' ORDER BY trtid10")
			curs.execute("SELECT trtid10, " + column1 + " FROM " + table1 + " WHERE " + condition + " ORDER BY trtid10")
			results = curs.fetchall()
			testCount = 0
			for row in results:
				testCount += 1
				#if (testCount > 1270): continue
				tractid = row[0]
				value1  = row[1] if row[1] else -9999      # Assign -9999 when the columns of numerators are none.
				#dict = {}        # key: trtid10, value: [[numerator, denominator], [numerator, denominator], ...]
				if tractid in dict:
					v = dict[tractid]    # [[numerator, denominator], [numerator, denominator], ...]
					for i in range(len(v), len(codes)-1): v.append([-9999, -9999])
					if len(v) == len(codes)-1: 
						v.append([value1, -9999])
					else:
						print "Abort '{:s}' because inter error at numerator '{:s}' in {:s}".format(val, column1, table1)
						print "All columns of row =", row
						print "codes =", codes
						print "dict['" + tractid + "'] =", v
						sys.exit("internal logic error!")
					dict[tractid] = v
				else:
					v = []
					for i in range(len(v), len(codes)-1): v.append([-9999, -9999])
					v.append([value1, -9999])
					dict[tractid] = v
		
		#  read a denominator part of the table and save in the dictionary 
		if (denominator != ""):
			#curs.execute("SELECT trtid10, " + column2 + " FROM " + table2 + " ORDER BY trtid10")
			#curs.execute("SELECT trtid10, " + column2 + " FROM " + table2 + " WHERE trtid10 BETWEEN '" + stateid + "' AND '" + stateid + "999999999" + "' ORDER BY trtid10")
			curs.execute("SELECT trtid10, " + column2 + " FROM " + table2 + " WHERE " + condition + " ORDER BY trtid10")
			results = curs.fetchall()
			testCount = 0
			for row in results:
				testCount += 1
				#if (testCount > 1270): continue
				tractid = row[0]
				value2  = row[1] if row[1] else -9999      # Assign -9999 when the columns of denominoator are none.
				#dict = {}        # key: trtid10, value: [[numerator, denominator], [numerator, denominator], ...]
				if tractid in dict:
					v = dict[tractid]    # [[numerator, denominator], [numerator, denominator], ...]
					for i in range(len(v), len(codes)): v.append([-9999, -9999])
					if len(v) == len(codes): 
						#v[len(codes)-1] = [v[len(codes)-1][0], value2]
						v[len(codes)-1][1] = value2
					else:
						print "Abort '{:s}' because inter error at numerator '{:s}' in {:s}".format(val, column2, table2)
						print "All columns of row =", row
						print "codes =", codes
						print "dict['" + tractid + "'] =", v
						sys.exit("internal logic error!")
					dict[tractid] = v
				else:
					v = []
					for i in range(len(v), len(codes)-1): v.append([-9999, -9999])
					v.append([-9999, value2])
					dict[tractid] = v
				
	
	output = []
	list = dict.items()
	list.sort(key=itemgetter(0))
	#print dict
	
	#outputfile = year + '_' + control['bitstring'] + '.csv'
	#print outputfile + '  file write started ...'
	#csvfile = open(outputfile, 'wb')
	#csvwriter = csv.writer(csvfile)
	
	header1 = ['tractid', 'state', 'county', 'tract', 'geojson']
	#header2 = ['', '', '', '']
	for v in codes:
		#code = v[0]
		code = v[0][0:len(v[0])-2] + year[2:]
		numerator = v[1]
		denominator = v[2]
		formula = v[3]
		shortname = v[4]
		#header1.extend(['', '', code + ' ' + formula])
		#header2.extend(['numerator', 'denominator', shortname])
		#header1.extend([code + ' ' + formula])
		header1.extend([code])
		#header2.extend([shortname])
	#csvwriter.writerow(header1)
	#csvwriter.writerow(header2)
	output.append(header1)
	#output.append(header2)
	
	oCount = 0
	
	#print codes
	for tuple in list:
		#print tuple
		tractid  = tuple[0]
		values = tuple[1]
		#print tractid, values
		
		state = ""
		county = ""
		tract = ""
		geojson = ""
		
		# Read tract table 
		curs.execute("SELECT * From tract WHERE tractid = '" + tractid + "'")
		results = curs.fetchall()
		if len(results) != 0:
			row = results[0]
			r = reg(curs, row)
			state = r.state
			county = r.county
			tract = r.tract
			geojson = r.geojson
		
		record = [tractid, state, county, tract, geojson]
		for idx, v in enumerate(values):
			numerator = v[0]
			denominator = v[1]
			result = numerator * 100.0 / denominator if denominator != 0 else -9999
			if numerator == -9999 or denominator == -9999: result = -9999
			if codes[idx][1] == "": result = -9999         # numerator in codes
			if codes[idx][2] == "": result = numerator     # denominator in codes
			#record.extend([numerator, denominator, result])
			record.extend([result])
		
		oCount += 1
		#csvwriter.writerow(record)
		output.append(record)
			
	#csvfile.close()
	'''
	
	conn.commit()
	curs.close()
	conn.close()
	
	return output


def getParameter(argv):
	year = '1970,1980,1990,2000,2010'
	possibleYear = year.split(',')
	inputfile = ''
	
	try:
		opts, args = getopt.getopt(argv, "hy:i:", ["year=", "inputfile="])
	except getopt.GetoptError:
		print("LongitudinalNeighborhoodAnalysis.py -y <year> -i <inputfile>")
		sys.exit(2)
	for opt, arg in opts:
		if opt == "-h":
			print("LongitudinalNeighborhoodAnalysis.py -y <year> -i <inputfile>")
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

# LongitudinalNeighborhoodAnalysis.py -y 1980 -i "C:\Users\Administrator\Documents\2018-01-30 LTDB setup\LongitudinalNeighborhoodAnalysis_SelectedVariableList.txt"

	#started_datetime = datetime.now()
	#dateYYMMDD = started_datetime.strftime('%Y%m%d')
	#timeHHMMSS = started_datetime.strftime('%H%M%S')
	#print 'LongitudinalNeighborhoodAnalysis start at %s %s' % (started_datetime.strftime('%Y-%m-%d'), started_datetime.strftime('%H:%M:%S'))
	
	# Get parameter from console
	parameter = getParameter(sys.argv[1:])
	year     = parameter['year']
	years    = parameter['years']
	#inputfile = parameter['inputfile']
	
	# Get parameter from client
	fields = cgi.FieldStorage()

	year = "1980"
	state = "06 CA"
	metro = "ALL"
	#metro = "31080"
	county = "ALL"
	codes = "1-01 nhwhtXX,1-14 a60blkXX,3-10 hincXX"
	statename = ""
	metroname = ""
	countyame = ""
	'''
	year = "1970"
	state = "01 AL"
	metro = "10700"
	county = "ALL"
	codes = "1-01 nhwhtXX,1-02 nhblkXX"
	statename = "ALABAMA"
	metroname = "Albertville"
	countyame = "All"
	'''
	if "year"  in fields: year  = fields['year'].value
	if "state"  in fields: state  = fields['state'].value
	if "metro"  in fields: metro  = fields['metro'].value
	if "county"  in fields: county  = fields['county'].value
	if "codes" in fields: codes = fields['codes'].value
	if "statename"  in fields: statename  = fields['statename'].value
	if "metroname"  in fields: metroname  = fields['metroname'].value
	if "countyame"  in fields: countyame  = fields['countyame'].value

	# Read input file and create bitstring for outputfileName and codes list
	#control = ReadInputFile(inputfile)
	#print control['bitstring']
	#print control['codes']
	
	# Parse input codes and create bitstring for outputfileName and codes list
	control = ParseInputCodes(years, codes)

	# Read codebook table and select
	#for year in years:
	#	LongitudinalNeighborhoodAnalysis(year, control)
	result = LongitudinalNeighborhoodAnalysis(year, state[0:2], metro, county, control)
	
	filename = year + '_' + state[3:5]
	if (metro != "ALL"): filename += '_' + metroname.split('-')[0].replace(' ', '-')
	if (county != "ALL"): filename += '_' + countyame.replace(' ', '-')
	filename += '_' + control['bitstring'] + '.csv'
	out_data = {'filename': filename, 'size': len(json.dumps(result)), 'result': result}
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
	#print 'LongitudinalNeighborhoodAnalysis ended at %s %s    Elapsed %02d:%02d:%02d' % (ended_datetime.strftime('%Y-%m-%d'), ended_datetime.strftime('%H:%M:%S'), hours, minutes, seconds)
