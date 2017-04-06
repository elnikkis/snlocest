# coding: utf-8

import os
from math import log
import pickle
from collections import defaultdict, Counter

import numpy as np
from scipy.optimize import curve_fit

from .base import NeighborsBasedMethod

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(
    logging.Formatter('%(levelname)s\t%(name)s\t%(asctime)s\t%(message)s'))
logger.addHandler(handler)


class NaiveProbabilityModel(NeighborsBasedMethod):
    '''友人関係と距離を確率モデルであらわして最尤推定する手法

    Reference:
    Find Me If You Can: Improving Geographical Prediction with Social and Spatial Proximity.
    Backstrom, Lars, Sun, Eric, Marlow, Cameron.
    Proceedings of the 19th International Conference on World Wide Web.
    Raleigh, North Carolina, USA, ACM, 2010, pp.61--70, (WWW '10).
    '''
    header = ['area_id', 'degree', 'labeled_degree', 'score', 'score1', 'score2']

    def __init__(self, network, distfunc, a=0.0019, b=0.196, c=1.05, meter=False):
        super().__init__(network)
        self.a = float(a)
        self.b = float(b)
        self.c = float(c)
        logger.debug('a={}, b={}, c={}'.format(a, b, c))
        self.distfunc = distfunc
        self.meter = meter # 与えられるdistanceの単位がmeterならTrue, mileならFalse

    def _probability(self, distance):
        '''距離からエッジが存在する確率を返す関数

        論文に書いてあるモデル式で計算している。

        Reference:
            figure 7
        '''
        if self.meter:
            # 1609.34 meter = 1 mile
            distance = distance / 1609.34
        return self.a * (distance + self.b) ** -self.c

    def _likelihood(self, area_id, neighbors):
        '''尤度を計算する

        This method is very computational expensive.
        Args:
            area_id: l_u
            neighbors: labeld neighbors of u

        Reference:
            expression in Section 4: likelihood of l_u
            p.66 の右側真ん中の表示領域が大きい式
        '''
        V = self.network.shape[0]
        neighbors = self.network.getrow(u)
        score1 = 0
        score2 = 0
        for v in range(V):
            l_v = self._labels[v]
            d = self.distfunc(area_id, l_v)
            p = self._probability(d)
            if v in neighbors:
                # first term
                score1 += log(p)
            else:
                # second term
                score2 += log(1 - p)
        return (score1 + score2, score1, score2)

    def _compute_likelihoods(self, node, friends_areas):
        neighbors = [n for n in self.network.getrow(node) if n in self._labels]
        scores = [(a,) + self._likelihood(a, neighbors) for a in self.areadata]
        return scores

    def select(self, node, locations):
        '''推定したarea_id を返す

        nodeの位置をl_uとしたときに尤度が最大になるl_uを選んで返す。

        Reference:
            Section 4 PREDICTING LOCATION
        Returns:
            inferred_area_id, degree, number of labeled neighbors, score, score1, score2
        '''
        num_friends = len(locations)
        friends_areas = [l for l in locations if l]
        nlabels = len(friends_areas)

        # ラベルの付いた友人がいない場合
        if not nlabels:
            return (0, num_friends, nlabels, 0, 0, 0)

        scores = self._compute_likelihoods(node, friends_areas)
        #import pdb; pdb.set_trace()

        # likelihoodが降順、エリアの出現回数が降順、エリアID昇順
        # それでも同じだったら、左辺(score1)昇順(小さい順）
        scores.sort() # area_id昇順
        scores.sort(key=lambda x: self._area_prob[x[0]], reverse=True) # エリア出現回数降順
        scores.sort(key=lambda x: x[1], reverse=True)

        return (scores[0][0], num_friends, nlabels) + scores[0][1:4]


