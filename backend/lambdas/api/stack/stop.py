try:
	import unzip_requirements
except ImportError:
	pass
from lambdas.utils.aws import AWSHelper
from lambdas.utils.http.response import controller, Response
from lambdas.utils.http.status_codes import HTTP_200_OK
from lambdas.utils.utils import get_post_param


@controller
def lambda_handler(event, context):
	ids = get_post_param(event, 'ids')

	ec2_ids = []
	rds_ids = []
	for item in ids:
		if item['service'] == 'ec2':
			ec2_ids.append(item['id'])

		if item['service'] == 'rds':
			rds_ids.append(item['id'])

	if ec2_ids:
		AWSHelper.EC2.stop_instances(ec2_ids)
	if rds_ids:
		AWSHelper.RDS.stop_instances(rds_ids)
	return Response({}, status=HTTP_200_OK)


if __name__ == '__main__':
	from lambdas.utils.dev_utils import sample_http_request

	sample_http_request(function=lambda_handler,
	                    path_params={},
	                    body_params={
		                    'ids': [
			                    {'service': 'ec2', 'id': 'i-0cbf115837e1c7b51'}
		                    ]
	                    },
	                    querystrings={})
