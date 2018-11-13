from sqlalchemy import and_, or_
from datetime import datetime

from db.models.base import Session
from db.models.tags import Tag
from db.models.places import Hours, Place
from pytz import timezone


def get_open_bars_in_area(latitude, longitude, radius, timezone_string, limit=None, session=None, queryset=None):
	if not queryset:
		queryset = session.query(Place)
	places_with_bar_label = queryset.filter(Place.tags.any(Tag.name.in_(['bar'])))
	return get_open_places_in_area(latitude, longitude, radius, timezone_string, limit=None, session=session,
	                               queryset=places_with_bar_label)


def get_open_places_in_area(latitude, longitude, radius, timezone_string, limit=None, session=None, queryset=None):
	place_ids = find_in_range(latitude=latitude, longitude=longitude, radius=radius, limit=limit, session=session)
	return get_open_places(session, timezone_string, place_ids=place_ids, queryset=queryset)


def get_time_elements(timezone_string=None):
	if timezone_string == 'CDT':
		timezone_string = 'US/Central'
	elif timezone_string in ['EST', 'EDT'] or timezone_string is None:
		timezone_string = 'US/Eastern'
	elif timezone_string == 'PDT':
		timezone_string = 'US/Pacific'
	else:
		raise Exception("Timezone conversion not implemented: {}".format(timezone_string))
	tz = timezone(timezone_string)
	now = datetime.now(tz)
	hour = (now.hour * 100)
	today = now.isoweekday() if now.isoweekday() <= 6 else 0
	tomorrow = today + 1 if today < 6 else 0
	yesterday = today - 1
	if 0 <= now.minute < 15:
		current_quarter_hour = 0
	elif 15 <= now.minute < 30:
		current_quarter_hour = 15
	elif 30 <= now.minute < 45:
		current_quarter_hour = 30
	elif 45 <= now.minute < 60:
		current_quarter_hour = 45
	else:
		raise ValueError("can't figure out quarter hour")
	return hour, current_quarter_hour, today, tomorrow, yesterday


def get_open_places(session, timezone_string, place_ids=None, queryset=None):
	if not place_ids:
		place_ids = []
	hour, current_quarter_hour, today, tomorrow, yesterday = get_time_elements(timezone_string)
	# Open - Close (Same Day) ex: 1000 - 2200 (It's 1700)
	same_day = and_(Hours.open_day_num == today, Hours.close_day_num == today, Hours.open_hour <= hour,
	                Hours.close_hour > hour)

	# Open - End of day if Cross Day ex: 1000 - 0200 Tomorrow (It's 1700).  Calculates up to Midnight
	close_past_midnight_current_day = and_(Hours.open_day_num == today, Hours.close_day_num == tomorrow,
	                                       Hours.open_hour < hour)

	# Yesterday Opening until Yesterday's close time for today.  ex: 1800 Yesterday - 0200 Today (It's 0100)
	close_past_midnight_next_day_early_morning = and_(Hours.open_day_num == yesterday, Hours.close_day_num == today,
	                                                  Hours.close_hour > hour)
	filter_ = or_(same_day, close_past_midnight_current_day, close_past_midnight_next_day_early_morning)
	if queryset:
		open_places = queryset.join(Hours).filter(filter_).filter(Place.id.in_(place_ids))
	else:
		open_places = session.query(Place).join(Hours).filter(filter_).filter(Place.id.in_(place_ids))
	return open_places


def find_in_range(latitude, longitude, radius=50, limit=None, table='places'):
	# https://www.plumislandmedia.net/mysql/haversine-mysql-nearest-loc/
	sql = '''
			SELECT id FROM (
			 SELECT z.id, z.latitude, z.longitude,
			        p.radius,
			        p.distance_unit * DEGREES(ACOS(COS(RADIANS(p.latpoint))
			                 		* COS(RADIANS(z.latitude))
			                 		* COS(RADIANS(p.longpoint - z.longitude))
			                 		+ SIN(RADIANS(p.latpoint))
			                 		* SIN(RADIANS(z.latitude)))) AS distance
			  FROM {} AS z
			  JOIN (
			        SELECT  {}  AS latpoint,  {} AS longpoint,
			                {} AS radius,      69.0 AS distance_unit
			    ) AS p ON 1=1
			  WHERE z.latitude
			     BETWEEN p.latpoint  - (p.radius / p.distance_unit)
			         AND p.latpoint  + (p.radius / p.distance_unit)
			    AND z.longitude
			     BETWEEN p.longpoint - (p.radius / (p.distance_unit * COS(RADIANS(p.latpoint))))
			         AND p.longpoint + (p.radius / (p.distance_unit * COS(RADIANS(p.latpoint))))
			 ) AS d
			 WHERE distance <= radius
			 ORDER BY distance
		'''.format(table, latitude, longitude, radius)
	if limit:
		sql += "\n LIMIT {}".format(limit)
	from sqlalchemy import text
	sql = text(sql)
	results = Session.execute(sql)

	return [x[0] for x in results if results]
