import os, sys, logging, logging.handlers
from archivedb.config import args

def get_logger(log_path):
	#LOG_PATH = os.path.join(os.path.expanduser(os.path.split(sys.argv[0])[0]), "logs")
	#LOG_FILE = "archivedb.log"
	LOG_FORMAT 		= "%(asctime)s :: %(levelname)-8s :: %(filename)s:%(lineno)s :: %(funcName)s :: %(message)s"
	CONSOLE_FORMAT	= "%(asctime)s :: %(levelname)-8s :: %(funcName)s :: %(message)s"
	if not os.path.isdir(os.path.dirname(log_path)):
		os.mkdir(os.path.dirname(log_path))

	log_formatter		= logging.Formatter(LOG_FORMAT)
	console_formatter	= logging.Formatter(CONSOLE_FORMAT)	
	log = logging.getLogger("archivedb")
	log.setLevel(logging.DEBUG)

	rotator = logging.handlers.RotatingFileHandler(
		filename=log_path,
		maxBytes=20000000,
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

if __name__ == "archivedb.logger":
	# create log file
	log = get_logger(args["log_path"])