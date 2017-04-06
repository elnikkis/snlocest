# coding: utf-8

import sys
import pandas as pd


def load_labellist(filename_or_buffer, delimiter='\t'):
    '''ラベルリストを読み込む

    ラベルファイルはdelimiterで区切られた node_id (str), label (int) を期待するが、
    node_idが数値のみで構成されている場合、pandasが自動で数値へ型変換する。

    Args:
        filename_or_buffer 読み込むファイル名またはファイルオブジェクト
        delimiter 読み込むファイルの区切り文字。デフォルトは'\t' (optional)
    Returns:
        (ノードリスト, 対応するラベルリスト) のタプル
    '''
    df = pd.read_csv(filename_or_buffer, sep=delimiter, header=None, usecols=[0, 1])
    mat = df.values
    nodes = mat[:, 0]
    labels = mat[:, 1]
    return nodes.astype(str), labels

def load_dataset(edgefile, labelfile, graphclass):
    '''sklearnで使えるgraph, x, yを返す'''
    graph = graphclass()
    graph.load_edgelist(edgefile)
    graph.load_labellist(labelfile)
    nodes = graph.labeled_nodes
    labels = graph.labels
    x = graph.vto_nodeidx(nodes)
    return graph, x, labels

def write_result(nodes, predictions, graph, info=None, outfile=sys.stdout):
    '''推定結果のnode_idxからnode_idへ変換して保存する'''
    if info is None:
        for node, predicted in zip(nodes, predictions):
            print(graph.to_nodename(node), predicted, sep='\t', file=outfile)
    else:
        for node, predicted, p in zip(nodes, predictions, info):
            print(graph.to_nodename(node), predicted, *p, sep='\t', file=outfile)

def load_result(resultfile):
    return load_labellist(resultfile)
