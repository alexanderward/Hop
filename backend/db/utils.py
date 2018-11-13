from datetime import datetime, timedelta
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql import ClauseElement
from sqlalchemy.sql import Insert
from db.models.base import inspector, engine, Session


class SQLAlchemyHelper(object):
	@staticmethod
	def get_or_create(model, defaults=None, **kwargs):
		instance = Session().query(model)
		unique_constraints_dict = dict()
		tmp = inspector.get_unique_constraints(model.__tablename__)
		tmp_lists = [x.get('column_names') for x in tmp]
		unique_constraints = set([item for sublist in tmp_lists for item in sublist])
		for column in unique_constraints:
			unique_constraints_dict[column] = kwargs.get(column)
		if not unique_constraints:
			instance = instance.filter_by(**kwargs).first()
		else:
			instance = instance.filter_by(**unique_constraints_dict).first()
		if instance:
			return instance, False
		else:
			params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
			params.update(defaults or {})
			instance = model(**params)
			Session().merge(instance)
			return instance, True

	@staticmethod
	def upsert(model, **kwargs):
		row_object, created = SQLAlchemyHelper.get_or_create(model, **kwargs)
		if not created:
			# model.set_Session()(Session())
			for key, value in kwargs.items():
				setattr(row_object, key, value)
			row_object = Session().merge(row_object)
		Session().commit()
		return row_object, created

	@staticmethod
	def bulk_upsert(model, data):

		@compiles(Insert, 'mysql')
		def suffix_insert(insert, compiler, **kw):
			stmt = compiler.visit_insert(insert, **kw)
			if 'mysql_on_duplicate' in insert.dialect_kwargs and insert.kwargs['mysql_on_duplicate']:
				my_var = insert.kwargs['mysql_on_duplicate']
				bb = ["{}=VALUES({})".format(x, x) for x in my_var]
				stmt += ' ON DUPLICATE KEY UPDATE %s' % (", ".join(bb))
			return stmt

		Insert.argument_for('mysql', 'on_duplicate', None)

		engine.execute(model.__table__.insert(mysql_on_duplicate=model.columns), data)


def gt(dt_str):
	dt, _, us = dt_str.partition(".")
	dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
	us = int(us.rstrip("Z"), 10)
	return dt + timedelta(microseconds=us)
