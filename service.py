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
import urllib
import re
import os

# cloudservice - standard XBMC modules
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs

# common routines
from resources.lib import kodi_common

# global variables
import addon_parameters
addon = addon_parameters.addon
cloudservice2 = addon_parameters.cloudservice2
cloudservice1 = addon_parameters.cloudservice1


#*** testing - gdrive
from resources.lib import tvWindow
from resources.lib import gSpreadsheets
from resources.lib import gSheets_api4

##**

# cloudservice - standard modules
#from resources.lib import gdrive
#from resources.lib import gdrive_api2
from resources.lib import cloudservice
from resources.lib import authorization
from resources.lib import folder
from resources.lib import file
from resources.lib import offlinefile
from resources.lib import package
from resources.lib import mediaurl
from resources.lib import crashreport
from resources.lib import gPlayer
from resources.lib import settings
from resources.lib import cache
from resources.lib import TMDB



#global variables
PLUGIN_URL = sys.argv[0]
plugin_handle = None
plugin_queries = None
try:
    plugin_handle = int(sys.argv[1])
    plugin_queries = settings.parse_query(sys.argv[2][1:])
except: pass

addon_dir = xbmc.translatePath( addon.getAddonInfo('path') )


kodi_common.debugger()


# cloudservice - create settings module
settings = settings.settings(addon)

# retrieve settings
user_agent = settings.getSetting('user_agent')
#obsolete, replace, revents audio from streaming
#if user_agent == 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)':
#    addon.setSetting('user_agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.38 Safari/532.0')

instanceName = addon_parameters.PLUGIN_NAME + str(settings.getSetting('account_default', 1))
service = cloudservice2(PLUGIN_URL,addon,instanceName, user_agent, settings)




# must load after all other (becomes blocking)
# streamer
if service is not None and service.settings.streamer:


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
    import urllib, urllib2
    from SocketServer import ThreadingMixIn
    import threading


    try:
        server = streamer.MyHTTPServer(('',  service.settings.streamPort), streamer.myStreamer)
        server.setAccount(service, '')
        if (settings.getSetting('local_db')):
            server.setTVDB(localTVDB)
            server.setTVDB(localMOVIEDB)
        print "ENABLED STREAMER \n\n\n"

        while server.ready:
            server.handle_request()
        server.socket.close()
    except: pass

