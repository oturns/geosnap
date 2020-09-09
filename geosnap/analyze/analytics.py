"""Tools for the spatial analysis of neighborhood change."""
import esda
import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_samples

from libpysal.weights import attach_islands
from libpysal.weights.contiguity import Queen, Rook, Voronoi
from libpysal.weights.distance import KNN, DistanceBand
from libpysal.weights import lag_categorical

from .._data import _Map
from .cluster import (
    affinity_propagation,
    azp,
    gaussian_mixture,
    hdbscan,
    kmeans,
    max_p,
    skater,
    spectral,
    spenc,
    ward,
    ward_spatial,
)

np.seterr(divide='ignore', invalid='ignore')

Ws = {
    "queen": Queen,
    "rook": Rook,
    "voronoi": Voronoi,
    "knn": KNN,
    "distanceband": DistanceBand,
}


class ModelResults:
    """Stores data about cluster and cluster_spatial models.

    Attributes
    ----------
    X: array-like
        data used to compute model
    columns: list-like
        columns used in model
    W: libpysal.weights.W
        libpysal spatial weights matrix used in model
    labels: array-like
        labels of each column
    instance: instance of model class used to generate neighborhood labels.
        fitted model instance, e.g sklearn.cluster.AgglomerativeClustering object
        or other model class used to estimate class labels
    nearest_labels: dataframe
        container for dataframe of nearest_labels
    silhouettes: dataframe
        container for dataframe of silhouette scores
    path_silhouettes: dataframe
        container for dataframe of path_silhouette scores
    boundary_silhouettes: dataframe
        container for dataframe of boundary_silhouette scores
    model_type: string
        says whether the model is spatial or aspatial (contains a W object)

    """

    def __init__(self, X, columns, labels, instance, W):
        """Initialize a new ModelResults instance.

        Parameters
        ----------
        X: array-like
            data of the cluster
        columns: list-like
            columns used to compute model
        W: libpysal.weights.W
            libpysal spatial weights matrix used in model
        labels: array-like
            labels of each column
        instance: AgglomerativeCluserting object, or other model specific object type
            how many clusters model was computed with
        nearest_labels: dataframe
            container for dataframe of nearest_labels
        silhouettes: dataframe
            container for dataframe of silhouette scores
        path_silhouettes: dataframe
            container for dataframe of path_silhouette scores
        boundary_silhouettes: dataframe
            container for dataframe of boundary_silhouette scores
        model_type: string
            says whether the model is spatial or aspatial (contains a W object)
        """
        self.columns = columns
        self.X = X
        self.W = W
        self.instance = instance
        self.labels = labels
        self.nearest_labels = None
        self.silhouettes = None
        self.path_silhouettes = None
        self.boundary_silhouettes = None
        if self.W is None:
            self.model_type = "aspatial"
        else:
            self.model_type = "spatial"

    # Standalone funcs to calc these if you don't want to graph them
    def sil_scores(self, **kwargs):
        """
        Calculate silhouette scores for the current model.

        Returns
        -------
        silhouette scores stored in a dataframe accessible from `comm.models.['model_name'].silhouettes`
        """
        self.silhouettes = pd.DataFrame()
        self.silhouettes["silhouettes"] = silhouette_samples(
            self.X.values, self.labels, **kwargs
        )
        self.silhouettes.index = self.X.index
        return self.silhouettes

    def nearest_label(self, **kwargs):
        """
        Calculate nearest_labels for the current model.

        Returns
        -------
        nearest_labels stored in a dataframe accessible from:
        `comm.models.['model_name'].nearest_labels`
        """
        self.nearest_labels = pd.DataFrame()
        self.nearest_labels["nearest_label"] = esda.nearest_label(
            self.X.values, self.labels, **kwargs
        )
        self.nearest_labels.index = self.X.index
        return self.nearest_labels

    def boundary_sil(self, **kwargs):
        """
        Calculate boundary silhouette scores for the current model.

        Returns
        -------
        boundary silhouette scores stored in a dataframe accessible from:
        `comm.models.['model_name'].boundary_silhouettes`
        """
        assert self.model_type == "spatial", (
            "Model is aspatial (lacks a W object), but has been passed to a spatial diagnostic."
            " Try aspatial diagnostics like nearest_label() or sil_scores()"
        )
        self.boundary_silhouettes = pd.DataFrame()
        self.boundary_silhouettes["boundary_silhouettes"] = esda.boundary_silhouette(
            self.X.values, self.labels, self.W, **kwargs
        )
        self.boundary_silhouettes.index = self.X.index
        return self.boundary_silhouettes

    def path_sil(self, **kwargs):
        """
        Calculate path silhouette scores for the current model.

        Returns
        -------
        path silhouette scores stored in a dataframe accessible from:
        `comm.models.['model_name'].path_silhouettes`
        """
        assert self.model_type == "spatial", (
            "Model is aspatial(lacks a W object), but has been passed to a spatial diagnostic."
            " Try aspatial diagnostics like nearest_label() or sil_scores()"
        )
        self.path_silhouettes = pd.DataFrame()
        self.path_silhouettes["path_silhouettes"] = esda.path_silhouette(
            self.X.values, self.labels, self.W, **kwargs
        )
        self.path_silhouettes.index = self.X.index
        return self.path_silhouettes


