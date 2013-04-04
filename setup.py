#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name="twistar",
    version="1.1-chevah2",
    description="An implementation of the Active Record pattern for Twisted",
    author="Brian Muller",
    author_email="bamuller@gmail.com",
    license="GPLv3",
    url="http://findingscience.com/twistar",
    packages=find_packages(),
    requires=["twisted.enterprise.adbapi"],
    install_requires=['twisted>=12.0']
)
