import os, sys, time, hashlib

def md5sum(f, block_size=2**20):
	md5 = hashlib.md5()
	with open(f, "rb") as fp:
		while True:
			# check if file has moved during md5 creation
			if not os.path.isfile(f):
				return(None)
			data = fp.read(block_size)
			if not data:
				break
			md5.update(data)
			
	return(md5.hexdigest())

def main():
	f = sys.argv[-1]
	start = time.time()
	print(md5sum(f))
	print("Time Elapsed: {0} seconds".format(time.time() - start))
	
if __name__ == '__main__':
	main()