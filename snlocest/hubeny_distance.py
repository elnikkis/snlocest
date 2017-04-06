# -*- coding: utf-8 -*-

'''
ヒュベニの公式を利用して、地球上での距離を計算する。

http://yamadarake.jp/trdi/report000001.html
Fig.1 の式を実装した。
'''

import math

A = 6378137.000
B = 6356752.314245
E2 = (A**2 - B**2) / A**2
M_NUR = A * (1 - E2)


def hubeny_distance(c1, c2):
    '''
    c1とc2の地球上での距離を計算して返す [m]
    Args:
        c1: coordinate tuple (lat, lon)
        c2: coordinate tuple (lat, lon)
    Returns:
        2点間の距離
    '''
    lat1 = math.radians(c1[0])
    lon1 = math.radians(c1[1])
    lat2 = math.radians(c2[0])
    lon2 = math.radians(c2[1])
    return hubeny_distance_radian(lat1, lon1, lat2, lon2)


def hubeny_distance_radian(lat1, lon1, lat2, lon2):
    '''
    地球上での距離を計算して返す [m]
    Args:
        lat1: 緯度 y1 [radian]
        lon1: 経度 x1 [radian]
        lat2: 緯度 y2 [radian]
        lon2: 経度 x2 [radian]
    '''
    dx = lon1 - lon2
    dy = lat1 - lat2
    mu_y = (lat1 + lat2) / 2

    w = math.sqrt(1 - E2 * math.sin(mu_y)**2)
    m = M_NUR / w**3
    n = A / w

    tmp1 = (dy * m) ** 2
    tmp2 = (dx * n * math.cos(mu_y)) ** 2
    return math.sqrt(tmp1 + tmp2)

if __name__ == '__main__':
    c1 = (36.10056, 140.09111)
    c2 = (35.65500, 139.74472)
    p1 = (c1[1], c1[0])
    p2 = (c2[1], c2[0])
    d = hubeny_distance(c1, c2)
    print(c1, c2)
    print(d)
