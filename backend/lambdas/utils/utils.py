import base64
import hashlib
import hmac
import json
import re
from datetime import datetime, timedelta

import itertools
from sqlalchemy import desc, asc, or_
from sqlalchemy import text

from sqlalchemy.orm.collections import InstrumentedList
from settings import PER_PAGE, DEFAULT_PAGE
from lambdas.utils.http.exceptions import ValidationError, PermissionDenied, ParseError

from sqlalchemy.sql import operators, extract

custom_operators = {
	'within_period': lambda c, v: within_date(c, v)
}
_operators = {
	'isnull': lambda c, v: (c == None) if v else (c != None),
	'exact': operators.eq,

	'gt': operators.gt,  # greater than , >
	'ge': operators.ge,  # greater than or equal, >=
	'lt': operators.lt,  # lower than, <
	'le': operators.le,  # lower than or equal, <=

	'in': operators.in_op,
	'between': lambda c, v: c.between(v[0], v[1]),

	'like': operators.like_op,
	'ilike': operators.ilike_op,
	'startswith': operators.startswith_op,
	'istartswith': lambda c, v: c.ilike(v + '%'),
	'endswith': operators.endswith_op,
	'iendswith': lambda c, v: c.ilike('%' + v),

	'year': lambda c, v: extract('year', c) == v,
	'month': lambda c, v: extract('month', c) == v,
	'day': lambda c, v: extract('day', c) == v
}


def get_querystring(event, variable, optional=False):
	default_value = None
	to_type = None
	raise_when_fail = False
	type_dict = {
		'to_int': lambda x: int(x),
		None: lambda x: x,
	}
	if variable == 'page':
		default_value = DEFAULT_PAGE
		to_type = 'to_int'
	elif variable == 'count':
		default_value = PER_PAGE
		to_type = 'to_int'
	elif variable == 'sort':
		default_value = 'id'
		to_type = None
	elif variable == 'all':
		default_value = False
	elif variable == 'filter':
		default_value = None
	else:
		raise_when_fail = True
	query_string = event.get('queryStringParameters', {})
	if query_string is None:
		query_string = {}
	value = query_string.get(variable, default_value)
	if not optional and value is None and raise_when_fail:
		raise ValidationError(
			"{} is missing from queryStringParameters".format(variable))
	value = type_dict[to_type](value)
	if value in ['true', 'True']:
		value = True
	elif value in ['false', 'False']:
		value = False
	elif value in ['null', 'None']:
		value = None

	return value


def get_path_parameter(event, variable):
	param = event.get('pathParameters', {}).get(variable, None)
	if param is None:
		raise ValidationError(
			"'{}' is missing from pathParameters".format(variable))
	return param


def get_header(event, variable):
	header_val = event.get('headers', {}).get(variable, None)
	if header_val is None:
		raise ValidationError("'{}' is missing from headers".format(variable))
	return header_val


def get_post_param(event, variable, optional=False):
	body = event.get('body', {})
	if not isinstance(body, dict):
		body = json.loads(body)

	value = body.get(variable, None)
	if value is None and not optional:
		raise ValidationError("'{}' is missing from the body".format(variable))
	return value


def build_filter_object(user_filter):

	custom_ors = {
		'request_search': ['title', 'request_info', 'cr_id']
	}

	filter_object = {}
	ors = []
	if user_filter:
		filter_strings = [x for x in user_filter.split('_AND_') if x]
		for filter_string in filter_strings:
			split_values = filter_string.split('=')
			key = split_values[0]
			value = "=".join(split_values[1:])
			split_key = key.split('__')
			column = split_key[0]
			operator = split_key[-1]
			if value in ['true', 'True']:
				value = True
			elif value in ['false', 'False']:
				value = False
			elif value in ['null', 'None']:
				value = None
			if 'like' in operator:
				value = "%" + value + "%"
			elif 'in' == operator:
				value = [x.strip() for x in value.split(',')]
			if column in custom_ors.keys():
				or_list = []
				for col in custom_ors[column]:
					formatted_operation = '{}__{}'.format(col, operator)
					filter_string = '{}={}'.format(formatted_operation, value)
					filter_strings.append(filter_string)
					or_list.append(formatted_operation)
				ors.append(or_list)
				continue
			filter_object[key] = value
	return filter_object, ors


def build_sort_object(user_sort):
	sort_object = {}
	if user_sort:
		for sort_string in user_sort.split(','):
			fk = sort_string.split('__')[0].replace('-', '')
			sort_object[fk] = sort_string
	return sort_object


def within_date(key, value):
	time_units = ['days', 'seconds', 'microseconds', 'milliseconds', 'minutes', 'hours', 'weeks']
	try:
		unit, value = value.split(":")
		assert unit in time_units
		kwargs = {unit: int(value)}
	except:
		raise ValidationError("within_filter requires the format of within_format=unit:duration ex: week:1.  Valid "
		                      "units are {}".format(",".join(time_units)))

	return text("{} >= '{}'".format(key, datetime.now() - timedelta(**kwargs)))


