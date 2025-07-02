"""Transition and sequence analysis of neighborhood change."""

from time import time
from warnings import warn

import geopandas as gpd
import numpy as np
import pandas as pd
from giddy.markov import Markov, Spatial_Markov
from giddy.sequence import Sequence
from libpysal.weights import Voronoi, lag_categorical
from libpysal.weights.contiguity import Queen, Rook
from libpysal.weights.distance import KNN, DistanceBand, Kernel
from numpy.random import PCG64, SeedSequence, default_rng
from sklearn.cluster import AgglomerativeClustering
from tqdm.auto import tqdm

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
    Model neighborhood change as a discrete spatial Markov process.

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
    assert unit_index in gdf.columns, (
        f"The unit_index ({unit_index}) column is not in the geodataframe"
    )
    gdf_temp = gdf.copy().reset_index()
    df = gdf_temp[[unit_index, temporal_index, cluster_col]]
    df_wide = df.pivot(
        index=unit_index, columns=temporal_index, values=cluster_col
    ).dropna()
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
    assert unit_index in gdf.columns, (
        f"The unit_index ({unit_index}) column is not in the geodataframe"
    )
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
    w_type="rook",
    w_options=None,
    base_year=None,
    new_colname=None,
    time_steps=1,
    increment=None,
    seed=None,
    verbose=True,
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
    verbose: bool
        if true, print warnings from the label sampling process

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

    assert cluster_col and cluster_col in gdf.columns, (
        f"The input dataframe has no column named {cluster_col}"
    )

    assert base_year, (
        "Missing `base_year`. You must provide an initial time point with labels to begin simulation"
    )
    assert base_year in gdf[temporal_index].unique().tolist(), (
        "A set of observations with `temporal_index`==`base_year` must be included in the gdf"
    )

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
        predicted = _draw_labels(w, gdf, cluster_col, t, unit_index, verbose)
        if new_colname:
            predicted = predicted.rename(columns={cluster_col: new_colname})
        return predicted

    else:
        assert increment, (
            "You must set the `increment` argument to simulate multiple time steps"
        )
        predictions = []
        gdf = gdf[gdf[temporal_index] == base_year]
        gdf = gdf[[unit_index, cluster_col, temporal_index, gdf.geometry.name]]
        current_time = base_year + increment
        gdf = gdf.dropna(subset=[cluster_col]).reset_index(drop=True)
        w = Ws[w_type].from_dataframe(gdf, **w_options)
        predictions.append(gdf)

        for step in range(1, time_steps + 1):
            # use the last known set of labels  to get the spatial context for each geog unit
            gdf = predictions[step - 1].copy()

            predicted = _draw_labels(w, gdf, cluster_col, t, unit_index, verbose)
            predicted[temporal_index] = current_time
            predictions.append(predicted)
            current_time += increment
        gdf = gpd.GeoDataFrame(pd.concat(predictions), crs=crs)
        if new_colname:
            gdf = gdf.rename(columns={cluster_col: new_colname})
        return gdf


def _draw_labels(w, gdf, cluster_col, markov, unit_index, verbose):
    """Draw a random class label from the spatially-conditioned transition rates.

    Parameters
    ----------
    w : libpysal.weights.W
        spatial weights object
    gdf : geopandas.GeoDataFrame
        geodataframe of observations with class/cluster labels as a column
    cluster_col : string
        the column on the dataframe that holds class labels
    markov : giddy.Spatial_Markov
        an instance of a Spatial_Markov class
    unit_index : string
        the column on the dataframe that identifies unique spatial units

    Returns
    -------
    geopandas.GeoDataFrame
        long-form geodataframe with predicted cluster labels stored in the `new_colname` column
    """
    gdf = gdf.copy()
    gdf = gdf.dropna(subset=[cluster_col])
    lags = lag_categorical(w, gdf[cluster_col].values)
    clusters = gdf.reset_index()[cluster_col].values
    classes = markov.classes
    cluster_idx = dict(zip(classes, list(range(len(classes)))))

    labels = {}
    for i, lag in enumerate(lags):
        #  select the transition matrix using the label of unit's spatial lag
        spatial_context = np.nan_to_num(markov.P, posinf=0.0, neginf=0.0)[
            cluster_idx[lag]
        ]
        #  select the class row from the transition matrix using the unit's label
        probs = spatial_context[cluster_idx[clusters[i]]]
        probs /= probs.sum()  # correct for tolerance, see https://stackoverflow.com/questions/25985120/numpy-1-9-0-valueerror-probabilities-do-not-sum-to-1
        probs = np.nan_to_num(probs.flatten())
        if sum(probs) == 0:
            # in case obs have a modal neighbor never before seen in the model
            # (so all transition probs are 0)
            # fall back to the aspatial transition matrix
            if verbose:
                warn(
                    f"Falling back to aspatial transition rule for unit "
                    f"{gdf[unit_index][i]}",
                    stacklevel=2,
                )
            probs = markov.p[cluster_idx[clusters[i]]].flatten()

        labels[i] = np.random.choice(classes, p=probs)

    labels = pd.Series(labels, name=cluster_col, index=gdf.index)
    out = gdf[[unit_index, gdf.geometry.name]]
    predicted = gpd.GeoDataFrame(pd.concat([labels, out], axis=1))
    return predicted


