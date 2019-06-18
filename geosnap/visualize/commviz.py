# first you have to load the geojson file
import os
import dash
import geopandas as gpd
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import mapclassify
import palettable
import json
from geosnap.data import dictionary
from geosnap.data import metros, Community

dictionary.variable.tolist()
mapbox_access_token = 'pk.eyJ1Ijoia25hYXB0aW1lIiwiYSI6ImlQeUJxazgifQ.35yYbOewGVVf7OkcM64obQ'
external_stylesheets = [dbc.themes.BOOTSTRAP]

#gdf = dc.tracts[dc.tracts.geoid.str.startswith('11')]

opts = [{'label': col.title(), 'value': col} for col in dictionary.variable]
metros = metros.sort_values(by='name')

metro_opts = [{
    'label': str(metro['name']),
    'value': metro['geoid']
} for _, metro in metros.iterrows()]

precomputed_color_ranges = palettable.colorbrewer.sequential.Blues_6.hex_colors
layers = []

trace = dict(type='scattermapbox', autocolorscale=True, name='metro')

navbar = dbc.NavbarSimple(
    children=[
        dbc.DropdownMenu(
            nav=True,
            in_navbar=True,
            label="Menu",
            children=[
                dbc.DropdownMenuItem("Variable Eplorer"),
                dbc.DropdownMenuItem("Neighborhood Identification"),
                dbc.DropdownMenuItem("Temporal Analysis"),
                dbc.DropdownMenuItem(divider=True),
                dbc.DropdownMenuItem(
                    "Github", href="http://github.com/spatialucr/geosnap"),
                dbc.DropdownMenuItem("Documentation",
                                     href='http://geosnap.readthedocs.io'),
            ],
        ),
    ],
    brand="geosnap",
    brand_href="http://spatial.ucr.edu",
    sticky="top",
)

body = dbc.Container(
    [
        html.H2(children='Variable Explorer',
                style={
                    'textAlign': 'center',
                    "padding-top": "2%",
                    "padding-bottom": "4%"
                }),
        dbc.Row([
            dbc.Col(
                [
                    html.H5(children='Metropolitan Region',
                            style={"padding-bottom": "2%"}),
                    dcc.Dropdown(
                        id='metro-choice', options=metro_opts, value='41740'),
                    html.H5(children='Variable',
                            style={
                                "padding-top": "2%",
                                "padding-bottom": "2%"
                            }),
                    dcc.Dropdown(id='overlay-choice',
                                 options=opts,
                                 value='median_home_value'),
                    html.H5(children='Year',
                            style={
                                "padding-top": "2%",
                                "padding-bottom": "2%"
                            }),
                    html.Div(dcc.Slider(id='year-slider',
                                        min=1970,
                                        max=2010,
                                        value=2010,
                                        marks={
                                            str(year): str(year)
                                            for year in range(1970, 2011, 10)
                                        },
                                        step=10),
                             style={
                                 "padding-left": "5%",
                                 "padding-right": "5%",
                                 "padding-top": "2%",
                                 "padding-bottom": "4%"
                             })
                ],
                md=3,
            ),
            dbc.Col([
                dcc.Graph(id='map-display'),
            ], md=9),
        ])
    ],
    className="mt-auto",
)

app = dash.Dash(external_stylesheets=external_stylesheets)

app.layout = html.Div([navbar, body])

map_layout = {
    'title':
    'geosnap',
    'data': [{
        'name': 'Layer name',
        'sourcetype': 'geojson',
        'opacity': 0.8,
        'type': 'scattermapbox',
        'hoverinfo': 'text',
        'showlegend': True,
        'mode': 'markers+text',
        'textposition': 'top'
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
                'lat': 0,
                'lon': 0,
            },
            'style': "light",
            'zoom': 8,
            'bearing': 0.0,
            'pitch': 0.0,
        },
    }
}


@app.callback(dash.dependencies.Output('map-display', 'figure'), [
    dash.dependencies.Input('overlay-choice', 'value'),
    dash.dependencies.Input('metro-choice', 'value'),
    dash.dependencies.Input('year-slider', 'value')
])
def update_map(overlay_choice, metro_choice, year_choice):

    tmp = map_layout.copy()

    community = Community(source='ltdb', cbsafips=metro_choice)

    gdf = community.tracts.merge(
        community.census[community.census.year == year_choice], on='geoid')

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
    tmp['data'][0]['text'] = gdf.geoid
    tmp['data'][0]['hovertext'] = gdf.geoid

    return tmp


if __name__ == '__main__':

    app.run_server()