def get_queryset(model=None, filter_str=None, sort_str=None):
	filters, ors, sorts, manual_joined_filters, custom_filters, manual_sorts = get_filters_sorts(
		model, filter_str, sort_str)
	or_dict = {}
	for or_query in ors:
		for item in or_query:
			or_dict[item] = filters.pop(item)

	_operators.update(custom_operators)
	try:
		queryset = model.smart_query(filters=filters, sort_attrs=sorts)
	except KeyError as e:
		invalid_column = re.match('.*?incorrect attribute `(.*?)`', str(e))
		if invalid_column:
			raise ValidationError(
				"No relationship found on '{}' for '{}'".format(model.__tablename__, invalid_column.group(1)))
		raise ParseError(str(e))

	for filter_name, value in custom_filters:
		tmp = filter_name.split('__')
		op = tmp[-1]
		field_name = "__".join(tmp[:-1])
		relate = _operators.get(op)
		queryset = queryset.filter(relate("{}.{}".format(model.__tablename__, field_name), value))

	for filter_name, value in manual_joined_filters:
		tmp = filter_name.split('__')
		op = tmp[-1]
		field_name = "__".join(tmp[:-1])
		queryset, field = join_tables(model, field_name, queryset)
		relate = _operators.get(op)
		queryset = queryset.filter(relate(field, value))

	or_query = []
	for filter_name_, or_value in or_dict.items():
		tmp = filter_name_.split('__')
		op = tmp[-1]
		field_name = "__".join(tmp[:-1])
		field = or_mapper(model, field_name)
		relate = _operators.get(op)
		or_query.append((relate(field, or_value)))
	if or_query:
		queryset = queryset.filter(or_(*or_query))

	for field_name in manual_sorts:
		direction = desc if "-" in field_name else asc
		if desc:
			field_name = field_name.replace('-', '')
		queryset, field = join_tables(model, field_name, queryset)
		queryset = queryset.order_by(direction(field))
	return queryset.distinct()


def join_tables(model, field_name, queryset):
	fields = field_name.split('__')
	field = None
	for field_name, field_name_in_relation in zip(fields, fields[1:]):
		relation = getattr(model, field_name)
		relation_model = relation.mapper.class_
		field = getattr(relation_model, field_name_in_relation)
		queryset = queryset.join(relation)
		model = relation_model
	if not field:
		raise ValidationError(
			"Column not provided for model '{}'.  Unable to filter".format(field_name))
	return queryset, field


def or_mapper(model, field_name):
	return getattr(model, field_name)


def print_query(queryset):
	from sqlalchemy.dialects import mysql
	print("\n{}\n" .format(str(queryset.statement.compile(dialect=mysql.dialect()))))


def add_joins_if_missing(joins, queryset):
	# Defunct. Work in progress
	print('Current Joins: ', [mapper.class_ for mapper in queryset._join_entities])
	for join_class in joins:
		if join_class not in [mapper.class_ for mapper in queryset._join_entities]:
			if join_class.__tablename__ not in list(itertools.chain.from_iterable([x.relationships.keys() for x in queryset._join_entities])):
				print('** Join was missing **', join_class)
				queryset = queryset.join(join_class)
				print('New Joins: ', [mapper.class_ for mapper in queryset._join_entities])
			# queryset._join_entities.append(join_class)
	return queryset


def get_filters_sorts(model, filter_str, sort_str):
	joins = model.relations
	filters, ors = build_filter_object(filter_str)
	sorts = build_sort_object(sort_str)
	manual_joined_filters = []
	manual_sorts = []
	custom_filters = []

	remove_filters = list()
	for filter_, value in filters.items():
		tmp = filter_.split('__')
		fk = tmp[0]
		op = tmp[-1]
		if fk in joins:
			manual_joined_filters.append((filter_, value))
			remove_filters.append(filter_)
		elif op in custom_operators.keys():
			custom_filters.append((filter_, value))
			remove_filters.append(filter_)
	remove_sorts = list()
	for fk_, value in sorts.items():
		if fk_ in joins:
			manual_sorts.append(value)
			remove_sorts.append(fk_)

	for remove_filter in remove_filters:
		filters.pop(remove_filter)

	for remove_sort in remove_sorts:
		sorts.pop(remove_sort)
	return filters, ors, [x for x in sorts.values()], manual_joined_filters, custom_filters, manual_sorts


def check_if_field_is_dirty(event, field, model):
	name = field.get('name', None)
	validator = field.get('validator', None)
	formatter = field.get('formatter', None)
	field_value = get_post_param(event, name, optional=True)
	if field_value is None:
		return False

	current_value = getattr(model, name)
	if validator:
		validator(field_value)
	if isinstance(current_value, str):
		if current_value == field_value:
			return False
		if formatter:
			field_value = formatter(field_value)
	elif isinstance(current_value, InstrumentedList):
		if set(current_value) != set(field_value):
			field_value = [formatter(x) for x in field_value]
		else:
			return False
	else:
		raise ValueError(
			"Unknown Type '{}' - need to add proper type checking".format(type(current_value)))
	setattr(model, name, field_value)
	return True


def partial_update(event, model, session, fields):
	form_is_dirty = []
	for field in fields:
		dirty = check_if_field_is_dirty(event, field, model)
		form_is_dirty.append(dirty)

	if any(form_is_dirty):
		session.add(model)
		session.commit()
