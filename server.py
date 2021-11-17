import sys
import xbmc
import threading
import constants
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
	settings_ = settings.Settings(addon)
	userAgent = settings_.getSetting("user_agent")
	port = settings_.getSettingInt("server_port", 8011)

	server = streamer.MyHTTPServer(("", port), streamer.MyStreamer)
	server.setDetails(pluginHandle, pluginName, pluginName, addon, userAgent, settings_)
	thread = threading.Thread(target=server.run)
	thread.start()
	monitor = xbmc.Monitor()

	while not monitor.abortRequested():
		xbmc.sleep(1000)

	server.socket.close()
	server.shutdown()
	thread.join()

# class KodiServer:

	# def __init__(self):
		# addon = constants.addon
		# settings_ = settings.Settings(addon)
		# userAgent = settings_.getSetting("user_agent")
		# PLUGIN_URL = constants.PLUGIN_NAME
		# PLUGIN_NAME = constants.PLUGIN_NAME

		# port = settings_.getSettingInt("server_port", 8011)
		# server = streamer.MyHTTPServer(("", port), streamer.MyStreamer)
		# server.setDetails(PLUGIN_HANDLE, PLUGIN_NAME, PLUGIN_URL, addon, userAgent, settings_)

	# def terminate(self):
		# self.server.socket.close()
		# self.server.shutdown()
