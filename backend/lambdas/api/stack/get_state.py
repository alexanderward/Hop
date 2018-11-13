try:
	import unzip_requirements
except ImportError:
	pass
import settings
from lambdas.utils.aws import AWSHelper
from lambdas.utils.http.response import controller, Response
from lambdas.utils.http.status_codes import HTTP_200_OK


@controller
def lambda_handler(event, context):
	data = {
		'instances': []
	}
	ec2_instances = AWSHelper.EC2.get_instances(stack=settings.STACK)
	data['instances'] += [{'id': x.id,
	                       'service': 'ec2',
	                       'status': x.state.get('Name'),
	                       'tags': ["{}:{}".format(tag['Key'], tag['Value']) for tag in x.tags if tag['Key'] not
	                                in ['app', 'stack']]}
	                      for x in ec2_instances]

	rds_instances = AWSHelper.RDS.get_instances(stack=settings.STACK)
	data['instances'] += [{'id': x['instance']['DBInstanceIdentifier'],
	                       'service': 'rds',
	                       'status': x['instance']['DBInstanceStatus'],
	                       'tags': ["{}:{}".format(tag['Key'], tag['Value']) for tag in x['tags']]} for x in rds_instances]

	return Response(data, status=HTTP_200_OK)


if __name__ == '__main__':
	from lambdas.utils.dev_utils import sample_http_request

	sample_http_request(function=lambda_handler,
	                    path_params={},
	                    body_params={},
	                    querystrings={})
