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

#*** testing - gdrive
from resources.lib import encryption
##**

# cloudservice - required python modules
import sys
import urllib
import cgi
import re
import os

# cloudservice - standard XBMC modules
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs

# global variables
PLUGIN_NAME = 'gdrive'
addon = xbmcaddon.Addon(id='plugin.video.gdrive')
#addon = xbmcaddon.Addon(id='plugin.video.gdrive-testing')

# cloudservice - helper methods
def log(msg, err=False):
    if err:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg, xbmc.LOGERROR)
    else:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg, xbmc.LOGDEBUG)

# cloudservice - helper methods
def parse_query(query):
    queries = cgi.parse_qs(query)
    q = {}
    for key, value in queries.items():
        q[key] = value[0]
    q['mode'] = q.get('mode', 'main')
    return q

# cloudservice - helper methods
def addMenu(url, title, img='', fanart='', total_items=0, instanceName=''):
#    listitem = xbmcgui.ListItem(decode(title), iconImage=img, thumbnailImage=img)
    listitem = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
    if not fanart:
        fanart = addon.getAddonInfo('path') + '/fanart.jpg'
    listitem.setProperty('fanart_image', fanart)

    # disallow play controls on menus
    listitem.setProperty('IsPlayable', 'false')


    if instanceName != '':
        cm=[]
        cm.append(( addon.getLocalizedString(30159), 'XBMC.RunPlugin('+PLUGIN_URL+ '?mode=delete&instance='+instanceName+')' ))
        listitem.addContextMenuItems(cm, True)



    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
                                isFolder=True, totalItems=total_items)

# cloudservice - helper methods
#http://stackoverflow.com/questions/1208916/decoding-html-entities-with-python/1208931#1208931
def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id))
    except:
        return id

# cloudservice - helper methods
def decode(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data).strip()

# cloudservice - helper methods
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

# cloudservice - helper methods
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

# cloudservice - helper methods
def numberOfAccounts(accountType):

    return 9
    count = 1
    max_count = int(getSetting(accountType+'_numaccounts',9))

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


addon_dir = xbmc.translatePath( addon.getAddonInfo('path') )


#import os
#sys.path.append(os.path.join( addon_dir, 'resources', 'lib' ) )

#*** testing - gdrive
from resources.lib import gdrive
from resources.lib import gdrive_api2
from resources.lib import tvWindow
from resources.lib import gSpreadsheets
##**

# cloudservice - standard modules
from resources.lib import cloudservice
from resources.lib import authorization
from resources.lib import folder
from resources.lib import file
from resources.lib import package
from resources.lib import mediaurl
from resources.lib import crashreport
from resources.lib import gPlayer
from resources.lib import settings
from resources.lib import cache


# cloudservice - standard debugging
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


# cloudservice - create settings module
settings = settings.settings(addon)

# retrieve settings
user_agent = getSetting('user_agent')
#obsolete, replace, revents audio from streaming
#if user_agent == 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)':
#    addon.setSetting('user_agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.38 Safari/532.0')



#*** old - gdrive
# hidden parameters which may not even be defined
useWRITELY = getSetting('force_writely')
##**

mode = getParameter('mode','main')

# make mode case-insensitive
mode = mode.lower()


log('plugin url: ' + PLUGIN_URL)
log('plugin queries: ' + str(plugin_queries))
log('plugin handle: ' + str(plugin_handle))


#*** old - gdrive
# allow for playback of public videos without authentication
if (mode == 'streamurl'):
  authenticate = False
else:
  authenticate = True
##**

instanceName = ''
try:
    instanceName = (plugin_queries['instance']).lower()
except:
    pass

# cloudservice - content type
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
        # cloudservice - sorting options
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')

      elif contextType == 'audio':
        if contentTypeDecider == 1:
            contentType = 4
        else:
            contentType = 3
        # cloudservice - sorting options
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TRACKNUM)

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

# cloudservice - sorting options
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_SIZE)

numberOfAccounts = numberOfAccounts(PLUGIN_NAME)


# cloudservice - utilities

if mode == 'dummy':
    xbmc.executebuiltin("XBMC.Container.Refresh")

