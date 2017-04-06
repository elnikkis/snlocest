# coding: utf-8

'''
複数の入力ファイルのcountを集計する

input:
count, user_id, area_id

output:
user_id, count, area_id

'''

import csv
from collections import defaultdict
from snlocest.argparse import GzipFileType


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='各ユーザのエリアを集計する')
    parser.add_argument('infiles', nargs='+', type=GzipFileType('rt', encoding='utf-8'))
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    count = defaultdict(int)
    for infile in args.infiles:
        for line in csv.reader(infile, delimiter='\t'):
            key = (line[1], line[2])
            count[key] += int(line[0])

    for k, v in count.items():
        user_id = k[0]
        area_id = k[1]
        print(user_id, v, area_id, sep='\t')
