"""
Indicators of Neighborhood Change
"""

from collections import defaultdict
import numpy as np

def _labels_to_neighborhoods(labels):
    """Convert a list of labels to neighborhoods dictionary

    Parameters
    -----------
    labels: list of neighborhood labels

    Returns
    -------
    neighborhoods: dictionary
                   key is the label for each neighborhood, value is the list of
                   area indexes defining that neighborhood

    Examples
    --------
    >>> labels = [1,1,1,2,2,3]
    >>> neighborhoods = _labels_to_neighborhoods(labels)
    >>> neighborhoods[1]
    [0, 1, 2]
    >>> neighborhoods[2]
    [3, 4]
    >>> neighborhoods[3]
    [5]
    """
    neighborhoods = defaultdict(list)
    for i, label in enumerate(labels):
        neighborhoods[label].append(i)
    return neighborhoods


def linc(labels_sequence):
    """Local Indicator of Neighborhood Change


    Arguments
    ---------
    labels_sequence: sequence of neighborhood labels (n,t)
                   n areas in t periods
                   first element is a list of neighborhood labels per area in
                   period 0, second element is a list of neighborhood labels
                   per area in period 1, and so on for all T periods.

    Returns
    -------
    lincs: array
           local indicator of neighborhood change over all periods

    Notes
    -----

    The local indicator of neighborhood change defined here allows for
    singleton neighborhoods (i.e., neighborhoods composed of a single primitive
    area such as a tract or block.). This is in contrast to the initial
    implementation in :cite:`Rey_2011` which prohibited singletons.

    Examples
    --------
    Time period 0 has the city defined as four neighborhoods on 10 tracts:

    >>> labels_0 = [1, 1, 1, 1, 2, 2, 3, 3, 3, 4]

    Time period 1 in the same city, with slight change in composition of the four neighborhoods

    >>> labels_1 = [1, 1, 1, 1, 1, 2, 3, 3, 3, 4]
    >>> res = linc([labels_0, labels_1])
    >>> res[4]
    1.0
    >>> res[1]
    0.25
    >>> res[7]
    0.0
    >>> res[-1]
    0.0

    And, in period 2, no change

    >>> labels_2 = [1, 1, 1, 1, 1, 2, 3, 3, 3, 4]
    >>> res = linc([labels_1, labels_2])
    >>> res[0]
    0.0

    We can pass more than two time periods, and get a "time-wise global linc"
    for each unit

    >>> res = linc([labels_0, labels_1, labels_2])
    >>> res[0]
    0.25

    """
    ltn = _labels_to_neighborhoods
    neighborhood_sequences = [ltn(labels) for labels in labels_sequence]
    ns = neighborhood_sequences
    n_areas = len(labels_sequence[0])
    lincs = np.zeros((n_areas,))

    T = len(labels_sequence)
    for i in range(n_areas):
        neighbors = []
        for t in range(T):
            neighbors.append(set(ns[t][labels_sequence[t][i]]))
        intersection = set.intersection(*neighbors)
        union = set.union(*neighbors)
        n_union = len(union)
        if n_union == 1: # singleton at all points in time
            lincs[i] = 0.
        else:
            lincs[i] = 1.0 - ((len(intersection)-1)/(n_union-1))
    return lincs
