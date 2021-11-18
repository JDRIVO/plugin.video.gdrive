import xbmc
import server
import watcher
from threading import Thread

if __name__ == "__main__":
	Thread(target=server.run, daemon=True).start()
	Thread(target=watcher.run, daemon=True).start()
	monitor = xbmc.Monitor()

	while not monitor.abortRequested():

		if monitor.waitForAbort(1):
			break
