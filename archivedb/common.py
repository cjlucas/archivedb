import os, re, hashlib
try:
    from progressbar import ProgressBar, Bar, ETA
    pbar_enabled = True
except ImportError:
    pbar_enabled = False

def md5sum(f, block_size=2 ** 20):
    md5 = hashlib.md5()
    # check if file was moved/deleted before opening
    if not os.path.isfile(f):
        return(None)

    file_size = os.stat(f).st_size

    if pbar_enabled and file_size > 0:
        widgets = [Bar(left="[", right="]", marker="#"), ' ', ETA()]
        # set maxval to the total size of the file, this is 
        # so progressbar can calc the eta/percentage completed of hash check
        bar = ProgressBar(widgets=widgets, maxval=file_size).start()
    else: bar = None

    try:
        with open(f, "rb") as fp:
            bytes_read = 0
            while True:
                # check if file has moved/deleted during md5 creation
                if not os.path.isfile(f):
                    return(None)
                data = fp.read(block_size)
                if not data:
                    break
                md5.update(data)
                bytes_read += len(data)

                if bar is not None: bar.update(bytes_read)

    except IOError:
        # another failsafe in case open() throws error
        return(None)

    if bar is not None: bar.finish()
    return(md5.hexdigest())


def split_path(watch_dirs, p):
    """
    Parses out a path to a file in a format suitable for
    inserting into and searching the database
    
    Args:
    watch_dirs - list of directories script is watching
    p - full path to file (if p is a directory [requires trailing slash], file_name will be "")
    
    Returns: tuple (watch_dir, base_path, file_name)
    """

    watch_dir = ""
    base_path = ""
    file_name = ""

    # find which watch_dir is being used
    for d in watch_dirs:
        split = re.split("^{0}".format(d), p)
        if split[0] == "":
            watch_dir = d.rstrip(os.sep)
            base_path = split[1].lstrip(os.sep)
            break

    base_path, file_name = os.path.split(base_path)

    return(watch_dir, base_path, file_name)

def join_path(watch_dir, path, file_name):
    return(os.path.join(watch_dir, path, file_name))

def escape_quotes(s):
    s = s.replace("\'", "\\'").replace('\"', '\\"')
    return(s)


def list_to_enum(watch_dirs):
    out = "enum('{0}')".format("','".join(watch_dirs))
    return(out)

def enum_to_list(enum):
    regex = "\'([^\']*)\'[\,\)]"
    watch_list = re.findall(regex, enum)
    return(watch_list)
