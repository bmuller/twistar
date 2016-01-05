# twistar: Asynchronous Python ORM
[![Build Status](https://secure.travis-ci.org/bmuller/twistar.png?branch=master)](https://travis-ci.org/bmuller/twistar) [![Coverage Status](https://coveralls.io/repos/bmuller/twistar/badge.svg?branch=master&service=github)](https://coveralls.io/github/bmuller/twistar?branch=master)

The Twistar Project provides an ActiveRecord (ORM) pattern interface to the Twisted Project's RDBMS library.  This file contains minimal documentation - see the project home page at http://findingscience.com/twistar for more information.

## Installation

```
pip install twistar
```

## Usage
Your database must be one of: MySQL, PostgreSQL, or SQLite.  The only DBAPI modules supported by Twistar are: MySQLdb, psycopg2, and sqlite3 - at least one of these must be installed.

Here's the obligatory TL;DR example of creating a User record, assuming that there is a table named "users" with varchar columns for first_name and last_name and an int age column:

```python
#!/usr/bin/env python
from twisted.enterprise import adbapi
from twistar.registry import Registry
from twistar.dbobject import DBObject
from twisted.internet import reactor

class User(DBObject):
     pass

def done(user):
     print "A user was just created with the name %s" % user.first_name
     reactor.stop()

# Connect to the DB
Registry.DBPOOL = adbapi.ConnectionPool('MySQLdb', user="twistar", passwd="apass", db="twistar")

# make a user
u = User()
u.first_name = "John"
u.last_name = "Smith"
u.age = 25

# Or, use this shorter version:
u = User(first_name="John", last_name="Smith", age=25)

# save the user
u.save().addCallback(done)

reactor.run()
```

Then, finding this user is easy:

```python
def found(users):
    print "I found %i users!" % len(users)
    for user in users:
        print "User: %s %s" % (user.first_name, user.last_name)

u = User.findBy(first_name="John", age=25).addCallback(found)
```

This is a very simple example - see http://findingscience.com/twistar for more complicated examples and additional uses.

## Testing
To run unit-tests you simply require [Tox](https://tox.readthedocs.org)

To run the tests:
```
tox
```

By default, the tests are run with the database driver sqlite3.  To change this, set the DBTYPE environment variable:

```
DBTYPE=postgres trial twistar
DBTYPE=mysql trial twistar
```

You'll need a database named "twistar" for each of those tests (or you can change the dbname, user, etc in the `<db type>_config.py` file in the tests folder).

## Documentation
If you intent on generating API documentation, you will need pydoctor.  If you want to generate the user documentation, you will need to install Twisted Lore.

To generate documentation:

```
make docs
```

Then open the docs/index.html file in a browser.
