from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Text, Boolean

from services import database


class ApiAccount(database.FlipperBase):
    name = Column(Text, nullable=False)
    key = Column(Text, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
