# coding: utf-8

from sklearn.model_selection import train_test_split

from snlocest.graph import SpMatLikeDOLGraph
from snlocest.areadata import AreaCoordinateData
from snlocest.distance import build_area_distance_func
from snlocest.util import load_dataset
from snlocest.methods import MajorityVote, GeometricMedian, ProbabilityModel, RandomNeighbor


EDGEFILE = 'testdata/test-dataset/networks/f_follower.tsv'
LABELFILE = 'testdata/test-dataset/groundtruth/labels.tsv'


def test_methods():
    graph, x, y = load_dataset(EDGEFILE, LABELFILE, SpMatLikeDOLGraph)
    x_train, x_test, y_train, y_test = train_test_split(x, y, random_state=123)

    coord_data = AreaCoordinateData()
    distance = build_area_distance_func(coord_data)

    methods = [MajorityVote, GeometricMedian, ProbabilityModel, RandomNeighbor]
    for Method in methods:
        # prepare parameters
        params = {'network': graph}
        if Method == GeometricMedian or Method == ProbabilityModel:
            params['distfunc'] = distance

        clf = Method(**params).fit(x_train, y_train)
        score = clf.score(x_test, y_test)
