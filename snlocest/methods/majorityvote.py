# coding: utf-8

import sys
from collections import Counter
from .base import NeighborsBasedMethod


class MajorityVote(NeighborsBasedMethod):
    '''ネットワークベースの多数決で位置推定をする手法

    隣接ノードのラベルで多数決をして、ノードのラベルを推定する。

    Reference:
    Inferring the Location of Twitter Messages Based on User Relationships.
    Davis Jr., Clodoveu A., Pappa, Gisele L., de Oliveira, Diogo Rennó Rocha, de L. Arcanjo, Filipe
    Transactions in GIS. 2011, vol. 15, no. 6, pp. 735--751
    Section 3.2 Location Inference Method
    '''
    header = ['area_id', 'degree', 'label_degree', 'vote_count']

    def __init__(self, network,
                 min_friends=0, max_friends=sys.maxsize, min_votes=0):
        super().__init__(network)
        self.min_friends = min_friends
        self.max_friends = max_friends
        self.min_votes = min_votes

    def _is_ok_num_friends(self, num_friends):
        '''友人数による推定するかどうかのフィルタ

        Returns:
            Trueなら推定する。Falseなら推定しない。
        '''
        #TODO
        return True

    def select(self, _, locations):
        ''' 周りのユーザのエリアで多数決をした結果のエリアを返す

        Returns:
            inferred_area_id, fdegree, ldegree, vote_count
            推定したエリアID、出エッジの総数、ラベル付きの友人数、最大投票数
        '''
        num_friends = len(locations)

        # TODO: check min_friends and max_friends
        if not self._is_ok_num_friends(num_friends):
            return None

        # ラベルなしをあらわすNoneを除外する
        friends_areas = [l for l in locations if l]
        nlabels = len(friends_areas)

        # ラベルの付いた友人がいない場合
        if not nlabels:
            return (0, num_friends, nlabels, 0)

        c = Counter(friends_areas)
        ordered_areas = self._sort_results(c.items())

        # TODO: check min_location_votes
        return (ordered_areas[0][0], num_friends, nlabels, ordered_areas[0][1])

    def _sort_results(self, areas):
        '''area_id, vote_countのリストを受け取り、0番目が推定結果になるようソートして返す
        '''
        # エリアのソートは、投票数が多い順、エリア出現回数が多い順、エリアID順、にする
        # ソートのデフォルトは昇順
        s = sorted(areas) # area_id昇順
        s.sort(key=lambda x: self._area_prob[x[0]], reverse=True) # エリア出現回数降順
        s.sort(key=lambda x: x[1], reverse=True) # 投票数降順
        return s
