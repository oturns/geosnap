# -*- coding: utf-8 -*-
import sys, getopt
import csv
import json
#import subprocess
import os
import datetime
from datetime import datetime
from datetime import timedelta
#from pytz import timezone
#import pytz
#import math
from operator import itemgetter, attrgetter
#import re
import psycopg2

class reg(object):
    def __init__(self, cursor, row):
        for (attr, val) in zip((d[0] for d in cursor.description), row) :
            setattr(self, attr, val)

# csv.DictReader has limit of reading csv, max 16,601,794 records
# this program not use csv.DictReader, but use csv.reader


def ReadInputFile(inputfile):
	result = {'bitstring': None, 'codes': [], 'codepositions': {}}
	bitmap = [0, 0, 0, 0]
	
	conn = psycopg2.connect("host='localhost' dbname='LTDB' user='neighborhood' password='Tomas159'")
	curs = conn.cursor()

	curs.execute("SELECT * From codebook LIMIT 0")
	colnames = [desc[0] for desc in curs.description]
	
	curs.execute("SELECT * From codebook ORDER BY serial")
	#print colnames
	results = curs.fetchall()
	count = [0, 0, 0, 0]        # for 4 groups
	for row in results:
		r = reg(curs, row)
		if r.web_system != 1: continue
		count[r.groupid - 1] += 1
		result['codepositions'][str(r.groupid)+' '+r.code] = count[r.groupid - 1]
		
	conn.commit()
	curs.close()
	conn.close()
	#print result['codepositions']
	
	f = open(inputfile, 'r')
	lines = f.readlines()
	for line in lines:
		if line.startswith('//'): continue        # bypass a comment line
		cols = line.split()
		selected = cols[0]
		groupid = cols[1][0:1]
		code = cols[2]
		if selected != '1': continue
		seqnumber = result['codepositions'][groupid+' '+code] if result['codepositions'][groupid+' '+code] else 32
		#print selected, groupid, seqnumber, code
		result['codes'].append(groupid+' '+code)
		idx = int(groupid) - 1
		bitmap[idx] = bitmap[idx] | 2 ** (int(seqnumber) - 1)
	f.close()
	
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

	
def LongitudinalNeighborhoodAnalysis(year, control):

	codes = []       # from control[[code, numerator, denominator, formula, shortname], ...]
	dict = {}        # key: trtid10, value: [[numerator, denominator], [numerator, denominator], ...]
	
	conn = psycopg2.connect("host='localhost' dbname='LTDB' user='neighborhood' password='Tomas159'")
	curs = conn.cursor()

	curs.execute("SELECT * From codebook LIMIT 0")
	colnames = [desc[0] for desc in curs.description]
	#print colnames
	
	for val in control['codes']:
		
		# val 의 값 '1 nhwhtXX' 에서 group 과 code 를 각각 분리한다.
		group = int(val.split()[0]);                       # 1
		code = val.split()[1];                             # nhwhtXX
		
		# codebook table 에 딱 하나만 존재하는지 확인한다.
		curs.execute("SELECT * From codebook WHERE code = '" + code + "'")
		results = curs.fetchall()
		if len(results) != 1:
			print "Ignore '{:s}' because codebook record count={:d}".format(val, len(results))
			continue
		# codebook table 에 존재 하더라도, 그룹 코드가 다르면 skip
		row = results[0]
		r = reg(curs, row)
		if r.groupid != group:
			print "Ignore '{:s}' because codebook group={:d}".format(val, r.groupid)
			continue
		
		# year 를 이용하여 분자, 분모를 찾아내고 공식을 만든다.
		numerators = {'1970': r.year1970, '1980': r.year1980, '1990': r.year1990, '2000': r.year2000, '2010': r.year2010, '2012': r.year2012}
		denominators = {'1970': r.denominator1970, '1980': r.denominator1980, '1990': r.denominator1990, '2000': r.denominator2000, '2010': r.denominator2010, '2012': r.denominator2012}
		numerator = numerators[year].strip() if numerators[year] else ""
		denominator = denominators[year].strip() if denominators[year] else ""
		formula = '('+numerator+'/'+denominator+')'
		if denominator == "": formula = '('+numerator+')'
		shortname = r.description_short_name
		print "{:8s}{:15s}{:30s}{:s}  ".format(year, val, formula, shortname)
		
		# 분자, 분모 모두 없는 경우는 여기서 미리 제낀다.
		if (numerator == "" and denominator == ""):
			#print "Ignore '{:s}' because both of numerator and denominator are not found.".format(val)
			#print 'All columns of codebook =', row
			continue
		
		# 분자가 있다고 지정된 table 에 지정한 column 이 있는지 확인한다.
		if (numerator != ""):
			table1 = 'std_' + year + '_fullcount'              # std_1980_fullcount
			column1 = numerator                                # NHWHT80
			if (numerator.endswith('_s') or numerator.endswith('_S')): 
				table1 = 'std_' + year + '_sample'             # std_1980_sample
				if (year == "2012"): table1 = 'std_2010_sample'
				column1 = numerator[0:len(numerator)-2]        # surfix _s 가 있으면 떼어낸다.
			column1 = column1.lower()
			curs.execute("SELECT * From " + table1 + " LIMIT 0")
			colnames = [desc[0] for desc in curs.description]
			if column1 not in colnames:
				print "Ignore '{:s}' because numerator '{:s}' is not found in {:s}".format(val, column1, table1)
				print 'All columns of ' + table1 + ' =', colnames
				continue

		# 분모가 있다고 지정된 table 에 지정한 column 이 있는지 확인한다.
		if (denominator != ""):
			table2 = 'std_' + year + '_fullcount'              # std_1980_fullcount
			column2 = denominator                              # pop80
			if (denominator.endswith('_s') or denominator.endswith('_S')): 
				table2 = 'std_' + year + '_sample'             # std_1980_sample
				if (year == "2012"): table2 = 'std_2010_sample'
				column2 = denominator[0:len(denominator)-2]    # surfix _s 가 있으면 떼어낸다.
			column2 = column2.lower()
			curs.execute("SELECT * From " + table2 + " LIMIT 0")
			colnames = [desc[0] for desc in curs.description]
			if column2 not in colnames:
				print "Ignore '{:s}' because denominator '{:s}' is not found in {:s}".format(val, column2, table2)
				print 'All columns of ' + table2 + ' =', colnames
				continue
		
		# 준비가 다 되었다. 이제 codes array 에 등록을 한다.
		codes.append([code, numerator, denominator, formula, shortname])
		#p = len(codes) - 1                                 # dict 의 value 안에 들어 갈 array position
		
		# 분자 부분의 table 을 읽어서 dict 에 저장한다.
		if (numerator != ""):
			curs.execute("SELECT trtid10, " + column1 + " From " + table1 + " ORDER BY trtid10")
			results = curs.fetchall()
			testCount = 0
			for row in results:
				testCount += 1
				#if (testCount > 5): continue
				tractid = row[0]
				value1  = row[1] if row[1] else -9999      # 분자 column 이 None 의 경우는 -9999 를 넣는다.
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
		
		# 분모 부분의 table 을 읽어서 dict 에 저장한다.
		if (denominator != ""):
			curs.execute("SELECT trtid10, " + column2 + " From " + table2 + " ORDER BY trtid10")
			results = curs.fetchall()
			testCount = 0
			for row in results:
				testCount += 1
				#if (testCount > 5): continue
				tractid = row[0]
				value2  = row[1] if row[1] else -9999      # 분모 column 이 None 의 경우는 -9999 를 넣는다.
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
				

	list = dict.items()
	list.sort(key=itemgetter(0))
	#print dict
	
	outputfile = year + '_' + control['bitstring'] + '.csv'
	print outputfile + '  file write started ...'
	csvfile = open(outputfile, 'wb')
	csvwriter = csv.writer(csvfile)
	
	header1 = ['tractid', 'state', 'county', 'tract']
	header2 = ['', '', '', '']
	for v in codes:
		#code = v[0]
		code = v[0][0:len(v[0])-2] + year[2:]
		numerator = v[1]
		denominator = v[2]
		formula = v[3]
		shortname = v[4]
		#header1.extend(['', '', code + ' ' + formula])
		#header2.extend(['numerator', 'denominator', shortname])
		header1.extend([code + ' ' + formula])
		header2.extend([shortname])
	csvwriter.writerow(header1)
	csvwriter.writerow(header2)
	
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
		
		# tract table 을 읽는다.
		curs.execute("SELECT * From tract WHERE tractid = '" + tractid + "'")
		results = curs.fetchall()
		if len(results) != 0:
			row = results[0]
			r = reg(curs, row)
			state = r.state
			county = r.county
			tract = r.tract
		
		record = [tractid, state, county, tract]
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
		csvwriter.writerow(record)
			
	csvfile.close()

	conn.commit()
	curs.close()
	conn.close()


