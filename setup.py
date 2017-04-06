# coding: utf-8

from setuptools import setup, find_packages

setup(
    name='snlocest',
    version='0.1.0',
    description='Network-based location estimation methods and tools',
    author='Shiori HIRONAKA',
    author_email='s143369@edu.tut.ac.jp',
    url='https://github.com/elnikkis/snlocest',
    license='MIT',
    packages=find_packages(exclude=['docs', 'tests*']),
)
