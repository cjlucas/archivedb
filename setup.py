from setuptools import setup
import sys
import platform

version = __import__('archivedb').__version__

if sys.version_info > (3, 0):
	required_pkgs = ["PyMySQL3", ]
elif sys.version_info > (2, 6):
	required_pkgs = ["PyMySQL", ]

# pyinotify support (linux only)
if platform.system() == 'Linux':
	required_pkgs.append("pyinotify")

required_pkgs.append("progressbar")

setup(
	name="archivedb",
	version=version,
	url='https://github.com/cjlucas/archivedb',
	author='Chris Lucas',
	author_email='chris@chrisjlucas.com',
	maintainer='Chris Lucas',
	maintainer_email='chris@chrisjlucas.com',
	description='A program that maintains a checksum database of your media archive',
	license="MIT",
	packages=['archivedb', 'archivedb.plugins'],
	scripts=["./bin/archivedb"],
	install_requires=required_pkgs,
)
