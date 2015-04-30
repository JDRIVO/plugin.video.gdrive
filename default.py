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


def addMenu(url, title, img='', fanart='', total_items=0):
    listitem = xbmcgui.ListItem(decode(title), iconImage=img, thumbnailImage=img)
    if not fanart:
        fanart = addon.getAddonInfo('path') + '/fanart.jpg'
    listitem.setProperty('fanart_image', fanart)

    # disallow play controls on menus
    listitem.setProperty('IsPlayable', 'false')
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

def getParameter(key,default=''):
    try:
        value = plugin_queries[key]
        if value == 'true':
            return True
        elif value == 'false':
            return False
        else:
            return value
    except:
        return default

def getSetting(key,default=''):
    try:
        value = addon.getSetting(key)
        if value == 'true':
            return True
        elif value == 'false':
            return False
        else:
            return value
    except:
        return default

def numberOfAccounts(accountType):

    count = 1
    max_count = int(getSetting(accountType+'_numaccounts',10))

    actualCount = 0
    while True:
        try:
            if getSetting(accountType+str(count)+'_username') != '':
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

addon = xbmcaddon.Addon(id='plugin.video.gdrive-testing')

addon_dir = xbmc.translatePath( addon.getAddonInfo('path') )


#import os
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
from resources.lib import gPlayer
from resources.lib import tvWindow
from resources.lib import gSpreadsheets


try:

    remote_debugger = getSetting('remote_debugger')
    remote_debugger_host = getSetting('remote_debugger_host')

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
user_agent = getSetting('user_agent')
#obsolete, replace, revents audio from streaming
#if user_agent == 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)':
#    addon.setSetting('user_agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.38 Safari/532.0')



# hidden parameters which may not even be defined
useWRITELY = getSetting('force_writely')


mode = getParameter('mode','main')

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


contextType = getParameter('content_type')



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
      contentTypeDecider = int(getSetting('context_video'))

      if contextType == 'video':
        if contentTypeDecider == 2:
            contentType = 2
        elif contentTypeDecider == 1:
            contentType = 1
        else:
            contentType = 0

      elif contextType == 'audio':
        if contentTypeDecider == 1:
            contentType = 4
        else:
            contentType = 3

      elif contextType == 'image':
        if contentTypeDecider == 2:
            contentType = 7
        elif contentTypeDecider == 1:
            contentType = 6
        else:
            contentType = 5

      # show all (for encfs)
      elif contextType == 'all':
            contentType = 8

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
        max_count = int(getSetting(PLUGIN_NAME+'_numaccounts',10))
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


        invokedUsername = getParameter('username')
        code = getParameter('code')

        count = 1
        max_count = int(getSetting(PLUGIN_NAME+'_numaccounts',10))
        loop = True
        while loop:
            instanceName = PLUGIN_NAME+str(count)
            try:
                username = getSetting(instanceName+'_username')
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

    silent = getParameter('silent', getSetting('strm_silent',0))
    if silent == '':
        silent = 0

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

        url = getParameter('streamurl')
        url = re.sub('---', '&', url)
        title = getParameter('title')

        if url != '':

                filename = path + '/' + title+'.strm'
                strmFile = xbmcvfs.File(filename, "w")

                strmFile.write(url+'\n')
                strmFile.close()
        else:

            folderID = getParameter('folder')
            filename = getParameter('filename')
            title = getParameter('title')
            invokedUsername = getParameter('username')

            if folderID != '':

                count = 1
                max_count = int(getSetting(PLUGIN_NAME+'_numaccounts',10))
                loop = True
                while loop:
                    instanceName = PLUGIN_NAME+str(count)
                    try:
                        username = getSetting(instanceName+'_username')
                        if username == invokedUsername:

                            #let's log in
                            if ( int(getSetting(instanceName+'_type',0))==0):
                                service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
                            else:
                                service = gdrive_api2.gdrive(PLUGIN_URL,addon,instanceName, user_agent)

                            loop = False
                    except:
                        break

                    if count == max_count:
                        try:
                            service
                        except NameError:
                            #fallback on first defined account
                            if ( int(getSetting(instanceName+'_type',0))==0):
                                service = gdrive.gdrive(PLUGIN_URL,addon,PLUGIN_NAME+'1', user_agent)
                            else:
                                service = gdrive_api2.gdrive(PLUGIN_URL,addon,PLUGIN_NAME+'1', user_agent)
                        break
                    count = count + 1

                service.buildSTRM(path + '/'+title,folderID, contentType=contentType, pDialog=pDialog)

            elif filename != '':
                            values = {'title': title, 'filename': filename, 'username': invokedUsername}
                            url = PLUGIN_URL+'?mode=video&'+urllib.urlencode(values)
                            filename = path + '/' + title+'.strm'
                            strmFile = xbmcvfs.File(filename, "w")
                            strmFile.write(url+'\n')
                            strmFile.close()

            else:

                count = 1
                max_count = int(getSetting(PLUGIN_NAME+'_numaccounts',10))
                while True:
                    instanceName = PLUGIN_NAME+str(count)
                    username = getSetting(instanceName+'_username')

                    if username != '' and username == invokedUsername:
                        if ( int(getSetting(instanceName+'_type',0))==0):
                                service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
                        else:
                            service = gdrive_api2.gdrive(PLUGIN_URL,addon,instanceName, user_agent)

                        service.buildSTRM(path + '/'+username, contentType=contentType, pDialog=pDialog)

                    if count == max_count:
                        #fallback on first defined account
                        try:
                            service
                        except NameError:
                            #fallback on first defined account
                            if ( int(getSetting(instanceName+'_type',0))==0):
                                    service = gdrive.gdrive(PLUGIN_URL,addon,PLUGIN_NAME+'1', user_agent)
                            else:
                                service = gdrive_api2.gdrive(PLUGIN_URL,addon,PLUGIN_NAME+'1', user_agent)
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

