import pyinotify
from pyinotify import IN_CLOSE_WRITE, IN_DELETE, IN_MOVED_FROM, IN_MOVED_TO

class InotifyHandler(pyinotify.ProcessEvent):
	def my_init(self):
		print("OMG")

	def process_IN_CLOSE_WRITE(self, event):
		print("IN_CLOSE_WRITE NOW")
		print(event.path)

	def process_default(self, event):
		print("HERE")
		print(event)

def main():
	masks = IN_CLOSE_WRITE | IN_DELETE | IN_MOVED_FROM | IN_MOVED_TO

	wm = pyinotify.WatchManager()
	notifier = pyinotify.Notifier(wm, default_proc_fun=InotifyHandler())
	#notifier = pyinotify.Notifier(wm)
	wm.add_watch("/mnt/user/stuff/test", pyinotify.ALL_EVENTS, rec=True, auto_add=True)
	
	notifier.loop()


if __name__ == '__main__':
	print("start")
	main()
