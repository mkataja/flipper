Flipper ircbot
==============

Requirements
------------

* Python 3.4
* [irc](http://pypi.python.org/pypi/irc) - IRC protocol client library for Python 
* [SQLAlchemy](http://www.sqlalchemy.org/)
* [pytz](http://pytz.sourceforge.net/) - World Timezone Definitions for Python
* [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/)

Other
-----

* [Data files](../../../flipper_data) for talkcommand and importer scripts

Pip install commands
--------------------

    pip install irc
    pip install sqlalchemy
    pip install pytz
    pip install beautifulsoup4

Running importer scripts
------------------------

    $ cd scripts
    $ PYTHONPATH=../src python markov_import_flat_file.py
    $ PYTHONPATH=../src python markov_import_xml.py
