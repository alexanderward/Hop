from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from db.models.tags import Tag
from db.models.base import Base
from db.models.mixins.output import OutputMixin
from db.serializers.places import PlacesSerializer, HoursSerializer, ActivityHoursSerializer, WeekDayTextSerializer


class Place(Base, OutputMixin):
	RELATIONSHIPS_TO_DICT_IGNORE = ['hours']
	serializer = PlacesSerializer
	__tablename__ = 'places'

	id = Column(Integer, primary_key=True, autoincrement=True)

	name = Column(String(255))
	street = Column(String(255))
	city = Column(String(255))
	state = Column(String(255))
	zip_code = Column(Integer)
	country = Column(String(255))
	formatted_address = Column(String(255))
	phone = Column(String(40))
	icon = Column(String(255))

	google_place_id = Column(String(255), unique=True)
	rating = Column(Integer)
	rating_count = Column(Integer)
	current_popularity = Column(Integer)
	latitude = Column(Float)
	longitude = Column(Float)

	utc_offset = Column(Integer)

	tags = relationship(Tag, back_populates="place")
	hours = relationship("Hours")
	weekday_text = relationship("WeekDayText")
	average_time_spent_at_location = Column(Text)

	photo = Column(Text)
	photo_height = Column(Integer)
	photo_width = Column(Integer)

	map_url = Column(String(255))
	website = Column(String(255))


class Hours(Base, OutputMixin):
	serializer = HoursSerializer
	__tablename__ = 'hours'

	id = Column(Integer, primary_key=True, autoincrement=True)

	open_day_num = Column(Integer)
	open_hour = Column(Integer)

	close_day_num = Column(Integer)
	close_hour = Column(Integer)

	place_id = Column(Integer, ForeignKey('places.id'))

	def __repr__(self):
		day_map = {
			0: "Sunday",
			1: "Monday",
			2: "Tuesday",
			3: "Wednesday",
			4: "Thursday",
			5: "Friday",
			6: "Saturday"
		}
		return "{}({}) - {}({})".format(day_map.get(self.open_day_num), self.open_hour,
		                                day_map.get(self.close_day_num), self.close_hour)

	__table_args__ = (
		UniqueConstraint('place_id', 'open_day_num', 'close_day_num', name='_place_id_open_day_num_close_day_num'),)


class WeekDayText(Base, OutputMixin):
	serializer = WeekDayTextSerializer
	__tablename__ = 'weekdays'

	id = Column(Integer, primary_key=True, autoincrement=True)
	text = Column(Text)

	day_num = Column(Integer)
	place_id = Column(Integer, ForeignKey('places.id'))

	__table_args__ = (UniqueConstraint('place_id', 'day_num', name='_day_number_place_id'),)


class ActivityHours(Base, OutputMixin):
	serializer = ActivityHoursSerializer
	__tablename__ = 'activity_hours'

	id = Column(Integer, primary_key=True, autoincrement=True)
	wait_time = Column(Integer)
	hour = Column(Integer)
	popularity = Column(Integer)

	day_number = Column(Integer)
	day_name = Column(String(10))

	place_id = Column(Integer, ForeignKey('places.id'))
	place = relationship('Place')

	__table_args__ = (UniqueConstraint('day_number', 'hour', 'place_id', name='_day_number_hour_place_id'),)
