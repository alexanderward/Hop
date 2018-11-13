import math

from lambdas.utils.http import status_codes
from lambdas.utils.http.utils import force_text, APIException


class ValidationError(APIException):
	status_code = status_codes.HTTP_400_BAD_REQUEST
	default_detail = 'Invalid input.'
	default_code = 'invalid'


class ParseError(APIException):
	status_code = status_codes.HTTP_400_BAD_REQUEST
	default_detail = 'Malformed request.'
	default_code = 'parse_error'


class AuthenticationFailed(APIException):
	status_code = status_codes.HTTP_401_UNAUTHORIZED
	default_detail = 'Incorrect authentication credentials.'
	default_code = 'authentication_failed'


class NotAuthenticated(APIException):
	status_code = status_codes.HTTP_401_UNAUTHORIZED
	default_detail = 'Authentication credentials were not provided.'
	default_code = 'not_authenticated'


class PermissionDenied(APIException):
	status_code = status_codes.HTTP_403_FORBIDDEN
	default_detail = 'You do not have permission to perform this action.'
	default_code = 'permission_denied'


class NotFound(APIException):
	status_code = status_codes.HTTP_404_NOT_FOUND
	default_detail = 'Not found.'
	default_code = 'not_found'


class MethodNotAllowed(APIException):
	status_code = status_codes.HTTP_405_METHOD_NOT_ALLOWED
	default_detail = 'Method "{method}" not allowed.'
	default_code = 'method_not_allowed'

	def __init__(self, method, detail=None, code=None):
		if detail is None:
			detail = force_text(self.default_detail).format(method=method)
		super(MethodNotAllowed, self).__init__(detail, code)


class NotAcceptable(APIException):
	status_code = status_codes.HTTP_406_NOT_ACCEPTABLE
	default_detail = 'Could not satisfy the request Accept header.'
	default_code = 'not_acceptable'

	def __init__(self, detail=None, code=None, available_renderers=None):
		self.available_renderers = available_renderers
		super(NotAcceptable, self).__init__(detail, code)


class UnsupportedMediaType(APIException):
	status_code = status_codes.HTTP_415_UNSUPPORTED_MEDIA_TYPE
	default_detail = 'Unsupported media type "{media_type}" in request.'
	default_code = 'unsupported_media_type'

	def __init__(self, media_type, detail=None, code=None):
		if detail is None:
			detail = force_text(self.default_detail).format(media_type=media_type)
		super(UnsupportedMediaType, self).__init__(detail, code)


class Throttled(APIException):
	status_code = status_codes.HTTP_429_TOO_MANY_REQUESTS
	default_detail = 'Request was throttled.'
	extra_detail_singular = 'Expected available in {wait} second.'
	extra_detail_plural = 'Expected available in {wait} seconds.'
	default_code = 'throttled'

	def __init__(self, wait=None, detail=None, code=None):
		if detail is None:
			detail = force_text(self.default_detail)
		if wait is not None:
			wait = math.ceil(wait)
		self.wait = wait
		super(Throttled, self).__init__(detail, code)
