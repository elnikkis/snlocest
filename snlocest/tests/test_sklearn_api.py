# coding: utf-8

'''
scikit-learnのAPIで推定手法が利用できる
'''


from sklearn.model_selection import train_test_split, LeaveOneOut, KFold, cross_val_score
from sklearn.metrics import precision_recall_fscore_support, classification_report

from snlocest.graph import SpMatLikeDOLGraph, CSRGraph
from snlocest.methods import MajorityVote
from snlocest.areadata import AreaCoordinateData
from snlocest.distance import build_area_distance_func
from snlocest.util import load_dataset

EDGEFILE = 'testdata/test-dataset/networks/f_follower.tsv'
LABELFILE = 'testdata/test-dataset/groundtruth/labels.tsv'


def test_api():
    graph, x, y = load_dataset(EDGEFILE, LABELFILE, SpMatLikeDOLGraph)
    x_train, x_test, y_train, y_test = train_test_split(x, y, random_state=123)
    clf = MajorityVote(graph).fit(x_train, y_train)
    predicted = clf.predict(x_test)
    score = clf.score(x_test, y_test)
    #report = classification_report(y_test, predicted)
    #print(report)

def test_cross_validation():
    graph, x, y = load_dataset(EDGEFILE, LABELFILE, SpMatLikeDOLGraph)
    clf = MajorityVote(graph)
    cv = KFold(n_splits=5, shuffle=True, random_state=123)
    scores = cross_val_score(clf, x, y, cv=cv)

def test_csr_api():
    graph, x, y = load_dataset(EDGEFILE, LABELFILE, CSRGraph)
    x_train, x_test, y_train, y_test = train_test_split(x, y, random_state=123)
    clf = MajorityVote(graph).fit(x_train, y_train)
    predicted = clf.predict(x_test)
    score = clf.score(x_test, y_test)