# delete the configuration for the specified account
elif mode == 'delete':

    #*** old - needs to be re-written
    if instanceName != '':

        try:
            # gdrive specific ***
            addon.setSetting(instanceName + '_username', '')
            addon.setSetting(instanceName + '_code', '')
            addon.setSetting(instanceName + '_client_id', '')
            addon.setSetting(instanceName + '_client_secret', '')
            addon.setSetting(instanceName + '_url', '')
            addon.setSetting(instanceName + '_password', '')
            addon.setSetting(instanceName + '_passcode', '')
            addon.setSetting(instanceName + '_auth_access_token', '')
            addon.setSetting(instanceName + '_auth_refresh_token', '')
            # ***
            xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30158))
        except:
            #error: instance doesn't exist
            pass
    xbmc.executebuiltin("XBMC.Container.Refresh")


# enroll a new account
elif mode == 'enroll':


        invokedUsername = getParameter('username')
        code = getParameter('code')

        count = 1
        loop = True
        while loop:
            instanceName = PLUGIN_NAME+str(count)
            try:
                username = getSetting(instanceName+'_username')
                if username == invokedUsername:
                    addon.setSetting(instanceName + '_type', str(1))
                    addon.setSetting(instanceName + '_code', str(code))
                    addon.setSetting(instanceName + '_username', str(invokedUsername))
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

            if count == numberOfAccounts:
                #fallback on first defined account
                addon.setSetting(instanceName + '_type', str(1))
                addon.setSetting(instanceName + '_code', code)
                addon.setSetting(instanceName + '_username', invokedUsername)
                xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30118), invokedUsername)
                loop = False
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
        type = int(getParameter('type', 0))

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
                loop = True
                while loop:
                    instanceName = PLUGIN_NAME+str(count)
                    try:
                        username = getSetting(instanceName+'_username')
                        if username == invokedUsername:

                            #let's log in
                            if ( int(getSetting(instanceName+'_type',0))==0):
                                service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent, settings)
                            else:
                                service = gdrive_api2.gdrive(PLUGIN_URL,addon,instanceName, user_agent, settings)

                            loop = False
                    except:
                        service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
                        break

                    if count == numberOfAccounts:
                        try:
                            service
                        except NameError:
                            #fallback on first defined account
                            if ( int(getSetting(instanceName+'_type',0))==0):
                                service = gdrive.gdrive(PLUGIN_URL,addon,PLUGIN_NAME+'1', user_agent, settings)
                            else:
                                service = gdrive_api2.gdrive(PLUGIN_URL,addon,PLUGIN_NAME+'1', user_agent, settings)
                        break
                    count = count + 1

                service.buildSTRM(path + '/'+title,folderID, contentType=contentType, pDialog=pDialog)

            elif filename != '':
                            values = {'title': title, 'filename': filename, 'username': invokedUsername}
                            if type == 1:
                                url = PLUGIN_URL+'?mode=audio&'+urllib.urlencode(values)
                            else:
                                url = PLUGIN_URL+'?mode=video&'+urllib.urlencode(values)

                            filename = path + '/' + title+'.strm'
                            strmFile = xbmcvfs.File(filename, "w")
                            strmFile.write(url+'\n')
                            strmFile.close()

            else:

                count = 1
                while True:
                    instanceName = PLUGIN_NAME+str(count)
                    username = getSetting(instanceName+'_username')

                    if username != '' and username == invokedUsername:
                        if ( int(getSetting(instanceName+'_type',0))==0):
                                service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent, settings)
                        else:
                            service = gdrive_api2.gdrive(PLUGIN_URL,addon,instanceName, user_agent, settings)

                        service.buildSTRM(path + '/'+username, contentType=contentType, pDialog=pDialog)

                    if count == numberOfAccounts:
                        #fallback on first defined account
                        try:
                            service
                        except NameError:
                            #fallback on first defined account
                            if ( int(getSetting(instanceName+'_type',0))==0):
                                    service = gdrive.gdrive(PLUGIN_URL,addon,PLUGIN_NAME+'1', user_agent, settings)
                            else:
                                service = gdrive_api2.gdrive(PLUGIN_URL,addon,PLUGIN_NAME+'1', user_agent, settings)
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



invokedUsername = getParameter('username')

# show list of services
if mode == 'delete' or mode == 'dummy':
            count = 1

elif numberOfAccounts > 1 and instanceName == '' and invokedUsername == '' and mode == 'main':
        mode = ''
        count = 1
        while True:
            instanceName = PLUGIN_NAME+str(count)
            try:
                username = getSetting(instanceName+'_username')
                if username != '':
                    addMenu(PLUGIN_URL+'?mode=main&content_type='+str(contextType)+'&instance='+str(instanceName),username, instanceName=instanceName)

            except:
                pass
            if count == numberOfAccounts:
                break
            count = count + 1

