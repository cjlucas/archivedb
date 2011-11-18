import os
import sys
import logging
import archivedb.common

_py3 = sys.version_info > (3,)

# The ConfigParser module has been renamed to configparser in Python 3.0
if _py3: import configparser
else: import ConfigParser as configparser #@UnresolvedImport


def get_default_params(section):
    """
    Args:
    section - section of config
    
    Returns: tuple (keys_sorted[section], defaults[section])
    keys_sorted[section] - since dict doesn't preserve order, this is used to keep order when writing
    defaults[section] - dict of default values
    required_keys[section] - list of keys that require user modification
    """

    defaults = {}
    keys_sorted = {}
    required_keys = {}

    defaults["general"] = {
        "watch_dirs"    : "",
        "ignore_dirs"   : "",
        "ignore_files"  : ".*\!ut.* ^\.",
        "scan_interval" : "12",
        "log_path"      :"/tmp/archivedb.log",
        "debug"         : "false",
    }
    defaults["db"] = {
        "host"    : "localhost",
        "port"    : "3306",
        "user"    : "username",
        "pass"    : "password",
    }

    keys_sorted["general"] = [
        "watch_dirs", "ignore_dirs", "ignore_files", "scan_interval",
        "log_path", "debug",
    ]
    keys_sorted["db"] = [
        "host", "port", "user", "pass",
    ]

    required_keys["general"] = [
        "watch_dirs"
    ]
    required_keys["db"] = [
        "user", "pass"
    ]


    return(keys_sorted[section], defaults[section], required_keys[section])

def create_default_config(conf_file):
    """ Create the default config file for archivedb """

    config = configparser.RawConfigParser()


    for section in ["general", "db"]:
        keys_sorted, defaults = get_default_params(section)[0:2]

        config.add_section(section)
        for k in keys_sorted:
            config.set(section, k, defaults[k])

    with open(conf_file, "wb") as configfile:
        config.write(configfile)

def validate_config(conf_file):
    """
    perform sanity checks on conf_file
    
    Args:
    conf_file - path to config file
    
    Returns:
    config - ConfigParser() object
    """

    config = configparser.ConfigParser()
    config.read(conf_file)

    required_sections = ["general", "db"]

    for sec in required_sections:
        keys_sorted, defaults, required_keys = get_default_params(sec)

        # check if sections exist, if not, use defaults
        if not config.has_section(sec):
            log.warning("section '{0}' not found in config, using defaults".format(sec))
            # load section defaults
            config.add_section(sec)
            for k in keys_sorted:
                config.set(sec, k, defaults[k])

        # check if items exist in conf file, if not, add defaults
        # if item is required, print error and halt the program
        # (this dict comprehension syntax is for py2.6 support)
        conf_dict = dict((pair[0], pair[1]) for pair in config.items(sec))
        log.debug("conf_dict = {0}".format(str(conf_dict)))

        for k in keys_sorted:
            if k in conf_dict:
                log.debug("conf_dict[{0}]    = {1}".format(k, conf_dict[k]))
            else:
                log.debug("conf_dict[{0}]    = N/A".format(k))
            log.debug("defaults[{0}]    = {1}".format(k, defaults[k]))

            if k in required_keys:
                if k not in conf_dict:
                        log.fatal("config file missing required key '{0}' (section: {1}) , exiting.".format(k, sec))
                        sys.exit(1)

                # key may exist, but if it's required, it can't be the default value
                elif conf_dict[k] == defaults[k]:
                    log.fatal("config file has required key '{0}' (section: {1}), but default value is not allowed, exiting".format(k, sec))
                    sys.exit(1)
            else:
                if k not in conf_dict:
                    # since we're only looking at non-required keys, we can
                    # use the default value (from get_default_params) if key
                    # isn't specified in conf file
                    log.warning("key: '{0}' not found in config, using default value: '{1}'".format(k, defaults[k]))
                    config.set(sec, k, defaults[k])
                else:
                    config.set(sec, k, conf_dict[k])

    return(config)

def parse_config(config):
    """
    Args:
    config - ConfigParser() object
    
    Returns:
    args - a dict of variables parsed from conf_file
    """

    args = {}

    sections = ["general", "db"]

    for sec in sections:
        for k, v in config.items(sec):
            if v == None:
                continue

            # section specific formatting
            # add db_ prefix to keys
            if sec == "db": args["db_{0}".format(k)] = v
            else: args[k] = v

    return(args)

def format_args(args):
    """
    Perform various type-casting, string splitting on given variables
    
    Args:
    args - dict (from parse_config())
    
    Return:
    args - new and improved
    """

    # convert values to int
    cast_int = ["db_port", "scan_interval"]
    cast_bool = ["debug"]

    for k in cast_int:
        if k in args:
            try:
                args[k] = int(args[k])
            except ValueError:
                log.critical("Given value for key '{0}' is not a valid integer. Check config.".format(k))
                sys.exit(1)

    for k in cast_bool:
        if k in args:
            if args[k].lower() in ["true", "1"]: args[k] = True
            elif args[k].lower() in ["false", "0"]: args[k] = False
            else:
                log.critical("Given value for key '{0}' is not valid. Check config.".format(k))
                sys.exit(1)

    # split values
    split_dict = {
        "watch_dirs"    : "|",
        "ignore_dirs"    : "|",
        "ignore_files"    : " ",
    }

    for k in split_dict:
        if k in args:
            # strip whitespace for every element in list after split()
            args[k] = [e.strip() for e in args[k].split(split_dict[k])]


    return(args)

def get_args():
    args = format_args(parse_config(config))
    return(args)

if __name__ == 'archivedb.config':
    log = logging.getLogger(__name__)

    CONF_FILE = os.path.expanduser("~/.archivedb.conf")
    # create config if none exists
    if not os.path.exists(CONF_FILE):
        #TODO: figure out why python2 cant create a config file
        #log.info("conf file not found, creating one at {0}".format(CONF_FILE))
        #create_default_config(CONF_FILE)
        log.critical("{0} not found, edit example.conf and copy.".format(CONF_FILE))
        sys.exit(1)

    config = validate_config(CONF_FILE)
    args = get_args()

    ## static args here ##
    args["threads"] = ["inotify", "oswalk"]

    args["db_name"] = "archivedb"
    # tables - sql query to create table
    args["tables"] = {
        "archive" : """CREATE TABLE `archivedb`.`archive` (
    `id` mediumint(9) NOT NULL AUTO_INCREMENT,
    `watch_dir` {0} NOT NULL,
    `path` longtext NOT NULL,
    `filename` longtext NOT NULL,
    `md5` varchar(32) NOT NULL,
    `mtime` int(10) NOT NULL,
    `size` varchar(12) NOT NULL,
    PRIMARY KEY (`id`),
    FULLTEXT `path` (path),
    FULLTEXT `filename` (filename)
) ENGINE=`MyISAM` AUTO_INCREMENT=1 DEFAULT CHARACTER SET latin1 COLLATE latin1_swedish_ci ROW_FORMAT=DYNAMIC CHECKSUM=0 DELAY_KEY_WRITE=0;""".format(archivedb.common.list_to_enum(args["watch_dirs"])),
    }
    args["table_struct"] = {
        "archive" : ("id", "watch_dir", "path", "filename", "md5", "mtime", "size"),
    }
