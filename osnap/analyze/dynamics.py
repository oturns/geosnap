"""Transition and sequence analysis of neighborhood change."""

import itertools
from itertools import combinations

import giddy as ga
import numpy as np
import scipy.spatial.distance as d

import libpysal
from libpysal.weights.contiguity import Queen, Rook
from libpysal.weights.distance import KNN, Kernel


class Transition(object):
    """
    (Spatial) Markov approaches to transitional dynamics of neighborhood types.

    Parameters
    ----------  
    dataset          : osnap.Dataset
                      osnap dataset object with column defining neighborhood clusters
    w_type           : libpysal spatial weights type ("rook", "queen", "knn" or "kernel")
                      spatial weights object.
    w_kwds          : dict
                      dictionary with options to be passed to libpysal.weights generator        
    permutations    : int, optional
                      number of permutations for use in randomization based
                      inference (the default is 0).
    cluster_type    : string
                      cluster algorithm (specification) used to generate
                      neighborhood types, such as "ward", "kmeans", etc.

    Attributes
    ----------
    p               : matrix
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

        y = dataset.data.copy().reset_index()
        y = y[['geoid', 'year', cluster_type]]
        y = y.groupby(['geoid', 'year']).first().unstack()
        y = y.dropna()

        tracts = dataset.tracts.copy().merge(
            y.reset_index(), on='geoid', how='right')
        w_dict = {'rook': Rook, 'queen': Queen, 'knn': KNN, 'kernel': Kernel}
        w = w_dict[w_type].from_dataframe(tracts)
        y = y.astype(int)

        sm = ga.markov.Spatial_Markov(
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
    w               : W
                      spatial weights object.
    subs_mat        : array
                      (k,k), substitution cost matrix. Should be hollow (
                      0 cost between the same type), symmetric and non-negative.
    dist_type       : string
                      "hamming": hamming distance (substitution only
                      and its cost is constant 1) from sklearn.metrics,
                      "Levenshtein": Levenshtein distance (allow
                      indels, but substitution cost is constant 1) from
                      jellyfish; "Markov": utilize empirical transition
                      probabilities to define substitution costs;
                      "interval": differences between states are used
                      to define substitution costs. Default is None.
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


    Done:
    * Handle sequences of non-equal length
    * Handle different input data type (array of string/integer)
    * Integrate hamming distance

    Todo:
    1. Integrate other distance metrics: markov...
    2. test on empirical datasets
    5. Look at local alignment?
    6. All the sequences should be transformed in the same way (should not
    rely on transformation when trying to compare every pair - the label
    might be different)

    To think about:
    * provide a sequence class so that users can create a sequence object
    which has several meaningful attribute/method:
        * balanced or unbalanced?
            * max/min/median/mean length
        * characteristics of individual sequences/ a set of sequences (
        sharing the same past or future)
            * distribution
            * sequence indicator:
                * longitudinal diversity
                * complexity of the sequence
                * duration in each state
            * max/min/median/mean duration in each state
        * visualization of sequences
            * allow for plotting the most frequent sequences
            * allow for plotting user-selected sequences
            * empirical transition matrix - could be used as the input for
            substitution cost matrix
        * other representations of a sequence:
            * distinct successive states (DSSs)
        * handle different input types: pandas dataframe, array, list...
    * survival analysis?
    * deal with missing values NA?
        * a special state: another "unique" class and corresponding
        substitution cost (the cost should be the same as the indel)

    >>> import numpy as np

    1. Testing on unequal string sequences
    1.1 substitution cost matrix and indel cost are not given, and will be
    generated based on the distance type "interval"

    >>> seq1 = 'ACGGTAG'
    >>> seq2 = 'CCTAAG'
    >>> seq3 = 'CCTAAGC'
    >>> seqAna = Sequence([seq1,seq2,seq3],dist_type="interval")
    >>> seqAna.k
    4
    >>> seqAna.classes
    array(['A', 'C', 'G', 'T'], dtype='<U1')
    >>> seqAna.subs_mat
    array([[0., 1., 2., 3.],
           [1., 0., 1., 2.],
           [2., 1., 0., 1.],
           [3., 2., 1., 0.]])
    >>> seqAna.seq_dis_mat
    array([[ 0.,  7., 10.],
           [ 7.,  0.,  3.],
           [10.,  3.,  0.]])

    1.2 User-defined substitution cost matrix and indel cost

    >>> subs_mat = np.array([[0, 0.76, 0.29, 0.05],[0.30, 0, 0.40, 0.60],[0.16, 0.61, 0, 0.26],[0.38, 0.20, 0.12, 0]])
    >>> indel = subs_mat.max()
    >>> seqAna = Sequence([seq1,seq2,seq3], subs_mat=subs_mat, indel=indel)
    >>> seqAna.seq_dis_mat
    array([[0.  , 1.94, 2.46],
           [1.94, 0.  , 0.76],
           [2.46, 0.76, 0.  ]])

    1.3 Calculating "hamming" distance will fail on unequal sequences

    >>> seqAna = Sequence([seq1,seq2,seq3], dist_type="hamming")
    Traceback (most recent call last):
    ValueError: hamming distance cannot be calculated for sequences of unequal lengths!


    2. Testing on equal string sequences
    >>> seq1 = 'ACGGTAG'
    >>> seq2 = 'CCTAAGA'
    >>> seq3 = 'CCTAAGC'

    2.1  Calculating "hamming" distance
    >>> seqAna = Sequence([seq1,seq2,seq3], dist_type="hamming")
    >>> seqAna.seq_dis_mat
    array([[0., 6., 6.],
           [6., 0., 1.],
           [6., 1., 0.]])

    2.2 User-defined substitution cost matrix and indel cost (distance
    between different types is always 1 and indel cost is 2) - give the same
    sequence distance matrix as "hamming" distance
    >>> subs_mat = np.array([[0., 1., 1., 1.],[1., 0., 1., 1.],[1., 1., 0., 1.],[1., 1., 1., 0.]])
    >>> indel = 2
    >>> seqAna = Sequence([seq1,seq2,seq3], subs_mat=subs_mat, indel=indel)
    >>> seqAna.seq_dis_mat
    array([[0., 6., 6.],
           [6., 0., 1.],
           [6., 1., 0.]])

    2.3 User-defined substitution cost matrix and indel cost (distance
    between different types is always 1 and indel cost is 1) - give a
    slightly different sequence distance matrix from "hamming" distance since
    insertion and deletion is happening
    >>> subs_mat = np.array([[0., 1., 1., 1.],[1., 0., 1., 1.],[1., 1., 0.,1.],[1., 1., 1., 0.]])
    >>> indel = 1
    >>> seqAna = Sequence([seq1,seq2,seq3], subs_mat=subs_mat, indel=indel)
    >>> seqAna.seq_dis_mat
    array([[0., 5., 5.],
           [5., 0., 1.],
           [5., 1., 0.]])

    3. Not passing proper parameters will raise an error
    >>> seqAna = Sequence([seq1,seq2,seq3])
    Traceback (most recent call last):
    ValueError: Please specify a proper `dist_type` or `subs_mat` and `indel` to proceed!

    >>> seqAna = Sequence([seq1,seq2,seq3], subs_mat=subs_mat)
    Traceback (most recent call last):
    ValueError: Please specify a proper `dist_type` or `subs_mat` and `indel` to proceed!
    
    >>> seqAna = Sequence([seq1,seq2,seq3], indel=indel)
    Traceback (most recent call last):
    ValueError: Please specify a proper `dist_type` or `subs_mat` and `indel` to proceed!
    """

    def __init__(self,
                 y,
                 subs_mat=None,
                 dist_type=None,
                 indel=None,
                 w=None,
                 cluster_type=None):

        merged = list(itertools.chain.from_iterable(y))
        self.classes = np.unique(merged)
        self.k = len(self.classes)
        self.n = len(y)
        self.indel = indel
        self.subs_mat = subs_mat
        self.cluster_type = cluster_type
        self.label_dict = dict(zip(self.classes, range(self.k)))

        y_int = []
        for yi in y:
            y_int.append(list(map(self.label_dict.get, yi)))
        y_int = np.array(y_int)

        if subs_mat is None or indel is None:
            if dist_type == "interval":
                self.indel = self.k - 1
                self.subs_mat = np.zeros((self.k, self.k))
                for i in range(0, self.k - 1):
                    for j in range(i + 1, self.k):
                        self.subs_mat[i, j] = j - i
                        self.subs_mat[j, i] = j - i
                self._om_dist(y_int)
            elif dist_type == "hamming":
                if len(y_int.shape) != 2:
                    raise ValueError(
                        "hamming distance cannot be calculated for "
                        "sequences of unequal lengths!")
                hamming_dist = d.pdist(
                    y_int, metric="hamming") * y_int.shape[1]
                self.seq_dis_mat = d.squareform(hamming_dist)
            else:
                raise ValueError("Please specify a proper `dist_type` or "
                                 "`subs_mat` and `indel` to proceed!")
        else:
            self._om_dist(y_int)

    def _om_pair_dist(self, seq1, seq2):
        """
        Method for calculating the optimal matching distance between a pair of
        sequences given a substitution cost matrix and a indel cost.

        Arguments
        ---------
        seq1            : array
                          (t1, ), the first sequence
        seq2            : array
                          (t2, ), the second sequence

        Returns
        -------
        D               : array
                          (t2+1, t1+1), score matrix: D[i+1,j+1] is the best
                          score for aligning the substring, seq1[0:j] and seq2[0:i],
                          and D[t2+1, t1+1] (or D[-1,-1]) is the global optimal score.

        """

        t1 = len(seq1)
        t2 = len(seq2)

        D = np.zeros((t2 + 1, t1 + 1))
        for j in range(1, t1 + 1):
            D[0, j] = self.indel * j
        for i in range(1, t2 + 1):
            D[i, 0] = self.indel * i

        for i in range(1, t2 + 1):
            for j in range(1, t1 + 1):
                gaps = D[i, j - 1] + self.indel
                gapt = D[i - 1, j] + self.indel
                match = D[i - 1, j - 1] + self.subs_mat[seq1[j - 1], seq2[i -
                                                                          1]]
                D[i, j] = min(match, gaps, gapt)
        return D

    def _om_dist(self, y_int):
        """
        Method for calculating the optimal matching distance between any pair of
        sequences given a substitution cost matrix and a indel cost.

        Arguments
        ---------
        seq1            : array
                          (t1, ), the first sequence
        seq2            : array
                          (t2, ), the second sequence

        Returns
        -------
        D               : array
                          (t2+1, t1+1), score matrix: D[i+1,j+1] is the best
                          score for aligning the substring, seq1[0:j] and seq2[0:i],
                          and D[t2+1, t1+1] (or D[-1,-1]) is the global optimal score.

        """

        seq_dis_mat = np.zeros((self.n, self.n))
        for pair in combinations(range(self.n), 2):
            seq1 = y_int[pair[0]]
            seq2 = y_int[pair[1]]
            seq_dis_mat[pair[0], pair[1]] = self._om_pair_dist(seq1,
                                                               seq2)[-1, -1]

        self.seq_dis_mat = seq_dis_mat + seq_dis_mat.transpose()
