# coding: utf-8

'''
ユーザごとにエリアIDの出現数を数える

input:
エリアIDの付いたツイートデータ
status_id, user_id, area_id

output:

'''

from subprocess import run


def main(args):
    awk = '''BEGIN{OFS="\t"}{print $1,$2,$3}'''
    run("cat {} | cut -f 2,3 | LC_ALL=C sort | LC_ALL=C uniq -c | awk '{}' > {}".format(args.infile, awk, args.outfile), shell=True, check=True)

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='ユーザごとにエリアIDの出現数を数える')
    parser.add_argument('--infile', help='ユーザIDとエリアIDの組のTSV', default='/dev/stdin')
    parser.add_argument('--outfile', help='出力ファイル名', default='/dev/stdout')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    main(args)
