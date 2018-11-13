from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import func


class TimestampMixin(object):
	created_at = Column(DateTime, server_default=func.now())
	modified_at = Column(DateTime, server_default=func.now(), onupdate=func.current_timestamp())
