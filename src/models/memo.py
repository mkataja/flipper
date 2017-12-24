from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column, UniqueConstraint, ForeignKey
from sqlalchemy.sql.sqltypes import Text, Integer

from models.user import User
from services import database


class Memo(database.FlipperBase):
    created_by_user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    name = Column(Text, nullable=False)

    created_by_user = relationship(User)

    UniqueConstraint(name)

    lines = relationship('MemoLine', order_by='MemoLine.created_on')

    def basic_info(self):
        return {
            'name': self.name,
            'created_on': self.created_on,
            'created_by': self.created_by_user.nick,
        }

    def full_info(self):
        additional_info = {'lines': [l.full_info() for l in self.lines]}
        return {**self.basic_info(), **additional_info}
