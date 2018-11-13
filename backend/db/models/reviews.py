from sqlalchemy import Column, Integer, ForeignKey, String, Text, Float
from sqlalchemy.orm import relationship

from db.models.base import Base
from db.models.mixins.output import OutputMixin
from db.serializers.reviews import ReviewsSerializer


class Review(Base, OutputMixin):
	serializer = ReviewsSerializer
	__tablename__ = 'reviews'

	id = Column(Integer, primary_key=True, autoincrement=True)

	time = Column(Integer)
	text = Column(Text)
	relative_time_description = Column(String(255))
	profile_photo_url = Column(String(255))
	rating = Column(Integer)
	author_url = Column(String(255))
	language = Column(String(10))
	author_name = Column(String(255))
	google_maps_url = Column(String(255))
	website = Column(String(255))

	rating_count = Column(Integer)
	current_popularity = Column(Integer)
	latitude = Column(Float)
	longitude = Column(Float)

	place_id = Column(Integer, ForeignKey('places.id'))
	place = relationship("Place")#  , back_populates="reviews")
