# first you have to load the geojson file
import os
import dash
import geopandas as gpd
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import mapclassify
import palettable
import json
from geosnap.data import Community
from geosnap.data import metros
from geosnap.util import convert_gdf

dc = Community(statefips='11', source='ltdb')

mapbox_access_token = 'pk.eyJ1Ijoia25hYXB0aW1lIiwiYSI6ImlQeUJxazgifQ.35yYbOewGVVf7OkcM64obQ'
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

#gdf = dc.tracts[dc.tracts.geoid.str.startswith('11')]

opts = [{'label': col.title(), 'value': col} for col in dc.census.columns]
metros = metros.sort_values(by='name')

metro_opts = [{
    'label': str(metro['name']),
    'value': metro['geoid']
} for _, metro in metros.iterrows()]

precomputed_color_ranges = palettable.colorbrewer.sequential.Blues_6.hex_colors
layers = []

trace = dict(type='scattermapbox', autocolorscale=True, name='metro')

app = dash.Dash(external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions'] = True

app.layout = html.Div([
    html.H2(children='geosnap variable explorer',
            style={'textAlign': 'center'}),
    dcc.Dropdown(id='metro-choice', options=metro_opts, value='47900'),
    dcc.Dropdown(id='overlay-choice',
                 options=opts,
                 value='n_nonhisp_black_persons'),
    html.Div([
        dcc.Graph(id='map-display', style={"height": "75vh"}),
        html.Div(id='intermediate-value', style={'display': 'none'}),
        html.Div(dcc.Slider(id='year-slider',
                            min=dc.census['year'].min(),
                            max=dc.census['year'].max(),
                            value=2010,
                            marks={
                                str(year): str(year)
                                for year in dc.census['year'].unique()
                            },
                            step=10),
                 style={
                     "padding-left": "10%",
                     "padding-right": "10%",
                     "padding-top": "2%"
                 })
    ]),
])

map_layout = {
    'data': [{
        'name': 'Layer name',
        'sourcetype': 'geojson',
        'type': 'fill',
        'opacity': 0.8,
        'color': '#FFFFFF',  # Dynamically replace this with your color options
        'type': 'scattermapbox',
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
                'lat': dc.tracts.unary_union.centroid.y,
                'lon': dc.tracts.unary_union.centroid.x,
            },
            'style': "light",
            'zoom': 8,
            'bearing': 0.0,
            'pitch': 0.0,
        },
    }
}


@app.callback(dash.dependencies.Output('intermediate-value', 'children'), [
    dash.dependencies.Input('metro-choice', 'value'),
])
def update_map(metro_choice):

    community = Community(source='ltdb', cbsafips=metro_choice)

    gdf = community.tracts.merge(community.census, on='geoid', how='right')
    return gdf.to_json()


@app.callback(Output('map-display', 'figure'), [
    dash.dependencies.Input('intermediate-value', 'children'),
    dash.dependencies.Input('overlay-choice', 'value'),
    dash.dependencies.Input('year-slider', 'value')
])
def update_graph_1(jsonified_data, overlay_choice, year_choice):

    gdf = gpd.read_file(jsonified_data)
    tmp = map_layout.copy()
    gdf[gdf['year'] == year_choice]
    gdf = gdf.assign(
        cl=mapclassify.Equal_Interval(gdf[overlay_choice], k=6).yb)
    # Create a layer for each region colored by LEP value

    gdf = gdf[['geoid', 'cl', 'geometry']]

    layers = []

    for i, lyr in enumerate(precomputed_color_ranges):
        example = {
            'name': 'Layer name',
            'source': json.loads(gdf[gdf.cl == i].to_json()),
            'sourcetype': 'geojson',
            'type': 'fill',
            'opacity': 0.8,
            'color': lyr
        }
        layers.append(example)

    tmp['layout']['mapbox']['layers'] = layers
    tmp['layout']['mapbox']['center'] = {
        'lat': gdf.unary_union.centroid.y,
        'lon': gdf.unary_union.centroid.x
    }

    return tmp


if __name__ == '__main__':
    app.run_server()
