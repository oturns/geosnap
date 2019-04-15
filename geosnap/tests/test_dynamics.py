from context import analyze
import numpy as np
import pytest

Sequence = analyze.dynamics.Sequence

def test_Sequence_unequal():
    '''
    1. Testing on sequences of unequal lengths.
    '''

    seq1 = 'ACGGTAG'
    seq2 = 'CCTAAG'
    seq3 = 'CCTAAGC'

    # 1.1 substitution cost matrix and indel cost are not given, and will be
    # generated based on the distance type "interval"
    seqAna = Sequence([seq1, seq2, seq3], dist_type="interval")
    subs_mat = np.array([[0., 1., 2., 3.],
                         [1., 0., 1., 2.],
                         [2., 1., 0., 1.],
                         [3., 2., 1., 0.]])
    seq_dis_mat = np.array([[ 0.,  7., 10.],
                            [ 7.,  0.,  3.],
                            [10.,  3.,  0.]])
    assert seqAna.k == 4
    assert all([a == b for a, b in zip(seqAna.subs_mat.flatten(),
                                       subs_mat.flatten())])
    assert all([a == b for a, b in zip(seqAna.seq_dis_mat.flatten(),
                                       seq_dis_mat.flatten())])


    # 1.2 User-defined substitution cost matrix and indel cost
    subs_mat = np.array([[0, 0.76, 0.29, 0.05],
                         [0.30, 0, 0.40, 0.60],
                         [0.16, 0.61, 0, 0.26],
                         [0.38, 0.20, 0.12, 0]])
    indel = subs_mat.max()
    seqAna = Sequence([seq1, seq2, seq3], subs_mat=subs_mat, indel=indel)
    seq_dis_mat = np.array([[0.  , 1.94, 2.46],
                            [1.94, 0.  , 0.76],
                            [2.46, 0.76, 0.  ]])
    assert all([a == b for a, b in zip(seqAna.seq_dis_mat.flatten(),
                                       seq_dis_mat.flatten())])

    # 1.3 Calculating "hamming" distance will fail on unequal sequences

    with pytest.raises(ValueError,):
        Sequence([seq1, seq2, seq3], dist_type="hamming")


def test_Sequence_equal():
    '''
    2. Testing on sequences of equal length.
    '''

    seq1 = 'ACGGTAG'
    seq2 = 'CCTAAGA'
    seq3 = 'CCTAAGC'

    # 2.1 Calculating "hamming" distance will not fail on equal sequences

    seqAna = Sequence([seq1, seq2, seq3], dist_type="hamming")
    seq_dis_mat = np.array([[0., 6., 6.],
                            [6., 0., 1.],
                            [6., 1., 0.]])
    assert all([a == b for a, b in zip(seqAna.seq_dis_mat.flatten(),
                                       seq_dis_mat.flatten())])

    # 2.2 User-defined substitution cost matrix and indel cost (distance
    #     between different types is always 1 and indel cost is 2 or larger) -
    #     give the same sequence distance matrix as "hamming" distance
    subs_mat = np.array([[0., 1., 1., 1.], [1., 0., 1., 1.], [1., 1., 0., 1.],
                         [1., 1., 1., 0.]])
    indel = 2
    seqAna = Sequence([seq1, seq2, seq3], subs_mat=subs_mat, indel=indel)
    seq_dis_mat = np.array([[0., 6., 6.],[6., 0., 1.],[6., 1., 0.]])
    assert all([a == b for a, b in zip(seqAna.seq_dis_mat.flatten(),
                                       seq_dis_mat.flatten())])

    # 2.3 User-defined substitution cost matrix and indel cost (distance
    #     between different types is always 1 and indel cost is 1) - give a
    #     slightly different sequence distance matrix from "hamming" distance since
    #     insertion and deletion is happening
    indel = 1
    seqAna = Sequence([seq1, seq2, seq3], subs_mat=subs_mat, indel=indel)
    seq_dis_mat = np.array([[0., 5., 5.],[5., 0., 1.],[5., 1., 0.]])
    assert all([a == b for a, b in zip(seqAna.seq_dis_mat.flatten(),
                                       seq_dis_mat.flatten())])
