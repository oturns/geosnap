"""Transition and sequence analysis of neighborhood change."""

from giddy.markov import Markov, Spatial_Markov
from giddy.sequence import Sequence
from libpysal.weights.contiguity import Queen, Rook
from libpysal.weights.distance import KNN, Kernel
from sklearn.cluster import AgglomerativeClustering


def transition(
    gdf, cluster_col, time_var="year", id_var="geoid", w_type=None, permutations=0
):
    """
    (Spatial) Markov approach to transitional dynamics of neighborhoods.

    Parameters
    ----------
    gdf             : geopandas.GeoDataFrame or pandas.DataFrame
                      Long-form geopandas.GeoDataFrame or pandas.DataFrame containing neighborhood
                      attributes with a column defining neighborhood clusters.
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
    --------
    mar             : giddy.markov.Markov instance or giddy.markov.Spatial_Markov
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

    gdf_temp = gdf.copy().reset_index()
    df = gdf_temp[[id_var, time_var, cluster_col]]
    df_wide = (
        df.pivot(index=id_var, columns=time_var, values=cluster_col)
        .dropna()
        .astype("int")
    )
    y = df_wide.values
    if w_type is None:
        mar = Markov(y)  # class markov modeling
    else:
        gdf_one = gdf_temp.drop_duplicates([id_var])
        gdf_wide = df_wide.merge(gdf_one, left_index=True, right_on=id_var)
        w_dict = {"rook": Rook, "queen": Queen, "knn": KNN, "kernel": Kernel}
        w = w_dict[w_type].from_dataframe(gdf_wide)
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
    time_var="year",
    id_var="geoid",
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
    time_var        : string, optional
                      Column defining time and or sequencing of the long-form data.
                      Default is "year".
    id_var          : string, optional
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

    gdf_temp = gdf.copy().reset_index()
    df = gdf_temp[[id_var, time_var, cluster_col]]
    df_wide = (
        df.pivot(index=id_var, columns=time_var, values=cluster_col)
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
    gdf_temp = gdf_temp.merge(df_wide[[name_seq]], left_on=id_var, right_index=True)
    gdf_temp = gdf_temp.reset_index()

    return gdf_temp, df_wide, seq_dis_mat