#        spreadshetModule = getSetting('library', False)
#        libraryAccount = getSetting('library_account')

 #       if spreadshetModule:
 #           addMenu(PLUGIN_URL+'?mode=kiosk&content_type='+str(contextType)+'&instance='+PLUGIN_NAME+str(libraryAccount),'[kiosk mode]')

elif instanceName == '' and invokedUsername == '' and numberOfAccounts == 1:

        count = 1
        options = []
        accounts = []

        for count in range (1, numberOfAccounts+1):
            instanceName = PLUGIN_NAME+str(count)
            try:
                username = getSetting(instanceName+'_username')
                if username != '':
                    options.append(username)
                    accounts.append(instanceName)

                if username != '':

                    #let's log in
                    if ( int(getSetting(instanceName+'_type',0))==0):
                            service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent, settings)
                    else:
                        service = gdrive_api2.gdrive(PLUGIN_URL,addon,instanceName, user_agent, settings)
                    break
            except:
                service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
                break

        try:
                    service
        except NameError:
                    ret = xbmcgui.Dialog().select(addon.getLocalizedString(30120), options)

                    #fallback on first defined account
                    if ( int(getSetting(instanceName+'_type',0))==0):
                            service = gdrive.gdrive(PLUGIN_URL,addon,accounts[ret], user_agent, settings)
                    else:
                        service = gdrive_api2.gdrive(PLUGIN_URL,addon,accounts[ret], user_agent, settings)


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
                service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent, settings)
        else:
            service = gdrive_api2.gdrive(PLUGIN_URL,addon,instanceName, user_agent, settings)

    # show entries of a single account (such as folder)
elif instanceName != '':

        #let's log in
        if ( int(getSetting(instanceName+'_type',0))==0):
                service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent, settings)
        else:
            service = gdrive_api2.gdrive(PLUGIN_URL,addon,instanceName, user_agent, settings)


elif invokedUsername != '':

        options = []
        accounts = []
        for count in range (1, numberOfAccounts+1):
            instanceName = PLUGIN_NAME+str(count)
            try:
                username = getSetting(instanceName+'_username')
                if username != '':
                    options.append(username)
                    accounts.append(instanceName)

                if username == invokedUsername:


                    #let's log in
                    if ( int(getSetting(instanceName+'_type',0))==0):
                        service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent, settings)
                    else:
                        service = gdrive_api2.gdrive(PLUGIN_URL,addon,instanceName, user_agent, settings)
                    break
            except:
                service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)


        #fallback on first defined account
        try:
                    service
        except NameError:
                    ret = xbmcgui.Dialog().select(addon.getLocalizedString(30120), options)

                    #fallback on first defined account
                    if ( int(getSetting(instanceName+'_type',0))==0):
                        service = gdrive.gdrive(PLUGIN_URL,addon,accounts[ret], user_agent, settings)
                    else:
                        service = gdrive_api2.gdrive(PLUGIN_URL,addon,accounts[ret], user_agent, settings)
#prompt before playback
else:

        options = []
        accounts = []
        for count in range (1, numberOfAccounts+1):
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
            service = gdrive_api2.gdrive(PLUGIN_URL,addon,'', user_agent, settings, authenticate=False)
        elif ( int(getSetting(instanceName+'_type',0))==0):
            service = gdrive.gdrive(PLUGIN_URL,addon,accounts[ret], user_agent, settings)
        else:
            service = gdrive_api2.gdrive(PLUGIN_URL,addon,accounts[ret], user_agent, settings)

# override playback
try:
    if settings.integratedPlayer:
        service.integratedPlayer = True
except: pass



#if mode == 'main':
#    addMenu(PLUGIN_URL+'?mode=options','<< '+addon.getLocalizedString(30043)+' >>')


