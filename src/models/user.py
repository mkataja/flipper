from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Text, Integer

from services import database


class User(database.FlipperBase):
    nick = Column(Text, nullable=False)
    alias_of = Column(Integer, ForeignKey('user.id'), nullable=True)

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
