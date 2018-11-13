try:
	import unzip_requirements
except ImportError:
	pass
import time
from db.models import Hours
from db.models import Place
from db.models import Tag
from db.models import WeekDayText
from db.utils import SQLAlchemyHelper

from logger import get_logger

logger = get_logger(__file__)


def insert_details(details, street, city, country, state, zipcode, place_id, longitude, latitude, photo_string,
                   photo_height, photo_width, session):
	with session.no_autoflush:
		place_object, created = SQLAlchemyHelper.upsert(Place, name=details.get('name'), street=street,
		                                                city=city, state=state, zip_code=zipcode,
		                                                country=country, formatted_address=details['formatted_address'],
		                                                phone=details.get('formatted_phone_number', None),
		                                                icon=details.get('icon'), utc_offset=details.get('utc_offset'),
		                                                google_place_id=place_id, longitude=longitude,
		                                                latitude=latitude,
		                                                photo=photo_string, photo_height=photo_height,
		                                                photo_width=photo_width,
		                                                rating=details.get('rating'), rating_count=None,
		                                                current_popularity=None, map_url=details.get('url'),
		                                                website=details.get('website'))
		SQLAlchemyHelper.bulk_upsert(Tag, [{"name": x, 'place_id': place_object.id} for x in
		                                   set(tag.lower() for tag in details.get('types', []))])

		bulk_data = []
		for period in details.get('opening_hours', {}).get('periods', []):
			if set(period.keys()) == {'open', 'close'}:
				bulk_data.append({
					'open_day_num': period['open']['day'],
					'close_day_num': period['close']['day'],
					'open_hour': period['open']['time'],
					'close_hour': period['close']['time'],
					'place_id': place_object.id
				})
		SQLAlchemyHelper.bulk_upsert(Hours, bulk_data)

		bulk_data = []
		for weekday_text in details.get('opening_hours', {}).get('weekday_text', []):
			day = weekday_text.split(':')[0]
			day_num = Places.day_map[day]
			bulk_data.append({
				'text': weekday_text,
				'day_num': day_num,
				'place_id': place_object.id
			})
		SQLAlchemyHelper.bulk_upsert(WeekDayText, bulk_data)


def callback(message, session):
	uuid = message.get('uuid')
	data = message.get('data')
	final_uuid = message.get('final_uuid')
	if not final_uuid:
		t0 = time.time()
		insert_details(*data, session)
		print(
			"SQLAlchemy Core: Total time: " + str(time.time() - t0) + " secs")  # 16.6, 14.17, 13.83, 13.71
	else:
		complete_uuid(final_uuid, 'places.check')


if __name__ == '__main__':
	listener = RabbitQueueListen(url=EC2_URL, queue=FIND_PLACES_INSERT_DETAILS, callback=callback)
	listener.start()
