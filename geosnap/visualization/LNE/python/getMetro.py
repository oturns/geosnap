# -*- coding: utf-8 -*-
# This program reads the table, "metro" in LTDB database and prints the data in JSON
import cgitb, cgi, json, sys, re
import time
from datetime import datetime
cgitb.enable()

import psycopg2


fields = cgi.FieldStorage()

stateid = "06"        # default 06 CA
if "stateid" in fields: stateid = fields['stateid'].value


class reg(object):
    def __init__(self, cursor, row):
        for (attr, val) in zip((d[0] for d in cursor.description), row) :
            setattr(self, attr, val)

conn = psycopg2.connect("host='localhost' dbname='LTDB' user='neighborhood' password='Tomas159'")
curs = conn.cursor()

curs.execute("SELECT * FROM metro LIMIT 0")
colnames = [desc[0] for desc in curs.description]

curs.execute("SELECT * FROM metro WHERE stateid = '" + stateid + "' ORDER BY stateid, metroid")
metros = curs.fetchall()

#results = curs.fetchall()
#metros = [colnames]
#for row in results:
#	r = reg(curs, row)
#	metros.append(row)

time.sleep(0)
out_data = {'metros': metros}

print("Content-Type: text/html\n")
print(json.dumps(out_data))
