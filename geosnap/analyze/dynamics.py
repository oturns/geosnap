"""Transition and sequence analysis of neighborhood change."""

import geopandas as gpd
import numpy as np
import pandas as pd
from giddy.markov import Markov, Spatial_Markov
from giddy.sequence import Sequence
from libpysal.weights import Voronoi, lag_categorical
from libpysal.weights.contiguity import Queen, Rook
from libpysal.weights.distance import KNN, DistanceBand, Kernel
from sklearn.cluster import AgglomerativeClustering

Ws = {
    "queen": Queen,
    "rook": Rook,
    "voronoi": Voronoi,
    "knn": KNN,
    "kernel": Kernel,
    "distanceband": DistanceBand,
}


def transition(
    gdf,
    cluster_col,
    temporal_index="year",
    unit_index="geoid",
    w_type="rook",
    w_options=None,
    permutations=0,
):
    """
    (Spatial) Markov approach to transitional dynamics of neighborhoods.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame or pandas.DataFrame
        Long-form geopandas.GeoDataFrame or pandas.DataFrame containing neighborhood
        attributes with a column defining neighborhood clusters.
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
        additional options passed to a libpysal weights constructor
        (e.g. `k` for a KNN weights matrix)
    permutations : int, optional
        number of permutations for use in randomization based
        inference (the default is 0).

    Returns
    --------
    mar : giddy.markov.Markov instance or giddy.markov.Spatial_Markov
        if w_type=None, a classic Markov instance is returned.
        if w_type is given, a Spatial_Markov instance is returned.

    Examples
    --------
    >>> from geosnap import Community
    >>> columbus = Community.from_ltdb(msa_fips="18140")
    >>> columbus1 = columbus.cluster(columns=['median_household_income',
    ... 'p_poverty_rate', 'p_edu_college_greater', 'p_unemployment_rate'],
    ... method='ward', n_clusters=6)
    >>> gdf = columbus1.gdf
    >>> a = transition(gdf, "ward", w_type="rook")
    >>> a.p
    array([[0.79189189, 0.00540541, 0.0027027 , 0.13243243, 0.06216216,
        0.00540541],
       [0.0203252 , 0.75609756, 0.10569106, 0.11382114, 0.        ,
        0.00406504],
       [0.00917431, 0.20183486, 0.75229358, 0.01834862, 0.        ,
        0.01834862],
       [0.1959799 , 0.18341709, 0.00251256, 0.61809045, 0.        ,
        0.        ],
       [0.32307692, 0.        , 0.        , 0.        , 0.66153846,
        0.01538462],
       [0.09375   , 0.0625    , 0.        , 0.        , 0.        ,
        0.84375   ]])
    >>> a.P[0]
    array([[0.82119205, 0.        , 0.        , 0.10927152, 0.06622517,
        0.00331126],
       [0.14285714, 0.57142857, 0.14285714, 0.14285714, 0.        ,
        0.        ],
       [0.5       , 0.        , 0.5       , 0.        , 0.        ,
        0.        ],
       [0.21428571, 0.14285714, 0.        , 0.64285714, 0.        ,
        0.        ],
       [0.18918919, 0.        , 0.        , 0.        , 0.78378378,
        0.02702703],
       [0.28571429, 0.        , 0.        , 0.        , 0.        ,
        0.71428571]])
    """
    if not w_options:
        w_options = {}
    assert (
        unit_index in gdf.columns
    ), f"The unit_index ({unit_index}) column is not in the geodataframe"
    gdf_temp = gdf.copy().reset_index()
    df = gdf_temp[[unit_index, temporal_index, cluster_col]]
    df_wide = (
        df.pivot(index=unit_index, columns=temporal_index, values=cluster_col)
        .dropna()
        .astype("int")
    )
    y = df_wide.values
    if w_type is None:
        mar = Markov(y)  # class markov modeling
    else:
        geoms = gdf_temp.groupby(unit_index).first()[gdf_temp.geometry.name]
        gdf_wide = df_wide.merge(geoms, left_index=True, right_index=True)
        w = Ws[w_type].from_dataframe(gpd.GeoDataFrame(gdf_wide), **w_options)
        w.transform = "r"
        mar = Spatial_Markov(
            y, w, permutations=permutations, discrete=True, variable_name=cluster_col
        )
    return mar


