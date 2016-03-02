'''
    Copyright (C) 2013-2016 ddurdle

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

#import os
import re
import urllib, urllib2
import sys
import os

# cloudservice - standard XBMC modules
import xbmc, xbmcaddon, xbmcgui, xbmcplugin
import xbmcvfs

from resources.lib import mediaurl
from resources.lib import kodi_common
from resources.lib import settings




#global variables
PLUGIN_URL = sys.argv[0]
plugin_handle = int(sys.argv[1])



def decode(data):
        return re.sub("&#(\d+)(;|(?=\s))", _callback, data).strip()

def decode_dict(data):
        for k, v in data.items():
            if type(v) is str or type(v) is unicode:
                data[k] = decode(v)
        return data

#http://stackoverflow.com/questions/1208916/decoding-html-entities-with-python/1208931#1208931
def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id))
    except:
        return id


##
# Calculate the number of accounts defined in settings
#   parameters: the account type (usually plugin name)
##
def numberOfAccounts(accountType):

    return 9
    count = 1
    max_count = int(settings.getSetting(accountType+'_numaccounts',9))

    actualCount = 0
    while True:
        try:
            if settings.getSetting(accountType+str(count)+'_username') != '':
                actualCount = actualCount + 1
        except:
            break
        if count == max_count:
            break
        count = count + 1
    return actualCount



##
# Delete an account, enroll an account or refresh the current listings
#   parameters: mode
##
def accountActions(addon, PLUGIN_NAME, mode, instanceName, numberOfAccounts):

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


            invokedUsername = settings.getParameter('username')
            code = settings.getParameter('code', '')


            if code == '':
                options = []
                options.append('Google Apps')
                ret = xbmcgui.Dialog().select('select type', options)

                invokedUsername = ''
                password = ''
                if ret == 0:
                    try:
                        dialog = xbmcgui.Dialog()
                        invokedUsername = dialog.input('username', type=xbmcgui.INPUT_ALPHANUM)
                        passcode = dialog.input('passcode', type=xbmcgui.INPUT_ALPHANUM)
                    except:
                        pass

                count = 1
                loop = True
                while loop:
                    instanceName = PLUGIN_NAME+str(count)
                    try:
                        username = settings.getSetting(instanceName+'_username')
                        if username == invokedUsername:
                            addon.setSetting(instanceName + '_type', str(4))
                            addon.setSetting(instanceName + '_username', str(invokedUsername))
                            addon.setSetting(instanceName + '_passcode', str(passcode))
                            xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30118), invokedUsername)
                            loop = False
                        elif username == '':
                            addon.setSetting(instanceName + '_type', str(4))
                            addon.setSetting(instanceName + '_username', str(invokedUsername))
                            addon.setSetting(instanceName + '_passcode', str(passcode))
                            xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30118), invokedUsername)
                            loop = False

                    except:
                        pass

                    if count == numberOfAccounts:
                        #fallback on first defined account
                        addon.setSetting(instanceName + '_type', str(4))
                        addon.setSetting(instanceName + '_username', invokedUsername)
                        addon.setSetting(instanceName + '_passcode', str(passcode))
                        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30118), invokedUsername)
                        loop = False
                    count = count + 1

            else:
                count = 1
                loop = True
                while loop:
                    instanceName = PLUGIN_NAME+str(count)
                    try:
                        username = settings.getSetting(instanceName+'_username')
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

##
# Delete an account, enroll an account or refresh the current listings
#   parameters: addon, plugin name, mode, instance name, user provided username, number of accounts, current context
#   returns: selected instance name
##
def getInstanceName(addon, PLUGIN_NAME, mode, instanceName, invokedUsername, numberOfAccounts, contextType):

    # show list of services
    if mode == 'delete' or mode == 'dummy':
                count = 1

    elif numberOfAccounts > 1 and instanceName == '' and invokedUsername == '' and mode == 'main':

            kodi_common.addMenu(PLUGIN_URL+'?mode=enroll&content_type='+str(contextType),'[enroll account]')

            if contextType != 'image':
                path = settings.getSetting('cache_folder')
                if path != '' and  (xbmcvfs.exists(path) or os.path.exists(path)):
                    kodi_common.addMenu(PLUGIN_URL+'?mode=offline&content_type='+str(contextType),'<offline media>')

            if contextType == 'image':
                path = settings.getSetting('photo_folder')
                if path != '' and  (xbmcvfs.exists(path) or os.path.exists(path)):
                    kodi_common.addMenu(path,'<offline photos>')

            path = settings.getSetting('encfs_target')
            if path != '' and  (xbmcvfs.exists(path) or os.path.exists(path)):
                kodi_common.addMenu(path,'<offline encfs>')


            mode = ''
            count = 1
            while True:
                instanceName = PLUGIN_NAME+str(count)
                try:
                    username = settings.getSetting(instanceName+'_username')
                    if username != '':
                        kodi_common.addMenu(PLUGIN_URL+'?mode=main&content_type='+str(contextType)+'&instance='+str(instanceName),username, instanceName=instanceName)

                except:
                    pass
                if count == numberOfAccounts:
                    break
                count = count + 1
            return None

    #        spreadshetModule = getSetting('library', False)
    #        libraryAccount = getSetting('library_account')

     #       if spreadshetModule:
     #           kodi_common.addMenu(PLUGIN_URL+'?mode=kiosk&content_type='+str(contextType)+'&instance='+PLUGIN_NAME+str(libraryAccount),'[kiosk mode]')

    elif instanceName == '' and invokedUsername == '' and numberOfAccounts == 1:

            count = 1
            options = []
            accounts = []

            for count in range (1, numberOfAccounts+1):
                instanceName = PLUGIN_NAME+str(count)
                try:
                    username = settings.getSetting(instanceName+'_username')
                    if username != '':
                        options.append(username)
                        accounts.append(instanceName)

                    if username != '':

                        return instanceName
                except:
                    return instanceName

            #fallback on first defined account
            return accounts[0]

    # no accounts defined and url provided; assume public
    elif numberOfAccounts == 0 and mode=='streamurl':
        return None

    # offline mode
    elif mode=='offline':
        return None
        # no accounts defined
    elif numberOfAccounts == 0:

            #legacy account conversion
            try:
                username = settings.getSetting('username')

                if username != '':
                    addon.setSetting(PLUGIN_NAME+'1_username', username)
                    addon.setSetting(PLUGIN_NAME+'1_password', settings,getSetting('password'))
                    addon.setSetting(PLUGIN_NAME+'1_auth_writely', settings.getSetting('auth_writely'))
                    addon.setSetting(PLUGIN_NAME+'1_auth_wise', settings.getSetting('auth_wise'))
                    addon.setSetting('username', '')
                    addon.setSetting('password', '')
                    addon.setSetting('auth_writely', '')
                    addon.setSetting('auth_wise', '')
                else:
                    xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30015))
                    xbmcplugin.endOfDirectory(plugin_handle)
            except :
                xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30015))
                xbmcplugin.endOfDirectory(plugin_handle)

            return instanceName

    # show entries of a single account (such as folder)
    elif instanceName != '':

        return instanceName



    elif invokedUsername != '':

            options = []
            accounts = []
            for count in range (1, numberOfAccounts+1):
                instanceName = PLUGIN_NAME+str(count)
                try:
                    username = settings.getSetting(instanceName+'_username')
                    if username != '':
                        options.append(username)
                        accounts.append(instanceName)

                    if username == invokedUsername:
                        return instanceName

                except:
                    return instanceName


            #fallback on first defined account
            return accounts[0]

    #prompt before playback
    else:

            options = []
            accounts = []

            # url provided; provide public option
            if mode=='streamurl':
                options.append('*public')
                accounts.append('public')

            for count in range (1, numberOfAccounts+1):
                instanceName = PLUGIN_NAME+str(count)
                try:
                    username = settings.getSetting(instanceName+'_username',10)
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
                return None
            else:
                return accounts[ret]


#
#
#
class cloudservice(object):
    # CloudService v0.2.3


    PLAYBACK_RESOLVED = 1
    PLAYBACK_PLAYER = 2
    PLAYBACK_NONE = 3

    def __init__(self): pass


    ##
    # perform login
    ##
    def login(self): pass

    ##
    # if we don't have an authorization token set for the plugin, set it with the recent login.
    #   auth_token will permit "quicker" login in future executions by reusing the existing login session (less HTTPS calls = quicker video transitions between clips)
    ##
    def updateAuthorization(self,addon):
        if self.authorization.isUpdated :#and addon.getSetting(self.instanceName+'_save_auth_token') == 'true':
            self.authorization.saveTokens(self.instanceName,addon)

    ##
    # return the appropriate "headers" for requests that include 1) user agent, 2) any authorization cookies/tokens
    #   returns: list containing the header
    ##
    def getHeadersList(self):
        return { 'User-Agent' : self.user_agent }

    ##
    # return the appropriate "headers" for requests that include 1) user agent, 2) any authorization cookies/tokens
    #   returns: URL-encoded header string
    ##
    def getHeadersEncoded(self):
        return urllib.urlencode(self.getHeadersList())


    ##
    # build STRM files to a given path for a given folder ID
    #   parameters: path, folder id, content type, dialog object (optional)
    ##
    def buildSTRM(self, path, folderID='', contentType=1, pDialog=None, epath='', dpath='', encfs=False):

        import xbmcvfs
        xbmcvfs.mkdir(path)

        mediaItems = self.getMediaList(folderID,contentType=contentType)

        if mediaItems and not encfs:
            for item in mediaItems:

                url = 0
                if item.file is None:
                    self.buildSTRM(path + '/'+str(item.folder.title), item.folder.id, pDialog=pDialog)
                else:
                    #'content_type': 'video',
                    values = { 'username': self.authorization.username, 'title': item.file.title, 'filename': item.file.id}
                    if item.file.type == 1:
                        url = self.PLUGIN_URL+ '?mode=audio&' + urllib.urlencode(values)
                    else:
                        url = self.PLUGIN_URL+ '?mode=video&' + urllib.urlencode(values)

                    #url = self.PLUGIN_URL+'?mode=video&title='+str(item.file.title)+'&filename='+str(item.file.id)+ '&username='+str(self.authorization.username)


                if url != 0:
                    title = item.file.title

                    if pDialog is not None:
                        pDialog.update(message=title)

                    if not xbmcvfs.exists(str(path) + '/' + str(title)+'.strm'):
                        filename = str(path) + '/' + str(title)+'.strm'
                        strmFile = xbmcvfs.File(filename, "w")

                        strmFile.write(url+'\n')
                        strmFile.close()

                    # nekwebdev contribution
                    if self.addon.getSetting('tvshows_path') != '' or self.addon.getSetting('movies_path') != '':
                        pathLib = ''

                        regmovie = re.compile('(.*?\(\d{4}\))'
                                          '.*?'
                                          '(?:(\d{3}\d?p)|\Z)?')

                        tv = item.file.regtv1.match(title)
                        if not tv:
                            tv = item.file.regtv2.match(title)
                        if not tv:
                            tv = item.file.regtv3.match(title)

                        if tv and self.addon.getSetting('tvshows_path') != '':
                            show = tv.group(1).replace("\S{2,}\.\S{2,}", " ")
                            show = show.rstrip("\.")
                            season = tv.group(2)
                            pathLib = self.addon.getSetting('tvshows_path') + '/' + show
                            if not xbmcvfs.exists(xbmc.translatePath(pathLib)):
                                xbmcvfs.mkdir(xbmc.translatePath(pathLib))
                            pathLib = pathLib + '/Season ' + season
                            if not xbmcvfs.exists(xbmc.translatePath(pathLib)):
                                xbmcvfs.mkdir(xbmc.translatePath(pathLib))
                        elif self.addon.getSetting('movies_path') != '':
                            movie = regmovie.match(title)
                            if movie:
                                pathLib = self.addon.getSetting('movies_path')

                        if pathLib != '':
                            if not xbmcvfs.exists(pathLib + '/' + str(title)+'.strm'):
                                filename = str(pathLib) + '/' + str(title)+'.strm'
                                strmFile = xbmcvfs.File(filename, "w")
                                strmFile.write(url+'\n')
                                strmFile.close()
        elif mediaItems and encfs:

            self.settings.setEncfsParameters()

            encryptedPath = self.settings.getParameter('epath', '')
            dencryptedPath = self.settings.getParameter('dpath', '')

            encfs_source = self.settings.encfsSource
            encfs_target = self.settings.encfsTarget
            encfs_inode = self.settings.encfsInode

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
                mediaList = ['.mp4', '.flv', '.mov', '.webm', '.avi', '.ogg', '.mkv']
            elif contentType == 10:
                mediaList = ['.mp3', '.flac']
            else:# contentType == 11:
                mediaList = ['.jpg', '.png']
            media_re = re.compile("|".join(mediaList), re.I)

            dirs, files = xbmcvfs.listdir(encfs_target + str(dencryptedPath) )
            url = 0
            for dir in dirs:
                index = ''
                if encfs_inode == 0:
                    index = str(xbmcvfs.Stat(encfs_target + str(dencryptedPath) + dir).st_ino())
                else:
                    index = str(xbmcvfs.Stat(encfs_target + str(dencryptedPath) + dir).st_ctime())
                if index in dirListINodes.keys():
                    xbmcvfs.rmdir(encfs_target + str(dencryptedPath) + dir)
#                    dirTitle = dir + ' [' +dirListINodes[index].title+ ']'
                    encryptedDir = dirListINodes[index].title
                    dirListINodes[index].displaytitle = dir + ' [' +dirListINodes[index].title+ ']'
                    #service.addDirectory(dirListINodes[index], contextType=contextType,  encfs=True, dpath=str(dencryptedPath) + str(dir) + '/', epath=str(encryptedPath) + str(encryptedDir) + '/' )
                    self.buildSTRM(path + '/'+str(item.folder.title), item.folder.id, pDialog=pDialog, encfs=True, dpath=str(dencryptedPath) + str(dir) + '/', epath=str(encryptedPath) + str(encryptedDir) + '/' )

                elif index in fileListINodes.keys():
                    xbmcvfs.rmdir(encfs_target + str(dencryptedPath) + dir)
                    fileListINodes[index].file.decryptedTitle = dir
                    if contentType < 9 or media_re.search(str(dir)):
                        #service.addMediaFile(fileListINodes[index], contextType=contextType, encfs=True,  dpath=str(dencryptedPath) + str(dir), epath=str(encryptedPath) )
                        #'content_type': 'video',
                        values = { 'username': self.authorization.username, 'encfs':'True', 'dpath': str(dencryptedPath) + str(dir), 'epath': str(encryptedPath), 'title': item.file.title, 'filename': item.file.id}
                        if item.file.type == 1:
                            url = self.PLUGIN_URL+ '?mode=audio&' + urllib.urlencode(values)
                        else:
                            url = self.PLUGIN_URL+ '?mode=video&' + urllib.urlencode(values)

                        #url = self.PLUGIN_URL+'?mode=video&title='+str(item.file.title)+'&filename='+str(item.file.id)+ '&username='+str(self.authorization.username)


                    if url != 0:
                        title = str(dir)

                        if pDialog is not None:
                            pDialog.update(message=title)

                        if not xbmcvfs.exists(str(path) + '/' + str(title)+'.strm'):
                            filename = str(path) + '/' + str(title)+'.strm'
                            strmFile = xbmcvfs.File(filename, "w")

                            strmFile.write(url+'\n')
                            strmFile.close()

            url=0
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
                        #service.addMediaFile(fileListINodes[index], contextType=contextType, encfs=True,  dpath=str(dencryptedPath) + str(file), epath=str(encryptedPath) )
                        #'content_type': 'video',
                        values = { 'username': self.authorization.username, 'encfs':'True', 'dpath': str(dencryptedPath) + str(dir), 'epath': str(encryptedPath), 'title': item.file.title, 'filename': item.file.id}
                        if item.file.type == 1:
                            url = self.PLUGIN_URL+ '?mode=audio&' + urllib.urlencode(values)
                        else:
                            url = self.PLUGIN_URL+ '?mode=video&' + urllib.urlencode(values)

                        #url = self.PLUGIN_URL+'?mode=video&title='+str(item.file.title)+'&filename='+str(item.file.id)+ '&username='+str(self.authorization.username)


                    if url != 0:
                        title = str(dir)

                        if pDialog is not None:
                            pDialog.update(message=title)

                        if not xbmcvfs.exists(str(path) + '/' + str(title)+'.strm'):
                            filename = str(path) + '/' + str(title)+'.strm'
                            strmFile = xbmcvfs.File(filename, "w")

                            strmFile.write(url+'\n')
                            strmFile.close()

    ##
    # retrieve a directory url
    #   parameters: folder id, context type, whether the directory is encfs, encfs:decryption path, encfs:encryption path
    #   returns: fully qualified url
    ##
    def getDirectoryCall(self, folder, contextType='video', encfs=False, dpath='', epath=''):
        if encfs:
            values = {'instance': self.instanceName, 'encfs': 'true', 'folder': folder.id, 'content_type': contextType, 'dpath': dpath, 'epath':epath}
        else:
            values = {'instance': self.instanceName, 'folder': folder.id, 'content_type': contextType, 'epath':epath}

        return self.PLUGIN_URL+'?mode=index&' +  urllib.urlencode(values)


    ##
    # download/retrieve a media file
    #   parameters: whether to playback file, media url object, package object, whether to force download (overwrite), whether the file is encfs, folder name (option)
    ##
    def downloadMediaFile(self, mediaURL, item, package, force=False, folderName='', playback=1, player=None):

        progress = ''
        cachePercent = int(self.settings.cachePercent)

        if cachePercent < 1:
            cachePercent = 1
        elif cachePercent > 100:
            cachePercent = 100

        fileSize = (int)(package.file.size)
        if fileSize == '' or fileSize < 1000:
            fileSize = 5000000

        sizeDownload = fileSize * (cachePercent*0.01)

        if sizeDownload < 1000000:
            sizeDownload = 1000000

        CHUNK = int(self.settings.cacheChunkSize)

        if CHUNK < 1024:
            CHUNK = 16 * 1024

        count = 0


        try:
            path = self.addon.getSetting('cache_folder')
        except:
            pass

        if not xbmcvfs.exists(path) and not os.path.exists(path):
            path = ''

        while path == '':
            path = xbmcgui.Dialog().browse(0,self.addon.getLocalizedString(30090), 'files','',False,False,'')
            if not xbmcvfs.exists(path) and not os.path.exists(path):
                path = ''
            else:
                self.addon.setSetting('cache_folder', path)


        if self.settings.cacheSingle:
            playbackFile = str(path) + '/cache.mp4'
            force= True

        else:
            try:
                xbmcvfs.mkdir(str(path) + '/'+ str(package.file.id))
            except: pass

            playbackFile = str(path) + '/' + str(package.file.id) + '/' + str(mediaURL.order) + '.stream.mp4'

        if not xbmcvfs.exists(str(path) + '/' + str(package.file.id) + '/' + str(package.file.id) + '.name') or force:

            nameFile = xbmcvfs.File(str(path) + '/' + str(package.file.id) + '/' + str(package.file.id)+'.name' , "w")
            nameFile.write(package.file.title +'\n')
            nameFile.close()

        if not xbmcvfs.exists(str(path) + '/' + str(package.file.id) + '/' + str(mediaURL.order) + '.stream.resolution') or force:

            resolutionFile = xbmcvfs.File(str(path) + '/' + str(package.file.id) + '/' + str(mediaURL.order) + '.stream.resolution' , "w")
            resolutionFile.write(mediaURL.qualityDesc +'\n')
            resolutionFile.close()


        if (not xbmcvfs.exists(playbackFile)  or  xbmcvfs.File(playbackFile).size() == 0) or force:

            req = urllib2.Request(mediaURL.url, None, self.getHeadersList())

            f = xbmcvfs.File(playbackFile, 'w')


            #print "DEBUG url = " + mediaURL.url + ", sizeDownload = " + str(sizeDownload) + ", playback = " + str(playback) + ", playbackFile = " + str(playbackFile)
#            if playbackURL != '':
#                progress = xbmcgui.DialogProgress()
#                progressBar = sizeDownload
#                progress.create(self.addon.getLocalizedString(30000), self.addon.getLocalizedString(30035), package.file.title)
#            else:
            progress = xbmcgui.DialogProgressBG()
            progressBar = fileSize
            progress.create(self.addon.getLocalizedString(30035), package.file.title)
            # if action fails, validate login
            try:
              response = urllib2.urlopen(req)

            except urllib2.URLError, e:
              self.refreshToken()
              req = urllib2.Request(mediaURL.url, None, self.getHeadersList())
              try:
                  response = urllib2.urlopen(req)

              except urllib2.URLError, e:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                self.crashreport.sendError('downloadMediaFile',str(e))
                return

            downloadedBytes = 0
            while sizeDownload > downloadedBytes:
                progress.update((int)(float(downloadedBytes)/progressBar*100),self.addon.getLocalizedString(30035))
                chunk = response.read(CHUNK)
                if not chunk: break
                f.write(chunk)
                downloadedBytes = downloadedBytes + CHUNK

        if playback != self.PLAYBACK_NONE:

            item.setPath(playbackFile)
            if playback == self.PLAYBACK_RESOLVED:
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
            else:
                #xbmc.executebuiltin("XBMC.PlayMedia("+playbackFile+")")
                player.PlayStream(playbackFile, item, package.file.resume, startPlayback=True, package=package)
            while not (player.isPlaying()):
                xbmc.sleep(1000)
                #print str(player.playStatus)
        try:
            count =1
            while True:
                if not self.settings.cacheContinue and player is not None and count % 12 == 0:
                    if not player.playStatus:
                        progress.close()
                        f.close()
                        return
                count = count + 1
                downloadedBytes = downloadedBytes + CHUNK
                progress.update((int)(float(downloadedBytes)/progressBar*100),self.addon.getLocalizedString(30092))
                chunk = response.read(CHUNK)
                if not chunk: break
                f.write(chunk)
                xbmc.sleep(1)

            f.close()
            progress.close()

        except: pass



    ##
    # download/retrieve a media file
    #   parameters: whether to playback file, media url object, package object, whether to force download (overwrite), whether the file is encfs, folder name (option)
    ##
    def downloadEncfsFile(self, mediaURL, package, playbackURL='', force=False, folderName='', resolvedPlayback=True,item=''):

        progress = ''
        cachePercent = int(self.settings.encfsCachePercent)

        if cachePercent < 1:
            cachePercent = 1
        elif cachePercent > 100:
            cachePercent = 100

        fileSize = (int)(package.file.size)
        if fileSize == '' or fileSize < 1000:
            fileSize = 5000000

        sizeDownload = fileSize * (cachePercent*0.01)

        if sizeDownload < 1000000:
            sizeDownload = 1000000

        CHUNK = int(self.settings.encfsCacheChunkSize)

        if CHUNK < 1024:
            CHUNK = 16 * 1024

        count = 0


        path = re.sub(r'\/[^\/]+$', r'', folderName)
        if folderName == path:
            path = re.sub(r'\\[^\\]+$', r'', folderName) #needed for windows?

        #ensure the folder and path exists
        try:
            xbmcvfs.mkdirs(path)
        except: pass

        playbackFile = folderName

        if (not xbmcvfs.exists(playbackFile) or xbmcvfs.File(playbackFile).size() == 0) or force:

            req = urllib2.Request(mediaURL.url, None, self.getHeadersList())

            f = xbmcvfs.File(playbackFile, 'w')

            progress = xbmcgui.DialogProgressBG()
            progressBar = fileSize
            progress.create(self.addon.getLocalizedString(30035), package.file.title)

            # if action fails, validate login
            try:
              response = urllib2.urlopen(req)

            except urllib2.URLError, e:
              self.refreshToken()
              req = urllib2.Request(mediaURL.url, None, self.getHeadersList())
              try:
                  response = urllib2.urlopen(req)

              except urllib2.URLError, e:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                self.crashreport.sendError('downloadMediaFile',str(e))
                return

            downloadedBytes = 0
            while sizeDownload > downloadedBytes:
                progress.update((int)(float(downloadedBytes)/progressBar*100),self.addon.getLocalizedString(30035))
                chunk = response.read(CHUNK)
                if not chunk: break
                f.write(chunk)
                downloadedBytes = downloadedBytes + CHUNK

        if playbackURL != '':

            if resolvedPlayback:
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
            xbmc.executebuiltin("XBMC.PlayMedia("+playbackURL+")")
        try:
            while True:
                downloadedBytes = downloadedBytes + CHUNK
                progress.update((int)(float(downloadedBytes)/progressBar*100),self.addon.getLocalizedString(30092))
                chunk = response.read(CHUNK)
                if not chunk: break
                f.write(chunk)
            f.close()
            progress.close()

        except: pass


    ##
    # download remote picture
    # parameters: url of picture, file location with path on disk
    ##
    def downloadGeneralFile(self, url, file, force=False):

        req = urllib2.Request(url, None, self.getHeadersList())

        # already downloaded
        if not force and xbmcvfs.exists(file) and xbmcvfs.File(file).size() > 0:
            return

        f = xbmcvfs.File(file, 'w')

        # if action fails, validate login
        try:
            f.write(urllib2.urlopen(req).read())
            f.close()

        except urllib2.URLError, e:
                self.refreshToken()
                req = urllib2.Request(url, None, self.getHeadersList())
                try:
                  f.write(urllib2.urlopen(req).read())
                  f.close()
                except urllib2.URLError, e:
                  xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                  self.crashreport.sendError('downloadGeneralFle',str(e))
                  return None
        #can't write to cache for some reason
        except IOError:
                return None
        return file
    ##
    # retrieve/download a general file
    #   parameters: title of video, whether to prompt for quality/format (optional), medial url object, package object, whether to force download (overwrite), whether folder is encrypted, folder name
    ##
    def downloadGeneralFileOLD(self, playback, mediaURL, package, force=False, encfs=False, folderName=''):


        cachePercent = int(self.settings.cachePercent)

        if cachePercent < 1:
            cachePercent = 1
        elif cachePercent > 100:
            cachePercent = 100

        fileSize = (int)(package.file.size)
        if fileSize == '' or fileSize < 1000:
            fileSize = 5000000

        sizeDownload = fileSize * (cachePercent*0.01)

        if sizeDownload < 1000000:
            sizeDownload = 1000000

        CHUNK = int(self.settings.cacheChunkSize)

        if CHUNK < 1024:
            CHUNK = 16 * 1024

        count = 0


        if encfs:
            try:
                path = self.addon.getSetting('encfs_source')
            except:
                pass
        else:
            try:
                path = self.addon.getSetting('cache_folder')
            except:
                pass

        #workaround for this issue: https://github.com/xbmc/xbmc/pull/8531
        if not xbmcvfs.exists(path) and not os.path.exists(path):
            path = ''

        while path == '':
            path = xbmcgui.Dialog().browse(0,self.addon.getLocalizedString(30090), 'files','',False,False,'')
            if not xbmcvfs.exists(path) and not os.path.exists(path):
                path = ''
            else:
                self.addon.setSetting('cache_folder', path)


        if encfs:
            try:
                xbmcvfs.mkdir(str(path) + '/'+str(folderName))
            except: pass

            playbackFile = str(path) + '/' + str(folderName) + '/' + str(package.file.title)

        else:
            try:
                xbmcvfs.mkdir(str(path) + '/'+ str(package.file.id))
            except: pass

            playbackFile = str(path) + '/' + str(package.file.id) + '/' + str(mediaURL.order) + '.stream.mp4'


        if (not xbmcvfs.exists(playbackFile) or xbmcvfs.File(playbackFile).size() == 0) or force:

            req = urllib2.Request(mediaURL.url, None, self.getHeadersList())

            f = xbmcvfs.File(playbackFile, 'w')


            if playback != '':
                progress = xbmcgui.DialogProgress()
                progressBar = sizeDownload
                progress.create(self.addon.getLocalizedString(30000), self.addon.getLocalizedString(30035), package.file.title)
            else:
                progress = xbmcgui.DialogProgressBG()
                progressBar = fileSize
                progress.create(self.addon.getLocalizedString(30035), package.file.title)

            # if action fails, validate login
            try:
              response = urllib2.urlopen(req)

            except urllib2.URLError, e:
              self.refreshToken()
              req = urllib2.Request(mediaURL.url, None, self.getHeadersList())
              try:
                  response = urllib2.urlopen(req)

              except urllib2.URLError, e:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                self.crashreport.sendError('downloadMediaFile',str(e))
                return

            downloadedBytes = 0
            while sizeDownload > downloadedBytes:
                progress.update((int)(float(downloadedBytes)/progressBar*100),self.addon.getLocalizedString(30035))
                chunk = response.read(CHUNK)
                if not chunk: break
                f.write(chunk)
                downloadedBytes = downloadedBytes + CHUNK

        if playback != '':
            try:
                progress.close()
            except:
                pass

            #item = xbmcgui.ListItem(path=playbackFile)
            item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail)#, path=playbackPath+'|' + service.getHeadersEncoded())

            item.setInfo( type="Video", infoLabels={ "Title": package.file.title , "Plot" : package.file.title } )
            xbmcplugin.setResolvedUrl(playback, True, item)
            xbmc.executebuiltin("XBMC.PlayMedia("+playbackFile+")")

        try:
            while True:
                downloadedBytes = downloadedBytes + CHUNK
                progress.update((int)(float(downloadedBytes)/progressBar*100),self.addon.getLocalizedString(30092))
                chunk = response.read(CHUNK)
                if not chunk: break
                f.write(chunk)
            f.close()
            progress.close()

        except: pass


    ##
    # Add a directory to a directory listing screen
    #   parameters: folder object, context type, local path (optional), whether folder is encfs, encfs:decryption path, encfs:encryption path
    ##
    def addDirectory(self, folder, contextType='video', localPath='', encfs=False, dpath='', epath=''):

        fanart = self.addon.getAddonInfo('path') + '/fanart.jpg'

        if folder is None:
            listitem = xbmcgui.ListItem('[Decrypted Folder]')
            #        listitem.addContextMenuItems(cm, False)
            listitem.setProperty('fanart_image', fanart)
            xbmcplugin.addDirectoryItem(plugin_handle, localPath, listitem,
                                isFolder=True, totalItems=0)
        else:

            if folder.id == 'SAVED SEARCH':
                listitem = xbmcgui.ListItem(decode(folder.displayTitle()), iconImage=decode(folder.thumb), thumbnailImage=decode(folder.thumb))
                values = {'instance': self.instanceName, 'title': folder.title}

                url = self.PLUGIN_URL+'?mode=search&content_type='+contextType + '&' + urllib.urlencode(values)

                xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
                                isFolder=True, totalItems=0)
            else:
                listitem = xbmcgui.ListItem(decode(folder.displayTitle()), iconImage=decode(folder.thumb), thumbnailImage=decode(folder.thumb))

                if folder.id != '':
                    cm=[]
                    if contextType != 'image' and not encfs:
                        values = {'username': self.authorization.username, 'title': folder.title, 'folder': folder.id, 'content_type': contextType }

                        cm.append(( self.addon.getLocalizedString(30042), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=buildstrm&'+ urllib.urlencode(values)+')', ))

                    #elif contextType != 'image':
                        #values = {'username': self.authorization.username, 'epath': epath, 'dpath': dpath, 'encfs':'true' ,'title': folder.title, 'folder': folder.id, 'content_type': contextType }

                        #cm.append(( self.addon.getLocalizedString(30042), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=buildstrm&'+ urllib.urlencode(values)+')', ))

                    elif contextType == 'image':
                        # slideshow
                        if encfs:
                            values = {'encfs': 'true', 'username': self.authorization.username, 'title': folder.title, 'folder': folder.id}
                        else:
                            values = {'username': self.authorization.username, 'title': folder.title, 'folder': folder.id}
                        #cm.append(( self.addon.getLocalizedString(30126), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=slideshow&'+urllib.urlencode(values)+')', ))

                    if (self.protocol == 2):
                        if contextType != 'image':
                            #download folder
                            values = {'instance': self.instanceName, 'title': folder.title, 'folder': folder.id}
                            cm.append(( self.addon.getLocalizedString(30113), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=downloadfolder&'+urllib.urlencode(values)+')', ))

                        if contextType == 'audio' and not encfs:
                            #playback entire folder
                            values = {'instance': self.instanceName, 'folder': folder.id}
                            cm.append(( self.addon.getLocalizedString(30162), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=audio&content_type='+contextType+'&'+urllib.urlencode(values)+')', ))
                        elif contextType == 'video' and not encfs:
                            #playback entire folder
                            values = {'instance': self.instanceName, 'folder': folder.id}
                            cm.append(( self.addon.getLocalizedString(30162), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=video&content_type='+contextType+'&'+urllib.urlencode(values)+')', ))


                        #add encfs option unless viewing as encfs already
                        if not encfs:
                            cm.append(( '[treat as encfs]', 'XBMC.Container.Update('+self.PLUGIN_URL+'?mode=index&content_type='+contextType+'&encfs=true&'+urllib.urlencode(values)+')', ))
                        #if within encfs and pictures, disable right-click default photo options; add download-folder
                        if encfs and contextType == 'image':
                            values = {'instance': self.instanceName, 'epath': epath, 'foldername': folder.title, 'folder': folder.id}

                            cm.append(( self.addon.getLocalizedString(30113), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=downloadfolder&content_type='+contextType+'&encfs=true&'+urllib.urlencode(values)+')', ))
                            listitem.addContextMenuItems(cm, True)
                        elif contextType == 'image':
                            cm.append(( self.addon.getLocalizedString(30113), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=downloadfolder&content_type='+contextType+'&'+urllib.urlencode(values)+')', ))


                    cm.append(( self.addon.getLocalizedString(30163), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=scan&content_type='+contextType+'&'+urllib.urlencode(values)+')', ))

                listitem.addContextMenuItems(cm, False)
                listitem.setProperty('fanart_image',  folder.fanart)

                xbmcplugin.addDirectoryItem(plugin_handle, self.getDirectoryCall(folder, contextType, encfs=encfs, dpath=dpath, epath=epath), listitem,
                                isFolder=True, totalItems=0)


    ##
    # Add a media file to a directory listing screen
    #   parameters: package, context type, whether file is encfs, encfs:decryption path, encfs:encryption path
    ##
    def addMediaFile(self, package, contextType='video', encfs=False, dpath='', epath=''):
        thumbnail = self.cache.getThumbnail(self, package.file.thumbnail,package.file.id)
        listitem = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail)

        # audio file, not in "pictures"
        if package.file.type == package.file.AUDIO and contextType != 'image':
            if package.file.hasMeta:
                infolabels = decode_dict({ 'title' : package.file.displayTrackTitle(), 'tracknumber' : package.file.trackNumber, 'artist': package.file.artist, 'album': package.file.album,'genre': package.file.genre,'premiered': package.file.releaseDate, 'size' : package.file.size })
            else:
                infolabels = decode_dict({ 'title' : package.file.displayTitle(), 'size' : package.file.size })
            listitem.setInfo('Music', infolabels)
            playbackURL = '?mode=audio'
            if self.integratedPlayer:
                listitem.setProperty('IsPlayable', 'false')
            else:
                listitem.setProperty('IsPlayable', 'true')

        # encrypted file, viewing in "pictures", assume image
        elif package.file.type == package.file.UNKNOWN and contextType == 'image':
            infolabels = decode_dict({ 'title' : package.file.displayTitle() , 'plot' : package.file.plot })
            listitem.setInfo('Pictures', infolabels)
            playbackURL = '?mode=photo'
            listitem.setProperty('IsPlayable', 'false')


        # encrypted file, viewing in "video", assume video
        elif package.file.type == package.file.UNKNOWN and contextType == 'video':
            infolabels = decode_dict({ 'title' : package.file.displayTitle() ,  'plot' : package.file.plot, 'size' : package.file.size })
            listitem.setInfo('Video', infolabels)
            playbackURL = '?mode=video'
            if self.integratedPlayer:
                listitem.setProperty('IsPlayable', 'false')
            else:
                listitem.setProperty('IsPlayable', 'true')
            if float(package.file.resume) > 0:
                listitem.setProperty('isResumable', 1)



        # encrypted file, viewing in "music", assume audio
        elif package.file.type == package.file.UNKNOWN and contextType == 'audio':
            if package.file.hasMeta:
                infolabels = decode_dict({ 'title' : package.file.displayTrackTitle(), 'tracknumber' : package.file.trackNumber, 'artist': package.file.artist, 'album': package.file.album,'genre': package.file.genre,'premiered': package.file.releaseDate, 'size' : package.file.size })
            else:
                infolabels = decode_dict({ 'title' : package.file.displayTitle(), 'size' : package.file.size })
            listitem.setInfo('Music', infolabels)
            playbackURL = '?mode=audio'
            if self.integratedPlayer:
                listitem.setProperty('IsPlayable', 'false')
            else:
                listitem.setProperty('IsPlayable', 'true')

        # audio file, viewing in "pictures"
        elif package.file.type == package.file.AUDIO and contextType == 'image':
            if package.file.hasMeta:
                infolabels = decode_dict({ 'title' : package.file.displayTrackTitle(), 'tracknumber' : package.file.trackNumber, 'artist': package.file.artist, 'album': package.file.album,'genre': package.file.genre,'premiered': package.file.releaseDate, 'size' : package.file.size })
            else:
                infolabels = decode_dict({ 'title' : package.file.displayTitle(), 'size' : package.file.size })
            listitem.setInfo('Music', infolabels)
            playbackURL = '?mode=audio'
            listitem.setProperty('IsPlayable', 'false')

        # video file
        elif package.file.type == package.file.VIDEO:
            if package.file.hasMeta:
                infolabels = decode_dict({ 'title' : package.file.displayShowTitle() ,  'plot' : package.file.plot, 'TVShowTitle': package.file.show, 'EpisodeName': package.file.showtitle, 'season': package.file.season, 'episode': package.file.episode,'size' : package.file.size })
            else:
                infolabels = decode_dict({ 'title' : package.file.displayTitle() ,  'plot' : package.file.plot, 'size' : package.file.size })
            listitem.setInfo('Video', infolabels)
            playbackURL = '?mode=video'
            if self.integratedPlayer:
                listitem.setProperty('IsPlayable', 'false')
            else:
                listitem.setProperty('IsPlayable', 'true')
            if float(package.file.resume) > 0:
                listitem.setProperty('isResumable', "1")
            if int(package.file.playcount) > 0: #or (float(package.file.resume) > 0 and package.file.duration > 0 and package.file.resume/package.file.duration > (1-self.settskipResume)):
                listitem.setInfo('video', {'playcount':int(package.file.playcount)})

            if int(package.file.resolution[0]) > 0:
                listitem.addStreamInfo('video', {'width': package.file.resolution[1], 'height': package.file.resolution[0], 'duration':package.file.duration})

        # image file
        elif package.file.type == package.file.PICTURE:
            infolabels = decode_dict({ 'title' : package.file.displayTitle() , 'plot' : package.file.plot, 'size' : package.file.size })
            listitem.setInfo('Pictures', infolabels)
            listitem.setProperty('mimetype', 'image/jpeg')

            playbackURL = '?mode=photo'
#            listitem.setProperty('IsPlayable', 'false')
            listitem.setProperty('IsPlayable', 'true')
            url = package.file.download+'|' + self.getHeadersEncoded()
            xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
                                isFolder=False, totalItems=0)
            return url
        # otherwise, assume video
        else:
            infolabels = decode_dict({ 'title' : package.file.displayTitle() , 'plot' : package.file.plot, 'size' : package.file.size })
            listitem.setInfo('Video', infolabels)
            playbackURL = '?mode=video'
            if self.integratedPlayer:
                listitem.setProperty('IsPlayable', 'false')
            else:
                listitem.setProperty('IsPlayable', 'true')
            if float(package.file.resume) > 0:
                listitem.setProperty('isResumable', 1)

        listitem.setProperty('fanart_image', package.file.fanart)


        cm=[]

        try:
            url = package.getMediaURL()
            cleanURL = re.sub('---', '', url)
            cleanURL = re.sub('&', '---', cleanURL)
        except:
            cleanURL = ''

    #    url = PLUGIN_URL+playbackURL+'&title='+package.file.title+'&filename='+package.file.id+'&instance='+str(self.instanceName)+'&folder='+str(package.folder.id)
        if encfs:
            values = {'instance': self.instanceName, 'dpath': dpath, 'epath': epath, 'encfs': 'true', 'title': package.file.title, 'filename': package.file.id, 'folder': package.folder.id}
        else:
            values = {'instance': self.instanceName, 'title': package.file.title, 'filename': package.file.id, 'folder': package.folder.id}
        url = self.PLUGIN_URL+ str(playbackURL)+ '&' + urllib.urlencode(values)

        if (contextType != 'image' and package.file.type != package.file.PICTURE):

            #STRM
            if encfs:
                valuesBS = {'username': self.authorization.username, 'dpath': dpath, 'epath': epath, 'encfs': 'true', 'title': package.file.title, 'filename': package.file.id, 'content_type': 'video'}
                cm.append(( self.addon.getLocalizedString(30042), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=buildstrm&type='+str(package.file.type)+'&'+urllib.urlencode(valuesBS)+')', ))
            else:
                valuesBS = {'username': self.authorization.username, 'title': package.file.title, 'filename': package.file.id, 'content_type': 'video'}
                cm.append(( self.addon.getLocalizedString(30042), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=buildstrm&type='+str(package.file.type)+'&'+urllib.urlencode(valuesBS)+')', ))

            if (self.protocol == 2):
                # play-original for video only
                if (contextType == 'video'):
                    if (package.file.type != package.file.AUDIO and self.settings.promptQuality) and not encfs:
                        cm.append(( self.addon.getLocalizedString(30123), 'XBMC.RunPlugin('+url + '&original=true'+')', ))
                    else:
                        cm.append(( self.addon.getLocalizedString(30151), 'XBMC.RunPlugin('+url + '&promptquality=true'+')', ))

                    # if the options are disabled in settings, display option to playback with feature
                    if not self.settings.srt:
                        cm.append(( self.addon.getLocalizedString(30138), 'XBMC.RunPlugin('+url + '&srt=true'+')', ))
                    if not self.settings.cc:
                        cm.append(( self.addon.getLocalizedString(30146), 'XBMC.RunPlugin('+url + '&cc=true'+')', ))

                    cm.append(( self.addon.getLocalizedString(30147), 'XBMC.RunPlugin('+url + '&seek=true'+')', ))
#                    cm.append(( self.addon.getLocalizedString(30148), 'XBMC.RunPlugin('+url + '&resume=true'+')', ))
#                    values = {'instance': self.instanceName, 'folder': package.folder.id}
#                    folderurl = self.PLUGIN_URL+ str(playbackURL)+ '&' + urllib.urlencode(values)
#                    cm.append(( 'folder', 'XBMC.RunPlugin('+folderurl+')', ))

                if contextType != 'image':
                    # download
                    cm.append(( self.addon.getLocalizedString(30113), 'XBMC.RunPlugin('+url + '&download=true'+')', ))

                    # download + watch
                    if not encfs:
                        cm.append(( self.addon.getLocalizedString(30124), 'XBMC.RunPlugin('+url + '&play=true&download=true'+')', ))



        elif package.file.type ==  package.file.PICTURE: #contextType == 'image':

                cm.append(( self.addon.getLocalizedString(30126), 'XBMC.SlideShow('+self.PLUGIN_URL+ '?mode=index&' + urllib.urlencode(values)+')', ))

        #encfs
#        if (self.protocol == 2):
#            cm.append(( self.addon.getLocalizedString(30130), 'XBMC.RunPlugin('+self.PLUGIN_URL+ '?mode=downloadfolder&encfs=true&' + urllib.urlencode(values)+'&content_type='+contextType+')', ))


        url = url + '&content_type='+contextType

        #    listitem.addContextMenuItems( commands )
        #    if cm:
        if  package.file.type ==  package.file.PICTURE: #contextType == 'image':
            listitem.addContextMenuItems(cm, True)
        else:
            listitem.addContextMenuItems(cm, False)

        xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
                                isFolder=False, totalItems=0)
        return url


    ##
    # Return the user selected media source
    #   parameters: list of media url objects, folder id, file id
    #   returns: select media url object
    ##
    def getMediaSelection(self, mediaURLs, folderID, filename):

        options = []
        newMediaURLs = []
        mediaURLs = sorted(mediaURLs)
        if self.settings.playOriginal:
            for mediaURL in mediaURLs:
                if mediaURL.qualityDesc == 'original':
                    options.append(mediaURL.qualityDesc)
                    newMediaURLs.append(mediaURL)
                    originalURL = mediaURL.url
        else:
            for mediaURL in mediaURLs:
                options.append(mediaURL.qualityDesc)
                newMediaURLs.append(mediaURL)
                if mediaURL.qualityDesc == 'original':
                    originalURL = mediaURL.url

        mediaURL = ''
#        if self.settings.download or  self.settings.cache:
#            mediaURL = mediaurl.mediaurl(originalURL, 'original', 0, 9999)
#            return mediaURL
        #elif self.settings.playOriginal:
        #    mediaURL = mediaurl.mediaurl(originalURL +'|' + self.getHeadersEncoded(), 'original', 0, 9999)
        #    return mediaURL

        #playbackPath = str(self.settings.cachePath) + '/' + str(filename) + '/'
        localResolutions = []
        localFiles = []
        if not self.settings.download and not self.settings.cache:
            (localResolutions,localFiles) = self.cache.getFiles(self)
        totalList = localFiles + newMediaURLs
        mediaCount = len(localFiles)

        if self.settings.promptQuality:
            ret = xbmcgui.Dialog().select(self.addon.getLocalizedString(30033), localResolutions + options)
            if ret >= mediaCount:
                mediaURL = totalList[ret]
                if self.settings.download or  self.settings.cache:
                    mediaURL.url = totalList[ret].url
                else:
                    mediaURL.url = totalList[ret].url +'|' + self.getHeadersEncoded()

            else:
                mediaURL = mediaurl.mediaurl(str(totalList[ret]), 'offline', 0, 0)
                mediaURL.offline = True

        else:
            if len(localFiles) == 0:
                mediaURL = totalList[0]
                if self.settings.download or  self.settings.cache:
                    mediaURL.url = totalList[0].url
                else:
                    mediaURL.url = totalList[0].url +'|' + self.getHeadersEncoded()

            else:
                mediaURL = mediaurl.mediaurl(str(totalList[0]), 'offline', 0, 0)
                mediaURL.offline = True


#        elif self.settings.promptQuality and len(options) > 1 and not self.settings.cache:
#            ret = xbmcgui.Dialog().select(self.addon.getLocalizedString(30033), options)
#            mediaURL = mediaURLs[ret]
#            if not self.settings.download:
#                mediaURLs[ret].url = mediaURLs[ret].url +'|' + self.getHeadersEncoded()

#        else:
#            mediaURLs[0].url = mediaURLs[0].url +'|' + self.getHeadersEncoded()
#            mediaURL = mediaURLs[0]

        return mediaURL


    ##
    # download remote picture
    # parameters: url of picture, file location with path on disk
    ##
    def downloadPicture(self, url, file):

        req = urllib2.Request(url, None, self.getHeadersList())

        # already downloaded
        if xbmcvfs.exists(file) and xbmcvfs.File(file).size() > 0:
            return

        f = xbmcvfs.File(file, 'w')

        # if action fails, validate login
        try:
            f.write(urllib2.urlopen(req).read())
            f.close()

        except urllib2.URLError, e:
                self.refreshToken()
                req = urllib2.Request(url, None, self.getHeadersList())
                try:
                  f.write(urllib2.urlopen(req).read())
                  f.close()
                except urllib2.URLError, e:
                  xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                  self.crashreport.sendError('downloadPicture',str(e))
                  return None
        #can't write to cache for some reason
        except IOError:
                return None
        return file



