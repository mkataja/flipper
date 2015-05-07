import contextlib
import logging

from sqlalchemy.engine import create_engine
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import sessionmaker

import config


def initialize():
    logging.info("Initializing database connection to " + config.DATABASE_URI)
    engine = create_engine(config.DATABASE_URI, pool_size=10)
    global Session
    Session = scoped_session(sessionmaker(bind=engine))

@contextlib.contextmanager
def get_session():
    try:
        logging.info("Creating SQLAlchemy session")
        yield Session()
    finally:
        logging.info("Removing SQLAlchemy session")
        Session.remove()
