# coding: utf-8

import numpy as np
from snlocest.graph import load_dsv_by_pandas, load_dsv_by_numpy, load_dsv

TESTFILE = 'testdata/test-dataset/networks/f_mutual.tsv'


def test_load_dsv_by():
    a1 = load_dsv_by_pandas(TESTFILE, delimiter='\t', dtype=np.int64)
    a2 = load_dsv_by_numpy(TESTFILE, delimiter='\t', dtype=np.int64)
    assert type(a1) == type(a2)
    assert a1.shape == a2.shape


def test_dsv():
    a = load_dsv(TESTFILE)
