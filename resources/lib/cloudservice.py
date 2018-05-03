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

PLUGIN_URL = sys.argv[0]

KODI = True
if re.search(re.compile('.py', re.IGNORECASE),PLUGIN_URL) is not None:
    KODI = False


if KODI:
    # cloudservice - standard XBMC modules
    import xbmc, xbmcgui, xbmcplugin
    import xbmcvfs
else:
    from resources.libgui import xbmc
    from resources.libgui import xbmcgui
    from resources.libgui import xbmcplugin
    from resources.libgui import xbmcvfs


from resources.lib import mediaurl
#from resources.lib import settings
from resources.lib import streamer


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


#
#
#
class cloudservice(object):
    # CloudService v0.2.3


    PLAYBACK_RESOLVED = 1
    PLAYBACK_PLAYER = 2
    PLAYBACK_NONE = 3

    def __init__(self): pass


    def getInstanceSetting(self,setting, default=None):
        try:
            return self.addon.getSetting(self.instanceName+'_'+setting)
        except:
            return default


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
    def getHeadersList(self, isPOST=False, additionalHeader=None, additionalValue=None, isJSON=False):
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
    def buildSTRM(self, plugin_handle, path, folderID='', contentType=1, pDialog=None, epath='', dpath='', encfs=False, spreadsheetFile=None, catalog=False, musicPath=None, moviePath=None,tvPath=None,videoPath=None, changeTracking=False, fetchChangeID=False, resolution=False, host=None, force=False, LOGGING=None, changeToken='', skip0Res=False, original=True, transcode=True, append='', removeExt=False):

        if host is None:
            PLUGIN_URL = self.PLUGIN_URL
        else:
            PLUGIN_URL = str(host) + '/default.py'

        xbmc.log("host = " + str(host) + ", PLUGIN_URL = " + str(PLUGIN_URL) + ", self.PLUGIN_URL = " + str(self.PLUGIN_URL), xbmc.LOGDEBUG)
        count = 0
        if catalog:
            if musicPath is None:
                musicPath = path + '/music'
            if moviePath is None:
                moviePath = path + '/movies'
            if tvPath is None:
                tvPath = path + '/tv'
            if videoPath is None:
                videoPath = path + '/video-other'
            xbmcvfs.mkdir(musicPath)
            xbmcvfs.mkdir(tvPath)
            xbmcvfs.mkdir(videoPath)
            xbmcvfs.mkdir(moviePath)
        else:
            xbmcvfs.mkdir(path)

        if changeToken == '0':
            changeToken = ''


        nextPageToken = ''
        largestChangeId = ''
        isContinue = True
        while isContinue:
            if fetchChangeID:
                xbmc.log("changeToken " + str(changeToken) + "largestChangeId " + str(largestChangeId) + " nextPageToken "+ str(nextPageToken), xbmc.LOGDEBUG)
                (mediaItems, nextPageToken, largestChangeId) = self.getChangeList(folderID,contentType=contentType, nextPageToken=nextPageToken, changeToken=changeToken)
                xbmc.log("changeToken " + str(changeToken) + "largestChangeId " + str(largestChangeId) + " nextPageToken "+ str(nextPageToken), xbmc.LOGDEBUG)

            # nothing to process (no new changes)
            # changeToken is blank, change tracking is enabled, so this is the first time run -- we want to fetch the largest change ID but not cycle through the existing change records
            if changeTracking and (largestChangeId == changeToken or changeToken == ''):
                isContinue = False
                break
            if changeTracking:
                if nextPageToken == '' or nextPageToken is None:
                    isContinue = False
                    #self.addon.setSetting(self.instanceName +'_'+str(folderID)+'_changetoken', str(largestChangeId))

            else:
                mediaItems = self.getMediaList(folderID,contentType=contentType)
                isContinue = False


            if mediaItems and not encfs:
                for item in mediaItems:
                    url = 0
                    if not changeTracking and item.file is None:
                        newcount=0
                        if catalog:
                            (newcount,nothing) = self.buildSTRM(plugin_handle,path + '/'+str(item.folder.title), item.folder.id, pDialog=pDialog, spreadsheetFile=spreadsheetFile, catalog=catalog, musicPath=musicPath, moviePath=moviePath,tvPath=tvPath,videoPath=videoPath, resolution=resolution, LOGGING=LOGGING, host=host, skip0Res=skip0Res, original=original, transcode=transcode, append=append, removeExt=removeExt)
                        else:
                            (newcount,nothing) = self.buildSTRM(plugin_handle,path + '/'+str(item.folder.title), item.folder.id, pDialog=pDialog, spreadsheetFile=spreadsheetFile, resolution=resolution, LOGGING=LOGGING, host=host, skip0Res=skip0Res,original=original, transcode=transcode,  append=append, removeExt=removeExt)
                        count += newcount
                    elif item.file is not None:

                        #'content_type': 'video',
                        values = { 'username': self.authorization.username, 'title': item.file.title, 'filename': item.file.id}
                        if item.file.type == 1:
                            url = PLUGIN_URL+ '?mode=audio&' + urllib.urlencode(values)
                        else:
                            url = PLUGIN_URL+ '?mode=video&' + urllib.urlencode(values)

                        #url = self.PLUGIN_URL+'?mode=video&title='+str(item.file.title)+'&filename='+str(item.file.id)+ '&username='+str(self.authorization.username)


                    if url != 0:
                        title = item.file.title
                        year = ''
                        season = ''
                        episode = ''
                        videoResolution = ''
                        show = None

                        if pDialog is not None:
                            pDialog.update(message=title)

                        #if not xbmcvfs.exists(str(path) + '/' + strmFileName):
                        if not catalog:


                            if removeExt:
                                strmFileName = str(path) + '/' + str(re.sub(r'\.[^\.]+$',r'', title))
                            else:
                                strmFileName = str(path) + '/' + str(title)

                            skip = False
                            extraFiles = []
                            if resolution and item.file is not None and item.file.resolution is not None and item.file.resolution[0] != 0:
                                extraFiles.append([strmFileName + ' - '+str(append)+'420p.strm', str(url) + '&preferred_quality=2'])

                                if int(item.file.resolution[0]) > 480:
                                    extraFiles.append([strmFileName + ' - '+str(append)+'720p.strm', str(url) + '&preferred_quality=1'])
                                if int(item.file.resolution[0]) > 720:
                                    extraFiles.append([strmFileName + ' - '+str(append)+'1080p.strm', str(url) + '&preferred_quality=0'])


                                strmFileName += ' - original ' + str(append)+ str(item.file.resolution[0]) + 'p.strm'
                                videoResolution = str(item.file.resolution[0])

                            elif resolution and skip0Res:
                                skip = True

                            else:
                                strmFileName += '.strm'


                            if original and not skip and (not xbmcvfs.exists(strmFileName) or force):
                                strmFile = xbmcvfs.File(strmFileName, "w")

                                if not KODI:
                                    if plugin_handle.server.keyvalue or plugin_handle.server.hide:
                                        params = re.search(r'^([^\?]+)\?([^\?]+)$', str(url))

                                        if params and plugin_handle.server.hide:
                                            base = str(params.group(1))
                                            extended = str(params.group(1))
                                            url = str(base) + '?kv=' +plugin_handle.server.encrypt.encryptString(str(url) + '&original=true')
                                        else:
                                            url = str(url) + '&original=true'

                                strmFile.write(url+'\n')
                                strmFile.close()

                            if transcode and not skip and (not xbmcvfs.exists(strmFileName) or force):
                                for x in extraFiles:
                                    strmFile = xbmcvfs.File(x[0], "w")
                                    tmpURL = x[1]
                                    if not KODI:
                                        if plugin_handle.server.keyvalue or plugin_handle.server.hide:
                                            params = re.search(r'^([^\?]+)\?([^\?]+)$', str(tmpURL))

                                            if params and plugin_handle.server.hide:
                                                base = str(params.group(1))
                                                extended = str(params.group(1))
                                                tmpURL = str(base) + '?kv=' +plugin_handle.server.encrypt.encryptString(tmpURL)
                                            else:
                                                tmpURL = str(tmpURL)
                                    strmFile.write(tmpURL+'\n')
                                    strmFile.close()
                            count += 1
                        elif catalog:
                            episode = ''
                            # nekwebdev contribution
                            pathLib = ''

                            filename = str(title)
                            tv = False
                            tv = item.file.cleantv.match(title)
                            if not tv:
                                tv = item.file.regtv1.match(title)
                            if not tv:
                                tv = item.file.regtv2.match(title)
                            if not tv:
                                tv = item.file.regtv3.match(title)

                            if tv:
                                show = tv.group(1).replace("\S{2,}\.\S{2,}", " ")
                                show = show.rstrip("\.")
                                if not show:
                                    show = tv.group(1).replace("\S{2,}\-\S{2,}", " ")
                                    show = show.rstrip("\-")
                                show = show.strip('.').lower()
                                season = tv.group(2)
                                if len(season) < 2:
                                    season = '0' + str(season)
                                episode = tv.group(3)
                                pathLib = tvPath + '/' + show
                                if not xbmcvfs.exists(xbmc.translatePath(pathLib)):
                                    xbmcvfs.mkdir(xbmc.translatePath(pathLib))
                                pathLib = pathLib +  '/season ' + str(season)
                                if not xbmcvfs.exists(xbmc.translatePath(pathLib)):
                                    xbmcvfs.mkdir(xbmc.translatePath(pathLib))
                                filename = 'S' + str(season) + 'E' + str(episode)
                            else:
                                movie = item.file.cleanmovie.match(title)
                                if not movie:
                                    movie = item.file.regmovie.match(title)
                                if movie:
                                    title = movie.group(1)
                                    title = re.sub(r'\.',r' ', title)
                                    title = title.strip('.').lower()
                                    year = movie.group(2)

                                    filename = str(title) + '(' + str(year) + ')'
                                    pathLib = moviePath +'/'+str(filename)
                                    #xbmcvfs.mkdir(xbmc.translatePath(pathLib))
                                    xbmcvfs.mkdir(pathLib)
                                else:
                                    pathLib = videoPath

                            skip = False
                            if pathLib != '':

                                if removeExt and pathLib == videoPath:
                                    strmFileName = str(pathLib) + '/' + str(re.sub(r'\.[^\.]+$',r'', filename))
                                else:
                                    strmFileName = str(pathLib) + '/' + str(filename)

                                extraFiles = []
                                if resolution and item.file is not None and item.file.resolution is not None and item.file.resolution[0] != 0:

                                    extraFiles.append([strmFileName + ' - '+str(append)+'420p.strm', str(url) + '&preferred_quality=2'])

                                    if int(item.file.resolution[0]) > 480:
                                        extraFiles.append([strmFileName + ' - '+str(append)+'720p.strm', str(url) + '&preferred_quality=1'])
                                    if int(item.file.resolution[0]) > 720:
                                        extraFiles.append([strmFileName + ' - '+str(append)+'1080p.strm', str(url) + '&preferred_quality=0'])


                                    strmFileName += ' - original ' + str(append)+ str(item.file.resolution[0]) + 'p.strm'
                                    videoResolution = str(item.file.resolution[0])

                                elif resolution and skip0Res:
                                    skip = True
                                else:
                                    strmFileName += '.strm'

                                if item.file.deleted and xbmcvfs.exists(strmFileName):
                                    xbmcvfs.delete(filename)
                                elif not skip and not item.file.deleted and (not xbmcvfs.exists(strmFileName) or force):

                                    if original:
                                        strmFile = xbmcvfs.File(strmFileName, "w")

                                        if not KODI:
                                            if plugin_handle.server.keyvalue or plugin_handle.server.hide:
                                                params = re.search(r'^([^\?]+)\?([^\?]+)$', str(url))

                                                if params and plugin_handle.server.hide:
                                                    base = str(params.group(1))
                                                    extended = str(params.group(1))
                                                    url = str(base) + '?kv=' +plugin_handle.server.encrypt.encryptString(str(url) + '&original=true')
                                                else:
                                                    url = str(url) + '&original=true'
                                        strmFile.write(url +'\n')
                                        strmFile.close()

                                    if transcode:
                                        for x in extraFiles:
                                            strmFile = xbmcvfs.File(x[0], "w")
                                            tmpURL = x[1]
                                            if not KODI:
                                                if plugin_handle.server.keyvalue or plugin_handle.server.hide:
                                                    params = re.search(r'^([^\?]+)\?([^\?]+)$', str(tmpURL))

                                                    if params and plugin_handle.server.hide:
                                                        base = str(params.group(1))
                                                        extended = str(params.group(1))
                                                        tmpURL = str(base) + '?kv=' +plugin_handle.server.encrypt.encryptString(tmpURL)
                                                    else:
                                                        tmpURL = str(tmpURL)
                                            strmFile.write(tmpURL+'\n')
                                            strmFile.close()

                                    count += 1

                            if spreadsheetFile is not None:
                                spreadsheetFile.write(str(item.folder.id) + '\t' + str(item.folder.title) + '\t'+str(item.file.id) + '\t'+str(item.file.title) + '\t'+str(episode)+'\t\t\t\t'+str(item.file.checksum) + '\t\t' + "\n")

                            if LOGGING is not None:
                                print >>LOGGING, str(item.folder.id) + '\t' + str(item.folder.title) + '\t'+str(item.file.id) + '\t'+str(item.file.title) + '\t'+str(show) + '\t' + str(season)+'\t'+str(episode)+'\t'+str(title) + '\t'+str(year)+'\t'+str(videoResolution)+'\t'+str(item.file.checksum) + '\t' + "\n"


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
                    mediaList = ['.mp4', '.flv', '.mov', '.webm', '.avi', '.ogg', '.mkv', '.iso', '.rmvb']
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
                        self.buildSTRM(plugin_handle,path + '/'+str(dir), dirListINodes[index].id, pDialog=pDialog, contentType=contentType, encfs=True, dpath=str(dencryptedPath) + str(dir) + '/', epath=str(encryptedPath) + str(encryptedDir) + '/' , spreadsheetFile=spreadsheetFile,changeTracking=changeTracking, resolution=resolution, LOGGING=LOGGING, host=host, skip0Res=skip0Res, original=original, transcode=transcode,  append=append, removeExt=removeExt)

                    elif index in fileListINodes.keys():
                        xbmcvfs.rmdir(encfs_target + str(dencryptedPath) + dir)
                        fileListINodes[index].file.decryptedTitle = dir
                        if contentType < 9 or media_re.search(str(dir)):
                            #service.addMediaFile(fileListINodes[index], contextType=contextType, encfs=True,  dpath=str(dencryptedPath) + str(dir), epath=str(encryptedPath) )
                            #'content_type': 'video',
                            values = { 'username': self.authorization.username, 'encfs':'True', 'dpath': str(dencryptedPath) + str(dir), 'epath': str(encryptedPath), 'title': item.file.title, 'filename': item.file.id}
                            if item.file.type == 1:
                                url = PLUGIN_URL+ '?mode=audio&' + urllib.urlencode(values)
                            else:
                                url = PLUGIN_URL+ '?mode=video&' + urllib.urlencode(values)

                            #url = self.PLUGIN_URL+'?mode=video&title='+str(item.file.title)+'&filename='+str(item.file.id)+ '&username='+str(self.authorization.username)


                        if url != 0:
                            title = str(dir)

                            if pDialog is not None:
                                pDialog.update(message=title)

                            if (not xbmcvfs.exists(str(path) + '/' + str(title)+'.strm') or force):
                                filename = str(path) + '/' + str(title)+'.strm'
                                strmFile = xbmcvfs.File(filename, "w")

                                if not KODI:
                                    if plugin_handle.server.keyvalue or plugin_handle.server.hide:
                                        params = re.search(r'^([^\?]+)\?([^\?]+)$', str(url))

                                        if params and plugin_handle.server.hide:
                                            base = str(params.group(1))
                                            extended = str(params.group(1))
                                            url = str(base) + '?kv=' +plugin_handle.server.encrypt.encryptString(url)
                                        else:
                                            url = str(url)

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
                                url = PLUGIN_URL+ '?mode=audio&' + urllib.urlencode(values)
                            else:
                                url = PLUGIN_URL+ '?mode=video&' + urllib.urlencode(values)

                            #url = self.PLUGIN_URL+'?mode=video&title='+str(item.file.title)+'&filename='+str(item.file.id)+ '&username='+str(self.authorization.username)


                        if url != 0:
                            title = str(dir)

                            if pDialog is not None:
                                pDialog.update(message=title)

                            if (not xbmcvfs.exists(str(path) + '/' + str(title)+'.strm') or force):
                                filename = str(path) + '/' + str(title)+'.strm'
                                strmFile = xbmcvfs.File(filename, "w")

                                if not KODI:
                                    if plugin_handle.server.keyvalue or plugin_handle.server.hide:
                                        params = re.search(r'^([^\?]+)\?([^\?]+)$', str(url))

                                        if params and plugin_handle.server.hide:
                                            base = str(params.group(1))
                                            extended = str(params.group(1))
                                            url = str(base) + '?kv=' +plugin_handle.server.encrypt.encryptString(url)
                                        else:
                                            url = str(url)

                                strmFile.write(url+'\n')
                                strmFile.close()
        return (count, largestChangeId)


    ##
    # retrieve a directory url
    #   parameters: folder id, context type, whether the directory is encfs, encfs:decryption path, encfs:encryption path
    #   returns: fully qualified url
    ##
    def getDirectoryCall(self, folder, contextType='video', encfs=False, dpath='', epath=''):
        if encfs:
            values = {'instance': self.instanceName, 'encfs': 'true', 'folder': folder.id, 'content_type': contextType, 'dpath': dpath, 'epath':epath}
        elif folder.id != '':
            values = {'instance': self.instanceName, 'folder': folder.id, 'content_type': contextType, 'epath':epath}
        elif folder.title != '':
            values = {'instance': self.instanceName, 'foldername': folder.title, 'content_type': contextType, 'epath':epath}


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
            path = None

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
            if not xbmcvfs.exists(str(path) + '/'+ str(package.file.id)):
                xbmcvfs.mkdir(str(path) + '/'+ str(package.file.id))

            playbackFile = str(path) + '/' + str(package.file.id) + '/' + str(mediaURL.order) + '.stream.mp4'

        if not xbmcvfs.exists(str(path) + '/' + str(package.file.id) + '/' + str(package.file.id) + '.name') or force:

            nameFile = xbmcvfs.File(str(path) + '/' + str(package.file.id) + '/' + str(package.file.id)+'.name' , "w")
            nameFile.write(package.file.title +'\n')
            nameFile.close()

        if not xbmcvfs.exists(str(path) + '/' + str(package.file.id) + '/' + str(mediaURL.order) + '.stream.resolution') or force:

            resolutionFile = xbmcvfs.File(str(path) + '/' + str(package.file.id) + '/' + str(mediaURL.order) + '.stream.resolution' , "w")
            resolutionFile.write(mediaURL.qualityDesc +'\n')
            resolutionFile.close()


        if (not xbmcvfs.exists(playbackFile)  or  xbmcvfs.File(playbackFile).size() == 0 or xbmcvfs.File(playbackFile).size() < package.file.size) or force:

            #seek to end of file for append
            # - must use python for append (xbmcvfs not supported)
            # - if path is not local or KODI-specific user must restart complete download
            if  os.path.exists(playbackFile) and xbmcvfs.File(playbackFile).size() < package.file.size and  xbmcvfs.File(playbackFile).size() != 0 and not force:
                req = urllib2.Request(mediaURL.url, None, self.getHeadersList(additionalHeader='Range', additionalValue='bytes='+str(xbmcvfs.File(playbackFile).size())+'-'+str(package.file.size)))

                f = open(playbackFile, 'a')

            else:
                req = urllib2.Request(mediaURL.url, None, self.getHeadersList())

                f = xbmcvfs.File(playbackFile, 'w')


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
                xbmc.log(self.addon.getAddonInfo('name') + ': downloadMediaFile ' + str(e), xbmc.LOGERROR)
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
            while not (player.isPlaying()) and not player.isExit:
                xbmc.sleep(1000)
        #try:
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
        #except



    ##
    # download/retrieve a media file
    #   parameters: whether to playback file, media url object, package object, whether to force download (overwrite), whether the file is encfs, folder name (option)
    ##
    def downloadEncfsFile(self, mediaURL, package, playbackURL='', force=False, folderName='', playback=1,item='', player=None, srt=None):

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

        if sizeDownload < 3000000:
            sizeDownload = 3000000

        CHUNK = int(self.settings.encfsCacheChunkSize)

        if CHUNK < 1024:
            CHUNK = 131072


        path = re.sub(r'\/[^\/]+$', r'', folderName)
        if folderName == path:
            path = re.sub(r'\\[^\\]+$', r'', folderName) #needed for windows?

        #ensure the folder and path exists
        if not xbmcvfs.exists(path):
            xbmcvfs.mkdirs(path)

        playbackFile = folderName

        if (not xbmcvfs.exists(playbackFile) or long(xbmcvfs.File(playbackFile).size()) == 0 or long(xbmcvfs.File(playbackFile).size()) < long(package.file.size)) or force:

            if not self.settings.encfsStream and not self.settings.encfsCacheSingle:
                progress = xbmcgui.DialogProgressBG()
                progressBar = fileSize
                progress.create(self.addon.getLocalizedString(30035), playbackURL)


            downloadedBytes = 0

            #seek to end of file for append
            # - must use python for append (xbmcvfs not supported)
            # - if path is not local or KODI-specific user must restart complete download
            if  os.path.exists(playbackFile) and long(xbmcvfs.File(playbackFile).size()) < long(package.file.size) and  long(xbmcvfs.File(playbackFile).size()) != 0 and not force:
                req = urllib2.Request(mediaURL.url, None, self.getHeadersList(additionalHeader='Range', additionalValue='bytes='+str(xbmcvfs.File(playbackFile).size())+'-'+str(package.file.size)))

                f = open(playbackFile, 'a')


                # if action fails, validate login
                try:
                  response = urllib2.urlopen(req)

                except urllib2.URLError, e:
                  self.refreshToken()
                  req = urllib2.Request(mediaURL.url, None, self.getHeadersList(additionalHeader='Range', additionalValue='bytes='+str(xbmcvfs.File(playbackFile).size())+'-'+str(package.file.size)))
                  try:
                      response = urllib2.urlopen(req)

                  except urllib2.URLError, e:
                    xbmc.log(self.addon.getAddonInfo('name') + ': downloadMediaFile ' + str(e), xbmc.LOGERROR)
                    return

            else:
                req = urllib2.Request(mediaURL.url, None, self.getHeadersList())

                f = xbmcvfs.File(playbackFile, 'w')


                # if action fails, validate login
                try:
                  response = urllib2.urlopen(req)

                except urllib2.URLError, e:
                  self.refreshToken()
                  req = urllib2.Request(mediaURL.url, None, self.getHeadersList())
                  try:
                      response = urllib2.urlopen(req)

                  except urllib2.URLError, e:
                    xbmc.log(self.addon.getAddonInfo('name') + ': downloadMediaFile ' + str(e), xbmc.LOGERROR)
                    return

                while sizeDownload > downloadedBytes:
                    if not self.settings.encfsStream and not self.settings.encfsCacheSingle:
                        progress.update((int)(float(downloadedBytes)/progressBar*100),self.addon.getLocalizedString(30035))
                    chunk = response.read(CHUNK)
                    if not chunk: break
                    f.write(chunk)
                    downloadedBytes = downloadedBytes + CHUNK

        if playbackURL != '':


            if playback == True:#self.PLAYBACK_NONE:

                item.setPath(playbackURL)
                #if playback == self.PLAYBACK_RESOLVED:
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
                #else:
                    #xbmc.executebuiltin("XBMC.PlayMedia("+playbackFile+")")
                #player.PlayStream(playbackURL, item, package.file.resume, startPlayback=True, package=package)
