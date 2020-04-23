import os
from pathlib import PurePath
try:
    from geosnap import io
except:
    pass

try:
    path = os.environ["GITHUB_WORKSPACE"]
except Exception: 
    path = os.getcwd()

try:
    io.store_ltdb(sample=PurePath(path,'ltdb_sample.zip'), fullcount=PurePath(path,'ltdb_full.zip'))
    io.store_ncdb(path + "ncdb.csv")

except:
    pass