def sequence(
    gdf,
    cluster_col,
    seq_clusters=5,
    subs_mat=None,
    dist_type=None,
    indel=None,
    temporal_index="year",
    unit_index="geoid",
):
    """
    Pairwise sequence analysis and sequence clustering.

    Dynamic programming if optimal matching.

    Parameters
    ----------
    gdf             : geopandas.GeoDataFrame or pandas.DataFrame
                      Long-form geopandas.GeoDataFrame or pandas.DataFrame containing neighborhood
                      attributes with a column defining neighborhood clusters.
    cluster_col     : string or int
                      Column name for the neighborhood segmentation, such as
                      "ward", "kmeans", etc.
    seq_clusters    : int, optional
                      Number of neighborhood sequence clusters. Agglomerative
                      Clustering with Ward linkage is now used for clustering
                      the sequences. Default is 5.
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
    subs_mat        : array
                      (k,k), substitution cost matrix. Should be hollow (
                      0 cost between the same type), symmetric and non-negative.
    indel           : float, optional
                      insertion/deletion cost.
    temporal_index        : string, optional
                      Column defining time and or sequencing of the long-form data.
                      Default is "year".
    unit_index          : string, optional
                      Column identifying the unique id of spatial units.
                      Default is "geoid".

    Returns
    --------
    gdf_temp        : geopandas.GeoDataFrame or pandas.DataFrame
                      geopandas.GeoDataFrame or pandas.DataFrame with a new column for sequence
                      labels.
    df_wide         : pandas.DataFrame
                      Wide-form DataFrame with k (k is the number of periods)
                      columns of neighborhood types and 1 column of sequence
                      labels.
    seq_dis_mat     : array
                      (n,n), distance/dissimilarity matrix for each pair of
                      sequences

    Examples
    --------
    >>> from geosnap.data import Community
    >>> columbus = Community.from_ltdb(msa_fips="18140")
    >>> columbus1 = columbus.cluster(columns=['median_household_income',
    ... 'p_poverty_rate', 'p_edu_college_greater', 'p_unemployment_rate'],
    ... method='ward', n_clusters=6)
    >>> gdf = columbus1.gdf
    >>> gdf_new, df_wide, seq_hamming = Sequence(gdf, dist_type="hamming")
    >>> seq_hamming.seq_dis_mat[:5, :5]
    array([[0., 3., 4., 5., 5.],
           [3., 0., 3., 3., 3.],
           [4., 3., 0., 2., 2.],
           [5., 3., 2., 0., 0.],
           [5., 3., 2., 0., 0.]])

    """
    assert (
        unit_index in gdf.columns
    ), f"The unit_index ({unit_index}) column is not in the geodataframe"
    gdf_temp = gdf.copy().reset_index()
    df = gdf_temp[[unit_index, temporal_index, cluster_col]]
    df_wide = (
        df.pivot(index=unit_index, columns=temporal_index, values=cluster_col)
        .dropna()
        .astype("int")
    )
    y = df_wide.values
    seq_dis_mat = Sequence(
        y, subs_mat=subs_mat, dist_type=dist_type, indel=indel, cluster_type=cluster_col
    ).seq_dis_mat
    model = AgglomerativeClustering(n_clusters=seq_clusters).fit(seq_dis_mat)
    name_seq = dist_type + "_%d" % (seq_clusters)
    df_wide[name_seq] = model.labels_
    gdf_temp = gdf_temp.merge(df_wide[[name_seq]], left_on=unit_index, right_index=True)
    gdf_temp = gdf_temp.reset_index(drop=True)

    return gdf_temp, df_wide, seq_dis_mat


