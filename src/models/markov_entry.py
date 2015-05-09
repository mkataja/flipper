from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, Text

from services import database


class MarkovEntry(database.FlipperBase):
    corpus_id = Column(Text, nullable=False)
    sentence_id = Column(Text, nullable=False)
    prev_2 = Column(Text, nullable=True)
    prev_1 = Column(Text, nullable=False)
    next = Column(Text, nullable=False)
