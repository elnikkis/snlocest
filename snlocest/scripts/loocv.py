# coding: utf-8

'''
Leave-one-out交差検証をする
'''

from sklearn.model_selection import LeaveOneOut, cross_val_predict
from snlocest.util import load_dataset, write_result
from snlocest.graph import SpMatLikeDOLGraph
from snlocest.util.command import snlocest_method
from snlocest.methods import GeometricMedian, ProbabilityModel, NearestNeighbor
from snlocest.areadata import AreaCoordinateData
from snlocest.distance import build_area_distance_func



def fast(edgefile, labelfile, Method, extra_info=False):
    # 学習1回なので早い。ただし、推定手法が推定対象のノードのラベル情報をみないときのみ正しい結果になる。
    graph, x, y = load_dataset(edgefile, labelfile, SpMatLikeDOLGraph)

    coord_data = AreaCoordinateData()
    distance = build_area_distance_func(coord_data)

    params = {'network': graph}
    if Method == GeometricMedian or Method == ProbabilityModel or Method == NearestNeighbor:
        params['distfunc'] = distance

    clf = Method(**params)
    clf.fit(x, y)
    predictions = clf.predict(x)
    if not extra_info:
        write_result(x, predictions, graph)
    else:
        info = clf.results
        write_result(x, predictions, graph, info=info)

def main(edgefile, labelfile, Method, njobs=1, extra_info=False):
    #TODO methodのparameterを受け取れるようにする
    graph, x, y = load_dataset(edgefile, labelfile, SpMatLikeDOLGraph)

    coord_data = AreaCoordinateData()
    distance = build_area_distance_func(coord_data)

    params = {'network': graph}
    if Method == GeometricMedian or Method == ProbabilityModel or Method == NearestNeighbor:
        params['distfunc'] = distance

    clf = Method(**params)
    loo = LeaveOneOut()
    predictions = cross_val_predict(clf, x, y, cv=loo, n_jobs=njobs, pre_dispatch='2*n_jobs')
    if not extra_info:
        write_result(x, predictions, graph)
    else:
        info = clf.results
        write_result(x, predictions, graph, info=info)

def parse_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('edgefile')
    parser.add_argument('labelfile')
    parser.add_argument('method', type=snlocest_method)
    parser.add_argument('--n-jobs', type=int, default=1, help='The number of CPUs to use')
    parser.add_argument('--fast', action='store_true', default=False, help='並列化しない')
    parser.add_argument('--extra', action='store_true', default=False, help='推定時の他の情報を出力するかどうか(default: False)')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    if args.fast:
        fast(args.edgefile, args.labelfile, args.method, extra_info=args.extra)
    else:
        # 並列数を増やしても早くならない気がする。推定時間よりオーバーヘッドが大きい
        main(args.edgefile, args.labelfile, args.method, njobs=args.n_jobs)
