#coding: utf-8

'''
ユーザリストを読み込んで、
それに含まれるユーザ同士のエッジのみを取り出す。

python seedfilter.py [edgelist] [userfile]

edgelist(TSV):
src_id, dst_id

userfile: data/geo-datasets/groundtruth_2014.tsv
    1列目がuser_idのTSV
'''

import sys
import csv

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        description='ユーザリストに含まれるユーザ同士のエッジを出力する')
    parser.add_argument('edgefile', help='エッジリスト',
                        type=argparse.FileType('r', encoding='utf-8'), nargs='?', default=sys.stdin)
    parser.add_argument('userlist', help='ユーザリスト',
                        type=argparse.FileType('r', encoding='utf-8'))
    return parser.parse_args()

def _main():
    args = parse_args()

    ids = {col[0] for col in csv.reader(args.userlist, delimiter='\t')}

    for col in csv.reader(args.edgefile, delimiter='\t'):
        if col[0] in ids and col[1] in ids:
            print(*col, sep='\t', file=sys.stdout)
        #else:
        #    print('Exclude:', *col, sep='\t', file=sys.stderr)

if __name__ == '__main__':
    _main()
