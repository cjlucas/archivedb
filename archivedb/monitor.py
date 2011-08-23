import os, sys, logging, re, time
import archivedb.config as config
import archivedb.sql as sql
from archivedb.common import md5sum, split_path, escape_quotes

log = logging.getLogger(__name__)
args = config.args

class EmptyClass:
	def __init__(self):
		pass

if os.name == 'posix': # linux only
	try:
		import pyinotify
		from pyinotify import ProcessEvent, IN_CLOSE_WRITE, IN_DELETE, IN_MOVED_FROM, IN_MOVED_TO, IN_ISDIR, IN_CREATE
	except ImportError:
		log.warning("module 'pyinotify' not found. disabling inotify monitoring")
		del args["threads"][args["threads"].index("inotify")]
		# fix for class initialization below
		ProcessEvent = EmptyClass


# disable oswalk thread for testing
#del args["threads"][args["threads"].index("oswalk")]

def is_ignored_file(f):
	for regex in args["ignore_files"]:
		if regex == "":
			continue
		if re.search(regex, f, re.I):
			log.debug("file '{0}' matched '{1}', skipping.".format(f, regex))
			return(True)
	
	return(False)
	
def is_ignored_directory(full_path):
	for d in args["ignore_dirs"]:
		if d == "":
			continue
		if d in full_path:
			log.debug("directory '{0}' matched ignore_dir '{1}', skipping".format(full_path, d))
			return(True)
	
	return(False)
	
def add_file(db, full_path):
	# skip if symlink or not file
	if not os.path.isfile(full_path) or os.path.islink(full_path):
		return
	
	mtime			= os.stat(full_path).st_mtime
	size			= os.stat(full_path).st_size
	
	(watch_dir, path, filename) = split_path(args["watch_dirs"], full_path)
	
	data = db.get_fields(watch_dir, path, filename, ["mtime","size"])
	
	if not data: # file is new
		md5 = md5sum(full_path)
		# md5sum returns None if file was moved/deleted
		if md5:
			db.insert_file(watch_dir, path, filename, md5, mtime, size)
		else:
			log.warn("file '{0}' was moved/deleted during md5sum creation. not being added to database".format(full_path))
	else:
		old_mtime	= data[0][0]
		old_size	= data[0][1]
		log.debug("old_mtime = {0}".format(old_mtime))
		log.debug("mtime = {0}".format(mtime))
		log.debug("old_size = {0}".format(old_size))
		log.debug("size = {0}".format(size))
		# check if it has changed
		if int(old_mtime) != int(mtime) or int(old_size) != int(size):
			md5 = md5sum(full_path)
			if md5:
				rows_changed = db.update_file(watch_dir, path, filename, md5, mtime, size)
				log.debug("rows_changed = {0}".format(rows_changed))
			else:
				log.warn("file '{0}' was moved/deleted during md5sum creation. not being added to database".format(full_path))


def delete_file(db, full_path):
	(watch_dir, path, filename) = split_path(args["watch_dirs"], full_path)

	# get id
	data = db.get_fields(watch_dir, path, filename, ["id"])

	if data:
		id = data[0][0]
		db.delete_file(id)
	else:
		log.debug("file '{0}' not found in database".format(full_path))
		return
	
def scan_dir(db, watch_dir):
	if not os.path.isdir(watch_dir):
		log.warning("watch_dir '{0}' does not exist, skipping".format(watch_dir))
		return
	else:
		log.info("checking watch_dir '{0}'".format(watch_dir))
	
	for root, dirs, files in os.walk(watch_dir):
		for f in files:
			full_path = os.path.join(root, f)
			if not is_ignored_file(f) and not is_ignored_directory(full_path):
				add_file(db, full_path)

def run_oswalk():
	log.info("oswalk thread: start")
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
			scan_dir(db, watch_dir)
					
		# sleep for a day, figure out a way to make this more customizable
		log.info("oswalk thread: sleeping")
		time.sleep(12*3600)
	
class InotifyHandler(ProcessEvent):
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
		self.last_moved_from = ""
	
	def process_IN_CLOSE_WRITE(self, event):
		log.debug(event)
		full_path = event.pathname
		f = event.name
		if not is_ignored_file(f) and not is_ignored_directory(full_path):
			add_file(self.db, full_path)

	
	def process_IN_DELETE(self, event):
		log.debug(event)
		if not event.dir:
			delete_file(self.db, event.pathname)
	
	def process_IN_MOVED_FROM(self, event):
		"""
			Used to delete files from database that have been moved out of
			the program's watch_dirs
		"""
		log.debug(event)
	
	def process_IN_MOVED_TO(self, event):
		"""
			Note about how the IN_MOVED_TO event works:
			when a dir/file is moved, if it's source location is being monitored
			by inotify, there will be an attribute in the event called src_pathname.
			if the dir/file was moved from somewhere outside of pyinotify's watch,
			the src_pathname attribute won't exist.
		"""
		log.debug(event)
		
		dest_full_path	= event.pathname
		dest_filename	= event.name
		if not is_ignored_file(dest_filename) and not is_ignored_directory(dest_full_path):
			# event.src_pathname will only exist if file was moved from a
			# directory that is being watched
			try:
				src_full_path = event.src_pathname
			except AttributeError:
				src_full_path = None
				
			if src_full_path:
				# append / so split_path knows it's input is a directory
				if event.dir:
					src_full_path	+= os.sep
					dest_full_path	+= os.sep
				
				src_split_path	= split_path(args["watch_dirs"], src_full_path)
				dest_split_path	= split_path(args["watch_dirs"], dest_full_path)
				log.debug("src_split_path	= {0}".format(src_split_path))
				log.debug("dest_split_path	= {0}".format(dest_split_path))
				
				if event.dir:
					rows_changed = self.db.move_directory(src_split_path, dest_split_path)
				else:
					rows_changed = self.db.move_file(src_split_path, dest_split_path)
				
				log.debug("rows_changed = {0}".format(rows_changed))
				if rows_changed == 0:
					# since update was unsuccesful, it's presumed that the original
					# file was not in the database, so we'll just insert it instead
					log.debug("no rows were changed, inserting {0} into database instead.".format(dest_full_path))
					add_file(self.db, dest_full_path)
			else:
				if event.dir:
					scan_dir(self.db, dest_full_path)
				else:
					add_file(self.db, dest_full_path)
		else:
			# since either the file or the path of the file was flagged as ignored,
			# it's not going to be updated in the database. therefor,
			# the src file should just be deleted from the database
			if src_full_path:
				delete_file(self.db, src_full_path)
				
	def process_default(self, event):
		print("THIS TRIGGERS")
		
def run_inotify():
	# IN_CREATE is only needed for auto_add to work
	masks = IN_CLOSE_WRITE | IN_DELETE | IN_MOVED_FROM | IN_MOVED_TO | IN_ISDIR | IN_CREATE
	
	wm = pyinotify.WatchManager()
	notifier = pyinotify.Notifier(wm, default_proc_fun=InotifyHandler())
		
	for watch_dir in args["watch_dirs"]:
		log.info("adding '{0}' to inotify monitoring (may take some time)".format(watch_dir))
		wm.add_watch(watch_dir, masks, rec=True, auto_add=True)
		
	log.info("starting inotify monitoring")
	notifier.loop()

		
if __name__ == 'archivedb.monitor':
	log.info("{0} imported".format(__name__))
