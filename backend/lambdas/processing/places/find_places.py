try:
	import unzip_requirements
except ImportError:
	pass
import copy
import json
import os
import boto3
from db.models import FindNearbyPlacesSearch
from db.utils import SQLAlchemyHelper
from lambdas.processing.google import get_coordinates_for_search, Places
from lambdas.utils.utils import get_post_param
from logger import get_logger
from settings import LARGE_CIRCLE_DIAMETER, SUB_CIRCLE_DIAMETER

logger = get_logger(__file__)
already_seen = []

SQS_CLIENT = boto3.client('sqs')


def find_places(coordinate, extras):
	lat, lng = coordinate
	logger.info('--> Searching for Places near {},{}'.format(lat, lng))
	local_places = list()
	bars = Places.places_nearby(lat, lng, place_type='bar', radius=SUB_CIRCLE_DIAMETER)
	if len(bars) >= 60:
		logger.warning("Too many bars in area {},{} with radius {}".format(lat, lng, SUB_CIRCLE_DIAMETER))
	dance_halls = Places.places_nearby(lat, lng, keyword='dance_hall', radius=SUB_CIRCLE_DIAMETER)
	if len(dance_halls) >= 60:
		logger.warning("Too many Dance Halls in area {},{} with radius {}".format(lat, lng, SUB_CIRCLE_DIAMETER))
	local_places += bars
	local_places += dance_halls
	unique_local_places = [x for x in {v['id']: v for v in local_places if v}.values() if x]
	logger.info('--> Found {} places near {},{}'.format(len(unique_local_places), lat, lng))
	place_list = []
	for place in unique_local_places:
		if place.get('id') not in already_seen:
			already_seen.append(place.get('id'))
			tmp = copy.deepcopy(extras)
			tmp['data'] = place
			place_list.append(tmp)

	return place_list


def lambda_handler(event, context):
	for record in event.get('Records', []):
		lat = get_post_param(record, 'latitude')
		lng = get_post_param(record, 'longitude')
		uuid_ = get_post_param(record, 'uuid')
		SQS_CLIENT.delete_message(QueueUrl=os.getenv('FindPlacesQueue_URL'), ReceiptHandle=record.get('receiptHandle'))
		SQLAlchemyHelper.upsert(FindNearbyPlacesSearch, latitude=lat, longitude=lng)
		coordinates = get_coordinates_for_search(coordinates=(float(lat), float(lng)),
		                                         large_circle_diameter=LARGE_CIRCLE_DIAMETER,
		                                         sub_circle_diameter=SUB_CIRCLE_DIAMETER)
		for coordinate in coordinates:
			for place in find_places(coordinate, {'latitude': lat, 'longitude': lng, 'uuid': uuid_}):
				SQS_CLIENT.send_message(QueueUrl=os.getenv('FindPlaceDetailsQueue_URL'), MessageBody=json.dumps(place))


if __name__ == '__main__':
	import uuid

	san_antonio = {
		'latitude': 29.434636,
		'longitude': -98.522472,
		'uuid': uuid.uuid4().hex
	}
	tysons = {
		'latitude': 38.901222,
		'longitude': -77.265259,
		'uuid': uuid.uuid4().hex
	}

	clarendon = {
		'latitude': 38.8863497,
		'longitude': -77.09520709999998,
		'uuid': uuid.uuid4().hex
	}
	bb = lambda_handler({
		'Records': [{
			'body': san_antonio
		}]
	}, None)
