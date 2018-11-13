import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


def log(message, message2=None):
	if message and message2:
		logger.info('{}: {}'.format(message, message2))
	else:
		logger.info(message)


def err(message, message2=None):
	if message:
		logger.error(message)
	logger.error(message2)
