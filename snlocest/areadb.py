# coding: utf-8

import sys

import mysql.connector
#from mysql.connector import errorcode

import logging
logger = logging.getLogger(__name__)


class MySQLManager():
    '''MySQLデータベースに対して基本的な操作ができるクラス

    たしか、残念なことに、prepated=Trueのcursorを使っても早くならずむしろ遅くなる
    '''
    def __init__(self, host='localhost', user='root', password=''):
        self.cnx = mysql.connector.connect(
            user=user, password=password, host=host)
        #self.cursor = self.cnx.cursor(prepared=True)
        self.cursor = make_cursor()

    def make_cursor(self, prepared=False):
        return self.cnx.cursor(prepated=prepared)

    def show_databases(self):
        sql = 'show databases'
        self.cursor.execute(sql)
        dbs = self.cursor.fetchall()
        return dbs

    def use_database(self, dbname):
        self.cursor.execute('use {}'.format(dbname))

    def show_tables(self):
        sql = 'show tables'
        self.cursor.execute(sql)
        tables = self.cursor.fetchall()
        return tables

    def drop_database(self, dbname):
        sql = 'drop database {}'.format(dbname)
        self.cursor.execute(sql)

    def drop_table(self, tablename):
        sql = 'drop table {}'.format(tablename)
        self.cursor.execute(sql)

    def execute(self, *args, cursor=None):
        # 未テスト
        if not cursor:
            cursor = self.cursor
        self.cursor.execute(*args)

    def close(self):
        self.cursor.close()
        self.cnx.close()


class AreaDataManager(MySQLManager):
    '''エリアDBの操作ができる

    トランザクションとかPREPAREとかなんかうまくいっていないので使うときに直す。
    現在preparedは使わないようになっている。
    '''

    def __init__(self, db_name, table_name, host='localhost', user='root', password=''):
        super().__init__(host, user, password)
        self.table_name = table_name
        self.use_database(db_name)
        self._contains_sql = ('select code, X(center), Y(center), name, area(shape) from {} '
                             'where st_contains(shape, geomfromtext(%s))'.format(self.table_name))

    def create_area_table(self):
        '''DBにエリア情報のtableを作成する'''
        sql = ('create table if not exists {} ( '
               'code mediumint(5) not null, '
               'name varchar(100) not null, '
               'shape multipolygon not null, '
               'center point, '
               'primary key (code), '
               'spatial key shape (shape) '
               ') engine=MyISAM default charset=utf8;'
              ).format(self.table_name)
        #TODO: 使うならArea(shape)を追加するべき
        logger.info(sql)
        self.execute(sql)

    def insert_area(self, code, name, polygons):
        '''DBにエリアをinsertする

        Args:
            code: ID
            name: 地名
            polygons: list of list of list
        '''
        # 毎回formatしていて非効率
        sql = ('insert ignore into {} (code, name, shape, center) values( '
               '?, ?, GeomFromText(?), st_centroid(shape) '
               ')').format(self.table_name)
        polys_str = ','.join(
            ['(({}))'.format(','.join(
                ['{} {}'.format(p[0], p[1]) for p in polygon]))
            for polygon in polygons])
        mpoly = 'multipolygon({})'.format(polys_str)
        self.execute(sql, [code, name, mpoly])

    def contains(self, point):
        '''pointが含まれているエリアを返す
        Args:
            point: [lon, lat]のリスト
        Returns:
            [code, centroid_x, centroid_y, name]
        '''
        sql = self._contains_sql
        p_str = 'POINT({} {})'.format(point[0], point[1])
        #print(sql, p_str, file=sys.stderr)
        self.execute(sql, [p_str])
        result = self.cursor.fetchall()
        #TODO: if len(result) > 1:
        result.sort(key=lambda x: x[4])
        if len(result) > 0:
            #return (result[0][0], result[0][1], result[0][2], result[0][3].decode('utf-8'))
            return result[0][0], result[0][1], result[0][2], result[0][3]
        else:
            return None

    def get_center(self, area_id):
        sql = 'SELECT X(center), Y(center) from {}'.format(self.table_name)
        raise NotImplementedError()
