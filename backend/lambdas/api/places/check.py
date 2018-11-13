try:
	import unzip_requirements
except ImportError:
	pass
from lambdas.utils.http.response import controller, Response
from lambdas.utils.http.status_codes import HTTP_200_OK
from lambdas.processing.helper_functions import find_in_range
from lambdas.utils.utils import get_post_param
from datetime import datetime, timedelta
from math import floor
from db.models import FindNearbyPlacesSearch
import uuid
import os
import boto3
import json

SQS_CLIENT = boto3.client('sqs')


@controller
def lambda_handler(event, context):
	lat = get_post_param(event, 'latitude')
	lng = get_post_param(event, 'longitude')
	uuid_ = uuid.uuid4().hex
	previous_searches = find_in_range(lat, lng, radius=floor(1 * .5), limit=None,
	                                  table='find_nearby_place_searches')
	queryset = FindNearbyPlacesSearch.query.filter(FindNearbyPlacesSearch.id.in_(previous_searches))

	current_time = datetime.utcnow()
	half_year = current_time - timedelta(weeks=26)
	previous_searches_half_year = queryset.filter(FindNearbyPlacesSearch.created > half_year).all()
	if not previous_searches:
		SQS_CLIENT.send_message(QueueUrl=os.getenv('SQS_URL'), MessageBody=json.dumps({'latitude': lat,
		                                                                               'longitude': lng,
		                                                                               'uuid': uuid_}))

	return Response({'need_to_scan': False if previous_searches_half_year else True,
	                 'latitude': lat,
	                 'uuid': uuid_,
	                 'longitude': lng}, status=HTTP_200_OK)


if __name__ == '__main__':
	from lambdas.utils.dev_utils import sample_http_request

	san_antonio = {
		'latitude': 29.434636,
		'longitude': -98.522472,
	}
	tysons = {
		'latitude': 38.901222,
		'longitude': -77.265259,
	}

	clarendon = {
		'latitude': 38.8863497,
		'longitude': -77.09520709999998,
	}

	sample_http_request(function=lambda_handler,
	                    path_params={},
	                    body_params=san_antonio,
	                    querystrings={})
