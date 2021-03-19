import os
import wget
import zipfile
from geosnap.io import store_census

try:
    url = os.environ['COMBO_DATA']
    wget.download(url, 'data.zip')
    with zipfile.ZipFile('data.zip', 'r') as zip_ref:
        zip_ref.extractall()
except Exception:
    print('Unable to download data')

store_census()