from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import ARRAY, Text

from services import database


class Channel(database.FlipperBase):
    name = Column(Text, nullable=False)
    alt_cmd_prefix = Column(Text, nullable=True, default=None)
    disabled_features = Column(ARRAY(Text), nullable=False, default=[])

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
