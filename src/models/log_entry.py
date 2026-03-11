from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import DateTime, Integer, Text

from models.channel import Channel
from models.user import User
from services import database


class LogEntry(database.FlipperBase):
    channel_id = Column(Integer, ForeignKey(Channel.id), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    message = Column(Text, nullable=False)
