import calendar
import json
import time
import requests
from math import floor, ceil, radians, cos, sin, atan2, sqrt, asin, degrees
from geopy.distance import vincenty, VincentyDistance
from geopy import Point

from lambdas.processing.proxy import Proxy
from settings import GOOGLE_API_KEY
from logger import get_logger

logger = get_logger(__file__)


def check_response_code(resp):
	if resp["status"] == "OK" or resp["status"] == "ZERO_RESULTS":
		return

	if resp["status"] == "REQUEST_DENIED":
		logger.error("Your request was denied, the API key is invalid.")

	if resp["status"] == "OVER_QUERY_LIMIT":
		logger.error(
			"You exceeded your Query Limit for Google Places API Web Service, "
			"check https://developers.google.com/places/web-service/usage to upgrade your quota.")

	if resp["status"] == "INVALID_REQUEST":
		logger.error(
			"The query string is malformed, check params.json if your formatting for lat/lng and radius is correct.")

	raise Exception("Query Failed")


def get_results(url, query_parameters, results, pagination_delay=2):
	""" Requires at least 2 second delay for pagination for the next_page to propagate on Google servers"""
	params = {
		'key': GOOGLE_API_KEY
	}
	params.update(query_parameters)
	response = requests.get(url, params=params)
	response_json = response.json()
	check_response_code(response_json)
	next_token = response_json.get('next_page_token')
	returned_results = response_json.get('results')
	if not returned_results:
		returned_results = [response_json.get('result')]
	results += returned_results
	if next_token:
		next_params = {
			'pagetoken': next_token,
		}
		time.sleep(pagination_delay)
		get_results(url, next_params, results)
	return results