#                while not (player.isPlaying()) and not player.isExit:
#                    xbmc.sleep(1000)

                    # load captions
            if (self.settings.srt or self.settings.cc):
                while not (player.isPlaying()):
                    xbmc.sleep(1000)

                for file in srt:
                    if file != '':
                        try:
                            file = file.decode('unicode-escape')
                            file = file.encode('utf-8')
                        except:
                            file = str(file)
                        player.setSubtitles(file)


            # need to seek?
            #if seek > 0:
            #player.PlayStream('', item, 99, startPlayback=False, package=package)
        try:
            count =1
            while True:
                if (self.settings.encfsStream or not self.settings.encfsContinue) and player is not None and count % 12 == 0:
                    if not player.playStatus:
                        if not self.settings.encfsStream and not self.settings.encfsCacheSingle:
                            progress.close()
                        f.close()
                        return
                count = count + 1
                downloadedBytes = downloadedBytes + CHUNK
                if not self.settings.encfsStream and not self.settings.encfsCacheSingle:
                    progress.update((int)(float(downloadedBytes)/progressBar*100),self.addon.getLocalizedString(30092))
                chunk = response.read(CHUNK)
                if not chunk: break
                f.write(chunk)
                xbmc.sleep(1)

            f.close()
            if not self.settings.encfsStream and not self.settings.encfsCacheSingle:
                progress.close()

        except: return



    ##
    # download/retrieve a media file
    #   parameters: whether to playback file, media url object, package object, whether to force download (overwrite), whether the file is encfs, folder name (option)
    ##
    def downloadEncfsFile2(self, mediaURL, package, playbackURL='', force=False, folderName='', playback=1,item='', player=None, srt=None):

        cachePercent = int(self.settings.encfsCachePercent)

        if cachePercent < 1:
            cachePercent = 1
        elif cachePercent > 100:
            cachePercent = 100

        fileSize = (int)(package.file.size)
        if fileSize == '' or fileSize < 1000:
            fileSize = 5000000

        sizeDownload = fileSize * (cachePercent*0.01)

        if sizeDownload < 3000000:
            sizeDownload = 3000000

        CHUNK = int(self.settings.encfsCacheChunkSize)

        if CHUNK < 1024:
            CHUNK = 131072


        path = re.sub(r'\/[^\/]+$', r'', folderName)
        if folderName == path:
            path = re.sub(r'\\[^\\]+$', r'', folderName) #needed for windows?

        #ensure the folder and path exists
        if not xbmcvfs.exists(path):
            xbmcvfs.mkdirs(path)

        playbackFile = folderName


        #seek to end of file for append
        # - must use python for append (xbmcvfs not supported)
        # - if path is not local or KODI-specific user must restart complete download

        req = urllib2.Request(mediaURL.url, None, self.getHeadersList())

        if (1):

            f = xbmcvfs.File(playbackFile, 'w')


        # if action fails, validate login
        try:
          response = urllib2.urlopen(req)

        except urllib2.URLError, e:
          self.refreshToken()
          req = urllib2.Request(mediaURL.url, None, self.getHeadersList())
          try:
              response = urllib2.urlopen(req)

          except urllib2.URLError, e:
            xbmc.log(self.addon.getAddonInfo('name') + ': downloadMediaFile ' + str(e), xbmc.LOGERROR)
            return

        CHUNK = 4096*100

        header = response.read(CHUNK)
        #f.write(header)
        if (1):
            f.write(header)

            f.close()
        if playbackURL != '':


            if playback == True:#self.PLAYBACK_NONE:


                from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

                try:
                    server = streamer.MyHTTPServer(('', 8006), streamer.myStreamer)
                except:
                    req = urllib2.Request('http://localhost:8005/kill', None, None)
                    try:
                        response = urllib2.urlopen(req)
                    except: return
                    server = streamer.MyHTTPServer(('', 8006), streamer.myStreamer)

                server.setFile(playbackURL,CHUNK, playbackFile, response, fileSize,  mediaURL.url, self)
                item.setPath('http://localhost:8006')
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
                setCC = True
                while server.ready:
                    try:
                        server.handle_request()
                    except:
                        break
                    if (setCC and (self.settings.srt or self.settings.cc)):
                        setCC = False
                        while not (player.isPlaying()):
                            xbmc.sleep(1000)

                        for file in srt:
                            if file != '':
                                try:
                                    file = file.decode('unicode-escape')
                                    file = file.encode('utf-8')
                                except:
                                    file = str(file)
                                player.setSubtitles(file)
                server.socket.close()


                #else:
                    #xbmc.executebuiltin("XBMC.PlayMedia("+playbackFile+")")
                #player.PlayStream(playbackURL, item, package.file.resume, startPlayback=True, package=package)
