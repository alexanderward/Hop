class BaseSerializer(object):
	RELATIONSHIPS_TO_DICT = True
	__fields = '__all__'
	__data = None
	expand_relationships = []
	rename_fields_as = {}

	@property
	def model(self):
		return self.__model

	@model.setter
	def model(self, model_):
		self.__model = model_

	@property
	def fields(self):
		return self.__fields

	@fields.setter
	def fields(self, fields_):
		self.__fields = fields_

	@property
	def data(self):
		return self.__data

	@data.setter
	def data(self, data_):
		self.__data = data_


class AllSerializer(BaseSerializer):
	fields = '__all__'