def predict_markov_labels(
    gdf,
    unit_index="geoid",
    temporal_index="year",
    cluster_col=None,
    w_type="queen",
    w_options=None,
    base_year=None,
    new_colname=None,
    time_steps=1,
    increment=None,
    seed=None,
):
    """Predict neighborhood labels based on spatial Markov transition model

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        a long-form geodataframe with a column of labels to be simulated with a spatial Markov model
    unit_index : str,
        column on dataframe that identifies unique geographic units, by default "geoid"
    temporal_index : str
        column on dataframe that identifies unique time periods, by default "year"
    cluster_col : str
        column on the dataframe that stores cluster or other labels to be simulated
    w_type : str, optional
        type of spatial weights matrix to include in the transition model, by default "queen"
    w_options : dict, optional
        additional keyword arguments passed to the libpysal weights constructor
    base_year : int or str, optional
        the year from which to begin simulation (i.e. the set of labels to define the first
        period of the Markov sequence)
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
    crs = gdf.crs
    np.random.seed(seed)
    if not new_colname:
        new_colname = "predicted"
    if not w_options:
        w_options = {}

    assert (
        cluster_col and cluster_col in gdf.columns
    ), f"The input dataframe has no column named {cluster_col}"

    assert (
        base_year
    ), "Missing `base_year`. You must provide an initial time point with labels to begin simulation"

    gdf = gdf.copy()
    gdf = gdf.dropna(subset=[cluster_col]).reset_index(drop=True)
    t = transition(
        gdf,
        cluster_col,
        w_type=w_type,
        unit_index=unit_index,
        temporal_index=temporal_index,
        w_options=w_options,
    )

    if time_steps == 1:

        gdf = gdf[gdf[temporal_index] == base_year].reset_index(drop=True)
        w = Ws[w_type].from_dataframe(gdf, **w_options)
        predicted = _draw_labels(w, gdf, cluster_col, t, unit_index)
        if new_colname:
            predicted = predicted.rename(columns={cluster_col: new_colname})
        return predicted

    else:
        assert (
            increment
        ), "You must set the `increment` argument to simulate multiple time steps"
        predictions = []
        gdf = gdf[gdf[temporal_index] == base_year]
        gdf = gdf[[unit_index, cluster_col, temporal_index, "geometry"]]
        current_time = base_year + increment
        gdf = gdf.dropna(subset=[cluster_col]).reset_index(drop=True)
        w = Ws[w_type].from_dataframe(gdf, **w_options)
        predictions.append(gdf)

        for step in range(time_steps):
            # use the last known set of labels  to get the spatial context for each geog unit
            gdf = predictions[step - 1].copy()

            predicted = _draw_labels(w, gdf, cluster_col, t, unit_index)
            predicted[temporal_index] = current_time
            predictions.append(predicted)
            current_time += increment
        gdf = gpd.GeoDataFrame(pd.concat(predictions), crs=crs)
        gdf[cluster_col] = gdf[cluster_col].astype(int)
        if new_colname:
            gdf = gdf.rename(columns={cluster_col: new_colname})
        return gdf


def _draw_labels(w, gdf, cluster_col, markov, unit_index):
    gdf = gdf.copy()
    lags = lag_categorical(w, gdf[cluster_col].values)
    lags = lags.astype(int)

    labels = {}
    for i, cluster in gdf[cluster_col].astype(int).iteritems():
        probs = np.nan_to_num(markov.P)[lags[i]][cluster]
        probs /= (
            probs.sum()
        )  # correct for tolerance, see https://stackoverflow.com/questions/25985120/numpy-1-9-0-valueerror-probabilities-do-not-sum-to-1
        try:
            # in case obs have a modal neighbor never before seen in the model
            # (so all transition probs are 0)
            # fall back to the aspatial transition matrix

            labels[i] = np.random.choice(markov.classes, p=probs)
        except:
            labels[i] = np.random.choice(markov.classes, p=markov.p[cluster])
    labels = pd.Series(labels, name=cluster_col)
    labels = labels.astype(int)
    out = gdf[[unit_index, gdf.geometry.name]]
    predicted = gpd.GeoDataFrame(pd.concat([labels, out], axis=1))
    return predicted
