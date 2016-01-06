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
import re

# cloudservice - standard XBMC modules
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs

# common routines
from resources.lib import kodi_common



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


# global variables
PLUGIN_NAME = 'gdrive'
addon = xbmcaddon.Addon(id='plugin.video.gdrive')
#addon = xbmcaddon.Addon(id='plugin.video.gdrive-testing')

#global variables
PLUGIN_URL = sys.argv[0]
plugin_handle = int(sys.argv[1])
plugin_queries = settings.parse_query(sys.argv[2][1:])


addon_dir = xbmc.translatePath( addon.getAddonInfo('path') )


kodi_common.debugger()


# cloudservice - create settings module
settings = settings.settings(addon)

# retrieve settings
user_agent = settings.getSetting('user_agent')
#obsolete, replace, revents audio from streaming
#if user_agent == 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)':
#    addon.setSetting('user_agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.38 Safari/532.0')



mode = settings.getParameter('mode','main')

# make mode case-insensitive
mode = mode.lower()


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
contextType = settings.getParameter('content_type')

#support encfs?
encfs = settings.getParameter('encfs', False)

contentType = kodi_common.getContentType(contextType,encfs)


# cloudservice - sorting options
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_SIZE)

numberOfAccounts = cloudservice.numberOfAccounts(PLUGIN_NAME)

# cloudservice - utilities
###

if mode == 'dummy' or mode == 'delete' or mode == 'enroll':

    cloudservice.accountActions(addon, PLUGIN_NAME, mode, instanceName, numberOfAccounts)

#create strm files
elif mode == 'buildstrm':

    silent = settings.getParameter('silent', settings.getSetting('strm_silent',0))
    if silent == '':
        silent = 0

    try:
        path = settings.getSetting('strm_path')
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

        url = settings.getParameter('streamurl')
        url = re.sub('---', '&', url)
        title = settings.getParameter('title')
        type = int(settings.getParameter('type', 0))

        if url != '':

                filename = path + '/' + title+'.strm'
                strmFile = xbmcvfs.File(filename, "w")

                strmFile.write(url+'\n')
                strmFile.close()
        else:

            folderID = settings.getParameter('folder')
            filename = settings.getParameter('filename')
            title = settings.getParameter('title')
            invokedUsername = settings.getParameter('username')

            if folderID != '':

                count = 1
                loop = True
                while loop:
                    instanceName = PLUGIN_NAME+str(count)
                    try:
                        username = settings.getSetting(instanceName+'_username')
                        if username == invokedUsername:

                            #let's log in
                            if ( int(settings.getSetting(instanceName+'_type',0))==0):
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
                            if ( int(settings.getSetting(instanceName+'_type',0))==0):
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
                    username = settings.getSetting(instanceName+'_username')

                    if username != '' and username == invokedUsername:
                        if ( int(settings.getSetting(instanceName+'_type',0))==0):
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
                            if ( int(settings.getSetting(instanceName+'_type',0))==0):
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

###


invokedUsername = settings.getParameter('username')
instanceName = cloudservice.getInstanceName(addon, PLUGIN_NAME, mode, instanceName, invokedUsername, numberOfAccounts, contextType)

service = None
if instanceName is None and (mode == 'index' or mode == 'main'):
    service = None
elif instanceName is None:
    service = gdrive_api2.gdrive(PLUGIN_URL,addon,'', user_agent, settings, authenticate=False)
elif int(settings.getSetting(instanceName+'_type',0))==0 :
    service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent, settings)
else:
    service = gdrive_api2.gdrive(PLUGIN_URL,addon,instanceName, user_agent, settings)

# override playback
try:
    if settings.integratedPlayer:
        service.integratedPlayer = True
except: pass


# options menu
#if mode == 'main':
#    addMenu(PLUGIN_URL+'?mode=options','<< '+addon.getLocalizedString(30043)+' >>')

if service is None:

    xbmcplugin.endOfDirectory(plugin_handle)

#dump a list of videos available to play
elif mode == 'main' or mode == 'index':

    folderName = settings.getParameter('folder', False)

    #** testing - gdrive specific
    try:
      decrypt = plugin_queries['decrypt']
      service.setDecrypt()
    except:
      decrypt = False
    ##**

    # treat as an encrypted folder?
