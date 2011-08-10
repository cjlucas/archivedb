import os, sys, re
# local
import archivedb.logger

log = archivedb.logger.get_logger("logs", "archivedb.log")

import archivedb.config


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
	
	return (watch_dir, base_path, file_name)

def main():
	args = archivedb.config.get_args()
	p = "/mnt/user/stuff/tv/Curb_Your_Enthusiasm/Curb.Your.Enthusiasm.S08.720p.HDTV.DD5.1.x264-NorTV/curb.mkv"
	print(split_path(args["watch_dirs"], p))


if __name__ == 'archivedb.core':
	log.info("start script")
	main()
	log.info("end script")