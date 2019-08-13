"""Transition and sequence analysis of neighborhood change."""

import itertools
from itertools import combinations
from giddy.markov import Markov, Spatial_Markov
import numpy as np
import scipy.spatial.distance as d
from libpysal.weights.contiguity import Queen, Rook
from libpysal.weights.distance import KNN, Kernel


def transition(dataset, cluster_col, w_type=None, permutations=0):
    """
    (Spatial) Markov approach to transitional dynamics of neighborhoods.

    Parameters
    ----------
    gdf             : pandas.DataFrame
                      Long-form (geo)DataFrame containing neighborhood
                      attributes with a column defining neighborhood clusters.
    cluster_col     : string
                      Column name for the neighborhood segmentation, such as
                      "ward", "kmeans", etc.
    w_type          : string, optional
                      Type of spatial weights type ("rook", "queen", "knn" or
                      "kernel") to be used for spatial structure. Default is
                      None, if non-spatial Markov transition rates are desired.
    permutations    : int, optional
                      number of permutations for use in randomization based
                      inference (the default is 0).

    Return
    ------
                    : giddy.markov.Markov instance or
                    giddy.markov.SpatialMarkov instance
                      (k, k), transition probability matrix for a-spatial
                      Markov.
    transitions     : matrix
                      (k, k), counts of transitions between each neighborhood type
                       i and j for a-spatial Markov.
    T               : matrix
                      (k, k, k), counts of transitions for each conditional
                      Markov.  T[0] is the matrix of transitions for
                      observations with categorical spatial lags of 0; T[k-1] is
                      the transitions for the observations with lags of k-1.
    P               : matrix
                      (k, k, k), transition probability matrix for spatial
                      Markov. First dimension is the conditioned on the
                      categorical spatial lag.
    """

    def __init__(self,
                 dataset,
                 w_type,
                 w_kwds=None,
                 permutations=0,
                 cluster_type=None):

        y = dataset.census.copy().reset_index()
        y = y[['geoid', 'year', cluster_type]]
        y = y.groupby(['geoid', 'year']).first().unstack()
        y = y.dropna()

        tracts = dataset.tracts.copy().merge(
            y.reset_index(), on='geoid', how='right')
        w_dict = {'rook': Rook, 'queen': Queen, 'knn': KNN, 'kernel': Kernel}
        w = w_dict[w_type].from_dataframe(tracts)
        y = y.astype(int)

        sm = Spatial_Markov(
            y,
            w,
            permutations=permutations,
            discrete=True,
            variable_name=cluster_type)
        self.p = sm.p
        self.transitions = sm.transitions
        self.P = sm.P
        self.T = sm.T
        self.summary = sm.summary
        self.cluster_type = cluster_type
        # keep the spatial markov instance here in case that users want to
        # estimate steady state distribution etc
        self.sm = sm


class Sequence(object):
    """
    Pairwise sequence analysis.

    Dynamic programming if optimal matching.

    Parameters
    ----------
    y               : array
                      one row per sequence of neighborhood types for each
                      spatial unit. Sequences could be of varying lengths.
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
    indel           : float
                      insertion/deletion cost.
    cluster_type    : string
                      cluster algorithm (specification) used to generate
                      neighborhood types, such as "ward", "kmeans", etc.

    Attributes
    ----------
    seq_dis_mat     : array
                      (n,n), distance/dissimilarity matrix for each pair of
                      sequences
    classes         : array
                      (k, ), unique classes
    k               : int
                      number of unique classes
    label_dict      : dict
                      dictionary - {input label: int value between 0 and k-1 (k
                      is the number of unique classes for the pooled data)}

    Examples
    --------
    >>> import numpy as np

    """

    def __init__(self, y, subs_mat=None, dist_type=None,
                 indel=None, cluster_type=None):
        y=y





