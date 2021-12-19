from threading import Thread

import xbmc

import server
import watcher

if __name__ == "__main__":
	Thread(target=server.run, daemon=True).start()
	Thread(target=watcher.run, daemon=True).start()
	monitor = xbmc.Monitor()

	while not monitor.abortRequested():

		if monitor.waitForAbort(1):
			break
