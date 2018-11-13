try:
	import unzip_requirements
except ImportError:
	pass
import json
import os
import boto3
from lambdas.processing.google import Places
from lambdas.utils.utils import get_post_param
from logger import get_logger

logger = get_logger(__file__)
SQS_CLIENT = boto3.client('sqs')


def get_details(place, extras):
	logger.info('--> Retrieving Place Details for {}'.format(place['name']))
	latitude = place['geometry']['location']['lat']
	longitude = place['geometry']['location']['lng']
	place_id = place['place_id']

	details = Places.get_details(place_id)
	try:
		street, city, state, country = details['formatted_address'].split(',')[-4:]
		street = street.strip()
	except ValueError:
		street = None
		city, state, country = details['formatted_address'].split(',')[-4:]
	city = city.strip()
	state = state.strip()
	country = country.strip()
	try:
		state, zipcode = state.split(' ')
	except:
		state, zipcode = None, None
	photo_string = None
	photo_height = 0
	photo_width = 0
	for photo in details.get('photos', []):
		photo_string = photo.get('photo_reference')
		photo_height = photo.get('height')
		photo_width = photo.get('width')
		break

	extras['data'] = details, street, city, country, state, zipcode, \
	                 place_id, longitude, latitude, photo_string, photo_height, photo_width
	return extras


def lambda_handler(event, context):
	for record in event.get('Records', []):
		lat = get_post_param(record, 'latitude')
		lng = get_post_param(record, 'longitude')
		data = get_post_param(record, 'data')
		uuid = get_post_param(record, 'uuid')
		SQS_CLIENT.delete_message(QueueUrl=os.getenv('FindPlaceDetailsQueue'),
		                          ReceiptHandle=record.get('receiptHandle'))
		details = get_details(data, {'latitude': lat, 'longitude': lng, 'uuid': uuid})
		SQS_CLIENT.send_message(QueueUrl=os.getenv('InsertPlaceDetailsQueue'), MessageBody=json.dumps(details))


if __name__ == '__main__':
	message = {"latitude": 38.8863497, "longitude": -77.09520709999998, "uuid": "669c620b516749ecbab53e1b2c2dfe51",
	           "data": {"geometry": {"location": {"lat": 38.81057699999999, "lng": -77.187579},
	                                 "viewport": {"northeast": {"lat": 38.8117833302915, "lng": -77.18622151970848},
	                                              "southwest": {"lat": 38.8090853697085, "lng": -77.1889194802915}}},
	                    "icon": "https://maps.gstatic.com/mapfiles/place_api/icons/bar-71.png",
	                    "id": "d937b5ee7a5e889b69b22b6954b54fe72be6ad51", "name": "FanFood",
	                    "place_id": "ChIJDbX25tGyt4kRiQLiJonhi-A",
	                    "plus_code": {"compound_code": "RR66+6X Springfield, Lee, VA, United States",
	                                  "global_code": "87C4RR66+6X"}, "reference": "ChIJDbX25tGyt4kRiQLiJonhi-A",
	                    "scope": "GOOGLE",
	                    "types": ["bar", "point_of_interest", "establishment"],
	                    "vicinity": "7026 Leebrad Street, Springfield"}}

	lambda_handler({
		'Records': [{
			'body': message
		}]
	}, None)
