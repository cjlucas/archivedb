import os
import sys
import logging, logging.handlers
import traceback
import platform
from archivedb import __author__, __version__

if sys.version_info[0] < 3:
    from StringIO import StringIO #@UnusedImport #@UnresolvedImport
else:
    from io import StringIO #@UnusedImport #@UnresolvedImport

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
    log.setLevel(logging.DEBUG)

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

def log_traceback(exc_info, header=None):
    """log traceback
    Args
    exc_info: tuple returned by sys.exc_info()
    header: info to be logged before the exception
    """

    s = StringIO()
    if header is not None:
        s.write(header + '\n')

    s.write("*** There has been an error, please contact the developer\n\n")

    traceback.print_exception(
                              exc_info[0],
                              exc_info[1],
                              exc_info[2],
                              file=s
                              )
    s.write("\n")
    s.write("*** Copy this message in the email.\n")
    s.write("*** archivedb: {0}\n".format(__version__))
    s.write("*** Python: {0}\n".format(platform.python_version()))
    s.write("*** Platform: {0}\n".format(platform.platform()))
    s.write("*** Contact Info: {0}\n".format(__author__))
    s.write("*** Please attach log file(s) (they can be found here: {0})\n".format(
                                                                    args["log_path"]))
    s.seek(0)
    log.critical(s.read())
    s.close()

if __name__ == "archivedb.logger":
    # create log file
    log = get_logger(args["log_path"])
