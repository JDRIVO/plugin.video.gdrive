import xbmc

from resources.lib.network.server import ServerRunner
from resources.lib.library.library_monitor import LibraryMonitor


if __name__ == "__main__":
	monitor = xbmc.Monitor()
	libraryMonitor = LibraryMonitor()
	server = ServerRunner()
	server.start()

	while not monitor.abortRequested():

		if monitor.waitForAbort(0.1):
			break

	server.shutdown()
