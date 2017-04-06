# coding: utf-8

import glob
import os.path
from subprocess import run

import luigi
from snlocest.tools.areadb import PreprocessAreaDataTask


# これらはdefault configに書きたい

# 位置情報付きツイートのあるディレクトリ
GEOTWEETS_DIR = 'data/twitter-geo/japan'
# 位置情報付きツイートを処理したデータを置く中間ディレクトリ
PREPROCESS_GEOTWEETS_DIR = 'data/geotweets'


class GeoTweetJSON(luigi.ExternalTask):
    '''ExternalTask: JSON file of geo-tagged tweets

    Args:
        date (datetime): Date of tweets
        geodir (string, optional): Base directory of JSON files
    '''
    date = luigi.DateParameter(description='date of geotweet')
    geodir = luigi.Parameter(default=GEOTWEETS_DIR)

    def output(self):
        path = os.path.join(self.geodir, self.date.strftime('%Y-%m'), self.date.strftime('json_%Y-%m-%d.txt.gz'))
        return luigi.LocalTarget(path)


class ExtractMetaDataFromGeoTweetsTask(luigi.Task):
    '''Task: Convert JSON of geo-tagged tweets into TSV format

    Args:
        date (datetime): date of tweets
        output_dir (:obj: `string`, optional): Output directory
    '''
    date = luigi.DateParameter(description='date of geotweet')
    output_dir = luigi.Parameter(default=os.path.join(PREPROCESS_GEOTWEETS_DIR, 'tweet-meta'))

    def requires(self):
        return GeoTweetJSON(date=self.date)

    def output(self):
        path = os.path.join(self.output_dir, self.date.strftime('%Y-%m'), self.date.strftime('%Y-%m-%d.tsv.gz'))
        return luigi.LocalTarget(path)

    def run(self):
        with self.output().temporary_path() as temp_output_path:
            run('gzip -dc {} | cut -f 2 | python -m snlocest.scripts.extweets | gzip > {}'.format(self.input().path, temp_output_path), shell=True, check=True)


class RangeExtractMetaDataFromGeoTweetsTask(luigi.WrapperTask):
    '''WrapperTask: Convert multiple geo-tagged tweets

    Args:
        date_range (datetime-datetime): The range to process
    '''
    date_range = luigi.DateIntervalParameter()

    def requires(self):
        return [ExtractMetaDataFromGeoTweetsTask(date) for date in self.date_range]


class AreaMatchTask(luigi.Task):
    '''Task: Mapping a coordinate of the tweet to an area

    Args:
        date (datetime): date of geo-tagged tweets
        output_dir (string, optional): (default='data/geotweets/area')
    '''
    date = luigi.DateParameter(description='date of geotweet')
    output_dir = luigi.Parameter(default=os.path.join(PREPROCESS_GEOTWEETS_DIR, 'area'))

    def requires(self):
        return [ExtractMetaDataFromGeoTweetsTask(date=self.date), PreprocessAreaDataTask()]

    def output(self):
        path = os.path.join(self.output_dir, self.date.strftime('%Y-%m'), self.date.strftime('%Y-%m-%d.tsv.gz'))
        return luigi.LocalTarget(path)

    def run(self):
        with self.output().temporary_path() as temp_output_path:
            run('gzip -dc {} | python -m snlocest.scripts.areamatcher --gxml {} | gzip > {}'.format(self.input()[0].path, self.input()[1].path, temp_output_path), shell=True, check=True)


class RangeAreaMatchTask(luigi.WrapperTask):
    '''WrapperTask of AreaMatchTask

    Args:
        date_range (datetime-datetime): Range of the dates to process
    '''
    date_range = luigi.DateIntervalParameter()

    def requires(self):
        return [AreaMatchTask(date) for date in self.date_range]


class CountArea(luigi.Task):
    '''Task: Count the number of appearances of the area for each user

    ユーザごとにエリアIDの出現数を数える

    Args:
        date (datetime): The date of the processing
        output_dir (string, optional): default='data/geotweets/countarea'
    '''
    date = luigi.DateParameter()
    output_dir = luigi.Parameter(default=os.path.join(PREPROCESS_GEOTWEETS_DIR, 'countarea'))

    def requires(self):
        return AreaMatchTask(date=self.date)

    def output(self):
        return luigi.LocalTarget(os.path.join(self.output_dir, self.date.strftime('%Y-%m'), self.date.strftime('%Y-%m-%d.tsv')))

    def run(self):
        #TODO 今はprepare_countarea.pyを実行しているけど、その内容をここに展開して良い
        with self.output().temporary_path() as temp_output_path:
            run('gzip -dc {} | python -m snlocest.scripts.prepare_countarea > {}'.format(self.input().path, temp_output_path), shell=True, check=True)


class AggregateCountArea(luigi.Task):
    '''Task: Aggregate the count for each file

    ファイルごとに数えたエリアを合計する

    Args:
        date_range (datetime-datetime):
        output_dir (string, optional): Output directory
        output_prefix (string, optional): default='aggarea'
    '''
    date_range = luigi.DateIntervalParameter()
    output_dir = luigi.Parameter(default=os.path.join(PREPROCESS_GEOTWEETS_DIR, 'aggarea'))
    output_prefix = luigi.Parameter(default='aggarea')

    def requires(self):
        return [CountArea(date=date) for date in self.date_range]

    def output(self):
        path = os.path.join(self.output_dir, '{}-{}.tsv'.format(self.output_prefix, self.date_range))
        return luigi.LocalTarget(path)

    def run(self):
        input_files = ' '.join([i.path for i in self.input()]) # if path includes any spaces, invalid params will be created
        with self.output().temporary_path() as temp_output_path:
            run('python -m snlocest.scripts.agg_count {} | LC_ALL=C sort > {}'.format(input_files, temp_output_path), shell=True, check=True)


class SelectMajorityHomeLocation(luigi.Task):
    '''Task: Select the home loation by majority voting

    Args:
        date_range (datetime-datetime):
        min_majoritynum (int, optional): The minimum number of the tweet in the majority area (default=1; no limit)
        min_totalnum (int, optional): The total number of the tweet of the user (default=1; no limit)
        output_dir (string, optional): output directory
    '''
    date_range = luigi.DateIntervalParameter()
    #method = luigi.Parameter(default='MajorityVote') # used in future
    min_majoritynum = luigi.IntParameter(default=1)
    min_totalnum = luigi.IntParameter(default=1)
    output_dir = luigi.Parameter(default=os.path.join(PREPROCESS_GEOTWEETS_DIR, 'homelocation', 'majority'))

    def requires(self):
        return AggregateCountArea(date_range=self.date_range)

    def output(self):
        path = os.path.join(self.output_dir, '{}_MinMajorityNum-{}_MinTotalNum-{}.tsv'.format(self.date_range, self.min_majoritynum, self.min_totalnum))
        return luigi.LocalTarget(path)

    def run(self):
        cmd = 'cat {} | python -m snlocest.scripts.decidehomelocation --min-majoritynum {} --min-totalnum {} > {}'
        with self.output().temporary_path() as temp_output_path:
            run(cmd.format(self.input().path, self.min_majoritynum, self.min_totalnum, temp_output_path), shell=True, check=True)


class TestTask(luigi.Task):
    date_range = luigi.DateIntervalParameter()

    def requires(self):
        return None

    def output(self):
        return None

    def run(self):
        print(self.date_range)


if __name__ == '__main__':
    #luigi.run(['TestTask', '--local-scheduler'])
    luigi.run()
