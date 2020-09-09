"""A Community is a thin wrapper around a long-form time-series geodataframe."""
import tempfile
from pathlib import PurePath
from warnings import warn

import contextily as ctx
import geopandas as gpd
import mapclassify.classifiers as classifiers
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import scikitplot as skplt

from ._data import _Map, datasets
from .analyze import cluster as _cluster
from .analyze import cluster_spatial as _cluster_spatial
from .analyze import sequence as _sequence
from .analyze import transition as _transition
from .analyze import predict_labels as _predict_labels
from .harmonize import harmonize as _harmonize
from .io import _fips_filter, _fipstable, _from_db, get_lehd
from .util import gif_from_path as _gif_from_path
from .visualize import plot_transition_matrix as _plot_transitions
from .visualize import plot_transition_graphs as _plot_transition_graphs

schemes = {}
for classifier in classifiers.CLASSIFIERS:
    schemes[classifier.lower()] = getattr(classifiers, classifier)


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
    **kwargs


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
        codes="developed",
        force_crs_match=True,
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
        # convert the long-form into a list of dataframes
        # data = [x[1] for x in self.gdf.groupby("year")]
        if codes == "developed":
            codes = [21, 22, 23, 24]
        gdf = _harmonize(
            self.gdf,
            target_year=target_year,
            weights_method=weights_method,
            extensive_variables=extensive_variables,
            intensive_variables=intensive_variables,
            allocate_total=allocate_total,
            raster=raster,
            codes=codes,
            force_crs_match=force_crs_match,
        )
        return Community(gdf, harmonized=True)

    def cluster(
        self,
        n_clusters=6,
        method=None,
        best_model=False,
        columns=None,
        verbose=False,
        scaler="std",
        pooling="fixed",
        **kwargs,
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
        scaler : None or scaler from sklearn.preprocessing, optional
            a scikit-learn preprocessing class that will be used to rescale the
            data. Defaults to sklearn.preprocessing.StandardScaler
        pooling : ["fixed", "pooled", "unique"], optional (default='fixed')
            How to treat temporal data when applying scaling. Options include:

            * fixed : scaling is fixed to each time period
            * pooled : data are pooled across all time periods
            * unique : if scaling, apply the scaler to each time period, then generate clusters unique to each time period.

        Returns
        -------
        geosnap.Community
            a copy of input Community with neighborhood cluster labels appended
            as a new column. If the cluster is already present, the name will be incremented

        """
        harmonized = self.harmonized
        gdf, model, model_name = _cluster(
            gdf=self.gdf.copy(),
            n_clusters=n_clusters,
            method=method,
            best_model=best_model,
            columns=columns,
            verbose=verbose,
            scaler=scaler,
            pooling=pooling,
            **kwargs,
        )

        comm = Community(gdf, harmonized=harmonized)
        comm.models.update(
            self.models
        )  # keep any existing models in the input Community
        comm.models[model_name] = model
        return comm

    def cluster_spatial(
        self,
        n_clusters=6,
        spatial_weights="rook",
        method=None,
        best_model=False,
        columns=None,
        threshold_variable="count",
        threshold=10,
        return_model=False,
        scaler=None,
        weights_kwargs=None,
        **kwargs,
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
        scaler : None or scaler from sklearn.preprocessing, optional
            a scikit-learn preprocessing class that will be used to rescale the
            data. Defaults to sklearn.preprocessing.StandardScaler

        Returns
        -------
        geosnap.Community
            a copy of input Community with neighborhood cluster labels appended
            as a new column. If the cluster is already present, the name will be incremented


        """
        harmonized = self.harmonized

        gdf, model, model_name = _cluster_spatial(
            gdf=self.gdf.copy(),
            n_clusters=n_clusters,
            spatial_weights=spatial_weights,
            method=method,
            best_model=best_model,
            columns=columns,
            threshold_variable=threshold_variable,
            threshold=threshold,
            return_model=return_model,
            scaler=scaler,
            weights_kwargs=weights_kwargs,
            **kwargs,
        )

        comm = Community(gdf, harmonized=harmonized)
        comm.models.update(
            self.models
        )  # keep any existing models in the input Community
        comm.models[model_name] = model
        return comm

    def plot_transition_matrix(
        self,
        cluster_col=None,
        w_type="queen",
        w_options=None,
        figsize=(13, 12),
        n_rows=3,
        n_cols=3,
        suptitle=None,
        savefig=None,
        dpi=300,
        **kwargs,
    ):
        """Plot global and spatially-conditioned transition matrices as heatmaps

        Parameters
        ----------
        cluster_col : str
            column on the Community.gdf containing neighborhood type labels
        w_type : str {'queen', 'rook'}
            which type of libpysal spatial weights objects to encode connectivity
        w_options : dict
            additional options passed to a libpysal weights constructor (e.g. `k` for a KNN weights matrix)
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
            self,
            cluster_col=cluster_col,
            w_type=w_type,
            w_options=w_options,
            figsize=figsize,
            n_rows=n_rows,
            n_cols=n_cols,
            suptitle=suptitle,
            savefig=savefig,
            dpi=dpi,
            **kwargs,
        )
        return ax

    def plot_transition_graphs(
        self,
        cluster_col=None,
        w_type='queen',
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
            self,
            cluster_col=cluster_col,
            w_type=w_type,
            layout=layout,
            args=args,
            output_dir=output_dir,
        )

    def plot_silhouette(self, model_name=None, year=None, **kwargs):
        """Make silhouette plot of the Community model.

        Parameters
        ----------
        model_name : str , required
                     model to be silhouette plotted
        year       : int, optional
                     year to be plotted if model created with pooling=='unique'
        kwargs     : **kwargs, optional
                     pass through to plot_silhouette()
        Returns
        -------
        silhouette plot of given model.

        """
        if not year:
            fig = skplt.metrics.plot_silhouette(
                self.models[model_name].X.values,
                self.models[model_name].labels,
                **kwargs,
            )
        else:
            fig = skplt.metrics.plot_silhouette(
                self.models[model_name][year].X.values,
                self.models[model_name][year].labels,
                **kwargs,
            )
        return fig

    def plot_silhouette_map(
        self,
        model_name=None,
        year=None,
        ctxmap=ctx.providers.Stamen.TonerLite,
        save_fig=None,
        figsize=(12, 3),
        alpha=0.5,
        cmap="bwr",
        title="",
        dpi=500,
        time_var="year",
        id_var="geoid",
        **kwargs,
    ):
        """Plot of the silhouette scores of a Community model.

        Parameters
        ----------
        model_name : str , required
                     model to be plotted
        year       : int, optional
                     year to be plotted if model created with pooling=='unique'
        ctxmap     : contextily map provider, optional
                     contextily basemap. Set to False for no basemap.
                     Default is ctx.providers.Stamen.TonerLite
        save_fig   : str, optional
                     path to save figure if desired.
        figsize    : tuple, optional
                     an order tuple where x is width and y is height
                     default is 12 inches wide and 3 inches high
        alpha      : float, optional
                     how transparent the plotted objects are
                     Default is 0.5
        cmap       : string, optional
                     cmap to be plotted
                     default is 'bwr'
        title      : string, optional
                     title of figure
                     default is no title
        dpi        : int, optional
                     dpi of the saved image if save_fig=True
                    default is 500
        time_var   : string, optional
                     the column in the community gdf that identifies time period
                     default is 'year' from US census data
        id_var     : string, optional
                     column in gdf that identifies geographic units
                     default is 'geoid' from US census data
        kwargs     : **kwargs, optional
                     pass through to matplotlib pyplot
        Returns
        -------
        silhouette scores mapped onto community geography

        """
        # Check for and use previously calculated values for graphs
        # Checking both arrays at the same time would be more efficient, but
        # comparing NumPy arrays with `and` is not allowed, and many solutions that try to compare numpy arrays
        # directly require error handling, so check if objects contain numpy arrays separately.
        df = self.gdf.copy()
        if not year:
            if self.models[model_name].silhouettes is None:
                self.models[model_name].sil_scores()
        else:
            if self.models[model_name][year].silhouettes is None:
                self.models[model_name][year].sil_scores()
        f, ax = plt.subplots(1, 2, figsize=figsize)
        if ctxmap:  # need to convert crs to mercator before graphing
            if df.crs != 3857:
                df = df.to_crs(epsg=3857)
        if not year:
            ax[0].hist(self.models[model_name].silhouettes["silhouettes"])
            df.join(self.models[model_name].silhouettes, on=[id_var, time_var]).plot(
                "silhouettes",
                ax=ax[1],
                alpha=alpha,
                legend=True,
                vmin=-1,
                vmax=1,
                cmap=cmap,
                **kwargs,
            )
            if ctxmap:
                ctx.add_basemap(ax[1], source=ctxmap)
        else:
            ax[0].hist(self.models[model_name][year].silhouettes["silhouettes"])
            df[df.year == year].join(
                self.models[model_name][year].silhouettes, on=[id_var, time_var]
            ).plot(
                "silhouettes",
                ax=ax[1],
                alpha=alpha,
                legend=True,
                vmin=-1,
                vmax=1,
                cmap=cmap,
                **kwargs,
            )
            if ctxmap:
                ctx.add_basemap(ax[1], source=ctxmap)
        ax[1].axis("off")
        #  using both tight_layout() and passing title makes plots and title overlap, so only use one
        if title:
            f.suptitle(title)
        else:
            f.tight_layout()
        if save_fig:
            f.savefig(save_fig, dpi=dpi, bbox_inches="tight")
        return ax

    def plot_next_best_label(
        self,
        model_name=None,
        year=None,
        ctxmap=ctx.providers.Stamen.TonerLite,
        save_fig=None,
        figsize=(12, 3),
        title="",
        alpha=0.5,
        dpi=500,
        time_var="year",
        id_var="geoid",
        **kwargs,
    ):
        """Plot the nearest_labels of the community model.

        Parameters
        ----------
        model_name : str , required
                     model to be plotted
        year       : int, optional
                     year to be plotted if model created with pooling=='unique'
        ctxmap     : contextily map provider, optional
                     contextily basemap. Set to False for no basemap.
                     Default is ctx.providers.Stamen.TonerLite
        save_fig   : str, optional
                     path to save figure if desired.
        figsize    : tuple, optional
                     an order tuple where x is width and y is height
                     default is 12 inches wide and 3 inches high
        title      : string, optional
                     title of figure
                     default is no title
        alpha      : float, optional
                     how transparent the plotted objects are
                     Default is 0.5
        dpi        : int, optional
                     dpi of the saved image if save_fig=True
                     default is 500
        time_var   : string, optional
                     the column in the community gdf that identifies time period
                     default is 'year' from US census data
        id_var     : string, optional
                     column in gdf that identifies geographic units
                     default is 'geoid' from US census data
        kwargs     : **kwargs, optional
                     pass through to matplotlib pyplot
        Returns
        -------
        nearest_labels scores of the passed model plotted onto community geography
        and an array made up of the the model labels and nearest labels that was used to graph the values

        """
        df = self.gdf.copy()
        if isinstance(self.models[model_name], dict) and not year:
            raise InputError(
                "This model has unique results for each time period; You must supply a value for `year`"
            )

        # If the user has already calculated, respect already calculated values
        if not year:
            if self.models[model_name].nearest_labels is None:
                self.models[model_name].nearest_label().astype(int)
        else:
            if self.models[model_name][year].nearest_labels is None:
                self.models[model_name][year].nearest_label().astype(int)
        f, ax = plt.subplots(1, 2, figsize=figsize)
        if ctxmap:
            if df.crs == 3857:
                pass
            else:  # need to convert crs to mercator before graphing
                df = df.to_crs(epsg=3857)
        if not year:
            temp_df = df.join(
                self.models[model_name].nearest_labels, on=[id_var, time_var]
            )
            temp_df = temp_df[["nearest_label", "geometry", model_name]]
            temp_df.set_index(model_name, inplace=True)
            df.plot(model_name, ax=ax[0], alpha=0.5, legend=True, categorical=True)
            temp_df.plot(
                "nearest_label",
                ax=ax[1],
                legend=True,
                categorical=True,
                alpha=alpha,
                **kwargs,
            )
            if ctxmap:
                ctx.add_basemap(ax[0], source=ctxmap)
                ctx.add_basemap(ax[1], source=ctxmap)
        else:
            temp_df = df.join(
                self.models[model_name][year].nearest_labels, on=[id_var, time_var]
            )
            temp_df = temp_df[["nearest_label", time_var, "geometry", model_name]]
            temp_df.set_index(model_name, inplace=True)
            df[df.year == year].plot(
                model_name, ax=ax[0], alpha=alpha, legend=True, categorical=True
            )
            temp_df[temp_df.year == year].plot(
                "nearest_label",
                ax=ax[1],
                alpha=alpha,
                legend=True,
                categorical=True,
                **kwargs,
            )
            if ctxmap:
                ctx.add_basemap(ax[0], source=ctxmap)
                ctx.add_basemap(ax[1], source=ctxmap)
        ax[0].axis("off")
        ax[1].axis("off")
        if title:
            f.suptitle(title)
        else:
            f.tight_layout()
        if save_fig:
            f.savefig(save_fig, dpi=dpi, bbox_inches="tight")
        return ax

    def plot_path_silhouette(
        self,
        model_name=None,
        year=None,
        ctxmap=ctx.providers.Stamen.TonerLite,
        save_fig=None,
        figsize=(12, 3),
        title="",
        alpha=0.5,
        cmap="bwr",
        dpi=500,
        time_var="year",
        id_var="geoid",
        **kwargs,
    ):
        """Plot the path_silhouettes of Commmunity model.

        Parameters
        ----------
        model_name : str , required
                     model to be plotted
        year       : int, optional
                     year to be plotted if model created with pooling=='unique'
        ctxmap     : contextily map provider, optional
                     contextily basemap. Set to False for no basemap.
                     Default is ctx.providers.Stamen.TonerLite
        save_fig   : str, optional
                     path to save figure if desired.
        figsize    : tuple, optional
                     an order tuple where x is width and y is height
                     default is 12 inches wide and 3 inches high
        title      : string, optional
                     title of figure
                     default is no title
        alpha      : float, optional
                     how transparent the plotted objects are
                     Default is 0.5
        cmap       : string, optional
                     cmap to be plotted
                     default is 'bwr'
        dpi        : int, optional
                     dpi of the saved image if save_fig=True
                     default is 500
        time_var   : string, optional
                     the column in the community gdf that identifies time period
                     default is 'year' from US census data
        id_var     : string, optional
                     column in gdf that identifies geographic units
                     default is 'geoid' from US census data
        kwargs     : **kwargs, optional
                     pass through to matplotlib pyplot
        Returns
        -------
        path_silhouette scores of the passed model plotted onto community geography

        """
        if not year:
            if self.models[model_name].path_silhouettes is None:
                self.models[model_name].path_sil()
        else:
            if self.models[model_name][year].path_silhouettes is None:
                self.models[model_name][year].path_sil()
        f, ax = plt.subplots(1, 2, figsize=figsize)
        if ctxmap:  # need to convert crs to mercator before graphing
            self.gdf = self.gdf.to_crs(epsg=3857)
        if not year:
            ax[0].hist(self.models[model_name].path_silhouettes["path_silhouettes"])
            self.gdf.join(
                self.models[model_name][year].path_silhouettes, on=[id_var, time_var]
            ).plot(
                "path_silhouettes",
                ax=ax[1],
                alpha=alpha,
                legend=True,
                vmin=-1,
                vmax=1,
                cmap=cmap,
                **kwargs,
            )
            if ctxmap:
                ctx.add_basemap(ax[1], source=ctxmap)
        else:
            ax[0].hist(
                self.models[model_name][year].path_silhouettes["path_silhouettes"]
            )
            self.gdf[self.gdf.year == year].join(
                self.models[model_name][year].path_silhouettes, on=[id_var, time_var]
            ).plot(
                "path_silhouettes",
                ax=ax[1],
                alpha=alpha,
                legend=True,
                vmin=-1,
                vmax=1,
                cmap=cmap,
                **kwargs,
            )
            if ctxmap:
                ctx.add_basemap(ax[1], source=ctxmap)
        ax[1].axis("off")
        if title:
            f.suptitle(title)
        else:
            f.tight_layout()
        if save_fig:
            f.savefig(save_fig, dpi=dpi, bbox_inches="tight")
        return ax

    def plot_boundary_silhouette(
        self,
        model_name=None,
        year=None,
        ctxmap=ctx.providers.Stamen.TonerLite,
        save_fig=None,
        figsize=(12, 3),
        title="",
        alpha=0.5,
        cmap="bwr",
        dpi=500,
        time_var="year",
        id_var="geoid",
        **kwargs,
    ):
        """Plot boundary_silhouettes of the Commiunity model.

        Parameters
        ----------
        model_name : str , required
                     model to be silhouette plotted
        year       : int, optional
                     year to be plotted if model created with pooling=='unique'
        ctxmap     : contextily map provider, optional
                     contextily basemap. Set to False for no basemap.
                     Default is ctx.providers.Stamen.TonerLite
        figsize    : tuple, optional
                     an order tuple where x is width and y is height
                     default is 12 inches wide and 3 inches high
        title      : string, optional
                     title of figure
                     default is no title
        save_fig   : str, optional
                     path to save figure if desired.
        alpha      : float, optional
                     how transparent the plotted objects are
                     Default is 0.5
        cmap       : string, optional
                     cmap to be plotted
                     default is 'bwr'
        dpi        : int, optional
                     dpi of the saved image if save_fig=True
                     default is 500
        time_var   : string, optional
                     the column in the community gdf that identifies time period
                     default is 'year' from US census data
        id_var     : string, optional
                     column in gdf that identifies geographic units
                     default is 'geoid' from US census data
        kwargs     : **kwargs, optional
                     pass through to matplotlib pyplot
        Returns
        -------
        boundary_silhouette scores of the passed model plotted onto community geography

        """
        # If the user has already calculated , respect already calculated values
        if not year:
            if self.models[model_name].boundary_silhouettes is None:
                self.models[model_name].boundary_sil()
        else:
            if self.models[model_name][year].boundary_silhouettes is None:
                self.models[model_name][year].boundary_sil()
        f, ax = plt.subplots(1, 2, figsize=figsize)
        if ctxmap:  # need to convert crs to mercator before graphing
            self.gdf = self.gdf.to_crs(epsg=3857)
        # To make visualization of boundary_silhouettes informative we need to remove the graphing of zero values
        if not year:
            ax[0].hist(
                self.models[model_name].boundary_silhouettes["boundary_silhouettes"][
                    self.models[model_name].boundary_silhouettes["boundary_silhouettes"]
                    != 0
                ]
            )
            self.gdf.join(
                self.models[model_name][year].boundary_silhouettes,
                on=[id_var, time_var],
            ).plot(
                "boundary_silhouettes",
                ax=ax[1],
                legend=True,
                alpha=alpha,
                vmin=-1,
                vmax=1,
                cmap=cmap,
                **kwargs,
            )
            if ctxmap:
                ctx.add_basemap(ax[1], source=ctxmap)
        else:
            ax[0].hist(
                self.models[model_name][year].boundary_silhouettes[
                    "boundary_silhouettes"
                ][
                    self.models[model_name][year].boundary_silhouettes[
                        "boundary_silhouettes"
                    ]
                    != 0
                ]
            )
            self.gdf[self.gdf.year == year].join(
                self.models[model_name][year].boundary_silhouettes,
                on=[id_var, time_var],
            ).plot(
                "boundary_silhouettes",
                ax=ax[1],
                legend=True,
                alpha=alpha,
                vmin=-1,
                vmax=1,
                cmap=cmap,
                **kwargs,
            )
            if ctxmap:
                ctx.add_basemap(ax[1], source=ctxmap)
        ax[1].axis("off")
        if title:
            f.suptitle(title)
        else:
            f.tight_layout()
        if save_fig:
            f.savefig(save_fig, dpi=dpi, bbox_inches="tight")
        return ax

    def plot_timeseries(
        self,
        column,
        title="",
        years=None,
        scheme="quantiles",
        k=5,
        pooled=True,
        cmap=None,
        legend=True,
        categorical=False,
        save_fig=None,
        dpi=200,
        legend_kwds="default",
        figsize=None,
        ncols=None,
        nrows=None,
        ctxmap=ctx.providers.Stamen.TonerLite,
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
        """
        # proplot needs to be used as a function-level import,
        # as it influences all figures when imported at the top of the file
        import proplot as plot

        if categorical:  # there's no pooled classification for categorical
            pooled = False

        df = self.gdf
        if categorical and not cmap:
            cmap = "Accent"
        elif not cmap:
            cmap = "Blues"
        if legend_kwds == "default":
            legend_kwds = {"ncols": 1, "loc": "b"}
        if ctxmap:  # need to convert crs to mercator before graphing
            if df.crs != 3857:
                df = df.to_crs(epsg=3857)
        if (
            pooled
        ):  # if pooling the classifier, create one from scratch and pass to user defined
            classifier = schemes[scheme](self.gdf[column].dropna().values, k=k)
        if not years:
            if nrows is None and ncols is None:
                f, axs = plot.subplots(ncols=len(df.year.unique()), figsize=figsize)
            else:
                f, axs = plot.subplots(ncols=ncols, nrows=nrows, figsize=figsize)
            for i, year in enumerate(
                sorted(df.year.unique())
            ):  # sort to prevent graphing out of order
                if categorical:
                    df[df.year == year].plot(
                        column=column,
                        ax=axs[i],
                        categorical=True,
                        cmap=cmap,
                        legend=legend,
                        legend_kwds=legend_kwds,
                        missing_kwds={
                            "color": "lightgrey",
                            "edgecolor": "red",
                            "hatch": "///",
                            "label": "Missing values",
                        },
                    )
                else:
                    if pooled:
                        df[df.year == year].plot(
                            column=column,
                            ax=axs[i],
                            scheme="user_defined",
                            classification_kwds={"bins": classifier.bins},
                            k=k,
                            cmap=cmap,
                            **kwargs,
                            legend=legend,
                            legend_kwds=legend_kwds,
                        )
                    else:
                        df[df.year == year].plot(
                            column=column,
                            ax=axs[i],
                            scheme=scheme,
                            k=k,
                            cmap=cmap,
                            **kwargs,
                            legend=legend,
                            legend_kwds=legend_kwds,
                        )
                if ctxmap:  # need set basemap of each graph
                    ctx.add_basemap(axs[i], source=ctxmap)
                axs[i].format(title=year)
        else:
            if nrows is None and ncols is None:
                f, axs = plot.subplots(ncols=len(years))
            else:
                f, axs = plot.subplots(ncols=ncols, nrows=nrows)
            for i, year in enumerate(
                years
            ):  # display in whatever order list is passed in
                if categorical:
                    df[df.year == year].plot(
                        column=column,
                        ax=axs[i],
                        categorical=True,
                        cmap=cmap,
                        legend=legend,
                        legend_kwds=legend_kwds,
                    )
                else:
                    df[df.year == year].plot(
                        column=column,
                        ax=axs[i],
                        scheme=scheme,
                        k=k,
                        cmap=cmap,
                        **kwargs,
                        legend=legend,
                        legend_kwds=legend_kwds,
                    )
                if ctxmap:  # need set basemap of each graph
                    ctx.add_basemap(axs[i], source=ctxmap)
                axs[i].format(title=year)

        if not title:  # only use title when passed
            axs.format(suptitle=column)
        else:
            axs.format(suptitle=title)
        axs.axis("off")

        if save_fig:
            f.savefig(save_fig, dpi=dpi, bbox_inches="tight")
        return axs

    def animate_timeseries(
        self,
        column=None,
        filename=None,
        title="",
        time_col="year",
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
        ctxmap=ctx.providers.Stamen.TonerLite,
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
        time_col     : str, required
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
        gdf = self.gdf.copy()
        if categorical and not cmap:
            cmap = "Accent"
        elif not cmap:
            cmap = "Blues"
        if not gdf.crs == 3857:
            gdf = gdf.to_crs(3857)
        if not time_periods:
            time_periods = gdf[time_col].unique()
        with tempfile.TemporaryDirectory() as tmpdirname:
            for i, time in enumerate(time_periods):
                fig, ax = plt.subplots(figsize=figsize)
                outpath = PurePath(tmpdirname, f"file_{i}.png")
                if categorical:
                    gdf[gdf[time_col] == time].plot(
                        column,
                        categorical=True,
                        ax=ax,
                        alpha=alpha,
                        legend=legend,
                        cmap=cmap,
                    )
                else:
                    classifier = schemes[scheme](gdf[column].dropna().values, k=k)
                    gdf[gdf[time_col] == time].plot(
                        column,
                        scheme="user_defined",
                        classification_kwds={"bins": classifier.bins},
                        k=k,
                        ax=ax,
                        alpha=alpha,
                        legend=legend,
                        cmap=cmap,
                    )
                ctx.add_basemap(ax=ax, source=ctxmap)
                ax.axis("off")
                ax.set_title(f"{time}", fontsize=subtitle_fontsize)
                fig.suptitle(f"{title}", fontsize=title_fontsize)

                plt.tight_layout()
                plt.savefig(outpath, dpi=dpi)

            _gif_from_path(
                tmpdirname,
                interval=interval,
                repeat_delay=repeat_delay,
                filename=filename,
                fps=fps,
                dpi=dpi,
            )

    def transition(
        self, cluster_col, time_var="year", id_var="geoid", w_type=None, permutations=0
    ):
        """
        (Spatial) Markov approach to transitional dynamics of neighborhoods.

        The transitional dynamics approach should be adopted after
        neighborhood segmentation since the column name of neighborhood
        labels is a required input.

        Parameters
        ----------
        cluster_col     : string or int
                          Column name for the neighborhood segmentation, such as
                          "ward", "kmeans", etc.
        time_var        : string, optional
                          Column defining time and or sequencing of the long-form data.
                          Default is "year".
        id_var          : string, optional
                          Column identifying the unique id of spatial units.
                          Default is "geoid".
        w_type          : string, optional
                          Type of spatial weights type ("rook", "queen", "knn" or
                          "kernel") to be used for spatial structure. Default is
                          None, if non-spatial Markov transition rates are desired.
        permutations    : int, optional
                          number of permutations for use in randomization based
                          inference (the default is 0).


        Returns
        ---------
        mar             : giddy.markov.Markov or giddy.markov.Spatial_Markov
                          if w_type=None, return a classic Markov instance;
                          if w_type is given, return a Spatial_Markov instance

        """
        mar = _transition(
            self.gdf,
            cluster_col,
            time_var=time_var,
            id_var=id_var,
            w_type=w_type,
            permutations=permutations,
        )
        return mar

    def sequence(
        self,
        cluster_col,
        seq_clusters=5,
        subs_mat=None,
        dist_type=None,
        indel=None,
        time_var="year",
        id_var="geoid",
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
        time_var        : string, optional
                          Column defining time and or sequencing of the long-form data.
                          Default is "year".
        id_var          : string, optional
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
            time_var=time_var,
            id_var=id_var,
        )
        gdf_new = Community(gdf_temp)
        return gdf_new, df_wide, seq_dis_mat

    def simulate(
        self,
        model_name=None,
        index_col="geoid",
        w_type="queen",
        w_options=None,
        base_year=2010,
        new_colname="predicted",
        increment=10,
        time_steps=3,
        time_col="year",
        seed=None,
    ):
        """Simulate community dynamics using spatial Markov transition rules.

        Parameters
        ----------
        model_name : [type], optional
            [description], by default None
        index_col : str, optional
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
        time_col : str, optional
            column on the community gdf that denotes the time index. For builtin data, this is "year"
        seed: int, optional\
            seed passed to numpy random number generator

        Returns
        -------
        geosnap.Community if time_steps > 1, else geopandas.GeoDataFrame
            If simulating multiple timesteps, the return is a new Community instance with simulated label values as its gdf.
            If simulating a single time step, the return is a single geodataframe
        """
        np.random.seed(seed)
        if time_steps == 1:
            gdf = _predict_labels(
                self,
                model_name=model_name,
                w_type=w_type,
                w_options=w_options,
                base_year=base_year,
                new_colname=new_colname,
                index_col=index_col,
                increment=increment,
                time_steps=time_steps,
                time_col=time_col,
                seed=seed
            )
            return gdf
        else:
            gdfs = _predict_labels(
                self,
                model_name=model_name,
                w_type=w_type,
                w_options=w_options,
                base_year=base_year,
                new_colname=new_colname,
                index_col=index_col,
                increment=increment,
                time_steps=time_steps,
                time_col=time_col,
                seed=seed
            )
            gdfs = pd.concat(gdfs)
            gdfs = gdfs.dropna(subset=[model_name])
            gdfs[model_name] = gdfs[model_name].astype(int)
            return Community.from_geodataframes(gdfs=[gdfs])

    ###### Constructor Methods ######
    #################################

    @classmethod
    def from_ltdb(
        cls,
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
        if years == "all":
            years = [1970, 1980, 1990, 2000, 2010]
        if isinstance(boundary, gpd.GeoDataFrame):
            tracts = datasets.tracts_2010()[["geoid", "geometry"]]
            ltdb = datasets.ltdb().reset_index()
            if boundary.crs != tracts.crs:
                warn(
                    "Unable to determine whether boundary CRS is WGS84 "
                    "if this produces unexpected results, try reprojecting"
                )
            tracts = tracts[
                tracts.representative_point().intersects(boundary.unary_union)
            ]
            gdf = ltdb[ltdb["geoid"].isin(tracts["geoid"])]
            gdf = gpd.GeoDataFrame(gdf.merge(tracts, on="geoid", how="left"))

        else:
            gdf = _from_db(
                data=datasets.ltdb(),
                state_fips=state_fips,
                county_fips=county_fips,
                msa_fips=msa_fips,
                fips=fips,
                years=years,
            )

        return cls(gdf=gdf.reset_index(), harmonized=True)

    @classmethod
    def from_ncdb(
        cls,
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
        if years == "all":
            years = [1970, 1980, 1990, 2000, 2010]
        if isinstance(boundary, gpd.GeoDataFrame):
            tracts = datasets.tracts_2010()[["geoid", "geometry"]]
            ncdb = datasets.ncdb().reset_index()
            if boundary.crs != tracts.crs:
                warn(
                    "Unable to determine whether boundary CRS is WGS84 "
                    "if this produces unexpected results, try reprojecting"
                )
            tracts = tracts[
                tracts.representative_point().intersects(boundary.unary_union)
            ]
            gdf = ncdb[ncdb["geoid"].isin(tracts["geoid"])]
            gdf = gpd.GeoDataFrame(gdf.merge(tracts, on="geoid", how="left"))

        else:
            gdf = _from_db(
                data=datasets.ncdb(),
                state_fips=state_fips,
                county_fips=county_fips,
                msa_fips=msa_fips,
                fips=fips,
                years=years,
            )

        return cls(gdf=gdf.reset_index(), harmonized=True)

    @classmethod
    def from_census(
        cls,
        state_fips=None,
        county_fips=None,
        msa_fips=None,
        fips=None,
        boundary=None,
        years="all",
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

        Returns
        -------
        Community
            Community with unharmonized census data

        """
        if years == "all":
            years = [1990, 2000, 2010]
        if isinstance(years, (str, int)):
            years = [years]

        msa_states = []
        if msa_fips:
            msa_states += datasets.msa_definitions()[
                datasets.msa_definitions()["CBSA Code"] == msa_fips
            ]["stcofips"].tolist()
        msa_states = [i[:2] for i in msa_states]

        # build a list of states in the dataset
        allfips = []
        for i in [state_fips, county_fips, fips, msa_states]:
            if i:
                if isinstance(i, (str,)):
                    i = [i]
                for each in i:
                    allfips.append(each[:2])
        states = list(set(allfips))

        # if using a boundary there will be no fips, so reset states to None
        if len(states) == 0:
            states = None

        df_dict = {
            1990: datasets.tracts_1990(states=states),
            2000: datasets.tracts_2000(states=states),
            2010: datasets.tracts_2010(states=states),
        }

        tracts = []
        for year in years:
            tracts.append(df_dict[year])
        tracts = pd.concat(tracts, sort=False)

        if isinstance(boundary, gpd.GeoDataFrame):
            if boundary.crs != tracts.crs:
                warn(
                    "Unable to determine whether boundary CRS is WGS84 "
                    "if this produces unexpected results, try reprojecting"
                )
            tracts = tracts[
                tracts.representative_point().intersects(boundary.unary_union)
            ]
            gdf = tracts.copy()

        else:

            gdf = _fips_filter(
                state_fips=state_fips,
                county_fips=county_fips,
                msa_fips=msa_fips,
                fips=fips,
                data=tracts,
            )

        return cls(gdf=gdf, harmonized=False)

    @classmethod
    def from_lodes(
        cls,
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
        if isinstance(years, (str,)):
            years = int(years)
        if isinstance(years, (int,)):
            years = [years]
        years = list(set(years))

        if msa_fips:
            msa_counties = datasets.msa_definitions()[
                datasets.msa_definitions()["CBSA Code"] == msa_fips
            ]["stcofips"].tolist()

        else:
            msa_counties = None

        # build a list of states in the dataset
        allfips = []
        stateset = []
        for i in [state_fips, county_fips, msa_counties, fips]:
            if i:
                if isinstance(i, (str,)):
                    i = [i]
                for each in i:
                    allfips.append(each)
                    stateset.append(each[:2])
            states = list(set(stateset))

        if any(year < 2010 for year in years):
            gdf00 = datasets.blocks_2000(states=states, fips=(tuple(allfips)))
            gdf00 = gdf00.drop(columns=["year"])
            gdf00 = _fips_filter(
                state_fips=state_fips,
                county_fips=county_fips,
                msa_fips=msa_fips,
                fips=fips,
                data=gdf00,
            )
            if isinstance(boundary, gpd.GeoDataFrame):
                if boundary.crs != gdf00.crs:
                    warn(
                        "Unable to determine whether boundary CRS is WGS84 "
                        "if this produces unexpected results, try reprojecting"
                    )
                gdf00 = gdf00[
                    gdf00.representative_point().intersects(boundary.unary_union)
                ]

        gdf = datasets.blocks_2010(states=states, fips=(tuple(allfips)))
        gdf = gdf.drop(columns=["year"])
        gdf = _fips_filter(
            state_fips=state_fips,
            county_fips=county_fips,
            msa_fips=msa_fips,
            fips=fips,
            data=gdf,
        )
        if isinstance(boundary, gpd.GeoDataFrame):
            if boundary.crs != gdf.crs:
                warn(
                    "Unable to determine whether boundary CRS is WGS84 "
                    "if this produces unexpected results, try reprojecting"
                )
            gdf = gdf[gdf.representative_point().intersects(boundary.unary_union)]

        # grab state abbreviations
        names = (
            _fipstable[_fipstable["FIPS Code"].isin(states)]["State Abbreviation"]
            .str.lower()
            .tolist()
        )
        if isinstance(names, str):
            names = [names]

        dfs = []
        for name in names:
            for year in years:
                try:
                    df = get_lehd(dataset=dataset, year=year, state=name)
                    df["year"] = year
                    if year < 2010:
                        df = gdf00.merge(df, on="geoid", how="inner")
                    else:
                        df = gdf.merge(df, on="geoid", how="inner")
                    df = df.set_index(["geoid", "year"])
                    dfs.append(df)
                except ValueError:
                    warn(f"{name.upper()} {year} not found!")
                    pass
        out = pd.concat(dfs, sort=True)
        out = out[~out.index.duplicated(keep="first")]
        out = out.reset_index()

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
        gdf = pd.concat(gdfs, sort=True)
        return cls(gdf=gdf)
