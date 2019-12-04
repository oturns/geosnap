# -*- coding: utf-8 -*-
# This program reads the table, "codebook" in LTDB database and prints the data in JSON
import cgitb, cgi, json, sys, re
import time
from datetime import datetime
cgitb.enable()

import psycopg2

'''
fields = cgi.FieldStorage()
date = "2014-05-06~2014-05-06"
time = ""
keyword=""
if "date"    in fields: date    = fields['date'].value
if "time"    in fields: time    = fields['time'].value
if "keyword" in fields: keyword = fields['keyword'].value
'''

class reg(object):
    def __init__(self, cursor, row):
        for (attr, val) in zip((d[0] for d in cursor.description), row) :
            setattr(self, attr, val)

conn = psycopg2.connect("host='localhost' dbname='LTDB' user='neighborhood' password='Tomas159'")
curs = conn.cursor()

curs.execute("SELECT * FROM state ORDER BY stateid")
states = curs.fetchall()

curs.execute("SELECT * FROM groups ORDER BY groupid")
groups = curs.fetchall()

#curs.execute("SELECT count(*) FROM codebook")
#result = curs.fetchone()
#count = result[0]

curs.execute("SELECT * FROM codebook LIMIT 0")
colnames = [desc[0] for desc in curs.description]

curs.execute("SELECT * FROM codebook ORDER BY serial")
results = curs.fetchall()

codebook = [colnames]
for row in results:
	r = reg(curs, row)
	if r.web_system != 1: continue
	codebook.append(row)


time.sleep(0)
out_data = {'states': states, 'groups': groups, 'codebook': codebook}

print ("Content-Type: text/html\n")
print (json.dumps(out_data))
