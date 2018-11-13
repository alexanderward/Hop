import json
from uuid import UUID

from datetime import datetime
from sqlalchemy.ext.declarative import DeclarativeMeta


class OutputMixin(object):
	RELATIONSHIPS_TO_DICT = True

	def __iter__(self):
		return self.to_dict().iteritems()

	def to_dict(self, rel=None, backref=None):
		assert self.serializer.fields
		if self.serializer.fields != '__all__':
			for key in self.__mapper__.c._data.keys():
				if key not in self.serializer.fields:
					del self.__mapper__.c._data[key]

		if rel is None:
			rel = self.RELATIONSHIPS_TO_DICT
		res = {column.key: getattr(self, attr)
		       for attr, column in self.__mapper__.c.items()}
		if rel:
			for attr, relation in self.__mapper__.relationships.items():
				# Avoid recursive loop between to tables.
				if backref == relation.table or (self.serializer.fields != '__all__' and attr not in self.serializer.fields):
					continue
				value = getattr(self, attr)
				relation.key = self.serializer.rename_fields_as.get(relation.key, relation.key)
				if value is None:
					res[relation.key] = None
				elif isinstance(value.__class__, DeclarativeMeta):
					res[relation.key] = value.to_dict(backref=self.__table__)
					if res[relation.key] and isinstance(res[relation.key], dict):
						if len(res[relation.key].keys()) == 1:
							res[relation.key] = [v for k, v in res[relation.key].items()][0]

				else:
					res[relation.key] = [i.to_dict(backref=self.__table__)
					                     for i in value]
					if res[relation.key]:
						if len(res[relation.key][0].keys()) == 1:
							values = list()
							for row in res[relation.key]:
								for key, value in row.items():
									values.append(value)
								res[relation.key] = values
		return res

	def to_json_string(self, rel=None, expand=list(), session=None):
		def extended_encoder(x):
			if isinstance(x, datetime):
				return x.isoformat()
			if isinstance(x, UUID):
				return str(x)

		if rel is None:
			rel = self.RELATIONSHIPS_TO_DICT
		model_dict = self.to_dict(rel=rel)

		if session:
			for fk_group in expand:
				for fk_name, model in fk_group.items():
					if fk_name in model_dict.keys():  # Enforces the __serialize_fields__ in the model
						value = getattr(self, fk_name)
						result = session.query(model).filter(model.id == value).one_or_none()
						if result:
							model_dict[fk_name] = result.to_json()
		# for member, new_member in self.serializer.rename_fields_as.items():
		# 	model_dict[new_member] = model_dict.pop(member)
		results = json.dumps(model_dict, default=extended_encoder)
		return results

	def to_json(self, rel=None, expand=list(), session=None):
		return json.loads(self.to_json_string(rel=rel, expand=expand, session=session))
