# coding: utf-8

'''
収集したフォロー関係のデータからソーシャルネットワークを作る
'''

import os.path
import glob
from subprocess import run
import luigi


NETWORK_DIR = 'data/socnetwork'

class TwitterFollowingFollowers(luigi.ExternalTask):
    '''Twitterユーザの関係データ
    '''
    month = luigi.MonthParameter()
    type = luigi.ChoiceParameter(choices=['followers', 'following'])
    basedir = luigi.Parameter(default='data/twitter-following-followers-geo')

    def output(self):
        return luigi.LocalTarget(os.path.join(self.basedir, self.month.strftime('%Y%m-{}.tar.gz'.format(self.type))))


class UnknownTxt(luigi.Task):
    '''unknown.txtを取り出す'''
    month = luigi.MonthParameter()
    type = luigi.ChoiceParameter(choices=['followers', 'following'])

    def requires(self):
        return TwitterFollowingFollowers(month=self.month, type=self.type)

    def output(self):
        return luigi.LocalTarget(os.path.join(NETWORK_DIR, 'raw-unknown', self.month.strftime('%Y%m-{}.txt'.format(self.type))))

    def run(self):
        with self.output().temporary_path() as temp_output_path:
            cmd = 'zcat {} | tar xO {} > {}'.format(self.input().path, self.month.strftime('%Y%m-{}/unknown.txt'.format(self.type)), temp_output_path)
            run(cmd, shell=True, check=True)


class LocationUserList(luigi.ExternalTask):
    '''居住地をつけたユーザのリスト

    1列目がuser_id
    '''
    path = luigi.Parameter()

    def output(self):
        return luigi.LocalTarget(self.path)


class TwitterFollowRawEdgelist(luigi.Task):
    '''エッジリスト形式にしたもの（ユーザでフィルタリングしていない）
    '''
    month = luigi.MonthParameter()
    type = luigi.ChoiceParameter(choices=['followers', 'following'])

    def requires(self):
        return TwitterFollowingFollowers(month=self.month, type=self.type)

    def output(self):
        return luigi.LocalTarget(os.path.join(NETWORK_DIR, 'raw', self.month.strftime('%Y%m-{}.tsv.gz'.format(self.type))))

    def run(self):
        with self.output().temporary_path() as temp_output_path:
            cmd = 'zcat {} | tar xO --wildcards {} | tr ";" "\t" | gzip > {}'.format(self.input().path, self.month.strftime('%Y%m-{}/%Y-%m-*.txt'.format(self.type)), temp_output_path)
            run(cmd, shell=True, check=True)


class UnknownList(luigi.Task):
    '''unknown.txtをマージする'''
    month = luigi.MonthParameter()
    sources = luigi.TupleParameter(default=('followers', 'following'))

    def requires(self):
        return [UnknownTxt(month=self.month, type=s) for s in self.sources]

    def output(self):
        return luigi.LocalTarget(os.path.join(NETWORK_DIR, 'unknown', self.month.strftime('%Y%m_{}_unknown.txt'.format('-'.join(self.sources)))))

    def run(self):
        with self.output().temporary_path() as temp_output_path:
            cmd = 'cat {} | LC_ALL=C sort -u > {}'.format(' '.join([i.path for i in self.input()]), temp_output_path)
            run(cmd, shell=True, check=True)


class SeedUserList(luigi.ExternalTask):
    month = luigi.MonthParameter()
    basedir = luigi.Parameter(default='data/twitter-following-followers-geo')
    number = luigi.IntParameter(default=2)  # 2が2014年にある市区町村で5回以上ツイートがあるユーザ、1はそれに加えて2014年に365回以上のツイートがあるユーザ

    def output(self):
        return luigi.LocalTarget(os.path.join(self.basedir, 'user_id_{}.txt'.format(self.number)))


