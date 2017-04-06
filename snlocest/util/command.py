# coding: utf-8

'''
推定手法のコマンドラインからの指定
'''

import argparse
from snlocest.methods import MajorityVote, GeometricMedian, ProbabilityModel, RandomNeighbor, NearestNeighbor


METHOD_MAP = {
    'mv': MajorityVote,
    'gm': GeometricMedian,
    'pm': ProbabilityModel,
    'rn': RandomNeighbor,
    'nn': NearestNeighbor,
}

def snlocest_method(string):
    try:
        return METHOD_MAP[string]
    except KeyError:
        raise argparse.ArgumentTypeError('Implemented method names are [{}]'.format(', '.join(METHOD_MAP.keys())))
