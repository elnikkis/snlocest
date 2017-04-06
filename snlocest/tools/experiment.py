# coding: utf-8

'''
居住地推定をする。
'''

import os
import os.path
from subprocess import run
import luigi
from snlocest.tools.socialnetwork import Edgelist, HomeLocation



# ---- Leave-one-out cross-validation -----

class LeaveOneOutPrediction(luigi.Task):
    name = luigi.Parameter() # データセット名
    edgetype = luigi.ChoiceParameter(choices=['linked', 'mutual', 'followee', 'follower'])
    method = luigi.Parameter()
    extra = luigi.BoolParameter(default=False)

    def requires(self):
        return {'edgelist': Edgelist(name=self.name, edgetype=self.edgetype), 'truth': HomeLocation(name=self.name)}

    def output(self):
        return luigi.LocalTarget(os.path.join('data/experiments/loocv/predicted', self.name, self.method, 'f_{}.tsv'.format(self.edgetype)))

    def run(self):
        extra_cmd = ''
        if self.extra:
            extra_cmd = '--extra'
        cmd = 'python -m snlocest.scripts.loocv {edgelist.path} {truth.path} {} --fast {} > {}'
        with self.output().temporary_path() as temp_output_path:
            run(cmd.format(self.method, extra_cmd, temp_output_path, **self.input()), shell=True, check=True)


class LeaveOneOutEvaluation(luigi.Task):
    name = luigi.Parameter()
    edgetypes = luigi.TupleParameter(default=('linked', 'mutual', 'followee', 'follower'))
    methods = luigi.TupleParameter(default=('mv', 'gm', 'pm', 'rn'))

    def requires(self):
        yield HomeLocation(name=self.name)
        for edgetype in self.edgetypes:
            for method in self.methods:
                yield LeaveOneOutPrediction(name=self.name, edgetype=edgetype, method=method)

    def output(self):
        output_path = os.path.join('data/experiments/loocv/evaluation', '{}.tsv'.format(self.name))
        return luigi.LocalTarget(output_path)

    def run(self):
        truth = self.input()[0]
        cmd = 'python -m snlocest.scripts.evaluate_prf {} {} >> {}'
        with self.output().temporary_path() as temp_output_path:
            for result in self.input()[1:]:
                run(cmd.format(truth.path, result.path, temp_output_path), shell=True, check=True)


# ---- K-fold cross-validation -----

class KFoldPredictionOne(luigi.Task):
    name = luigi.Parameter() # データセット名
    edgetype = luigi.ChoiceParameter(choices=['linked', 'mutual', 'followee', 'follower'])
    method = luigi.Parameter()
    ith = luigi.IntParameter()
    random_state = luigi.IntParameter()
    n_splits = luigi.IntParameter()
    stem = luigi.Parameter(default='result')
    #ext

    def requires(self):
        return {'edgelist': Edgelist(name=self.name, edgetype=self.edgetype), 'truth': HomeLocation(name=self.name)}

    def output(self):
        return luigi.LocalTarget(os.path.join('data/experiments/kfoldcv/predicted', self.name, self.method, self.edgetype, '{}_{}.tsv'.format(self.stem, self.ith)))

    def run(self):
        outputdir = os.path.dirname(self.output().path)
        os.makedirs(outputdir, exist_ok=True)
        cmd = 'python -m snlocest.scripts.kfoldcv --n-splits {n_splits} --random-state {random_state} --nth {nth} {edgelist} {truth} {method} > {output}'
        with self.output().temporary_path() as temp_output_path:
            run(cmd.format(n_splits=self.n_splits,
                            random_state=self.random_state,
                            nth=self.ith,
                            edgelist=self.input()['edgelist'].path,
                            truth=self.input()['truth'].path,
                            method=self.method,
                            output=temp_output_path), shell=True, check=True)


class KFoldEvaluation(luigi.Task):
    name = luigi.Parameter()
    edgetypes = luigi.TupleParameter(default=('linked', 'mutual', 'followee', 'follower'))
    methods = luigi.TupleParameter(default=('mv', 'gm', 'pm', 'rn'))
    random_state = luigi.IntParameter(default=50)
    n_splits = luigi.IntParameter(default=10)

    def requires(self):
        yield HomeLocation(name=self.name)
        for edgetype in self.edgetypes:
            for method in self.methods:
                for i in range(self.n_splits):
                    yield KFoldPredictionOne(
                        name=self.name, 
                        edgetype=edgetype, method=method, ith=i,
                        random_state=self.random_state, n_splits=self.n_splits)

    def output(self):
        output_path = os.path.join('data/experiments/kfoldcv/evaluation', '{}.tsv'.format(self.name))
        return luigi.LocalTarget(output_path)

    def run(self):
        truth = self.input()[0]
        cmd = 'python -m snlocest.scripts.evaluate_prf --random-state {random_state} {truth} {result_dir} >> {output}'

        result_paths = [result.path for result in self.input()[1:]]
        dirs = {os.path.dirname(path) for path in result_paths}
        with self.output().temporary_path() as temp_output_path:
            for result_dir in dirs:
                run(cmd.format(random_state=self.random_state,
                               truth=truth.path,
                               result_dir=result_dir,
                               output=temp_output_path),
                    shell=True, check=True)
