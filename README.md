Flipper ircbot
==============


## Requirements

* Python 3.10
* [irc](http://pypi.python.org/pypi/irc) - IRC protocol client library for Python 
* [SQLAlchemy](http://www.sqlalchemy.org/)
* [Psycopg](https://www.psycopg.org/docs/)
* [pytz](http://pytz.sourceforge.net/) - World Timezone Definitions for Python
* [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/)


### Installing with pip

    pip install pipenv
    pipenv install


## Database

A PostgreSQL database is required for most features to fully work. Use the
included docker compose config for a low effort development database setup:

   docker-compose up -d --force-recreate --renew-anon-volumes postgres


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


## Running the bot

Run the main entrypoint from the `src` directory:

    cd src
    pipenv run ./flipper.py


## Running single commands

Run the CLI harness from the `src` directory:

    cd src
    pipenv run ./cli.py <command> [args]

Commands are invoked just like in IRC but without the command prefix. E.g.:

    pipenv run ./cli.py sää helsinki


## Formatting and linting

To keep changes minimal over the originally non-autoformatted code, autopep8 is 
used for linting. Run the formatter from the project root:

    pipenv run autopep8 --in-place --recursive src/ scripts/

Ruff is used for static analysis. Run the linter from the project root:

    pipenv run ruff check src/ scripts/

Auto-fix safe issues:

    pipenv run ruff check src/ scripts/ --fix


## Optional dependencies

* [Data files](../../../flipper_data) for importer scripts and talkcommand.


### Importing data files using scripts

    $ cd scripts
    $ PYTHONPATH=../src python markov_import_flat_file.py
    $ PYTHONPATH=../src python markov_import_xml.py
