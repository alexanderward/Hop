from db.models.base import engine, Session
import sqlalchemy as sqla  # pylint: disable=E0401
import sqlalchemy.ext.declarative as sqld  # pylint: disable=E0401


def destroy():
	print("Destroying DB")
	sqla_base = sqld.declarative_base()
	sqla_base.metadata.bind = engine
	sqla_base.metadata.drop_all()

	# sql = sqla.text("SET FOREIGN_KEY_CHECKS = 0")
	session = Session()
	# session.execute(sql)
	for table in engine.table_names():
		sql = sqla.text("DROP TABLE IF EXISTS {} CASCADE ".format(table))
		print(sql)
		session.execute(sql)
	print("Destroying DB Complete")


if __name__ == '__main__':
	destroy()