class RemainedHomeLocation(luigi.Task):
    '''作成した居住地データ（LocationuserList）からunknownになったユーザをひいて、
    ソーシャルネットワークを取得しているuserlistとANDをとったものを保存する

    Args:
        --homelocation-path 居住地データのファイルへのパス
    '''
    name = luigi.Parameter()
    month = luigi.MonthParameter()
    sources = luigi.TupleParameter(default=('followers', 'following'))
    homelocation_path = luigi.Parameter()

    def requires(self):
        return {
            'unknown': UnknownList(month=self.month, sources=self.sources),
            'userlist': LocationUserList(path=self.homelocation_path),
            'seed': SeedUserList(month=self.month)
        }

    def output(self):
        return luigi.LocalTarget(os.path.join('data/datasets', self.name, 'groundtruth', os.path.basename(self.input()['userlist'].path)))

    def run(self):
        cmd = 'cat {userlist.path} | python -m snlocest.scripts.edgefilter -e {unknown.path} | python -m snlocest.scripts.edgefilter -i {seed.path} > {}'
        with self.output().temporary_path() as temp_output_path:
            run(cmd.format(temp_output_path, **self.input()), shell=True, check=True)


class FollowFilteredEdgelist(luigi.Task):
    '''edgelistの左側にunknownが出て来るエッジを消して、居住地の付けたユーザからのデータのみにしたエッジリスト

    Args:
        --name LocationUserListとUnknownListがわかるように保存パスに使われる名前
        --month
    '''
    month = luigi.MonthParameter()
    name = luigi.Parameter()
    type = luigi.ChoiceParameter(choices=['followers', 'following'])
    sources = luigi.TupleParameter(default=('followers', 'following'))

    def requires(self):
        return {'edgelist': TwitterFollowRawEdgelist(month=self.month, type=self.type), 'hl': RemainedHomeLocation(name=self.name, month=self.month)}

    def output(self):
        return luigi.LocalTarget(os.path.join(NETWORK_DIR, 'filtered', self.name, self.month.strftime('%Y%m_{}.tsv.gz'.format(self.type))))

    def run(self):
        with self.output().temporary_path() as temp_output_path:
            cmd = 'zcat {edgelist.path} | python -m snlocest.scripts.edgefilter -i {hl.path} | gzip > {}'.format(temp_output_path, **self.input())
            run(cmd, shell=True, check=True)


class MasterFollowEdgelist(luigi.Task):
    '''followingとfollowersをマージしたエッジリスト(followee)を作る

    Args:
        --name LocationUserListとmonthとsourcesが識別できるような名前
        --month
    '''
    month = luigi.MonthParameter()
    sources = luigi.TupleParameter(default=('followers', 'following'))
    name = luigi.Parameter()

    def requires(self):
        return {s: FollowFilteredEdgelist(month=self.month, type=s, name=self.name, sources=self.sources) for s in self.sources}

    def output(self):
        return luigi.LocalTarget(os.path.join(NETWORK_DIR, 'master', self.name, self.month.strftime('%Y%m_{}.tsv.gz'.format('-'.join(self.sources)))))

    def run(self):
        #!!! sources = ('followers', 'following') にしか対応していない
        followers = '''zcat %s | awk -F"\t" 'BEGIN{OFS="\t"}{print $2,$1}' ''' % self.input()['followers'].path
        following = 'zcat {}'.format(self.input()['following'].path)
        with self.output().temporary_path() as temp_output_path:
            cmd = 'cat <({}) <({}) | LC_ALL=C sort -u | gzip > {}'.format(followers, following, temp_output_path)
            run(cmd, shell=True, check=True, executable='/bin/bash')


class MutualNetwork(luigi.Task):
    month = luigi.MonthParameter()
    name = luigi.Parameter()

    def requires(self):
        return MasterFollowEdgelist(month=self.month, name=self.name)

    def output(self):
        return luigi.LocalTarget(os.path.join('data/datasets', self.name, 'networks', 'f_mutual.tsv'))

    def run(self):
        with self.output().temporary_path() as temp_output_path:
            cmd = '''zcat %s | awk -F"\t" 'BEGIN{OFS="\t"}{print $1,$2;print $2,$1}' | LC_ALL=C sort | LC_ALL=C uniq -d > %s ''' % (self.input().path, temp_output_path)
            run(cmd, shell=True, check=True)


class FollowerNetwork(luigi.Task):
    month = luigi.MonthParameter()
    name = luigi.Parameter()

    def requires(self):
        return MasterFollowEdgelist(month=self.month, name=self.name)

    def output(self):
        return luigi.LocalTarget(os.path.join('data/datasets', self.name, 'networks', 'f_follower.tsv'))

    def run(self):
        with self.output().temporary_path() as temp_output_path:
            cmd = '''zcat %s | awk -F"\t" 'BEGIN{OFS="\t"}{print $2,$1}' > %s''' % (self.input().path, temp_output_path)
            run(cmd, shell=True, check=True)


