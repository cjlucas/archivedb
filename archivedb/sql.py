import os
import sys
import re
import pymysql
import logging
import archivedb.config as config
from archivedb.common import enum_to_list, list_to_enum, escape_quotes, split_path

class DatabaseConnection:
    def __init__(self, host, user, passwd, database, port, table_name):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.database = database
        self.port = port
        self.table_name = table_name
        self.table_struct = config.args["table_struct"][table_name]

        self.create_connection()

    def _check_connection(self):
        reconnect = False
        try:
            if self.db.ping() == False:
                reconnect = True
        except pymysql.err.OperationalError:
            # pymysql.err.OperationalError: (2013, 'Lost connection to MySQL server during query')
            reconnect = True

        if reconnect:
            log.warning("lost connection to database, reconnecting.")
            self.create_connection()

    def table_exists(self, table_name):
        self._check_connection()
        self.c.execute("SHOW TABLES")
        tables = self.c.fetchall()
        tables = [t[0] for t in tables]

        if table_name in tables: return(True)
        else: return(False)

    def create_database(self):
        db = pymysql.connect(self.host, self.user, self.passwd, port=self.port)
        c = db.cursor()
        c.execute("CREATE DATABASE IF NOT EXISTS `{0}`".format(self.database))
        log.info("database '{0}' created".format(self.database))

    def create_table(self, query):
        self._check_connection()
        self._execute(query)
        log.info("table created")

    def create_connection(self):
        try:
            self.db = pymysql.connect(
                host=self.host,
                user=self.user,
                passwd=self.passwd,
                db=self.database,
                port=self.port,
            )
            self.c = self.db.cursor()
            log.debug("mysql connection successful")
        except (pymysql.OperationalError, pymysql.InternalError) as e:
            error_code = e.args[0]
            if error_code == 1049: # mysql server is up, but database doesn't exist
                log.info("database '{0}' not found, creating.".format(self.database))
                self.create_database()
                # call create_conn() again now that database is created
                self.create_conn()
            else:
                log.critical("error when trying to connect to database")
                raise(e)

    def insert_file(self, watch_dir, path, filename, md5, mtime, size):
        self._check_connection()
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

        return(self._execute(query))

    def update_file(self, watch_dir, path, filename, md5, mtime, size):
        self._check_connection()
        watch_dir, path, filename = (escape_quotes(watch_dir),
                                     escape_quotes(path),
                                     escape_quotes(filename),
                                    )

        query = """UPDATE `{0}` SET `md5`='{1}', `mtime`='{2}', `size`='{3}'
                WHERE watch_dir = '{4}' and path = '{5}'
                and filename = '{6}'""".format(
                    self.table_name,
                    md5,
                    mtime,
                    size,
                    watch_dir,
                    path,
                    filename,
                )

        return(self._execute(query))

    def move_file(self, src, dest):
        self._check_connection()
        dest = [
            escape_quotes(dest[0]),
            escape_quotes(dest[1]),
            escape_quotes(dest[2]),
        ]
        src = [
            escape_quotes(src[0]),
            escape_quotes(src[1]),
            escape_quotes(src[2]),
        ]

        query = """UPDATE `archive` SET watch_dir = '{0}', path = '{1}',
                filename = '{2}' WHERE watch_dir = '{3}' and path = '{4}'
                and filename = '{5}'""".format(
                    dest[0], dest[1], dest[2],
                    src[0], src[1], src[2],
                )

        return(self._execute(query))

    def delete_file(self, id):
        # TODO: rename this method 'delete_id', then move monitor.delete_file here
        self._check_connection()
        query = """DELETE FROM `archive` WHERE id = '{0}'""".format(id)

        return(self._execute(query))

    def delete_directory(self, d):
        self._check_connection()
        d = d.rstrip(os.sep) + os.sep # append os.sep so split_path knows its a dir
        watch_dir, path = split_path(config.args["watch_dirs"], d)[0:2]

        # the REGEXP will delete all sub directories as well
        query = """DELETE FROM `archive` WHERE `watch_dir` = '{0}' AND
                `path` REGEXP '{1}(\/|$)'""".format(watch_dir, path)

        return(self._execute(query))

    def move_directory(self, src, dest):
        self._check_connection()
        src_watch_dir = src[0]
        dest_watch_dir = dest[0]
        src_path = src[1]
        dest_path = dest[1]

        query = """SELECT `id`,`path` FROM `archive` WHERE `path` 
                REGEXP '{0}(\/|$)'""".format(re.escape(src_path))
        self.c.execute(query)
        log.debug(query)
        rows_changed = 0
        temp_c = self.db.cursor()

        data = self.c.fetchone()
        while data:
            id = data[0]
            old_path = data[1]
            new_path = old_path.replace(src_path, dest_path).strip(os.sep)

            query = """UPDATE `archive` SET `watch_dir` = '{0}', path = '{1}'
                    WHERE `id` = '{2}'""".format(
                        dest_watch_dir,
                        new_path,
                        id,
                    )

            log.debug(query)
            rows_changed += temp_c.execute(query)

            data = self.c.fetchone()

        return(rows_changed)


    def get_fields(self, watch_dir, path, filename, fields):
        self._check_connection()
        if isinstance(fields, str): fields = [fields]
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
        results = self._query(query)
        if len(results) == 0: return(None)
        else: return(results)


    def get_enum(self, field_index=1):
        self._check_connection()
        self._execute("DESCRIBE `{0}`".format(self.table_name))
        # field type always at index pos 1
        enum_line = self.c.fetchall()[field_index][1]

        watch_list = enum_to_list(enum_line)
        return(watch_list)

    def alter_enum(self, field_name, watch_dirs):
        self._check_connection()
        query = "ALTER TABLE `{0}` MODIFY `{1}` {2}".format(
            self.table_name,
            field_name,
            list_to_enum(watch_dirs),
        )
        self._execute(query)

    def _execute(self, sql):
        """Execute the given query and return the number of rows changed"""
        log.debug("sql = {0}".format(sql))
        rows_changed = self.c.execute(sql)
        return(rows_changed)

    def _query(self, sql):
        """Execute the given query and return all rows"""
        log.debug("sql = {0}".format(sql))
        self.c.execute(sql)
        return(self.c.fetchall())

if __name__ == 'archivedb.sql':
    log = logging.getLogger(__name__)
