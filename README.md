ABOUT THIS PROJECT
-----------------
This project was mainly to fill a need I had. I was tired of manually
creating md5sum files for every one of my dvd backups, as well as having to
write shoddy scripts to verify that all my files were intact. This program will
use inotify (linux only) in conjunction with os.walk (any OS) to keep a
constantly updated database of your entire media archive, and also notify the user if
checksum mismatches are found. I also plan to build plugins to extend the
functionality of this backend with movie info from IMDb, and tv info from TVRage.

REQUIREMENTS
------------
- OS
  - Linux: full support
  - OS X: no support for real time file system monitoring, only minor testing
  - Windows: untested

- [Python](http://www.python.org/) 2.6+ or 3.2+ (may work on older versions, but these are what I'm testing against)

- [MySQL](http://www.mysql.com/) 4.1+

- [PyMySQL](http://www.pymysql.org/)
- [python-progressbar](http://code.google.com/p/python-progressbar/) (optional)


INSTALL INSTRUCTIONS
--------------------
- Run ```python setup.py install``` or ```easy_install archivedb```
- Copy example.conf to ~/.archivedb.conf and edit
- Copy bin/archivedb into /usr/bin

TODO
----
- plugin support
  - A few ideas: IMDb, TVRage, Ebook 
- API support
- automatic database backup