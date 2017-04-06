# coding: utf-8

import numpy as np
import pytest
from snlocest.graph import CSRGraph, DictOfListGraph, SpMatLikeDOLGraph

TEST_EDGEFILE = 'testdata/test-dataset/networks/f_follower.tsv'
#TEST_EDGEFILE = 'testdata/test-dataset/networks/f_mutual.tsv'
TEST_LABELFILE = 'testdata/test-dataset/groundtruth/labels.tsv'


def test_DOLGraph():
    g = DictOfListGraph()
    g.load_edgelist(TEST_EDGEFILE)
    g.load_labellist(TEST_LABELFILE)

def test_CSRGraph():
    g = CSRGraph()
    g.load_edgelist(TEST_EDGEFILE)
    g.load_labellist(TEST_LABELFILE)

def test_SpMatLikeDOLGraph():
    g = SpMatLikeDOLGraph()
    g.load_edgelist(TEST_EDGEFILE)
    g.load_labellist(TEST_LABELFILE)

def test_graph():
    # 読み込んだ2つの形式のグラフでノード数、エッジ数が一致するかを調べる
    g1 = CSRGraph().load_edgelist(TEST_EDGEFILE).load_labellist(TEST_LABELFILE)
    g2 = DictOfListGraph().load_edgelist(TEST_EDGEFILE).load_labellist(TEST_LABELFILE)

    # nodes, num_edges, num_nodes, neighbors
    V1 = sorted(list(g1.nodes))
    V2 = sorted(list(g2.nodes))
    assert V1 == V2
    assert len(V1) == len(V2)

    assert g1.num_nodes == g2.num_nodes
    assert g1.num_edges == g2.num_edges

    targets = [100, 12341, 1331, 23452, 5110, 1000, 2000, 3000, 4000, 5000, 6000]
    for t in targets:
        u = V1[t]
        assert sorted(g1.neighbors(u)) == sorted(g2.neighbors(u))

def test_graph2():
    graphs = [DictOfListGraph, CSRGraph]
    for Graph in graphs:
        g = Graph()
        g.load_edgelist(TEST_EDGEFILE)
        g.load_labellist(TEST_LABELFILE)

        # nodesのneighborsのテスト
        for u in g.nodes:
            n = g.neighbors(u)

        # labeled_nodesのテスト
        for u in g.labeled_nodes:
            n = g.neighbors(u)

        assert len(g.labels) == len(g.labeled_nodes)

def test_SpMatLikeDOLGraph():
    g1 = CSRGraph().load_edgelist(TEST_EDGEFILE).load_labellist(TEST_LABELFILE)
    g2 = SpMatLikeDOLGraph().load_edgelist(TEST_EDGEFILE).load_labellist(TEST_LABELFILE)

    i = 1235
    u = g2.to_nodename(1235)
    assert np.all([g2.to_nodename(n) for n in g2.getrow(i)] == g1.neighbors(u))
    assert np.all(sorted([g1.to_nodename(n) for n in g1.getrow(g1.to_nodeidx(u))]) == sorted([g2.to_nodename(n) for n in g2.getrow(g2.to_nodeidx(u))]))

def test_CSR_SpMatLike():
    g = CSRGraph()
    g.load_edgelist(TEST_EDGEFILE)
    g.load_labellist(TEST_LABELFILE)
    node_idxes = g.vto_nodeidx(g.nodes)
    for u in node_idxes:
        n = g.getrow(u)

def test_DOL_SpMatLike():
    g = SpMatLikeDOLGraph().load_edgelist(TEST_EDGEFILE).load_labellist(TEST_LABELFILE)
    node_idxes = g.vto_nodeidx(g.nodes)
    for u in node_idxes:
        n = g.getrow(u)

@pytest.mark.skipif("True")
def test_graph_size():
    # ノード数が必要なだけ以上挿入できるか（エラーが起きないか）調べる
    # 44739243
    #d = {}
    #for i in range(100000000):
    #    d[i] = 1
    g = DictOfListGraph()
    for i in range(62676854):
        g.add_edge(str(i), str(i+1))
    assert g.num_nodes == 62676855
