import os, re, hashlib

def md5sum(f, block_size=2**20):
	md5 = hashlib.md5()
	
	with open(f, "rb") as fp:
		while True:
			data = fp.read(block_size)
			if not data:
				break
			md5.update(data)
	
	return(md5.hexdigest())
	

def split_path(watch_dirs, p):
	"""
	Parses out a path to a file in a format suitable for
	inserting into and searching the database
	
	Args:
	watch_dirs - list of directories script is watching
	p - full path to file
	
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
			base_path = split[1].strip(os.sep)
			break
		
	base_path, file_name = os.path.split(base_path)
	
	return(watch_dir, base_path, file_name)
	
def escape_quotes(s):
	s = s.replace("\'","\\'").replace('\"','\\"')
	return(s)
	

def list_to_enum(watch_dirs):
	out = "enum('{0}')".format("','".join(watch_dirs))
	return(out)

def enum_to_list(enum):
	regex = "\'([^\']*)\'[\,\)]"
	watch_list = re.findall(regex, enum)
	return(watch_list)