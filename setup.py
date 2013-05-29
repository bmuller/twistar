#!/usr/bin/env python
try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

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
    requires=["twisted.enterprise.adbapi"],
    install_requires=['twisted >= 12.1']
)
