# coding: utf-8

'''
distance計算のときのcacheヒット率を調べる
'''

import csv
from snlocest.distance import distance
from snlocest.util.time import record_time


#TEST_EDGELIST = 'data/datasets/active-closed/networks/f_follower.tsv'
#TEST_LABEL = 'data/datasets/active-closed/groundtruth/groundtruth_2014_active.tsv'
TEST_EDGELIST = 'testdata/test-dataset/networks/f_follower.tsv'
TEST_LABEL = 'testdata/test-dataset/groundtruth/labels.tsv'
TEST_AREADB = 'data/areadata/area_database.tsv'


@record_time
def test_cache():
    with open(TEST_AREADB, 'r') as fp:
        areadb = {cols[0]: (float(cols[1]), float(cols[2])) for cols in csv.reader(fp, delimiter='\t')}

    with open(TEST_LABEL, 'r') as fp:
        labels = {cols[0]: cols[1] for cols in csv.reader(fp, delimiter='\t')}

    with open(TEST_EDGELIST, 'r') as fp:
        for cols in csv.reader(fp, delimiter='\t'):
            # closedなエッジだけ計算する
            if not (cols[0] in labels and cols[1] in labels):
                continue
            a1 = labels[cols[0]]
            a2 = labels[cols[1]]
            l1 = areadb[a1]
            l2 = areadb[a2]
            distance(l1, l2)
    info = distance.cache_info()
    # CacheInfo(hits=1040, misses=3274, maxsize=524288, currsize=3274)