class Places(object):
	day_map = {
		'Sunday': 0,
		'Monday': 1,
		'Tuesday': 2,
		'Wednesday': 3,
		'Thursday': 4,
		'Friday': 5,
		'Saturday': 6
	}

	@staticmethod
	def places_nearby(_lat, _lng, place_type=None, keyword=None, radius=5000):
		""" Max of 60 records can be returned """
		url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
		conversion_factor = .00062137119
		meters = floor(radius / conversion_factor)
		parameters = {
			'location': '{},{}'.format(_lat, _lng),
			'radius': meters,
			# 'type': 'bar',
		}
		if keyword:
			parameters['keyword'] = keyword
		elif type:
			parameters['type'] = place_type
		# if place_types:
		# 	parameters['name'] = place_types if isinstance(place_types, str) else "|".join(place_types)
		results = get_results(url, parameters, [])
		if len(results) == 60:
			logger.warning("Results for Nearyby Search exceeded GEO area.  Try a smaller circle.")
		return results

	@staticmethod
	def text_search(_lat, _lng, query, radius=15):
		""" Max of 60 records can be returned & Counts as 10 Quota """
		url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
		if not isinstance(query, list):
			query = [query]

		conversion_factor = .00062137119
		meters = floor(radius / conversion_factor)

		query_list = []
		for q in query:
			parameters = {
				'location': '{},{}'.format(_lat, _lng),
				'radius': meters,
				'query': q
			}
			query_list.append([url, parameters, []])
		results = get_results(query_list[0])
		# mt_query = MultiThreadedQuery(query_function=get_results, query_workers=10, data=query_list)
		# mt_query.start()
		# results = [item for sublist in mt_query.join() for item in sublist]
		if len(results) == 60:
			logger.warning("Results for Text Search exceeded GEO area.  Try a smaller circle.")
		return results

	@staticmethod
	def get_details(place_ids):
		""" Max of 60 records can be returned  """
		url = "https://maps.googleapis.com/maps/api/place/details/json"
		results = []
		single = False
		if not isinstance(place_ids, list):
			place_ids = [place_ids]
			single = True

		for place_id in place_ids:
			parameters = {
				'placeid': place_id
			}
			results.append(get_results(url, parameters, [])[0])

		if len(results) == 60:
			logger.warning("Results for Text Search exceeded GEO area.  Try a smaller circle.")
		return results if not single else results[0]

	@staticmethod
	def get_popular_times_from_search(place_identifier, session):
		def index_get(array, *argv):
			try:

				for index in argv:
					array = array[index]
				return array

			# there is either no info available or no popular times
			# TypeError: rating/rating_n/populartimes wrong of not available
			except (IndexError, TypeError):
				return None

		def get_popularity_for_day(popularity):
			"""

			:param popularity:
			:return:
			"""
			pop_json = [[0 for _ in range(24)] for _ in range(7)]
			wait_json = [[[0, "Closed"] for _ in range(24)] for _ in range(7)]
			popularity = popularity if popularity else []
			for day in popularity:

				day_no, pop_times = day[:2]

				if pop_times is not None:
					for el in pop_times:

						hour, pop, wait_str = el[0], el[1], el[3],

						pop_json[day_no - 1][hour] = pop

						wait_l = [int(s) for s in wait_str.replace("\xa0", " ").split(" ") if s.isdigit()]
						wait_json[day_no - 1][hour] = 0 if len(wait_l) == 0 else wait_l[0]

						# day wrap
						if hour == 23:
							day_no = day_no % 7 + 1

			# {"name" : "monday", "data": [...]} for each weekday as list
			result_dict = {}
			for d in range(7):
				popularity = pop_json[d]
				wait_time = [x if isinstance(x, int) else x[0] for x in wait_json[d]]
				result_dict[list(calendar.day_name)[d]] = list(zip(popularity, wait_time))
			return result_dict

		def get_data(proxy_):
			current_proxy = proxy_.current()
			try:
				return requests.get("https://www.google.com/search", params=params_url, headers=user_agent,
				                    proxies=current_proxy, timeout=5)
			except Exception as e:
				# print(e)
				# logger.warning("Proxy {} failed while retrieving popularity".format(current_proxy))
				proxy_.mark_bad()
				proxy_.next()
				return get_data(proxy_)

		params_url = {
			"tbm": "map",
			"hl": "en",
			"tch": 1,
			"q": place_identifier,
			"pb": "!4m12!1m3!1d4005.9771522653964!2d-122.42072974863942!3d37.8077459796541!2m3!1f0!2f0!3f0!3m2!1i1125!2i976"
			      "!4f13.1!7i20!10b1!12m6!2m3!5m1!6e2!20e3!10b1!16b1!19m3!2m2!1i392!2i106!20m61!2m2!1i203!2i100!3m2!2i4!5b1"
			      "!6m6!1m2!1i86!2i86!1m2!1i408!2i200!7m46!1m3!1e1!2b0!3e3!1m3!1e2!2b1!3e2!1m3!1e2!2b0!3e3!1m3!1e3!2b0!3e3!"
			      "1m3!1e4!2b0!3e3!1m3!1e8!2b0!3e3!1m3!1e3!2b1!3e2!1m3!1e9!2b1!3e2!1m3!1e10!2b0!3e3!1m3!1e10!2b1!3e2!1m3!1e"
			      "10!2b0!3e4!2b1!4b1!9b0!22m6!1sa9fVWea_MsX8adX8j8AE%3A1!2zMWk6Mix0OjExODg3LGU6MSxwOmE5ZlZXZWFfTXNYOGFkWDh"
			      "qOEFFOjE!7e81!12e3!17sa9fVWea_MsX8adX8j8AE%3A564!18e15!24m15!2b1!5m4!2b1!3b1!5b1!6b1!10m1!8e3!17b1!24b1!"
			      "25b1!26b1!30m1!2b1!36b1!26m3!2m2!1i80!2i92!30m28!1m6!1m2!1i0!2i0!2m2!1i458!2i976!1m6!1m2!1i1075!2i0!2m2!"
			      "1i1125!2i976!1m6!1m2!1i0!2i0!2m2!1i1125!2i20!1m6!1m2!1i0!2i956!2m2!1i1125!2i976!37m1!1e81!42b1!47m0!49m1"
			      "!3b1"
		}
		user_agent = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) "
		                            "AppleWebKit/537.36 (KHTML, like Gecko) "
		                            "Chrome/54.0.2840.98 Safari/537.36"}
		proxy = Proxy(session=session)
		resp = get_data(proxy)
		data = resp.text.split('/*""*/')[0]
		# find eof json
		jend = data.rfind("}")
		if jend >= 0:
			data = data[:jend + 1]

		if data:
			jdata = json.loads(data)["d"]
			jdata = json.loads(jdata[4:])

			# get info from result array, has to be adapted if backend api changes
			info = index_get(jdata, 0, 1, 0, 14)

			rating = index_get(info, 4, 7)
			rating_n = index_get(info, 4, 8)

			popular_times = index_get(info, 84, 0)
			popularity_and_wait_times = get_popularity_for_day(popular_times)
			# current_popularity is also not available if popular_times isn't
			current_popularity = index_get(info, 84, 7, 1)

			time_spent = index_get(info, 117, 0)

			is_ascii = lambda s: len(s) == len(s.encode())
			# extract numbers from time string
			if time_spent is not None:
				time_spent = time_spent.replace("\xa0", " ")
				if is_ascii(time_spent):
					time_spent = [[
						              float(s) for s in time_spent.replace("-", " ").replace(",", ".").split(" ")
						              if s.replace('.', '', 1).isdigit()
						              ], time_spent]
				else:
					time_spent = None

			google_place_id = index_get(info, 78)
			timezone = index_get(info, 30)
			additional_tags = set()
			try:
				also_searched = info[99][0][0][1]
				for other_bar in also_searched:
					try:
						if other_bar[1][13]:
							[additional_tags.add(x.replace(' ', '_').lower()) for x in other_bar[1][13]]
					except IndexError:
						pass
			except (IndexError, TypeError):
				pass
			tag_super_list = index_get(info, 76)
			tag_super_list = tag_super_list if tag_super_list else []
			tags = [item for sublist in tag_super_list for item in sublist if is_ascii(item)]
			tags += list(additional_tags)
			return rating, rating_n, popularity_and_wait_times, current_popularity, time_spent, list(set(tags))
		return None, None, None, None, None, list()


