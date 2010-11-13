#!/usr/bin/env python
try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

setup(
    name="twistar",
    version="0.1",
    description="An implementation of the Active Record pattern for Twisted",
    author="Brian Muller",
    author_email="bmuller@butterfat.net",
    license="GPLv3",
    url="http://findingscience.com/twistar",
    packages=["twistar", "twistar.dbconfig", "twistar.tests", 'BermiInflector', 'BermiInflector.Rules'],
    requires=["twisted.enterprise.adbapi"]
)
