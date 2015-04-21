'''
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

import os
import re
import urllib, urllib2
import xbmc, xbmcaddon, xbmcgui, xbmcplugin
import xbmcvfs


#
#
#
class cloudservice(object):
    # CloudService v0.2.3

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
        if self.authorization.isUpdated and addon.getSetting(self.instanceName+'_save_auth_token') == 'true':
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

    # helper methods
    def log(msg, err=False):
        if err:
            xbmc.log(self.addon.getAddonInfo('name') + ': ' + msg, xbmc.LOGERROR)
        else:
            xbmc.log(self.addon.getAddonInfo('name') + ': ' + msg, xbmc.LOGDEBUG)


    def traverse(self, path, cacheType, folderID, savePublic, level):
        import os
        import xbmcvfs

        xbmcvfs.mkdir(path)

        folders = self.getFolderList(folderID)
        files = self.getMediaList(folderID,contentType=contentType)

        if files:
            for media in files:
                filename = xbmc.translatePath(os.path.join(path, media.title+'.strm'))
                strmFile = open(filename, "w")

                strmFile.write(self.PLUGIN_URL+'?mode=streamURL&url=' + self.FILE_URL+ media.id +'\n')
                strmFile.close()

        if folders and level == 1:
            count = 1
            progress = xbmcgui.DialogProgress()
            progress.create(self.addon.getLocalizedString(30000),self.addon.getLocalizedString(30036),'\n','\n')

            for folder in folders:
                max = len(folders)
                progress.update(count/max*100,self.addon.getLocalizedString(30036),folder.title,'\n')
                self.traverse( path+'/'+folder.title + '/',cacheType,folder.id,savePublic,0)
                count = count + 1

        if folders and level == 0:
            for folder in folders:
                self.traverse( path+'/'+folder.title + '/',cacheType,folder.id,savePublic,0)

    ##
    # build STRM files to a given path for a given folder ID
    ##
    def buildSTRM(self, path, folderID='', contentType=7, pDialog=None):

        import xbmcvfs
        xbmcvfs.mkdir(path)

        mediaItems = self.getMediaList(folderID,contentType=contentType)

        if mediaItems:
            for item in mediaItems:

                url = 0
                if item.file is None:
                    self.buildSTRM(path + '/'+item.folder.title, item.folder.id, pDialog=pDialog)
                else:
                    url = self.PLUGIN_URL+'?mode=video&title='+item.file.title+'&filename='+item.file.id+ '&username='+self.authorization.username


                if url != 0:
                    title = item.file.title

                    if pDialog is not None:
                        pDialog.update(message=title)

                    if not xbmcvfs.exists(path + title+'.strm'):
                        filename = path + '/' + title+'.strm'
                        strmFile = xbmcvfs.File(filename, "w")

                        strmFile.write(url+'\n')
                        strmFile.close()

                    # nekwebdev contribution
                    if self.addon.getSetting('tvshows_path') != '' or self.addon.getSetting('movies_path') != '':
                        pathLib = ''
                        regtv1 = re.compile('(.+?)'
                                       '[ .]S(\d\d?)E(\d\d?)'
                                       '.*?'
                                       '(?:[ .](\d{3}\d?p)|\Z)?')
                        regtv2 = re.compile('(.+?)'
                                       '[ .]s(\d\d?)e(\d\d?)'
                                       '.*?'
                                       '(?:[ .](\d{3}\d?p)|\Z)?')
                        regtv3 = re.compile('(.+?)'
                                       '[ .](\d\d?)x(\d\d?)'
                                       '.*?'
                                       '(?:[ .](\d{3}\d?p)|\Z)?')
                        regtv4 = re.compile('(.+?)'
                                       '[ .](\d\d?)X(\d\d?)'
                                       '.*?'
                                       '(?:[ .](\d{3}\d?p)|\Z)?')
                        regmovie = re.compile('(.*?[ .]\d{4})'
                                          '.*?'
                                          '(?:[ .](\d{3}\d?p)|\Z)?')

                        tv = regtv1.match(title)
                        if not tv:
                            tv = regtv2.match(title)
                        if not tv:
                            tv = regtv3.match(title)
                        if not tv:
                            tv = regtv4.match(title)

                        if tv and self.addon.getSetting('tvshows_path') != '':
                            show = tv.group(1).replace(".", " ")
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
                            if not xbmcvfs.exists(pathLib + title+'.strm'):
                                filename = path + '/' + title+'.strm'
                                strmFile = xbmcvfs.File(filename, "w")
                                strmFile.write(url+'\n')
                                strmFile.close()

    ##
    # retrieve a directory url
    #   returns: url
    ##
    def getDirectoryCall(self, folder, contextType='video'):
        return self.PLUGIN_URL+'?mode=index&instance='+str(self.instanceName)+'&folder='+str(folder.id)+'&content_type='+str(contextType)


    ##
    # retrieve a media file
    #   parameters: title of video, whether to prompt for quality/format (optional),
    ##
    def downloadMediaFile(self, playback, url, title, folderID, filename, fileSize, force=False, encfs=False, folderName=''):


        try:
            cachePercent = int(self.addon.getSetting('cache_percent'))
        except:
            cachePercent = 10

        if cachePercent < 1:
            cachePercent = 1
        elif cachePercent > 100:
            cachePercent = 100
        fileSize = (int)(fileSize)
        if fileSize == '' or fileSize < 1000:
            fileSize = 5000000

        sizeDownload = fileSize * (cachePercent*0.01)

        if sizeDownload < 1000000:
            sizeDownload = 1000000

        CHUNK = 0
        try:
            CHUNK = int(self.addon.getSetting('chunk_size'))
        except:
            CHUNK = 32 * 1024

        if CHUNK < 1024:
            CHUNK = 16 * 1024

        count = 0

        try:
            cacheSingleFile = self.addon.getSetting('cache_single')
            if cacheSingleFile == 'true':
                cacheSingleFile = True
                force = True
            else:
                cacheSingleFile = False
        except:
            cacheSingleFile = False


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

        if not xbmcvfs.exists(path):
            path = ''

        while path == '':
            path = xbmcgui.Dialog().browse(0,self.addon.getLocalizedString(30090), 'files','',False,False,'')
            if not xbmcvfs.exists(path):
                path = ''
            else:
                self.addon.setSetting('cache_folder', path)


        if encfs:
            try:
                xbmcvfs.mkdir(str(path) + '/'+str(folderName))
            except: pass

            playbackFile = str(path) + '/' + str(folderName) + '/' + str(title)

        elif cacheSingleFile:
            playbackFile = str(path) + '/cache.mp4'

        else:
            try:
                xbmcvfs.mkdir(str(path) + '/'+str(folderID))
            except: pass

            try:
                xbmcvfs.mkdir(str(path) + '/'+str(folderID)+ '/' + str(filename))
            except: pass

            playbackFile = str(path) + '/' + str(folderID) + '/' + str(filename) + '/' + str(title)


        if not xbmcvfs.exists(playbackFile) or force:

            req = urllib2.Request(url, None, self.getHeadersList())

            f = xbmcvfs.File(playbackFile, 'w')


            if playback != '':
                progress = xbmcgui.DialogProgress()
                progressBar = sizeDownload
                progress.create(self.addon.getLocalizedString(30000), self.addon.getLocalizedString(30035), title)
            else:
                progress = xbmcgui.DialogProgressBG()
                progressBar = fileSize
                progress.create(self.addon.getLocalizedString(30035), title)

            # if action fails, validate login
            try:
              response = urllib2.urlopen(req)

            except urllib2.URLError, e:
              self.refreshToken()
              req = urllib2.Request(url, None, self.getHeadersList())
              try:
                  response = urllib2.urlopen(req)

              except urllib2.URLError, e:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                self.crashreport.sendError('downloadPicture',str(e))
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

            item = xbmcgui.ListItem(path=playbackFile)
            item.setInfo( type="Video", infoLabels={ "Title": title , "Plot" : title } )
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
