import os
import sys
import logging
import re
import time

import archivedb.config as config
import archivedb.sql as sql
from archivedb.common import md5sum, split_path, escape_quotes
from archivedb.logger import log_traceback

log = logging.getLogger(__name__)
args = config.args

class EmptyClass:
    def __init__(self):
        pass

if os.name == 'posix': # linux only
    try:
        import pyinotify
        from pyinotify import ProcessEvent, IN_CLOSE_WRITE, IN_DELETE, IN_MOVED_FROM, IN_MOVED_TO, IN_ISDIR, IN_CREATE
    except ImportError:
        log.warning("module 'pyinotify' not found. disabling inotify monitoring")
        del args["threads"][args["threads"].index("inotify")]
        # fix for class initialization below
        ProcessEvent = EmptyClass


# disable oswalk thread for testing
#del args["threads"][args["threads"].index("oswalk")]

def is_ignored_file(f):
    for regex in args["ignore_files"]:
        if regex == "":
            continue
        if re.search(regex, f, re.I):
            log.debug("file '{0}' matched '{1}', skipping.".format(f, regex))
            return(True)

    return(False)

def is_ignored_directory(full_path):
    for d in args["ignore_dirs"]:
        if d == "":
            continue
        if d in full_path:
            log.debug("directory '{0}' matched ignore_dir '{1}', skipping".format(full_path, d))
            return(True)

    return(False)

def add_file(db, full_path):
    # skip if symlink or not file
    if not os.path.isfile(full_path) or os.path.islink(full_path):
        return

    mtime = os.stat(full_path).st_mtime
    size = os.stat(full_path).st_size

    (watch_dir, path, filename) = split_path(args["watch_dirs"], full_path)

    data = db.get_fields(watch_dir, path, filename, ["mtime", "size"])

    if not data: # file is new
        log.info("generating checksum for {0} ...".format(filename))
        md5 = md5sum(full_path)
        # md5sum returns None if file was moved/deleted
        if md5:
            log.info("inserting {0} into the database.".format(filename))
            db.insert_file(watch_dir, path, filename, md5, mtime, size)
        else:
            log.warn("file '{0}' was moved/deleted during md5sum creation. not being added to database".format(full_path))
    else:
        old_mtime = data[0][0]
        old_size = data[0][1]
        # check if it has changed
        if int(old_mtime) != int(mtime) or int(old_size) != int(size):
            log.debug("old_mtime = {0}".format(old_mtime))
            log.debug("mtime = {0}".format(mtime))
            log.debug("old_size = {0}".format(old_size))
            log.debug("size = {0}".format(size))
            log.info("generating checksum for {0} ...".format(filename))

            md5 = md5sum(full_path)
            if md5:
                log.info("updating {0} in the database.".format(filename))
                rows_changed = db.update_file(watch_dir, path, filename, md5, mtime, size)
                log.debug("rows_changed = {0}".format(rows_changed))
            else:
                log.warn("file '{0}' was moved/deleted during md5sum creation. not being added to database".format(full_path))


def delete_file(db, full_path):
    (watch_dir, path, filename) = split_path(args["watch_dirs"], full_path)

    # get id
    data = db.get_fields(watch_dir, path, filename, ["id"])

    if data:
        id = data[0][0]
        log.info("removing {0} from the database.".format(filename))
        db.delete_file(id)
    else:
        log.debug("file '{0}' not found in database.".format(full_path))

def scan_dir(db, d):
    if not os.path.isdir(d):
        log.warning("'{0}' does not exist, skipping.".format(d))
        return
    else:
        log.info("scanning directory: '{0}'".format(d))

    for root, dirs, files in os.walk(d):
        for f in files:
            full_path = os.path.join(root, f)
            if not is_ignored_file(f) and not is_ignored_directory(full_path):
                add_file(db, full_path)

def run_oswalk():
    log.info("oswalk thread: start")

    while True:
        db = sql.DatabaseConnection(args["db_host"],
                                    args["db_user"],
                                    args["db_pass"],
                                    args["db_name"],
                                    args["db_port"],
                                    "archive",
                                    )

        try:
            for watch_dir in args["watch_dirs"]:
                scan_dir(db, watch_dir)
        except:
            # catch-all, log any exceptions raised and continue
            log_traceback(sys.exc_info(), "Exception raised in run_oswalk():")

        log.info("oswalk thread: sleeping")
        time.sleep(args["scan_interval"]*3600)

