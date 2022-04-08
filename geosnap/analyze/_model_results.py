from functools import cached_property
from warnings import warn

import esda
import geopandas as gpd
import scikitplot as skplt
from sklearn.metrics import silhouette_samples

from ..visualize.mapping import plot_timeseries
from .dynamics import predict_markov_labels as _predict_markov_labels
from .incs import lincs_from_gdf


class ModelResults:
    """Storage for clustering and regionalization results.

    Attributes
    ----------
    df: pandas.DataFrame
        data used to estimate the model
    columns: list
        subset of variables in the dataframe used to fit the model
    W: libpysal.weights.W
        libpysal spatial weights matrix used in model
    labels: array-like
        `cluster` or `region` label assigned to each observation
    instance: instance of model class used to generate neighborhood labels.
        fitted model instance, e.g sklearn.cluster.AgglomerativeClustering object
        or other model class used to estimate class labels
    name : str
        name of model
    temporal_index : str, optional
        which column on the dataframe defines time and or sequencing of the
        long-form data. Default is "year"
    unit_index : str, optional
        which column on the long-form dataframe identifies the stable units
        over time. In a wide-form dataset, this would be the unique index
    """

    def __init__(
        self, df, columns, labels, instance, W, name, unit_index, temporal_index
    ):
        """Initialize a new ModelResults instance.

        Parameters
        ----------
        df: array-like
            data of the cluster
        columns: list-like
            columns used to compute model
        W: libpysal.weights.W
            libpysal spatial weights matrix used in model
        labels: array-like
            labels of each column
        instance: AgglomerativeCluserting object, or other model specific object type
            how many clusters model was computed with
        name: str
            name of the model
        """
        self.columns = columns
        self.df = df
        self.W = W
        self.instance = instance
        self.labels = labels
        if self.W is None:
            self.model_type = "aspatial"
        else:
            self.model_type = "spatial"
        self.name = name
        self.unit_index = unit_index
        self.temporal_index = temporal_index

    @cached_property
    def lincs(self):
        """Calculate silhouette scores for the current model.

        Returns
        -------
        silhouette scores stored in a dataframe accessible from `comm.models.['model_name'].silhouettes`
        """
        assert (
            self.model_type != "spatial"
        ), "The Local Index of Neighborhood Change (LINC) measure is only valid for models where labels are pooled across time periods"
        df = self.df.copy()
        df = df.dropna(subset=self.columns)
        lincs = lincs_from_gdf(
            self.df,
            unit_index=self.unit_index,
            temporal_index=self.temporal_index,
            cluster_col=self.name,
            periods="all",
        )
        return lincs

    @cached_property
    def silhouette_scores(self):
        """Calculate silhouette scores for the current model.

        Returns
        -------
        silhouette scores stored in a dataframe accessible from `comm.models.['model_name'].silhouettes`
        """
        df = self.df.copy()
        df = df.dropna(subset=self.columns)
        return gpd.GeoDataFrame(
            {
                "silhouette_score": silhouette_samples(
                    df[self.columns].values, df[self.name]
                ),
                self.unit_index: df[self.unit_index],
                self.temporal_index: df[self.temporal_index],
            },
            index=self.df.index,
            geometry=self.df.geometry,
            crs=self.df.crs,
        )

    @cached_property
    def nearest_label(self):
        """Calculate nearest_labels for the current model.

        Returns
        -------
        nearest_labels stored in a dataframe accessible from:
        `comm.models.['model_name'].nearest_labels`
        """
        df = self.df.copy()
        df = df.dropna(subset=self.columns)
        return gpd.GeoDataFrame(
            {
                "nearest_label": esda.silhouettes.nearest_label(
                    self.df[self.columns].values, self.labels
                ),
                self.unit_index: df[self.unit_index],
                self.temporal_index: df[self.temporal_index],
            },
            index=self.df.index,
            geometry=self.df.geometry,
            crs=self.df.crs,
        )

    @cached_property
    def boundary_silhouette(self):
        """
        Calculate boundary silhouette scores for the current model.

        Returns
        -------
        boundary silhouette scores stored in a dataframe accessible from:
        `comm.models.['model_name'].boundary_silhouettes`
        """
        df = self.df.copy()
        df = df.dropna(subset=self.columns)
        assert self.model_type == "spatial", (
            "Model is aspatial (lacks a W object), but has been passed to a spatial diagnostic."
            " Try aspatial diagnostics like nearest_label() or sil_scores()"
        )
        return gpd.GeoDataFrame(
            {
                "boundary_silhouette": esda.boundary_silhouette(
                    self.df[self.columns].values, self.labels, self.W
                ),
                self.unit_index: df[self.unit_index],
                self.temporal_index: df[self.temporal_index],
            },
            index=self.df.index,
            geometry=self.df.geometry,
            crs=self.df.crs,
        )

    @cached_property
    def path_silhouette(self):
        """
        Calculate path silhouette scores for the current model.

        Returns
        -------
        path silhouette scores stored in a dataframe accessible from:
        `comm.models.['model_name'].path_silhouettes`
        """
        df = self.df.copy()
        df = df.dropna(subset=self.columns)
        assert self.model_type == "spatial", (
            "Model is aspatial(lacks a W object), but has been passed to a spatial diagnostic."
            " Try aspatial diagnostics like nearest_label() or sil_scores()"
        )
        return gpd.GeoDataFrame(
            {
                "path_silhouette": esda.path_silhouette(
                    self.df[self.columns].values, self.labels, self.W
                ),
                self.unit_index: df[self.temporal_index],
                self.temporal_index: df[self.temporal_index],
            },
            index=self.df.index,
            geometry=self.df.geometry,
            crs=self.df.crs,
        )

    def plot_silhouette(self, metric="euclidean", title="Silhouette Score"):
        """Make silhouette plot of the Community model.

        Parameters
        ----------
        metric : str, optional
            metric used to calculate distance. Accepts any string
            used with sklearn.metrics.pairwise
        title : str, optional
            title passed to the matplotlib figure. Defaults to "Silhouette Score"

        Returns
        -------
        matplotlib.Figure
            silhouette plot created by scikit-plot.

        """
        fig = skplt.metrics.plot_silhouette(
            self.df[self.columns].values, self.labels, metric=metric, title=title
        )

        return fig

    def plot_silhouette_map(
        self,
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
        """Plot of the silhouette scores of a Community model.

        Parameters
        ----------
        scheme : string,optional
            matplotlib scheme to be used
            default is 'quantiles'
        k : int, optional
            number of bins to graph. k may be ignored
            or unnecessary for some schemes, like headtailbreaks, maxp, and maximum_breaks
            Default is 6.
        cmap : string, optional
            matplotlib colormap used to shade polygons
        title : string, optional
            title of figure.
        dpi : int, optional
            dpi of the saved image if save_fig=True
            default is 500
        web_mercator : bool, optional
            whether to reproject the data into web mercator (epsg 3857)
            prior to plotting. Defaults to True
        ncols : int, optional
            number of columns in the figure
            if passing ncols, nrows must also be passed
            default is None
        nrows : int, optional
            number of rows in the figure
            if passing nrows, ncols must also be passed
            default is None
        figsize : tuple, optional
            the desired size of the matplotlib figure
        save_fig : str, optional
            path to save figure if desired.
        ctxmap : contextily map provider, optional
            contextily basemap. Set to False for no basemap.
            Default is Stamen.TonerLite
        alpha : int (optional)
            Transparency parameter passed to matplotlib

        Returns
        -------
        silhouette scores mapped onto community geography

        """
        if not plot_kwargs:
            plot_kwargs = dict()

        df = self.silhouette_scores.copy()

        if time_periods == "all":
            time_periods = df[self.temporal_index].unique()

        ax = plot_timeseries(
            df,
            "silhouette_score",
            time_subset=time_periods,
            alpha=alpha,
            legend=True,
            cmap=cmap,
            scheme=scheme,
            k=k,
            figsize=figsize,
            ncols=ncols,
            nrows=nrows,
            temporal_index=self.temporal_index,
            ctxmap=ctxmap,
            title=title,
            web_mercator=web_mercator,
            dpi=dpi,
            save_fig=save_fig,
            **plot_kwargs,
        )

        return ax

    def plot_next_best_label(
        self,
        time_periods="all",
        ctxmap="default",
        figsize=None,
        nrows=None,
        ncols=None,
        save_fig=None,
        alpha=0.5,
        cmap="set1",
        scheme="quantiles",
        k=8,
        title="Next-Best Label",
        dpi=500,
        plot_kwargs=None,
        web_mercator=True,
    ):
        """Plot of the silhouette scores of a Community model.

        Parameters
        ----------
        Parameters
        ----------
        cmap : string, optional
            matplotlib colormap used to shade polygons
        title : string, optional
            title of figure.
        dpi : int, optional
            dpi of the saved image if save_fig=True
            default is 500
        web_mercator : bool, optional
            whether to reproject the data into web mercator (epsg 3857)
            prior to plotting. Defaults to True
        ncols : int, optional
            number of columns in the figure
            if passing ncols, nrows must also be passed
            default is None
        nrows : int, optional
            number of rows in the figure
            if passing nrows, ncols must also be passed
            default is None
        figsize : tuple, optional
            the desired size of the matplotlib figure
        save_fig : str, optional
            path to save figure if desired.
        ctxmap : contextily map provider, optional
            contextily basemap. Set to False for no basemap.
            Default is Stamen.TonerLite
        alpha : int (optional)
            Transparency parameter passed to matplotlib

        Returns
        -------
        matplotlib.Axes
            plot of next-best label assignments for each geographic unit

        """
        if not plot_kwargs:
            plot_kwargs = dict()

        df = self.nearest_label.copy()

        if time_periods == "all":
            time_periods = df[self.temporal_index].unique()

        ax = plot_timeseries(
            df,
            "nearest_label",
            time_subset=time_periods,
            alpha=alpha,
            legend=True,
            cmap=cmap,
            categorical=True,
            figsize=figsize,
            ncols=ncols,
            nrows=nrows,
            temporal_index=self.temporal_index,
            ctxmap=ctxmap,
            title=title,
            web_mercator=web_mercator,
            dpi=dpi,
            save_fig=save_fig,
            **plot_kwargs,
        )

        return ax

    def plot_path_silhouette(
        self,
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
        """Plot of the silhouette scores of a Community model.

        Parameters
        ----------
        scheme : string,optional
            matplotlib scheme to be used
            default is 'quantiles'
        k : int, optional
            number of bins to graph. k may be ignored
            or unnecessary for some schemes, like headtailbreaks, maxp, and maximum_breaks
            Default is 6.
        cmap : string, optional
            matplotlib colormap used to shade polygons
        title : string, optional
            title of figure.
        dpi : int, optional
            dpi of the saved image if save_fig=True
            default is 500
        web_mercator : bool, optional
            whether to reproject the data into web mercator (epsg 3857)
            prior to plotting. Defaults to True
        ncols : int, optional
            number of columns in the figure
            if passing ncols, nrows must also be passed
            default is None
        nrows : int, optional
            number of rows in the figure
            if passing nrows, ncols must also be passed
            default is None
        figsize : tuple, optional
            the desired size of the matplotlib figure
        save_fig : str, optional
            path to save figure if desired.
        ctxmap : contextily map provider, optional
            contextily basemap. Set to False for no basemap.
            Default is Stamen.TonerLite
        alpha : int (optional)
            Transparency parameter passed to matplotlib

        Returns
        -------
        matplotlib.Axes
            plot of next-best label assignments for each geographic unit

        """
        if not plot_kwargs:
            plot_kwargs = dict()

        df = self.path_silhouette.copy()

        if time_periods == "all":
            time_periods = df[self.temporal_index].unique()

        ax = plot_timeseries(
            df,
            "path_silhouette",
            time_subset=time_periods,
            alpha=alpha,
            legend=True,
            cmap=cmap,
            figsize=figsize,
            ncols=ncols,
            nrows=nrows,
            temporal_index=self.temporal_index,
            ctxmap=ctxmap,
            title=title,
            dpi=dpi,
            save_fig=save_fig,
            web_mercator=web_mercator,
            **plot_kwargs,
        )

        return ax

    def plot_boundary_silhouette(
        self,
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
        """Plot of the silhouette scores of a Community model.

        Parameters
        ----------
        scheme : string,optional
            matplotlib scheme to be used
            default is 'quantiles'
        k : int, optional
            number of bins to graph. k may be ignored
            or unnecessary for some schemes, like headtailbreaks, maxp, and maximum_breaks
            Default is 6.
        cmap : string, optional
            matplotlib colormap used to shade polygons
        title : string, optional
            title of figure.
        dpi : int, optional
            dpi of the saved image if save_fig=True
            default is 500
        web_mercator : bool, optional
            whether to reproject the data into web mercator (epsg 3857)
            prior to plotting. Defaults to True
        ncols : int, optional
            number of columns in the figure
            if passing ncols, nrows must also be passed
            default is None
        nrows : int, optional
            number of rows in the figure
            if passing nrows, ncols must also be passed
            default is None
        figsize : tuple, optional
            the desired size of the matplotlib figure
        save_fig : str, optional
            path to save figure if desired.
        ctxmap : contextily map provider, optional
            contextily basemap. Set to False for no basemap.
            Default is Stamen.TonerLite
        alpha : int (optional)
            Transparency parameter passed to matplotlib

        Returns
        -------
        matplotlib.Axes
            plot of next-best label assignments for each geographic unit

        """
        if not plot_kwargs:
            plot_kwargs = dict()

        df = self.boundary_silhouette.copy()

        if time_periods == "all":
            time_periods = df[self.temporal_index].unique()

        ax = plot_timeseries(
            df,
            "boundary_silhouette",
            time_subset=time_periods,
            alpha=alpha,
            legend=True,
            cmap=cmap,
            figsize=figsize,
            ncols=ncols,
            nrows=nrows,
            temporal_index=self.temporal_index,
            ctxmap=ctxmap,
            title=title,
            dpi=dpi,
            save_fig=save_fig,
            web_mercator=web_mercator,
            **plot_kwargs,
        )

        return ax

    def plot_lincs(
        self,
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
        """Plot of the silhouette scores of a Community model.

        Parameters
        ----------
        scheme : string,optional
            matplotlib scheme to be used
            default is 'quantiles'
        k : int, optional
            number of bins to graph. k may be ignored
            or unnecessary for some schemes, like headtailbreaks, maxp, and maximum_breaks
            Default is 6.
        cmap : string, optional
            matplotlib colormap used to shade polygons
        title : string, optional
            title of figure.
        dpi : int, optional
            dpi of the saved image if save_fig=True
            default is 500
        web_mercator : bool, optional
            whether to reproject the data into web mercator (epsg 3857)
            prior to plotting. Defaults to True
        ncols : int, optional
            number of columns in the figure
            if passing ncols, nrows must also be passed
            default is None
        nrows : int, optional
            number of rows in the figure
            if passing nrows, ncols must also be passed
            default is None
        figsize : tuple, optional
            the desired size of the matplotlib figure
        save_fig : str, optional
            path to save figure if desired.
        ctxmap : contextily map provider, optional
            contextily basemap. Set to False for no basemap.
            Default is Stamen.TonerLite
        alpha : int (optional)
            Transparency parameter passed to matplotlib

        Returns
        -------
        matplotlib.Axes
            plot of next-best label assignments for each geographic unit

        """
        if not plot_kwargs:
            plot_kwargs = dict()

        df = self.lincs.copy()

        if time_periods == "all":
            time_periods = df[self.temporal_index].unique()

        ax = plot_timeseries(
            df,
            "boundary_silhouette",
            time_subset=time_periods,
            alpha=alpha,
            legend=True,
            cmap=cmap,
            figsize=figsize,
            ncols=ncols,
            nrows=nrows,
            temporal_index=self.temporal_index,
            ctxmap=ctxmap,
            title=title,
            dpi=dpi,
            save_fig=save_fig,
            web_mercator=web_mercator,
            **plot_kwargs,
        )

        return ax

    def predict_markov_labels(
        self,
        w_type="queen",
        w_options=None,
        base_year=None,
        new_colname=None,
        time_steps=1,
        increment=None,
        seed=None,
    ):
        """Predict neighborhood labels from the model in future time periods using a spatial Markov transition model

        Parameters
        ----------
        w_type : str, optional
            type of spatial weights matrix to include in the transition model, by default "queen"
        w_options : dict, optional
            additional keyword arguments passed to the libpysal weights constructor
        base_year : int or str, optional
            the year from which to begin simulation (i.e. the set of labels to define the first
            period of the Markov sequence). Defaults to the last year of available labels
        new_colname : str, optional
            new column name to store predicted labels under. Defaults to "predicted"
        time_steps : int, optional
            the number of time-steps to simulate, by default 1
        increment : str or int, optional
            styled increment each time-step referrs to. For example, for a model fitted to decadal
            Census data, each time-step refers to a period of ten years, so an increment of 10 ensures
            that the temporal index aligns appropriately with the time steps being simulated

        Returns
        -------
        geopandas.GeoDataFrame
            long-form geodataframe with predicted cluster labels stored in the `new_colname` column
        """
        if not base_year:
            base_year = max(self.df[self.temporal_index].unique())
            warn(
                f"No base_year provided. Using the last period for which labels are known:  {base_year} "
            )
        inputs = locals()
        del inputs["self"]
        output = _predict_markov_labels(
            self.df, self.unit_index, self.temporal_index, self.name, **inputs
        )
        return output
