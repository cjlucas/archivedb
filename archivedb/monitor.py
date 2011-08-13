import os, sys, logging

log = logging.getLogger(__name__)
log.info("{0} imported".format(__name__))

if os.name == 'posix': # linux only
	try:
		import pyinotify
	except ImportError:
		log.critical("module 'pyinotify' not found. disabling inotify monitoring")
		# add code to do that (import config module and edit something)