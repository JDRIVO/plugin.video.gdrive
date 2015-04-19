'''
    gdrive XBMC Plugin
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

from resources.lib import encryption

import sys
import urllib
import cgi
import re
import xbmcvfs


import xbmc, xbmcgui, xbmcplugin, xbmcaddon

# global variables
PLUGIN_NAME = 'gdrive'

#helper methods
def log(msg, err=False):
    if err:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg, xbmc.LOGERROR)
    else:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg, xbmc.LOGDEBUG)

def parse_query(query):
    queries = cgi.parse_qs(query)
    q = {}
    for key, value in queries.items():
        q[key] = value[0]
    q['mode'] = q.get('mode', 'main')
    return q


def addMediaFile(service, package, contextType='video'):

    listitem = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail)

    if package.file.type == package.file.AUDIO:
        if package.file.hasMeta:
            infolabels = decode_dict({ 'title' : package.file.displayTitle(), 'tracknumber' : package.file.trackNumber, 'artist': package.file.artist, 'album': package.file.album,'genre': package.file.genre,'premiered': package.file.releaseDate, 'size' : package.file.size })
        else:
            infolabels = decode_dict({ 'title' : package.file.displayTitle(), 'size' : package.file.size })
        listitem.setInfo('Music', infolabels)
        playbackURL = '?mode=audio'
        listitem.setProperty('IsPlayable', 'true')
    elif package.file.type == package.file.VIDEO:
        infolabels = decode_dict({ 'title' : package.file.displayTitle() , 'plot' : package.file.plot, 'size' : package.file.size })
        listitem.setInfo('Video', infolabels)
        playbackURL = '?mode=video'
        listitem.setProperty('IsPlayable', 'true')
    elif package.file.type == package.file.PICTURE:
        infolabels = decode_dict({ 'title' : package.file.displayTitle() , 'plot' : package.file.plot })
        listitem.setInfo('Pictures', infolabels)
        playbackURL = '?mode=photo'
    else:
        infolabels = decode_dict({ 'title' : package.file.displayTitle() , 'plot' : package.file.plot, 'size' : package.file.size })
        listitem.setInfo('Video', infolabels)
        playbackURL = '?mode=video'
        listitem.setProperty('IsPlayable', 'true')

    listitem.setProperty('fanart_image', package.file.fanart)
    cm=[]

    try:
        url = package.getMediaURL()
        cleanURL = re.sub('---', '', url)
        cleanURL = re.sub('&', '---', cleanURL)
    except:
        cleanURL = ''

#    url = PLUGIN_URL+'?mode=streamurl&title='+package.file.title+'&url='+cleanURL
    url = PLUGIN_URL+playbackURL+'&title='+package.file.title+'&filename='+package.file.id+'&instance='+str(service.instanceName)+'&filesize='+str(package.file.size)+'&folder='+str(package.folder.id)


    if (contextType != 'image' and package.file.type != package.file.PICTURE):
        cm.append(( addon.getLocalizedString(30042), 'XBMC.RunPlugin('+PLUGIN_URL+'?mode=buildstrm&username='+str(service.authorization.username)+'&title='+package.file.title+'&filename='+package.file.id+')', ))
        if (service.protocol == 2):
            cm.append(( addon.getLocalizedString(30113), 'XBMC.RunPlugin('+url + '&download=true'+')', ))
            cm.append(( addon.getLocalizedString(30123), 'XBMC.RunPlugin('+url + '&original=true'+')', ))
            cm.append(( addon.getLocalizedString(30124), 'XBMC.RunPlugin('+url + '&play=true&download=true'+')', ))
            cm.append(( addon.getLocalizedString(30125), 'XBMC.RunPlugin('+url + '&cache=true'+')', ))


    elif contextType == 'image':
        cm.append(( addon.getLocalizedString(30126), 'XBMC.RunPlugin('+PLUGIN_URL+'?mode=slideshow&folder='+str(package.folder.id)+'&instance='+str(service.instanceName)+')', ))

    url = url + '&content_type='+contextType

#    listitem.addContextMenuItems( commands )
#    if cm:
    listitem.addContextMenuItems(cm, False)


    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
                                isFolder=False, totalItems=0)
    return url


def addDirectory(service, folder, contextType='video'):

    listitem = xbmcgui.ListItem(decode(folder.displayTitle()), iconImage=decode(folder.thumb), thumbnailImage=decode(folder.thumb))
    fanart = addon.getAddonInfo('path') + '/fanart.jpg'


    if folder.id != '':
        cm=[]
        if contextType != 'image':
            cm.append(( addon.getLocalizedString(30042), 'XBMC.RunPlugin('+PLUGIN_URL+'?mode=buildstrm&title='+folder.title+'&username='+str(service.authorization.username)+'&folderID='+str(folder.id)+')', ))
#        cm.append(( addon.getLocalizedString(30081), 'XBMC.RunPlugin('+PLUGIN_URL+'?mode=createbookmark&title='+folder.title+'&instanceName='+str(service.instanceName)+'&folderID='+str(folder.id)+')', ))
        elif contextType == 'image':
            cm.append(( addon.getLocalizedString(30126), 'XBMC.RunPlugin('+PLUGIN_URL+'?mode=slideshow&title='+str(folder.title) + '&folder='+str(folder.id)+'&username='+str(service.authorization.username)+')', ))

        if (service.protocol == 2):
            cm.append(( addon.getLocalizedString(30113), 'XBMC.RunPlugin('+PLUGIN_URL+'?mode=downloadfolder&title='+str(folder.title) + '&folder='+str(folder.id)+'&instance='+str(service.instanceName)+')', ))

        listitem.addContextMenuItems(cm, False)
    listitem.setProperty('fanart_image', fanart)

    xbmcplugin.addDirectoryItem(plugin_handle, service.getDirectoryCall(folder, contextType), listitem,
                                isFolder=True, totalItems=0)


def addMenu(url, title, img='', fanart='', total_items=0):
    listitem = xbmcgui.ListItem(decode(title), iconImage=img, thumbnailImage=img)
    if not fanart:
        fanart = addon.getAddonInfo('path') + '/fanart.jpg'
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


def numberOfAccounts(accountType):

    count = 1
    try:
        max_count = int(addon.getSetting(accountType+'_numaccounts'))
    except:
        max_count = 10
    actualCount = 0
    while True:
        try:
            if addon.getSetting(accountType+str(count)+'_username') != '':
                actualCount = actualCount + 1
        except:
            break
        if count == max_count:
            break
        count = count + 1
    return actualCount

#global variables
PLUGIN_URL = sys.argv[0]
plugin_handle = int(sys.argv[1])
plugin_queries = parse_query(sys.argv[2][1:])

addon = xbmcaddon.Addon(id='plugin.video.gdrive')

addon_dir = xbmc.translatePath( addon.getAddonInfo('path') )


import os
#sys.path.append(os.path.join( addon_dir, 'resources', 'lib' ) )

from resources.lib import gdrive
from resources.lib import gdrive_api2
from resources.lib import cloudservice
from resources.lib import authorization
from resources.lib import folder
from resources.lib import file
from resources.lib import package
from resources.lib import mediaurl
from resources.lib import crashreport



try:

    remote_debugger = addon.getSetting('remote_debugger')
    remote_debugger_host = addon.getSetting('remote_debugger_host')

    # append pydev remote debugger
    if remote_debugger == 'true':
        # Make pydev debugger works for auto reload.
        # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
        import pysrc.pydevd as pydevd
        # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
        pydevd.settrace(remote_debugger_host, stdoutToServer=True, stderrToServer=True)
except ImportError:
    log(addon.getLocalizedString(30016), True)
    sys.exit(1)
except :
    pass


# retrieve settings
user_agent = addon.getSetting('user_agent')
#obsolete, replace, revents audio from streaming
#if user_agent == 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)':
#    addon.setSetting('user_agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.38 Safari/532.0')

#promptQuality = addon.getSetting('prompt_quality')


# hidden parameters which may not even be defined
try:
    useWRITELY = addon.getSetting('force_writely')
    if useWRITELY == 'true':
        useWRITELY = True
    else:
        useWRITELY = False
except :
    useWRITELY = True


mode = plugin_queries['mode']

# make mode case-insensitive
mode = mode.lower()


log('plugin url: ' + PLUGIN_URL)
log('plugin queries: ' + str(plugin_queries))
log('plugin handle: ' + str(plugin_handle))

# allow for playback of public videos without authentication
if (mode == 'streamurl'):
  authenticate = False
else:
  authenticate = True

instanceName = ''
try:
    instanceName = (plugin_queries['instance']).lower()
except:
    pass

# sorting options
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_SIZE)


try:
    contextType = plugin_queries['content_type']
except:
    contextType = ''


    #contentType
    #video context
    # 0 video
    # 1 video and music
    # 2 everything
    #
    #music context
    # 3 music
    # 4 everything
    #
    #photo context
    # 5 photo
    # 6 music and photos
    # 7 everything

try:
      contentType = 0
      if contextType == 'video':
        if (int(addon.getSetting('context_video'))) == 2:
            contentType = 2
        elif (int(addon.getSetting('context_video'))) == 1:
            contentType = 1
        else:
            contentType = 0

      elif contextType == 'audio':
        if (int(addon.getSetting('context_music'))) == 1:
            contentType = 4
        else:
            contentType = 3

      elif contextType == 'image':
        if (int(addon.getSetting('context_photo'))) == 2:
            contentType = 7
        elif (int(addon.getSetting('context_photo'))) == 1:
            contentType = 6
        else:
            contentType = 5
except:
      contentType = 2

#* utilities *
#clear the authorization token(s) from the identified instanceName or all instances
if mode == 'clearauth':

    if instanceName != '':

        try:
            # gdrive specific ***
            addon.setSetting(instanceName + '_auth_writely', '')
            addon.setSetting(instanceName + '_auth_wise', '')
            # ***
            xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30023))
        except:
            #error: instance doesn't exist
            pass

    # clear all accounts
    else:
        count = 1
        max_count = int(addon.getSetting(PLUGIN_NAME+'_numaccounts'))
        while True:
            instanceName = PLUGIN_NAME+str(count)
            try:
                # gdrive specific ***
                addon.setSetting(instanceName + '_auth_writely', '')
                addon.setSetting(instanceName + '_auth_wise', '')
                # ***
            except:
                break
            if count == max_count:
                break
            count = count + 1
        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30023))
    xbmcplugin.endOfDirectory(plugin_handle)

# enroll a new account
elif mode == 'enroll':


        invokedUsername = ''
        try:
            invokedUsername = plugin_queries['username']
        except:
            pass

        code = ''
        try:
            code = plugin_queries['code']
        except:
            pass

        count = 1
        max_count = int(addon.getSetting(PLUGIN_NAME+'_numaccounts'))
        loop = True
        while loop:
            instanceName = PLUGIN_NAME+str(count)
            try:
                username = addon.getSetting(instanceName+'_username')
                if username == invokedUsername:
                    addon.setSetting(instanceName + '_type', str(1))
                    addon.setSetting(instanceName + '_code', str(code))
                    addon.setSetting(instanceName + '_auth_wise', str(invokedUsername))
                    xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30118), invokedUsername)
                    loop = False
                elif username == '':
                    addon.setSetting(instanceName + '_type', str(1))
                    addon.setSetting(instanceName + '_code', str(code))
                    addon.setSetting(instanceName + '_username', str(invokedUsername))
                    xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30118), invokedUsername)
                    loop = False

            except:
                pass

            if count == max_count:
                #fallback on first defined account
                addon.setSetting(instanceName + '_type', str(1))
                addon.setSetting(instanceName + '_code', code)
                addon.setSetting(instanceName + '_username', username)
            count = count + 1

#create strm files
elif mode == 'buildstrm':

    silent = 0
    try:
        silent = int(addon.getSetting('strm_silent'))
    except:
        silent = 0

    try:
        silent = int(plugin_queries['silent'])
    except:
        pass

    try:
        path = addon.getSetting('strm_path')
    except:
        path = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30026), 'files','',False,False,'')
        addon.setSetting('strm_path', path)

    if path == '':
        path = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30026), 'files','',False,False,'')
        addon.setSetting('strm_path', path)

    if path != '':
        returnPrompt = xbmcgui.Dialog().yesno(addon.getLocalizedString(30000), addon.getLocalizedString(30027) + '\n'+path +  '?')


    if path != '' and returnPrompt:

        if silent != 2:
            try:
                pDialog = xbmcgui.DialogProgressBG()
                pDialog.create(addon.getLocalizedString(30000), 'Building STRMs...')
            except:
                pass

        try:
            url = plugin_queries['streamurl']
            title = plugin_queries['title']
            url = re.sub('---', '&', url)
        except:
            url=''

        if url != '':

                filename = path + '/' + title+'.strm'
                strmFile = xbmcvfs.File(filename, "w")

                strmFile.write(url+'\n')
                strmFile.close()
        else:

            try:
                folderID = plugin_queries['folderID']
                title = plugin_queries['title']
            except:
                folderID = ''

            try:
                filename = plugin_queries['filename']
                title = plugin_queries['title']
            except:
                filename = ''

            try:
                    invokedUsername = plugin_queries['username']
            except:
                    invokedUsername = ''

            if folderID != '':

                count = 1
                max_count = int(addon.getSetting(PLUGIN_NAME+'_numaccounts'))
                loop = True
                while loop:
                    instanceName = PLUGIN_NAME+str(count)
                    try:
                        username = addon.getSetting(instanceName+'_username')
                        if username == invokedUsername:

                            #let's log in
                            if ( int(addon.getSetting(instanceName+'_type')) > 0):
                                service = gdrive_api2.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
                            else:
                                service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)

                            loop = False
                    except:
                        break

                    if count == max_count:
                        try:
                            service
                        except NameError:
                            #fallback on first defined account
                            if ( int(addon.getSetting(PLUGIN_NAME+'1'+'_type')) > 0):
                                service = gdrive_api2.gdrive(PLUGIN_URL,addon,PLUGIN_NAME+'1', user_agent)
                            else:
                                service = gdrive.gdrive(PLUGIN_URL,addon,PLUGIN_NAME+'1', user_agent)
                        break
                    count = count + 1

                service.buildSTRM(path + '/'+title,folderID, contentType=contentType, pDialog=pDialog)


            elif filename != '':
                            url = PLUGIN_URL+'?mode=video&title='+title+'&filename='+filename + '&username='+invokedUsername
                            filename = path + '/' + title+'.strm'
                            strmFile = xbmcvfs.File(filename, "w")
                            strmFile.write(url+'\n')
                            strmFile.close()

            else:

                count = 1
                max_count = int(addon.getSetting(PLUGIN_NAME+'_numaccounts'))
                while True:
                    instanceName = PLUGIN_NAME+str(count)
                    try:
                        username = addon.getSetting(instanceName+'_username')
                    except:
                        username = ''

                    if username != '':
                        if ( int(addon.getSetting(instanceName+'_type')) > 0):
                            service = gdrive_api2.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
                        else:
                            service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)

                        service.buildSTRM(path + '/'+username, contentType=contentType, pDialog=pDialog)

                    if count == max_count:
                        #fallback on first defined account
                        try:
                            service
                        except NameError:
                            #fallback on first defined account
                            if ( int(addon.getSetting(PLUGIN_NAME+'1'+'_type')) > 0):
                                service = gdrive_api2.gdrive(PLUGIN_URL,addon,PLUGIN_NAME+'1', user_agent)
                            else:
                                service = gdrive.gdrive(PLUGIN_URL,addon,PLUGIN_NAME+'1', user_agent)
                        break
                    count = count + 1

        if silent != 2:
            try:
                pDialog.update(100)
                pDialog.close()
            except:
                pass
        if silent == 0:
            xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30028))
    xbmcplugin.endOfDirectory(plugin_handle)


numberOfAccounts = numberOfAccounts(PLUGIN_NAME)

try:
    invokedUsername = plugin_queries['username']
except:
    invokedUsername = ''

# show list of services
if numberOfAccounts > 1 and instanceName == '' and invokedUsername == '' and mode == 'main':
        mode = ''
        count = 1
        max_count = int(addon.getSetting(PLUGIN_NAME+'_numaccounts'))
        while True:
            instanceName = PLUGIN_NAME+str(count)
            try:
                username = addon.getSetting(instanceName+'_username')
                if username != '':
                    addMenu(PLUGIN_URL+'?mode=main&content_type='+str(contextType)+'&instance='+str(instanceName),username)
            except:
                break
            if count == max_count:
                break
            count = count + 1

    # show index of accounts
elif instanceName == '' and invokedUsername == '' and numberOfAccounts == 1:

        count = 1
        options = []
        accounts = []
        max_count = int(addon.getSetting(PLUGIN_NAME+'_numaccounts'))

        for count in range (1, max_count):
            instanceName = PLUGIN_NAME+str(count)
            try:
                username = addon.getSetting(instanceName+'_username')
                if username != '':
                    options.append(username)
                    accounts.append(instanceName)

                if username != '':

                    #let's log in
                    if ( int(addon.getSetting(instanceName+'_type')) > 0):
                        service = gdrive_api2.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
                    else:
                        service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
                    break
            except:
                break

        try:
                    service
        except NameError:
                    ret = xbmcgui.Dialog().select(addon.getLocalizedString(30120), options)

                    #fallback on first defined account
                    if ( int(addon.getSetting(accounts[ret]+'_type')) > 0):
                        service = gdrive_api2.gdrive(PLUGIN_URL,addon,accounts[ret], user_agent)
                    else:
                        service = gdrive.gdrive(PLUGIN_URL,addon,accounts[ret], user_agent)


# no accounts defined and url provided; assume public
elif numberOfAccounts == 0 and mode=='streamurl':
    service = gdrive_api2.gdrive(PLUGIN_URL,addon,'', user_agent, authenticate=False)

    # no accounts defined
elif numberOfAccounts == 0:

        #legacy account conversion
        try:
            username = addon.getSetting('username')

            if username != '':
                addon.setSetting(PLUGIN_NAME+'1_username', username)
                addon.setSetting(PLUGIN_NAME+'1_password', addon.getSetting('password'))
                addon.setSetting(PLUGIN_NAME+'1_auth_writely', addon.getSetting('auth_writely'))
                addon.setSetting(PLUGIN_NAME+'1_auth_wise', addon.getSetting('auth_wise'))
                addon.setSetting('username', '')
                addon.setSetting('password', '')
                addon.setSetting('auth_writely', '')
                addon.setSetting('auth_wise', '')
            else:
                xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30015))
                log(addon.getLocalizedString(30015), True)
                xbmcplugin.endOfDirectory(plugin_handle)
        except :
            xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30015))
            log(addon.getLocalizedString(30015), True)
            xbmcplugin.endOfDirectory(plugin_handle)

        #let's log in
        if ( int(addon.getSetting(instanceName+'_type')) > 0):
            service = gdrive_api2.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
        else:
            service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)


    # show entries of a single account (such as folder)
elif instanceName != '':

        #let's log in
        if ( int(addon.getSetting(instanceName+'_type')) > 0):
            service = gdrive_api2.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
        else:
            service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)


elif invokedUsername != '':

        options = []
        accounts = []
        max_count = int(addon.getSetting(PLUGIN_NAME+'_numaccounts'))
        for count in range (1, max_count):
            instanceName = PLUGIN_NAME+str(count)
            try:
                username = addon.getSetting(instanceName+'_username')
                if username != '':
                    options.append(username)
                    accounts.append(instanceName)

                if username == invokedUsername:

                    #let's log in
                    if ( int(addon.getSetting(instanceName+'_type')) > 0):
                        service = gdrive_api2.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
                    else:
                        service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
                    break
            except:
                break

        #fallback on first defined account
        try:
                    service
        except NameError:
                    ret = xbmcgui.Dialog().select(addon.getLocalizedString(30120), options)

                    #fallback on first defined account
                    if ( int(addon.getSetting(accounts[ret]+'_type')) > 0):
                        service = gdrive_api2.gdrive(PLUGIN_URL,addon,accounts[ret], user_agent)
                    else:
                        service = gdrive.gdrive(PLUGIN_URL,addon,accounts[ret], user_agent)
#prompt before playback
else:

        options = []
        accounts = []
        max_count = int(addon.getSetting(PLUGIN_NAME+'_numaccounts'))
        for count in range (1, max_count):
            instanceName = PLUGIN_NAME+str(count)
            try:
                username = addon.getSetting(instanceName+'_username')
                if username != '':
                    options.append(username)
                    accounts.append(instanceName)
            except:
                break

        # url provided; provide public option
        if mode=='streamurl':
            options.append('public')
            accounts.append('public')

        ret = xbmcgui.Dialog().select(addon.getLocalizedString(30120), options)

        #fallback on first defined account
        if accounts[ret] == 'public':
            service = gdrive_api2.gdrive(PLUGIN_URL,addon,'', user_agent, authenticate=False)
        elif ( int(addon.getSetting(accounts[ret]+'_type')) > 0):
            service = gdrive_api2.gdrive(PLUGIN_URL,addon,accounts[ret], user_agent)
        else:
            service = gdrive.gdrive(PLUGIN_URL,addon,accounts[ret], user_agent)


#if mode == 'main':
#    addMenu(PLUGIN_URL+'?mode=options','<< '+addon.getLocalizedString(30043)+' >>')


#dump a list of videos available to play
if mode == 'main' or mode == 'index':

    folderName = ''
    try:
      folderName = plugin_queries['folder']
    except:
      folderName = False


    # gdrive specific ***
    try:
      decrypt = plugin_queries['decrypt']
      service.setDecrypt()
      log('decrypt ')
    except:
      decrypt = False
    # ***

    # display option for all Videos/Music/Photos, across gdrive
    # gdrive specific ***
    if mode == 'main':
        if contentType in (2,4,7):
            addMenu(PLUGIN_URL+'?mode=index&folder=ALL&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30030)+']')
        elif contentType == 1:
            addMenu(PLUGIN_URL+'?mode=index&folder=VIDEOMUSIC&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30031)+']')
        elif contentType == 0:
            addMenu(PLUGIN_URL+'?mode=index&folder=VIDEO&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30025)+']')
        elif contentType == 3:
            addMenu(PLUGIN_URL+'?mode=index&folder=MUSIC&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30094)+']')
        elif contentType == 5:
            addMenu(PLUGIN_URL+'?mode=index&folder=PHOTO&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30034)+']')
        elif contentType == 6:
            addMenu(PLUGIN_URL+'?mode=index&folder=PHOTOMUSIC&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30032)+']')
        folderName = 'root'
        if (service.protocol != 2):
            addMenu(PLUGIN_URL+'?mode=index&folder=STARRED-FILES&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+ ' '+addon.getLocalizedString(30095)+']')
            addMenu(PLUGIN_URL+'?mode=index&folder=STARRED-FOLDERS&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+  ' '+addon.getLocalizedString(30096)+']')
        addMenu(PLUGIN_URL+'?mode=index&folder=SHARED&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+  ' '+addon.getLocalizedString(30098)+']')
        addMenu(PLUGIN_URL+'?mode=index&folder=STARRED-FILESFOLDERS&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+  ' '+addon.getLocalizedString(30097)+']')
        addMenu(PLUGIN_URL+'?mode=search&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30111)+']')

    # ***

    try:
        service
    except NameError:
        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30051), addon.getLocalizedString(30052))
        log(addon.getLocalizedString(30050)+ 'gdrive-login', True)
        xbmcplugin.endOfDirectory(plugin_handle)

    mediaItems = service.getMediaList(folderName,contentType=contentType)

    if mediaItems:
            for item in mediaItems:

                    if item.file is None:
                        addDirectory(service, item.folder, contextType)
                    else:
                        addMediaFile(service, item, contextType)

 #   if contextType == 'image':
#        item = xbmcgui.ListItem(path='/downloads/pics/0/')
#        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, item)
#        xbmc.executebuiltin("XBMC.SlideShow(/downloads/pics/0/)")

    service.updateAuthorization(addon)


elif mode == 'photo':

    try:
      title = plugin_queries['title']
    except:
      title = 0

    try:
      docid = plugin_queries['filename']
    except:
      docid = ''

    try:
      folder = plugin_queries['folder']
    except:
      folder = 0


    path = ''
    try:
        path = addon.getSetting('photo_folder')
    except:
        pass

    if not xbmcvfs.exists(path):
        path = ''

    while path == '':
        path = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30038), 'files','',False,False,'')
        if not xbmcvfs.exists(path):
            path = ''
        else:
            addon.setSetting('photo_folder', path)

    if (not xbmcvfs.exists(str(path) + '/'+str(folder) + '/')):
        xbmcvfs.mkdir(str(path) + '/'+str(folder))
    try:
        xbmcvfs.rmdir(str(path) + '/'+str(folder)+'/'+str(title))
    except:
        pass

    # don't redownload if present already
    if (not xbmcvfs.exists(str(path) + '/'+str(folder)+'/'+str(title))):
        url = service.getDownloadURL(docid)
        service.downloadPicture(url, str(path) + '/'+str(folder) + '/'+str(title))

    xbmc.executebuiltin("XBMC.ShowPicture("+str(path) + '/'+str(folder) + '/'+str(title)+")")
    item = xbmcgui.ListItem(path=str(path) + '/'+str(folder) + '/'+str(title))
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, item)

#*** needs updating
elif mode == 'downloadfolder':

    #title
    try:
        title = plugin_queries['title']
    except:
        title = ''

    try:
        folderID = plugin_queries['folder']
    except:
        folderID = ''

    try:
        service
    except NameError:
        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30051), addon.getLocalizedString(30052))
        log(addon.getLocalizedString(30050)+ 'gdrive-login', True)
        xbmcplugin.endOfDirectory(plugin_handle)

    mediaItems = service.getMediaList(folderName=folderID, contentType=contentType)

    if mediaItems:
        for item in mediaItems:
            if item.file is not None:
                service.downloadMediaFile('', item.mediaurl.url, item.file.title, folderID, item.file.id, item.file.size)


#*** needs updating
elif mode == 'decryptfolder':
    try:
      folder = plugin_queries['folder']
    except:
      folder = 0

    try:
      title = plugin_queries['title']
    except:
      title = 0

    path = '/tmp/2/'

    enc_password = str(addon.getSetting('enc_password'))

    salt = encryption.read_salt(str(addon.getSetting('salt')))

    key = encryption.generate_key(enc_password,salt,encryption.NUMBER_OF_ITERATIONS)

    service.decryptFolder(key,path,folder)



elif mode == 'slideshow':
    try:
      folder = plugin_queries['folder']
    except:
      folder = 0

    try:
      title = plugin_queries['title']
    except:
      title = 0

    path = ''
    try:
        path = addon.getSetting('photo_folder')
    except:
        pass

    if not xbmcvfs.exists(path):
        path = ''


    if (not xbmcvfs.exists(str(path) + '/'+str(folder) + '/')):
        xbmcvfs.mkdir(str(path) + '/'+str(folder))
    try:
        xbmcvfs.rmdir(str(path) + '/'+str(folder)+'/'+str(title))
    except:
        pass


    while path == '':
        path = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30038), 'files','',False,False,'')
        if not xbmcvfs.exists(path):
            path = ''
        else:
            addon.setSetting('photo_folder', path)

    mediaItems = service.getMediaList(folderName=folder, contentType=5)

    xbmc.executebuiltin("XBMC.SlideShow("+str(path) + '/'+str(folder)+"/)")

    if mediaItems:
                for item in mediaItems:
                    if item.file is not None:
                        service.downloadPicture(item.mediaurl.url,str(path) + '/'+str(folder)+ '/'+item.file.title)
                        xbmc.executebuiltin("XBMC.SlideShow("+str(path) + '/'+str(folder)+"/)")

elif mode == 'audio':

    #title
    try:
        title = plugin_queries['title']
    except:
        title = ''


    #docid
    try:
        filename = plugin_queries['filename']
    except:
        filename = ''

    #docid
    try:
        folderID = plugin_queries['folder']
        if folderID == 'False':
            folderID = 'SEARCH'
    except:
        folderID = ''

    try:
        service
    except NameError:
        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30051), addon.getLocalizedString(30052))
        log(addon.getLocalizedString(30050)+ 'gdrive-login', True)
        xbmcplugin.endOfDirectory(plugin_handle)


    #force cache
    try:
        download = addon.getSetting('always_cache')
        if download == 'true':
            download = True
            play = True
        else:
            download = False
            play = False
    except:
        download = False
        play = False

    #user selected to download
    try:
        download = plugin_queries['download']
        if download == 'true':
            download = True
        else:
            download = False
    except:
        pass

    #user selected to playback
    try:
        play = plugin_queries['play']
        if play == 'true':
            play = True
        else:
            play = False
    except:
        pass

    #user selected to playback from cache
    try:
        cache = plugin_queries['cache']
        if cache == 'true':
            cache = True
            download = False
            play = False
        else:
            cache = False
    except:
        cache = False

    #filesize (used for downloading)
    try:
      fileSize = plugin_queries['filesize']
    except:
      fileSize = ''

    #cache folder (used for downloading)
    try:
        path = addon.getSetting('cache_folder')
    except:
        path = ''


    playbackMedia = True
    #if we don't have the docid, search for the video for playback
    if (filename != ''):
        mediaFile = file.file(filename, title, '', service.MEDIA_TYPE_MUSIC, '','')
        mediaFolder = folder.folder(folderID,'')
        mediaURLs = service.getPlaybackCall(0,package=package.package(mediaFile,mediaFolder))
    else:
        if mode == 'search':

            if title == '':

                try:
                    dialog = xbmcgui.Dialog()
                    title = dialog.input(addon.getLocalizedString(30110), type=xbmcgui.INPUT_ALPHANUM)
                except:
                    xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30100))
                    title = 'test'
            mediaItems = service.getMediaList(title=title, contentType=contentType)
            playbackMedia = False

            options = []
            urls = []

            if mediaItems:
                for item in mediaItems:
                    if item.file is None:
                        addDirectory(service, item.folder, contextType)
                    else:
                        options.append(item.file.title)
                        urls.append(addMediaFile(service, item))

            #search from STRM
            if contextType == '':

                ret = xbmcgui.Dialog().select(addon.getLocalizedString(30112), options)
                playbackURL = urls[ret]

                item = xbmcgui.ListItem(path=playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY))
                # for unknown reasons, for remote music, if Music is tagged as Music, it errors-out when playing back from "Music", doesn't happen when labeled "Video"
                item.setInfo( type="Video", infoLabels={ "Title": options[ret] } )
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

        else:
            mediaURLs = service.getPlaybackCall(0,None,title=title)


    if playbackMedia:

        playbackURL = ''
        playbackQuality = ''
        playbackPath = ''
        if cache:
            playbackPath = str(path) + '/' + str(folderID) + '/' + str(filename) + '/'

            if xbmcvfs.exists(playbackPath):

                    dirs,files = xbmcvfs.listdir(playbackPath)

                    playbackPath = str(playbackPath) + str(files[0])

        else:
            playbackURL = mediaURLs[0].url
            playbackQuality = mediaURLs[0].quality

        #right-menu context or STRM
        if contextType == '':
            #download only
            if download and not play:
                service.downloadMediaFile('',playbackURL, str(title)+'.'+ str(playbackQuality), folderID, filename, fileSize, force=True)
            #download and play
            elif download and play:
                service.downloadMediaFile(int(sys.argv[1]), playbackURL, str(title)+'.'+ str(playbackQuality), folderID, filename, fileSize)
            elif cache:
                xbmc.executebuiltin("XBMC.PlayMedia("+str(playbackPath)+")")
            #stream
            else:
                item = xbmcgui.ListItem(path=playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY))
                # for unknown reasons, for remote music, if Music is tagged as Music, it errors-out when playing back from "Music", doesn't happen when labeled "Video"
                item.setInfo( type="Video", infoLabels={ "Title": title } )
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, item)

                #xbmc.executebuiltin("XBMC.PlayMedia("+str(playbackURL)+'|' + service.getHeadersEncoded(service.useWRITELY)+")")

        #direct playback from within plugin
        elif cache:
                item = xbmcgui.ListItem(path=str(playbackPath))
                # local, not remote. "Music" is ok
                item.setInfo( type="Music", infoLabels={ "Title": title } )
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

        #direct playback from within plugin
        else:

            item = xbmcgui.ListItem(path=playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY))
            # for unknown reasons, for remote music, if Music is tagged as Music, it errors-out when playing back from "Music", doesn't happen when labeled "Video"
            item.setInfo( type="Video", infoLabels={ "Title": title } )
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, item)
#            xbmc.executebuiltin("XBMC.PlayMedia("+str(playbackURL)+'|' + service.getHeadersEncoded(service.useWRITELY)+")")

#force stream - play a video given its url
elif mode == 'streamurl':

    try:
      url = plugin_queries['url']
    except:
      url = 0

    try:
      title = plugin_queries['title']
    except:
      title = ''

    promptQuality = True
    try:
        promptQuality = addon.getSetting('prompt_quality')
        if promptQuality == 'false':
            promptQuality = False
    except:
        pass

    mediaURLs = service.getPublicStream(url)
    options = []

    if mediaURLs:
        mediaURLs = sorted(mediaURLs)
        for mediaURL in mediaURLs:
            options.append(mediaURL.qualityDesc)

        if promptQuality:
            ret = xbmcgui.Dialog().select(addon.getLocalizedString(30033), options)
        else:
            ret = 0

        playbackURL = mediaURLs[ret].url

        if (playbackURL == ''):
            xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30020),addon.getLocalizedString(30021))
            xbmc.log(addon.getAddonInfo('name') + ': ' + addon.getLocalizedString(20021), xbmc.LOGERROR)
        else:
            # if invoked in .strm or as a direct-video (don't prompt for quality)
            item = xbmcgui.ListItem(path=playbackURL+ '|' + service.getHeadersEncoded(service.useWRITELY))
            item.setInfo( type="Video", infoLabels={ "Title": mediaURLs[ret].title , "Plot" : mediaURLs[ret].title } )
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
    else:
            xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30020),addon.getLocalizedString(30021))
            xbmc.log(addon.getAddonInfo('name') + ': ' + addon.getLocalizedString(20021), xbmc.LOGERROR)




#playback of video
# legacy (depreicated) - memorycachevideo [given title]
# legacy (depreicated) - play [given title]
# legacy (depreicated) - playvideo [given title]
# legacy (depreicated) - streamvideo [given title]
elif mode == 'video' or mode == 'search' or mode == 'play' or mode == 'memorycachevideo' or mode == 'playvideo' or mode == 'streamvideo':

    #title
    try:
        title = plugin_queries['title']
    except:
        title = ''

    #closed captions
    srt = ''
    try:
        srt = plugin_queries['srt']
    except:
        srt = ''

    #docid
    try:
        filename = plugin_queries['filename']
    except:
        filename = ''

    #docid
    try:
        folderID = plugin_queries['folder']
    except:
        folderID = ''

    try:
        service
    except NameError:
        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30051), addon.getLocalizedString(30052))
        log(addon.getLocalizedString(30050)+ 'gdrive-login', True)
        xbmcplugin.endOfDirectory(plugin_handle)


    promptQuality = True
    try:
        promptQuality = addon.getSetting('prompt_quality')
        if promptQuality == 'false':
            promptQuality = False
    except:
        pass

    try:
        playOriginal = addon.getSetting('never_stream')
        if playOriginal == 'true':
            playOriginal = True
        else:
            playOriginal = False
    except:
        playOriginal = False

    try:
        playOriginal = plugin_queries['original']
        if playOriginal == 'true':
            playOriginal = True
    except:
        pass


    try:
        download = addon.getSetting('always_cache')
        if download == 'true':
            download = True
            play = True
        else:
            download = False
            play = False
    except:
        download = False
        play = False

    try:
        download = plugin_queries['download']
        if download == 'true':
            download = True
        else:
            download = False
    except:
        pass

    try:
        play = plugin_queries['play']
        if play == 'true':
            play = True
        else:
            play = False
    except:
        pass

    if mode == 'memorycachevideo':
        play = True
        download = True
    elif mode == 'playvideo':
        play = False
        download = False
        playOriginal = True

    try:
        cache = plugin_queries['cache']
        if cache == 'true':
            cache = True
            download = False
            play = False
        else:
            cache = False
    except:
        cache = False

    try:
      fileSize = plugin_queries['filesize']
    except:
      fileSize = ''

    try:
        path = addon.getSetting('cache_folder')
    except:
        path = ''

    if srt != '':
        SRTURL = service.getSRT(title)

    playbackMedia = True
    #if we don't have the docid, search for the video for playback
    if (filename != ''):
        mediaFile = file.file(filename, title, '', 0, '','')
        mediaFolder = folder.folder(folderID,'')
        mediaURLs = service.getPlaybackCall(0,package=package.package(mediaFile,mediaFolder))
    else:
        if mode == 'search':

            if title == '':

                try:
                    dialog = xbmcgui.Dialog()
                    title = dialog.input(addon.getLocalizedString(30110), type=xbmcgui.INPUT_ALPHANUM)
                except:
                    xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30100))
                    title = 'test'
            mediaItems = service.getMediaList(title=title, contentType=contentType)
            playbackMedia = False

            options = []
            urls = []

            if mediaItems:
                for item in mediaItems:
                    if item.file is None:
                        addDirectory(service, item.folder, contextType)
                    else:
                        options.append(item.file.title)
                        urls.append(addMediaFile(service, item))

            if contextType == '':

                ret = xbmcgui.Dialog().select(addon.getLocalizedString(30112), options)
                playbackURL = urls[ret]

                item = xbmcgui.ListItem(path=playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY))
                item.setInfo( type="Video", infoLabels={ "Title": options[ret] , "Plot" : options[ret] } )
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

        else:
            mediaURLs = service.getPlaybackCall(0,None,title=title)

    originalURL = ''
    if playbackMedia:
        options = []
        mediaURLs = sorted(mediaURLs)
        for mediaURL in mediaURLs:
            options.append(mediaURL.qualityDesc)
            if mediaURL.qualityDesc == 'original':
                originalURL = mediaURL.url

        playbackURL = ''
        playbackQuality = ''
        playbackPath = ''
        if playOriginal and not cache:
            playbackURL = originalURL
            playbackQuality = 'original'
        elif promptQuality and len(options) > 1 and not cache:
            ret = xbmcgui.Dialog().select(addon.getLocalizedString(30033), options)
            playbackURL = mediaURLs[ret].url
            playbackQuality = mediaURLs[ret].quality
        elif cache:
            playbackPath = str(path) + '/' + str(folderID) + '/' + str(filename) + '/'

            if xbmcvfs.exists(playbackPath):

                    dirs,files = xbmcvfs.listdir(playbackPath)

                    options = []

                    files = sorted(files)
                    for file in files:
                        options.append(file)
                    if promptQuality:
                        ret = xbmcgui.Dialog().select(addon.getLocalizedString(30033), options)
                        playbackPath = str(playbackPath) + str(files[ret])
                    else:
                        playbackPath = str(playbackPath) + str(files[0])

        else:
            playbackURL = mediaURLs[0].url
            playbackQuality = mediaURLs[0].quality

        #right-menu context
        if contextType == '':
            #download only
            if download and not play:
                service.downloadMediaFile('',playbackURL, str(title)+'.'+ str(playbackQuality), folderID, filename, fileSize, force=True)
            #download and play
            elif download and play:
                service.downloadMediaFile(int(sys.argv[1]), playbackURL, str(title)+'.'+ str(playbackQuality), folderID, filename, fileSize)
            elif cache:
                xbmc.executebuiltin("XBMC.PlayMedia("+str(playbackPath)+")")
            #stream
            else:
                xbmc.executebuiltin("XBMC.PlayMedia("+str(playbackURL)+'|' + service.getHeadersEncoded(service.useWRITELY)+")")
        elif cache:
                item = xbmcgui.ListItem(path=str(playbackPath))
                item.setInfo( type="Video", infoLabels={ "Title": title , "Plot" : title } )
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
        else:

            item = xbmcgui.ListItem(path=playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY))
            item.setInfo( type="Video", infoLabels={ "Title": title , "Plot" : title } )
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

#force stream - play a video given its url
elif mode == 'streamurl':

    try:
      url = plugin_queries['url']
    except:
      url = 0

    try:
      title = plugin_queries['title']
    except:
      title = ''

    promptQuality = True
    try:
        promptQuality = addon.getSetting('prompt_quality')
        if promptQuality == 'false':
            promptQuality = False
    except:
        pass

    mediaURLs = service.getPublicStream(url)
    options = []

    if mediaURLs:
        mediaURLs = sorted(mediaURLs)
        for mediaURL in mediaURLs:
            options.append(mediaURL.qualityDesc)

        if promptQuality:
            ret = xbmcgui.Dialog().select(addon.getLocalizedString(30033), options)
        else:
            ret = 0

        playbackURL = mediaURLs[ret].url

        if (playbackURL == ''):
            xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30020),addon.getLocalizedString(30021))
            xbmc.log(addon.getAddonInfo('name') + ': ' + addon.getLocalizedString(20021), xbmc.LOGERROR)
        else:
            # if invoked in .strm or as a direct-video (don't prompt for quality)
            item = xbmcgui.ListItem(path=playbackURL+ '|' + service.getHeadersEncoded(service.useWRITELY))
            item.setInfo( type="Video", infoLabels={ "Title": mediaURLs[ret].title , "Plot" : mediaURLs[ret].title } )
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
    else:
            xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30020),addon.getLocalizedString(30021))
            xbmc.log(addon.getAddonInfo('name') + ': ' + addon.getLocalizedString(20021), xbmc.LOGERROR)



# migrate *
#if username != prev_username:
#    addon.setSetting('prev_username', username)
# *

# the parameter set for wise vs writely was detected as incorrect during this run; reset as necessary
try:
    if useWRITELY == True  and service.useWRITELY == False:
        addon.setSetting('force_writely','false')
    elif useWRITELY == False and service.useWRITELY == True:
        addon.setSetting('force_writely','true')
except:
    pass
xbmcplugin.endOfDirectory(plugin_handle)

