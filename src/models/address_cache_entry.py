from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Text, Float

from services import database


class AddressCacheEntry(database.FlipperBase):
    address = Column(Text, unique=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
