import logging
from .logging_plotting import ColouredFormatter

LogLevel = {'CRITICAL': logging.CRITICAL, 
			'ERROR': logging.ERROR, 
			'WARNING': logging.WARNING, 
			'INFO': logging.INFO, 
			'DEBUG': logging.DEBUG, 
			'NOTSET': logging.NOTSET, 
			}


def get_level(level):
	if level.upper() in LogLevel:
		return LogLevel[level.upper()]
	return logging.INFO

def log_init(logfile='default.log'):
	logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)8s%(name)8s: %(message)s', filename=logfile)
	formatter = ColouredFormatter('%(asctime)s %(levelname)8s%(name)8s: %(message)s')
	ch = logging.StreamHandler()
	ch.setFormatter(formatter)
	return ch

def log_preparation(loglist, logfile='default.log'):
	# ch = log_init(logfile=logfile)
	filehandler = logging.FileHandler(logfile, encoding='utf-8')
	formatter = logging.Formatter('%(asctime)s %(levelname)8s%(name)8s: %(message)s')
	filehandler.setFormatter(formatter)
	for logname, level in loglist:
		logger = logging.getLogger(logname)
		# logger.addHandler(ch)
		logger.addHandler(filehandler)
		logger.setLevel(get_level(level))
