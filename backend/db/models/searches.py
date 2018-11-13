from sqlalchemy import Column, Integer, Float
from sqlalchemy import DateTime
from sqlalchemy import func

from db.models.base import Base
from db.models.mixins.output import OutputMixin


class RefreshPopularitySearch(Base, OutputMixin):
	__tablename__ = 'refresh_popularity_searches'

	id = Column(Integer, primary_key=True, autoincrement=True)

	place_id = Column(Integer, unique=True)
	hour = Column(Integer)
	quarter_hour = Column(Integer)  # 0, 15, 30, 45
	day = Column(Integer)


class FindNearbyPlacesSearch(Base):
	__tablename__ = 'find_nearby_place_searches'

	id = Column(Integer, primary_key=True, autoincrement=True)

	latitude = Column(Float)
	longitude = Column(Float)
	created = Column(DateTime(timezone=True), server_default=func.now())
