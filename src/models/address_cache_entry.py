from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Float, Text

from services import database


class AddressCacheEntry(database.FlipperBase):
    address = Column(Text, unique=True, nullable=False)
    # Nullable to support failed geocoding results:
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
