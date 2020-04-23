import os

try:
    from geosnap import io
except:
    pass


try:
    io.store_ltdb(sample='/ltdb_sample.zip', fullcount='/ltdb_full.zip')
    io.store_ncdb(path + "/ncdb.csv")

except:
    pass