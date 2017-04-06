# coding: utf-8

'''
K分割交差検証をする

nを指定すると、そのn番目の分割の推定のみを実行する
'''

import sys
import os.path
import numpy as np
from sklearn.model_selection import KFold
import snlocest.util as util
from snlocest.graph import SpMatLikeDOLGraph
from snlocest.methods import MajorityVote
from snlocest.util.command import snlocest_method
from snlocest.methods import GeometricMedian, ProbabilityModel
from snlocest.areadata import AreaCoordinateData
from snlocest.distance import build_area_distance_func


def predict(clf, graph, x, y, train, test):
    x_train, y_train = x[train], y[train]
    x_test, y_test = x[test], y[test]
    clf.fit(x_train, y_train)
    predicted = clf.predict(x_test)
    return x_test, predicted

def main(args):
    '''
    Args:
        args.edgefile
        args.labelfile
        args.outputdir
        args.n_splits
        args.n_jobs (optional)
        args.random_state (default: 100)
        args.nth (optional)
    '''
    #n_jobs = getattr(args, 'n_jobs', 1)
    random_state = args.random_state if args.random_state is not None else 100
    n_splits = args.n_splits
    Method = args.method

    graph, x, y = util.load_dataset(args.edgefile, args.labelfile, SpMatLikeDOLGraph)

    coord_data = AreaCoordinateData()
    distance = build_area_distance_func(coord_data)

    params = {'network': graph}
    if Method == GeometricMedian or Method == ProbabilityModel:
        params['distfunc'] = distance

    clf = Method(**params)
    if hasattr(args, 'stratify'):
        #StratifiedKFold # クラスバランスが同じになるように分割する
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    else:
        cv = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    x = np.asarray(x)
    y = np.asarray(y)
    if args.nth is None:
        for i, (train, test) in enumerate(cv.split(x)):
            x_test, predicted = predict(clf, graph, x, y, train, test)
            output_path = os.path.join(args.outputdir, 'result_{}.tsv'.format(i))
            with open(output_path, 'w') as fp:
                util.write_result(x_test, predicted, graph, outfile=fp)
            print('Saved at:', output_path, file=sys.stderr)
    else:
        # nth番目のテストセットの推定だけをして標準出力へ書き出す
        for i, (train, test) in enumerate(cv.split(x)):
            if i != args.nth:
                continue
            x_test, predicted = predict(clf, graph, x, y, train, test)
            util.write_result(x_test, predicted, graph, outfile=sys.stdout)


def parse_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('edgefile')
    parser.add_argument('labelfile')
    parser.add_argument('method', type=snlocest_method)
    parser.add_argument('--n-jobs', type=int, default=1, help='The number of CPUs to use')
    parser.add_argument('--n-splits', type=int, default=10, help='K-fold')
    parser.add_argument('--random-state', type=int)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--outputdir')
    group.add_argument('--nth', type=int, help='If this parameter is given, only the nth test set is predicted.')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    main(args)