#    encfs = settings.getParameter('encfs', False)
    encfs_target = settings.getSetting('encfs_target')


    # display option for all Videos/Music/Photos, across gdrive
    #** gdrive specific
    if mode == 'main':
        if contentType in (2,4,7):
            kodi_common.addMenu(PLUGIN_URL+'?mode=index&folder=ALL&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30030)+']')
        elif contentType == 1:
            kodi_common.addMenu(PLUGIN_URL+'?mode=index&folder=VIDEOMUSIC&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30031)+']')
        elif contentType == 0:
            kodi_common.addMenu(PLUGIN_URL+'?mode=index&folder=VIDEO&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30025)+']')
        elif contentType == 3:
            kodi_common.addMenu(PLUGIN_URL+'?mode=index&folder=MUSIC&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30094)+']')
        elif contentType == 5:
            kodi_common.addMenu(PLUGIN_URL+'?mode=index&folder=PHOTO&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30034)+']')
        elif contentType == 6:
            kodi_common.addMenu(PLUGIN_URL+'?mode=index&folder=PHOTOMUSIC&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30032)+']')
        folderName = 'root'
        if (service.protocol != 2):
            kodi_common.addMenu(PLUGIN_URL+'?mode=index&folder=STARRED-FILES&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+ ' '+addon.getLocalizedString(30095)+']')
            kodi_common.addMenu(PLUGIN_URL+'?mode=index&folder=STARRED-FOLDERS&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+  ' '+addon.getLocalizedString(30096)+']')
        kodi_common.addMenu(PLUGIN_URL+'?mode=index&folder=SHARED&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+  ' '+addon.getLocalizedString(30098)+']')
        kodi_common.addMenu(PLUGIN_URL+'?mode=index&folder=STARRED-FILESFOLDERS&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+  ' '+addon.getLocalizedString(30097)+']')
        kodi_common.addMenu(PLUGIN_URL+'?mode=search&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30111)+']')
    ##**

#        if encfs_target != '':
#                service.addDirectory(None, contextType, localPath=encfs_target)

