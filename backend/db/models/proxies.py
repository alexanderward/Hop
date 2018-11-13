from sqlalchemy import Boolean
from sqlalchemy import Column, Integer, String
from sqlalchemy import DateTime
from sqlalchemy import func
from db.models.base import Base


class Proxy(Base):
	__tablename__ = 'proxies'

	id = Column(Integer, primary_key=True, autoincrement=True)

	sock4 = Column(String(255), unique=True)
	time_created = Column(DateTime(timezone=True), server_default=func.now())
	time_updated = Column(DateTime(timezone=True), onupdate=func.now())
	count = Column(Integer)
	bad = Column(Boolean, default=False)
