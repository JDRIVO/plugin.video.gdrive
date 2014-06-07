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

# global variables
PLUGIN_NAME = 'plugin.video.gdrive'
PLUGIN_URL = 'plugin://'+PLUGIN_NAME+'/'
ADDON = xbmcaddon.Addon(id=PLUGIN_NAME)

#helper methods
def log(msg, err=False):
    if err:
        xbmc.log(ADDON.getAddonInfo('name') + ': ' + msg, xbmc.LOGERROR)
    else:
        xbmc.log(ADDON.getAddonInfo('name') + ': ' + msg, xbmc.LOGDEBUG)

def parse_query(query):
    queries = cgi.parse_qs(query)
    q = {}
    for key, value in queries.items():
        q[key] = value[0]
    q['mode'] = q.get('mode', 'main')
    return q

def addVideo(url, infolabels, label, img='', fanart='', total_items=0,
                   cm=[], cm_replace=False):
    infolabels = decode_dict(infolabels)
    log('adding video: %s - %s' % (infolabels['title'], url))
    listitem = xbmcgui.ListItem(label, iconImage=img,
                                thumbnailImage=img)
    listitem.setInfo('video', infolabels)
    listitem.setProperty('IsPlayable', 'true')
    listitem.setProperty('fanart_image', fanart)
    if cm:
        listitem.addContextMenuItems(cm, cm_replace)
    if not xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
                                isFolder=False, totalItems=total_items):
        return False
    return True

def addDirectory(url, title, img='', fanart='', total_items=0):
    log('adding dir: %s - %s' % (title, url))
    listitem = xbmcgui.ListItem(decode(title), iconImage=img, thumbnailImage=img)
    if not fanart:
        fanart = ADDON.getAddonInfo('path') + '/fanart.jpg'
    listitem.setProperty('fanart_image', fanart)
    # allow play controls on folders
    listitem.setProperty('IsPlayable', 'true')
    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
                                isFolder=True, totalItems=total_items)

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



#global variables
plugin_url = sys.argv[0]
plugin_handle = int(sys.argv[1])
plugin_queries = parse_query(sys.argv[2][1:])


try:

    remote_debugger = ADDON.getSetting('remote_debugger')
    remote_debugger_host = ADDON.getSetting('remote_debugger_host')

    # append pydev remote debugger
    if remote_debugger == 'true':
        # Make pydev debugger works for auto reload.
        # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
        import pysrc.pydevd as pydevd
        # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
        pydevd.settrace(remote_debugger_host, stdoutToServer=True, stderrToServer=True)
except ImportError:
    log(ADDON.getLocalizedString(30016), True)
    sys.exit(1)
except :
    pass


# retrieve settings
username = ADDON.getSetting('username')
password = ADDON.getSetting('password')
user_agent = ADDON.getSetting('user_agent')
save_auth_token = ADDON.getSetting('save_auth_token')
promptQuality = ADDON.getSetting('prompt_quality')

if promptQuality == 'true':
    promptQuality = True
else:
    promptQuality = False

# hidden parameters which may not even be defined
try:
    auth_writely = ADDON.getSetting('auth_writely')
    auth_wise = ADDON.getSetting('auth_wise')
    useWRITELY = ADDON.getSetting('force_writely')
    if useWRITELY == 'true':
        useWRITELY = True
    else:
        useWRITELY = False
except :
    auth_writely = ''
    auth_wise = ''
    useWRITELY = True



mode = plugin_queries['mode']

# allow for playback of public videos without authentication
if (mode == 'streamurl'):
  authenticate = False
else:
  authenticate = True

# you need to have at least a username&password set or an authorization token
if ((username == '' or password == '') and (auth_writely == '' and auth_wise == '') and (authenticate == True)):
    xbmcgui.Dialog().ok(ADDON.getLocalizedString(30000), ADDON.getLocalizedString(30015))
    log(ADDON.getLocalizedString(30015), True)
    xbmcplugin.endOfDirectory(plugin_handle)


#let's log in
gdrive = gdrive.gdrive(username, password, auth_writely, auth_wise, user_agent, authenticate, useWRITELY)

# if we don't have an authorization token set for the plugin, set it with the recent login.
#   auth_token will permit "quicker" login in future executions by reusing the existing login session (less HTTPS calls = quicker video transitions between clips)
if auth_writely == '' and save_auth_token == 'true':
    ADDON.setSetting('auth_writely', gdrive.writely)
    ADDON.setSetting('auth_wise', gdrive.wise)


log('plugin url: ' + plugin_url)
log('plugin queries: ' + str(plugin_queries))
log('plugin handle: ' + str(plugin_handle))

# make mode case-insensitive
mode = mode.lower()

#dump a list of videos available to play
if mode == 'main' or mode == 'index':
    cacheType = int(ADDON.getSetting('playback_type'))

    try:
      folder = plugin_queries['folder']
    except:
      folder = False

    if mode == 'main':
      addDirectory(PLUGIN_URL+'?mode=index&folder=','<< '+ADDON.getLocalizedString(30018)+' >>')
      folder = 'root'


    videos = gdrive.getVideosList(cacheType, folder)


    for title in sorted(videos.iterkeys()):
        if not videos[title]['mediaType'] == gdrive.MEDIA_TYPE_FOLDER  and (videos[title]['mediaType'] == gdrive.MEDIA_TYPE_MUSIC or (videos[title]['mediaType'] == gdrive.MEDIA_TYPE_VIDEO and(cacheType == gdrive.CACHE_TYPE_MEMORY or cacheType == gdrive.CACHE_TYPE_DISK  or (cacheType == gdrive.CACHE_TYPE_STREAM and not promptQuality)))):
            addVideo(videos[title]['url'],
                             { 'title' : title , 'plot' : title }, title,
                             img=videos[title]['thumbnail'])
        else:
            addDirectory(videos[title]['url'],title, img=videos[title]['thumbnail'])


