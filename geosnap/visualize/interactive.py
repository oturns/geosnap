from warnings import warn

import geopandas as gpd
import numpy as np
import pandas as pd
from mapclassify.util import get_color_array
from matplotlib import colormaps
from matplotlib.colors import LinearSegmentedColormap

__all__ = ["GeosnapAccessor"]


# these methods
@pd.api.extensions.register_dataframe_accessor("gvz")
class GeosnapAccessor:
    def __init__(self, pandas_obj):
        self._validate(pandas_obj)
        self._obj = pandas_obj

    @staticmethod
    def _validate(obj):
        # verify there is a column latitude and a column longitude
        if not isinstance(obj, gpd.GeoDataFrame):
            raise AttributeError("must be a geodataframe")

    def explore(
        self,
        column=None,
        cmap=None,
        scheme=None,
        k=6,
        categorical=False,
        elevation=None,
        extruded=False,
        elevation_scale=1,
        alpha=1,
        layer_kwargs=None,
        map_kwargs=None,
        classify_kwargs=None,
        nan_color=[255, 255, 255, 255],
        color=None,
        wireframe=False,
        tiles="CartoDB Darkmatter",
    ):
        """explore a dataframe using lonboard and deckgl

        Parameters
        ----------
        gdf : geopandas.GeoDataFrame
            dataframe to visualize
        column : str, optional
            name of column on dataframe to visualize on map, by default None
        cmap : str, optional
            name of matplotlib colormap to , by default None
        scheme : str, optional
            name of a classification scheme defined by mapclassify.Classifier, by default
            None
        k : int, optional
            number of classes to generate, by default 6
        categorical : bool, optional
            whether the data should be treated as categorical or continuous, by default
            False
        elevation : str or array, optional
            name of column on the dataframe used to extrude each geometry or  an array-like
            in the same order as observations, by default None
        extruded : bool, optional
            whether to extrude geometries using the z-dimension, by default False
        elevation_scale : int, optional
            constant scaler multiplied by elevation valuer, by default 1
        alpha : float, optional
            alpha (opacity) parameter in the range (0,1) passed to
            mapclassify.util.get_color_array, by default 1
        layer_kwargs : dict, optional
            additional keyword arguments passed to lonboard.viz layer arguments (either
            polygon_kwargs, scatterplot_kwargs, or path_kwargs, depending on input
            geometry type), by default None
        map_kwargs : dict, optional
            additional keyword arguments passed to lonboard.viz map_kwargs, by default
            None
        classify_kwargs : dict, optional
            additional keyword arguments passed to `mapclassify.classify`, by default
            None
        nan_color : list-like, optional
            color used to shade NaN observations formatted as an RGBA list, by
            default [255, 255, 255, 255]
        color : str or array-like, optional
            single or array of colors passed to `lonboard.Layer` object (get_color if
            input dataframe is linestring, or get_fill_color otherwise. By default None
        wireframe : bool, optional
            whether to use wireframe styling in deckgl, by default False
        tiles : str or lonboard.basemap
            either a known string {"CartoDB Positron", "CartoDB Positron No Label",
            "CartoDB Darkmatter", "CartoDB Darkmatter No Label", "CartoDB Voyager",
            "CartoDB Voyager No Label"} or a lonboard.basemap object, or a string to a
            maplibre style basemap.

        Returns
        -------
        lonboard.Map
            a lonboard map with geodataframe included as a Layer object.
        """
        return _dexplore(
            self._obj,
            column,
            cmap,
            scheme,
            k,
            categorical,
            elevation,
            extruded,
            elevation_scale,
            alpha,
            layer_kwargs,
            map_kwargs,
            classify_kwargs,
            nan_color,
            color,
            wireframe,
            tiles,
        )


