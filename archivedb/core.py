import os, sys, re, time

import archivedb.logger
log = archivedb.logger.get_logger("logs", "archivedb.log")

import archivedb.config as config
import archivedb.threads
import archivedb.sql



def split_path(watch_dirs, p):
	"""
	Parses out a path to a file in a format suitable for
	inserting into and searching the database
	
	Args:
	watch_dirs - list of directories script is watching
	p - full path to file
	
	Returns: tuple (watch_dir, base_path, file_name)
	"""
	
	watch_dir = ""
	base_path = ""
	file_name = ""
	
	# find which watch_dir is being used
	for d in watch_dirs:
		split = re.split("^{0}".format(d), p)
		if split[0] == "":
			watch_dir = d.rstrip(os.sep)
			base_path = split[1].strip(os.sep)
			break
		
	base_path, file_name = os.path.split(base_path)
	
	return (watch_dir, base_path, file_name)

def main():
	threads = ["inotify", "oswalk"]
	threads_dict = archivedb.threads.initialize_child_processes(threads)
	
	while True:
		print("hi")
		time.sleep(2)
		threads_dict = archivedb.threads.keep_child_processes_alive(threads_dict)


if __name__ == 'archivedb.core':
	log.info("start script")
	main()
	log.info("end script")