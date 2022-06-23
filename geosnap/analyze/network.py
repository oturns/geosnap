import geopandas as gpd
import numpy as np
import pandas as pd
from libpysal.cg import alpha_shape_auto
from tqdm.auto import tqdm


def compute_travel_cost_adjlist(
    origins, destinations, network, index_orig=None, index_dest=None
):
    """Generate travel cost adjacency list.

    Parameters
    ----------
    origins : geopandas.GeoDataFrame
        a geodataframe containing the locations of origin features
    destinations : geopandas.GeoDataFrame
        a geodataframe containing the locations of destination features
    network : pandana.Network
        pandana Network instance for calculating the shortest path between origins and destinations
    index_orig : str, optional
        Column on the origins dataframe the defines unique units to be used as the origins id
        on the resulting dataframe. If not set, each unit will be assigned the index from its
        associated node_id on the network
    index_dest : str, optional
        Column on the destinations dataframe the defines unique units to be used as the destinations id
        on the resulting dataframe. If not set, each unit will be assigned the index from its
        associated node_id on the network

    Returns
    -------
    pandas.DataFrame
        pandas DataFrame containing the shortest-cost distance from each origin feature to each destination feature
    """

    # NOTE: need to add an option/check for symmetric networks so we only need half the routing calls

    origins = origins.copy()
    destinations = destinations.copy()

    origins["osm_ids"] = network.get_node_ids(
        origins.centroid.x, origins.centroid.y
    ).astype(int)
    destinations["osm_ids"] = network.get_node_ids(
        destinations.centroid.x, destinations.centroid.y
    ).astype(int)

    ods = []

    if not index_orig:
        origins["idx"] = origins.index.values
        index_orig = "idx"
    if not index_dest:
        destinations["idx"] = destinations.index.values
        index_dest = "idx"

    # I dont think there's a way to do this in parallel, so we can at least show a progress bar
    with tqdm(total=len(origins["osm_ids"])) as pbar:
        for origin in origins["osm_ids"]:
            df = pd.DataFrame()
            df["cost"] = network.shortest_path_lengths(
                [origin for d in destinations["osm_ids"]],
                [d for d in destinations["osm_ids"]],
            )
            df["destination"] = destinations[index_dest].values
            df["origin"] = origins[origins.osm_ids == origin][index_orig].values[0]

            ods.append(df)
            pbar.update(1)

    combined = pd.concat(ods)
    # reorder the columns
    return combined[['origin', 'destination', 'cost']]


def isochrone(origin, network, threshold):
    """Create travel isochrone(s) from a single origin using a pandana network.

    Parameters
    ----------
    origin : int or list
        A single or list of node id(s) from a `pandana.Network.nodes_df` to serve as isochrone origins
    network : pandana.Network
        A pandana network object
    threshold : int or list
        A single or list of threshold distances for which isochrones will be computed. These are in the
        same units as edges from the pandana.Network.edge_df

    Returns
    -------
    geopandas.GeoDataFrame
        A geodataframe with a single attribute (distance) and a polygon geometry representing
        a travel time isochrone, with a row for each threshold distance
    """
    dfs = []

    # create a geodataframe of nodes from the network
    node_df = gpd.GeoDataFrame(
        network.nodes_df,
        geometry=gpd.points_from_xy(network.nodes_df.x, network.nodes_df.y),
        crs=4326,
    )
    matrix = compute_travel_cost_adjlist(
        origins=node_df[node_df.index == origin],
        destinations=node_df,
        network=network,
    )
    if not isinstance(threshold, list):
        threshold = [threshold]
    threshold.sort(reverse=True)

    for distance in threshold:

        # select the nodes within each threshold distance and take their alpha shape
        df = matrix[matrix.cost <= distance]
        nodes = node_df[node_df.index.isin(df.destination.tolist())]
        alpha = alpha_shape_auto(
            np.array([(nodes.loc[i].x, nodes.loc[i].y) for i in nodes.index.tolist()])
        )
        alpha = gpd.GeoDataFrame(geometry=pd.Series(alpha), crs=4326)
        alpha["distance"] = distance

        dfs.append(alpha)

    alpha = pd.concat(dfs).reset_index(drop=True)

    return alpha


def isochrones(origins, threshold, network, matrix=None, network_crs=4326):
    """ Create travel isochrones for several origins simultaneously

    Parameters
    ----------
    origins : geopandas.GeoDataFrame
        a geodataframe containing the locations of origin point features
    network : pandana.Network
        pandana Network instance for calculating the shortest path isochrone for each origin feature
    threshold: float
        maximum travel distance to define the isochrone, measured in the same units as edges_df
        in the pandana.Network object. If the network was created with pandana this is usually meters;
        if it was created with urbanaccess this is usually travel time in minutes.
    matrix: pandas dataframe (optional)
        precalculated adjacency list dataframe created with `compute_travel_adjlist`
    network_crs : str, int, pyproj.CRS (optional)
        the coordinate system used to store x and y coordinates in the passed pandana network.
        If the network was created with pandana or urbanaccess this is nearly always 4326.

    Returns
    -------
    GeoPandas.DataFrame
        polygon geometries with the isochrones for each origin point feature

    """
    destinations = gpd.GeoDataFrame(
        network.nodes_df,
        geometry=gpd.points_from_xy(network.nodes_df.x, network.nodes_df.y),
        crs=network_crs,
    )
    if matrix is None:
        matrix = compute_travel_cost_adjlist(origins, destinations, network=network)
    matrix = matrix[matrix.cost <= threshold]
    alphas = []
    for origin in matrix.origin.unique():
        do = matrix[matrix.origin == origin]
        alpha = alpha_shape_auto(
            np.array(
                [
                    (destinations.loc[i].x, destinations.loc[i].y)
                    for i in do.destination.values
                ]
            )
        )
        alpha = gpd.GeoDataFrame(geometry=pd.Series(alpha), crs=network_crs)
        alpha["distance"] = threshold
        alpha["origin"] = origin
        alphas.append(alpha)
    return gpd.GeoDataFrame(pd.concat(alphas, ignore_index=True), crs=network_crs)
