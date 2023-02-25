from threading import Thread

import xbmc

import constants
from resources.lib.network import server
from resources.lib.library import monitor

if __name__ == "__main__":
	kodiMonitor = xbmc.Monitor()
	libraryMonitor = monitor.LibraryMonitor()
	server = server.MyHTTPServer(constants.settings)
	Thread(target=server.run, daemon=True).start()

	while not kodiMonitor.abortRequested():

		if kodiMonitor.waitForAbort(1):
			break

	server.shutdown()
