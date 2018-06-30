#!/usr/bin/env python
from __future__ import absolute_import
from setuptools import setup, find_packages

from twistar import version

setup(
    name="twistar",
    version=version,
    description="An implementation of the Active Record pattern for Twisted",
    author="Brian Muller",
    author_email="bamuller@gmail.com",
    license="MIT",
    url="http://findingscience.com/twistar",
    packages=find_packages(),
    install_requires=['twisted >= 12.1','six']
)