def cluster(
    gdf,
    n_clusters=6,
    method=None,
    best_model=False,
    columns=None,
    verbose=False,
    time_var="year",
    id_var="geoid",
    scaler="std",
    pooling="fixed",
    **kwargs,
):
    """Create a geodemographic typology by running a cluster analysis on the study area's neighborhood attributes.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame, required
        long-form GeoDataFrame containing neighborhood attributes
    n_clusters : int, required
        the number of clusters to model. The default is 6).
    method : str in ['kmeans', 'ward', 'affinity_propagation', 'spectral','gaussian_mixture', 'hdbscan'], required
        the clustering algorithm used to identify neighborhood types
    best_model : bool, optional
        if using a gaussian mixture model, use BIC to choose the best
        n_clusters. (the default is False).
    columns : list-like, required
        subset of columns on which to apply the clustering
    verbose : bool, optional
        whether to print warning messages (the default is False).
    time_var : str, optional
        which column on the dataframe defines time and or sequencing of the
        long-form data. Default is "year"
    id_var : str, optional
        which column on the long-form dataframe identifies the stable units
        over time. In a wide-form dataset, this would be the unique index
    scaler : None or scaler from sklearn.preprocessing, optional
        a scikit-learn preprocessing class that will be used to rescale the
        data. Defaults to sklearn.preprocessing.StandardScaler
    pooling : ["fixed", "pooled", "unique"], optional (default='fixed')
        How to treat temporal data when applying scaling. Options include:

        * fixed : scaling is fixed to each time period
        * pooled : data are pooled across all time periods
        * unique : if scaling, apply the scaler to each time period, then generate
          clusters unique to each time period.

    Returns
    -------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame with a column of neighborhood cluster labels
        appended as a new column. If cluster method exists as a column on the DataFrame
        then the column will be incremented.

    model : named tuple
        A tuple with attributes X, columns, labels, instance, W, which store the
        input matrix, column labels, fitted model instance, and spatial weights matrix

    model_name : str
        name of model to be stored in a Community

    """
    specification = {
        "ward": ward,
        "kmeans": kmeans,
        "affinity_propagation": affinity_propagation,
        "gaussian_mixture": gaussian_mixture,
        "spectral": spectral,
        "hdbscan": hdbscan,
    }
    if scaler == "std":
        scaler = StandardScaler()
    if method not in specification.keys():
        raise ValueError(
            "`method` must of one of ['kmeans', 'ward', 'affinity_propagation', 'spectral', 'gaussian_mixture', 'hdbscan']"
        )

    # if we already have a column named after the clustering method, then increment it.
    if method in gdf.columns.tolist():
        model_name = method + str(len(gdf.columns[gdf.columns.str.startswith(method)]))
    else:
        model_name = method
    if not columns:
        raise ValueError("You must provide a subset of columns as input")

    times = gdf[time_var].unique()
    gdf = gdf.set_index([time_var, id_var])

    # this is the dataset we'll operate on
    data = gdf.copy()[columns]
    data = data.dropna(how="any", subset=columns)

    if scaler:

        if pooling in ["fixed", "unique"]:
            # if fixed (or unique), scale within each time period
            for time in times:
                data.loc[time] = scaler.fit_transform(data.loc[time].values)

        elif pooling == "pooled":
            # if pooled, scale the whole series at once
            data.loc[:, columns] = scaler.fit_transform(data.values)

    # the rescalar can create nans if a column has no variance, so fill with 0
    data = data.fillna(0)

    if pooling != "unique":

        # run the cluster model then join the labels back to the original data
        model = specification[method](
            data,
            n_clusters=n_clusters,
            best_model=best_model,
            verbose=verbose,
            **kwargs,
        )
        labels = model.labels_.astype(str)
        data = data.reset_index()
        clusters = pd.DataFrame(
            {model_name: labels, time_var: data[time_var], id_var: data[id_var]}
        )
        clusters.set_index([time_var, id_var], inplace=True)
        clusters = clusters[~clusters.index.duplicated(keep="first")]
        gdf = gdf.join(clusters, how="left")
        gdf = gdf.reset_index()
        results = ModelResults(
            X=data.set_index([id_var, time_var]),
            columns=columns,
            labels=model.labels_,
            instance=model,
            W=None,
        )
        return gdf, results, model_name

    elif pooling == "unique":
        models = _Map()
        gdf[model_name] = np.nan
        data = data.reset_index()

        for time in times:
            df = data[data[time_var] == time]

            model = specification[method](
                df[columns],
                n_clusters=n_clusters,
                best_model=best_model,
                verbose=verbose,
                **kwargs,
            )

            labels = model.labels_.astype(str)
            clusters = pd.DataFrame(
                {model_name: labels, time_var: time, id_var: df[id_var]}
            )
            clusters.set_index([time_var, id_var], inplace=True)
            gdf.update(clusters)
            results = ModelResults(
                X=df.set_index([id_var, time_var]),
                columns=columns,
                labels=model.labels_,
                instance=model,
                W=None,
            )
            models[time] = results

        gdf = gdf.reset_index()

        return gdf, models, model_name


