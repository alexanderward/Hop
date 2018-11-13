from lambdas.utils.aws import AWSHelper

try:
	import unzip_requirements
except ImportError:
	pass
from lambdas.utils.utils import get_querystring
from lambdas.utils.http.response import controller, Response
from lambdas.utils.http.status_codes import HTTP_200_OK
import settings


@controller
def lambda_handler(event, context):
	data = {
		'state': 'running',
		'instances': []
	}
	instances = AWSHelper.EC2.get_instances(stack=settings.STACK, tags={'type': [get_querystring(event, 'type')]},
	                                        running=True)
	data['instances'] = [x.id for x in instances]
	return Response(data, status=HTTP_200_OK)


if __name__ == '__main__':
	from lambdas.utils.dev_utils import sample_http_request

	sample_http_request(function=lambda_handler,
	                    path_params={},
	                    body_params={},
	                    querystrings={'type': 'pgbouncer'})
