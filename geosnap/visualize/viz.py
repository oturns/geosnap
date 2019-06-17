# first you have to load the geojson file
import os
import dash
import geopandas as gpd
import dash_core_components as dcc
import dash_html_components as html

import mapclassify
import palettable
import json
from geosnap.data import Community

dc = Community(statefips='11', source='ltdb')

mapbox_access_token = 'pk.eyJ1Ijoia25hYXB0aW1lIiwiYSI6ImlQeUJxazgifQ.35yYbOewGVVf7OkcM64obQ'

gdf = dc.tracts[dc.tracts.geoid.str.startswith('11')]
gdf = gdf.merge(dc.census[dc.census.year == 2010], on='geoid')

opts = [{'label': col.title(), 'value': col} for col in gdf.columns]

precomputed_color_ranges = palettable.colorbrewer.sequential.Blues_6.hex_colors
layers = []

trace = dict(type='scattermapbox',
             autocolorscale=True,
             locations=dc.tracts['geoid'],
             name='DC',
             text=gdf.geoid)

app = dash.Dash()

app.layout = html.Div([
    html.H1(children='geosnap'),
    dcc.Dropdown(id='overlay-choice',
                 options=opts,
                 value='n_nonhisp_black_persons'),
    html.Div([
        dcc.Graph(id='map-display', style={"height": "100vh"}),
    ])
])

map_layout = {
    'title':
    'geosnap',
    'data': [{
        'name': 'Layer name',
        'sourcetype': 'geojson',
        'type': 'fill',
        'opacity': 1.0,
        'color': '#FFFFFF',  # Dynamically replace this with your color options
        'type': 'scattermapbox',
        'text': gdf['geoid'],
        'hoverinfo': 'text',
        'showlegend': True,
    }],
    'layout': {
        'autosize': True,
        'hovermode': 'closest',
        'margin': {
            'l': 0,
            'r': 0,
            'b': 0,
            't': 0
        },
        'mapbox': {
            'accesstoken': mapbox_access_token,
            'center': {
                'lat': gdf.unary_union.centroid.y,
                'lon': gdf.unary_union.centroid.x,
            },
            'style': "light",
            'zoom': 8.0,
            'bearing': 0.0,
            'pitch': 0.0,
        },
    }
}


@app.callback(dash.dependencies.Output('map-display', 'figure'),
              [dash.dependencies.Input('overlay-choice', 'value')])
def update_map(overlay_choice):

    tmp = map_layout.copy()

    gdf = dc.tracts[dc.tracts.geoid.str.startswith('11')]
    gdf = gdf.merge(dc.census[dc.census.year == 2010], on='geoid')

    gdf = gdf.assign(
        cl=mapclassify.Equal_Interval(gdf[overlay_choice], k=6).yb)
    # Create a layer for each region colored by LEP value

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

    tmp['layout']['mapbox']['layers'] = layers

    return tmp


# End update_map()
if __name__ == '__main__':

    app.run_server()