class InotifyHandler(ProcessEvent):
    def my_init(self):
        log.debug("calling my_init()")
        self.db = sql.DatabaseConnection(
                args["db_host"],
                args["db_user"],
                args["db_pass"],
                args["db_name"],
                args["db_port"],
                "archive",
        )
        self.last_moved = None

    def check_last_moved(self, event):
        """
            This is my solution for recognizing when files are moved
            outside of the given watch directories which should be deleted:
            
            When moving a file within the given watch directories, it is
            assumed that immediately after the IN_MOVED_FROM event,
            an IN_MOVED_TO event follows. So if there is no IN_MOVED_TO
            event, it's assumed that the file was moved outside 
            of the watch directories
            
            process_IN_MOVED_FROM sets self.last_moved to the latest
            moved file
            
            This function will check event.src_pathname with self.last_moved,
            if they're equal, then the file is moved within the watch_dirs
            
            This function should be called at the top of ALL process_* functions
            
        """
        del_last_moved = False
        # if var is None, just skip
        if self.last_moved:
            log.debug("self.last_moved = {0}".format(self.last_moved))
            if "IN_MOVED_TO" in event.maskname.split("|"):
                # check if IN_MOVED_TO contains src_pathname attribute
                # (damn them for not just setting src_pathname to None)
                if not hasattr(event, "src_pathname"): del_last_moved = True

                # check if IN_MOVED_TO is the result of the last IN_MOVED_FROM
                log.debug("event.src_pathname = {0}".format(event.src_pathname))
                log.debug("self.last_moved.pathname = {0}".format(
                                                    self.last_moved.pathname))
                if event.src_pathname == self.last_moved.pathname: \
                                            self.last_moved = None
                else: del_last_moved = True
            else:
                # if any event triggers and last_moved is not None, then
                # assume IN_MOVED_TO was never triggered for that file and delete it
                del_last_moved = True

        if del_last_moved:
            log.debug("it is assumed file was moved outside watch_dirs, deleting.")
            log.info("deleting '{0}'".format(self.last_moved.pathname))
            if self.last_moved.dir: self.db.delete_directory(
                                        self.last_moved.pathname)
            else: delete_file(self.db, self.last_moved)
            self.last_moved = None

    def process_IN_CLOSE_WRITE(self, event):
        log.debug(event)
        self.check_last_moved(event)

        full_path = event.pathname
        f = event.name
        if not is_ignored_file(f) and not is_ignored_directory(full_path):
            add_file(self.db, full_path)


    def process_IN_DELETE(self, event):
        log.debug(event)
        self.check_last_moved(event)

        if event.dir: self.db.delete_directory(event.pathname)
        else: delete_file(self.db, event.pathname)

    def process_IN_MOVED_FROM(self, event):
        """
            Used to delete files from database that have been moved out of
            the program's watch_dirs
        """
        log.debug(event)
        self.check_last_moved(event)

        self.last_moved = event

    def process_IN_MOVED_TO(self, event):
        """
            Note about how the IN_MOVED_TO event works:
            when a dir/file is moved, if it's source location is being monitored
            by inotify, there will be an attribute in the event called src_pathname.
            if the dir/file was moved from somewhere outside of pyinotify's watch,
            the src_pathname attribute won't exist.
        """
        log.debug(event)
        self.check_last_moved(event)

        # event.src_pathname will only exist if file was moved from a
        # directory that is being watched
        try:
            src_full_path = event.src_pathname
        except AttributeError:
            src_full_path = None

        dest_full_path = event.pathname
        dest_filename = event.name
        if not is_ignored_file(dest_filename) and not is_ignored_directory(dest_full_path):
            if src_full_path:
                # append / so split_path knows it's input is a directory
                if event.dir:
                    src_full_path += os.sep
                    dest_full_path += os.sep

                src_split_path = split_path(args["watch_dirs"], src_full_path)
                dest_split_path = split_path(args["watch_dirs"], dest_full_path)
                log.debug("src_split_path    = {0}".format(src_split_path))
                log.debug("dest_split_path    = {0}".format(dest_split_path))

                if event.dir:
                    log.info("directory '{0}' has been moved to '{1}', updating.".format(src_full_path,
                                                                                         dest_full_path))
                    rows_changed = self.db.move_directory(src_split_path, dest_split_path)
                else:
                    log.info("{0} has been moved to {1}, updating.".format(src_full_path,
                                                                           dest_full_path))
                    rows_changed = self.db.move_file(src_split_path, dest_split_path)

                log.debug("rows_changed = {0}".format(rows_changed))
                if rows_changed == 0:
                    # since update was unsuccessful, it's presumed that the original
                    # file was not in the database, so we'll just insert it instead
                    log.debug("no rows were changed during UPDATE, inserting {0} into database.".format(dest_full_path))

                    if event.dir: scan_dir(self.db, dest_full_path)
                    else: add_file(self.db, dest_full_path)
            else:
                if event.dir: scan_dir(self.db, dest_full_path)
                else: add_file(self.db, dest_full_path)
        else:
            # since either the file or the path of the file was flagged as ignored,
            # it's not going to be updated in the database. therefor,
            # the src file should just be deleted from the database
            if src_full_path: delete_file(self.db, src_full_path)

def run_inotify():
    # IN_CREATE is only needed for auto_add to work
    masks = IN_CLOSE_WRITE | IN_DELETE | IN_MOVED_FROM | IN_MOVED_TO | IN_ISDIR | IN_CREATE

    wm = pyinotify.WatchManager()
    notifier = pyinotify.Notifier(wm, default_proc_fun=InotifyHandler())

    log.info("initializing inotify monitoring")
    for watch_dir in args["watch_dirs"]:
        log.info("now monitoring: '{0}'".format(watch_dir))
        wm.add_watch(watch_dir, masks, rec=True, auto_add=True)

    log.info("starting inotify monitoring")

    try:
        notifier.loop()
    except:
        # catch-all, log any exceptions raised and continue
        log_traceback(sys.exc_info(), "Exception raised in run_inotify():")
