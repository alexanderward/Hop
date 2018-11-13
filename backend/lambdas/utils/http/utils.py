import datetime
from collections import OrderedDict
from decimal import Decimal

import six

from lambdas.utils.http import status_codes

_PROTECTED_TYPES = (
	type(None), int, float, Decimal, datetime.datetime, datetime.date, datetime.time,
)


class CustomUnicodeDecodeError(UnicodeDecodeError):
	def __init__(self, obj, *args):
		self.obj = obj
		super().__init__(*args)

	def __str__(self):
		return '%s. You passed in %r (%s)' % (super().__str__(), self.obj, type(self.obj))


def unicode_to_repr(value):
	# Coerce a unicode string to the correct repr return type, depending on
	# the Python version. We wrap all our `__repr__` implementations with
	# this and then use unicode throughout internally.
	if six.PY2:
		return value.encode('utf-8')
	return value


def is_protected_type(obj):
	"""Determine if the object instance is of a protected type.

	Objects of protected types are preserved as-is when passed to
	force_text(strings_only=True).
	"""
	return isinstance(obj, _PROTECTED_TYPES)


def force_text(s, encoding='utf-8', strings_only=False, errors='strict'):
	"""
	Similar to smart_text, except that lazy instances are resolved to
	strings, rather than kept as lazy objects.

	If strings_only is True, don't convert (some) non-string-like objects.
	"""
	# Handle the common case first for performance reasons.
	if issubclass(type(s), str):
		return s
	if strings_only and is_protected_type(s):
		return s
	try:
		if isinstance(s, bytes):
			s = str(s, encoding, errors)
		else:
			s = str(s)
	except UnicodeDecodeError as e:
		raise CustomUnicodeDecodeError(s, *e.args)
	return s


class ReturnDict(OrderedDict):
	"""
	Return object from `serializer.data` for the `Serializer` class.
	Includes a backlink to the serializer instance for renderers
	to use if they need richer field information.
	"""

	def __init__(self, *args, **kwargs):
		self.serializer = kwargs.pop('serializer')
		super(ReturnDict, self).__init__(*args, **kwargs)

	def copy(self):
		return ReturnDict(self, serializer=self.serializer)

	def __repr__(self):
		return dict.__repr__(self)

	def __reduce__(self):
		# Pickling these objects will drop the .serializer backlink,
		# but preserve the raw data.
		return dict, (dict(self),)


class ReturnList(list):
	"""
	Return object from `serializer.data` for the `SerializerList` class.
	Includes a backlink to the serializer instance for renderers
	to use if they need richer field information.
	"""

	def __init__(self, *args, **kwargs):
		self.serializer = kwargs.pop('serializer')
		super(ReturnList, self).__init__(*args, **kwargs)

	def __repr__(self):
		return list.__repr__(self)

	def __reduce__(self):
		# Pickling these objects will drop the .serializer backlink,
		# but preserve the raw data.
		return list, (list(self),)


def get_error_details(data, default_code=None):
	"""
    Descend into a nested data structure, forcing any
    lazy translation strings or strings into `ErrorDetail`.
    """
	if isinstance(data, list):
		ret = [
			get_error_details(item, default_code) for item in data
			]
		if isinstance(data, ReturnList):
			return ReturnList(ret, serializer=data.serializer)
		return ret
	elif isinstance(data, dict):
		ret = {
			key: get_error_details(value, default_code)
			for key, value in data.items()
			}
		if isinstance(data, ReturnDict):
			return ReturnDict(ret, serializer=data.serializer)
		return ret

	# text = force_text(data)
	text = str(data)
	code = getattr(data, 'code', default_code)
	return ErrorDetail(text, code)


def _get_codes(detail):
	if isinstance(detail, list):
		return [_get_codes(item) for item in detail]
	elif isinstance(detail, dict):
		return {key: _get_codes(value) for key, value in detail.items()}
	return detail.code


def _get_full_details(detail):
	if isinstance(detail, list):
		return [_get_full_details(item) for item in detail]
	elif isinstance(detail, dict):
		return {key: _get_full_details(value) for key, value in detail.items()}
	return {
		'message': detail,
		'code': detail.code
	}


class ErrorDetail(six.text_type):
	"""
    A string-like object that can additionally have a code.
    """
	code = None

	def __new__(cls, string, code=None):
		self = super(ErrorDetail, cls).__new__(cls, string)
		self.code = code
		return self

	def __eq__(self, other):
		r = super(ErrorDetail, self).__eq__(other)
		try:
			return r and self.code == other.code
		except AttributeError:
			return r

	def __ne__(self, other):
		return not self.__eq__(other)

	def __repr__(self):
		return unicode_to_repr('ErrorDetail(string=%r, code=%r)' % (
			six.text_type(self),
			self.code,
		))

	def __hash__(self):
		return hash(str(self))


class APIException(Exception):
	"""
    Base class for REST framework exceptions.
    Subclasses should provide `.status_code` and `.default_detail` properties.
    """
	status_code = status_codes.HTTP_500_INTERNAL_SERVER_ERROR
	default_detail = 'A server error occurred.'
	default_code = 'error'

	def __init__(self, detail=None, code=None):
		if detail is None:
			detail = self.default_detail
		if code is None:
			code = self.default_code

		self.detail = get_error_details(detail, code)

	def __str__(self):
		return six.text_type(self.detail)

	def get_codes(self):
		"""
        Return only the code part of the error details.
        Eg. {"name": ["required"]}
        """
		return _get_codes(self.detail)

	def get_full_details(self):
		"""
        Return both the message & code parts of the error details.
        Eg. {"name": [{"message": "This field is required.", "code": "required"}]}
        """
		return _get_full_details(self.detail)
