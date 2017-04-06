#coding: utf-8

'''
除外user_idリストとエッジリストを入力として受け取って、
除外user_idが含まれない行（エッジ）だけを出力する

リストに含まれるidを使うエッジを除外または抽出する
input:
edgelist
idlist

python edgefilter.py [edgelist] -e [exclusionfile]
exclusionfile: data/network/active_unknown.txt
'''

import sys
import csv

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        description='除外IDから出るエッジを消す')
    parser.add_argument('edgefile', help='エッジリスト', nargs='?',
                        default=sys.stdin, type=argparse.FileType('r'))
    parser.add_argument('idlist', help='',
                        type=argparse.FileType('r'))

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-e', '--exclude', action='store_true',
                       help='動作：除外する')
    group.add_argument('-i', '--include', action='store_true',
                       help='動作：抽出する')

    parser.add_argument('-r', '--reverse', default=False, action='store_true',
                        help='IDを調べる向きを逆にする (default: 左側; 1カラム目)')
    return parser.parse_args()

def _main():
    args = parse_args()

    # IDリストをつくる
    ids = {col[0] for col in csv.reader(args.idlist, delimiter='\t')}

    # 調べる列番号
    num = 0 if not args.reverse else 1

    if args.exclude:
        for col in csv.reader(args.edgefile, delimiter='\t'):
            if col[num] not in ids:
                print(*col, sep='\t', file=sys.stdout)
    elif args.include:
        for col in csv.reader(args.edgefile, delimiter='\t'):
            if col[num] in ids:
                print(*col, sep='\t', file=sys.stdout)

if __name__ == '__main__':
    _main()