#    if encfs_target != '' and encfs == False and folderName != False and folderName != '':
#                    service.addDirectory(folder.folder(folderName,'[decrypted]'), contextType, encfs=True)


    # cloudservice - validate service
    try:
        service
    except NameError:
        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30051), addon.getLocalizedString(30052))
        xbmc.log(addon.getLocalizedString(30050)+ 'gdrive-login', xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(plugin_handle)

    #if encrypted, get everything(as encrypted files will be of type application/ostream)
    if encfs:

        encryptedPath = settings.getParameter('epath', '')
        dencryptedPath = settings.getParameter('dpath', '')

        print "folderPath = " + str(encryptedPath)

        encfs_source = settings.getSetting('encfs_source')
        encfs_target = settings.getSetting('encfs_target')
        encfs_inode = int(settings.getSetting('encfs_inode', 0))

        mediaItems = service.getMediaList(folderName,contentType=8)

        if mediaItems:
            dirListINodes = {}
            fileListINodes = {}
            for item in mediaItems:

                    if item.file is None:
                        xbmcvfs.mkdir(encfs_source + str(encryptedPath))
                        xbmcvfs.mkdir(encfs_source + str(encryptedPath) + str(item.folder.title) + '/' )

                        if encfs_inode == 0:
                            dirListINodes[(str(xbmcvfs.Stat(encfs_source + str(encryptedPath) + str(item.folder.title)).st_ino()))] = item.folder
                        else:
                            dirListINodes[(str(xbmcvfs.Stat(encfs_source + str(encryptedPath) + str(item.folder.title)).st_ctime()))] = item.folder
                        #service.addDirectory(item.folder, contextType=contextType,  encfs=True)
                    else:
                        xbmcvfs.mkdir(encfs_source +  str(encryptedPath))
                        xbmcvfs.mkdir(encfs_source +  str(encryptedPath) + str(item.file.title))
                        if encfs_inode == 0:
                            fileListINodes[(str(xbmcvfs.Stat(encfs_source +  str(encryptedPath)+ str(item.file.title)).st_ino()))] = item
                        else:
                            fileListINodes[(str(xbmcvfs.Stat(encfs_source +  str(encryptedPath) + str(item.file.title)).st_ctime()))] = item
                        #service.addMediaFile(item, contextType=contextType)
                    if encfs_inode > 0:
                            xbmc.sleep(1000)


            if contentType == 9:
                mediaList = ['.mp4', '.flv', '.mov', '.webm', '.avi', '.ogg']
            elif contentType == 10:
                mediaList = ['.mp3', '.flac']
            else:# contentType == 11:
                mediaList = ['.jpg', '.png']
            media_re = re.compile("|".join(mediaList))
            print "contentType =" + str(contentType)

            dirs, files = xbmcvfs.listdir(encfs_target + str(dencryptedPath) )
            for dir in dirs:
                index = ''
                if encfs_inode == 0:
                    index = str(xbmcvfs.Stat(encfs_target + str(dencryptedPath) + dir).st_ino())
                else:
                    index = str(xbmcvfs.Stat(encfs_target + str(dencryptedPath) + dir).st_ctime())
                if index in dirListINodes.keys():
                    xbmcvfs.rmdir(encfs_target + str(dencryptedPath) + dir)
                    print "delete = " + encfs_target + str(dencryptedPath) + dir
#                    dirTitle = dir + ' [' +dirListINodes[index].title+ ']'
                    encryptedDir = dirListINodes[index].title
                    dirListINodes[index].title = dir + ' [' +dirListINodes[index].title+ ']'
                    service.addDirectory(dirListINodes[index], contextType=contextType,  encfs=True, dpath=str(dencryptedPath) + str(dir) + '/', epath=str(encryptedPath) + str(encryptedDir) + '/' )
                elif index in fileListINodes.keys():
                    xbmcvfs.rmdir(encfs_target + str(dencryptedPath) + dir)
                    print "delete = " + encfs_target + str(dencryptedPath) + dir
                    fileListINodes[index].file.decryptedTitle = dir
                    if contentType < 9 or media_re.search(str(dir)):
                        service.addMediaFile(fileListINodes[index], contextType=contextType, encfs=True,  dpath=str(dencryptedPath) + str(dir), epath=str(encryptedPath) )


            # file is already downloaded
            for file in files:
                index = ''
                if encfs_inode == 0:
                    index = str(xbmcvfs.Stat(encfs_target + str(dencryptedPath) + file).st_ino())
                else:
                    index = str(xbmcvfs.Stat(encfs_target + str(dencryptedPath) + file).st_ctime())
                if index in fileListINodes.keys():
                    fileListINodes[index].file.decryptedTitle = file
                    if contentType < 9 or media_re.search(str(file)):
                        service.addMediaFile(fileListINodes[index], contextType=contextType, encfs=True,  dpath=str(dencryptedPath) + str(file), epath=str(encryptedPath) )

        #xbmc.executebuiltin("XBMC.Container.Refresh")


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

    spreadshetModule = settings.getSetting('library', False)


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

    title = settings.getParameter('title',0)
    title = re.sub('/', '_', title) #remap / from titles (google photos)

    docid = settings.getParameter('filename')
    folder = settings.getParameter('folder',0)

    encfs = settings.getParameter('encfs', False)

    if encfs:

        encryptedPath = settings.getParameter('epath', '')
        dencryptedPath = settings.getParameter('dpath', '')

        print "folderPath = " + str(encryptedPath)

        encfs_source = settings.getSetting('encfs_source')
        encfs_target = settings.getSetting('encfs_target')
        encfs_inode = int(settings.getSetting('encfs_inode', 0))

#        if (not xbmcvfs.exists(str(encfs_target) + dencryptedPath)):
#            xbmcvfs.mkdir(str(encfs_target) + dencryptedPath)

#        folderINode = ''
#        if encfs_inode == 0:
#            folderINode = str(xbmcvfs.Stat(encfs_target + dencryptedPath + str(folder)).st_ino())
#        else:
#            folderINode = str(xbmcvfs.Stat(encfs_target + dencryptedPath + str(folder)).st_ctime())


        # don't redownload if present already
        if (not xbmcvfs.exists(str(encfs_source) + encryptedPath +str(title))):
            url = service.getDownloadURL(docid)
            service.downloadPicture(url, str(encfs_source) + encryptedPath +str(title))
#        fileINode = ''
#        if encfs_inode ==0:
#            fileINode = str(xbmcvfs.Stat(str(encfs_source) + encryptedPath +str(title)).st_ino())
#        else:
#            fileINode = str(xbmcvfs.Stat(str(encfs_source) + encryptedPath +str(title)).st_ctime())
        print "IN" + encfs_target + dencryptedPath

        xbmc.executebuiltin("XBMC.ShowPicture("+encfs_target + dencryptedPath+")")
        item = xbmcgui.ListItem(path=encfs_target + dencryptedPath)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, item)
        print "file ="+encfs_target + dencryptedPath

