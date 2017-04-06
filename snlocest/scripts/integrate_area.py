# coding: utf-8

'''
gxmlparser.pyの出力から市区町村レベルでエリアをまとめる
'''

import sys
import csv
csv.field_size_limit(100000000)
from itertools import groupby
import shapely.wkt as wkt
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import cascaded_union
from snlocest.argparse import GzipFileType


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='エリアをまとめる')
    parser.add_argument('gxml_tsv', type=GzipFileType(mode='rt', encoding='utf-8'),
                        nargs='?', default=sys.stdin,
                        help='ソート済みのgxmlparserの出力（.gzで終わる場合はgzip圧縮されているとみなす）')
    return parser.parse_args()


if __name__ == '__main__':
    from shapely.validation import explain_validity
    args = parse_args()
    for k, g in groupby(csv.reader(args.gxml_tsv, delimiter='\t'), key=lambda x: x[0]):
        area_id = k
        areas = list(g)
        name = areas[0][1]
        polygons = [wkt.loads(area[2]) for area in areas]
        #mulp = MultiPolygon(polygons)
        mulp = cascaded_union(polygons)
        print(area_id, name, wkt.dumps(mulp), sep='\t')
