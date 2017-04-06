# coding: utf-8

'''
ここのGraphはedgelistをstr, strとして読み込めるように作られている
int, intだとしたら、もっとコンパクトになる
'''

import csv
import numpy as np
from abc import ABCMeta, abstractmethod
from itertools import chain
from scipy.sparse import coo_matrix, csr_matrix
from snlocest.util import load_labellist
from snlocest.largedict import LargeDict


def load_dsv_by_pandas(filepath, delimiter, dtype):
    import pandas as pd
    df = pd.read_csv(filepath, sep=delimiter, dtype=dtype, header=None)
    return df.as_matrix()

def load_dsv_by_numpy(filepath, delimiter, dtype):
    a = np.genfromtxt(filepath, dtype=dtype, delimiter=delimiter)
    return a

def load_dsv(filepath, delimiter='\t', dtype=np.int64):
    try:
        import pandas as pd
        func = load_dsv_by_pandas
    except:
        func = load_dsv_by_numpy
    return func(filepath, delimiter, dtype)


def load_adj_matrix(edgefile, delimiter='\t', numbers=False):
    '''Load adjacency matrix from edge list

    Args:
        edgefile: file path to edge list (DSV format)
        delimiter (optional): delimiter of edge list
        numbers (optional): nodes are represented by numbers of 0 to |V| - 1 (int64)
            edge listのノードが0から|V|-1までのint64で表現されている（Falseならstrとして読み込む）
    Returns:
        Adjacency matrix (scipy coo_matrix), List of nodes
    '''
    if numbers:
        dtype = np.int64
    else:
        dtype = str

    arr = load_dsv(edgefile, delimiter=delimiter, dtype=dtype)

    nodes = sorted(set(arr[:, 0]) | set(arr[:, 1])) # id_to_node
    #nodes = sorted(set(np.hstack([arr[:, 0], arr[:, 1]]))) # id_to_node
    if numbers:
        node_to_idx = nodes
    else:
        node_to_idx = dict(zip(nodes, range(len(nodes))))
        func = lambda a: node_to_idx[a]
        vfunc = np.vectorize(func)
        arr = vfunc(arr)

    row = arr[:, 0]
    col = arr[:, 1]
    data = np.ones_like(row)
    V = len(nodes)
    coo = coo_matrix((data, (row, col)), shape=(V, V), copy=False)
    return coo, nodes, node_to_idx


class Graph(metaclass=ABCMeta):
    @property
    @abstractmethod
    def nodes(self):
        '''Returns an iterator of nodes'''
        raise NotImplementedError()

    @property
    def edges(self):
        '''Returns an iterator of edges'''
        for u in self.nodes:
            for v in self.neighbors(u):
                yield (u, v)

    @abstractmethod
    def neighbors(self, n):
        '''Returns a list of neighbors of node n'''
        raise NotImplementedError()

    @property
    def num_nodes(self):
        '''Returns the number of nodes'''
        return len(list(self.nodes))

    @property
    def num_edges(self):
        '''Returns the number of edges'''
        return len(list(self.edges))

    @abstractmethod
    def load_edgelist(self, filename, delimiter='\t'):
        raise NotImplementedError()

    @abstractmethod
    def load_labellist(self, filename, delimiter='\t'):
        raise NotImplementedError()

    @property
    @abstractmethod
    def labeled_nodes(self):
        '''Returns a list of labeled nodes'''
        raise NotImplementedError()

    @property
    @abstractmethod
    def labels(self):
        '''Returns a list of labels corresponding labeled_nodes'''
        raise NotImplementedError()



class SparseMatrixLike(metaclass=ABCMeta):
    '''Sparse Matrixのように振る舞う

    #vto_nodeidx(x)
    #vto_nodename(x)
    to_nodename(x)
    TODO: いろいろプロパティが足りないと思う
    '''
    @abstractmethod
    def getrow(self, i):
        raise NotImplementedError()

    @property
    @abstractmethod
    def nodes(self):
        '''Returns an iterator of nodes'''
        raise NotImplementedError()

    @property
    @abstractmethod
    def shape(self):
        raise NotImplementedError()