def cluster_spatial(
    gdf,
    n_clusters=6,
    spatial_weights="rook",
    method=None,
    columns=None,
    threshold_variable="count",
    threshold=10,
    time_var="year",
    id_var="geoid",
    scaler="std",
    weights_kwargs=None,
    **kwargs,
):
    """Create a *spatial* geodemographic typology by running a cluster
    analysis on the metro area's neighborhood attributes and including a
    contiguity constraint.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        long-form geodataframe holding neighborhood attribute and geometry data.
    n_clusters : int
        the number of clusters to model. The default is 6).
    spatial_weights : ['queen', 'rook'] or libpysal.weights.W object
        spatial weights matrix specification`. By default, geosnap will calculate Rook
        weights, but you can also pass a libpysal.weights.W object for more control
        over the specification.
    method : str in ['ward_spatial', 'spenc', 'skater', 'azp', 'max_p']
        the clustering algorithm used to identify neighborhood types
    columns : array-like
        subset of columns on which to apply the clustering
    threshold_variable : str
        for max-p, which variable should define `p`. The default is "count",
        which will grow regions until the threshold number of polygons have
        been aggregated
    threshold : numeric
        threshold to use for max-p clustering (the default is 10).
    time_var : str
        which column on the dataframe defines time and or sequencing of the
        long-form data. Default is "year"
    id_var : str
        which column on the long-form dataframe identifies the stable units
        over time. In a wide-form dataset, this would be the unique index
    weights_kwargs : dict
        If passing a libpysal.weights.W instance to spatial_weights, these additional
        keyword arguments that will be passed to the weights constructor
    scaler : None or scaler class from sklearn.preprocessing
        a scikit-learn preprocessing class that will be used to rescale the
        data. Defaults to sklearn.preprocessing.StandardScaler

    Returns
    -------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame with a column of neighborhood cluster labels
        appended as a new column. If cluster method exists as a column on the DataFrame
        then the column will be incremented.

    models : dict of named tuples
        tab-completable dictionary of named tuples keyed on the Community's time variable
        (e.g. year). The tuples store model results and have attributes X, columns, labels,
        instance, W, which store the input matrix, column labels, fitted model instance,
        and spatial weights matrix

    model_name : str
        name of model to be stored in a Community

    """
    specification = {
        "azp": azp,
        "spenc": spenc,
        "ward_spatial": ward_spatial,
        "skater": skater,
        "max_p": max_p,
    }
    if method not in specification.keys():
        raise ValueError(
            "`method` must be one of  ['ward_spatial', 'spenc', 'skater', 'azp', 'max_p']"
        )

    if method in gdf.columns.tolist():
        model_name = method + str(len(gdf.columns[gdf.columns.str.startswith(method)]))
    else:
        model_name = method
    if not columns:
        raise ValueError("You must provide a subset of columns as input")
    if not method:
        raise ValueError("You must choose a clustering algorithm to use")
    if scaler == "std":
        scaler = StandardScaler()

    times = gdf[time_var].unique()
    gdf = gdf.set_index([time_var, id_var])

    # this is the dataset we'll operate on
    data = gdf.copy()[columns + ["geometry"]]

    contiguity_weights = {"queen": Queen, "rook": Rook}

    if spatial_weights in contiguity_weights.keys():
        W = contiguity_weights[spatial_weights]
    else:
        W = spatial_weights

    models = _Map()
    ws = {}
    clusters = []
    gdf[model_name] = np.nan

    # loop over each time period, standardize the data and build a weights matrix
    for time in times:
        df = data.loc[time].dropna(how="any", subset=columns).reset_index()
        df[time_var] = time

        if scaler:
            df[columns] = scaler.fit_transform(df[columns].values)

        if weights_kwargs:
            w0 = W.from_dataframe(df, **weights_kwargs)
        else:
            w0 = W.from_dataframe(df)
        w1 = KNN.from_dataframe(df, k=1)
        ws = [w0, w1]

        if threshold_variable and threshold_variable != "count":
            data[threshold_variable] = gdf[threshold_variable]
            threshold_var = data.threshold_variable.values
            ws[0] = attach_islands(ws[0], ws[1])

        elif threshold_variable == "count":
            threshold_var = np.ones(len(data.loc[time]))
            ws[0] = attach_islands(ws[0], ws[1])

        else:
            threshold_var = None

        model = specification[method](
            df[columns],
            w=ws[0],
            n_clusters=n_clusters,
            threshold_variable=threshold_var,
            threshold=threshold,
            **kwargs,
        )

        labels = model.labels_.astype(str)
        clusters = pd.DataFrame(
            {model_name: labels, time_var: df[time_var], id_var: df[id_var]}
        )
        clusters = clusters.drop_duplicates(subset=[id_var])
        clusters.set_index([time_var, id_var], inplace=True)
        gdf.update(clusters)
        results = ModelResults(
            X=df.set_index([id_var, time_var]).drop("geometry", axis=1),
            columns=columns,
            labels=model.labels_,
            instance=model,
            W=ws[0],
        )
        models[time] = results

    gdf = gdf.reset_index()

    return gdf, models, model_name


