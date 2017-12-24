from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Text, Integer

from models.memo import Memo
from models.user import User
from services import database


class MemoLine(database.FlipperBase):
    memo_id = Column(Integer, ForeignKey(Memo.id), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    content = Column(Text, nullable=False)

    memo = relationship(Memo)
    created_by_user = relationship(User)

    def full_info(self):
        return {
            'created_on': self.created_on,
            'created_by': self.created_by_user.nick,
            'content': self.content,
        }
