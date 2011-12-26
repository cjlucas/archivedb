import os
import sys
import re
import pymysql
import logging
import archivedb.config as config
from archivedb.common import enum_to_list, list_to_enum, split_path

#### DEPRECATED ################################################################
# def escape_string(s):
#    """hack until I properly implement query formatting"""
#    return(pymysql.converters.escape_string(s).strip("'"))
################################################################################

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
        # CREATE TABLE query is specified in archivedb.config (may be utilized
        # by plugins later)
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
        self._check_connection()
################################################################################
#        watch_dir, path, filename = (escape_string(watch_dir),
#                                     escape_string(path),
#                                     escape_string(filename),
#                                    )
# 
#         query = """INSERT INTO `{0}`
#                (watch_dir, path, filename, md5, mtime, size) VALUES
#                ('{1}', '{2}', '{3}', '{4}', '{5}', '{6}')""".format(
#                    self.table_name,
#                    watch_dir,
#                    path,
#                    filename,
#                    md5,
#                    mtime,
#                    size,
#                )
################################################################################

        query = """INSERT INTO `{0}` (watch_dir, path, filename, md5, mtime, size) 
        VALUES %s""".format(self.table_name)

        args = (
                (watch_dir,
                path,
                filename,
                md5,
                mtime,
                size),
        )

        self._execute(query, args)

    def update_file(self, watch_dir, path, filename, md5, mtime, size):
        self._check_connection()

        ########################################################################
        # watch_dir, path, filename = (escape_string(watch_dir),
        #                             escape_string(path),
        #                             escape_string(filename),
        #                            )
        # 
        # query = """UPDATE `{0}` SET `md5`='{1}', `mtime`='{2}', `size`='{3}'
        #        WHERE watch_dir = '{4}' and path = '{5}'
        #        and filename = '{6}'""".format(
        #            self.table_name,
        #            md5,
        #            mtime,
        #            size,
        #            watch_dir,
        #            path,
        #            filename,
        #        )
        ########################################################################

        query = """UPDATE `{0}` SET `md5` = %s, `mtime` = %s, `size` = %s
                WHERE `watch_dir` = %s and `path` = %s 
                and `filename` = %s""".format(self.table_name)

        args = (md5,
                mtime,
                size,
                watch_dir,
                path,
                filename)

        return(self._execute(query, args))

    def move_file(self, src, dest):
        self._check_connection()

        ########################################################################
        #        dest = [
        #            escape_string(dest[0]),
        #            escape_string(dest[1]),
        #            escape_string(dest[2]),
        #        ]
        #        src = [
        #            escape_string(src[0]),
        #            escape_string(src[1]),
        #            escape_string(src[2]),
        #        ]
        # 
        #        query = """UPDATE `archive` SET watch_dir = '{0}', path = '{1}',
        #                filename = '{2}' WHERE watch_dir = '{3}' and path = '{4}'
        #                and filename = '{5}'""".format(
        #                    dest[0], dest[1], dest[2],
        #                    src[0], src[1], src[2],
        #                )
        ########################################################################

        query = """UPDATE `{0}` SET `watch_dir` = %s, path = %s,
                 filename = %s WHERE `watch_dir` = %s and `path` = %s 
                 and filename = %s""".format(self.table_name)

        args = (dest[0], dest[1], dest[2],
                src[0], src[1], src[2])

        return(self._execute(query, args))

    def delete_file(self, full_path):
        (watch_dir, path, filename) = split_path(config.args["watch_dirs"], full_path)

        # get id
        data = self.get_fields(watch_dir, path, filename, ["id"])

        if data:
            id = data[0][0]
            log.info("removing {0} from the database.".format(filename))
            self.delete_id(id)
        else:
            log.debug("file '{0}' not found in database.".format(full_path))

    def delete_id(self, id):
        self._check_connection()
        query = """DELETE FROM `archive` WHERE id = %s"""
        args = id
        return(self._execute(query, args))

    def delete_directory(self, d):
        self._check_connection()
        d = d.rstrip(os.sep) + os.sep # append os.sep so split_path knows its a dir
        watch_dir, path = split_path(config.args["watch_dirs"], d)[0:2]

        ########################################################################
        # query = """DELETE FROM `archive` WHERE `watch_dir` = '{0}' AND
        #        `path` REGEXP '{1}(\/|$)'""".format(watch_dir, path)
        ########################################################################

        # the REGEXP will delete all sub directories as well
        query = """DELETE FROM `{0}` WHERE `watch_dir` = %s and
                `path` REGEXP %s""".format(self.table_name)

        args = (watch_dir,
                re.escape(path) + "(\/|$)")

        return(self._execute(query, args))

    def move_directory(self, src, dest):
        self._check_connection()
        src_watch_dir = src[0]
        dest_watch_dir = dest[0]
        src_path = src[1]
        dest_path = dest[1]

        ########################################################################
        # query = """SELECT `id`,`path` FROM `archive` WHERE `path` 
        #        REGEXP '{0}(\/|$)'""".format(re.escape(src_path))
        ########################################################################

        query = """SELECT `id`, `path` FROM `{0}` WHERE `path` 
                REGEXP %s""".format(self.table_name)

        args = re.escape(src_path) + "(\/|$)"

        self._execute(query, args)
        rows_changed = 0
        temp_c = self.db.cursor()
        data = self.c.fetchone()
        while data:
            id = data[0]
            old_path = data[1]
            # because subdirectories have to be moved too, we're just going
            # to replace src_path with dest_path
            # ex: src_path = Some.Movie dest_path = Renamed.Movie
            #     Some.Movie/CD1 will be renamed to Renamed.Movie/CD1
            #     without the subdirectory being affected
            new_path = old_path.replace(src_path, dest_path).strip(os.sep)

            ####################################################################
            # query = """UPDATE `archive` SET `watch_dir` = '{0}', path = '{1}'
            #        WHERE `id` = '{2}'""".format(
            #            escape_string(dest_watch_dir),
            #            escape_string(new_path),
            #            id,
            #        )
            ####################################################################

            query = """UPDATE `{0}` SET `watch_dir` = %s, `path` = %s 
                    WHERE `id` = %s""".format(self.table_name)

            args = (dest_watch_dir,
                    new_path,
                    id)

            rows_changed += self._execute(query, args, c=temp_c)
            data = self.c.fetchone()

        return(rows_changed)


    def get_fields(self, watch_dir, path, filename, fields):
        self._check_connection()
        if isinstance(fields, str): fields = [fields]
        ########################################################################
        # watch_dir, path, filename = (escape_string(watch_dir),
        #                             escape_string(path),
        #                             escape_string(filename),
        #                             )
        ########################################################################

        fields = "{0}".format("`,`".join(fields))
        ########################################################################
        # query = """SELECT `{0}` FROM `{1}` WHERE
        # watch_dir = '{2}' and path = '{3}' and filename = '{4}'""".format(
        #    selections,
        #    self.table_name,
        #    watch_dir,
        #    path,
        #    filename,
        # )
        ########################################################################
        query = """SELECT `{0}` FROM `{1}` WHERE watch_dir = %s and path = %s
                and filename = %s""".format(fields, self.table_name)

        args = (watch_dir, path, filename)

        if self._execute(query, args) == 0: return(None)
        else: return(self.c.fetchall())


    def get_enum(self, field_index=1):
        self._check_connection()
        self._execute("DESCRIBE `{0}`".format(self.table_name))
        # enum at index pos 1
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

    def _execute(self, query, args=None, c=None):
        """Returns number of rows affected"""
        if c == None: c = self.c
        log.debug("query = {0}".format(query))
        log.debug("args = {0}".format(args))

        rows_affected = c.execute(query, args)
        log.debug("rows_affected = {0}".format(rows_affected))
        return(rows_affected)

    def _query(self, query, args=None, c=None):
        """Returns all rows from given query"""
        self._execute(query, args)
        return(self.c.fetchall())

if __name__ == 'archivedb.sql':
    log = logging.getLogger(__name__)