invokedUsername = getParameter('username')

# show list of services
if numberOfAccounts > 1 and instanceName == '' and invokedUsername == '' and mode == 'main':
        mode = ''
        count = 1
        max_count = int(getSetting(PLUGIN_NAME+'_numaccounts',10))
        while True:
            instanceName = PLUGIN_NAME+str(count)
            try:
                username = getSetting(instanceName+'_username')
                if username != '':
                    addMenu(PLUGIN_URL+'?mode=main&content_type='+str(contextType)+'&instance='+str(instanceName),username)
            except:
                break
            if count == max_count:
                break
            count = count + 1

        spreadshetModule = getSetting('library', False)
        libraryAccount = getSetting('library_account')

        if spreadshetModule:
            addMenu(PLUGIN_URL+'?mode=kiosk&content_type='+str(contextType)+'&instance='+PLUGIN_NAME+str(libraryAccount),'[kiosk mode]')

    # show index of accounts
elif instanceName == '' and invokedUsername == '' and numberOfAccounts == 1:

        count = 1
        options = []
        accounts = []
        max_count = int(getSetting(PLUGIN_NAME+'_numaccounts',10))

        for count in range (1, max_count):
            instanceName = PLUGIN_NAME+str(count)
            try:
                username = getSetting(instanceName+'_username')
                if username != '':
                    options.append(username)
                    accounts.append(instanceName)

                if username != '':

                    #let's log in
                    if ( int(getSetting(instanceName+'_type',0))==0):
                            service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
                    else:
                        service = gdrive_api2.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
                    break
            except:
                break

        try:
                    service
        except NameError:
                    ret = xbmcgui.Dialog().select(addon.getLocalizedString(30120), options)

                    #fallback on first defined account
                    if ( int(getSetting(instanceName+'_type',0))==0):
                            service = gdrive.gdrive(PLUGIN_URL,addon,accounts[ret], user_agent)
                    else:
                        service = gdrive_api2.gdrive(PLUGIN_URL,addon,accounts[ret], user_agent)


# no accounts defined and url provided; assume public
elif numberOfAccounts == 0 and mode=='streamurl':
    service = gdrive_api2.gdrive(PLUGIN_URL,addon,'', user_agent, authenticate=False)

    # no accounts defined
