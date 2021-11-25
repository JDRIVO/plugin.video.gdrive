import sys
import xbmc
import constants
from threading import Thread
from resources.lib import settings, streamer

try:
	pluginHandle = int(sys.argv[1])
	pluginQueries = settings.parse_query(sys.argv[2][1:])
except:
	pluginHandle = None
	pluginQueries = None


def run():
	addon = constants.addon
	pluginName = constants.PLUGIN_NAME
	settings_ = settings.Settings()
	port = settings_.getSettingInt("server_port", 8011)

	server = streamer.MyHTTPServer(("", port), streamer.MyStreamer)
	server.setDetails(pluginHandle, pluginName, pluginName, settings_)
	Thread(target=server.run, daemon=True).start()
	monitor = xbmc.Monitor()

	while not monitor.abortRequested():

		if monitor.waitForAbort(1):
			break

	server.socket.close()
	server.shutdown()