#dump a list of videos available to play
if mode == 'main' or mode == 'index':

    folderName = getParameter('folder', False)

    #** testing - gdrive specific
    try:
      decrypt = plugin_queries['decrypt']
      service.setDecrypt()
      log('decrypt ')
    except:
      decrypt = False
    ##**

    # treat as an encrypted folder?
    encfs = getParameter('encfs', False)
    encfs_target = getSetting('encfs_target')


    # display option for all Videos/Music/Photos, across gdrive
    #** gdrive specific
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
    ##**

        if encfs_target != '':
                service.addDirectory(None, contextType, localPath=encfs_target)

    if encfs_target != '' and encfs == False and folderName != False and folderName != '':
                    service.addDirectory(folder.folder(folderName,'[decrypted]'), contextType, encfs=True)

    # cloudservice - validate service
    try:
        service
    except NameError:
        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30051), addon.getLocalizedString(30052))
        log(addon.getLocalizedString(30050)+ 'gdrive-login', True)
        xbmcplugin.endOfDirectory(plugin_handle)

    #if encrypted, get everything(as encrypted files will be of type application/ostream)
    if encfs:
        encfs_source = getSetting('encfs_source')
        encfs_target = getSetting('encfs_target')
        encfs_inode = int(getSetting('encfs_inode', 0))

        mediaItems = service.getMediaList(folderName,contentType=8)

        if mediaItems:
            dirListINodes = {}
            fileListINodes = {}
            for item in mediaItems:

                    if item.file is None:
                        xbmcvfs.mkdir(encfs_source + '/' + str(item.folder.title))
                        if encfs_inode == 0:
                            dirListINodes[(str(xbmcvfs.Stat(encfs_source + '/' + str(item.folder.title)).st_ino()))] = item.folder
                        else:
                            dirListINodes[(str(xbmcvfs.Stat(encfs_source + '/' + str(item.folder.title)).st_ctime()))] = item.folder
                        #service.addDirectory(item.folder, contextType=contextType,  encfs=True)
                    else:
                        xbmcvfs.mkdir(encfs_source + '/' + str(item.file.title))
                        if encfs_inode == 0:
                            fileListINodes[(str(xbmcvfs.Stat(encfs_source + '/' + str(item.file.title)).st_ino()))] = item
                        else:
                            fileListINodes[(str(xbmcvfs.Stat(encfs_source + '/' + str(item.file.title)).st_ctime()))] = item
                        #service.addMediaFile(item, contextType=contextType)
                    if encfs_inode > 0:
                            xbmc.sleep(1000)

            dirs, files = xbmcvfs.listdir(encfs_target)
            for dir in dirs:
                index = ''
                if encfs_inode == 0:
                    index = str(xbmcvfs.Stat(encfs_target + '/' + dir).st_ino())
                else:
                    index = str(xbmcvfs.Stat(encfs_target + '/' + dir).st_ctime())
                if index in dirListINodes.keys():
                    xbmcvfs.rmdir(encfs_target + '/' + dir)
                    dirListINodes[index].title = dir + ' [' +dirListINodes[index].title+ ']'
                    service.addDirectory(dirListINodes[index], contextType=contextType,  encfs=True)
                elif index in fileListINodes.keys():
                    xbmcvfs.rmdir(encfs_target + '/' + dir)
                    fileListINodes[index].file.decryptedTitle = dir
                    service.addMediaFile(fileListINodes[index], contextType=contextType, encfs=True)



    else:
        mediaItems = service.getMediaList(folderName,contentType=contentType)

        if mediaItems:
            for item in mediaItems:

                    if item.file is None:
                        service.addDirectory(item.folder, contextType=contextType)
                    else:
                        service.addMediaFile(item, contextType=contextType)

    service.updateAuthorization(addon)

#** testing - gdrive
elif mode == 'kiosk':

    spreadshetModule = getSetting('library', False)


    if spreadshetModule:
            gSpreadsheet = gSpreadsheets.gSpreadsheets(service,addon, user_agent)
            service.gSpreadsheet = gSpreadsheet
            spreadsheets = gSpreadsheet.getSpreadsheetList()


            channels = []
            for title in spreadsheets.iterkeys():
                if title == 'TVShows':
                  worksheets = gSpreadsheet.getSpreadsheetWorksheets(spreadsheets[title])

                  if 0:
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
                            player.setService(service)
                            player.setContent(episodes)
                            player.setWorksheet(worksheets['data'])
                            player.next()
                            while not player.isExit:
                                xbmc.sleep(5000)
                  else:
                    for worksheet in worksheets.iterkeys():
                        if worksheet == 'db':
                            episodes = gSpreadsheet.getMedia(worksheets[worksheet], service.getRootID())
                            player = gPlayer.gPlayer()
                            player.setService(service)
#                            player.setContent(episodes)
                            player.setWorksheet(worksheets['db'])
                            player.PlayStream('plugin://plugin.video.gdrive-testing/?mode=video&instance='+str(service.instanceName)+'&title='+episodes[0][3], None,episodes[0][7],episodes[0][2])
                            #player.next()
                            while not player.isExit:
                                player.saveTime()
                                xbmc.sleep(5000)

##**

