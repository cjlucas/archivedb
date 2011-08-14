import os, sys, logging
import archivedb.config as config
import archivedb.sql as sql
from archivedb.common import md5sum, split_path, escape_quotes

log = logging.getLogger(__name__)
args = config.args

if os.name == 'posix': # linux only
	try:
		import pyinotify
	except ImportError:
		log.warning("module 'pyinotify' not found. disabling inotify monitoring")
		del args["threads"][args["threads"].index("inotify")]

		
def run_oswalk():
	db = sql.DatabaseConnection(args["db_host"],
								args["db_user"],
								args["db_pass"],
								args["db_name"],
								args["db_port"],
								"archive",
								)
	#db.create_conn()
	
	while True:
		for watch_dir in args["watch_dirs"]:
			if not os.path.isdir(watch_dir):
				log.warning("watch_dir '{0}' does not exist, skipping".format(watch_dir))
			else:
				log.info("checking watch_dir '{0}'".format(watch_dir))
			
			for root, dirs, files in os.walk(watch_dir):
				for f in files:
					full_path		= os.path.join(root, f)
					mtime			= os.stat(full_path).st_mtime
					size			= os.stat(full_path).st_size
					
					(watch_dir, path, filename) = split_path(args["watch_dirs"], full_path)
					
					data = db.get_fields(watch_dir, path, filename, "mtime")
					
					if not data: # file is new
						db.insert_file(watch_dir, path, filename, md5sum(full_path), mtime, size)
					else:
						old_mtime = data[0][0]
						#log.debug("old_mtime = {0}".format(old_mtime))
						# check if it has changed
						if old_mtime != mtime:
							rows_changed = db.update_file(watch_dir, path, filename, md5sum(full_path), mtime, size)
							log.debug("rows_changed = {0}".format(rows_changed))
					
		break

		
def run_inotify():
	pass
		
		
		

		
if __name__ == 'archivedb.monitor':
	log.info("{0} imported".format(__name__))