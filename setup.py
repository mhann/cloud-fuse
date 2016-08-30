#!/usr/bin/env python

from __future__ import with_statement

from setuptools import setup

with open('README') as readme:
    documentation = readme.read()

setup(
    name    = 'cloud-fuse',
    version = '0.0.4',

    description      = 'Framework for building block based fuse filesystems aimed mainly at cloud storage',
    long_description = documentation,
    author           = 'Marcus Hann',
    author_email     = 'marcus@hannmail.co.uk',
    maintainer       = 'Marcus Hann',
    maintainer_email = 'marcus@hannmail.co.uk',
    license          = 'ISC',
    url              = 'http://github.com/mhann/cloud-fuse',

    classifiers = [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3',
        'Topic :: System :: Filesystems',
    ]
)
