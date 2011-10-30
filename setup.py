from setuptools import setup
import sys

version = __import__('archivedb').version

if sys.version_info > (3, 0):
	REQUIRED = ["PyMySQL3", ]
elif sys.version_info > (2, 6):
	REQUIRED = ["PyMySQL", ]

REQUIRED.append("progressbar")

setup(
	name="archivedb",
	version=version,
	url='https://github.com/cjlucas/archivedb',
	author='Chris Lucas',
	author_email='cjlucas07@gmail.com',
	maintainer='Chris Lucas',
	maintainer_email='cjlucas07@gmail.com',
	description='A program that maintains a checksum database of your media archive',
	license="MIT",
	packages=['archivedb', 'archivedb.plugins'],
	scripts=["./bin/archivedb"],
	install_requires=REQUIRED,
)
