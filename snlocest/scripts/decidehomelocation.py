# coding: utf-8

'''
ユーザごとのエリアIDから、居住地を決める
多数決で決める（ユーザごとに、最もツイート数が多いエリアを選択する）

要：入力ファイルがメモリにのること


input: agg_count.py
user_id, count, area_id
（ソートされていること）


最多のツイートがあるエリアでの最小ツイート数 
NumOfTweetsAtMajorityArea := 5

最小総ツイート数
'''


import sys
import pandas as pd


def load_data(infile):
    df = pd.read_csv(infile, sep='\t', names=['user_id', 'count', 'area_id'])
    return df

def process(df, args):
    sorted = df.sort_values(by='count')
    result = sorted.drop_duplicates('user_id', keep='last')
    result = result.set_index('user_id')
    result['total'] = df.groupby('user_id')['count'].sum()

    if args.min_majoritynum:
        result = result[result['count'] >= args.min_majoritynum]

    if args.min_totalnum:
        result = result[result['total'] >= args.min_totalnum]

    result.to_csv(args.outfile, sep='\t', columns=['area_id', 'count', 'total'], header=False)

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='ユーザごとのエリアIDを処理する')
    parser.add_argument('--infile', default=sys.stdin)
    parser.add_argument('--outfile', default=sys.stdout)
    parser.add_argument('--min-majoritynum', default=1, type=int, help='最多のツイートがあるエリアでの最小ツイート数')
    parser.add_argument('--min-totalnum', default=1, type=int, help='最小総ツイート数')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    df = load_data(args.infile)
    process(df, args)