elif mode == 'photo':

    title = getParameter('title',0)
    docid = getParameter('filename')
    folder = getParameter('folder',0)

    encfs = getParameter('encfs', False)

    if encfs:
        encfs_source = getSetting('encfs_source')
        encfs_target = getSetting('encfs_target')
        encfs_inode = int(getSetting('encfs_inode', 0))

        if (not xbmcvfs.exists(str(encfs_target) + '/'+str(folder) + '/')):
            xbmcvfs.mkdir(str(encfs_target) + '/'+str(folder))

        folderINode = ''
        if encfs_inode == 0:
            folderINode = str(xbmcvfs.Stat(encfs_target + '/' + str(folder)).st_ino())
        else:
            folderINode = str(xbmcvfs.Stat(encfs_target + '/' + str(folder)).st_ctime())


        dirs, filesx = xbmcvfs.listdir(encfs_source)
        for dir in dirs:
            index = ''
            if encfs_inode == 0:
                index = str(xbmcvfs.Stat(encfs_source + '/' + dir).st_ino())
            else:
                index = str(xbmcvfs.Stat(encfs_source + '/' + dir).st_ctime())

            if index == folderINode:
                # don't redownload if present already
                if (not xbmcvfs.exists(str(encfs_source) + '/'+str(dir)+'/'+str(title))):
                    url = service.getDownloadURL(docid)
                    service.downloadPicture(url, str(encfs_source) + '/'+str(dir) + '/'+str(title))
                fileINode = ''
                if encfs_inode ==0:
                    fileINode = str(xbmcvfs.Stat(str(encfs_source) + '/'+str(dir)+'/'+str(title)).st_ino())
                else:
                    fileINode = str(xbmcvfs.Stat(str(encfs_source) + '/'+str(dir)+'/'+str(title)).st_ctime())

                dirsx, files = xbmcvfs.listdir(encfs_target + '/' + str(folder))
                for file in files:
                    index = ''
                    if encfs_inode ==0:
                        index = str(xbmcvfs.Stat(encfs_target + '/' + str(folder) + '/' + file).st_ino())
                    else:
                        index = str(xbmcvfs.Stat(encfs_target + '/' + str(folder) + '/' + file).st_ctime())
                    if index == fileINode:
                        xbmc.executebuiltin("XBMC.ShowPicture("+encfs_target + '/' + str(folder) + '/' + file+")")
                        item = xbmcgui.ListItem(path=encfs_target + '/' + str(folder) + '/' + file)
                        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, item)

    else:
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
                service.downloadGeneralFile('',  item.mediaurl, item,  force=True, encfs=encfs, folderName=folderName)