def Cleansing_CSV(inputfile, outputfile):

	csvfile = open(outputfile, 'wb')
	csvwriter = csv.writer(csvfile)
	iCount = 0
	oCount = 0
	with open(inputfile, 'rb') as csvInputfile:
		csvreader = csv.reader(x.replace('\0','') for x in csvInputfile)
		headers = csvreader.next()
		csvwriter.writerow(headers)
		for row in csvreader:
			iCount += 1
			cols = row
			for idx, val in enumerate(cols):
				if idx < 5: continue
				if val == " " : row[idx] = ""
			
			oCount += 1
			csvwriter.writerow(row)
			
	csvInputfile.close()
	csvfile.close()
	
	print "Input  Document = %d,    Output Document = %d" % (iCount, oCount)


def Checking_codebook():

	group = 1
	year = '1980'

	conn = psycopg2.connect("host='localhost' dbname='LTDB' user='neighborhood' password='Tomas159'")
	curs = conn.cursor()

	curs.execute("SELECT * From codebook LIMIT 0")
	colnames = [desc[0] for desc in curs.description]
	
	curs.execute("SELECT * From codebook")
	print colnames
	results = curs.fetchall()
	count = 0
	for row in results:
		r = reg(curs, row)
		if r.groupid != group: continue
		if r.web_system != 1: continue
		count += 1
		code = r.code[0:len(r.code)-2] + year[2:]
		numerators = {'1970': r.year1970, '1980': r.year1980, '1990': r.year1990, '2000': r.year2000, '2010': r.year2010, '2012': r.year2012}
		denominators = {'1970': r.denominator1970, '1980': r.denominator1980, '1990': r.denominator1990, '2000': r.denominator2000, '2010': r.denominator2010, '2012': r.denominator2012}
		numerator = numerators[year].strip() if numerators[year] else ""
		denominator = denominators[year].strip() if denominators[year] else ""
		print "{:2d}  {:10s}    {:30s}    {:s}".format(count, code, '('+numerator+'/'+denominator+')', r.description_short_name)
	
	conn.commit()
	curs.close()
	conn.close()

	