def draw_sequence_from_gdf(
    gdf,
    w,
    label_column,
    smk,
    time_column,
    start_time=None,
    time_steps=1,
    increment=None,
    seed=None,
    aspatial=False,
):
    """Draw a set of class labels for each unit in a geodataframe using transition
    probabilities defined by a giddy.Spatial_Markov model and the spatial lag of each
    unit.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        geodataframe of observations with class/cluster labels as a column
    w : libpysal.weights.W
        spatial weights object that defines the neigbhbor graph for each unit.
    label_column : str
        the column on the dataframe that holds class labels
    smk : giddy.Spatial_Markov
        an instance of a Spatial_Markov class created from the giddy package
        or `geosnap.analyze.transition`
    time_column : str
        column on dataframe that identifies unique time periods, by default "year"
    start_time : str, int, or float, optional
        Time period to begin drawing a sequence of labels (must be present in
        `gdf[label_col]`). If None, use the most recent time period given by
        max(gdf[label_column].unique()). By default None
    time_steps : int, optional
        the number of time-steps to simulate (i.e. the number of labels to draw in a
        sequence for each unit), by default 1
    increment : itn, required
        styled increment each time-step referrs to. For example, for a model fitted to
        decadal Census data, each time-step refers to a period of ten years, so an
        increment of 10 ensures that the temporal index aligns appropriately with the
        time steps being simulated
    seed: int
        seed for  reproducible pseudo-random results. Used to create a SeedSequence and
        spawn a set of Generators using PCG64. If None, uses the current time

    Returns
    -------
    geopandas.GeoDataFrame
        long-form geodataframe with the same index as the geodataframe in the
        time period equal the start time (i.e. `gdf[gdf[time_column]==start_time]`).

    """
    assert increment

    steps = [start_time + (increment * step) for step in range(time_steps + 1)]
    steps = steps[1:]
    gdf = gdf.copy()
    gdf = gdf[[label_column, time_column, gdf.geometry.name]].copy()

    dfs = list()

    current_df = gdf[gdf[time_column] == start_time].reset_index()

    if seed is None:
        seed = int(time())

    base_seq = SeedSequence(seed)
    child_seqs = base_seq.spawn(time_steps)
    generators = [PCG64(seq) for seq in child_seqs]

    dfs.append(current_df)
    # must run in sequence because we need the prior time's spatial lag
    for i, step in enumerate(tqdm(steps)):
        # `steps` and `dfs` are off by one so the ith in dfs is the previous time period
        current_df = dfs[i].copy()
        predicted_labels = _draw_labels_from_gdf(
            current_df, w, label_column, smk, generators[i], aspatial=aspatial
        )
        predicted_df = gdf[gdf[time_column] == start_time].copy().reset_index()
        # overwrite labels with predictions for the new time period
        predicted_df[label_column] = predicted_labels
        predicted_df[time_column] = step

        dfs.append(predicted_df)
    simulated = pd.concat(dfs)

    return simulated


