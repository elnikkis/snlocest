# coding: utf-8

'''
エントリー数が44739243くらいを超えても使えるdictもどき
ハッシュの偏りがなく理想的な状況での最大エントリー数は44739243*10くらい
'''

from itertools import chain
from collections.abc import Mapping


class LargeDict(Mapping):
    def __init__(self):
        self.d = [{} for i in range(10)]

    def toint(self, item):
        # return str(item).encode()[-1] % 10  # hashの方が早い
        # 永続化だめ（起動毎に値が変わる）
        return hash(item) % 10

    def __setitem__(self, key, value):
        self.d[self.toint(key)][key] = value

    def __getitem__(self, key):
        return self.d[self.toint(key)][key]

    def __iter__(self):
        return chain.from_iterable(self.d)

    def __contains__(self, item):
        return item in self.d[self.toint(item)]

    def __len__(self):
        return sum([len(s) for s in self.d])

    def get(self, key, default):
        if key not in self:
            self[key] = default()
        return self[key]

    def print_usage(self):
        l = [len(s) for s in self.d]
        print('各辞書のエントリ数:', l)
