import os, sys, re, time

import archivedb.logger
log = archivedb.logger.get_logger("logs", "archivedb.log")

import archivedb.config as config
import archivedb.threads
import archivedb.sql
import archivedb.monitor
from archivedb.common import split_path

def main():
	args = config.args
	## perform db checks ##
	db_host = config.args["db_host"]
	db_port = config.args["db_port"]
	db_user = config.args["db_user"]
	db_pass = config.args["db_pass"]
	db_name = config.args["db_name"]
	
	db = archivedb.sql.DatabaseConnection(db_host, db_user, db_pass, db_name, db_port, "test")
	#db.create_conn()
	
	
	# check if tables exist
	# add code to append to tables list if plugins are enabled
	tables = ["archive"]
	#c = db.cursor()
	for t in tables:
		if db.table_exists(t):
			log.debug("table '{0}' exists.".format(t))
		else:
			log.info("required table '{0}' doesn't exist, creating.".format(t))
			archivedb.sql.create_table(c, args["tables"][t])
			sys.exit(1)
			
	# perform enum checks here
	# check if watch dirs in conf file match watch dirs set in database
	# use set() because it doesn't care about order
	conf_watch_dirs = set(args["watch_dirs"])
	db_watch_dirs	= set(db.get_enum())
	if conf_watch_dirs == db_watch_dirs:
		log.debug("watch_dirs in conf match watch dirs in database, no need to update enum")

	else:
		log.debug("watch_dirs in conf don't match to watch dirs in database, need to update")
		log.debug("conf_watch_dirs	= {0}".format(conf_watch_dirs))
		log.debug("db_watch_dirs	= {0}".format(db_watch_dirs))
		db.alter_enum("watch_dir", args["watch_dirs"])
		
		
	## create threads ##
	threads_dict = archivedb.threads.initialize_child_processes(args["threads"])
	
	while True:
		time.sleep(2)
		threads_dict = archivedb.threads.keep_child_processes_alive(threads_dict)


if __name__ == 'archivedb.core':
	log.info("start script")
	main()
	log.info("end script")