import json
import traceback

from lambdas.utils.decorators import db_session
from settings import STACK

from lambdas.utils.http.utils import APIException
from lambdas.utils.http.status_codes import HTTP_200_OK
from lambdas.utils.log import err, log


class ResponseWrapper(object):
	class ResponseDict(object):
		def __init__(self, value):
			self.value = value

		def get_value(self):
			return self.value

	def __call__(self, data, status=None):
		if not status:
			status = HTTP_200_OK
		return self.ResponseDict({
			"headers": {
				"Access-Control-Allow-Origin": "*",
				'Access-Control-Allow-Credentials': True,
			},
			"statusCode": status,
			"body": json.dumps(data)
		})


from functools import wraps


def double_decorator(inner_dec):
	def ddmain(outer_dec):
		def decwrapper(f):
			wrapped = inner_dec(outer_dec(f))

			def fwrapper(*args, **kwargs):
				return wrapped(*args, **kwargs)

			return fwrapper

		return decwrapper

	return ddmain


# @double_decorator(db_session)
def controller(fn):
	@wraps(fn)
	def wrapper(*args, **kwargs):
		log("event", args[0])
		try:
			results = fn(*args, **kwargs)
			if not issubclass(results.__class__, ResponseWrapper.ResponseDict):
				raise Exception("Missing Response(data, status=status_code.XXXX) in Lambda return value")
			return results.get_value()
		except Exception as exc:
			err("Traceback", traceback.format_exc())
			if not issubclass(exc.__class__, APIException):
				if STACK != 'prod':
					exc = APIException(traceback.format_exc())
				else:
					exc = APIException(APIException.default_detail)
			if isinstance(exc.detail, (list, dict)):
				data = {'detail': ", ".join(["{}: {}".format(exc.__class__.__name__, str(x)) for x in exc.detail])}
			else:
				data = {'detail': "{}: {}".format(exc.__class__.__name__, str(exc.detail))}
			return Response(data, status=exc.status_code).get_value()

	return wrapper


Response = ResponseWrapper()