elif numberOfAccounts == 0:

        #legacy account conversion
        try:
            username = getSetting('username')

            if username != '':
                addon.setSetting(PLUGIN_NAME+'1_username', username)
                addon.setSetting(PLUGIN_NAME+'1_password', getSetting('password'))
                addon.setSetting(PLUGIN_NAME+'1_auth_writely', getSetting('auth_writely'))
                addon.setSetting(PLUGIN_NAME+'1_auth_wise', getSetting('auth_wise'))
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
        if ( int(getSetting(instanceName+'_type',0))==0):
                service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
        else:
            service = gdrive_api2.gdrive(PLUGIN_URL,addon,instanceName, user_agent)


    # show entries of a single account (such as folder)
elif instanceName != '':

        #let's log in
        if ( int(getSetting(instanceName+'_type',0))==0):
                service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
        else:
            service = gdrive_api2.gdrive(PLUGIN_URL,addon,instanceName, user_agent)


elif invokedUsername != '':

        options = []
        accounts = []
        max_count = int(getSetting(PLUGIN_NAME+'_numaccounts',10))
        for count in range (1, max_count):
            instanceName = PLUGIN_NAME+str(count)
            try:
                username = getSetting(instanceName+'_username')
                if username != '':
                    options.append(username)
                    accounts.append(instanceName)

                if username == invokedUsername:

                    #let's log in
                    if ( int(getSetting(instanceName+'_type',0))==0):
                        service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
                    else:
                        service = gdrive_api2.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
                    break
            except:
                break

        #fallback on first defined account
        try:
                    service
        except NameError:
                    ret = xbmcgui.Dialog().select(addon.getLocalizedString(30120), options)

                    #fallback on first defined account
                    if ( int(getSetting(instanceName+'_type',0))==0):
                        service = gdrive.gdrive(PLUGIN_URL,addon,accounts[ret], user_agent)
                    else:
                        service = gdrive_api2.gdrive(PLUGIN_URL,addon,accounts[ret], user_agent)
#prompt before playback
else:

        options = []
        accounts = []
        max_count = int(getSetting(PLUGIN_NAME+'_numaccounts',10))
        for count in range (1, max_count):
            instanceName = PLUGIN_NAME+str(count)
            try:
                username = getSetting(instanceName+'_username',10)
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
        elif ( int(getSetting(instanceName+'_type',0))==0):
            service = gdrive.gdrive(PLUGIN_URL,addon,accounts[ret], user_agent)
        else:
            service = gdrive_api2.gdrive(PLUGIN_URL,addon,accounts[ret], user_agent)

# override playback
integratedPlayer = getSetting('integrated_player')
try:
    if integratedPlayer:
        service.integratedPlayer = True
except: pass



#if mode == 'main':
#    addMenu(PLUGIN_URL+'?mode=options','<< '+addon.getLocalizedString(30043)+' >>')


#dump a list of videos available to play
if mode == 'main' or mode == 'index':

    folderName = getParameter('folder', False)

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

        encfs_target = getSetting('encfs_target')
        if encfs_target != '':
                service.addDirectory(None, contextType, localPath=encfs_target)


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
                        service.addDirectory(item.folder, contextType=contextType)
                    else:
                        service.addMediaFile(item, contextType=contextType)

 #   if contextType == 'image':
#        item = xbmcgui.ListItem(path='/downloads/pics/0/')
#        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, item)
#        xbmc.executebuiltin("XBMC.SlideShow(/downloads/pics/0/)")

    service.updateAuthorization(addon)

elif mode == 'kiosk':

    spreadshetModule = getSetting('library', False)


    if spreadshetModule:
            gSpreadsheet = gSpreadsheets.gSpreadsheets(service,addon, user_agent)
            spreadsheets = gSpreadsheet.getSpreadsheetList()


            channels = []
            for title in spreadsheets.iterkeys():
                if title == 'TVShows':
                    worksheets = gSpreadsheet.getSpreadsheetWorksheets(spreadsheets[title])

                    import time
                    hour = time.strftime("%H")
                    minute = time.strftime("%M")
                    weekDay = time.strftime("%w")
                    month = time.strftime("%m")
                    day = time.strftime("%d")

                    for worksheet in worksheets.iterkeys():
                         if worksheet == 'schedule':
                             channels = gSpreadsheet.getChannels(worksheets[worksheet])
                             ret = xbmcgui.Dialog().select(addon.getLocalizedString(30112), channels)
                             shows = gSpreadsheet.getShows(worksheets[worksheet] ,channels[ret])
                             showList = []
                             for show in shows:
                                 showList.append(shows[show][6])
                             ret = xbmcgui.Dialog().select(addon.getLocalizedString(30112), showList)

                    for worksheet in worksheets.iterkeys():
                        if worksheet == 'data':
                            episodes = gSpreadsheet.getVideo(worksheets[worksheet] ,showList[ret])
                            player = gPlayer.gPlayer()
                            player.setScheduler(gSpreadsheet)
                            player.setContent(episodes)
                            player.setWorksheet(worksheets['data'])
                            player.next()
                            while player.isExit == 0:
                                xbmc.sleep(10000)


