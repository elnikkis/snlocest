# coding: utf-8

import numpy as np
from .base import NeighborsBasedMethod


class NearestNeighbor(NeighborsBasedMethod):
    '''最近傍のノードとの距離を計算する

    最も近いノードを知っている（神）
    O(ノード数x平均エッジ数)
    '''
    header = ['area_id', 'degree', 'labeled_degree', 'distance']

    def __init__(self, network, distfunc):
        super().__init__(network)
        self.distfunc = distfunc

    def select(self, node, locations):
        '''
        Returns:
            area_id, num_friends, ラベル付き友人数, min_distance
        '''
        num_friends = len(locations)
        friends_areas = [l for l in locations if l]
        nlabels = len(friends_areas)

        # 自分の位置が不明
        if node not in self._labels:
            return (0, num_friends, nlabels, None)

        # 自分の位置を知っている
        u = self._labels[node]

        # 友人がいない
        if not nlabels:
            return (0, num_friends, nlabels, None)

        dists = [self.distfunc(u, v) for v in friends_areas]
        idx = np.argmin(dists, axis=0)
        return friends_areas[idx], num_friends, nlabels, dists[idx]
