from context import analyze

linc = analyze.incs.linc

def test_linc():
    labels_0 = [1, 1, 1, 1, 2, 2, 3, 3, 3, 4]
    labels_1 = [1, 1, 1, 1, 1, 2, 3, 3, 3, 4]
    res = linc([labels_0, labels_1])
    assert res[4] == 1.0
    assert res[7] == 0.0 == res[-1]

    labels_2 = [1, 1, 1, 1, 1, 2, 3, 3, 3, 4]
    res = linc([labels_1, labels_2])
    assert res[0] ==  0.0

    res = linc([labels_0, labels_1, labels_2])
    assert res[0] == 0.25
