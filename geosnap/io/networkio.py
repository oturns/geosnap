from warnings import warn

import geopandas as gpd
import pandana as pdna


def _reproject_osm_nodes(nodes_df, input_crs, output_crs):
    #  take original x,y coordinates and convert into geopandas.Series, then reproject
    nodes = gpd.points_from_xy(x=nodes_df.x, y=nodes_df.y, crs=input_crs).to_crs(
        output_crs
    )
    #  convert to dataframe and recreate the x and y cols
    nodes = gpd.GeoDataFrame(index=nodes_df.index, geometry=nodes)
    nodes["x"] = nodes.centroid.x
    nodes["y"] = nodes.centroid.y
    return nodes


def get_network_from_gdf(
    gdf, network_type="walk", twoway=False, add_travel_times=False, default_speeds=None
):
    """Create a pandana.Network object from a geodataframe (via OSMnx graph).

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        dataframe covering the study area of interest; Note the first step is to take
        the unary union of this dataframe, which is expensive, so large dataframes may
        be time-consuming. The network will inherit the CRS from this dataframe
    network_type : str, {"all_private", "all", "bike", "drive", "drive_service", "walk"}
        the type of network to collect from OSM (passed to `osmnx.graph_from_polygon`)
        by default "walk"
    twoway : bool, optional
        Whether to treat the pandana.Network as directed or undirected. For a directed network,
        use `twoway=False` (which is the default). For an undirected network (e.g. a
        walk network) where travel can flow in both directions, the network is more
        efficient when twoway=True but forces the impedance to be equal in both
        directions. This has implications for auto or multimodal
        networks where impedance is generally different depending on travel direction.
    add_travel_times : bool, default=False
        whether to use posted travel times from OSM as the impedance measure (rather
        than network-distance). Speeds are based on max posted drive speeds, see
        <https://osmnx.readthedocs.io/en/stable/internals-reference.html#osmnx-speed-module>
        for more information.
    default_speeds : dict, optional
        default speeds passed assumed when no data available on the OSM edge. Defaults
        to  {"residential": 35, "secondary": 50, "tertiary": 60}. Only considered if
        add_travel_times is True

    Returns
    -------
    pandana.Network
        a pandana.Network object with node coordinates stored in the same system as the
        input geodataframe. If add_travel_times is True, the network impedance
        is travel time measured in seconds (assuming automobile travel speeds); else 
        the impedance is travel distance measured in meters

    Raises
    ------
    ImportError
        requires `osmnx`, raises if module not available
    """
    gdf = gdf.copy()
    try:
        import osmnx as ox
    except ImportError as e:
        raise ImportError("this functions requires the osmnx module") from e
    output_crs = None
    if not gdf.crs.is_geographic:
        output_crs = gdf.crs
        warn(
            f"GeoDataFrame is stored in coordinate system {output_crs} so the "
            "pandana.Network will also be stored in this system",
            stacklevel=1,
        )
        gdf = gdf.to_crs(4326)

    if default_speeds is None:
        default_speeds = {
            "residential": 35,
            "secondary": 50,
            "tertiary": 60,
        }

    impedance = "length"
    graph = ox.graph_from_polygon(gdf.union_all(), network_type=network_type)
    if add_travel_times:
        graph = ox.add_edge_speeds(graph, hwy_speeds=default_speeds)
        graph = ox.add_edge_travel_times(graph)
        impedance = "travel_time"

    n, e = ox.graph_to_gdfs(graph)
    if output_crs is not None:
        n = _reproject_osm_nodes(n, input_crs=4326, output_crs=output_crs)
        e = e.to_crs(output_crs)
    e = e.reset_index()

    net = pdna.Network(
        edge_from=e["u"],
        edge_to=e["v"],
        edge_weights=e[[impedance]],
        node_x=n["x"],
        node_y=n["y"],
        twoway=twoway,
    )
    # keep the geometries on hand, since we have them already
    net.edges_df = gpd.GeoDataFrame(net.edges_df, geometry=e.geometry, crs=output_crs)

    return net

def project_network(network, output_crs=None, input_crs=4326):
    """Reproject a pandana.Network object into another coordinate system.

    Note this function does not change the legth of any network edges, but
    reprojects the x and y coordinates of the nodes (e.g. for precise snapping)
    between nodes and projected origin/destination data

    Parameters
    ----------
    network : pandana.Network
        an instantiated pandana Network object
    input_crs : int, optional
        the coordinate system used in the Network.node_df dataframe. Typically
        these data are collected in Lon/Lat, so the default 4326
    output_crs : int, str, or pyproj.crs.CRS, required
        EPSG code or pyproj.crs.CRS object of the output coordinate system

    Returns
    -------
    pandana.Network
        an initialized pandana.Network with 'x' and y' values represented
        by coordinates in the specified CRS
    """
    assert output_crs, "You must provide an output CRS"

    #  take original x,y coordinates and convert into geopandas.Series, then reproject
    nodes = _reproject_osm_nodes(network.nodes_df, input_crs, output_crs)
    edges = network.edges_df.copy()
    if "geometry" in edges.columns:
        edges = edges.to_crs(output_crs)

    #  reinstantiate the network (needs to rebuild the tree)
    net = pdna.Network(
        node_x=nodes["x"],
        node_y=nodes["y"],
        edge_from=edges["from"],
        edge_to=edges["to"],
        edge_weights=edges[[network.impedance_names[0]]],
        twoway=network._twoway,
    )
    return net
