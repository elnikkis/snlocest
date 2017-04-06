# coding: utf-8

'''
This module provides cached geographic distance functions.
メモ化のついた距離関数を提供する。

対応している距離関数：
 - vincenty (geopy)
 - #great_circle (geopy)
 - hubeny formula

Usage:
p1 = (lon, lat)
p2 = (lon, lat)
from snlocest.distance import distance
distance(p1, p2) # this method is cached
'''

from functools import lru_cache
from geopy.distance import vincenty as _vincenty
from .hubeny_distance import hubeny_distance as _hubeny


CACHE_SIZE = 2 ** 19

@lru_cache(maxsize=CACHE_SIZE)
def hubeny(p1, p2):
    return _hubeny(p1, p2)

@lru_cache(maxsize=CACHE_SIZE)
def vincenty(p1, p2):
    return _vincenty(p1, p2).meters

_meter_vincenty = lambda p1, p2: _vincenty(p1, p2).meters

def build_area_distance_func(area_coord_data, distfunc=_meter_vincenty):
    '''Build a cached distance function between area_ids.

    エリアの座標データarea_coord_dataと地理的な距離を計算する関数distfuncを使って、
    lru_cacheの付いた、エリア間の距離を計算する関数を作って返す

    Args:
        area_coord_data: snlocest.areadata.AreaCoordinateData
        distfunc: Callable[[Tuple[float, float], Tuple[float, float]], float] (optional)
    Returns:
        A distance function between area_ids
    '''
    @lru_cache(maxsize=CACHE_SIZE)
    def distance(a1, a2):
        '''エリアa1とa2のあいだの地理的な距離を返す'''
        p1 = area_coord_data.get_point(a1)
        p2 = area_coord_data.get_point(a2)
        return distfunc(p1, p2)
    distance.areadata = area_coord_data
    distance.distfunc = distfunc
    return distance

distance = vincenty
