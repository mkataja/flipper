Flipper ircbot
==============


## Requirements

* Python 3.10
* [irc](http://pypi.python.org/pypi/irc) - IRC protocol client library for Python 
* [SQLAlchemy](http://www.sqlalchemy.org/)
* [Psycopg](https://www.psycopg.org/docs/)
* [pytz](http://pytz.sourceforge.net/) - World Timezone Definitions for Python
* [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/)
* [Flask](http://flask.pocoo.org/)


### Installing with pip

    pip install -r requirements.txt


## Configuring

Create a new `config_local.py` by copying the example config:

    cp config_local.py.example config_local.py

Open `config_local.py` and change the defaults to suit your preferences.

At the very least set the following options:

 * `NICK`: Set to something unique
 * `SERVER`: Use your preferred server or try some of the supplied alternatives
 * `DATABASE_URI`: Point to an existing postgresql database or use `None` to run
   without a database (but note that a database is required by most features)

Required by some features, will run fine without setting these:

 * `GOOGLE_API_KEY`: required by specific commands
 * `API_HOST` and `WEBUI_ADDRESS`: related to web UI integration


## Running

Run the main entrypoint from the `src` directory:

    cd src
    ./flipper.py


## Optional dependencies

* [Data files](../../../flipper_data) for importer scripts and talkcommand.


### Importing data files using scripts

    $ cd scripts
    $ PYTHONPATH=../src python markov_import_flat_file.py
    $ PYTHONPATH=../src python markov_import_xml.py
