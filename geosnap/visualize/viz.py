# first you have to load the geojson file
import os
import dash
import dash_core_components as dcc

import json
from geosnap.data import Community

dc = Community(statefips='11', source='ltdb')

dirname = os.path.abspath(os.path.dirname(__file__))
jsonpath = os.path.join(dirname, 'data.geojson')
mapbox_access_token = 'pk.eyJ1Ijoia25hYXB0aW1lIiwiYSI6ImlQeUJxazgifQ.35yYbOewGVVf7OkcM64obQ'

print(jsonpath)

with open(jsonpath) as geofile:
    geojson_layer = json.load(geofile)

trace = dict(type='scattermapbox',
             autocolorscale=True,
             locations=dc.tracts['geoid'])

app = dash.Dash()

app.layout = dcc.Graph(
    id="mapbox",
    figure={
        "data": [trace],
        "layout":
        dict(autosize=True,
             hovermode="closest",
             margin=dict(l=0, r=0, t=0, b=0),
             mapbox=dict(accesstoken=mapbox_access_token,
                         bearing=0,
                         center=dict(lon=dc.tracts.unary_union.centroid.x,
                                     lat=dc.tracts.unary_union.centroid.y),
                         style="light",
                         pitch=0,
                         zoom=6,
                         layers=[
                             dict(
                                 type="fill",
                                 sourcetype="geojson",
                                 source=geojson_layer,
                                 opacity=0.8,
                             )
                         ]))
    },
    style={"height": "100vh"})

app.run_server()