#            elif item.folder is not None:
#                # create path if doesn't exist
#                if (not xbmcvfs.exists(str(path) + '/'+str(folder) + '/')):
#                    xbmcvfs.mkdir(str(path) + '/'+str(folder))

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


    encfs = getParameter('encfs', False)

    if encfs:
        encfs_inode = int(getSetting('encfs_inode', 0))

        encfs_source = getSetting('encfs_source')
        encfs_target = getSetting('encfs_target')

        if (not xbmcvfs.exists(str(encfs_target) + '/'+str(folder) + '/')):
            xbmcvfs.mkdir(str(encfs_target) + '/'+str(folder))

        folderINode = ''
        if encfs_inode == 0:
            folderINode = str(xbmcvfs.Stat(encfs_target + '/' + str(folder)).st_ino())
        else:
            folderINode = str(xbmcvfs.Stat(encfs_target + '/' + str(folder)).st_ctime())

        mediaItems = service.getMediaList(folderName=folder, contentType=8)

        if mediaItems:

            dirs, filesx = xbmcvfs.listdir(encfs_source)
            for dir in dirs:
                index = ''
                if encfs_inode == 0:
                    index = str(xbmcvfs.Stat(encfs_source + '/' + dir).st_ino())
                else:
                    index = str(xbmcvfs.Stat(encfs_source + '/' + dir).st_ctime())

                if index == folderINode:

                    progress = xbmcgui.DialogProgressBG()
                    progress.create(addon.getLocalizedString(30035), 'Preparing list...')
                    count=0
                    for item in mediaItems:
                        if item.file is not None:
                            count = count + 1;
                            progress.update((int)(float(count)/len(mediaItems)*100),addon.getLocalizedString(30035), item.file.title)
                            if (not xbmcvfs.exists(str(encfs_source) + '/'+str(dir)+'/'+str(item.file.title))):
                                service.downloadPicture(item.mediaurl.url,str(encfs_source) + '/'+str(dir)+ '/'+str(item.file.title))
                                if encfs_inode > 0:
                                    xbmc.sleep(100)


                    progress.close()
                    xbmc.executebuiltin("XBMC.SlideShow("+str(encfs_target) + '/'+str(folder)+"/)")

    else:
        path = getSetting('photo_folder')

        if not xbmcvfs.exists(path):
            path = ''


        while path == '':
            path = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30038), 'files','',False,False,'')
            if not xbmcvfs.exists(path):
                path = ''
            else:
                addon.setSetting('photo_folder', path)

            # create path if doesn't exist
            if (not xbmcvfs.exists(str(path) + '/'+str(folder) + '/')):
                xbmcvfs.mkdir(str(path) + '/'+str(folder))

            mediaItems = service.getMediaList(folderName=folder, contentType=5)


            if mediaItems:
                progress = xbmcgui.DialogProgressBG()
                progress.create(addon.getLocalizedString(30035), 'Preparing list...')
                count=0
                for item in mediaItems:
                    if item.file is not None:
                        count = count + 1;
                        progress.update((int)(float(count)/len(mediaItems)*100),addon.getLocalizedString(30035), item.file.title)
                        service.downloadPicture(item.mediaurl.url,str(path) + '/'+str(folder)+ '/'+item.file.title)
                        #xbmc.executebuiltin("XBMC.SlideShow("+str(path) + '/'+str(folder)+"/)")
                progress.close()
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
                if settings.integratedPlayer:
                    player = gPlayer.gPlayer()
                    player.play(playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY), item)
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
                else:
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

        else:
            (mediaURLs,package) = service.getPlaybackCall(None,title=title)


    if playbackMedia:
        cache = cache.cache(package)
        service.cache = cache

        (localResolutions,localFiles) = service.cache.getFiles(service)
        if len(localFiles) > 0:
            mediaURL = mediaurl.mediaurl(str(localFiles[0]), 'offline', 0, 0)
        else:
            mediaURL = mediaURLs[0]
            if not settings.download:
                mediaURL.url =  mediaURL.url +'|' + service.getHeadersEncoded(service.useWRITELY)

        playbackPlayer = settings.integratedPlayer

        #download and play
        if settings.download and settings.play:
            service.downloadMediaFile(int(sys.argv[1]), mediaURL, package)
            playbackMedia = False
        ###
        #right-menu context or STRM
        ##
        elif contextType == '':

            #download
            if settings.download and not settings.play:
                service.downloadMediaFile('',mediaURL, package, force=True)
                playbackMedia = False

            # for STRM (force resolve) -- resolve-only
            elif settings.username != '':
                playbackPlayer = False

            else:
                playbackPlayer = True


        # from within pictures mode, music won't be playable, force
        #direct playback from within plugin
        elif contextType == 'image' and settings.cache:
                item = xbmcgui.ListItem(path=str(playbackPath))
                # local, not remote. "Music" is ok
                item.setInfo( type="Music", infoLabels={ "Title": title } )
                player = gPlayer.gPlayer()
                player.play(mediaURL.url, item)
                playbackMedia = False

        # from within pictures mode, music won't be playable, force
        #direct playback from within plugin
        elif contextType == 'image':
            item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail, path=mediaURL.url)
            # for unknown reasons, for remote music, if Music is tagged as Music, it errors-out when playing back from "Music", doesn't happen when labeled "Video"
            item.setInfo( type="Video", infoLabels={ "Title": title } )

            player = gPlayer.gPlayer()
            player.play(mediaURL.url, item)
            playbackMedia = False


        if playbackMedia:

                item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail, path=mediaURL.url)

                item.setInfo( type="Video", infoLabels={ "Title": package.file.title} )
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

                if playbackPlayer:

#                    item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
#                                thumbnailImage=package.file.thumbnail)#, path=playbackPath+'|' + service.getHeadersEncoded(service.useWRITELY))
                    # for unknown reasons, for remote music, if Music is tagged as Music, it errors-out when playing back from "Music", doesn't happen when labeled "Video"
#                    item.setInfo( type="Video", infoLabels={ "Title": package.file.title , "Plot" : package.file.title } )
                    #xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

                    player = gPlayer.gPlayer()
                    #player.play(playbackPath, item)
                    player.PlayStream(mediaURL.url, item, 0)

 #               else:

#                    item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
   #                             thumbnailImage=package.file.thumbnail, path=mediaURL.url)
                    # for unknown reasons, for remote music, if Music is tagged as Music, it errors-out when playing back from "Music", doesn't happen when labeled "Video"
 #                   item.setInfo( type="Video", infoLabels={ "Title": package.file.title , "Plot" : package.file.title } )
  #                  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


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
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

            if settings.integratedPlayer:
                player = gPlayer.gPlayer()
                player.play(playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY), item)