class OptimizedProbabilityModel(NaiveProbabilityModel):
    def __init__(self, network, distfunc, a=0.0019, b=0.196, c=1.05, meter=False):
        super().__init__(network, a=a, b=b, c=c, distfunc=distfunc, meter=meter)
        self._gamma_model = {} # precomputed gamma
        self._trained = False

    def _memo_gamma_l(self, area_id):
        if area_id in self._gamma_model:
            return self._gamma_model[area_id]
        value = self._gamma_l(area_id)
        self._gamma_model[area_id] = value
        return value

    def _gamma_l(self, area_id):
        '''
        log(gamma_l(area_id)) = \sum_{a \in A} c(a)log[1 - p(dist(area_id, a))]
        A: set of area_ids
        c(a): 学習データにエリアaが出現する回数
        Reference:
            論文p.67左側一番目(文中)に出てくる式
        '''
        score = 0
        for l in self._area_prob:
        #for l in self.distfunc.areadata:
            d = self.distfunc(area_id, l)
            p = self._probability(d)
            score += log(1 - p) * self._area_prob[l]
        return score

    #def fit(self, X, y):
    #    super().fit(X, y)
    #    return self

    def _compute_likelihoods(self, node, friends_areas):
        scores = [(a,) + self._likelihood(a, friends_areas) for a in sorted(set(friends_areas))]
        return scores

    def _likelihood(self, area_id, locations):
        '''尤度を計算する

        log(gamma(l, u)) = \sum_{v \in N_u} { log(p(dist(l_u, l_v))) - log(1 - p(dist(l_u, l_v))) }
        Args:

        Reference:
            p.67
        '''
        score = 0
        c = Counter(locations)
        for a in sorted(c.keys()):
            d = self.distfunc(area_id, a)
            p = self._probability(d)
            score += c[a] * (log(p) - log(1 - p))

        #for l_v in locations:
        #    d = self.distfunc(area_id, l_v)
        #    p = self._probability(d)
        #    score += log(p) - log(1 - p)

        g_l = self._memo_gamma_l(area_id)
        return (score + g_l, score, g_l)


class LearnProbabilityModel(OptimizedProbabilityModel):
    '''
    学習データからa, b, cのパラメータ獲得をするProbability Model
    '''
    def __init__(self, network):
        super().__init__(network)
        raise NotImplementedError('このクラスは完成していません')

    """
    def fit(self, X, y):
        super().fit(X, y)
        # 学習データからa, b, cを計算する
        # 各エッジの距離を計算する
        E = 0 # closedなエッジ数
        dists = defaultdict(int)
        for v in self.network.users_iter():
            # 居住地の付いているノード同士のみしか距離計算できない
            if v not in self._labels:
                continue
            av = self._labels.get_area_id(v)
            for n in self.network.get_friends(v):
                if n not in self._labels:
                    continue
                E += 1
                #d = self._distance(av, self._labels.get_area_id(n))
                d = self.distfunc(av, self._labels[n])
                dists[d] += 1

        xx = np.array(sorted(dists.keys()))
        yy = np.array([dists[x] for x in xx])
        yy = yy / E
        func = lambda x, a, b, c: a * (x + b) ** c
        params = curve_fit(func, xx, yy, maxfev=100000)[0]
        self.a = params[0]
        self.b = params[1]
        self.c = params[2]
        logger.info('E={}'.format(E))
        logger.info('a={}, b={}, c={}'.format(self.a, self.b, self.c))
        return self
    """

    def fit(self, X, y):
        super().fit(X, y)
        # 学習データからa, b, cを計算する
        # 各エッジの距離を計算する
        E = 0 # closedなエッジ数
        dists = []
        for v in self.network.users_iter():
            # 居住地の付いているノード同士のみしか距離計算できない
            if v not in self._labels:
                continue
            av = self._labels.get_area_id(v)
            for n in self.network.get_friends(v):
                if n not in self._labels:
                    continue
                E += 1
                #d = self._distance(av, self._labels.get_area_id(n))
                d = self.distfunc(av, self._labels[n])
                dists.append(d)

        dists = np.array(dists)
        yy, binEdges = np.histogram(dists/1000, bins=500)
        xx = binEdges[0:-1]
        yy = yy / E
        func = lambda x, a, b, c: a * (x + b) ** c
        params = curve_fit(func, xx, yy, maxfev=100000)[0]
        self.a = params[0]
        self.b = params[1]
        self.c = params[2]
        logger.info('E={}'.format(E))
        logger.info('a={}, b={}, c={}'.format(self.a, self.b, self.c))
        return self
