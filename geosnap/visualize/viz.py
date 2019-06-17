# first you have to load the geojson file
import os
import dash
import geopandas as gpd
import dash_core_components as dcc
import mapclassify
import palettable
import json
from geosnap.data import Community

dc = Community(statefips='11', source='ltdb')

mapbox_access_token = 'pk.eyJ1Ijoia25hYXB0aW1lIiwiYSI6ImlQeUJxazgifQ.35yYbOewGVVf7OkcM64obQ'

gdf = dc.tracts[dc.tracts.geoid.str.startswith('11')]
gdf = gdf.merge(dc.census[dc.census.year == 2010], on='geoid')

gdf = gdf.assign(
    cl=mapclassify.Equal_Interval(gdf.n_nonhisp_black_persons, k=6).yb)

precomputed_color_ranges = palettable.colorbrewer.sequential.Blues_6.hex_colors
layers = []

for i, lyr in enumerate(precomputed_color_ranges):
    example = {
        'name': 'Layer name',
        'source': json.loads(gdf[gdf.cl == i].to_json()),
        'sourcetype': 'geojson',
        'type': 'fill',
        'opacity': 1.0,
        'color': lyr  # Dynamically replace this with your color options
    }
    layers.append(example)

trace = dict(type='scattermapbox',
             autocolorscale=True,
             locations=dc.tracts['geoid'],
             name='DC',
             text=gdf.index)

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
                         zoom=10,
                         layers=layers))
    },
    style={"height": "100vh"})

app.run_server()
