import hashlib

def md5sum(f, block_size=2**20):
	md5 = hashlib.md5()
	
	with open(f, "rb") as fp:
		while True:
			data = fp.read(block_size)
			if not data:
				break
			md5.update(data)
	
	return(md5.hexdigest())