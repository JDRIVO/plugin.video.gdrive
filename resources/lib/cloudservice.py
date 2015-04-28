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

#import os
import re
import urllib, urllib2
import xbmc, xbmcaddon, xbmcgui, xbmcplugin
import xbmcvfs
import sys

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
#                filename = xbmc.translatePath(os.path.join(path, media.title+'.strm'))
#                strmFile = open(filename, "w")
                filename = path + '/' + str(media.title)+'.strm'
                strmFile = xbmcvfs.File(filename, "w")
                strmFile.write(self.PLUGIN_URL+'?mode=streamURL&url=' + self.FILE_URL+ str(media.id) +'\n')
                strmFile.close()

 #               strmFile.write(self.PLUGIN_URL+'?mode=streamURL&url=' + self.FILE_URL+ media.id +'\n')
 #               strmFile.close()

        if folders and level == 1:
            count = 1
            progress = xbmcgui.DialogProgress()
            progress.create(self.addon.getLocalizedString(30000),self.addon.getLocalizedString(30036),'\n','\n')

            for folder in folders:
                max = len(folders)
                progress.update(count/max*100,self.addon.getLocalizedString(30036),folder.title,'\n')
                self.traverse( path+'/'+str(folder.title) + '/',cacheType,folder.id,savePublic,0)
                count = count + 1

        if folders and level == 0:
            for folder in folders:
                self.traverse( path+'/'+str(folder.title) + '/',cacheType,folder.id,savePublic,0)

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
                    self.buildSTRM(path + '/'+str(item.folder.title), item.folder.id, pDialog=pDialog)
                else:
                    #'content_type': 'video',
                    values = { 'username': self.authorization.username, 'title': item.file.title, 'filename': item.file.id}
                    url = self.PLUGIN_URL+ '?mode=video&' + urllib.urlencode(values)
                    #url = self.PLUGIN_URL+'?mode=video&title='+str(item.file.title)+'&filename='+str(item.file.id)+ '&username='+str(self.authorization.username)


                if url != 0:
                    title = item.file.title

                    if pDialog is not None:
                        pDialog.update(message=title)

                    if not xbmcvfs.exists(str(path) + str(title)+'.strm'):
                        filename = str(path) + '/' + str(title)+'.strm'
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
                            if not xbmcvfs.exists(pathLib + str(title)+'.strm'):
                                filename = str(path) + '/' + str(title)+'.strm'
                                strmFile = xbmcvfs.File(filename, "w")
                                strmFile.write(url+'\n')
                                strmFile.close()

    ##
    # retrieve a directory url
    #   returns: url
    ##
    def getDirectoryCall(self, folder, contextType='video'):
        values = {'instance': self.instanceName,   'folder': folder.id, 'content_type': contextType}

        return self.PLUGIN_URL+'?mode=index&' +  urllib.urlencode(values)


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



    def addDirectory(self, folder, contextType='video', localPath=''):

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
                    if contextType != 'image':
                        values = {'username': self.authorization.username, 'title': folder.title, 'folder': folder.id, 'content_type': contextType }

                        cm.append(( self.addon.getLocalizedString(30042), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=buildstrm&'+ urllib.urlencode(values)+')', ))
                    elif contextType == 'image':
                        values = {'username': self.authorization.username, 'title': folder.title, 'folderID': folder.id}
                        cm.append(( self.addon.getLocalizedString(30126), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=slideshow&'+urllib.urlencode(values)+')', ))

                    #download folder
                    if (self.protocol == 2):
                        values = {'instance': self.instanceName, 'title': folder.title, 'folder': folder.id}
                        cm.append(( self.addon.getLocalizedString(30113), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=downloadfolder&'+urllib.urlencode(values)+')', ))

                        #encfs
                        values = {'instance': self.instanceName, 'foldername': folder.title, 'folder': folder.id}
                        cm.append(( self.addon.getLocalizedString(30130), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=downloadfolder&content_type='+contextType+'&encfs=true&'+urllib.urlencode(values)+')', ))

                listitem.addContextMenuItems(cm, False)
                listitem.setProperty('fanart_image', fanart)

                xbmcplugin.addDirectoryItem(plugin_handle, self.getDirectoryCall(folder, contextType), listitem,
                                isFolder=True, totalItems=0)



    def addMediaFile(self, package, contextType='video'):

        listitem = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail)

        if package.file.type == package.file.AUDIO and contextType != 'image':
            if package.file.hasMeta:
                infolabels = decode_dict({ 'title' : package.file.displayTitle(), 'tracknumber' : package.file.trackNumber, 'artist': package.file.artist, 'album': package.file.album,'genre': package.file.genre,'premiered': package.file.releaseDate, 'size' : package.file.size })
            else:
                infolabels = decode_dict({ 'title' : package.file.displayTitle(), 'size' : package.file.size })
            listitem.setInfo('Music', infolabels)
            playbackURL = '?mode=audio'
            if self.integratedPlayer:
                listitem.setProperty('IsPlayable', 'false')
            else:
                listitem.setProperty('IsPlayable', 'true')
        elif package.file.type == package.file.AUDIO and contextType == 'image':
            if package.file.hasMeta:
                infolabels = decode_dict({ 'title' : package.file.displayTitle(), 'tracknumber' : package.file.trackNumber, 'artist': package.file.artist, 'album': package.file.album,'genre': package.file.genre,'premiered': package.file.releaseDate, 'size' : package.file.size })
            else:
                infolabels = decode_dict({ 'title' : package.file.displayTitle(), 'size' : package.file.size })
            listitem.setInfo('Music', infolabels)
            playbackURL = '?mode=audio'
            listitem.setProperty('IsPlayable', 'false')

        elif package.file.type == package.file.VIDEO:
            infolabels = decode_dict({ 'title' : package.file.displayTitle() , 'plot' : package.file.plot, 'size' : package.file.size })
            listitem.setInfo('Video', infolabels)
            playbackURL = '?mode=video'
            if self.integratedPlayer:
                listitem.setProperty('IsPlayable', 'false')
            else:
                listitem.setProperty('IsPlayable', 'true')
        elif package.file.type == package.file.PICTURE:
            infolabels = decode_dict({ 'title' : package.file.displayTitle() , 'plot' : package.file.plot })
            listitem.setInfo('Pictures', infolabels)
            playbackURL = '?mode=photo'
            listitem.setProperty('IsPlayable', 'false')
        else:
            infolabels = decode_dict({ 'title' : package.file.displayTitle() , 'plot' : package.file.plot, 'size' : package.file.size })
            listitem.setInfo('Video', infolabels)
            playbackURL = '?mode=video'
            if self.integratedPlayer:
                listitem.setProperty('IsPlayable', 'false')
            else:
                listitem.setProperty('IsPlayable', 'true')

        listitem.setProperty('fanart_image', package.file.fanart)
        cm=[]

        try:
            url = package.getMediaURL()
            cleanURL = re.sub('---', '', url)
            cleanURL = re.sub('&', '---', cleanURL)
        except:
            cleanURL = ''

    #    url = PLUGIN_URL+playbackURL+'&title='+package.file.title+'&filename='+package.file.id+'&instance='+str(self.instanceName)+'&filesize='+str(package.file.size)+'&folder='+str(package.folder.id)
        values = {'instance': self.instanceName, 'title': package.file.title, 'filename': package.file.id, 'filesize': package.file.size, 'folder': package.folder.id}
        url = self.PLUGIN_URL+ str(playbackURL)+ '&' + urllib.urlencode(values)

        if (contextType != 'image' and package.file.type != package.file.PICTURE):
            valuesBS = {'username': self.authorization.username, 'title': package.file.title, 'filename': package.file.id, 'filesize': package.file.size, 'content_type': 'video'}
            cm.append(( self.addon.getLocalizedString(30042), 'XBMC.RunPlugin('+self.PLUGIN_URL+'?mode=buildstrm&'+urllib.urlencode(valuesBS)+')', ))

            if (self.protocol == 2):
                # download
                cm.append(( self.addon.getLocalizedString(30113), 'XBMC.RunPlugin('+url + '&download=true'+')', ))
                # download + watch
                cm.append(( self.addon.getLocalizedString(30124), 'XBMC.RunPlugin('+url + '&play=true&download=true'+')', ))
                # watch downloaded copy
                cm.append(( self.addon.getLocalizedString(30125), 'XBMC.RunPlugin('+url + '&cache=true'+')', ))

                # play-original for video only
                if (contextType == 'video'):
                    cm.append(( self.addon.getLocalizedString(30123), 'XBMC.RunPlugin('+url + '&original=true'+')', ))
                    cm.append(( self.addon.getLocalizedString(30138), 'XBMC.RunPlugin('+url + '&srt=true'+')', ))
                    cm.append(( self.addon.getLocalizedString(30146), 'XBMC.RunPlugin('+url + '&cc=true'+')', ))
                    cm.append(( self.addon.getLocalizedString(30147), 'XBMC.RunPlugin('+url + '&seek=true'+')', ))


        elif contextType == 'image':

            cm.append(( self.addon.getLocalizedString(30126), 'XBMC.RunPlugin('+self.PLUGIN_URL+ '?mode=slideshow&' + urllib.urlencode(values)+')', ))

        #encfs
        if (self.protocol == 2):
            cm.append(( self.addon.getLocalizedString(30130), 'XBMC.RunPlugin('+self.PLUGIN_URL+ '?mode=downloadfolder&encfs=true&' + urllib.urlencode(values)+'&content_type='+contextType+')', ))


        url = url + '&content_type='+contextType

        #    listitem.addContextMenuItems( commands )
        #    if cm:
        listitem.addContextMenuItems(cm, False)


        xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
                                isFolder=False, totalItems=0)
        return url



