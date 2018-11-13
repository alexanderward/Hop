import requests
from sqlalchemy import func
from sqlalchemy.sql.elements import and_

from db.models.base import Session
from db.utils import SQLAlchemyHelper
from logger import get_logger
from db.models.proxies import Proxy as ProxyModel

logger = get_logger(__file__)


# ITALY,JAPAN,

class Proxy(object):
	url = 'https://hidester.com/proxydata/php/data.php?mykey=data&offset=0&limit=1000&orderBy=latest_check&' \
	      'sortOrder=DESC&country=ALBANIA,ALGERIA,ANDORRA,ANGOLA,ARGENTINA,ARMENIA,AUSTRALIA,AUSTRIA,' \
	      'BANGLADESH,BELARUS,BELGIUM,BOLIVIA,CAMBODIA,BULGARIA,BRAZIL,CAMEROON,CHILE,CANADA,COLOMBIA,' \
	      'CROATIA,CZECH%20REPUBLIC,ECUADOR,EGYPT,ESTONIA,FRANCE,FINLAND,GEORGIA,GERMANY,GREECE,GUATEMALA,' \
	      'HONDURAS,HUNGARY,INDONESIA,ISRAEL,KAZAKHSTAN,LEBANON,MACEDONIA,MALAYSIA,' \
	      'MALDIVES,MALI,MEXICO,MONTENEGRO,MYANMAR,NEPAL,NETHERLANDS,NEW%20ZEALAND,NIGERIA,NORWAY,PARAGUAY,' \
	      'PANAMA,PERU,PHILIPPINES,POLAND,ROMANIA,RUSSIAN%20FEDERATION,SATELLITE%20PROVIDER,SERBIA,SINGAPORE,' \
	      'SOUTH%20AFRICA,SPAIN,SWEDEN,TAIWAN,THAILAND,TRINIDAD%20AND%20TOBAGO,SWITZERLAND,TURKEY,UKRAINE' \
	      ',UNITED%20KINGDOM,UNITED%20STATES,VENEZUELA&port=&type=4&anonymity=7&ping=7&gproxy=2'
	headers = {
		"referer": "https://hidester.com/proxylist/"
	}
	current_proxy = None

	def __init__(self, session):
		self.session = session
		self.next()

	def __retrieve(self):
		logger.info("Retrieving Proxy List")
		resp = requests.get(self.url, headers=self.headers)
		proxy_pool = 0
		for proxy in resp.json():
			sock4 = "%s://%s:%s" % (proxy['type'], proxy['IP'], proxy['PORT'])
			proxy_pool += 1
			proxy_object, created = SQLAlchemyHelper.upsert(ProxyModel,
			                                                sock4=sock4,
			                                                count=0)
		logger.info("Successfully Retrieved {} Proxies".format(proxy_pool))

	def __select_proxy(self):

		queryset = ProxyModel.query.filter(and_(
			(ProxyModel.bad == False),
			(ProxyModel.sock4 != self.current_proxy)
		))
		queryset = queryset.order_by(func.random())  # for PostgreSQL, SQLite
		# else:
		# 	queryset = queryset.order_by(func.rand())  # for MySQL

		proxy = queryset.first()
		if not proxy:
			self.__retrieve()
			return self.__select_proxy()
		else:
			proxy.count += 1
			self.session.add(proxy)
			self.session.commit()
			self.current_proxy = proxy.sock4
			self.session.expunge(proxy)
		return self.current_proxy

	def next(self):
		return {"https": self.__select_proxy()}

	def current(self):
		return {"https": self.current_proxy}

	def mark_bad(self):
		sock4 = self.session.query(ProxyModel).filter(ProxyModel.sock4 == self.current_proxy).first()
		sock4.bad = True
		self.session.add(sock4)
		self.session.commit()


if __name__ == '__main__':
	import pprint

	def test_methods():
		proxy = Proxy(Session)
		pprint.pprint(requests.get('https://api.ipify.org/?format=json', proxies=None).json())
		pprint.pprint(requests.get('https://api.ipify.org/?format=json', proxies=proxy.next()).json())
		pprint.pprint(requests.get('https://api.ipify.org/?format=json', proxies=proxy.next()).json())


	test_methods()
