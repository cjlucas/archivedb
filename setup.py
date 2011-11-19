from setuptools import setup
import sys
import platform

version = __import__('archivedb').__version__

if sys.version_info > (3, 0): required_pkgs = ["PyMySQL3", ]
elif sys.version_info > (2, 6): required_pkgs = ["PyMySQL", ]

# pyinotify support (linux only)
if platform.system() == 'Linux': required_pkgs.append("pyinotify")

# defaults
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
	classifiers=["Development Status :: 4 - Beta",
				"Intended Audience :: End Users/Desktop",
				"Natural Language :: English",
				"License :: OSI Approved :: MIT License",
				"Natural Language :: English",
				"Operating System :: MacOS",
				"Operating System :: POSIX :: Linux",
				"Programming Language :: Python :: 2",
				"Programming Language :: Python :: 3",
				"Topic :: Database",
				"Topic :: System :: Archiving",
				],
	packages=['archivedb', 'archivedb.plugins'],
	scripts=["./bin/archivedb"],
	install_requires=required_pkgs,
)
