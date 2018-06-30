"""
Twistar is a Python implementation of the U{active record pattern<http://en.wikipedia.org/wiki/Active_record_pattern>}
that uses the U{Twisted <http://twistedmatrix.com/trac/>} framework's
U{RDBMS support<http://twistedmatrix.com/documents/current/core/howto/rdbms.html>} to provide a non-blocking interface to
relational databases.

@author: Brian Muller U{bamuller@gmail.com}
"""
from __future__ import absolute_import
version_info = (2, 0)
version = '.'.join(map(str, version_info))
