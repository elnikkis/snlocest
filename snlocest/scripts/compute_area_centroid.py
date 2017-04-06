# coding: utf-8

'''
エリアのcentroidを計算する

input:
area_id, name, MultiPolygon(WKT)

output:
area_id, centroid (lon), centroid (lat), name
'''

from snlocest.argparse import GzipFileType
from snlocest.areadata import AreaData


def parse_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('gxmltsv')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    areas = AreaData(path=args.gxmltsv)
    for area_id, name, polygon in areas.iter_areas():
        centroid = polygon.centroid
        print(area_id, centroid.x, centroid.y, name, sep='\t')
