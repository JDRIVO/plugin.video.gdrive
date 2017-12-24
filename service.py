'''
    CloudService XBMC Plugin
    Copyright (C) 2013-2014 ddurdle

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''



# cloudservice - required python modules
import sys
import re

# cloudservice - standard XBMC modules
import xbmc


KODI = True

if KODI:
    # cloudservice - standard XBMC modules
#            import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
    # global variables
    import constants
    addon = constants.addon

    PLUGIN_URL = constants.PLUGIN_NAME

PLUGIN_NAME = constants.PLUGIN_NAME

cloudservice2 = constants.cloudservice2




# cloudservice - standard modules
from resources.lib import settings
#if constants.CONST.tmdb:
#    from resources.lib import TMDB



#global variables
PLUGIN_URL = sys.argv[0]
plugin_handle = None
plugin_queries = None
try:
    plugin_handle = int(sys.argv[1])
    plugin_queries = settings.parse_query(sys.argv[2][1:])
except:
    plugin_handle = None
    plugin_queries = None


addon_dir = xbmc.translatePath( addon.getAddonInfo('path') )



# cloudservice - create settings module
settings = settings.settings(addon)

# retrieve settings
user_agent = settings.getSetting('user_agent')
#obsolete, replace, revents audio from streaming
#if user_agent == 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)':
#    addon.setSetting('user_agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.38 Safari/532.0')

#instanceName = PLUGIN_NAME + str(settings.getSetting('account_default', 1))
#service = cloudservice2(plugin_handle,PLUGIN_URL,addon,instanceName, user_agent, settings)

if 0:
    from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
    from resources.lib import enroll_proxy

    import threading

    try:
        server = enroll_proxy.MyHTTPServer(('',  9978), enroll_proxy.enrollBrowser)


        doLoop = True

        #except:
        #    doLoop = False

        monitor = xbmc.Monitor()

        thread = threading.Thread(None, server.run)
        thread.start()

        while not monitor.abortRequested() and doLoop:
            if monitor.waitForAbort(10):
                break
        server.shutdown()
        thread.join()

    except:
        pass


# must load after all other (becomes blocking)
# streamer


localTVDB = {}
localMOVIEDB = {}
#load data structure containing TV and Movies from KODI
if (settings.getSetting('local_db')):

    result = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {  "sort": {"method":"lastplayed"}, "filter": {"field": "title", "operator": "isnot", "value":"1"}, "properties": [  "file"]}, "id": "1"}')
    for match in re.finditer('"episodeid":(\d+)\,"file"\:"[^\"]+"', result):#, re.S):
        localTVDB[match.group(2)] = match.group(1)
    result = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {  "sort": {"method":"lastplayed"}, "filter": {"field": "title", "operator": "isnot", "value":"1"}, "properties": [  "file"]}, "id": "1"}')
    for match in re.finditer('"file":"[^\"]+","label":"[^\"]+","movieid":(\d+)', result):#, re.S):
        localMOVIEDB[match.group(1)] = match.group(2)



from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from resources.lib import streamer
from SocketServer import ThreadingMixIn
import threading


port = int(settings.getSettingInt('stream_port', 8011))
server = streamer.MyHTTPServer(('',  port), streamer.myStreamer)
server.setDetails(plugin_handle,PLUGIN_NAME,PLUGIN_URL,addon,user_agent, settings)
#server.setAccount(service, '')
if (settings.getSetting('local_db')):
    server.setTVDB(localTVDB)
    server.setTVDB(localMOVIEDB)

doLoop = True

#except:
#    doLoop = False

monitor = xbmc.Monitor()

thread = threading.Thread(None, server.run)
thread.start()

while not monitor.abortRequested() and doLoop:
    if monitor.waitForAbort(10):
        break
server.shutdown()
thread.join()

#while not monitor.abortRequested() and doLoop and server.ready:
#    server.handle_request()
#server.socket.close()
