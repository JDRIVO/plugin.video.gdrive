'''
    gdrive XBMC Plugin
    Copyright (C) 2013 dmdsoftware

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

from resources.lib import gdrive 
import sys
import urllib
import cgi
import re

import xbmc, xbmcgui, xbmcplugin, xbmcaddon


        
def log(msg, err=False):
    if err:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg.encode('utf-8'), xbmc.LOGERROR)    
    else:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg.encode('utf-8'), xbmc.LOGDEBUG)    

def parse_query(query):
    queries = cgi.parse_qs(query)
    q = {}
    for key, value in queries.items():
        q[key] = value[0]
    q['mode'] = q.get('mode', 'main')
    return q

def addVideo(url, infolabels, img='', fanart='', total_items=0, 
                   cm=[], cm_replace=False):
    infolabels = decode_dict(infolabels)
    log('adding video: %s - %s' % (infolabels['title'].decode('utf-8','ignore'), url))
    listitem = xbmcgui.ListItem(infolabels['title'], iconImage=img, 
                                thumbnailImage=img)
    listitem.setInfo('video', infolabels)
    listitem.setProperty('IsPlayable', 'true')
    listitem.setProperty('fanart_image', fanart)
    if cm:
        listitem.addContextMenuItems(cm, cm_replace)
    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem, 
                                isFolder=False, totalItems=total_items)


#http://stackoverflow.com/questions/1208916/decoding-html-entities-with-python/1208931#1208931
def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id))
    except:
        return id

def decode(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data).strip()

def decode_dict(data):
    for k, v in data.items():
        if type(v) is str or type(v) is unicode:
            data[k] = decode(v)
    return data



plugin_url = sys.argv[0]
plugin_handle = int(sys.argv[1])
plugin_queries = parse_query(sys.argv[2][1:])

addon = xbmcaddon.Addon(id='plugin.video.gdrive')
#plugin_path = addon.getAddonInfo('path')

username = addon.getSetting('username')
password = addon.getSetting('password')
auth_token = addon.getSetting('auth_token')
user_agent = addon.getSetting('user_agent')
save_auth_token = addon.getSetting('save_auth_token')

# you need to have at least a username&password set or an authorization token
if ((username == '' or password == '') and auth_token == ''):
    xbmcgui.Dialog().ok(addon.getLocalizedString(30000), 'Set the Username and Password in addon settings before running.')
    log('Set the Username and Password in addon settings before running.', True)
    xbmcplugin.endOfDirectory(plugin_handle)


#let's log in
gdrive = gdrive.gdrive(username, password, auth_token, user_agent)

# if we don't have an authorization token set for the plugin, set it with the recent login.
#   auth_token will permit "quicker" login in future executions by reusing the existing login session (less HTTPS calls = quicker video transitions between clips)
if auth_token == '' and save_auth_token:
    addon.setSetting('auth_token', gdrive.writely)  
    

log('plugin google authorization: ' + gdrive.returnHeaders())
log('plugin url: ' + plugin_url)
log('plugin queries: ' + str(plugin_queries))
log('plugin handle: ' + str(plugin_handle))

mode = plugin_queries['mode']

#dump a list of videos available to play
if mode == 'main':
    log(mode)

    videos = gdrive.getVideosHash()

    for title in sorted(videos.iterkeys()):
        addVideo(videos[title]+'|'+gdrive.returnHeaders(),
                             { 'title' : title , 'plot' : title },
                             img='None')
#play a URL that is passed in (presumely requires authorizated session)
elif mode == 'play':
    url = plugin_queries['url']
    log('play url: ' + url)

    item = xbmcgui.ListItem(path=url+'|'+gdrive.returnHeaders())
    log('play url: ' + url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item) 

#play a video given its exact-title
elif mode == 'playvideo':
    title = plugin_queries['title']
    log('play title: ' + title)
    videoURL = gdrive.getVideoLink(title)
    item = xbmcgui.ListItem(path=videoURL+'|'+gdrive.returnHeaders())
    log('play url: ' + videoURL)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item) 

#clear the authorization token
elif mode == 'clearauth':
    addon.setSetting('auth_token', '')
     
xbmcplugin.endOfDirectory(plugin_handle)

