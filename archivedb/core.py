import os, sys, re, time

import archivedb.logger
log = archivedb.logger.get_logger("logs", "archivedb.log")

import archivedb.config as config
import archivedb.threads
import archivedb.sql
from archivedb.common import split_path

def main():
	args = config.args
	## perform db checks ##
	db_host = config.args["db_host"]
	db_port = config.args["db_port"]
	db_user = config.args["db_user"]
	db_pass = config.args["db_pass"]
	
	blah = split_path(args["watch_dirs"], "/mnt/user/stuff/sabnzbd/complete/The.Colbert.Report.2011.08.11.Gloria.Steinem.720p.HDTV.x264-LMAO/the.colbert.report.2011.08.11.gloria.steinem.720p.hdtv.x264-lmao.mkv")
	print(blah)
	# check if server is up/if archivedb database exists
	db = archivedb.sql.create_conn(db_host, db_user, db_pass, "archivedb", db_port)
	
	# check if tables exist
	# add code to append to tables if plugins are enabled
	tables = ["archive"]
	c = db.cursor()
	for t in tables:
		if archivedb.sql.table_exists(c, t):
			log.info("table '{0}' exists.")
		else:
			log.critical("required table '{0}' doesn't exist, exiting.".format(t))
			print(args["tables"][t])
			sys.exit(1)
	
	## create threads ##
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