import contextlib
import logging
import re

from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative.api import declarative_base, declared_attr
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer

import config
from sqlalchemy.exc import SQLAlchemyError


def initialize():
    global Session
    Session = None
    if not config.DATABASE_URI:
        logging.error("Cannot initialize the database service: "\
                      "DATABASE_URI not configured")
        return
    logging.info("Initializing database connection to " + config.DATABASE_URI)
    try:
        engine = create_engine(config.DATABASE_URI, pool_size=10)
        FlipperBase.metadata.create_all(engine)
    except SQLAlchemyError as e:
        logging.error("Failed to initialize database: " + str(e))
        return
    Session = scoped_session(sessionmaker(bind=engine))

@contextlib.contextmanager
def get_session():
    if not Session:
        raise ValueError("Tried to get database session "\
                         "but database is not initialized")
    try:
        logging.info("Creating SQLAlchemy session")
        yield Session()
    finally:
        logging.info("Removing SQLAlchemy session")
        Session.remove()
        

Base = declarative_base()

class FlipperBase(Base):
    __abstract__ = True
    
    _tablename = None
    
    @declared_attr
    def __tablename__(self):
        if self._tablename is None:
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', self.__name__)
            self._tablename = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        return self._tablename

    id = Column(Integer, primary_key=True)
