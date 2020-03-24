#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = [
    # TODO: put package requirements here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='intergov',
    version='0.1.0',
    description="Mechanism for exchanging messages/documents between nations",
    long_description=readme,
    author="Chris Gough",
    author_email='chris.gough@omg.management',
    url='https://github.com/trustbridge/intergov',
    packages=[
        'intergov',
    ],
    package_dir={'intergov':
                 'intergov'},
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords='intergov',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
