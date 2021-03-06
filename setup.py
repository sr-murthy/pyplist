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
    author='Sandeep R. Murthy',
    author_email=(
        'smurthy@tuta.io'
    ),
    maintainer='Sandeep R. Murthy',
    maintainer_email='smurthy@tuta.io',
    description=(
        'A library and CLI tool for finding, inspecting and comparing plists '
        '(property list files), and detecting plists associated with '
        'non-standard or malicious processes and apps, on Apple MacOS/OX X, '
        'iOS and other relevant systems and devices.'
    ),
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/sr-murthy/pyplist',
    keywords=[
        'plist',
        'property list',
    ],
    packages=find_packages(
        include=[
            'pyplist',
            'pyplist.*'
        ]
    ),
    py_modules=[
    ],
    entry_points={},
    exclude_package_data={
        '': ['__pycache__', '*.py[co]'],
    },
    install_requires=python_requirements,
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
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
