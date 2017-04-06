# coding: utf-8

import os
import glob
from subprocess import run
import luigi

AREADB_DIR = 'data/areadata'


class GxmlFiles(luigi.ExternalTask):
    '''ExternalTask: G-XML files of the area

    Args:
        gxml_files (string, optional): glob string of gxml files
    '''
    gxml_files = luigi.Parameter(default='data/g-xml/h22ka/xml/*.xml')

    def output(self):
        return [luigi.LocalTarget(file) for file in glob.glob(self.gxml_files)]


class PreprocessAreaDataTask(luigi.Task):
    '''Task: Preprocess of g-xml data

    Args:
        output_path (string, optional): output path
    '''
    output_path = luigi.Parameter(default=os.path.join(AREADB_DIR, 'japan-gxml.tsv.gz'))

    def requires(self):
        return GxmlFiles()

    def output(self):
        return luigi.LocalTarget(self.output_path)

    def run(self):
        awk = """'BEGIN{OFS="\t"}{print int($1 $2),$4 $5 $6,$10}'"""
        cmd = 'python -m snlocest.scripts.gxmlparser {} | awk -F"\t" {} | LC_ALL=C sort | python -m snlocest.scripts.integrate_area | gzip > {}'
        with self.output().temporary_path() as temp_output_path:
            input_files = ' '.join([i.path for i in self.input()]) # if path includes any spaces, invalid args will be created
            run(cmd.format(input_files, awk, temp_output_path), shell=True, check=True)


class CreateAreaDatabase(luigi.Task):
    def requires(self):
        return PreprocessAreaDataTask()

    def output(self):
        return luigi.LocalTarget(os.path.join(AREADB_DIR, 'area_database.tsv'))

    def run(self):
        with self.output().temporary_path() as temp_output_path:
            cmd = 'python -m snlocest.scripts.compute_area_centroid {} > {}'
            run(cmd.format(self.input().path, temp_output_path), shell=True, check=True)
