from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Text, Boolean

from services import database


class Channel(database.FlipperBase):
    name = Column(Text, nullable=False)
    autojoin = Column(Boolean, nullable=False, default=False)
    commands_enabled = Column(Boolean, nullable=False, default=True)

    @classmethod
    def get_or_create(cls, channel_name):
        channel_name = channel_name.lower()
        with database.get_session() as session:
            channel = session.query(Channel).filter_by(name=channel_name).first()
            if not channel:
                channel = Channel()
                channel.name = channel_name
                session.add(channel)
                session.commit()
            return channel
