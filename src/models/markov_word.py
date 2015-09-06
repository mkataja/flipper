from sqlalchemy.sql.schema import Column, UniqueConstraint
from sqlalchemy.sql.sqltypes import Text

from services import database


class MarkovWord(database.FlipperBase):
    text = Column(Text, nullable=False)
    
    UniqueConstraint(text)
