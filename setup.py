# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

setup(
    name='pixel_reader',
    version='0.0.1',
    description='Implements a fast OpenGL glReadPixels function.',
    long_description=readme,
    author='Dimitri Henkel',
    author_email='Dimitri.Henkel@gmail.com',
    packages=find_packages(exclude=('tests', 'docs'))
)