class CSRGraph(Graph, SparseMatrixLike):
    '''Compressed Sparse Row Matrixでグラフを保存しているクラス

    pros: pandasのおかげで読み込みが早い
    cons: neighborsが遅い 50us
    '''

    def __init__(self):
        # CSR Matrix (indices |E| + data |E| + indptr |V|)
        self._adjmat = csr_matrix((1, 1))
        # node list |V|
        self._nodes = [] # translation table of index to node
        self._labeled_nodes = []
        self._labels = []
        # dict |V|
        self._node_to_idx = {} # translation table of node to index

    def _update_table(self):
        '''self._nodesとself._labeled_nodesをもとに、
        self._nodesをすべてのノードを含むよう更新し、新しいself._node_to_idxを作る'''
        set_nodes = set(self._nodes)
        self._nodes.extend(n for n in self._labeled_nodes if n not in set_nodes)
        self._node_to_idx = dict(zip(self._nodes, range(len(self._nodes))))

        n_nodes = self.num_nodes
        a = self._adjmat.tocoo()
        self._adjmat = csr_matrix((a.data, (a.row, a.col)), shape=(n_nodes, n_nodes), copy=False)
        #self._adjmat = csr_matrix((a.data, a.indices, a.indptr), shape=(n_nodes, n_nodes), copy=False)

    def load_edgelist(self, filename, delimiter='\t'):
        adj, nodes, node_to_idx = load_adj_matrix(filename, delimiter=delimiter)
        self._adjmat = adj.tocsr()
        self.nodes = nodes
        #self._id_to_node = nodes
        return self

    def to_nodeidx(self, a):
        return self._node_to_idx[str(a)]

    def to_nodename(self, a):
        return self._nodes[a]

    def vto_nodeidx(self, x):
        return [self._node_to_idx[a] for a in x]

    def vto_nodename(self, x):
        return [self._nodes[a] for a in x]

    def load_labellist(self, filename, delimiter='\t'):
        labeled_nodes, labels = load_labellist(filename)
        self.labeled_nodes = labeled_nodes
        self._labels = labels
        return self

    @property
    def labeled_nodes(self):
        return self._labeled_nodes

    @labeled_nodes.setter
    def labeled_nodes(self, value):
        self._labeled_nodes = value
        # self._node_to_idxは_nodesと_labeled_nodesがセットされたときに更新する
        self._update_table()

    @property
    def labels(self):
        return self._labels

    @property
    def nodes(self):
        '''Return a list of nodes'''
        return self._nodes

    @nodes.setter
    def nodes(self, value):
        self._nodes = value
        # self._node_to_idxは_nodesと_labeled_nodesがセットされたときに更新する
        self._update_table()

    @property
    def num_edges(self):
        return int(self._adjmat.sum())

    def neighbors(self, n):
        '''Return a list of the neighbors of node n'''
        try:
            i = self._node_to_idx[n]
        except ValueError:
            if i < self.num_nodes:
                return []
            raise IndexError("node [%s] is not in this graph" % n)
        neighbors = self.getrow(i)
        #return self.vto_nodename(neighbors)
        return [self.to_nodename(n) for n in neighbors]

    def getrow(self, i):
        '''node_idではなくindexを受け取り、indexのまま返す
        '''
        #r = self._adjmat.getrow(i)
        #neighbors = r.indices

        # fast getrow
        indptr = self._adjmat.indptr
        neighbors = self._adjmat.indices[indptr[i]:indptr[i+1]]
        return neighbors

    @property
    def shape(self):
        return self._adjmat.shape


class DictOfListGraph(Graph):
    '''Dict of list でグラフを保存しているクラス

    pros: neighborsが早い 500ns
    cons: 読み込みが遅い
    '''

    def __init__(self):
        # nodeをあらわすstrだけでedgelistのファイルサイズくらいある...
        self._adj = LargeDict() # dict |V| + list K * |V|
        self._nodes = [] # : list
        self._labeled_nodes = [] # : list
        self._labels = [] # : list

    def _update_nodes(self):
        # self._adj, self.labeled_nodesをもとにself._nodesを作る
        self._nodes = sorted(set(self._adj.keys()) | set(chain.from_iterable(self._adj.values())) | set(self.labeled_nodes))

    def load_edgelist(self, filename, delimiter='\t'):
        with open(filename, 'r') as fp:
            for line in csv.reader(fp, delimiter=delimiter):
                self._add_edge(line[0], line[1])
        self._update_nodes()
        return self

    def load_labellist(self, labelfile, delimiter='\t'):
        nodes, labels = load_labellist(labelfile)
        self._labeled_nodes = nodes
        self._labels = labels
        self._update_nodes()
        return self

    @property
    def labeled_nodes(self):
        return self._labeled_nodes

    @property
    def labels(self):
        return self._labels

    @property
    def nodes(self):
        return self._nodes

    def neighbors(self, n):
        return self._adj.get(n, list)

    def _add_edge(self, src, dst):
        n = self._adj.get(src, list)
        n.append(dst)
        self._adj[src] = n


class SpMatLikeDOLGraph(SparseMatrixLike):
    '''DictOfListGraphクラスをSparse Matrixと同じように操作できるようにするクラス

    Sparse Matrixに擬態するためのクラス。
    '''

    def __init__(self):
        self._graph = DictOfListGraph()
        self._node_to_idx = {}

    def to_nodeidx(self, a):
        return self._node_to_idx[a]

    def to_nodename(self, a):
        return self._graph.nodes[a]

    def vto_nodeidx(self, x):
        return [self._node_to_idx[a] for a in x]

    def vto_nodename(self, x):
        return [self._graph.nodes[a] for a in x]

    def _update_table(self):
        self._node_to_idx = dict(zip(self._graph.nodes, range(len(self._graph.nodes))))

    def load_edgelist(self, filename, delimiter='\t'):
        self._graph.load_edgelist(filename, delimiter)
        self._update_table()
        return self

    def load_labellist(self, filename, delimiter='\t'):
        self._graph.load_labellist(filename, delimiter)
        self._update_table()
        return self

    def getrow(self, i):
        #return self.vto_nodeidx(self._graph.neighbors(self.to_nodename(i)))
        return [self.to_nodeidx(n) for n in self._graph.neighbors(self.to_nodename(i))]

    def shape(self):
        V = len(self._nodes)
        return (V, V)

    @property
    def nodes(self):
        return self._graph.nodes

    @property
    def labeled_nodes(self):
        return self._graph.labeled_nodes

    @property
    def labels(self):
        return self._graph.labels


if __name__ == '__main__':
    #path = 'data/datasets/active-closed/networks/f_mutual.tsv'
    path = 'data/datasets/full-closed/networks/f_mutual.tsv'
    #gr1 = CSRGraph().load_edgelist(path)
    gr2 = DictOfListGraph().load_edgelist(path)
