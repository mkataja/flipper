from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Text, Integer

from models.memo import Memo
from services import database
from sqlalchemy.orm import relationship


class MemoLine(database.FlipperBase):
    memo_id = Column(Integer, ForeignKey(Memo.id), nullable=False)
    content = Column(Text, nullable=False)

    memo = relationship(Memo)

    def basic_info(self):
        return {
                'created_on': self.created_on,
                'content': self.content,
                }
