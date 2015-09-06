from sqlalchemy.sql.schema import Column, UniqueConstraint
from sqlalchemy.sql.sqltypes import Text

from services import database


class MarkovCorpus(database.FlipperBase):
    name = Column(Text, nullable=False)
    
    UniqueConstraint(name)