#            else:
#                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

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

    title = getParameter('title') #file title
    filename = getParameter('filename') #file ID
    folderID = getParameter('folder') #folder ID

    settings.setVideoParameters()

    seek = 0
    if settings.seek:
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

    #settings.setCacheParameters()

    if mode == 'memorycachevideo':
        settings.play = True
        settings.download = True
    elif mode == 'playvideo':
        settings.play = False
        settings.download = False
        settings.playOriginal = True

    if settings.cache:
            settings.download = False
            settings.play = False


    playbackMedia = True

    # file ID provided
    if (filename != ''):
        mediaFile = file.file(filename, title, '', 0, '','')
        mediaFolder = folder.folder(folderID,'')
        (mediaURLs,package) = service.getPlaybackCall(package=package.package(mediaFile,mediaFolder))
    # search
    elif mode == 'search':

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
                playbackPath = urls[ret]

                item = xbmcgui.ListItem(path=playbackPath+'|' + service.getHeadersEncoded(service.useWRITELY))
                item.setInfo( type="Video", infoLabels={ "Title": options[ret] , "Plot" : options[ret] } )
                if settings.integratedPlayer:
                    player = gPlayer.gPlayer()
                    player.play(playbackPath+'|' + service.getHeadersEncoded(service.useWRITELY), item)
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
                else:
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
    # folder only
    elif folderID != '' and title == '':
        mediaItems = service.getMediaList(folderName=folderID, contentType=contentType)
        if mediaItems:
            if contextType == '':
                player = gPlayer.gPlayer()
                player.setMedia(mediaItems)
                player.playLgist(service)
                playbackMedia = False
    # title provided
    else:
            (mediaURLs,package) = service.getPlaybackCall(None,title=title)


    originalURL = ''
    if playbackMedia:
        cache = cache.cache(package)
        service.cache = cache
        package.file.thumbnail = cache.setThumbnail(service)

       # SRTURL = ''
        srtpath = ''
        if settings.srt and service.protocol == 2:
            cache.setSRT(service)

        # download closed-captions
        if settings.cc and service.protocol == 2:
            cache.setCC(service)


        mediaURL = service.getMediaSelection(mediaURLs, folderID, filename)
        playbackPlayer = settings.integratedPlayer
        #mediaURL.url = mediaURL.url +'|' + service.getHeadersEncoded(service.useWRITELY)

        #download and play
        if not mediaURL.offline and settings.download and settings.play:
#            service.downloadMediaFile(int(sys.argv[1]), playbackPath, str(title)+'.'+ str(playbackQuality), folderID, filename, fileSize)
            service.downloadMediaFile(int(sys.argv[1]), mediaURL, package)
            playbackMedia = False

        ###
        #right-menu context OR STRM
        ##
        elif contextType == '':

            # right-click force download only
            if not mediaURL.offline and settings.download and not settings.play:
