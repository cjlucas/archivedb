import sys, pymysql, logging
import archivedb.config as config

#def create_table(watch_dirs, table_name):

#def create_database():

def table_exists(c, table_name):
	c.execute("SHOW TABLES")
	tables = c.fetchall()
	tables = [t[0] for t in tables]
	
	if table_name in tables:
		return(True)
	else:
		return(False)

def create_conn(host, user, passwd, database, port=3306):
	try:
		db = pymysql.connect(
			host=host,
			user=user,
			passwd=passwd,
			port=port,
			db=database,
		)
		
	except (pymysql.OperationalError, pymysql.InternalError) as e:
		error_code = e.args[0]
		if error_code == 1094: # mysql server is up, but database doesn't exist
			log.debug("database '{0}' not found, creating.".format(database))
			# insert database creation code here
			#
			# call create_conn() again now that database is created
			db = create_conn(host, user, passwd, database, port)
		else:
			log.critical("error when trying to connect to db: {0}".format(e))
			log.critical("closing thread")
			sys.exit(1)
			
	return(db)


if __name__ == 'archivedb.sql':
	log = logging.getLogger(__name__)
	log.info("{0} imported".format(__name__))
	
	db_host = config.args["db_host"]
	db_port = config.args["db_port"]
	db_user = config.args["db_user"]
	db_pass = config.args["db_pass"]
	watch_dirs = config.args["watch_dirs"]