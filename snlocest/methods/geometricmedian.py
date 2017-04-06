# coding: utf-8

from collections import Counter
from .base import NeighborsBasedMethod


class GeometricMedian(NeighborsBasedMethod):
    '''周囲ののGeometric Medianを推定位置とする手法

    Reference:
    That's What Friends Are For: Inferring Location in Online Social Media Platforms Based on Social Relationships.
    Jurgens, David.
    Proceedings of the 7th International AAAI Conference on Weblogs and Social Media.
    Cambridge, Massachusetts, 2013, pp. 273--282, (ICWSM '13).
    Section 2.1 Equation (1)
    '''
    header = ['area_id', 'fdegree', 'ldegree']

    def __init__(self, network, distfunc):
        super().__init__(network)
        self.distfunc = distfunc


    def select(self, _, locations):
        '''friendsのgeometric medianを計算する
        Args:
            friends(list of int): 友人のuser_idのリスト
        Returns:
            推定結果 (area_id, fdegree, ldegree)
            エリアID、友人の数（次数）、ラベルの付いている友人の数

        '''
        num_friends = len(locations)

        # ラベルなしをあらわすNoneを除外
        friends_areas = [l for l in locations if l]
        nlabels = len(friends_areas)

        # ラベルの付いた友人がいない場合
        if not nlabels:
            return (0, num_friends, nlabels)

        c = Counter(friends_areas)

        min_dist = float('inf')
        med_area = None
        areas = list(c.keys())
        areas.sort(key=lambda a: self._area_prob[a], reverse=True) # エリアの出現回数降順
        for a1 in areas:
            dist_sum = 0
            for a2 in areas:
                dist = self.distfunc(a1, a2)
                dist_sum += dist * c[a2]
                if min_dist < dist_sum:
                    break
            if min_dist > dist_sum:
                min_dist = dist_sum
                med_area = a1
        return (med_area, num_friends, nlabels)