#                service.downloadMediaFile('',playbackPath, str(title)+'.'+ str(playbackQuality), folderID, filename, fileSize, force=True)
                service.downloadMediaFile('',mediaURL, package, force=True)
                playbackMedia = False

            # for STRM (force resolve) -- resolve-only
            elif settings.username != '':
                playbackPlayer = False

            # right-click play original, srt, caption, seek
            elif settings.playOriginal or settings.srt or settings.cc or settings.seek:
                playbackPlayer = True

            # TESTING
            elif settings.resume:
                playbackPlayer = False

                spreadshetModule = getSetting('library', False)
                spreadshetName = getSetting('library_filename', 'TVShows')

                media = {}
                if spreadshetModule:
                    try:
                        gSpreadsheet = gSpreadsheets.gSpreadsheets(service,addon, user_agent)
                        service.gSpreadsheet = gSpreadsheet
                        spreadsheets = gSpreadsheet.getSpreadsheetList()
                    except:
                        spreadshetModule = False

                    if spreadshetModule:
                      for title in spreadsheets.iterkeys():
                        if title == spreadshetName:
                            worksheets = gSpreadsheet.getSpreadsheetWorksheets(spreadsheets[title])

                            for worksheet in worksheets.iterkeys():
                                if worksheet == 'db':
                                    media = gSpreadsheet.getMedia(worksheets[worksheet], fileID=package.file.id)
                                    item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                                            thumbnailImage=package.file.thumbnail)

                                    item.setInfo( type="Video", infoLabels={ "Title": package.file.title , "Plot" : package.file.title } )
                                    player = gPlayer.gPlayer()
                                    player.setService(service)
                                    player.setWorksheet(worksheets['db'])
                                    if len(media) == 0:
                                        player.PlayStream(mediaURL.url, item, 0, package)
                                    else:
                                        player.PlayStream(mediaURL.url, item,media[0][7],package)
                                    while not player.isExit:
                                        player.saveTime()
                                        xbmc.sleep(5000)
                playbackMedia = False
            elif mediaURL.offline:
                playbackMedia = True



        if playbackMedia:

                item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail, path=mediaURL.url)

                item.setInfo( type="Video", infoLabels={ "Title": package.file.title , "Plot" : package.file.title } )
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

                if playbackPlayer:

                    item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail)#, path=playbackPath+'|' + service.getHeadersEncoded(service.useWRITELY))

                    item.setInfo( type="Video", infoLabels={ "Title": package.file.title , "Plot" : package.file.title } )
                    #xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

                    player = gPlayer.gPlayer()
                    #player.play(playbackPath, item)
                    if seek > 0:
                        player.PlayStream(mediaURL.url, item, seek, package=package)
                    elif float(package.file.resume) > 0:
                        player.PlayStream(mediaURL.url, item, package.file.resume, package=package)
                    else:
                        player.PlayStream(mediaURL.url, item, 0, package=package)


                    #load any cc or srt
                    if (settings.srt or settings.cc) and  service.protocol == 2:
                        while not (player.isPlaying()):
                            xbmc.sleep(1000)

                        files = cache.getSRT(service)
                        for file in files:
                            if file != '':
                                try:
                                    file = file.decode('unicode-escape')
                                    file = file.encode('utf-8')
                                except:
                                    pass
                                player.setSubtitles(file)

                    while not player.isExit:
                        player.saveTime()
                        xbmc.sleep(5000)
                    #service.setProperty(package.file.id,'playcount', 1)

                    # save new resume point
                    if service.protocol == 2 and player.time > package.file.resume:
                        service.setProperty(package.file.id,'resume', player.time)

                else:

                    #need a player?
#                    if seek > 0 or package.file.resume > 0 or settings.srt or settings.cc:

                    player = gPlayer.gPlayer()
                    player.setService(service)
                    # need to seek?
                    if seek > 0:
                        player.PlayStream(mediaURL.url, item, seek, startPlayback=False, package=package)
                    elif float(package.file.resume) > 0:
                        player.PlayStream(mediaURL.url, item, package.file.resume, startPlayback=False, package=package)
                    else:
                        player.PlayStream(mediaURL.url, item, 0, startPlayback=False, package=package)

                    # load captions
                    if  (settings.srt or settings.cc) and service.protocol == 2:
                        while not (player.isPlaying()):
                            xbmc.sleep(1000)

                        files = cache.getSRT(service)
                        for file in files:
                            if file != '':
                                try:
                                    file = file.decode('unicode-escape')
                                    file = file.encode('utf-8')
                                except:
                                    pass
                                player.setSubtitles(file)


                    while not player.isExit:
                        player.saveTime()
                        xbmc.sleep(5000)
                    #service.setProperty(package.file.id,'playcount', 1)

                    # save new resume point
                    if service.protocol == 2 and player.time > package.file.resume:
                        service.setProperty(package.file.id,'resume', player.time)

#                player = gPlayer.gPlayer()
#                player.play(playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY), item)
#                while not (player.isPlaying()):
#                    xbmc.sleep(1)

#                player.seekTime(1000)
#                w = tvWindow.tvWindow("tvWindow.xml",addon.getAddonInfo('path'),"Default")
#                w.setPlayer(player)
#                w.doModal()

#                player.seekTime(1000)
#                w = tvWindow.tvWindow("tvWindow.xml",addon.getAddonInfo('path'),"Default")
#                w.setPlayer(player)
#                w.doModal()

#                xbmc.executebuiltin("XBMC.PlayMedia("+str(playbackPath)+'|' + service.getHeadersEncoded(service.useWRITELY)+")")




# the parameter set for wise vs writely was detected as incorrect during this run; reset as necessary
try:
    if useWRITELY == True  and service.useWRITELY == False:
        addon.setSetting('force_writely','false')
    elif useWRITELY == False and service.useWRITELY == True:
        addon.setSetting('force_writely','true')
except:
    pass
xbmcplugin.endOfDirectory(plugin_handle)

