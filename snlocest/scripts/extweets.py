# coding: utf-8

import sys
import json
from snlocest.tweetfilter import tweet_filter

# sys.stdinがerrorsを指定しても利用しないため、UnicodeDecodeError起きるので、対処
import codecs
sys.stdin = codecs.getreader(sys.stdin.encoding)(sys.stdin.detach(), errors='ignore')


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        description='Tweetsオブジェクトから使う情報を取り出す')
    parser.add_argument('--infile', type=argparse.FileType('r', encoding='utf-8', errors='ignore'),
                        default=sys.stdin)
    parser.add_argument('--outfile', type=argparse.FileType('w', encoding='utf-8'),
                        default=sys.stdout)
    return parser.parse_args()

def print_extract(tweet, outfile):
    try:
        user_id = tweet['user']['id_str']
        created_at = tweet['created_at']
        status_id = tweet['id_str']
        if 'coordinates' in tweet and tweet['coordinates']:
            coord = tweet['coordinates']
            lon, lat = coord['coordinates']
        else:
            lon, lat = None, None
        if 'place' in tweet and tweet['place']:
            place_id = tweet['place']['id']
        else:
            place_id = None
    except (KeyError, TypeError) as ex:
        print(ex, file=sys.stderr)
        print(tweet, file=sys.stderr)
        pass
    else:
        print(status_id, user_id, lon, lat, place_id, created_at,
              file=outfile, sep='\t')

def parse_tweet(infile):
    for line in infile:
        tweet_json = line.rstrip()
        try:
            tweet_obj = json.loads(tweet_json)
            yield tweet_obj
        except ValueError:
            # Ignore broken JSON
            # 文字コードが変なときでも落ちる
            pass

if __name__ == '__main__':
    args = parse_args()
    for tweet in filter(tweet_filter, parse_tweet(args.infile)):
        print_extract(tweet, outfile=args.outfile)
