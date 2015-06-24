from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Text, DateTime

from services import database


class LogEntry(database.FlipperBase):
    target = Column(Text, nullable=False)
    nick = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    message = Column(Text, nullable=False)
