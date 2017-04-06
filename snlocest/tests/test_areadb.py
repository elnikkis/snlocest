# coding: utf-8

import pytest

mysql = pytest.importorskip("mysql.connector")
from snlocest.areadb import AreaDataManager



def pytest_funcarg__areadb(request):
    return AreaDataManager('geo', 'area_feature')
    #return AreaDataManager('test20160513_geo', 'test20160513_area')



# エリアDBにデータがちゃんと入っているかのテスト

def test_areadb(areadb):
    sql = 'select count(code) from {}'.format(areadb.table_name)
    areadb.execute(sql)
    res = areadb.cursor.fetchall()
    assert res[0][0] == 1901

def test_contains(areadb):
    res = areadb.contains([137.408818, 34.701704])
    assert res[0] == 23201
    assert res[3] == '愛知県豊橋市 '
