from setuptools import setup


version = __import__('archivedb').version

setup(
	name = "archivedb",
	version = version,
	url = 'https://github.com/cjlucas/archivedb',
	author = 'Chris Lucas',
	author_email = 'cjlucas07@gmail.com',
	maintainer = 'Chris Lucas',
	maintainer_email = 'cjlucas07@gmail.com',
	description = 'A program that maintains a checksum database of your media archive',
	license = "MIT",
	packages = ['archivedb', 'archivedb.plugins'],
	scripts = ["./bin/archivedb"],
)