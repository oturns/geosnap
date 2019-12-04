"""
Indicators of Neighborhood Change
"""

from collections import defaultdict
import numpy as np

def _labels_to_neighborhoods(labels):
    """Convert a list of labels to neighborhoods dictionary
    Arguments
    ---------
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
        #if label != -9999:
        neighborhoods[label].append(i)
    return neighborhoods


def linc(labels_sequence):
    """Local Indicator of Neighborhood Change
    Arguments
    ---------
    labels_sequence: sequence of neighborhood labels (n,t)
                   n areas in n periods
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
    implementation in :cite:`rey2011` which prohibited singletons.
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
    #print(labels_sequence)
    neighborhood_sequences = [ltn(labels) for labels in labels_sequence]
    #print(neighborhood_sequences[0])
    #print(neighborhood_sequences[1])
    ns = neighborhood_sequences
    n_areas = len(labels_sequence[0])
    lincs = np.zeros((n_areas,))

    T = len(labels_sequence)
    for i in range(n_areas):
        neighbors = []
        for t in range(T):
            if (labels_sequence[t][i] == None or labels_sequence[t][i] == -9999): continue
            neighbors.append(set(ns[t][labels_sequence[t][i]]))
        if (len(neighbors) < 2): 
            lincs[i] = -9999
        else:
            intersection = set.intersection(*neighbors)
            union = set.union(*neighbors)
            n_union = len(union)
            if n_union == 1: # singleton at all points in time
                lincs[i] = 0.
            else:
                #lincs[i] = round(1.0 - ((len(intersection)-1)/(n_union-1)),2)
                lincs[i] = 1.0 - ((len(intersection)-1)/(n_union-1))
        #print("Tract ID #", i, "-----------------------------------")		
        #print("*neighbors=",*neighbors)		
        #print("intersection= ",intersection)
        #print("union=",union)
        #print("                                                  ")
        #print("                                                  ")    
    return lincs
	
if __name__ == '__main__':	
	           #0, 1, 2, 3, 4, 5, 6, 7, 8, 9
    tract70 = [1, 1, 2, 2, 3, 3, 1, 2, 2, 1 ]	
    tract80 = [1, 1, 1, 3, 3, 3, 3, 2, 2, 3 ]
    tract90 = [1, 1, 3, 3, 2, 2, 3, 2, 2, 3 ]	
               #0, 1, 2, 3, 4, 5, 6, 7, 8, 9
    #labels_0 = [1, 1, 1, 1, 2, 2, 3, 3, 4, 4] 
    #labels_1 = [1, 1, 1, 1, 1, 2, 3, 3, 3, 4]
    #INC_bw_70_80 = linc([tract70, tract80])
    INC_bw_80_90 = linc([tract80, tract90])
    #INC_bw_70_80_90 = linc([tract70, tract80, tract90])
    #print("INC_bw_70_80= ",INC_bw_70_80)
    print("INC_bw_80_90= ",INC_bw_80_90)
    #print("INC_bw_70_80_90= ",INC_bw_70_80_90)

	 #tractID:   0     1     2     3     4     5     6    7    8     9
#labels_0 =     [1,    1,    1,    1,    2,    2,    3,   3,   4,    4] 
#labels_1 =     [1,    1,    1,    1,    1,    2,    3,   3,   3,    4]
#Res          = [0.25, 0.25, 0.25, 0.25, 1.00, 1.00 ,0.5, 0.5, 1.00, 1.00  ]