def _draw_labels_from_gdf(gdf, w, label_column, smk, seed, aspatial=False):
    """Draw set of new labels given a geodataframe and a spatial Markov transition model

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        a geodataframe defining the study region, including a column holding class labels
    w : libpysal.Weights
        a spatial weights matrix relating units to one another. This should be the same
        W object that was used to fit the Spatial_Markov instance
    label_column : str
        the column in gdf holding class labels
    smk : giddy.Spatial_Markov
        a spatial Markov transition model created by the pysal giddy package
        or geosnap.analyze.transition
    seed: int or nmnumpy.random.Generator instance
        seed passed to np.random.default_rng for reproducible pseudo-random results

    Returns
    -------
    numpy.array
        an array of simulated class labels drawn from the conditional probabilities
        provided in the Spatial_Markov object
    """
    classes = smk.classes
    labels = gdf[label_column].values
    lags = lag_categorical(w, labels)
    probs = _conditional_probs_from_smk(
        labels, lags, smk, fill_null_probs=True, aspatial=aspatial
    )
    assert len(lags) == len(probs), (
        "Lag values and probability vectors are different lengths"
    )
    simulated_labels = _draw_labels_from_probs(classes, probs=probs, seed=seed)

    return simulated_labels


def _draw_labels_from_probs(classes, probs, seed):
    """Draw from a fized set of classes using a vector of probabilities

    Parameters
    ----------
    classes : list-like
        set of class labels
    probs : list-like
        list of probabilities
    seed: int or numpy.random.Generator instance
        seed passed to np.random.default_rng for reproducible pseudo-random results
    verbose : bool, optional
        if true, print a warning when a label cannot be drawn from the
        probability vector, by default True

    Returns
    -------
    list
        list of labels drawn from `classes` with size n_probs
    """
    rng = default_rng(seed=seed)
    probs = pd.Series(probs)
    # for each set of probabilities in the array, draw a label
    # this could also be done in parallel. We could also take multiple draws per
    # unit by passing a `size` argument to rng.choice
    probs = probs.apply(lambda x: rng.choice(classes, p=x))

    return probs.values


def _conditional_probs_from_smk(
    labels, lags, smk, fill_null_probs=True, aspatial=False
):
    """Given a set of existing labels and associated lags, return a vector of
    transition probabilities from a giddy.Spatial_Markov model

    Parameters
    ----------
    labels : list
        array of categorical labels that define a class for each unit
    lags : list
        array of categorical labels that define the context for each unit
    smk : giddy.Spatial_Markov
        a spatial Markov transition model from giddy or geosnap.analyze.transition

    Returns
    -------
    list
        list of lists, where each element of the outer list is
        a set of transition probabilities, and each element of the innerr
        list(s) is the probability of transitioning into class with index i
    """
    # classes = pd.Categorical(smk.classes)
    class_idx = dict(zip(smk.classes, range(len(smk.classes))))

    # mapping back to the order each class is given in the smk object
    # class_idx = dict(zip(classes, list(range(len(classes)))))

    # print(class_idx)

    probs = list()
    # this piece could be parallelized as long as it gets concatenated back in order
    for i, _ in enumerate(labels):
        current_label = labels[i]
        current_class_idx = class_idx[current_label]
        # print(current_class_idx)

        aspatial_p = np.nan_to_num(smk.p[current_class_idx]).flatten()
        aspatial_p /= aspatial_p.sum()
        # print(i,class_idx[lags[i]])
        lag_idx = class_idx[lags[i]]
        conditional_matrix = smk.P[lag_idx]
        p = conditional_matrix[current_class_idx].flatten()
        # correct for tolerance, see https://stackoverflow.com/questions/25985120/numpy-1-9-0-valueerror-probabilities-do-not-sum-to-1
        # p = np.nan_to_num(p)
        if aspatial:
            probs.append(aspatial_p)
        else:
            if p.sum() == 0:
                if fill_null_probs:
                    warn(
                        f"No spatial transition rules for {current_label} with context {lags[i]} "
                        "falling back to aspatial transition rules",
                        stacklevel=2,
                    )
                    probs.append(aspatial_p)
                else:
                    raise ValueError(
                        f"No spatial transition rules for {current_label} with context {lags[i]} "
                    )
            else:
                # p /= p.sum()

                probs.append(np.nan_to_num(p))

    return probs