elif mode == 'photo':

    title = getParameter('title',0)
    docid = getParameter('filename')
    folder = getParameter('folder',0)


    path = getSetting('photo_folder')

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
#    try:
#        xbmcvfs.rmdir(str(path) + '/'+str(folder)+'/'+str(title))
#    except:
#        pass

    # don't redownload if present already
    if (not xbmcvfs.exists(str(path) + '/'+str(folder)+'/'+str(title))):
        url = service.getDownloadURL(docid)
        service.downloadPicture(url, str(path) + '/'+str(folder) + '/'+str(title))

    xbmc.executebuiltin("XBMC.ShowPicture("+str(path) + '/'+str(folder) + '/'+str(title)+")")
    item = xbmcgui.ListItem(path=str(path) + '/'+str(folder) + '/'+str(title))
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, item)

#*** needs updating
elif mode == 'downloadfolder':

    title = getParameter('title')
    folderID = getParameter('folder')
    folderName = getParameter('foldername')
    encfs = getParameter('encfs', False)

    try:
        service
    except NameError:
        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30051), addon.getLocalizedString(30052))
        log(addon.getLocalizedString(30050)+ 'gdrive-login', True)
        xbmcplugin.endOfDirectory(plugin_handle)

    if encfs:
        mediaItems = service.getMediaList(folderName=folderID, contentType=8)
    else:
        mediaItems = service.getMediaList(folderName=folderID, contentType=contentType)

    if mediaItems:
        for item in mediaItems:
            if item.file is not None:
                service.downloadMediaFile('', item.mediaurl.url, item.file.title, folderID, item.file.id, item.file.size, encfs=encfs, folderName=folderName)


#*** needs updating
elif mode == 'decryptfolder':

    folder = getParameter('folder',0)
    title = getParameter('title',0)

    path = '/tmp/2/'

    enc_password = getSetting('enc_password')

    salt = encryption.read_salt(strgetSetting('salt'))

    key = encryption.generate_key(enc_password,salt,encryption.NUMBER_OF_ITERATIONS)

    service.decryptFolder(key,path,folder)



elif mode == 'slideshow':

    folder = getParameter('folder',0)
    title = getParameter('title',0)

    path = getSetting('photo_folder')

    if not xbmcvfs.exists(path):
        path = ''


    if (not xbmcvfs.exists(str(path) + '/'+str(folder) + '/')):
        xbmcvfs.mkdir(str(path) + '/'+str(folder))
#    try:
#        xbmcvfs.rmdir(str(path) + '/'+str(folder)+'/'+str(title))
#    except:
#        pass


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