#        dirsx, files = xbmcvfs.listdir(encfs_target + dencryptedPath)
#        for file in files:
#                    index = ''
#                    if encfs_inode ==0:
#                        index = str(xbmcvfs.Stat(encfs_target + dencryptedPath + file).st_ino())
#                    else:
#                        index = str(xbmcvfs.Stat(encfs_target + dencryptedPath + file).st_ctime())
#                    if index == fileINode:
#                        xbmc.executebuiltin("XBMC.ShowPicture("+encfs_target + dencryptedPath + file+")")
#                        item = xbmcgui.ListItem(path=encfs_target + dencryptedPath + file)
#                        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, item)
#                        print "file ="+encfs_target + dencryptedPath + file
    else:
        path = settings.getSetting('photo_folder')

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

    title = settings.getParameter('title')
    folderID = settings.getParameter('folder')
    folderName = settings.getParameter('foldername')
    encfs = settings.getParameter('encfs', False)

    try:
        service
    except NameError:
        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30051), addon.getLocalizedString(30052))
        xbmc.log(addon.getLocalizedString(30050)+ 'gdrive-login',xbmc.LOGERROR)
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

    folder = settings.getParameter('folder',0)
    title = settings.getParameter('title',0)

    path = '/tmp/2/'

    enc_password = settings.getSetting('enc_password')

    salt = encryption.read_salt(str(settings.getSetting('salt')))

    key = encryption.generate_key(enc_password,salt,encryption.NUMBER_OF_ITERATIONS)

    service.decryptFolder(key,path,folder)



