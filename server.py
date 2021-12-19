import sys
from threading import Thread

import xbmc

import constants
from resources.lib import streamer


def run():
	settings = constants.addon
	pluginName = constants.PLUGIN_NAME
	port = settings.getSettingInt("server_port", 8011)
	server = streamer.MyHTTPServer(("", port), streamer.MyStreamer)

	server.setDetails(pluginName, settings)
	Thread(target=server.run, daemon=True).start()
	monitor = xbmc.Monitor()

	while not monitor.abortRequested():

		if monitor.waitForAbort(1):
			break

	server.socket.close()
	server.shutdown()
