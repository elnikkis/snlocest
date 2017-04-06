# coding: utf-8

'''
rtreeを使ってエリア照合をする

input
gxml: gxmlparser.py の出力
code, MultiPolygon(WKT)
ken, city, seq_no2, ken_name, gst_name, css_name, moji, x_code, y_code, polygon のTSV

infile:
status_id, user_id, lon, lat

output:
status_id, user_id, area_id

'''

import sys
import csv
csv.field_size_limit(100000000000)
import collections

from shapely.geometry import Polygon, Point
import shapely.wkt as wkt
from rtree import index

from snlocest.util.time import record_time
from snlocest.argparse import GzipFileType
from snlocest.areadata import AreaData


Area = collections.namedtuple('Area', ['area_id', 'polygon'])

class RtreeAreaMatcher():
    def insert_from_iterator(self, itr):
        '''(id, Polygon)を返すイテレータからRtreeを作る

        Polygon.boundをもとに作成したRtreeは、idとPolygonを保持する。

        Args:
            itr: (id, Polygon)を返すイテレータ
        '''
        self.idx = index.Index()
        for i, (area_id, polygon) in enumerate(itr):
            obj = Area(area_id=area_id, polygon=polygon)
            self.idx.insert(i, polygon.bounds, obj)

    def contains(self, lat, lon):
        '''Point(lat, lon)を含むPolygonのarea_idを返す。

        2つ以上のPolygonとマッチした場合は、面積の小さいほうのエリアを返す。
        '''
        result = []
        point = Point(lat, lon)
        for hit in self.idx.intersection(point.bounds, objects=True):
            if hit.object.polygon.contains(point):
                result.append(hit.object)
        if len(result) > 1:
            result.sort(key=lambda x: (x.polygon.area, x.area_id))
        return [r.area_id for r in result]

@record_time
def prepare_database(args):
    areadata = AreaData()
    def gen(areadata):
        for area_id, name, polygon in areadata.iter_areas():
            yield area_id, polygon
    db = RtreeAreaMatcher()
    db.insert_from_iterator(gen(areadata))
    return db


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='rtreeを使ってエリア照合をする')
    parser.add_argument('--infile', type=GzipFileType('rt', encoding='utf-8'), default=sys.stdin)
    parser.add_argument('--gxml', required=True, type=GzipFileType(mode='rt', encoding='utf-8'),
                        help='gxmlファイルのTSV (.gzで終わる場合はgzip圧縮されているとみなす)')
    return parser.parse_args()


@record_time
def main(areadb):
    # 入力されたlat, longのエリアを探す
    for cols in csv.reader(args.infile, delimiter='\t'):
        # Tweet JSONをTSVにしたものが入力なので、coordinatesを持っていないツイートが存在するのでスキップする
        if cols[2] != 'None':
            results = areadb.contains(float(cols[2]), float(cols[3]))
            if results:
                # status_id, user_id, area_id[, area_id, ...]
                print(cols[0], cols[1], *results, sep='\t')

if __name__ == '__main__':
    args = parse_args()
    areadb = prepare_database(args)
    main(areadb)
