
class Serialize(object):
	def __init__(self, queryset, session=None):
		self.queryset = queryset
		self.session = session
		self.data = self.get_data()

	def get_data(self):
		if isinstance(self.queryset, list):
			self.data = list()
			for row_obj in self.queryset:
				self.data.append(row_obj.to_json(session=self.session,
				                                 expand=row_obj.serializer.expand_relationships))
			return self.data
		else:
			return self.queryset.to_json(session=self.session, expand=self.queryset.serializer.expand_relationships)