###
# for audio files
###
elif mode == 'audio':

    title = getParameter('title')
    filename = getParameter('filename')
    folderID = getParameter('folder')
    if folderID == 'False':
            folderID = 'SEARCH'

    try:
        service
    except NameError:
        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30051), addon.getLocalizedString(30052))
        log(addon.getLocalizedString(30050)+ 'gdrive-login', True)
        xbmcplugin.endOfDirectory(plugin_handle)


    #force cache

    download = getSetting('always_cache', getParameter('download', False))
    play = getSetting('always_cache', getParameter('play', False))

    cache = getParameter('cache', False)
    if cache:
        download = False
        play = False

    filesize = getParameter('filesize')

    #cache folder (used for downloading)
    path = getSetting('cache_folder')


    playbackMedia = True
    #if we don't have the docid, search for the video for playback
    if (filename != ''):
        mediaFile = file.file(filename, title, '', service.MEDIA_TYPE_MUSIC, '','')
        mediaFolder = folder.folder(folderID,'')
        (mediaURLs,package) = service.getPlaybackCall(package=package.package(mediaFile,mediaFolder))
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
                        service.addDirectory(item.folder, contextType=contextType)
                    else:
                        options.append(item.file.title)
                        urls.append(service.addMediaFile(item, contextType=contextType))

            #search from STRM
            if contextType == '':

                ret = xbmcgui.Dialog().select(addon.getLocalizedString(30112), options)
                playbackURL = urls[ret]

                item = xbmcgui.ListItem(path=playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY))
                # for unknown reasons, for remote music, if Music is tagged as Music, it errors-out when playing back from "Music", doesn't happen when labeled "Video"
                item.setInfo( type="Video", infoLabels={ "Title": options[ret] } )
                if integratedPlayer:
                    player = gPlayer.gPlayer()
                    player.play(playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY), item)
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
                else:
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

        else:
            (mediaURLs,package) = service.getPlaybackCall(None,title=title)


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

        #download and play
        if download and play:
            service.downloadMediaFile(int(sys.argv[1]), playbackURL, str(title)+'.'+ str(playbackQuality), folderID, filename, fileSize)

        ###
        #right-menu context or STRM
        ##
        elif contextType == '':

            #download
            if download and not play:
                service.downloadMediaFile('',playbackURL, str(title)+'.'+ str(playbackQuality), folderID, filename, fileSize, force=True)

            #play cache
            elif cache:
#                xbmc.executebuiltin("XBMC.PlayMedia("+str(playbackPath)+")")
                player = gPlayer.gPlayer()
                player.play(str(playbackPath))

            #right-click play-original
            elif playOriginal:
                item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail, path=playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY))
                # for unknown reasons, for remote music, if Music is tagged as Music, it errors-out when playing back from "Music", doesn't happen when labeled "Video"
                item.setInfo( type="Video", infoLabels={ "Title": title } )
                if integratedPlayer:
                    player = gPlayer.gPlayer()
                    player.play(playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY), item)
                else:
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
            #STRM
            else:
                item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail, path=playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY))
                # for unknown reasons, for remote music, if Music is tagged as Music, it errors-out when playing back from "Music", doesn't happen when labeled "Video"
                item.setInfo( type="Video", infoLabels={ "Title": title } )
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


#                w = tvWindow.tvWindow("tvWindow.xml",addon.getAddonInfo('path'),"Default")
#                w.setPlayer(player)
#                w.doModal()


        # from within pictures mode, music won't be playable, force
        #direct playback from within plugin
        elif contextType == 'image' and cache:
                item = xbmcgui.ListItem(path=str(playbackPath))
                # local, not remote. "Music" is ok
                item.setInfo( type="Music", infoLabels={ "Title": title } )
                player = gPlayer.gPlayer()
                player.play(playbackPath, item)

        #direct playback from within plugin
        elif cache:
                item = xbmcgui.ListItem(path=str(playbackPath))
                # local, not remote. "Music" is ok
                item.setInfo( type="Music", infoLabels={ "Title": title } )
                if integratedPlayer:
                    player = gPlayer.gPlayer()
                    player.play(playbackPath, item)
                else:
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

        # from within pictures mode, music won't be playable, force
        #direct playback from within plugin
        elif contextType == 'image':
            item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail, path=playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY))
            # for unknown reasons, for remote music, if Music is tagged as Music, it errors-out when playing back from "Music", doesn't happen when labeled "Video"
            item.setInfo( type="Video", infoLabels={ "Title": title } )
            player = gPlayer.gPlayer()
            player.play(playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY), item)

        else:

            item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail, path=playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY))
            # for unknown reasons, for remote music, if Music is tagged as Music, it errors-out when playing back from "Music", doesn't happen when labeled "Video"
            item.setInfo( type="Video", infoLabels={ "Title": title } )
            if integratedPlayer:
                player = gPlayer.gPlayer()
                player.play(playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY), item)
            else:
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


###
# for video files
# force stream - play a video given its url
###
elif mode == 'streamurl':

    url = getParameter('url',0)
    title = getParameter('title')


    promptQuality = getSetting('prompt_quality', True)

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
            if integratedPlayer:
                player = gPlayer.gPlayer()
                player.play(playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY), item)
            else:
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

    else:
            xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30020),addon.getLocalizedString(30021))
            xbmc.log(addon.getAddonInfo('name') + ': ' + addon.getLocalizedString(20021), xbmc.LOGERROR)



