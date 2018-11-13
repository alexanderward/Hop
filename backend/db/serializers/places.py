from db.serializers.base import BaseSerializer


class PlacesSerializer(BaseSerializer):
	fields = ['average_time_spent_at_location', 'formatted_address', 'current_popularity', 'map_url', 'website',
	          'name', 'tags', 'photo', 'photo_width', 'photo_height', 'icon', 'latitude', 'longitude', 'phone',
	          'rating']


class HoursSerializer(BaseSerializer):
	fields = ['open_day_num', 'close_day_num', 'open_hour', 'close_hour']


class WeekDayTextSerializer(BaseSerializer):
	fields = ['text']


class ActivityHoursSerializer(BaseSerializer):
	fields = ['popularity', 'wait_time']
