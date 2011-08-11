import pymysql
import archivedb.config as config

def create_conn(host, user, passwd, port=3306, db=None):
	db = connect(
		host=host,
		user=user,
		passwd=passwd,
		port=port,
	)

if __name__ == 'archivedb.sql':
	db_host = config.args["db_host"]
	db_port = config.args["db_port"]
	db_user = config.args["db_user"]
	db_pass = config.args["db_pass"]