#play a URL that is passed in (presumably requires authorizated session)
elif mode == 'play':
    url = plugin_queries['url']

    item = xbmcgui.ListItem(path=url+'|'+gdrive.getHeadersEncoded(gdrive.useWRITELY))
    log('play url: ' + url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

#play a video given its exact-title
elif mode == 'playvideo':
    title = plugin_queries['title']
    cacheType = int(ADDON.getSetting('playback_type'))

    videoURL = gdrive.getVideoLink(title,cacheType)

    #effective 2014/02, video stream calls require a wise token instead of writely token
    videoURL = videoURL + '|' + gdrive.getHeadersEncoded(gdrive.useWRITELY)

    item = xbmcgui.ListItem(path=videoURL)
    log('play url: ' + videoURL)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

#force memory-cache - play a video given its exact-title
elif mode == 'memorycachevideo':
    title = plugin_queries['title']
    videoURL = gdrive.getVideoLink(title)

    #effective 2014/02, video stream calls require a wise token instead of writely token
    videoURL = videoURL + '|' + gdrive.getHeadersEncoded(gdrive.useWRITELY)

    item = xbmcgui.ListItem(path=videoURL)
    log('play url: ' + videoURL)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


#force stream - play a video given its exact-title
elif mode == 'streamvideo':
    try:
      title = plugin_queries['title']
    except:
      title = 0

    try:
      pquality = int(ADDON.getSetting('preferred_quality'))
      pformat = int(ADDON.getSetting('preferred_format'))
      acodec = int(ADDON.getSetting('avoid_codec'))
    except :
      pquality=-1
      pformat=-1
      acodec=-1

    # result will be a list of streams
    singlePlayback=''
    videos = gdrive.getVideoLink(title, gdrive.CACHE_TYPE_STREAM,pquality,pformat,acodec)

    for label in sorted(videos.iterkeys()):
        # if invoked as a directory, user is expecting a list of qualities to select from, add each video stream playback
        addVideo(videos[label]+'|'+gdrive.getHeadersEncoded(gdrive.useWRITELY),
                             { 'title' : title , 'plot' : title },label,
                             img='None')
        if singlePlayback == '':
            singlePlayback = label

    # if invoked in .strm or as a direct-video (don't prompt for quality)
    item = xbmcgui.ListItem(path=videos[singlePlayback]+ '|' + gdrive.getHeadersEncoded(gdrive.useWRITELY))
    item.setInfo( type="Video", infoLabels={ "Title": title , "Plot" : title } )
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


#force stream - play a video given its exact-title
elif mode == 'streamurl':
    try:
      url = plugin_queries['url']
    except:
      url = 0

    # check for promptQuality override
    try:
      pquality = int(ADDON.getSetting('preferred_quality'))
      pformat = int(ADDON.getSetting('preferred_format'))
      acodec = int(ADDON.getSetting('avoid_codec'))
    except :
      pquality=-1
      pformat=-1
      acodec=-1

    singlePlayback=''
    videos = gdrive.getVideoStream(pquality=pquality,pformat=pformat,acodec=acodec, url=url)

    for label in sorted(videos.iterkeys()):
          addVideo(videos[label]+'|'+gdrive.getHeadersEncoded(gdrive.useWRITELY),
                             { 'title' : label , 'plot' : label },label,
                             img='None')
          if singlePlayback == '':
            singlePlayback = label

    # if invoked in .strm or as a direct-video (don't prompt for quality)
    item = xbmcgui.ListItem(path=videos[singlePlayback]+ '|' + gdrive.getHeadersEncoded(gdrive.useWRITELY))
    item.setInfo( type="Video", infoLabels={ "Title": label , "Plot" : label } )
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


#elif mode == 'streamurl':
#    url = plugin_queries['url']

#    videoURL = gdrive.getPublicStream(url)
#    item = xbmcgui.ListItem(path=videoURL)
#    log('play url: ' + videoURL)
#    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

#clear the authorization token
elif mode == 'clearauth':
    ADDON.setSetting('auth_writely', '')
    ADDON.setSetting('auth_wise', '')

# if we don't have an authorization token set for the plugin, set it with the recent login.
#   auth_token will permit "quicker" login in future executions by reusing the existing login session (less HTTPS calls = quicker video transitions between clips)
# update the authorization token in the configuration file if we had to login for a new one during this execution run
if auth_writely != gdrive.writely and save_auth_token == 'true':
    ADDON.setSetting('auth_writely', gdrive.writely)
    ADDON.setSetting('auth_wise', gdrive.wise)

# the parameter set for wise vs writely was detected as incorrect during this run; reset as necessary
if useWRITELY == True  and gdrive.useWRITELY == False:
    ADDON.setSetting('force_writely','false')
elif useWRITELY == False and gdrive.useWRITELY == True:
    ADDON.setSetting('force_writely','true')

xbmcplugin.endOfDirectory(plugin_handle)

