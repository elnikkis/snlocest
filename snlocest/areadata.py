# coding: utf-8

'''
data/areadata以下のファイルをあらわすクラスたち
'''

import csv
csv.field_size_limit(100000000)
import gzip
from collections import OrderedDict
import shapely.wkt as wkt


class AreaData():
    '''エリアデータ

    area_id, name, MultiPolygon
    '''
    def __init__(self, path='data/areadata/japan-gxml.tsv.gz'):
        self._data = OrderedDict()
        if path.endswith('.gz'):
            with gzip.open(path, 'rt', encoding='utf-8') as fp:
                self._load_data(fp)
        else:
            with open(path, 'rt', encoding='utf-8') as fp:
                self._load_data(fp)

    def _load_data(self, infile):
        for line in csv.reader(infile, delimiter='\t'):
            area_id = int(line[0])
            name = line[1]
            polygon = wkt.loads(line[2])
            self._data[area_id] = (name, polygon)

    def get_coordinate(self, area_id):
        raise NotImplementedError()

    def get_areaname(self, area_id):
        '''Return an area name of area_id'''
        return self._data[int(area_id)][0]

    def get_shape(self, area_id):
        '''Return an MultiPolygon of area_id'''
        return self._data[int(area_id)][1]

    def __iter__(self):
        '''Iterate all area_id which exists'''
        return iter(self._data.keys())

    def iter_areas(self):
        '''Return an iterator of (area_id, name, MultiPolygon)'''
        for k, v in self._data.items():
            yield k, v[0], v[1]


class AreaCoordinateData():
    '''エリア座標データ

    area_id, lon, lat
    '''
    def __init__(self, dbpath='data/areadata/area_database.tsv'):
        with open(dbpath, 'r') as f:
            self.db = self._load_db(f)

    def _load_db(self, dbfile):
        db = OrderedDict()
        for line in csv.reader(dbfile, delimiter='\t'):
            db[int(line[0])] = (float(line[1]), float(line[2]), line[3])
        return db

    def get_point(self, area_id):
        return self.db[int(area_id)][0:2]

    def get_name(self, area_id):
        return self.db[int(area_id)][2]

    def __iter__(self):
        '''存在するすべてのarea_idを繰り返す
        '''
        return iter(self.db.keys())

    def __getitem__(self, key):
        return self.get_point(key)
