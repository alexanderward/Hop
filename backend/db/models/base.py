from sqlalchemy import create_engine
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from sqlalchemy_mixins import AllFeaturesMixin

from settings import DB

SQLALCHBASE = declarative_base()


class Base(AllFeaturesMixin, SQLALCHBASE):
	__abstract__ = True

	__table_args__ = {'useexisting': True}

	def __init__(self, **kwargs):
		super(Base, self).__init__(**kwargs)
		# try:
		# 	if persist:
		# 		session.add(self)
		# 		session.commit()
		# except SQLAlchemyError as error:
		# 	session.rollback()
		# 	session.close()
		# 	raise error


def enable_db_logging():
	import logging
	logging.basicConfig()
	logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


def get_engine_path(db):
	return create_engine(
		'%s://%s:%s@%s:%s/%s' % (
			db.get('type'), db.get('user'), db.get('password'), db.get('url'),
			db.get('port'), db.get('name')), poolclass=NullPool)


engine = get_engine_path(DB)
SQLALCHBASE.metadata.bind = engine
Session = scoped_session(sessionmaker())
Session.configure(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
inspector = Inspector.from_engine(engine)
Base.set_session(Session)
