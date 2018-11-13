import json
import pprint
from lambdas.utils.log import log


def sample_http_request(function, path_params, querystrings, body_params=None, return_data=False):
	results = function({
		"queryStringParameters": querystrings,
		"pathParameters": path_params,
		"headers": {
			# "Authorization": token if token else User.login(username, "Password1@").id_token
		},
		"body": body_params if body_params else {}
	}, 'context')
	if return_data:
		results['body'] = json.loads(results.get('body', '{}'))
		log('response', results)
		return results
	if isinstance(results, dict):
		if not results.get('detail'):
			pprint.pprint(json.loads(results.get('body', {})))
	else:
		pprint.pprint(json.loads(results.get('body', {})))
