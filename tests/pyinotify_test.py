import pyinotify
from pyinotify import IN_CLOSE_WRITE, IN_DELETE, IN_MOVED_FROM, IN_MOVED_TO

class InotifyHandler(pyinotify.ProcessEvent):
	def process_default(self):
		print(self)

def main():
	masks = IN_CLOSE_WRITE | IN_DELETE | IN_MOVED_FROM | IN_MOVED_TO

	wm = pyinotify.WatchManager()
	notifier = pyinotify.Notifier(wm, default_proc_fun=InotifyHandler)
	
	wm.add_watch("/mnt/user/stuff/test", masks, rec=True, auto_add=True)
	
	notifier.loop()


if __name__ == '__main__':
	main()