import sys, pymysql, logging
import archivedb.config as config
from archivedb.common import enum_to_list, list_to_enum, md5sum

def table_exists(c, table_name):
	c.execute("SHOW TABLES")
	tables = c.fetchall()
	tables = [t[0] for t in tables]
	
	if table_name in tables:
		return(True)
	else:
		return(False)

def create_database(host, user, passwd, db_name, port=3306):
	db = pymysql.connect(
		host=host,
		user=user,
		passwd=passwd,
		port=port
	)
	c = db.cursor()
	c.execute("CREATE DATABASE IF NOT EXISTS `{0}`".format(db_name))
	log.info("database '{0}' created".format(db_name))
	
def create_table(c, query):
	c.execute(query)
	log.info("table created")

def create_conn(host, user, passwd, database, port=3306):
	try:
		db = pymysql.connect(
			host=host,
			user=user,
			passwd=passwd,
			db=database,
			port=port,
		)
		log.debug("MySQL connection successful")
	except (pymysql.OperationalError, pymysql.InternalError) as e:
		error_code = e.args[0]
		if error_code == 1049: # mysql server is up, but database doesn't exist
			log.info("database '{0}' not found, creating.".format(database))
			create_database(host, user, passwd, database, port)
			# call create_conn() again now that database is created
			db = create_conn(host, user, passwd, database, port)
		else:
			log.critical("error when trying to connect to db: {0}".format(e))
			log.critical("closing thread")
			sys.exit(1)
			
	return(db)
	
def get_enum(c, table_name, field_index=1):
	c.execute("DESCRIBE `{0}`".format(table_name))
	# field type always at index pos 1
	enum_line = c.fetchall()[field_index][1]

	watch_list = enum_to_list(enum_line)
	return(watch_list)
	
def alter_enum(c, table_name, field_name, watch_dirs):
	query = "ALTER TABLE `{0}` MODIFY `{1}` {2}".format(
		table_name,
		field_name,
		list_to_enum(watch_dirs),
	)
	log.debug("query = {0}".format(query))
	c.execute(query)


if __name__ == 'archivedb.sql':
	log = logging.getLogger(__name__)
	log.info("{0} imported".format(__name__))
	
	db_host		= config.args["db_host"]
	db_port		= config.args["db_port"]
	db_user		= config.args["db_user"]
	db_pass		= config.args["db_pass"]
	db_name		= config.args["db_name"]
	watch_dirs	= config.args["watch_dirs"]