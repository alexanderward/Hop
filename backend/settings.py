import os

APP = 'hop'
STACK = os.environ.get('stack', 'dev')
assert STACK

# Pagination
PER_PAGE = 5
DEFAULT_PAGE = 1

DB = {
	"user": "hop",
	"password": "alex3412",
	"name": "hop",
	"type": "postgresql+psycopg2",
	"port": "6432",
	"url": "pgbouncer-058198b5c904e704.elb.us-east-1.amazonaws.com"
}  # PGBOUNCER

GOOGLE_API_KEY = "AIzaSyDS9nquKc8FlfpthfPIyMFdRu8laL2Zy80"

LARGE_CIRCLE_DIAMETER = 15
SUB_CIRCLE_DIAMETER = .5
