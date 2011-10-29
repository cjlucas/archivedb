import os, logging, logging.handlers
from archivedb.config import args

def get_logger(log_path):
    #LOG_PATH = os.path.join(os.path.expanduser(os.path.split(sys.argv[0])[0]), "logs")
    #LOG_FILE = "archivedb.log"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    LOG_FORMAT = "%(asctime)s :: %(levelname)-8s :: %(filename)s:%(lineno)s :: %(funcName)s :: %(message)s"
    #CONSOLE_FORMAT = "%(asctime)s :: %(levelname)-8s :: %(funcName)s :: %(message)s"
    CONSOLE_FORMAT = "%(asctime)s %(levelname)-8s: %(message)s"

    if not os.path.isdir(os.path.dirname(log_path)):
        os.mkdir(os.path.dirname(log_path))

    log_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    console_formatter = logging.Formatter(CONSOLE_FORMAT, datefmt=DATE_FORMAT)

    log = logging.getLogger("archivedb")
    #log.setLevel(logging.DEBUG)

    # file rotator logging
    rotator = logging.handlers.RotatingFileHandler(
        filename=log_path,
        maxBytes=20000000,
        backupCount=5,
    )
    rotator.setLevel(logging.DEBUG)
    rotator.setFormatter(log_formatter)
    log.addHandler(rotator)

    # console logging
    console = logging.StreamHandler()
    if args["debug"]: console_level = logging.DEBUG
    else: console_level = logging.INFO

    console.setLevel(console_level)
    console.setFormatter(console_formatter)
    log.addHandler(console)

    return(log)

if __name__ == "archivedb.logger":
    # create log file
    log = get_logger(args["log_path"])
