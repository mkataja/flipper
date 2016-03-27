from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Text

from services import database


class Memo(database.FlipperBase):
    name = Column(Text, nullable=False)

    lines = relationship('MemoLine', order_by='MemoLine.created_on')

    def basic_info(self):
        return {
            'name': self.name,
            'created_on': self.created_on,
            'lines': [x.basic_info() for x in self.lines]
        }