###
# for video files - playback of video
# force stream - play a video given its url
###
#
# legacy (depreicated) - memorycachevideo [given title]
# legacy (depreicated) - play [given title]
# legacy (depreicated) - playvideo [given title]
# legacy (depreicated) - streamvideo [given title]
elif mode == 'video' or mode == 'search' or mode == 'play' or mode == 'memorycachevideo' or mode == 'playvideo' or mode == 'streamvideo':

    title = getParameter('title')
    srt = getParameter('srt', False)
    cc = getParameter('cc', False)
    filename = getParameter('filename')
    folderID = getParameter('folder')
    seek = getParameter('seek', 0)

    if seek:
        dialog = xbmcgui.Dialog()
        seek = dialog.numeric(2, 'Time to seek to', '00:00')
        for r in re.finditer('(\d+)\:(\d+)' ,seek, re.DOTALL):
            seekHours, seekMins = r.groups()
            seek = int(seekMins) + (int(seekHours)*60)

    try:
        service
    except NameError:
        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30051), addon.getLocalizedString(30052))
        log(addon.getLocalizedString(30050)+ 'gdrive-login', True)
        xbmcplugin.endOfDirectory(plugin_handle)


    promptQuality = getSetting('prompt_quality', True)
    playOriginal = getSetting('never_stream', getParameter('original', False))

    download = getSetting('always_cache', getParameter('download', False))
    play = getSetting('always_cache', getParameter('play', False))


    if mode == 'memorycachevideo':
        play = True
        download = True
    elif mode == 'playvideo':
        play = False
        download = False
        playOriginal = True

    cache = getParameter('cache', False)
    if cache:
            download = False
            play = False

    filesize = getParameter('filesize')

    path = getSetting('cache_folder')


    playbackMedia = True
    #if we don't have the docid, search for the video for playback
    if (filename != ''):
        mediaFile = file.file(filename, title, '', 0, '','')
        mediaFolder = folder.folder(folderID,'')
        (mediaURLs,package) = service.getPlaybackCall(package=package.package(mediaFile,mediaFolder))
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
                        service.addDirectory( item.folder, contextType=contextType)
                    else:
                        options.append(item.file.title)
                        urls.append(service.addMediaFile(item, contextType=contextType))

            if contextType == '':

                ret = xbmcgui.Dialog().select(addon.getLocalizedString(30112), options)
                playbackURL = urls[ret]

                item = xbmcgui.ListItem(path=playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY))
                item.setInfo( type="Video", infoLabels={ "Title": options[ret] , "Plot" : options[ret] } )
                if integratedPlayer:
                    player = gPlayer.gPlayer()
                    player.play(playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY), item)
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
                else:
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

        else:
            (mediaURLs,package) = service.getPlaybackCall(None,title=title)

    originalURL = ''
    if playbackMedia:

        SRTURL = ''
        srtpath = ''
        if srt:
            SRTURL = service.getSRT(title)
            if SRTURL != '':

                try:
                    srtpath = addon.getSetting('srt_folder')
                except:
                    srtpath = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30136), 'files','',False,False,'')
                    addon.setSetting('srt_folder', srtpath)

                if srtpath == '':
                    srtpath = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30136), 'files','',False,False,'')
                    addon.setSetting('srt_folder', srtpath)

                if srtpath != '':
                    srtpath = srtpath + '/subtitle.en.srt'
                    service.downloadPicture(SRTURL, srtpath)

        if cc:
            SRTURL,lang = service.getTTS(package.file.srtURL)

            if SRTURL != '':
                try:
                    srtpath = addon.getSetting('srt_folder')
                except:
                    srtpath = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30136), 'files','',False,False,'')
                    addon.setSetting('srt_folder', srtpath)

                if srtpath == '':
                    srtpath = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30136), 'files','',False,False,'')
                    addon.setSetting('srt_folder', srtpath)

                if srtpath != '':
                    srtpath = srtpath + '/subtitle.'+str(lang)+'.srt'
                    service.downloadTTS(SRTURL, srtpath)


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

        #download and play
        if download and play:
            service.downloadMediaFile(int(sys.argv[1]), playbackURL, str(title)+'.'+ str(playbackQuality), folderID, filename, fileSize)

        ###
        #right-menu context OR STRM
        ##
        elif contextType == '':

            #download only
            if download and not play:
                service.downloadMediaFile('',playbackURL, str(title)+'.'+ str(playbackQuality), folderID, filename, fileSize, force=True)

            elif cache:
                item = xbmcgui.ListItem(path=str(playbackPath))
                item.setInfo( type="Video", infoLabels={ "Title": title , "Plot" : title } )
                if integratedPlayer:
                    player = gPlayer.gPlayer()
                    player.play(playbackPath, item)
                else:
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

            #right-click play original
            elif playOriginal:
                item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail, path=playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY))

                item.setInfo( type="Video", infoLabels={ "Title": title , "Plot" : title } )

                player = gPlayer.gPlayer()
                player.play(playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY), item)

            elif srt or cc:
                item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail, path=playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY))

                item.setInfo( type="Video", infoLabels={ "Title": title , "Plot" : title } )
                player = gPlayer.gPlayer()
                player.play(playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY), item)

                while not (player.isPlaying()):
                        xbmc.sleep(1)

                if srtpath != '':
                        player.setSubtitles(srtpath.encode("utf-8"))

            elif seek:
                item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail, path=playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY))

                item.setInfo( type="Video", infoLabels={ "Title": title , "Plot" : title } )
                player = gPlayer.gPlayer()
                player.PlayStream(playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY), item, seek)


            #for STRM
            else :
                item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail, path=playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY))

                item.setInfo( type="Video", infoLabels={ "Title": title , "Plot" : title } )
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

                if seek > 0:
                    player = gPlayer.gPlayer()
                    player.PlayStream(playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY), item, seek)

