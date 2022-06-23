"""A Community is a thin wrapper around a long-form time-series geodataframe."""
import warnings
from warnings import warn

import numpy as np
import pandas as pd

from ._data import DataStore, _Map
from .analyze import cluster as _cluster
from .analyze import predict_markov_labels as _predict_labels
from .analyze import regionalize as _cluster_spatial
from .analyze import sequence as _sequence
from .analyze import transition as _transition
from .harmonize import harmonize as _harmonize
from .io import get_census as _get_census
from .io import get_lodes as _get_lodes
from .io import get_ltdb as _get_ltdb
from .io import get_ncdb as _get_ncdb
from .visualize import animate_timeseries as _animate_timeseries
from .visualize import plot_timeseries as _plot_timeseries
from .visualize import plot_transition_graphs as _plot_transition_graphs
from .visualize import plot_transition_matrix as _plot_transitions

warnings.simplefilter("always", UserWarning)


def _implicit_storage_deprecation(store):
    if store is None:
        warn(
            "Creating a community from an uninstantiated datastore is deprecated and will raise an error in future versions.  "
            "Please use `datastore=geosnap.io.DataStore` and pass it to the Community constructor",
            DeprecationWarning,
        )
        return DataStore()
    return store


class Community:
    """Spatial and tabular data for a collection of "neighborhoods" over time.

       A community is a collection of "neighborhoods" represented by spatial
       boundaries (e.g. census tracts, or blocks in the US), and tabular data
       which describe the composition of each neighborhood (e.g. data from
       surveys, sensors, or geocoded misc.). A Community can be large (e.g. a
       metropolitan region), or small (e.g. a handfull of census tracts) and
       may have data pertaining to multiple discrete points in time.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        long-form geodataframe that holds spatial and tabular data.
    harmonized : bool
        Whether neighborhood boundaries have been harmonized into a set of
        time-consistent units

    Attributes
    ----------
    gdf : geopandas.GeoDataFrame
        long-form geodataframe that stores neighborhood-level attributes
        and geometries for one or more time periods
    harmonized : bool
        Whether neighborhood boundaries have been harmonized into
        consistent units over time
    models : dict of geosnap.analyze.ModelResults
        Dictionary of model instances that have been fitted on the community.
        The model name is the key and the value is an instance of geosnap.analyze.ModelResults.
        For cluster models, the model name will match a column on the Community.gdf.

    """

    def __init__(self, gdf=None, harmonized=None, **kwargs):
        """Initialize a new Community.

        Parameters
        ----------
        gdf : geopandas.GeoDataFrame
            long-form geodataframe that stores neighborhood-level attributes
            and geometries for one or more time periods
        harmonized : bool
            Whether neighborhood boundaries have been harmonized into
            consistent units over time
        **kwargs : kwargs
            extra keyword arguments `**kwargs`.

        """
        self.gdf = gdf
        self.harmonized = harmonized
        self.models = _Map()

    def harmonize(
        self,
        target_year=None,
        weights_method="area",
        extensive_variables=None,
        intensive_variables=None,
        allocate_total=True,
        raster=None,
        pixel_values="developed",
        temporal_index='year',
        unit_index=None
    ):
        """Standardize inconsistent boundaries into time-static ones.

        Parameters
        ----------
        target_year: int
            Polygons from this year will become the target boundaries for
            spatial interpolation.
        weights_method : string
            The method that the harmonization will be conducted. This can be set to

            * area :         harmonization using simple area-weighted interprolation.
            * dasymetric :   harmonization using area-weighted interpolation with raster-based
                             ancillary data such as <https://www.mrlc.gov/data/nlcd-2016-land-cover-conus>
                             to mask out uninhabited land.
        extensive_variables : list
            The names of variables in each dataset of raw_community that contains
            extensive variables to be harmonized (see (2) in Notes).
        intensive_variables : list
            The names of variables in each dataset of raw_community that contains
            intensive variables to be harmonized (see (2) in Notes).
        allocate_total : bool
            True if total value of source area should be allocated.
            False if denominator is area of i. Note that the two cases
            would be identical when the area of the source polygon is
            exhausted by intersections. See (3) in Notes for more details.
        raster : str
            the path to a local raster image to be used as a dasymetric mask. If using
            "dasymetric" as the weights method, this is a required argument.
        codes : list of ints
            list of raster pixel values that should be considered as
            'populated'. Default values are consistent with the National Land Cover
            Database (NLCD), and include

            * 21 (Developed, Open Space)
            * 22 (Developed, Low Intensity)
            * 23 (Developed, Medium Intensity)
            * 24 (Developed, High Intensity)

            The description of each code can be found here:
            <https://www.mrlc.gov/sites/default/files/metadata/landcover.html>
            Ignored if not using dasymetric harmonizatiton.
        force_crs_match : bool. Default is True.
            Wheter the Coordinate Reference System (CRS) of the polygon will be
            reprojected to the CRS of the raster file. It is recommended to
            leave this argument True.
            Only taken into consideration for harmonization raster based.

        Notes
        -----
        1) A quick explanation of extensive and intensive variables can be found
        here: <http://ibis.geog.ubc.ca/courses/geob370/notes/intensive_extensive.htm>

        2) For an extensive variable, the estimate at target polygon j (default case) is:

            v_j = \sum_i v_i w_{i,j}

            w_{i,j} = a_{i,j} / \sum_k a_{i,k}

            If the area of the source polygon is not exhausted by intersections with
            target polygons and there is reason to not allocate the complete value of
            an extensive attribute, then setting allocate_total=False will use the
            following weights:

            v_j = \sum_i v_i w_{i,j}

            w_{i,j} = a_{i,j} / a_i

            where a_i is the total area of source polygon i.

            For an intensive variable, the estimate at target polygon j is:

            v_j = \sum_i v_i w_{i,j}

            w_{i,j} = a_{i,j} / \sum_k a_{k,j}

        Returns
        -------
        None
            New data are added to the input Community

        """
        if pixel_values == "developed":
            pixel_values = [21, 22, 23, 24]
        gdf = _harmonize(
            self.gdf,
            target_year=target_year,
            weights_method=weights_method,
            extensive_variables=extensive_variables,
            intensive_variables=intensive_variables,
            allocate_total=allocate_total,
            raster=raster,
            pixel_values=pixel_values,
            temporal_index=temporal_index,
        )
        return Community(gdf.reset_index(), harmonized=True, unit_index='id')

    def cluster(
        self,
        n_clusters=6,
        method=None,
        best_model=False,
        columns=None,
        verbose=False,
        scaler="std",
        pooling="fixed",
        temporal_index="year",
        unit_index="geoid",
        random_state=None,
        cluster_kwargs=None,
        model_colname=None
    ):
        """Create a geodemographic typology by running a cluster analysis on the study area's neighborhood attributes.

        Parameters
        ----------
        n_clusters : int, required
            the number of clusters to model. The default is 6).
        method : str in ['kmeans', 'ward', 'affinity_propagation', 'spectral', 'gaussian_mixture', 'hdbscan'], required
            the clustering algorithm used to identify neighborhood types
        best_model : bool, optional
            if using a gaussian mixture model, use BIC to choose the best
            n_clusters. (the default is False).
        columns : array-like, required
            subset of columns on which to apply the clustering
        verbose : bool, optional
            whether to print warning messages (the default is False).
        temporal_index : str
            which column on the dataframe defines time and or sequencing of the
            long-form data. Default is "year"
        unit_index : str
            which column on the long-form dataframe identifies the stable units
            over time. In a wide-form dataset, this would be the unique index.
            Default is "geoid"
        scaler : None or scaler from sklearn.preprocessing, optional
            a scikit-learn preprocessing class that will be used to rescale the
            data. Defaults to sklearn.preprocessing.StandardScaler
        pooling : ["fixed", "pooled", "unique"], optional (default='fixed')
            How to treat temporal data when applying scaling. Options include:

            * fixed : scaling is fixed to each time period
            * pooled : data are pooled across all time periods
            * unique : if scaling, apply the scaler to each time period, then generate clusters unique to each time period.
        model_colname : str
            column name for storing cluster labels on the output dataframe. If no name is provided,
            the colun will be named after the clustering method. If there is already a column
            named after the clustering method, the name will be incremented with a number

        Returns
        -------
        geosnap.Community
            a copy of input Community with neighborhood cluster labels appended
            as a new column. If the cluster is already present, the name will be incremented

        """
        if not cluster_kwargs:
            cluster_kwargs = dict()
        harmonized = self.harmonized
        gdf, model = _cluster(
            gdf=self.gdf.copy(),
            n_clusters=n_clusters,
            method=method,
            best_model=best_model,
            columns=columns,
            verbose=verbose,
            scaler=scaler,
            pooling=pooling,
            temporal_index=temporal_index,
            unit_index=unit_index,
            random_state=random_state,
            cluster_kwargs=cluster_kwargs,
            return_model=True,
            model_colname=model_colname
            
        )

        comm = Community(gdf, harmonized=harmonized)
        comm.models.update(
            self.models
        )  # keep any existing models in the input Community
        comm.models[model.name] = model
        return comm

    def regionalize(
        self,
        n_clusters=6,
        spatial_weights="rook",
        method=None,
        columns=None,
        threshold_variable="count",
        threshold=10,
        unit_index="geoid",
        temporal_index="year",
        scaler="std",
        weights_kwargs=None,
        region_kwargs=None,
        model_colname=None
    ):
        """Create a *spatial* geodemographic typology by running a cluster analysis on the metro area's neighborhood attributes and including a contiguity constraint.

        Parameters
        ----------
        n_clusters : int, required
            the number of clusters to model. The default is 6).
        spatial_weights : str ('queen' or 'rook') or libpysal.weights.W instance, optional
            spatial weights matrix specification` (the default is "rook"). If 'rook' or 'queen'
            then contiguity weights will be constructed internally, otherwise pass a
            libpysal.weights.W with additional arguments specified in weights_kwargs
        weights_kwargs : dict, optional
            If passing a libpysal.weights.W instance to spatial_weights, these additional
            keyword arguments that will be passed to the weights constructor
        method : str in ['ward_spatial', 'spenc', 'skater', 'azp', 'max_p'], required
            the clustering algorithm used to identify neighborhood types
        columns : array-like, required
            subset of columns on which to apply the clustering
        threshold_variable : str, required if using max-p, optional otherwise
            for max-p, which variable should define `p`. The default is "count",
            which will grow regions until the threshold number of polygons have
            been aggregated
        threshold : numeric, optional
            threshold to use for max-p clustering (the default is 10).
        temporal_index : str
            which column on the dataframe defines time and or sequencing of the
            long-form data. Default is "year"
        unit_index : str
            which column on the long-form dataframe identifies the stable units
            over time. In a wide-form dataset, this would be the unique index.
            Default is "geoid"
        scaler : None or scaler from sklearn.preprocessing, optional
            a scikit-learn preprocessing class that will be used to rescale the
            data. Defaults to sklearn.preprocessing.StandardScaler
        model_colname : str
            column name for storing cluster labels on the output dataframe. If no name is provided,
            the colun will be named after the clustering method. If there is already a column
            named after the clustering method, the name will be incremented with a number

        Returns
        -------
        geosnap.Community
            a copy of input Community with neighborhood cluster labels appended
            as a new column. If the cluster is already present, the name will be incremented


        """
        harmonized = self.harmonized
        if not region_kwargs:
            region_kwargs = dict()

        gdf, models = _cluster_spatial(
            gdf=self.gdf.copy(),
            n_clusters=n_clusters,
            spatial_weights=spatial_weights,
            method=method,
            columns=columns,
            threshold_variable=threshold_variable,
            threshold=threshold,
            scaler=scaler,
            weights_kwargs=weights_kwargs,
            unit_index=unit_index,
            temporal_index=temporal_index,
            region_kwargs=region_kwargs,
            return_model=True,
            model_colname=model_colname
        )

        comm = Community(gdf, harmonized=harmonized)
        comm.models.update(
            self.models
        )  # keep any existing models in the input Community
        comm.models[models[list(models.keys())[0]].name] = models
        return comm

    def plot_transition_matrix(
        self,
        cluster_col=None,
        w_type="queen",
        w_options=None,
        temporal_index="year",
        unit_index="geoid",
        permutations=0,
        figsize=(13, 12),
        n_rows=3,
        n_cols=3,
        suptitle=None,
        title_kwds=None,
        savefig=None,
        dpi=300,
    ):
        """Plot global and spatially-conditioned transition matrices as heatmaps.

        Parameters
        ----------
        cluster_col : str
            column on the Community.gdf containing neighborhood type labels
        temporal_index : string, optional
            Column defining time and or sequencing of the long-form data.
            Default is "year".
        unit_index : string, optional
            Column identifying the unique id of spatial units.
            Default is "geoid".
        w_type : string, optional
            Type of spatial weights type ("rook", "queen", "knn" or
            "kernel") to be used for spatial structure. Default is
            None, if non-spatial Markov transition rates are desired.
        w_options : dict
            additional options passed to a libpysal weights constructor (e.g. `k` for a KNN weights matrix)
        permutations : int, optional
            number of permutations for use in randomization based
            inference (the default is 0).
        figsize : tuple, optional
            size of the resulting figure (13, 12)
        n_rows : int, optional
            rows in the plot; n_rows * n_cols must be >= the number of neighborhood types
        n_cols : int, optional
            columns in the plot; n_rows * n_cols must be >= the number of neighborhood types
        suptitle : str, optional
            title of the figure
        title_kwds : dict, optional
            additional keyword options for formatting the title
        savefig : str, optional
            location the plot will be saved
        dpi : int, optional
            dpi of the resulting image, default is 300

        Returns
        -------
        matplotlib Axes
            the axes on which the plots are drawn
        """
        ax = _plot_transitions(
            self.gdf,
            cluster_col=cluster_col,
            w_type=w_type,
            w_options=w_options,
            temporal_index=temporal_index,
            unit_index=unit_index,
            permutations=permutations,
            figsize=figsize,
            n_rows=n_rows,
            n_cols=n_cols,
            suptitle=suptitle,
            title_kwds=title_kwds,
            savefig=savefig,
            dpi=dpi,
        )
        return ax

    def plot_transition_graphs(
        self,
        cluster_col=None,
        w_type="queen",
        layout="dot",
        args="-n -Groot=0 -Goverlap=false -Gmindist=3.5 -Gsize=30,30!",
        output_dir=".",
    ):
        """Plot a network graph representation of global and spatially-conditioned transition matrices.

        This function requires pygraphviz to be installed. For linux and macos, it can be installed with
        `conda install -c conda-forge pygraphviz`. At the time of this writing there is no pygraphviz build
        available for Windows from mainstream conda channels, but it can be installed with
        `conda install -c alubbock pygraphviz`

        Parameters
        ----------
        cluster_col : str
            column on the Community.gdf containing neighborhood type labels
        output_dir : str
            the location that output images will be placed
        w_type : str {'queen', 'rook'}
            which type of libpysal spatial weights objects to encode connectivity
        layout : str, 'dot'
            graphviz layout for plotting
        args : str, optional
            additional arguments passed to graphviz.
            default is  "-n -Groot=0 -Goverlap=false -Gnodesep=0.01 -Gfont_size=1 -Gmindist=3.5 -Gsize=30,30!"

        Returns
        ------
        None
        """
        _plot_transition_graphs(
            self.gdf,
            cluster_col=cluster_col,
            w_type=w_type,
            layout=layout,
            args=args,
            output_dir=output_dir,
        )

    def plot_timeseries(
        self,
        column,
        title="",
        temporal_index="year",
        time_subset=None,
        scheme="quantiles",
        k=5,
        pooled=True,
        cmap=None,
        legend=True,
        categorical=False,
        save_fig=None,
        dpi=200,
        legend_kwds="default",
        missing_kwds="default",
        figsize=None,
        ncols=None,
        nrows=None,
        ctxmap="default",
        alpha=1,
        **kwargs,
    ):
        """Plot an attribute from a Community arranged as a timeseries.

        Parameters
        ----------
        Community    : Community object
                       community object
        column       : str
                       column to be graphed in a time series
        title        : str, optional
                       desired title of figure
        years        : list, optional
                       years to be graphed
                       default is every year in dataframe.
        scheme       : string,optional
                       matplotlib scheme to be used
                       default is 'quantiles'
        k            : int, optional
                       number of bins to graph. k may be ignored
                       or unnecessary for some schemes, like headtailbreaks, maxp, and maximum_breaks
                       Default is 5.
        pooled       : bool, optional
                       whether the classification should be pooled across time periods or unique to each.
                       E.g. with a 'quantile' scheme, pooled=True indicates that quantiles should be identified
                       on the entire time series, whereas pooled=False indicates that they should be calculated
                       independently for each time period
        legend       : bool, optional
                       whether to display a legend on the plot
        categorical  : bool, optional
                       whether the data should be plotted as categorical as opposed to continuous
        save_fig     : str, optional
                       path to save figure if desired.
        dpi          : int, optional
                       dpi of the saved image if save_fig=True
                       default is 500
        legend_kwds  : dictionary, optional
                       parameters for the legend
        missing_kwds  : dictionary, optional
                       parameters for the plotting missing data
                       Default is 1 column on the bottom of the graph.
        ncols        : int, optional
                       number of columns in the figure
                       if passing ncols, nrows must also be passed
                       default is None
        nrows        : int, optional
                       number of rows in the figure
                       if passing nrows, ncols must also be passed
                       default is None
        figsize      : tuple, optional
                       the desired size of the matplotlib figure
        ctxmap       : contextily map provider, optional
                       contextily basemap. Set to False for no basemap.
                       Default is Stamen.TonerLite
        alpha : int (optional)
            Transparency parameter passed to matplotlib
        """
        # proplot needs to be used as a function-level import,
        # as it influences all figures when imported at the top of the file
        inputs = locals()
        del inputs["self"]
        axs = _plot_timeseries(self.gdf, **inputs)
        return axs

    def animate_timeseries(
        self,
        column=None,
        filename=None,
        title="",
        temporal_index="year",
        time_periods=None,
        scheme="quantiles",
        k=5,
        cmap=None,
        legend=True,
        alpha=0.6,
        categorical=False,
        dpi=200,
        fps=0.5,
        interval=500,
        repeat_delay=1000,
        title_fontsize=40,
        subtitle_fontsize=38,
        figsize=(20, 20),
        ctxmap="default",
    ):
        """Create an animated gif from a Community timeseries.

        Parameters
        ----------
        column       : str
                       column to be graphed in a time series
        filename     : str, required
                        output file name
        title        : str, optional
                       desired title of figure
        temporal_index     : str, required
                        column on the Community.gdf that stores time periods
        time_periods:  list, optional
                        subset of time periods to include in the animation. If None, then all times will be used
        scheme       : string, optional
                       matplotlib scheme to be used
                       default is 'quantiles'
        k            : int, optional
                       number of bins to graph. k may be ignored
                       or unnecessary for some schemes, like headtailbreaks, maxp, and maximum_breaks
                       Default is 5.
        legend       : bool, optional
                       whether to display a legend on the plot
        categorical  : bool, optional
                       whether the data should be plotted as categorical as opposed to continuous
        alpha:       : float, optional
                       transparency parameter passed to matplotlib
        dpi          : int, optional
                       dpi of the saved image if save_fig=True
                       default is 500
        figsize      : tuple, optional
                       the desired size of the matplotlib figure
        ctxmap       : contextily map provider, optional
                       contextily basemap. Set to False for no basemap.
        figsize      : tuple, optional
                        output figure size passed to matplotlib.pyplot
        fps          : float, optional
                       frames per second, used to speed up or slow down animation
        interval     : int, optional
                       interval between frames in miliseconds, default 500
        repeat_delay : int, optional
                        time before animation repeats in miliseconds, default 1000
        """
        inputs = locals()
        del inputs["self"]
        _animate_timeseries(self.gdf, **inputs)

    def plot_boundary_silhouette(
        self,
        model_name,
        time_periods="all",
        ctxmap="default",
        figsize=None,
        nrows=None,
        ncols=None,
        save_fig=None,
        alpha=0.5,
        cmap="bwr",
        scheme="quantiles",
        k=6,
        title="Boundary Silhouette",
        dpi=500,
        plot_kwargs=None,
        web_mercator=True,
    ):
        inputs = locals()
        del inputs["self"]
        del inputs["model_name"]
        model = self.models[model_name]
        if isinstance(model, dict):
            for key in model.keys():
                ax = model[key].plot_boundary_silhouette(**inputs)
        else:
            ax = model.plot_boundary_silhouette(**inputs)
        return ax

    def plot_path_silhouette(
        self,
        model_name,
        time_periods="all",
        ctxmap="default",
        figsize=None,
        nrows=None,
        ncols=None,
        save_fig=None,
        alpha=0.5,
        cmap="bwr",
        scheme="quantiles",
        k=6,
        title="Path Silhouette",
        dpi=500,
        plot_kwargs=None,
        web_mercator=True,
    ):
        inputs = locals()
        del inputs["self"]
        del inputs["model_name"]
        model = self.models[model_name]
        if isinstance(model, dict):
            for key in model.keys():
                ax = model[key].plot_path_silhouette(**inputs)
        else:
            ax = model.plot_path_silhouette(**inputs)
        return ax

    def plot_silhouette_map(
        self,
        model_name,
        time_periods="all",
        ctxmap="default",
        figsize=None,
        nrows=None,
        ncols=None,
        save_fig=None,
        alpha=0.5,
        cmap="bwr",
        scheme="quantiles",
        k=8,
        title="Silhouette Score",
        dpi=500,
        plot_kwargs=None,
        web_mercator=True,
    ):
        inputs = locals()
        del inputs["self"]
        del inputs["model_name"]
        model = self.models[model_name]
        if isinstance(model, dict):
            for key in model.keys():
                ax = model[key].plot_silhouette_map(**inputs)
        else:
            ax = model.plot_silhouette_map(**inputs)
        return ax

    def plot_next_best_label(
        self,
        model_name,
        time_periods="all",
        ctxmap="default",
        figsize=None,
        nrows=None,
        ncols=None,
        save_fig=None,
        alpha=0.5,
        cmap="set1",
        title="Next-Best Label",
        dpi=500,
        plot_kwargs=None,
        web_mercator=True,
    ):
        inputs = locals()
        del inputs["self"]
        del inputs["model_name"]
        model = self.models[model_name]
        if isinstance(model, dict):
            for key in model.keys():
                ax = model[key].plot_next_best_label(**inputs)
        else:
            ax = model.plot_next_best_label(**inputs)
        return ax

    def transition(
        self,
        cluster_col,
        temporal_index="year",
        unit_index="geoid",
        w_type=None,
        w_options=None,
        permutations=0,
    ):
        """
        (Spatial) Markov approach to transitional dynamics of neighborhoods.

        The transitional dynamics approach should be adopted after
        neighborhood segmentation since the column name of neighborhood
        labels is a required input.

        Parameters
        ----------
        cluster_col : string or int
            Column name for the neighborhood segmentation, such as
            "ward", "kmeans", etc.
        temporal_index : string, optional
            Column defining time and or sequencing of the long-form data.
            Default is "year".
        unit_index : string, optional
            Column identifying the unique id of spatial units.
            Default is "geoid".
        w_type : string, optional
            Type of spatial weights type ("rook", "queen", "knn" or
            "kernel") to be used for spatial structure. Default is
            None, if non-spatial Markov transition rates are desired.
        w_options : dict
            additional options passed to a libpysal weights constructor (e.g. `k` for a KNN weights matrix)
        permutations : int, optional
            number of permutations for use in randomization based
            inference (the default is 0).

        Returns
        ---------
        mar : giddy.markov.Markov or giddy.markov.Spatial_Markov
            if w_type=None, return a classic Markov instance;
            if w_type is given, return a Spatial_Markov instance

        """
        assert unit_index in self.gdf.columns.to_list(), (
            f"unit_index: {unit_index} is not in the columns."
            " Please use an appropriate index that properly identifies spatial units."
        )

        mar = _transition(
            self.gdf,
            cluster_col,
            temporal_index=temporal_index,
            unit_index=unit_index,
            w_type=w_type,
            permutations=permutations,
            w_options=w_options,
        )
        return mar

    def sequence(
        self,
        cluster_col,
        seq_clusters=5,
        subs_mat=None,
        dist_type=None,
        indel=None,
        temporal_index="year",
        unit_index="geoid",
    ):
        """
        Pairwise sequence analysis to evaluate the distance/dissimilarity
        between every two neighborhood sequences.

        The sequence approach should be adopted after
        neighborhood segmentation since the column name of neighborhood
        labels is a required input.

        Parameters
        ----------
        cluster_col     : string or int
                          Column name for the neighborhood segmentation, such as
                          "ward", "kmeans", etc.
        seq_clusters    : int, optional
                          Number of neighborhood sequence clusters. Agglomerative
                          Clustering with Ward linkage is now used for clustering
                          the sequences. Default is 5.
        subs_mat        : array
                          (k,k), substitution cost matrix. Should be hollow (
                          0 cost between the same type), symmetric and non-negative.
        dist_type       : string
                          "hamming": hamming distance (substitution only
                          and its cost is constant 1) from sklearn.metrics;
                          "markov": utilize empirical transition
                          probabilities to define substitution costs;
                          "interval": differences between states are used
                          to define substitution costs, and indel=k-1;
                          "arbitrary": arbitrary distance if there is not a
                          strong theory guidance: substitution=0.5, indel=1.
                          "tran": transition-oriented optimal matching. Sequence of
                          transitions. Based on :cite:`Biemann:2011`.
        indel           : float, optional
                          insertion/deletion cost.
        temporal_index   : string, optional
                          Column defining time and or sequencing of the long-form data.
                          Default is "year".
        unit_index       : string, optional
                          Column identifying the unique id of spatial units.
                          Default is "geoid".

        Returns
        -------
        gdf_new         : Community instance
                          New Community instance with attribute "gdf" having
                          a new column for sequence labels.
        df_wide         : pandas.DataFrame
                          Wide-form DataFrame with k (k is the number of periods)
                          columns of neighborhood types and 1 column of sequence
                          labels.
        seq_dis_mat     : array
                          (n,n), distance/dissimilarity matrix for each pair of
                          sequences

        """
        gdf_temp, df_wide, seq_dis_mat = _sequence(
            self.gdf,
            cluster_col,
            seq_clusters=seq_clusters,
            subs_mat=subs_mat,
            dist_type=dist_type,
            indel=indel,
            temporal_index=temporal_index,
            unit_index=unit_index,
        )
        gdf_new = Community(gdf_temp)
        return gdf_new, df_wide, seq_dis_mat

    def simulate(
        self,
        model_name=None,
        unit_index="geoid",
        w_type="queen",
        w_options=None,
        base_year=2010,
        new_colname="predicted",
        increment=10,
        time_steps=3,
        temporal_index="year",
        seed=None,
    ):
        """Simulate community dynamics using spatial Markov transition rules.

        Parameters
        ----------
        model_name : [type], optional
            [description], by default None
        unit_index : str, optional
            column on the community gdf that denotes the unique index of geographic units
            for U.S. census data this is "geoid" (which is the default)
        w_type : str {'queen', 'rook'}
            which type of libpysal spatial weights objects to encode connectivity
        w_options : dict
            additional options passed to a libpysal weights constructor (e.g. `k` for a KNN weights matrix)
        base_year : int, optional
            time period to begin the simulation. Typically this is the last time period for which
            labels have been estimated by a cluster model.
        new_colname : str, optional
            name of new column holding predicted neighorhood labels. Default is "predicted"
        increment : int, optional
            number of units in each time step (e.g. for a model based on decennial census data, this is 10)
        time_steps : int, optional
            number of time periods to simulate
        temporal_index : str, optional
            column on the community gdf that denotes the time index. For builtin data, this is "year"
        seed: int, optional
            seed passed to numpy random number generator

        Returns
        -------
        geosnap.Community if time_steps > 1, else geopandas.GeoDataFrame
            If simulating multiple timesteps, the return is a new Community instance with simulated label values as its gdf.
            If simulating a single time step, the return is a single geodataframe
        """
        assert (
            self.harmonized
        ), "Predictions based on transition models require harmonized data"

        gdf = self.gdf.copy()
        gdf = gdf.dropna(subset=[model_name]).reset_index(drop=True)
        np.random.seed(seed)

        gdfs = _predict_labels(
            self.gdf,
            cluster_col=model_name,
            w_type=w_type,
            w_options=w_options,
            base_year=base_year,
            new_colname=new_colname,
            unit_index=unit_index,
            increment=increment,
            time_steps=time_steps,
            temporal_index=temporal_index,
            seed=seed,
        )
        return Community.from_geodataframes(gdfs=[gdfs])

    ###### Constructor Methods ######
    #################################

    @classmethod
    def from_ltdb(
        cls,
        datastore=None,
        state_fips=None,
        county_fips=None,
        msa_fips=None,
        fips=None,
        boundary=None,
        years="all",
    ):
        """Create a new Community from LTDB data.

           Instiantiate a new Community from pre-harmonized LTDB data. To use
           you must first download and register LTDB data with geosnap using
           the `store_ltdb` function. Pass lists of states, counties, or any
           arbitrary FIPS codes to create a community. All fips code arguments
           are additive, so geosnap will include the largest unique set.
           Alternatively, you may provide a boundary to use as a clipping
           feature.

        Parameters
        ----------
        state_fips : list or str
            string or list of strings of two-digit fips codes defining states
            to include in the study area.
        county_fips : list or str
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        msa_fips : list or str
            string or list of strings of fips codes defining
            MSAs to include in the study area.
        fips : list or str
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        boundary : geopandas.GeoDataFrame
            geodataframe that defines the total extent of the study area.
            This will be used to clip tracts lazily by selecting all
            `GeoDataFrame.representative_point()`s that intersect the
            boundary gdf
        years : list of ints
            list of years (decades) to include in the study data
            (the default "all" is [1970, 1980, 1990, 2000, 2010]).

        Returns
        -------
        Community
            Community with LTDB data


        """
        datastore = _implicit_storage_deprecation(datastore)
        gdf = _get_ltdb(
            datastore,
            state_fips=state_fips,
            county_fips=county_fips,
            msa_fips=msa_fips,
            fips=fips,
            boundary=boundary,
            years=years,
        )

        return cls(gdf=gdf.reset_index(), harmonized=True)

    @classmethod
    def from_ncdb(
        cls,
        datastore=None,
        state_fips=None,
        county_fips=None,
        msa_fips=None,
        fips=None,
        boundary=None,
        years="all",
    ):
        """Create a new Community from NCDB data.

           Instiantiate a new Community from pre-harmonized NCDB data. To use
           you must first download and register LTDB data with geosnap using
           the `store_ncdb` function. Pass lists of states, counties, or any
           arbitrary FIPS codes to create a community. All fips code arguments
           are additive, so geosnap will include the largest unique set.
           Alternatively, you may provide a boundary to use as a clipping
           feature.

        Parameters
        ----------
        state_fips : list or str
            string or list of strings of two-digit fips codes defining states
            to include in the study area.
        county_fips : list or str
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        msa_fips : list or str
            string or list of strings of fips codes defining
            MSAs to include in the study area.
        fips : list or str
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        boundary : geopandas.GeoDataFrame
            geodataframe that defines the total extent of the study area.
            This will be used to clip tracts lazily by selecting all
            `GeoDataFrame.representative_point()`s that intersect the
            boundary gdf
        years : list of ints
            list of years (decades) to include in the study data
            (the default is all available [1970, 1980, 1990, 2000, 2010]).

        Returns
        -------
        Community
            Community with NCDB data

        """
        datastore = _implicit_storage_deprecation(datastore)

        gdf = _get_ncdb(
            datastore=datastore,
            state_fips=state_fips,
            county_fips=county_fips,
            msa_fips=msa_fips,
            fips=fips,
            boundary=boundary,
            years=years,
        )

        return cls(gdf=gdf, harmonized=True)

    @classmethod
    def from_census(
        cls,
        datastore=None,
        state_fips=None,
        county_fips=None,
        msa_fips=None,
        fips=None,
        boundary=None,
        years="all",
        constant_dollars=True,
        currency_year=2015,
    ):
        """Create a new Community from original vintage US Census data.

           Instiantiate a new Community from . To use
           you must first download and register census data with geosnap using
           the `store_census` function. Pass lists of states, counties, or any
           arbitrary FIPS codes to create a community. All fips code arguments
           are additive, so geosnap will include the largest unique set.
           Alternatively, you may provide a boundary to use as a clipping
           feature.

        Parameters
        ----------
        state_fips : list or str, optional
            string or list of strings of two-digit fips codes defining states
            to include in the study area.
        county_fips : list or str, optional
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        msa_fips : list or str, optional
            string or list of strings of fips codes defining
            MSAs to include in the study area.
        fips : list or str, optional
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        boundary : geopandas.GeoDataFrame, optional
            geodataframe that defines the total extent of the study area.
            This will be used to clip tracts lazily by selecting all
            `GeoDataFrame.representative_point()`s that intersect the
            boundary gdf
        years : list of ints, required
            list of years to include in the study data
            (the default is [1990, 2000, 2010]).
        constant_dollars : bool, optional
            whether to standardize currency columns to constant dollars. If true,
            each year will be expressed in dollars set by the `currency_year` parameter
        currency_year : int, optional
            If adjusting for inflation, this parameter sets the year in which dollar values will
            be expressed

        Returns
        -------
        Community
            Community with unharmonized census data

        """
        datastore = _implicit_storage_deprecation(datastore)

        gdf = _get_census(
            datastore,
            state_fips=state_fips,
            county_fips=county_fips,
            msa_fips=msa_fips,
            fips=fips,
            boundary=boundary,
            years=years,
            constant_dollars=constant_dollars,
            currency_year=currency_year,
        )

        return cls(gdf=gdf, harmonized=False)

    @classmethod
    def from_lodes(
        cls,
        datastore=None,
        state_fips=None,
        county_fips=None,
        msa_fips=None,
        fips=None,
        boundary=None,
        years=2015,
        dataset="wac",
    ):
        """Create a new Community from Census LEHD/LODES data.

           Instantiate a new Community from LODES data.
           Pass lists of states, counties, or any
           arbitrary FIPS codes to create a community. All fips code arguments
           are additive, so geosnap will include the largest unique set.
           Alternatively, you may provide a boundary to use as a clipping
           feature.

        Parameters
        ----------
        state_fips : list or str, optional
            string or list of strings of two-digit fips codes defining states
            to include in the study area.
        county_fips : list or str, optional
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        msa_fips : list or str, optional
            string or list of strings of fips codes defining
            MSAs to include in the study area.
        fips : list or str, optional
            string or list of strings of five-digit fips codes defining
            counties to include in the study area.
        boundary : geopandas.GeoDataFrame, optional
            geodataframe that defines the total extent of the study area.
            This will be used to clip tracts lazily by selecting all
            `GeoDataFrame.representative_point()`s that intersect the
            boundary gdf
        years : list of ints, required
            list of years to include in the study data
            (the default is 2015).
        dataset : str, required
            which LODES dataset should be used to create the Community.
            Options are 'wac' for workplace area characteristics or 'rac' for
            residence area characteristics. The default is "wac" for workplace.

        Returns
        -------
        Community
            Community with LODES data

        """
        datastore = _implicit_storage_deprecation(datastore)

        out = _get_lodes(
            datastore=datastore,
            state_fips=state_fips,
            county_fips=county_fips,
            msa_fips=msa_fips,
            fips=fips,
            boundary=boundary,
            years=years,
            dataset=dataset,
        )

        return cls(gdf=out, harmonized=False)

    @classmethod
    def from_geodataframes(cls, gdfs=None):
        """Create a new Community from a list of geodataframes.

        Parameters
        ----------
        gdfs : list-like of geopandas.GeoDataFrames
            list of geodataframes that hold attribute and geometry data for
            a study area. Each geodataframe must have neighborhood
            attribute data, geometry data, and a time column that defines
            how the geodataframes are sequenced. The geometries may be
            stable over time (in which case the dataset is harmonized) or
            may be unique for each time. If the data are harmonized, the
            dataframes must also have an ID variable that indexes
            neighborhood units over time.

        """
        crss = set([gdf.crs for gdf in gdfs])
        assert len(crss) == 1, (
            f"These geodataframes have {len(crss)} different CRS: "
            f"{[i.to_string() for i in crss]}."
            " To continue, reproject the geodataframes into a single consistent system."
            " See: https://geopandas.org/projections.html for more inforamtion."
        )
        gdf = pd.concat(gdfs, sort=True)
        return cls(gdf=gdf)