#                while not (player.isPlaying()) and not player.isExit:
#                    xbmc.sleep(1000)

                    # load captions
            if (self.settings.srt or self.settings.cc):
                while not (player.isPlaying()):
                    xbmc.sleep(1000)

                for file in srt:
                    if file != '':
                        try:
                            file = file.decode('unicode-escape')
                            file = file.encode('utf-8')
                        except:
                            file = str(file)
                        player.setSubtitles(file)



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
                  xbmc.log(self.addon.getAddonInfo('name') + ': downloadGeneralFle ' + str(e), xbmc.LOGERROR)
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
            CHUNK = 131072


        if encfs:
            try:
                path = self.addon.getSetting('encfs_source')
            except:
                path = None
        else:
            try:
                path = self.addon.getSetting('cache_folder')
            except:
                path = None

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
            if not xbmcvfs.exists(str(path) + '/'+str(folderName)):
                xbmcvfs.mkdir(str(path) + '/'+str(folderName))

            playbackFile = str(path) + '/' + str(folderName) + '/' + str(package.file.title)

        else:
            if not xbmcvfs.exists(str(path) + '/'+ str(package.file.id)):
                xbmcvfs.mkdir(str(path) + '/'+ str(package.file.id))

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
                xbmc.log(self.addon.getAddonInfo('name') + ': downloadMediaFile ' + str(e), xbmc.LOGERROR)
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
                progress = None

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

        except: return


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
            xbmcplugin.addDirectoryItem(self.plugin_handle, localPath, listitem,
                                isFolder=True, totalItems=0)
        else:

            if folder.id == 'SAVED SEARCH':
                listitem = xbmcgui.ListItem(decode(folder.displayTitle()), iconImage=decode(folder.thumb), thumbnailImage=decode(folder.thumb))
                values = {'instance': self.instanceName, 'title': folder.title}

                url = self.PLUGIN_URL+'?mode=search&content_type='+contextType + '&' + urllib.urlencode(values)

                xbmcplugin.addDirectoryItem(self.plugin_handle, url, listitem,
                                isFolder=True, totalItems=0)
            elif folder.id == 'CLOUD_DB_GENRE':
                listitem = xbmcgui.ListItem(decode(folder.displayTitle()), iconImage=decode(folder.thumb), thumbnailImage=decode(folder.thumb))
                values = {'instance': self.instanceName, 'title': folder.title}

                url = self.PLUGIN_URL+'?mode=cloud_dbtest&action=genre&content_type='+contextType + '&' + urllib.urlencode(values)

                xbmcplugin.addDirectoryItem(self.plugin_handle, url, listitem,
                                isFolder=True, totalItems=0)
            elif folder.id == 'CLOUD_DB_TITLE':
                listitem = xbmcgui.ListItem(decode(folder.displayTitle()), iconImage=decode(folder.thumb), thumbnailImage=decode(folder.thumb))
                values = {'instance': self.instanceName, 'title': folder.title}

                url = self.PLUGIN_URL+'?mode=cloud_dbtest&action=title&content_type='+contextType + '&' + urllib.urlencode(values)

                xbmcplugin.addDirectoryItem(self.plugin_handle, url, listitem,
                                isFolder=True, totalItems=0)
            elif folder.id == 'CLOUD_DB_RESOLUTION':
                listitem = xbmcgui.ListItem(decode(folder.displayTitle()), iconImage=decode(folder.thumb), thumbnailImage=decode(folder.thumb))
                values = {'instance': self.instanceName, 'title': folder.title}

                url = self.PLUGIN_URL+'?mode=cloud_dbtest&action=resolution&content_type='+contextType + '&' + urllib.urlencode(values)

                xbmcplugin.addDirectoryItem(self.plugin_handle, url, listitem,
                                isFolder=True, totalItems=0)
            elif folder.id == 'CLOUD_DB_YEAR':
                listitem = xbmcgui.ListItem(decode(folder.displayTitle()), iconImage=decode(folder.thumb), thumbnailImage=decode(folder.thumb))
                values = {'instance': self.instanceName, 'title': folder.title}

                url = self.PLUGIN_URL+'?mode=cloud_dbtest&action=year&content_type='+contextType + '&' + urllib.urlencode(values)

                xbmcplugin.addDirectoryItem(self.plugin_handle, url, listitem,
                                isFolder=True, totalItems=0)
            elif folder.id == 'CLOUD_DB_COUNTRY':
                listitem = xbmcgui.ListItem(decode(folder.displayTitle()), iconImage=decode(folder.thumb), thumbnailImage=decode(folder.thumb))
                values = {'instance': self.instanceName, 'title': folder.title}

                url = self.PLUGIN_URL+'?mode=cloud_dbtest&action=country&content_type='+contextType + '&' + urllib.urlencode(values)

                xbmcplugin.addDirectoryItem(self.plugin_handle, url, listitem,
                                isFolder=True, totalItems=0)
            elif folder.id == 'CLOUD_DB_DIRECTOR':
                listitem = xbmcgui.ListItem(decode(folder.displayTitle()), iconImage=decode(folder.thumb), thumbnailImage=decode(folder.thumb))
                values = {'instance': self.instanceName, 'title': folder.title}

                url = self.PLUGIN_URL+'?mode=cloud_dbtest&action=director&content_type='+contextType + '&' + urllib.urlencode(values)

                xbmcplugin.addDirectoryItem(self.plugin_handle, url, listitem,
                                isFolder=True, totalItems=0)
            elif folder.id == 'CLOUD_DB_STUDIO':
                listitem = xbmcgui.ListItem(decode(folder.displayTitle()), iconImage=decode(folder.thumb), thumbnailImage=decode(folder.thumb))
                values = {'instance': self.instanceName, 'title': folder.title}

                url = self.PLUGIN_URL+'?mode=cloud_dbtest&action=studio&content_type='+contextType + '&' + urllib.urlencode(values)

                xbmcplugin.addDirectoryItem(self.plugin_handle, url, listitem,
                                isFolder=True, totalItems=0)
            else:
                listitem = xbmcgui.ListItem(decode(folder.displayTitle()), iconImage=decode(folder.thumb), thumbnailImage=decode(folder.thumb))

                cm=[]

                # is a real folder
                if folder.id != '':

                    if contextType != 'image' and not encfs:
                        values = {'username': self.authorization.username, 'title': folder.title, 'folder': folder.id, 'content_type': contextType }

                        cm.append(( self.addon.getLocalizedString(30042), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=buildstrm&'+ urllib.urlencode(values)+')', ))
                        #if folder.isRoot:
                        #    cm.append(( self.addon.getLocalizedString(30206), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=buildstrm&catalog=true&'+ urllib.urlencode(values)+')', ))

                    #encfs
                    elif contextType != 'image':
                        values = {'username': self.authorization.username, 'epath': epath, 'dpath': dpath, 'encfs':'true' ,'title': folder.title, 'folder': folder.id, 'content_type': contextType }

                        cm.append(( self.addon.getLocalizedString(30042), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=buildstrm&'+ urllib.urlencode(values)+')', ))

                    elif KODI and contextType == 'image':
                        # slideshow
                        if encfs:
                            values = {'encfs': 'true', 'username': self.authorization.username, 'title': folder.title, 'folder': folder.id}
                        else:
                            values = {'username': self.authorization.username, 'title': folder.title, 'folder': folder.id}
                        #cm.append(( self.addon.getLocalizedString(30126), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=slideshow&'+urllib.urlencode(values)+')', ))

                    if (self.protocol == 2):
                        if KODI and contextType != 'image':
                            #download folder
                            values = {'instance': self.instanceName, 'title': folder.title, 'folder': folder.id}
                            cm.append(( self.addon.getLocalizedString(30113), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=downloadfolder&'+urllib.urlencode(values)+')', ))

                        if KODI and contextType == 'audio' and not encfs:
                            #playback entire folder
                            values = {'instance': self.instanceName, 'folder': folder.id}
                            cm.append(( self.addon.getLocalizedString(30162), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=audio&content_type='+contextType+'&'+urllib.urlencode(values)+')', ))
                        elif KODI and contextType == 'video' and not encfs:
                            #playback entire folder
                            values = {'instance': self.instanceName, 'folder': folder.id}
                            cm.append(( self.addon.getLocalizedString(30162), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=video&content_type='+contextType+'&'+urllib.urlencode(values)+')', ))


                        #add encfs option unless viewing as encfs already
                        if not encfs:
                            cm.append((  self.addon.getLocalizedString(30192), 'XBMC.Container.Update('+self.PLUGIN_URL+'?mode=index&content_type='+contextType+'&encfs=true&'+urllib.urlencode(values)+')', ))
                        cm.append((  self.addon.getLocalizedString(30193), 'XBMC.Container.Update('+self.PLUGIN_URL+'?mode=index&content_type='+contextType+'&encfs=true&'+urllib.urlencode(values)+')', ))

                        cm.append((  self.addon.getLocalizedString(30126), 'XBMC.Container.Update('+self.PLUGIN_URL+'?mode=slideshow&content_type='+contextType+'&'+urllib.urlencode(values)+')', ))

                        #if within encfs and pictures, disable right-click default photo options; add download-folder
                        if KODI and encfs and contextType == 'image':
                            values = {'instance': self.instanceName, 'epath': epath, 'foldername': folder.title, 'folder': folder.id}

                            cm.append(( self.addon.getLocalizedString(30113), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=downloadfolder&content_type='+contextType+'&encfs=true&'+urllib.urlencode(values)+')', ))
                            listitem.addContextMenuItems(cm, True)
                        elif KODI and contextType == 'image':
                            cm.append(( self.addon.getLocalizedString(30113), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=downloadfolder&content_type='+contextType+'&'+urllib.urlencode(values)+')', ))


                    if KODI:
                        cm.append(( self.addon.getLocalizedString(30163), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=scan&content_type='+contextType+'&'+urllib.urlencode(values)+')', ))

                else:

                    if contextType != 'image' and not encfs:
                        values = {'username': self.authorization.username, 'title': folder.title,  'content_type': contextType }

                        cm.append(( self.addon.getLocalizedString(30042), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=buildstrm&'+ urllib.urlencode(values)+')', ))
                        if folder.isRoot:
                            cm.append(( self.addon.getLocalizedString(30201), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=buildstrm2&'+ urllib.urlencode(values)+')', ))


                listitem.addContextMenuItems(cm, False)
                listitem.setProperty('fanart_image',  folder.fanart)

                xbmcplugin.addDirectoryItem(self.plugin_handle, self.getDirectoryCall(folder, contextType, encfs=encfs, dpath=dpath, epath=epath), listitem,
                                isFolder=True, totalItems=0)


    ##
    # Add a media file to a directory listing screen
    #   parameters: package, context type, whether file is encfs, encfs:decryption path, encfs:encryption path
    ##
    def addMediaFile(self, package, contextType='video', encfs=False, dpath='', epath='', isMock=False):
        #thumbnail = self.cache.getThumbnail(self, package.file.thumbnail,package.file.id)
        listitem = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail)

        # audio file, not in "pictures"
        if package.file.type == package.file.AUDIO and contextType != 'image':
            if package.file.hasMeta:
                #infolabels = decode_dict({ 'title' : package.file.displayTrackTitle(), 'tracknumber' : package.file.trackNumber, 'artist': package.file.artist, 'album': package.file.album,'genre': package.file.genre,'premiered': package.file.releaseDate, 'size' : package.file.size })
                infolabels = decode_dict({ 'title' : package.file.displayTitle(), 'size' : package.file.size })
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
            if float(package.file.cloudResume) > 0:
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
                if package.file.actors != None:
                    infolabels = decode_dict({ 'title' : package.file.displayTitle() , 'cast': package.file.actors,  'plot' : package.file.plot,  'ratingandvotes' : package.file.rating, 'director': package.file.director, 'set': package.file.set, 'country': package.file.country, 'genre': package.file.genre, 'year': package.file.year,  'size' : package.file.size})
                else:
                    infolabels = decode_dict({ 'title' : package.file.displayTitle() , 'plot' : package.file.plot,  'ratingandvotes' : package.file.rating, 'director': package.file.director, 'set': package.file.set, 'country': package.file.country, 'genre': package.file.genre, 'year': package.file.year,  'size' : package.file.size})


            listitem.setInfo('Video', infolabels)
            playbackURL = '?mode=video'
            if self.integratedPlayer:
                listitem.setProperty('IsPlayable', 'false')
            else:
                listitem.setProperty('IsPlayable', 'true')

            if float(package.file.cloudResume) > 0:
                listitem.setProperty('isResumable', "1")
            if int(package.file.playcount) > 0: #or (float(package.file.resume) > 0 and package.file.duration > 0 and package.file.resume/package.file.duration > (1-self.settskipResume)):
                listitem.setInfo('video', {'playcount':int(package.file.playcount)})

            if package.file.resolution is not None and int(package.file.resolution[0]) > 0:
                listitem.addStreamInfo('video', {'width': package.file.resolution[1], 'height': package.file.resolution[0], 'duration':package.file.duration})

        # image file
        elif package.file.type == package.file.PICTURE:
            infolabels = decode_dict({ 'title' : package.file.displayTitle() , 'plot' : package.file.plot, 'size' : package.file.size })
            listitem.setInfo('Pictures', infolabels)
            listitem.setProperty('mimetype', 'image/jpeg')

            playbackURL = '?mode=photo'
#            listitem.setProperty('IsPlayable', 'false')
            listitem.setProperty('IsPlayable', 'true')
            if package.mediaurl.url != '':
                # resized photos do not need authentication
                url = package.mediaurl.url# +'|' + self.getHeadersEncoded()
            else:
                url = package.file.download+'|' + self.getHeadersEncoded()
            xbmcplugin.addDirectoryItem(self.plugin_handle, url, listitem,
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
            if float(package.file.cloudResume) > 0:
                listitem.setProperty('isResumable', 1)

        listitem.setProperty('fanart_image', package.file.fanart)
        if package.file.cloudResume > 0:
            listitem.setProperty('ResumeTime', str(package.file.resume))
        if package.file.duration > 0:
            listitem.setProperty('TotalTime', str(package.file.duration))


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

        elif package.file.id == '':
            values = {'instance': self.instanceName, 'title': package.file.title, 'sheet': 'x', 'year': package.file.year, 'folder': package.folder.id}

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
                #cm.append(( self.addon.getLocalizedString(30201), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=buildstrm2&type='+str(package.file.type)+'&'+urllib.urlencode(valuesBS)+')', ))

            if (self.protocol == 2):
                # play-original for video only
                if (KODI and contextType == 'video'):
                    if (package.file.type != package.file.AUDIO and self.settings.promptQuality) and not encfs:
                        cm.append(( self.addon.getLocalizedString(30123), 'XBMC.RunPlugin('+url + '&strm=false&original=true'+')', ))
                    else:
                        cm.append(( self.addon.getLocalizedString(30151), 'XBMC.RunPlugin('+url + '&strm=false&promptquality=true'+')', ))

                    # if the options are disabled in settings, display option to playback with feature
                    if not self.settings.srt:
                        cm.append(( self.addon.getLocalizedString(30138), 'XBMC.RunPlugin('+url + '&strm=false&srt=true'+')', ))
                    if not self.settings.cc:
                        cm.append(( self.addon.getLocalizedString(30146), 'XBMC.RunPlugin('+url + '&strm=false&cc=true'+')', ))

                    cm.append(( self.addon.getLocalizedString(30147), 'XBMC.RunPlugin('+url + '&strm=false&seek=true'+')', ))
#                    cm.append(( self.addon.getLocalizedString(30148), 'XBMC.RunPlugin('+url + '&resume=true'+')', ))
#                    values = {'instance': self.instanceName, 'folder': package.folder.id}
#                    folderurl = self.PLUGIN_URL+ str(playbackURL)+ '&' + urllib.urlencode(values)
#                    cm.append(( 'folder', 'XBMC.RunPlugin('+folderurl+')', ))
                elif (contextType == 'video'):
                    cm.append(( self.addon.getLocalizedString(30228) + 'SD', 'XBMC.RunPlugin('+url + '&preferred_quality=2'+')', ))
                    if package.file.resolution is not None and int(package.file.resolution[0]) > 480:
                        cm.append(( self.addon.getLocalizedString(30228) + '720p', 'XBMC.RunPlugin('+url + '&preferred_quality=1'+')', ))
                    if package.file.resolution is not None and int(package.file.resolution[0]) > 720:
                        cm.append(( self.addon.getLocalizedString(30228) + '1080p', 'XBMC.RunPlugin('+url + '&preferred_quality=0'+')', ))



                if KODI and contextType != 'image':
                    # download
                    cm.append(( self.addon.getLocalizedString(30113), 'XBMC.RunPlugin('+url + '&download=true'+')', ))

                    # download + watch
                    if not encfs:
                        cm.append(( self.addon.getLocalizedString(30124), 'XBMC.RunPlugin('+url + '&play=true&download=true'+')', ))



        elif KODI and package.file.type ==  package.file.PICTURE: #contextType == 'image':

                cm.append(( self.addon.getLocalizedString(30126), 'XBMC.SlideShow('+self.PLUGIN_URL+ '?mode=index&' + urllib.urlencode(values)+')', ))

        #encfs
#        if (self.protocol == 2):
#            cm.append(( self.addon.getLocalizedString(30130), 'XBMC.RunPlugin('+self.PLUGIN_URL+ '?mode=downloadfolder&encfs=true&' + urllib.urlencode(values)+'&content_type='+contextType+')', ))

        #CLOUD_DB
        if self.gSpreadsheet is not None:
                cm.append(( self.addon.getLocalizedString(30177) + self.addon.getLocalizedString(30178),  'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=cloud_db&' + urllib.urlencode(values) + '&action=watch'+')', ))
                cm.append(( self.addon.getLocalizedString(30177) + self.addon.getLocalizedString(30179),  'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=cloud_db&' + urllib.urlencode(values) + '&action=queue'+')', ))

        url = url + '&content_type='+contextType

        #    listitem.addContextMenuItems( commands )
        #    if cm:
        if  package.file.type ==  package.file.PICTURE: #contextType == 'image':
            listitem.addContextMenuItems(cm, True)
        else:
            listitem.addContextMenuItems(cm, False)

        if not isMock:
            xbmcplugin.addDirectoryItem(self.plugin_handle, url, listitem,
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
                    #originalURL = mediaURL.url
        else:
            for mediaURL in mediaURLs:
                options.append(mediaURL.qualityDesc)
                newMediaURLs.append(mediaURL)
                #if mediaURL.qualityDesc == 'original':
                    #originalURL = mediaURL.url

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
        # if we are not downloading-only
        if self.settings.play:
            (localResolutions,localFiles) = self.cache.getFiles(self)
        totalList = localFiles + newMediaURLs
        mediaCount = len(localFiles)

        if KODI and self.settings.promptQuality:
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
                  xbmc.log(self.addon.getAddonInfo('name') + ': downloadPicture ' + str(e), xbmc.LOGERROR)
                  return None
        #can't write to cache for some reason
        except IOError:
                return None
        return file