#                    while not player.isPlaying(): #<== The should be    while self.isPlaying():
#                        print "LOOP"
#                        xbmc.sleep(2000)
#                    xbmc.sleep(1000)
#                    print "SEEK "+str(seek)
#                    player.seekTime(seek)

#                    while not (player.isPlaying()):
#                        xbmc.sleep(1)
#                    player.seekTime(seek)


#                player.seekTime(1000)
#                w = tvWindow.tvWindow("tvWindow.xml",addon.getAddonInfo('path'),"Default")
#                w.setPlayer(player)
#                w.doModal()

#                xbmc.executebuiltin("XBMC.PlayMedia("+str(playbackURL)+'|' + service.getHeadersEncoded(service.useWRITELY)+")")

        #direct-click
        elif cache:
                item = xbmcgui.ListItem(path=str(playbackPath))
                item.setInfo( type="Video", infoLabels={ "Title": title , "Plot" : title } )
                if integratedPlayer:
                    player = gPlayer.gPlayer()
                    player.play(playbackPath, item)
                else:
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

        #direct-click
        else:
                item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail, path=playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY))

                item.setInfo( type="Video", infoLabels={ "Title": title , "Plot" : title } )

                if integratedPlayer:
                    player = gPlayer.gPlayer()
                    player.play(playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY), item)

                    while not (player.isPlaying()):
                        xbmc.sleep(1)

                    if srtpath != '':

#                    xbmc.Player().setSubtitles(subtitle.encode("utf-8"))
                    #player.setSubtitles(subtitle.encode("utf-8"))
                        player.setSubtitles(srtpath.encode("utf-8"))


                    while (player.isPlaying()):
                        xbmc.sleep(3)


                else:
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
#                player = gPlayer.gPlayer()
#                player.play(playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY), item)
#                while not (player.isPlaying()):
#                    xbmc.sleep(1)

#                player.seekTime(1000)
#                w = tvWindow.tvWindow("tvWindow.xml",addon.getAddonInfo('path'),"Default")
#                w.setPlayer(player)
#                w.doModal()





# the parameter set for wise vs writely was detected as incorrect during this run; reset as necessary
try:
    if useWRITELY == True  and service.useWRITELY == False:
        addon.setSetting('force_writely','false')
    elif useWRITELY == False and service.useWRITELY == True:
        addon.setSetting('force_writely','true')
except:
    pass
xbmcplugin.endOfDirectory(plugin_handle)

