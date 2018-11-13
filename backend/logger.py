import logging, sys
from logging.handlers import RotatingFileHandler


def get_logger(name, level=logging.DEBUG):
	logger = logging.getLogger(name)

	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

	stdout_handler = logging.StreamHandler(stream=sys.stdout)
	stdout_handler.setFormatter(formatter)
	stdout_handler.setLevel(level)

	logger.addHandler(stdout_handler)
	logger.setLevel(level)
	return logger
