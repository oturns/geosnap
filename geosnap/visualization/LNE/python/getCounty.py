# -*- coding: utf-8 -*-
# This program reads the table, "county" or "metro_county" in LTDB database and prints the data in JSON
import cgitb, cgi, json, sys, re
import time
from datetime import datetime
cgitb.enable()

import psycopg2


fields = cgi.FieldStorage()

stateid = "06"                         # default 06 CA
metroid = "ALL"                        # default
if "stateid" in fields: stateid = fields['stateid'].value
if "metroid" in fields: metroid = fields['metroid'].value


class reg(object):
    def __init__(self, cursor, row):
        for (attr, val) in zip((d[0] for d in cursor.description), row) :
            setattr(self, attr, val)

conn = psycopg2.connect("host='localhost' dbname='LTDB' user='neighborhood' password='Tomas159'")
curs = conn.cursor()

if metroid == "ALL":                   # request all county in the state.
	curs.execute("SELECT countyid, countyname FROM county WHERE countyid BETWEEN '" + stateid + "' AND '" + stateid + "999" +"' ORDER BY countyid")
	counties = curs.fetchall()
else:                                  # request all county in the metro area
	curs.execute("SELECT geoid10_county AS countyid, name10_county AS countyname FROM metro_county WHERE states_msa_code = '" + stateid + "' AND geoid_msa = '" + metroid + "' ORDER BY states_msa_code, geoid_msa, geoid10_county")
	counties = curs.fetchall()

time.sleep(0)
out_data = {'counties': counties}

print ("Content-Type: text/html\n")
print (json.dumps(out_data))
