from mapclassify import *


def explore(data="census"):
    """Launch an interactive visualization portal.

    This function launches an interactive dataset explorer based on plotly's `dash`
    Currently it is still experimental, but it provides a set of interactive widgets
    and maps that allow users to rapidly create  metropolitan-scale datasets and choropleth
    webmaps using a variety of census data.

    Parameters
    ----------
    data : str
        Which dataset to explore. Options include "census, "ltdb", and "ncdb" (the default is "census").

    Returns
    -------
    None
        Launches a web-browser with the interactive visualization.

    """
    mem = {}
    mem["last_metro"] = ""
    mem["last_comm"] = ""

    import dash
    import dash_core_components as dcc
    import dash_html_components as html
    import dash_bootstrap_components as dbc
    import webbrowser
    import palettable
    import json
    from geosnap import Community, datasets

    mem["data"] = data

    mapbox_access_token = (
        "pk.eyJ1Ijoia25hYXB0aW1lIiwiYSI6ImlQeUJxazgifQ.35yYbOewGVVf7OkcM64obQ"
    )
    external_stylesheets = [dbc.themes.JOURNAL]

    opts = []
    for colname in datasets.codebook().variable:
        val = colname
        if colname.startswith("n_"):
            colname = colname[1:]
        elif colname.startswith("p_"):
            colname = colname[1:]
            colname = colname + " (%)"
        colname = colname.replace("_", " ")
        colname = colname.title()
        opts.append({"label": colname, "value": val})

    # opts = [{'label': col.title(), 'value': col} for col in dictionary.variable]

    k_opts = [{"label": str(k), "value": k} for k in range(3, 11)]
    data_type = ["sequential", "diverging", "qualitative"]
    data_opts = [{"label": scheme, "value": scheme.title()} for scheme in data_type]

    scheme_dispatch = {
        "Equal Interval": EqualInterval,
        "Fisher Jenks": FisherJenks,
        "Head-Tail Breaks": HeadTailBreaks,
        "Jenks Caspall": JenksCaspall,
        "Max-P Classifier": MaxP,
        "Maximum Breaks": MaximumBreaks,
        "Natural Breaks": NaturalBreaks,
        "Quantiles": Quantiles,
        "Percentiles": Percentiles,
    }

    sequential = [
        "Blues",
        "BuGn",
        "BuPu",
        "GnBu",
        "Greens",
        "Greys",
        "OrRd",
        "Oranges",
        "PuBu",
        "PuBuGn",
        "PuRd",
        "Purples",
        "RdPu",
        "Reds",
        "YlGn",
        "YlGnBu",
        "YlOrBr",
        "YlOrRd",
    ]
    diverging = [
        "BrBG",
        "PRGn",
        "PiYG",
        "PuOr",
        "RdBu",
        "RdGy",
        "RdYlBu",
        "RdYlGn",
        "Spectral",
    ]
    qualitative = [
        "Accent",
        "Dark2",
        "Paired",
        "Pastel1",
        "Pastel2",
        "Set1",
        "Set2",
        "Set3",
    ]

    cmaps = sequential + diverging + qualitative

    cmap_opts = [{"label": cmap, "value": cmap} for cmap in cmaps]

    scheme_opts = [{"label": str(v), "value": v} for v in scheme_dispatch]

    metro_opts = [
        {"label": str(metro["name"]), "value": metro["geoid"]}
        for _, metro in datasets.msas().iterrows()
    ]

    precomputed_color_ranges = palettable.colorbrewer.sequential.Blues_6.hex_colors

    trace = dict(type="scattermapbox", autocolorscale=True, name="metro")

    navbar = dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("geosnap", href="http://spatial.ucr.edu")),
            dbc.DropdownMenu(
                nav=True,
                in_navbar=True,
                label="Menu",
                children=[
                    dbc.DropdownMenuItem("Explore Variables"),
                    dbc.DropdownMenuItem("Identify Neighborhoods"),
                    dbc.DropdownMenuItem("Model Neighborhood Change"),
                    dbc.DropdownMenuItem(divider=True),
                    dbc.DropdownMenuItem("Docs", href="http://geosnap.readthedocs.io"),
                    dbc.DropdownMenuItem(
                        "Github", href="http://github.com/spatialucr/geosnap"
                    ),
                ],
            ),
        ],
        brand="cgs",
        brand_href="#",
        sticky="top",
        dark=True,
        color="dark",
    )

    body = dbc.Container(
        [
            html.H2(
                children="Variable Explorer",
                style={
                    "textAlign": "center",
                    "padding-top": "2%",
                    "padding-bottom": "4%",
                },
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5(
                                children="Metropolitan Region",
                                style={"padding-bottom": "4%"},
                            ),
                            dcc.Dropdown(
                                id="metro-choice",
                                options=metro_opts,
                                value="41740",
                                style={"padding-bottom": "2%"},
                            ),
                            html.H5(
                                children="Variable",
                                style={"padding-top": "2%", "padding-bottom": "2%"},
                            ),
                            dcc.Dropdown(
                                id="overlay-choice",
                                options=opts,
                                value="median_home_value",
                                style={"padding-bottom": "2%"},
                            ),
                            html.H5(
                                children="Classification Scheme",
                                style={"padding-top": "2%", "padding-bottom": "2%"},
                            ),
                            dcc.Dropdown(
                                id="scheme-choice",
                                options=scheme_opts,
                                value="Equal Interval",
                                style={"padding-bottom": "2%"},
                            ),
                            html.H5(
                                children="Colormap",
                                style={"padding-top": "2%", "padding-bottom": "2%"},
                            ),
                            dcc.Dropdown(
                                id="cmap-choice",
                                options=cmap_opts,
                                value="YlOrBr",
                                style={"padding-bottom": "2%"},
                            ),
                            html.H5(
                                children="Number of Classes",
                                style={"padding-top": "2%", "padding-bottom": "2%"},
                            ),
                            dcc.Dropdown(
                                id="k-choice",
                                options=k_opts,
                                value=6,
                                style={"padding-bottom": "2%"},
                            ),
                            html.H5(
                                children="Year",
                                style={"padding-top": "2%", "padding-bottom": "2%"},
                            ),
                            html.Div(
                                dcc.Slider(
                                    id="year-slider",
                                    min=1970,
                                    max=2010,
                                    value=2010,
                                    marks={
                                        str(year): str(year)
                                        for year in range(1970, 2011, 10)
                                    },
                                    step=10,
                                ),
                                style={
                                    "padding-left": "5%",
                                    "padding-right": "5%",
                                    "padding-top": "2%",
                                    "padding-bottom": "4%",
                                },
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            dcc.Loading(
                                id="loading-output-1",
                                children=[dcc.Graph(id="map-display")],
                                type="default",
                            )
                        ],
                        md=9,
                    ),
                ]
            ),
        ],
        className="mt-4",
    )

    app = dash.Dash(external_stylesheets=external_stylesheets)

    app.layout = html.Div([navbar, body])

    map_layout = {
        "data": [
            {
                "name": "Layer name",
                "sourcetype": "geojson",
                "opacity": 0.8,
                "type": "scattermapbox",
                "showlegend": True,
                "textposition": "top",
                "text": "geoid",
                "mode": "markers+text",
                "hoverinfo": "text",
                "marker": dict(size=5, color="white", opacity=0),
            }
        ],
        "layout": {
            "autosize": True,
            "hovermode": "closest",
            "margin": {"l": 0, "r": 0, "b": 0, "t": 0},
            "showlegend": True,
            "mapbox": {
                "accesstoken": mapbox_access_token,
                "center": {"lat": 0, "lon": 0},
                "style": "light",
                "zoom": 8,
                "bearing": 0.0,
                "pitch": 0.0,
            },
        },
    }

    @app.callback(
        dash.dependencies.Output("map-display", "figure"),
        [
            dash.dependencies.Input("overlay-choice", "value"),
            dash.dependencies.Input("metro-choice", "value"),
            dash.dependencies.Input("year-slider", "value"),
            dash.dependencies.Input("k-choice", "value"),
            dash.dependencies.Input("scheme-choice", "value"),
            dash.dependencies.Input("cmap-choice", "value"),
        ],
    )
    def update_map(
        overlay_choice, metro_choice, year_choice, k_choice, scheme_choice, cmap_choice
    ):

        readers = {
            "census": Community.from_census,
            "ltdb": Community.from_ltdb,
            "ncdb": Community.from_ncdb,
        }
        if cmap_choice in qualitative:
            cmap_type = "qualitative"
        elif cmap_choice in sequential:
            cmap_type = "sequential"
        else:
            cmap_type = "diverging"

        tmp = map_layout.copy()

        if metro_choice != mem["last_metro"]:
            community = readers[mem["data"]](msa_fips=metro_choice)
            mem["last_metro"] = metro_choice
            mem["last_comm"] = community
        else:
            community = mem["last_comm"]

        gdf = community.gdf[community.gdf.year == year_choice]

        gdf = gdf.dropna(subset=[overlay_choice]).reset_index()

        if scheme_choice in ["Max-P Classifier", "Maximum Breaks", "Head-Tail Breaks"]:
            classes = scheme_dispatch[scheme_choice](gdf[overlay_choice]).yb
        else:
            classes = scheme_dispatch[scheme_choice](gdf[overlay_choice], k=k_choice).yb
        gdf = gdf.assign(cl=classes)

        if not k_choice:
            k_choice = len(gdf.cl.unique())
        # Create a layer for each region colored by LEP value

        gdf = gdf[["geoid", "cl", "geometry"]]

        layers = []

        precomputed_color_ranges = palettable.colorbrewer.get_map(
            cmap_choice, cmap_type, k_choice
        ).hex_colors
        for i, lyr in enumerate(precomputed_color_ranges):
            example = {
                "name": "Layer name",
                "source": json.loads(gdf[gdf.cl == i].to_json()),
                "sourcetype": "geojson",
                "type": "fill",
                "opacity": 0.8,
                "color": lyr,
            }
            layers.append(example)

        tmp["layout"]["mapbox"]["layers"] = layers
        tmp["layout"]["mapbox"]["center"] = {
            "lat": gdf.unary_union.centroid.y,
            "lon": gdf.unary_union.centroid.x,
        }

        tmp["data"][0]["text"] = gdf["geoid"].tolist()

        return tmp

    @app.callback(dash.dependencies.Output("loading-output-1", "children"))
    def input_triggers_spinner(value):
        return value

    webbrowser.open("http://127.0.0.1:8050")
    app.run_server()


if __name__ == "__main__":
    explore()
