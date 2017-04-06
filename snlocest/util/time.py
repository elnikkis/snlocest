# coding: utf-8

import sys
import time

def record_time(func):
    '''funcの実行にかかった時間をstderrに出力する'''
    def record(*args, **kwargs):
        start = time.time()
        ret = func(*args, **kwargs)
        elapsed_time = time.time() - start
        print('Elapsed time in {}: {} [sec]'.format(func.__name__, elapsed_time), file=sys.stderr)
        return ret
    return record