def miles_to_meters(miles):
	conversion_factor = 1609.34
	return miles * conversion_factor


def meters_to_miles(meters):
	conversion_factor = 0.621371
	return meters * conversion_factor


def get_circle_centers(lower_coordinates, upper_coordinates, radius):
	"""
    the function covers the area within the bounds with circles
    this is done by calculating the lat/lng distances and the number of circles needed to fill the area
    as these circles only intersect at one point, an additional grid with a (+radius,+radius) offset is used to
    cover the empty spaces
	"""

	meters = miles_to_meters(radius)
	bounds = {
		"lower": {
			"lat": min(float(lower_coordinates[0]), float(upper_coordinates[0])),
			"lng": min(float(lower_coordinates[1]), float(upper_coordinates[1]))
		},
		"upper": {
			"lat": max(float(lower_coordinates[0]), float(upper_coordinates[0])),
			"lng": max(float(lower_coordinates[1]), float(upper_coordinates[1]))
		}
	}

	sw = Point([bounds["lower"]["lat"], bounds["lower"]["lng"]])
	ne = Point([bounds["upper"]["lat"], bounds["upper"]["lng"]])

	# north/east distances
	dist_lat = int(vincenty(Point(sw[0], sw[1]), Point(ne[0], sw[1])).meters)
	dist_lng = int(vincenty(Point(sw[0], sw[1]), Point(sw[0], ne[1])).meters)

	def cover(p_start, n_lat, n_lng, r):
		_coords = []

		for i in range(n_lat):
			for j in range(n_lng):
				v_north = VincentyDistance(meters=i * r * 2)
				v_east = VincentyDistance(meters=j * r * 2)

				_coords.append(v_north.destination(v_east.destination(point=p_start, bearing=90), bearing=0))

		return _coords

	coords = []

	# get circles for base cover
	coords += cover(sw,
	                ceil((dist_lat - meters) / (2 * meters)) + 1,
	                ceil((dist_lng - meters) / (2 * meters)) + 1, meters)

	# update south-west for second cover
	vc_radius = VincentyDistance(meters=meters)
	sw = vc_radius.destination(vc_radius.destination(point=sw, bearing=0), bearing=90)

	# get circles for offset cover
	coords += cover(sw,
	                ceil((dist_lat - 2 * meters) / (2 * meters)) + 1,
	                ceil((dist_lng - 2 * meters) / (2 * meters)) + 1, meters)

	# only return the coordinates
	return [c[:2] for c in coords]


def get_distance_between_points(coordinates1, coordinates2):
	earth_radius = 6373.0

	lat1, lon1 = coordinates1
	lat2, lon2 = coordinates2
	lat1 = radians(lat1)
	lon1 = radians(lon1)
	lat2 = radians(lat2)
	lon2 = radians(lon2)

	dlon = lon2 - lon1
	dlat = lat2 - lat1

	a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
	c = 2 * atan2(sqrt(a), sqrt(1 - a))

	distance = earth_radius * c

	return meters_to_miles(distance)


def get_coordinates(latitude, longitude, bearing, radius):
	earth_radius = 6378.1  # Radius of the Earth
	kilometers = radius / 1000
	lat1 = radians(latitude)  # Current lat point converted to radians
	lon1 = radians(longitude)  # Current long point converted to radians

	lat2 = asin(sin(lat1) * cos(kilometers / earth_radius) +
	            cos(lat1) * sin(kilometers / earth_radius) * cos(bearing))

	lon2 = lon1 + atan2(sin(bearing) * sin(kilometers / earth_radius) * cos(lat1),
	                    cos(kilometers / earth_radius) - sin(lat1) * sin(lat2))

	lat2 = degrees(lat2)
	lon2 = degrees(lon2)

	return lat2, lon2


def get_lower_and_upper_coordinates_of_circle(center_point, radius):
	meters = miles_to_meters(radius)
	north_east = get_coordinates(center_point[0], center_point[1], bearing=0.78539816, radius=meters)  # 45 Degrees
	south_west = get_coordinates(center_point[0], center_point[1], bearing=3.92699082, radius=meters)  # 225 Degrees

	return north_east, south_west


def get_coordinates_for_search(coordinates, large_circle_diameter=10, sub_circle_diameter=2):
	p1, p2 = get_lower_and_upper_coordinates_of_circle(coordinates, radius=large_circle_diameter / 2.0)
	geo = get_circle_centers(p1, p2, radius=sub_circle_diameter / 2.0)

	# http://www.gpsvisualizer.com/map_input
	# print(",".join(["name", "description","latitude", "longitude"]))
	# for x, y in geo:
	# 	print(",".join(["", "", str(x), str(y)]))
	return geo
