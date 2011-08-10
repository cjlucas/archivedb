import os, sys, logging, logging.handlers

print(__name__)

def get_logger(log_path, log_file):
	#LOG_PATH = os.path.join(os.path.expanduser(os.path.split(sys.argv[0])[0]), "logs")
	#LOG_FILE = "archivedb.log"
	LOG_FORMAT = "%(asctime)s :: %(levelname)s :: %(filename)s:%(lineno)s :: %(funcName)s :: %(message)s"
	# create logs directory if doesn't exist
	if not os.path.isdir(log_path):
		os.mkdir(log_path)

	formatter = logging.Formatter(LOG_FORMAT)

	log = logging.getLogger("archivedb")
	log.setLevel(logging.DEBUG)

	rotator = logging.handlers.RotatingFileHandler(
		filename=os.path.join(log_path, log_file),
		maxBytes=5242880,
		backupCount=5,
	)
	console = logging.StreamHandler()
	
	rotator.setLevel(logging.DEBUG)
	rotator.setFormatter(formatter)

	console.setLevel(logging.DEBUG)
	console.setFormatter(formatter)
	
	log.addHandler(rotator)
	log.addHandler(console)
	
	return(log)