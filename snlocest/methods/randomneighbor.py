# coding: utf-8

import random
from .base import NeighborsBasedMethod


class RandomNeighbor(NeighborsBasedMethod):
    '''隣接ノードのラベルからランダムに推定する手法
    '''
    header = ['area_id', 'degree', 'labeled_degree']

    def __init__(self, network, random_state=0):
        super().__init__(network)
        self.random_state = random_state
        random.seed(random_state)

    def select(self, _, locations):
        num_friends = len(locations)
        friends_areas = [l for l in locations if l]
        nlabels = len(friends_areas)

        # ラベルの付いた友人がいない場合
        if not nlabels:
            return (0, num_friends, nlabels)

        sel = random.randrange(nlabels)
        return (friends_areas[sel], num_friends, nlabels)
