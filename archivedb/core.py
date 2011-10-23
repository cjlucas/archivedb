import os, sys, re, time, logging

import archivedb.logger
import archivedb.config as config
import archivedb.threads
import archivedb.sql
import archivedb.monitor
from archivedb.common import split_path, join_path

def _database_check():
    """ Perform preliminary database checks
    - Ensures required databases exist, and are created if they don't
    - Ensures required tables exist, and are created if they don't
    - Updates the watch_dir field based on what watch_dirs is set to in the conf
    
    @return: db
    @rtype: L{DatabaseConnection}
    """

    ## perform db checks ##
    db_host = config.args["db_host"]
    db_port = config.args["db_port"]
    db_user = config.args["db_user"]
    db_pass = config.args["db_pass"]
    db_name = config.args["db_name"]

    db = archivedb.sql.DatabaseConnection(db_host, db_user, db_pass, db_name, db_port, "archive")
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
            db.create_table(args["tables"][t])

    # perform enum checks here
    # check if watch dirs in conf file match watch dirs set in database
    # use set() because it doesn't care about order
    conf_watch_dirs = set(args["watch_dirs"])
    db_watch_dirs = set(db.get_enum())
    if conf_watch_dirs == db_watch_dirs:
        log.debug("watch_dirs in conf match watch_dirs in database, no need to update enum")

    else:
        log.debug("watch_dirs in conf don't match to watch_dirs in database, need to update enum")
        log.debug("conf_watch_dirs    = {0}".format(conf_watch_dirs))
        log.debug("db_watch_dirs    = {0}".format(db_watch_dirs))
        db.alter_enum("watch_dir", args["watch_dirs"])

    return(db)

def clean():
    log.debug("start: clean()")
    rows_cleaned = 0
    db = _database_check()

    # remove all rows where watch_dir = '' 
    # (this would occur when a watch_dir has been removed from the enum list)
    query = "DELETE FROM `archive` WHERE watch_dir = ''"
    log.debug("executing: \"{0}\"".format(query))
    rows = db._execute(query)
    log.debug("{0} rows removed from last query.".format(rows))
    rows_cleaned += rows

    # check all files in the database for their existence, remove if not found
    ROW_COUNT = 500
    row_offset = 0
    log.info("purging nonexistent files in the database (may take awhile)")
    while True:
        sql = """SELECT id, watch_dir, path, filename LIMIT {0}, {1}""".format(
                                                                    row_offset,
                                                                    ROW_COUNT)
        log.debug("executing: {0}".format(sql))
        rows = db._query(sql)
        for r in rows:
            full_path = os.path.join(*r[1:])
            if not os.path.exists(full_path):
                log.info("Deleting: {0}".format(full_path))
                #db.delete_file(r[0])
                rows_cleaned += 1

            if len(rows) < ROW_COUNT: break
            else: row_offset += len(rows)


    log.info("total rows cleaned: {0}".format(rows_cleaned))
    log.debug("end: clean()")

def main():
    _database_check()
    ## create threads ##
    threads_dict = archivedb.threads.initialize_child_processes(args["threads"])

    while True:
        time.sleep(2)
        threads_dict = archivedb.threads.keep_child_processes_alive(threads_dict)


if __name__ == 'archivedb.core':
    args = config.args
    log = logging.getLogger(__name__)
