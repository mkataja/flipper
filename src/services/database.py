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


def initialize():
    logging.info("Initializing database connection to " + config.DATABASE_URI)
    engine = create_engine(config.DATABASE_URI, pool_size=10)
    FlipperBase.metadata.create_all(engine)
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