def predict_labels(
    comm,
    index_col='geoid',
    time_col='year',
    model_name=None,
    w_type='queen',
    w_options=None,
    base_year=None,
    new_colname=None,
    time_steps=1,
    increment=None,
    seed=None
):
    np.random.seed(seed)
    if not new_colname:
        new_colname = "predicted"
    if not w_options:
        w_options = {}

    assert (
        comm.harmonized
    ), "Predictions based on transition models require harmonized data"
    assert (
        model_name and model_name in comm.gdf.columns
    ), "You must provide the name of a cluster model present on the Community gdf"

    assert base_year, "Missing `base_year`. You must provide an initial time point with labels to begin simulation"

    gdf = comm.gdf.copy()
    gdf = gdf.dropna(subset=[model_name]).reset_index()
    t = comm.transition(model_name, w_type=w_type)

    if time_steps == 1:

        gdf = gdf[gdf[time_col] == base_year].reset_index()
        w = Ws[w_type].from_dataframe(gdf, **w_options)
        lags = lag_categorical(w, gdf[model_name].values)
        lags = lags.astype(int)

        labels = {}
        for i, cluster in gdf[model_name].astype(int).iteritems():
            probs = np.nan_to_num(t.P)[lags[i]][cluster]
            probs /= (
                probs.sum()
            )  # correct for tolerance, see https://stackoverflow.com/questions/25985120/numpy-1-9-0-valueerror-probabilities-do-not-sum-to-1
            try:
                # in case obs have a modal neighbor never before seen in the model
                # (so all transition probs are 0)
                # fall back to the aspatial transition matrix

                labels[i] = np.random.choice(t.classes, p=probs)
            except:
                labels[i] = np.random.choice(t.classes, p=t.p[cluster])
        labels = pd.Series(labels, name=new_colname)
        out = gdf[[index_col, "geometry"]]
        predicted = pd.concat([labels, out], axis=1)
        return gpd.GeoDataFrame(predicted)

    else:
        assert (
            increment
        ), "You must set the `increment` argument to simulate multiple time steps"
        predictions = []
        gdf = gdf[gdf[time_col] == base_year]
        gdf = gdf[[index_col, model_name, time_col, "geometry"]]
        current_time = base_year + increment
        gdf = gdf.dropna(subset=[model_name]).reset_index()
        w = Ws[w_type].from_dataframe(gdf, **w_options)
        predictions.append(gdf)

        for step in range(time_steps):
            # use the last known set of labels  to get the spatial context for each geog unit
            gdf = predictions[step - 1].copy()
            lags = lag_categorical(w, gdf[model_name].values)
            lags = lags.astype(int)
            labels = {}
            for i, cluster in gdf[model_name].astype(int).iteritems():
                #  use labels and spatial context to get the transition probabilities for each unit
                probs = np.nan_to_num(t.P)[lags[i]][cluster]
                probs /= (
                    probs.sum()
                )  # correct for tolerance, see https://stackoverflow.com/questions/25985120/numpy-1-9-0-valueerror-probabilities-do-not-sum-to-1
                try:
                    #  draw from the conditional probabilities for each unit
                    # in case obs have a modal neighbor never before seen in the model
                    # (so all transition probs are 0)
                    # fall back to the aspatial transition matrix
                    labels[i] = np.random.choice(t.classes, p=probs)
                except:
                    labels[i] = np.random.choice(t.classes, p=t.p[cluster])
            labels = pd.Series(labels, name=model_name)
            out = gdf[[index_col, "geometry"]]
            out[time_col] = current_time
            predicted = pd.concat([labels, out], axis=1)
            predictions.append(gpd.GeoDataFrame(predicted).dropna(subset=[model_name]))
            current_time += increment
        return predictions
