# coding: utf-8

from abc import ABCMeta, abstractmethod
from collections import Counter
from typing import List, Any, Tuple
import numpy as np

from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.metrics import accuracy_score

from ..areadata import AreaCoordinateData

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(
    logging.Formatter('%(levelname)s\t%(name)s\t%(asctime)s\t%(message)s'))
logger.addHandler(handler)


class Labels(metaclass=ABCMeta):
    '''reference typing用クラス
    '''
    T = int # Any

    def __contains__(self, item: T):
        raise NotImplementedError()

    def __getitem__(self, key: int):
        raise NotImplementedError()


class Network(metaclass=ABCMeta):
    '''reference typing用クラス'''
    def getrow(self, i: int) -> List[int]:
        raise NotImplementedError()

    @property
    def shape(self) -> Tuple[int, int]:
        raise NotImplementedError()


class NetworkBasedMethod(BaseEstimator, ClassifierMixin, metaclass=ABCMeta):
    '''ネットワークベースユーザ位置推定手法の基底クラス

    network: Type[Network] グラフの隣接行列 (scipy Sparse Matrixなど)
    _labels: Type[Labels] ノードのラベル
    '''

    def __init__(self, network):
        self.network = network
        #self._areadb = AreaCoordinateData()

    def fit(self, x, y):
        '''モデルを訓練する

        Args:
            x (array of int): list of node IDs
            y (array of int): list of labels corresponds each x
        '''
        # labelsは node_id(int;id) -> label(object) が引けるもの
        labels = {u: l for u, l in zip(x, y)}

        # node_idはindexになっているので、長さ|V|の配列にすることもできる
        # そのときラベルなしは、Noneではなくnp.nanであらわす
        #labels = np.ma.masked_array(np.zeros(self.network.shape[0]), mask=True, dtype=np.int)
        #labels[x] = y

        self._labels = labels
        logger.info('train with %d labels', len(self._labels))
        self._area_prob = Counter(y) # 変数名に反して、確率ではなく出現回数。出現回数の総数で割ると確率になる。
        return self

    @abstractmethod
    def predict(self, x):
        raise NotImplementedError()

    def score(self, x, y):
        '''スコア（labelsでの再現率: accuracy）を計算する

        Args:
            x (array of int): list of indexes
            y (array of int): list of labels
        '''
        predicted = self.predict(x)
        acc = accuracy_score(y, predicted)
        return acc


class NeighborsBasedMethod(NetworkBasedMethod):
    '''隣接ノードのみからユーザ位置推定をする手法の基底クラス
    '''

    def __init__(self, network):
        super().__init__(network)

    @abstractmethod
    def select(self, node, locations):
        '''エリアのリストからエリアを1つ選んで返す

        継承したクラスで実装する。
        Args:
            node: int ノードID
            locations: List[int] エリアIDのリスト
        Returns:
            area_idを返す。推定できなかったら0を返す。
        '''
        raise NotImplementedError()

    def predict(self, x):
        '''xに含まれるノードのラベルを推定をする

        Args:
            x: Iterable[int] Node set to estimate
        Returns:
            List[int] Array of area_id
        '''
        predicted = [] #array('I')
        results = []

        labels = self._labels
        node_to_label = lambda x: [labels[n] if n in labels else None for n in x ]
        for i, node in enumerate(x):
            neighbors = self.network.getrow(node)
            locations = node_to_label(neighbors)
            result = self.select(node, locations)
            # area_id, ...
            predicted.append(result[0])
            results.append(result[1:])
            if i % 10000 == 0:
                logger.debug('Inferred %s nodes out of %s', i, len(x))

        # 推定したときに得たその他の情報(推定に使った投票数とか)をクラスに保存する
        self.results = results
        return predicted
