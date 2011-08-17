import os, sys, logging, re, time
import archivedb.config as config
import archivedb.sql as sql
from archivedb.common import md5sum, split_path, escape_quotes

log = logging.getLogger(__name__)
args = config.args

if os.name == 'posix': # linux only
	try:
		import pyinotify
		from pyinotify import IN_CLOSE_WRITE, IN_DELETE, IN_MOVED_FROM, IN_MOVED_TO, IN_ISDIR, IN_CREATE
	except ImportError:
		log.warning("module 'pyinotify' not found. disabling inotify monitoring")
		del args["threads"][args["threads"].index("inotify")]


# disable oswalk thread for testing
del args["threads"][args["threads"].index("oswalk")]		

def run_oswalk():
	log.debug("start run_oswalk")
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
				continue
			else:
				log.info("checking watch_dir '{0}'".format(watch_dir))
			
			for root, dirs, files in os.walk(watch_dir):
				for f in files:
					# check if f should be ignored
					skip = False
					for regex in args["ignore_files"]:
						if re.search(regex, f, re.I):
							log.info("file '{0}' matched '{1}', skipping.".format(f, regex))
							skip = True
							break
					
					if skip:
						continue
					full_path		= os.path.join(root, f)
					mtime			= os.stat(full_path).st_mtime
					size			= os.stat(full_path).st_size
					
					(watch_dir, path, filename) = split_path(args["watch_dirs"], full_path)
					
					data = db.get_fields(watch_dir, path, filename, ["mtime","size"])
					
					if not data: # file is new
						db.insert_file(watch_dir, path, filename, md5sum(full_path), mtime, size)
					else:
						old_mtime	= data[0][0]
						old_size	= data[0][1]
						log.debug("old_mtime = {0}".format(old_mtime))
						log.debug("mtime = {0}".format(mtime))
						log.debug("old_size = {0}".format(old_size))
						log.debug("size = {0}".format(size))
						# check if it has changed
						if int(old_mtime) != int(mtime) or int(old_size) != int(size):
							rows_changed = db.update_file(watch_dir, path, filename, md5sum(full_path), mtime, size)
							log.debug("rows_changed = {0}".format(rows_changed))
					
			# sleep for an hour, figure out a way to make this more customizable
			time.sleep(3600)
	
class InotifyHandler(pyinotify.ProcessEvent):
	def my_init(self):
		log.debug("calling my_init()")
		self.db = sql.DatabaseConnection(
				args["db_host"],
				args["db_user"],
				args["db_pass"],
				args["db_name"],
				args["db_port"],
				"archive",
		)
	
	def process_IN_CLOSE_WRITE(self, event):
		log.debug(event)
		full_path = event.pathname


	
	def process_IN_DELETE(self, event):
		log.debug(event)
	
	def process_IN_MOVED_FROM(self, event):
		log.debug(event)
	
	def process_IN_MOVED_TO(self, event):
		log.debug(event)

		
def run_inotify():
	# IN_CREATE is only needed for auto_add to work
	masks = IN_CLOSE_WRITE | IN_DELETE | IN_MOVED_FROM | IN_MOVED_TO | IN_ISDIR | IN_CREATE
	
	wm = pyinotify.WatchManager()
	notifier = pyinotify.Notifier(wm, default_proc_fun=InotifyHandler())
		
	for watch_dir in args["watch_dirs"]:
		log.info("adding '{0}' to inotify monitoring".format(watch_dir))
		wm.add_watch(watch_dir, masks, rec=True, auto_add=True)
		
	notifier.loop()
		
		
		

		
if __name__ == 'archivedb.monitor':
	log.info("{0} imported".format(__name__))
