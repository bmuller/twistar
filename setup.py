#!/usr/bin/env python
try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

setup(
    name="twistdb",
    version="0.1",
    description="",
    author="",
    author_email="",
    license="GPL",
    url="",
    packages=["twistdb", "twistdb.dbconfig"]
)
