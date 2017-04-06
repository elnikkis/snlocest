# coding: utf-8

import os.path
import pytest
from snlocest.areadata import AreaCoordinateData


AREADB = 'data/areadata/area_database.tsv'

@pytest.mark.skipif('not os.path.exists(AREADB)')
def test_AreaCoordinateData_iter():
    # OrderedDictなら元ファイルとkeyの並び順が同じになる
    areadata = AreaCoordinateData(AREADB)
    areas = [a for a in areadata]

    with open(AREADB, 'r') as fp:
        for line, area in zip(fp, areas):
            area_id = int(line.rstrip().split('\t')[0])
            assert area_id == area
