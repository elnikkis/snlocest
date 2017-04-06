# coding: utf-8

'''
Precision, Recall, F1で評価する

Leave-one-outの結果

K-foldの結果
'''

import sys
import os.path
import snlocest.util as util
import numpy as np
import pandas as pd

from sklearn.model_selection import KFold
from sklearn.metrics import precision_recall_fscore_support, classification_report


def precision_recall_fscore(nodes, y_true, y_pred):
    df = pd.DataFrame({'true': y_true, 'pred': y_pred}, index=nodes)
    #df['pred'].replace(0, np.NaN, inplace=True)
    n_predicted_nodes = len(df[df['pred'] != 0])
    n_corrects = len(df[df['pred'] == df['true']])
    n_test = len(nodes)
    p = n_corrects / n_predicted_nodes
    r = n_corrects / n_test
    f = 2 * p * r / (p + r)
    return (p, r, f, n_predicted_nodes, n_corrects, n_test)

def main(args):
    # ラベルが付けられたノードIDのリスト、それに対応するラベルのリスト
    labeled_nodes, labels = util.load_labellist(args.labelfile)

    if args.random_state:
        random_state = args.random_state
        n_splits = args.n_splits if args.n_splits else 10

        cv = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
        for i, (train, test) in enumerate(cv.split(labeled_nodes)):
            filepath = os.path.join(args.resultfile_or_dir, '{}_{}.{}'.format(args.stem, i, args.ext))
            test_nodes, y_pred = util.load_result(filepath)

            y_test = labels[test]
            assert np.all(labeled_nodes[test] == test_nodes), '分割後のノードID集合が異なる。random_stateが違うのでは？'
            #assert len(y_pred) == len(y_test)
            #precision, recall, f1, support = precision_recall_fscore_support(y_test, y_pred, average='micro')
            #print(args.resultfile_or_dir, i, precision, recall, f1, support, sep='\t')
            #report = classification_report(y_test, y_pred)
            #print(report)
            print(args.resultfile_or_dir, i, *precision_recall_fscore(test_nodes, y_test, y_pred), sep='\t')
    else:
        resultfile = args.resultfile_or_dir
        # '-'が指定されたら標準入力から読み込む
        if args.resultfile_or_dir == '-':
            resultfile = sys.stdin
        test_nodes, y_pred = util.load_result(resultfile)
        assert np.all(labeled_nodes == test_nodes)
        print(args.resultfile_or_dir, *precision_recall_fscore(test_nodes, labels, y_pred), sep='\t')

def parse_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('labelfile')
    parser.add_argument('resultfile_or_dir')
    parser.add_argument('--random-state', type=int)
    parser.add_argument('--n-splits', type=int, default=10)
    parser.add_argument('--stem', default='result', help='結果ファイル名の文字列')
    parser.add_argument('--ext', default='tsv', help='結果ファイルの拡張子')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    df = main(args)
