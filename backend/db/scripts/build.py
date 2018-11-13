from db.models.base import engine, Base  # pylint: disable=F0002
from db.models import *


def build():
	print("Building DB")
	Base.metadata.create_all(engine)
	print("Building Complete")


if __name__ == '__main__':
	build()
