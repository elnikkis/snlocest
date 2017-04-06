# coding: utf-8

'''
filter関数に使えるフィルタを実装した。

Reference:
森國泰平, 吉田光男, 岡部正幸, 梅村恭司
ツイート投稿位置推定のためのノイズとなる単語の除去手法
DEIM Forum 2015 G8-1

4.2 ツイートデータ
（1） Twitterクライアント名に「NightFoxDuo」を含む
（2） ツイート内容に「きつねかわいい！！！」を含む
（3） 緯度経度が(34.967096, 135.772691)である
（4） Twitter クライアント, アカウント名, 表示名, プロフィールのうち、
        1つ以上に「BOT」「Bot」「bot」「人工無能」のいずれかを含む
(1),(2),(3),(4)に当てはまるものをフィルタする

Implementation:
（1） Twitterクライアント名に「nightfoxduo（大文字と小文字を区別しない）」を含む

'''

import math


def tweet_filter(tweet):
    '''
    tweetをフィルタする。
    Returns:
        tweetを取り除きたいときFalseを返す
    '''
    try:
        return all([yogitsune_filter(tweet), bot_filter(tweet)])
    except KeyError as e:
        return False

def yogitsune_filter(tweet):
    '''
    Tweet filter for NightFoxDuo

    >>> yogitsune_filter({'source': 'NightFoxDuo', 'coordinates': {'coordinates': [0, 0]}, 'text': ''})
    False
    >>> yogitsune_filter({'source': 'NightfoxDuo', 'coordinates': {'coordinates': [0, 0]}, 'text': ''})
    False
    >>> yogitsune_filter({'source': '', 'coordinates': {'coordinates': [135.772691, 34.967096]}, 'text': ''})
    False
    >>> yogitsune_filter({'source': '', 'coordinates': {'coordinates': ['135.772691', '34.967096']}, 'text': ''})
    False
    '''
    # (1)
    if 'nightfoxduo' in tweet['source'].lower():
        return False
    # (3)
    if 'coordinates' in tweet and tweet['coordinates']:
        (coox, cooy)= map(float, tweet['coordinates']['coordinates'])
        #if (cooy == 34.967096 and coox == 135.772691):
        if math.isclose(cooy, 34.967096, abs_tol=1e-5) and math.isclose(coox, 135.772691, abs_tol=1e-5): # math.isclose is added in Python 3.5
            return False
    # (2)
    if 'きつねかわいい！！！' in tweet['text']:
        return False
    return True

def bot_filter(tweet):
    '''
    Tweet filter for bot user

    >>> bot_filter({'user': {'name': 'あいうbot', 'description': '','screen_name':''}, 'source': ''})
    False
    >>> bot_filter({'user': {'name': 'あいうBot', 'description': '','screen_name':''}, 'source': ''})
    False
    >>> bot_filter({'user': {'name': 'あいうBOta', 'description': '','screen_name':''}, 'source': ''})
    True
    >>> bot_filter({'user': {'name': 'あいうBOTaa', 'description': '','screen_name':''}, 'source': ''})
    False
    >>> bot_filter({'user': {'name': 'ｃ人工無能a', 'description': '','screen_name':''}, 'source': ''})
    False
    >>> bot_filter({'user': {'name': '', 'description': 'ｃ人工無能a','screen_name':''}, 'source': ''})
    False
    >>> bot_filter({'user': {'name': '', 'description': '', 'screen_name':'botan_no_hana'}, 'source': ''})
    False
    '''
    # (4)
    bot_words = ['BOT', 'Bot', 'bot', '人工無能']
    user = tweet['user']
    for word in bot_words:
        if (word in user['name'] 
            or (user['description'] and word in user['description'])
            or word in user['screen_name']
            or word in tweet['source']):
            return False
    return True

def arg_parse():
    import argparse
    parser = argparse.argumentparser(
            description='フィルタされるツイートを表示する')
    parser.add_argument('globpath', help='読み込むgzipファイルのglobpath')
    return parser.parse_args()

def gzip_test():
    args = arg_parse()
    from locationtweetdatasets import locationtweetdatasets
    datasets = locationtweetdatasets(args.globpath)
    import itertools
    filtered = itertools.filterfalse(tweet_filter, datasets.read_all_tweets())
    itr = filtered #itertools.islice(filtered, 10)
    for tweet in itr:
        print(tweet)

if __name__ == '__main__':
    gzip_test()
