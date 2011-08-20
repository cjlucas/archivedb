import os, sys, pymysql, logging
import archivedb.config as config
from archivedb.common import enum_to_list, list_to_enum, md5sum, escape_quotes

class DatabaseConnection:
	def __init__(self, host, user, passwd, database, port, table_name):
		self.host 			= host
		self.user 			= user
		self.passwd			= passwd
		self.database		= database
		self.port			= port
		self.table_name 	= table_name
		self.table_struct	= config.args["table_struct"][table_name]
		
		self.create_conn()

	def table_exists(self, table_name):
		self.c.execute("SHOW TABLES")
		tables = self.c.fetchall()
		tables = [t[0] for t in tables]
		
		if table_name in tables:
			return(True)
		else:
			return(False)
	
	def create_database(self):
		db = pymysql.connect(self.host, self.user, self.passwd, port=self.port)
		c = db.cursor()
		c.execute("CREATE DATABASE IF NOT EXISTS `{0}`".format(self.database))
		log.info("database '{0}' created".format(self.database))
		
	def create_table(self, query):
		self.c.execute(query)
		log.info("table created")
	
	def create_conn(self):
		try:
			self.db = pymysql.connect(
				host=self.host,
				user=self.user,
				passwd=self.passwd,
				db=self.database,
				port=self.port,
			)
			self.c = self.db.cursor()
			log.debug("MySQL connection successful")
		except (pymysql.OperationalError, pymysql.InternalError) as e:
			error_code = e.args[0]
			if error_code == 1049: # mysql server is up, but database doesn't exist
				log.info("database '{0}' not found, creating.".format(self.database))
				self.create_database()
				# call create_conn() again now that database is created
				self.create_conn()
			else:
				log.critical("error when trying to connect to db: {0}".format(e))
				log.critical("closing thread")
				sys.exit(1)
		
	def insert_file(self, watch_dir, path, filename, md5, mtime, size):
		watch_dir, path, filename = (escape_quotes(watch_dir),
									 escape_quotes(path),
									 escape_quotes(filename),
									)
		
		query = """INSERT INTO `{0}`
				(watch_dir, path, filename, md5, mtime, size) VALUES
				('{1}', '{2}', '{3}', '{4}', '{5}', '{6}')""".format(
					self.table_name,
					watch_dir,
					path,
					filename,
					md5,
					mtime,
					size,
				)
				
		log.debug(query)
		self.c.execute(query)
	
	def update_file(self, watch_dir, path, filename, md5, mtime, size):
		watch_dir, path, filename = (escape_quotes(watch_dir),
									 escape_quotes(path),
									 escape_quotes(filename),
									)
		
		query = """UPDATE `{0}` SET `md5` = '{1}', `mtime`= '{2}'
				WHERE watch_dir = '{3}' and path = '{4}'
				and filename = '{5}' and size = '{6}'""".format(
					self.table_name,
					md5,
					mtime,
					watch_dir,
					path,
					filename,
					size,
				)
		log.debug(query)
		rows_changed = self.c.execute(query)
		return(rows_changed)
		
	def move_file(self, src, dest):
		query = """UPDATE `archive` SET watch_dir = '{0}', path = '{1}',
				filename = '{2}' WHERE watch_dir = '{3}' and path = '{4}'
				and filename = '{5}'""".format(
					dest[0], dest[1], dest[2],
					src[0], src[1], src[2],
				)
				
		log.debug(query)
		rows_changed = self.c.execute(query)
		return(rows_changed)
		
	def delete_file(self, id):
		query = """DELETE FROM `archive` WHERE id = '{0}'""".format(id)
		
		log.debug(query)
		rows_changed = self.c.execute(query)
		return(rows_changed)
		
	def move_directory(self, src, dest):
		src_watch_dir	= src[0]
		dest_watch_dir	= dest[0]
		src_path		= src[1]
		dest_path		= dest[1]
		
		query = "SELECT `id`,`path` FROM `archive` WHERE `path` REGEXP '{0}(\/|$)'".format(src_path)
		self.c.execute(query)
		log.debug(query)
		rows_changed = 0
		
		data = self.c.fetchone()
		while data:
			id			= data[0]
			old_path	= data[1]
			new_path	= old_path.replace(src_path, dest_path).strip(os.sep)
			
			query = """UPDATE `archive` SET `watch_dir` = '{0}', path = '{1}'
					WHERE `id` = '{2}'""".format(
						dest_watch_dir,
						new_path,
						id,
					)
			
			log.debug(query)
			rows_changed += self.c.execute(query)
					
			data = self.c.fetchone()
			
		return(rows_changed)

			
	def get_fields(self, watch_dir, path, filename, fields):
		if fields.__class__ == str:
			fields = [fields]
		watch_dir, path, filename = (escape_quotes(watch_dir),
									 escape_quotes(path),
									 escape_quotes(filename),
									)
			
		selections = "{0}".format("`,`".join(fields))
		query = """SELECT `{0}` FROM `{1}` WHERE
		watch_dir = '{2}' and path = '{3}' and filename = '{4}'""".format(
			selections,
			self.table_name,
			watch_dir,
			path,
			filename,
		)
		log.debug(query)
		if self.c.execute(query) == 0:
			return(None)
		else:
			return(self.c.fetchall())
			
		
	def get_enum(self, field_index=1):
		self.c.execute("DESCRIBE `{0}`".format(self.table_name))
		# field type always at index pos 1
		enum_line = self.c.fetchall()[field_index][1]
	
		watch_list = enum_to_list(enum_line)
		return(watch_list)
		
	def alter_enum(self, field_name, watch_dirs):
		query = "ALTER TABLE `{0}` MODIFY `{1}` {2}".format(
			self.table_name,
			field_name,
			list_to_enum(watch_dirs),
		)
		log.debug("query = {0}".format(query))
		self.c.execute(query)


if __name__ == 'archivedb.sql':
	log = logging.getLogger(__name__)
	log.info("{0} imported".format(__name__))