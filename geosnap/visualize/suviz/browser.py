import urllib.parse
import webbrowser
import os

# uncomment to local a remote file in a browser window
#url = 'http://sarasen.asuscomm.com/GEOSNAP_CL/2_Bivariate_ACM/Bivariate_ACM.html'
#webbrowser.open(url)

# openning a local file

local_dir = os.path.dirname(os.path.realpath(__file__))
print(local_dir)
fname =urllib.parse.quote('Adaptive Choropleth Mapper with Parallel Coordinates Plot.html')
template_dir = os.path.join(local_dir, 'templates')
url = 'file://' + os.path.join(template_dir, fname)
print(url)
webbrowser.open(url)

