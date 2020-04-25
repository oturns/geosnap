import os
from pathlib import PurePath
try:
    from geosnap import io
except:
    pass

path = os.getcwd()

try:
    io.store_ltdb(sample=PurePath(path, 'ltdb_sample.zip'), fullcount=PurePath(path, 'ltdb_full.zip'))
    io.store_ncdb(PurePath(path, "ncdb.csv"))

except:
    pass