class FolloweeNetwork(luigi.Task):
    month = luigi.MonthParameter()
    name = luigi.Parameter()

    def requires(self):
        return MasterFollowEdgelist(month=self.month, name=self.name)

    def output(self):
        return luigi.LocalTarget(os.path.join('data/datasets', self.name, 'networks', 'f_followee.tsv'))

    def run(self):
        with self.output().temporary_path() as temp_output_path:
            run('zcat {} > {}'.format(self.input().path, temp_output_path), shell=True, check=True)


class LinkedNetwork(luigi.Task):
    month = luigi.MonthParameter()
    name = luigi.Parameter()

    def requires(self):
        return MasterFollowEdgelist(month=self.month, name=self.name)

    def output(self):
        return luigi.LocalTarget(os.path.join('data/datasets', self.name, 'networks', 'f_linked.tsv'))

    def run(self):
        with self.output().temporary_path() as temp_output_path:
            cmd = '''zcat %s | awk -F"\t" 'BEGIN{OFS="\t"}{print $1,$2;print $2,$1}' | LC_ALL=C sort | LC_ALL=C uniq > %s ''' % (self.input().path, temp_output_path)
            run(cmd, shell=True, check=True)


class FollowSocialNetworks(luigi.WrapperTask):
    month = luigi.MonthParameter()
    name = luigi.Parameter()

    def requires(self):
        networks = [MutualNetwork, FollowerNetwork, FolloweeNetwork, LinkedNetwork]
        return [N(month=self.month, name=self.name) for N in networks]


# ------- external dataset ----

class Edgelist(luigi.ExternalTask):
    name = luigi.Parameter()
    edgetype = luigi.Parameter()

    def output(self):
        return luigi.LocalTarget(os.path.join('data/datasets', self.name, 'networks', 'f_{}.tsv'.format(self.edgetype)))


class HomeLocation(luigi.ExternalTask):
    name = luigi.Parameter()

    def output(self):
        path = os.path.join('data/datasets', self.name, 'groundtruth', '*.tsv')
        files = glob.glob(path)
        assert len(files) == 1, 'data/datasets/groundtruth/以下に2つ以上のファイルがあります（1つでないといけません）'
        return luigi.LocalTarget(files[0])


# ------- closed network ----

class ClosedNetwork(luigi.Task):
    '''FollowSocialNetworksからclosedなエッジだけを取り出したネットワークを作る'''
    src_name = luigi.Parameter()
    dst_name = luigi.Parameter()
    source = luigi.ChoiceParameter(choices=['linked', 'mutual', 'followee', 'follower'])

    def requires(self):
        return {'edgelist': Edgelist(name=self.src_name, edgetype=self.source),
                'truth': HomeLocation(name=self.src_name)}

    def output(self):
        return luigi.LocalTarget(os.path.join('data/datasets', self.dst_name, 'networks', 'f_{}.tsv'.format(self.source)))

    def run(self):
        cmd = 'cat {edgelist.path} | python -m snlocest.scripts.seedfilter {truth.path} > {}'
        with self.output().temporary_path() as temp_output_path:
            run(cmd.format(temp_output_path, **self.input()), shell=True, check=True)


class CopyGroundtruth(luigi.Task):
    src_name = luigi.Parameter()
    dst_name = luigi.Parameter()

    def requires(self):
        return HomeLocation(name=self.src_name)

    def output(self):
        basename = os.path.basename(self.input().path)
        return luigi.LocalTarget(os.path.join('data/datasets', self.dst_name, 'groundtruth', basename))

    def run(self):
        with self.output().temporary_path() as temp_output_path:
            run(['cp', self.input().path, temp_output_path], check=True)


class ClosedDataset(luigi.WrapperTask):
    '''closed_[name]なデータセットを作る'''
    name = luigi.Parameter()
    sources = luigi.TupleParameter(default=('linked', 'mutual', 'followee', 'follower'))

    def requires(self):
        dst_name = 'closed_' + self.name
        return ([CopyGroundtruth(src_name=self.name, dst_name=dst_name)]
                + [ClosedNetwork(src_name=self.name, dst_name=dst_name, source=s) for s in self.sources])