def getParameter(argv):
	year = '1970,1980,1990,2000,2010,2012'
	possibleYear = year.split(',')
	inputfile = ''
	
	try:
		opts, args = getopt.getopt(argv, "hy:i:", ["year=", "inputfile="])
	except getopt.GetoptError:
		print "LongitudinalNeighborhoodAnalysis.py -y <year> -i <inputfile>"
		sys.exit(2)
	for opt, arg in opts:
		if opt == "-h":
			print "LongitudinalNeighborhoodAnalysis.py -y <year> -i <inputfile>"
			sys.exit()
		elif opt in ("-y", "--year"):
			year = arg
		elif opt in ("-i", "--inputfile"):
			inputfile = arg

	print "year       is : ", year
	print "Input file is : ", inputfile
	
	years = year.split(',')
	for var in years:
		if var not in possibleYear:
			print "Impossible year found in --year parameter."
			sys.exit("year parameter error!")
	
	return {'year': years, 'inputfile': inputfile}
    
            
if __name__ == '__main__':

# LongitudinalNeighborhoodAnalysis.py -y 1980 -i "C:\Users\Administrator\Documents\2018-01-30 LTDB setup\LongitudinalNeighborhoodAnalysis_SelectedVariableList.txt"

	started_datetime = datetime.now()
	dateYYMMDD = started_datetime.strftime('%Y%m%d')
	timeHHMMSS = started_datetime.strftime('%H%M%S')
	print 'LongitudinalNeighborhoodAnalysis start at %s %s' % (started_datetime.strftime('%Y-%m-%d'), started_datetime.strftime('%H:%M:%S'))
	
	# Get parameter from console
	parameter = getParameter(sys.argv[1:])
	years     = parameter['year']
	inputfile = parameter['inputfile']
	
	# Read input file and create bitstring for outputfileName and codes list
	control = ReadInputFile(inputfile)
	#print control['bitstring']
	#print control['codes']

	# Read codebook table and select
	for year in years:
		LongitudinalNeighborhoodAnalysis(year, control)

	ended_datetime = datetime.now()
	elapsed = ended_datetime - started_datetime
	total_seconds = int(elapsed.total_seconds())
	hours, remainder = divmod(total_seconds,60*60)
	minutes, seconds = divmod(remainder,60)	
	print 'LongitudinalNeighborhoodAnalysis ended at %s %s    Elapsed %02d:%02d:%02d' % (ended_datetime.strftime('%Y-%m-%d'), ended_datetime.strftime('%H:%M:%S'), hours, minutes, seconds)
