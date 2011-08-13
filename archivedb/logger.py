import os, sys, logging, logging.handlers

def get_logger(log_path, log_file):
	#LOG_PATH = os.path.join(os.path.expanduser(os.path.split(sys.argv[0])[0]), "logs")
	#LOG_FILE = "archivedb.log"
	LOG_FORMAT 		= "%(asctime)s :: %(levelname)-8s :: %(filename)s:%(lineno)s :: %(funcName)s :: %(message)s"
	CONSOLE_FORMAT	= "%(asctime)s :: %(levelname)-8s :: %(message)s"
	# create logs directory if doesn't exist
	if not os.path.isdir(log_path):
		os.mkdir(log_path)

	log_formatter		= logging.Formatter(LOG_FORMAT)
	console_formatter	= logging.Formatter(CONSOLE_FORMAT)	
	log = logging.getLogger("archivedb")
	log.setLevel(logging.DEBUG)

	rotator = logging.handlers.RotatingFileHandler(
		filename=os.path.join(log_path, log_file),
		maxBytes=5242880,
		backupCount=5,
	)
	console = logging.StreamHandler()
	
	rotator.setLevel(logging.DEBUG)
	rotator.setFormatter(log_formatter)

	console.setLevel(logging.INFO)
	console.setFormatter(console_formatter)
	
	log.addHandler(rotator)
	log.addHandler(console)
	
	return(log)