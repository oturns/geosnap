import os

try:
    from geosnap import io
except:
    pass

path = os.environ['DLPATH']

try:
    io.store_ltdb(sample=path + '/ltdb_sample.zip', fullcount=path + '/ltdb_full.zip')
    io.store_ncdb(path + "/ncdb.csv")

except:
    pass