#coding: utf-8

'''
G-XMLをパースしてtsvで出力する

output tsv:
ken, city, seq_no2, ken_name, gst_name, css_name, moji, x_code, y_code, polygon(WKT)
'''

from shapely.geometry import Polygon
import shapely.wkt as wkt


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        description='g-xml形式のデータから座標データを取り出す')
    parser.add_argument('infiles', nargs='+')
    return parser.parse_args()

def construct_polygon(outer, inners):
    exterior = [tuple(map(float, p.split(','))) for p in outer.split(' ')]
    if inners:
        interiors = [[tuple(map(float, p.split(','))) for p in inner.split(' ')] for inner in inners]
    else:
        interiors = None
    polygon = Polygon(exterior, interiors)
    return polygon

def read_feature(g_feature):
    props = {}
    for node in g_feature:
        if node.tag == 'Geometry':
            outer = node.find('Polygon').find('OuterBoundary').find('LinearRing').find('Coordinates').text
            innerboundaries = node.find('Polygon').findall('InnerBoundary')
            inners = [innerboundary.find('LinearRing').find('Coordinates').text for innerboundary in innerboundaries]
            if not inners:
                inners = None
            polygon = construct_polygon(outer, inners)
            props['POLYGON'] = wkt.dumps(polygon)
        elif node.tag == 'Property':
            props[node.attrib['propertytypename']] = node.text
    return props

def write_data(props):
    print(props['KEN'], props['CITY'], props['SEQ_NO2'],
          #props['KIHON1'], props['KIHON2'], props['KEY_CODE'], 
          props['KEN_NAME'], props['GST_NAME'], props['CSS_NAME'], props['MOJI'], 
          #props['AREA'], 
          props['X_CODE'], props['Y_CODE'], props['POLYGON'],
          sep='\t')

if __name__ == '__main__':
    args = parse_args()
    import xml.etree.ElementTree as ET
    for infile in args.infiles:
        with open(infile, encoding='cp932') as xmlfile:
            # 1行目にある文字コード宣言を飛ばす
            next(xmlfile)
            xmltext = next(xmlfile)
        root = ET.fromstring(xmltext)
        for g_feature in root.find('MetricGeospace').findall('GeometricFeature'):
            props = read_feature(g_feature)
            write_data(props)
