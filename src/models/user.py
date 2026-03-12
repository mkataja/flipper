from sqlalchemy.sql import expression
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Boolean, Integer, Text

from services import database

# TODO: Keep track of current nick?


class User(database.FlipperBase):
    nick = Column(Text, nullable=False)
    alias_of = Column(Integer, ForeignKey('user.id'), nullable=True)
    location = Column(Text, nullable=True)
    emoji_enabled = Column(
        Boolean, nullable=False, default=True, server_default=expression.true()
    )

    @classmethod
    def get_or_create(cls, user_nick):
        user_nick = user_nick.rstrip('_').lower()
        with database.get_session() as session:
            user = session.query(User).filter_by(nick=user_nick).first()
            if not user:
                user = User()
                user.nick = user_nick
                session.add(user)
                session.commit()
            return user

    def set_location(self, lat, long):
        with database.get_session() as session:
            self.location = f"{lat},{long}"
            session.commit()

    def set_emoji_enabled(self, enabled):
        with database.get_session() as session:
            self.emoji_enabled = enabled
            session.commit()
