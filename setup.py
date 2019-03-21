#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013-2014 Paulo Henrique Silva <ph.silva@gmail.com>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

import os

METADATA = {
    'name': 'pcb-tools-extension',
    'version': 0.1,
    'author': 'Hiroshi Murayama <opiopan@gmail.com>',
    'author_email': "opiopan@gmail.com",
    'description': ("Extension for pcb-tools package to panelize gerber files"),
    'license': "Apache",
    'keywords': "pcb gerber tools extension",
    'url': "http://github.com/opiopan/pcb-tools-extension",
    'packages': ['gerberex'],
    'classifiers':[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apple Public Source License",
    ],
}

SETUPTOOLS_METADATA = {
    'install_requires': ['pcb-tools', 'dxfgrabber'],
}


def install():
    """ Install using setuptools, fallback to distutils
    """
    try:
        from setuptools import setup
        METADATA.update(SETUPTOOLS_METADATA)
        setup(**METADATA)
    except ImportError:
        from sys import stderr
        stderr.write('Could not import setuptools, using distutils')
        stderr.write('NOTE: You will need to install dependencies manualy')
        from distutils.core import setup
        setup(**METADATA)

if __name__ == '__main__':
    install()