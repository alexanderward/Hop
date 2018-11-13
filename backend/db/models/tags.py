from sqlalchemy import Column, Integer, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from db.models.base import Base
from db.models.mixins.output import OutputMixin
from db.serializers.tags import TagsSerializer


class Tag(Base, OutputMixin):
	serializer = TagsSerializer
	__tablename__ = 'tags'

	id = Column(Integer, primary_key=True, autoincrement=True)

	name = Column(String(255))

	place_id = Column(Integer, ForeignKey('places.id'))
	place = relationship("Place", back_populates="tags")

	__table_args__ = (UniqueConstraint('name', 'place_id', name='_name_place_id'),)
