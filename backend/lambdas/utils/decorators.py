from functools import wraps


def db_session(fn, *outer_args, **outer_kwargs):
	@wraps(fn)
	def wrapper(*args, **kwargs):
		from db.models.base import Session, Base
		session = Session()
		Base.set_session(session)
		kwargs.setdefault('session', session)
		try:
			results = fn(*args, **kwargs)
		except Exception as e:
			session.rollback()
			raise e
		session.close()
		return results

	return wrapper