'''
    Copyright (C) 2014-2015 ddurdle

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

# cloudservice - standard modules
import os

# cloudservice - standard XBMC modules
import xbmcgui, xbmcvfs

#
# This class handles fetching files from local when cached, rather then making calls to the web service
#
class cache:
    # CloudService v0.2.3

    ##
    ##
    def __init__(self, package=None):
        self.package = package
        self.cachePath = ''
        self.files = []

    ##
    #  set the media package
    ##
    def setPackage(self, package):
        self.package = package


    ##
    #  set the SRT
    ##
    def setSRT(self, service):
        if self.cachePath == '':
            cachePath = service.settings.cachePath
        else:
            cachePath = self.cachePath

        if cachePath == '':
            cachePath = xbmcgui.Dialog().browse(0,service.addon.getLocalizedString(30136), 'files','',False,False,'')
            service.addon.setSetting('cache_folder', cachePath)
            self.cachePath = cachePath

        if cachePath != '':
            cachePath = str(cachePath) + '/' + str(self.package.file.id)+'/'#+ '.'+str(lang)+'.srt'
            if not xbmcvfs.exists(cachePath):
                xbmcvfs.mkdir(cachePath)
            srt = service.getSRT(self.package.file.title)
            if srt:
                for file in srt:
                    if not service.settings.cachePath or not xbmcvfs.exists(cachePath + str(file[0])):
                        service.downloadPicture(file[1], cachePath + str(file[0]))

    ##
    #  set the CC
    ##
    def setCC(self, service):
        if self.cachePath == '':
            cachePath = service.settings.cachePath
        else:
            cachePath = self.cachePath

        if cachePath == '':
            cachePath = xbmcgui.Dialog().browse(0,service.addon.getLocalizedString(30136), 'files','',False,False,'')
            service.addon.setSetting('cache_folder', cachePath)
            self.cachePath = cachePath

        if cachePath != '':
            cachePath = str(cachePath) + '/' + str(self.package.file.id)+'/'#+ '.'+str(lang)+'.srt'
            if not xbmcvfs.exists(cachePath):
                xbmcvfs.mkdir(cachePath)
            cachePath = str(cachePath) + str(self.package.file.id)
            cc = service.getTTS(self.package.file.srtURL)
            if cc:
                for file in cc:
                    if not service.settings.cachePath or not xbmcvfs.exists(cachePath + str(file[0])):
                        service.downloadTTS(file[1], cachePath + str(file[0]))

    ##
    #  fetch the SRT
    ##
    def getSRT(self, service):
        cc = []
        dirs, files = xbmcvfs.listdir(service.settings.cachePath + '/'+ str(self.package.file.id) + '/')
        for file in files:
            if os.path.splitext(file)[1] == '.srt':
                cc.append(service.settings.cachePath + '/'+ str(self.package.file.id) + '/' + file)
        return cc

    ##
    #  set the thumbnail
    ##
    def setThumbnail(self, service, url=''):
        if self.cachePath == '':
            cachePath = service.settings.cachePath
        else:
            cachePath = self.cachePath

        if cachePath == '':
            cachePath = xbmcgui.Dialog().browse(0,service.addon.getLocalizedString(30136), 'files','',False,False,'')
            service.addon.setSetting('cache_folder', cachePath)
            self.cachePath = cachePath

        if url == '':
            url = self.package.file.thumbnail

        #simply no thumbnail
        if url == '':
            return ""

        cachePath = str(cachePath) + str(self.package.file.id) + '/'
        if not xbmcvfs.exists(cachePath):
            xbmcvfs.mkdir(cachePath)
        if not xbmcvfs.exists(cachePath + str(self.package.file.id) + '.jpg'):
            service.downloadPicture(url, cachePath + str(self.package.file.id) + '.jpg')
            print url
        return cachePath + str(self.package.file.id) + '.jpg'


    ##
    #  get the thumbnail
    ##
    def getThumbnail(self,service, url='', fileID=''):
        if fileID == '':
            if xbmcvfs.exists(str(self.cachePath) + str(self.package.file.id) + '/' + str(self.package.file.id) + '.jpg'):
                return str(self.cachePath) + str(self.package.file.id) + '/' + str(self.package.file.id) + '.jpg'
            else:
                return self.package.file.thumbnail
        else:
            if xbmcvfs.exists(str(self.cachePath) + str(fileID) + '/' + str(fileID) + '.jpg'):
                return str(self.cachePath) + str(fileID) + '/' + str(fileID) + '.jpg'
            else:
                return url + '|' + service.getHeadersEncoded()

    ##
    #  get a list of offline files for this file
    ##
    def getFiles(self,service):
        if self.cachePath == '':
            cachePath = service.settings.cachePath
        else:
            cachePath = self.cachePath

        cachePath = cachePath + '/' + self.package.file.id + '/'
        localResolutions = []
        localFiles = []
        if xbmcvfs.exists(cachePath):
            dirs,files = xbmcvfs.listdir(cachePath)
            for file in files:
                if os.path.splitext(file)[1] == '.stream':
                    try:
                        resolutionFile = xbmcvfs.File(cachePath  + str(file) + '.resolution')
                        resolution = resolutionFile.read()
                        resolutionFile.close()
                    except:
                        resolution = file
                    localResolutions.append('offline - ' + str(resolution))
                    localFiles.append(cachePath + file)

        return (localResolutions,localFiles)


    ##
    #  get a list of offline files
    ##
    def getOfflineFileList(self, fileID):
        localFiles = []
        if xbmcvfs.exists(self.cachePath):
            dirs,files = xbmcvfs.listdir(self.cachePath)
            for file in files:
                if os.path.splitext(file)[1] == '.stream':
                    try:
                        nameFile = xbmcvfs.File(cachePath + '/' + + str(fileID) + '/' + str(fileID) + '.name')
                        filename = nameFile.read()
                        nameFile.close()
                    except:
                        filename = file
                    localFiles.append(file)


        return localFiles