def _dexplore(
    gdf,
    column=None,
    cmap=None,
    scheme=None,
    k=6,
    categorical=False,
    elevation=None,
    extruded=False,
    elevation_scale=1,
    alpha=1,
    layer_kwargs=None,
    map_kwargs=None,
    classify_kwargs=None,
    nan_color=[255, 255, 255, 255],
    color=None,
    wireframe=False,
    tiles="CartoDB Darkmatter",
):
    """explore a dataframe using lonboard and deckgl

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        dataframe to visualize
    column : str, optional
        name of column on dataframe to visualize on map, by default None
    cmap : str, optional
        name of matplotlib colormap to , by default None
    scheme : str, optional
        name of a classification scheme defined by mapclassify.Classifier, by default
        None
    k : int, optional
        number of classes to generate, by default 6
    categorical : bool, optional
        whether the data should be treated as categorical or continuous, by default
        False
    elevation : str or array, optional
        name of column on the dataframe used to extrude each geometry or  an array-like
        in the same order as observations, by default None
    extruded : bool, optional
        whether to extrude geometries using the z-dimension, by default False
    elevation_scale : int, optional
        constant scaler multiplied by elevation valuer, by default 1
    alpha : float, optional
        alpha (opacity) parameter in the range (0,1) passed to
        mapclassify.util.get_color_array, by default 1
    layer_kwargs : dict, optional
        additional keyword arguments passed to lonboard.viz layer arguments (either
        polygon_kwargs, scatterplot_kwargs, or path_kwargs, depending on input
        geometry type), by default None
    map_kwargs : dict, optional
        additional keyword arguments passed to lonboard.viz map_kwargs, by default None
    classify_kwargs : dict, optional
        additional keyword arguments passed to `mapclassify.classify`, by default None
    nan_color : list-like, optional
        color used to shade NaN observations formatted as an RGBA list, by
        default [255, 255, 255, 255]
    color : str or array-like, optional
        _description_, by default None
    wireframe : bool, optional
        whether to use wireframe styling in deckgl, by default False

    Returns
    -------
    lonboard.Map
        a lonboard map with geodataframe included as a Layer object.

    """
    try:
        from lonboard import basemap, viz
        from lonboard.colormap import apply_continuous_cmap
    except ImportError as e:
        raise ImportError(
            "you must have the lonboard package installed to use this function"
        ) from e
    providers = {
        "CartoDB Positron": basemap.CartoBasemap.Positron,
        "CartoDB Positron No Label": basemap.CartoBasemap.PositronNoLabels,
        "CartoDB Darkmatter": basemap.CartoBasemap.DarkMatter,
        "CartoDB Darkmatter No Label": basemap.CartoBasemap.DarkMatterNoLabels,
        "CartoDB Voyager": basemap.CartoBasemap.Voyager,
        "CartoDB Voyager No Label": basemap.CartoBasemap.VoyagerNoLabels,
    }
    if cmap is None:
        cmap = "Set1" if categorical else "viridis"
    if map_kwargs is None:
        map_kwargs = dict()
    if classify_kwargs is None:
        classify_kwargs = dict()
    if layer_kwargs is None:
        layer_kwargs = dict()
    if isinstance(elevation, str):
        if elevation in gdf.columns:
            elevation = gdf[elevation]
        else:
            raise ValueError(
                f"the designated height column {elevation} is not in the dataframe"
            )

    # only polygons have z
    if ["Polygon", "MultiPolygon"] in gdf.geometry.geom_type.unique():
        layer_kwargs["get_elevation"] = elevation
        layer_kwargs["extruded"] = extruded
        layer_kwargs["elevation_scale"] = elevation_scale
        layer_kwargs["wireframe"] = wireframe

    LINE = False  # set color of lines, not fill_color
    if ["LineString", "MultiLineString"] in gdf.geometry.geom_type.unique():
        LINE = True
    if color:
        if LINE:
            layer_kwargs["get_color"] = color
        else:
            layer_kwargs["get_fill_color"] = color
    if column is not None:
        if column not in gdf.columns:
            raise ValueError(f"the designated column {column} is not in the dataframe")
        if categorical:
            color_array = _get_categorical_cmap(gdf[column], cmap, nan_color)
        elif scheme is None:
            # minmax scale the column first, matplotlib needs 0-1
            transformed = (gdf[column] - np.nanmin(gdf[column])) / (
                np.nanmax(gdf[column]) - np.nanmin(gdf[column])
            )
            color_array = apply_continuous_cmap(
                values=transformed, cmap=colormaps[cmap], alpha=alpha
            )
        else:
            color_array = get_color_array(
                gdf[column],
                scheme=scheme,
                k=k,
                cmap=cmap,
                alpha=alpha,
                nan_color=nan_color,
                **classify_kwargs,
            )

        if LINE:
            layer_kwargs["get_color"] = color_array

        else:
            layer_kwargs["get_fill_color"] = color_array
    if tiles:
        map_kwargs["basemap_style"] = providers[tiles]
    m = viz(
        gdf,
        polygon_kwargs=layer_kwargs,
        scatterplot_kwargs=layer_kwargs,
        path_kwargs=layer_kwargs,
        map_kwargs=map_kwargs,
    )

    return m


def _get_categorical_cmap(categories, cmap, nan_color):
    try:
        from lonboard.colormap import apply_categorical_cmap
    except ImportError as e:
        raise ImportError(
            "this function requres the lonboard package to be installed"
        ) from e

    categories = categories.copy()
    unique_cats = categories.dropna().unique()
    n_cats = len(unique_cats)
    if isinstance(colormaps[cmap], LinearSegmentedColormap):
        colors = colormaps[cmap].resampled(n_cats)(list(range(n_cats)))
    else:
        colors = colormaps[cmap].resampled(n_cats).colors
    colors = (np.array(colors) * 255).astype(int)
    colors = np.vstack([colors, nan_color])

    cat_ints = list(range(1, n_cats + 1))
    n_colors = colors.shape[0]
    nan_place = n_cats + 1
    cat_to_int = dict(zip(unique_cats, cat_ints))
    categories = categories.fillna(nan_place)
    categories = categories.replace(cat_to_int).astype(int)
    if n_cats > n_colors:
        warn(
            "the number of unique categories exceeds the number of available colors",
            stacklevel=3,
        )
        floor = (n_cats // n_colors) + 1
        colors = np.vstack([colors] * floor)
        print(colors.shape)
    cat_ints.append(nan_place)
    temp_cmap = dict(zip(cat_ints, colors))
    fill_color = apply_categorical_cmap(categories, temp_cmap)
    return fill_color