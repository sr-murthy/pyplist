#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from setuptools import setup, find_packages


import pyplist


python_requires = '>=3.7.4'


requirements_file = Path('requirements.txt')
with open(requirements_file, 'r') as req_fh:
    # Note this assumes each requirement contains no spaces but may be
    #   followed by whitespace and a comment on the same line.
    python_requirements = [
        requirement.strip().split()[0]
        for requirement in req_fh.readlines()
    ]


readme_file = Path('README.rst')
with open(readme_file, 'r') as long_desc_fh:
    long_description = long_desc_fh.read()


setup(
    name='pyplist',
    version=pyplist.__version__,
    author='Sandeep Murthy',
    author_email=(
        'smurthy@tuta.io'
    ),
    description=(
        'A library and CLI tool for inspecting and comparing Mac plist files, '
        'and detecting plist files associated with malicious processes and '
        'apps.'
    ),
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/sr-murthy/pyplist',
    packages=find_packages(
        include=[
            'pyplist',
            'pyplist.*'
        ]
    ),
    py_modules=[
    ],
    entry_points={},
    include_package_data=True,
    exclude_package_data={
        '': ['__pycache__', '*.py[co]'],
    },
    install_requires=python_requirements,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS'
    ],
    python_requires=python_requires,
)