elif mode == 'slideshow':

    folder = settings.getParameter('folder',0)
    title = settings.getParameter('title',0)


    encfs = settings.getParameter('encfs', False)

    if encfs:
        encfs_inode = int(settings.getSetting('encfs_inode', 0))

        encfs_source = settings.getSetting('encfs_source')
        encfs_target = settings.getSetting('encfs_target')

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
        path = settings.getSetting('photo_folder')

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
# for video files
# force stream - play a video given its url
###
elif mode == 'streamurl':

    url = settings.getParameter('url',0)
    title = settings.getParameter('title')


    promptQuality = settings.getSetting('prompt_quality', True)

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
            item = xbmcgui.ListItem(path=playbackURL+ '|' + service.getHeadersEncoded())
            item.setInfo( type="Video", infoLabels={ "Title": mediaURLs[ret].title , "Plot" : mediaURLs[ret].title } )
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

            if settings.integratedPlayer:
                player = gPlayer.gPlayer()
                player.play(playbackURL+'|' + service.getHeadersEncoded(), item)
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
elif mode == 'audio' or mode == 'video' or mode == 'search' or mode == 'play' or mode == 'memorycachevideo' or mode == 'playvideo' or mode == 'streamvideo':

    title = settings.getParameter('title') #file title
    filename = settings.getParameter('filename') #file ID
    folderID = settings.getParameter('folder') #folder ID

    if folderID == 'False':
            folderID = 'SEARCH'

    if mode != 'audio':
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
        xbmc.log(addon.getLocalizedString(30050)+ 'gdrive-login', xbmc.LOGERROR)
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


    encfs = settings.getParameter('encfs', False)

    if encfs:

        encryptedPath = settings.getParameter('epath', '')
        dencryptedPath = settings.getParameter('dpath', '')

        encfs_source = settings.getSetting('encfs_source')
        encfs_target = settings.getSetting('encfs_target')
        encfs_inode = int(settings.getSetting('encfs_inode', 0))

        # don't redownload if present already
        if (not xbmcvfs.exists(str(encfs_source) + encryptedPath +str(title))):
            url = service.getDownloadURL(filename)
            service.downloadPicture(url, str(encfs_source) + encryptedPath +str(title))

        item = xbmcgui.ListItem(path=encfs_target + dencryptedPath)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

        playbackMedia = False

    else:
        playbackMedia = True

    # file ID provided
    #if we don't have the docid, search for the video for playback
    if (playbackMedia and filename != '' and mode == 'audio'):
        mediaFile = file.file(filename, title, '', service.MEDIA_TYPE_MUSIC, '','')
        mediaFolder = folder.folder(folderID,'')
        (mediaURLs,package) = service.getPlaybackCall(package=package.package(mediaFile,mediaFolder))
    elif (playbackMedia and filename != ''):
        mediaFile = file.file(filename, title, '', 0, '','')
        mediaFolder = folder.folder(folderID,'')
        (mediaURLs,package) = service.getPlaybackCall(package=package.package(mediaFile,mediaFolder))
    # search
    elif playbackMedia and mode == 'search':

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

            #search from STRM
            if contextType == '':

                ret = xbmcgui.Dialog().select(addon.getLocalizedString(30112), options)
                playbackPath = urls[ret]

                item = xbmcgui.ListItem(path=playbackPath+'|' + service.getHeadersEncoded())
                item.setInfo( type="Video", infoLabels={ "Title": options[ret] , "Plot" : options[ret] } )
                if settings.integratedPlayer:
                    player = gPlayer.gPlayer()
                    player.play(playbackPath+'|' + service.getHeadersEncoded(), item)
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
                else:
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
    # folder only
    elif playbackMedia and folderID != '' and title == '':
        mediaItems = service.getMediaList(folderName=folderID, contentType=contentType)
        if mediaItems:
            if contextType == '':
                player = gPlayer.gPlayer()
                player.setMedia(mediaItems)
                player.playLgist(service)
                playbackMedia = False
    # title provided
    elif playbackMedia:
            (mediaURLs,package) = service.getPlaybackCall(None,title=title)


    originalURL = ''
    if playbackMedia and mode != 'audio':
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
        #mediaURL.url = mediaURL.url +'|' + service.getHeadersEncoded()

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

                spreadshetModule = settings.getSetting('library', False)
                spreadshetName = settings.getSetting('library_filename', 'TVShows')

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
                                thumbnailImage=package.file.thumbnail)#, path=playbackPath+'|' + service.getHeadersEncoded())

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
                    # file property - gdrive
                    if settings.cloudResume == 1 and service.protocol == 2 and player.time > package.file.resume:
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
                    # file property - gdrive
                    if  settings.cloudResume == 1 and  service.protocol == 2 and player.time > package.file.resume:
                        service.setProperty(package.file.id,'resume', player.time)

#                player = gPlayer.gPlayer()
#                player.play(playbackURL+'|' + service.getHeadersEncoded(), item)
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

#                xbmc.executebuiltin("XBMC.PlayMedia("+str(playbackPath)+'|' + service.getHeadersEncoded()+")")


    elif playbackMedia:
        cache = cache.cache(package)
        service.cache = cache

        (localResolutions,localFiles) = service.cache.getFiles(service)
        if len(localFiles) > 0:
            mediaURL = mediaurl.mediaurl(str(localFiles[0]), 'offline', 0, 0)
        else:
            mediaURL = mediaURLs[0]
            if not settings.download:
                mediaURL.url =  mediaURL.url +'|' + service.getHeadersEncoded()

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
#                                thumbnailImage=package.file.thumbnail)#, path=playbackPath+'|' + service.getHeadersEncoded())
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


xbmcplugin.endOfDirectory(plugin_handle)

