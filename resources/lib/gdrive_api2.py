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

import os
import re
import urllib, urllib2
import cookielib
from cloudservice import cloudservice

from resources.lib import encryption
from resources.lib import downloadfile
from resources.lib import authorization
from resources.lib import folder
from resources.lib import file
from resources.lib import package
from resources.lib import mediaurl
from resources.lib import crashreport
import unicodedata



import xbmc, xbmcaddon, xbmcgui, xbmcplugin
import xbmcvfs

# global variables
PLUGIN_NAME = 'plugin.video.gdrive'
PLUGIN_URL = 'plugin://'+PLUGIN_NAME+'/'

addon = xbmcaddon.Addon(id='plugin.video.gdrive')
addon_dir = xbmc.translatePath( addon.getAddonInfo('path') )
SERVICE_NAME = 'dmdgdrive'

import sys


#
# Google Drive API 2 implementation of Google Drive
#
class gdrive(cloudservice):

    AUDIO = 1
    VIDEO = 2
    PICTURE = 3

    # magic numbers
    MEDIA_TYPE_MUSIC = 1
    MEDIA_TYPE_VIDEO = 2
    MEDIA_TYPE_PICTURE = 3

    MEDIA_TYPE_FOLDER = 0


    API_VERSION = '3.0'

    PROTOCOL = 'https://'

    API_URL = PROTOCOL+'www.googleapis.com/drive/v2/'

    ##
    # initialize (save addon, instance name, user agent)
    ##
    def __init__(self, PLUGIN_URL, addon, instanceName, user_agent, authenticate=True):
        self.PLUGIN_URL = PLUGIN_URL
        self.addon = addon
        self.instanceName = instanceName
        self.protocol = 2
        if authenticate == True:
            self.type = int(addon.getSetting(instanceName+'_type'))


        # gdrive specific ***
        self.decrypt = False

        #depreciated - backward compatibility
        self.useWRITELY = False
        #***

        self.crashreport = crashreport.crashreport(self.addon)
#        self.crashreport.sendError('test','test')

        try:
            username = self.addon.getSetting(self.instanceName+'_username')
        except:
            username = ''
        self.authorization = authorization.authorization(username)


        self.cookiejar = cookielib.CookieJar()

        self.user_agent = user_agent

        # load the OAUTH2 tokens or force fetch if not set
        if (authenticate == True and (not self.authorization.loadToken(self.instanceName,addon, 'auth_access_token') or not self.authorization.loadToken(self.instanceName,addon, 'auth_refresh_token'))):
            if self.addon.getSetting(self.instanceName+'_code'):
                self.getToken(self.addon.getSetting(self.instanceName+'_code'))
            else:
                xbmcgui.Dialog().ok(self.addon.getLocalizedString(30000), self.addon.getLocalizedString(30017), self.addon.getLocalizedString(30018))
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
        #***


    ##
    # get OAUTH2 access and refresh token for provided code
    #   parameters: OAUTH2 code
    #   returns: none
    ##
    def getToken(self,code):


            header = { 'User-Agent' : self.user_agent }

            if (self.type == 2):
                url = addon.getSetting(self.instanceName+'_url')
                values = {
                      'code' : code
                      }
                req = urllib2.Request(url, urllib.urlencode(values), header)

            elif (self.type == 3):
                url = 'https://accounts.google.com/o/oauth2/token'
                clientID = addon.getSetting(self.instanceName+'_client_id')
                clientSecret = addon.getSetting(self.instanceName+'_client_secret')
                header = { 'User-Agent' : self.user_agent , 'Content-Type': 'application/x-www-form-urlencoded'}

                req = urllib2.Request(url, 'code='+str(code)+'&client_id='+str(clientID)+'&client_secret='+str(clientSecret)+'&redirect_uri=urn:ietf:wg:oauth:2.0:oob&grant_type=authorization_code', header)

            else:
                url = 'http://dmdsoftware.net/api/gdrive.php'
                values = {
                      'code' : code
                      }
                req = urllib2.Request(url, urllib.urlencode(values), header)




            # try login
            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                if e.code == 403:
                    #login issue
                    xbmcgui.Dialog().ok(self.addon.getLocalizedString(30000), self.addon.getLocalizedString(30017), self.addon.getLocalizedString(30118))
                    xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                else:
                    xbmcgui.Dialog().ok(self.addon.getLocalizedString(30000), self.addon.getLocalizedString(30017), self.addon.getLocalizedString(30118))
                    xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                return


            response_data = response.read()
            response.close()

            # retrieve authorization token
            for r in re.finditer('\"access_token\"\s?\:\s?\"([^\"]+)\".+?' +
                             '\"refresh_token\"\s?\:\s?\"([^\"]+)\".+?' ,
                             response_data, re.DOTALL):
                accessToken,refreshToken = r.groups()
                self.authorization.setToken('auth_access_token',accessToken)
                self.authorization.setToken('auth_refresh_token',refreshToken)
                self.updateAuthorization(self.addon)

            for r in re.finditer('\"error_description\"\s?\:\s?\"([^\"]+)\"',
                             response_data, re.DOTALL):
                errorMessage = r.group(1)
                xbmcgui.Dialog().ok(self.addon.getLocalizedString(30000), self.addon.getLocalizedString(30119), errorMessage)
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(errorMessage), xbmc.LOGERROR)

            return


    ##
    # refresh OAUTH2 access given refresh token
    #   parameters: none
    #   returns: none
    ##
    def refreshToken(self):

            header = { 'User-Agent' : self.user_agent }

            if (self.type == 2):
                url = addon.getSetting(self.instanceName+'_url')
                values = {
                      'refresh_token' : self.authorization.getToken('auth_refresh_token')
                      }
                req = urllib2.Request(url, urllib.urlencode(values), header)

            elif (self.type == 3):
                url = 'https://accounts.google.com/o/oauth2/token'
                clientID = addon.getSetting(self.instanceName+'_client_id')
                clientSecret = addon.getSetting(self.instanceName+'_client_secret')
                header = { 'User-Agent' : self.user_agent , 'Content-Type': 'application/x-www-form-urlencoded'}

                req = urllib2.Request(url, 'client_id='+clientID+'&client_secret='+clientSecret+'&refresh_token='+self.authorization.getToken('auth_refresh_token')+'&grant_type=refresh_token', header)

            else:
                url = 'http://dmdsoftware.net/api/gdrive.php'
                values = {
                      'refresh_token' : self.authorization.getToken('auth_refresh_token')
                      }
                req = urllib2.Request(url, urllib.urlencode(values), header)


            # try login
            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                if e.code == 403:
                    #login issue
                    xbmcgui.Dialog().ok(self.addon.getLocalizedString(30000), self.addon.getLocalizedString(30017), self.addon.getLocalizedString(30118))
                    xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                else:
                    xbmcgui.Dialog().ok(self.addon.getLocalizedString(30000), self.addon.getLocalizedString(30017), self.addon.getLocalizedString(30118))
                    xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                return

            response_data = response.read()
            response.close()

            # retrieve authorization token
            for r in re.finditer('\"access_token\"\s?\:\s?\"([^\"]+)\".+?' ,
                             response_data, re.DOTALL):
                accessToken = r.group(1)
                self.authorization.setToken('auth_access_token',accessToken)
                self.updateAuthorization(self.addon)

            for r in re.finditer('\"error_description\"\s?\:\s?\"([^\"]+)\"',
                             response_data, re.DOTALL):
                errorMessage = r.group(1)
                xbmcgui.Dialog().ok(self.addon.getLocalizedString(30000), self.addon.getLocalizedString(30119), errorMessage)
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(errorMessage), xbmc.LOGERROR)

            return

    ##
    # return the appropriate "headers" for Google Drive requests that include 1) user agent, 2) authorization token
    #   returns: list containing the header
    ##
    def getHeadersList(self, forceWritely=True):
        if self.authorization.isToken(self.instanceName,addon, 'auth_access_token'):
#            return { 'User-Agent' : self.user_agent, 'Authorization' : 'Bearer ' + self.authorization.getToken('auth_access_token') }
            return { 'Authorization' : 'Bearer ' + self.authorization.getToken('auth_access_token') }
        else:
            return { 'User-Agent' : self.user_agent}


    #*** not used
    def setDecrypt(self):
        self.decrypt = True


    ##
    # return the appropriate "headers" for Google Drive requests that include 1) user agent, 2) authorization token, 3) api version
    #   returns: URL-encoded header string
    ##
    def getHeadersEncoded(self, forceWritely=True):
        return urllib.urlencode(self.getHeadersList(forceWritely))



    ##
    # retrieve a list of videos, using playback type stream
    #   parameters: prompt for video quality (optional), cache type (optional)
    #   returns: list of videos
    ##
    def getMediaList(self, folderName=False, title=False, contentType=7):

        # retrieve all items
        url = self.API_URL +'files/'

        # show all videos
        if folderName=='VIDEO':
            url = url + "?q=mimeType+contains+'video'"
        # show all music
        elif folderName=='MUSIC':
            url = url + "?q=mimeType+contains+'audio'"
        # show all music and video
        elif folderName=='VIDEOMUSIC':
            url = url + "?q=mimeType+contains+'audio'+or+mimeType+contains+'video'"
        # show all photos and music
        elif folderName=='PHOTOMUSIC':
            url = url + "?q=mimeType+contains+'image'+or+mimeType+contains+'music'"
        # show all photos
        elif folderName=='PHOTO':
            url = url + "?q=mimeType+contains+'image'"
        # show all music, photos and video
        elif folderName=='ALL':
            url = url + "?q=mimeType+contains+'audio'+or+mimeType+contains+'video'+or+mimeType+contains+'image'"

        # search for title
        elif title != False:
            encodedTitle = re.sub(' ', '+', title)
            url = url + "?q=title+contains+'" + str(encodedTitle) + "'"

        # show all starred items
        elif folderName == 'STARRED-FILES' or folderName == 'STARRED-FILESFOLDERS' or folderName == 'STARRED-FOLDERS':
            url = url + "?q=starred%3dtrue"
        # show all shared items
        elif folderName == 'SHARED':
            url = url + "?q=sharedWithMe%3dtrue"

        # default / show root folder
        elif folderName == '' or folderName == 'me' or folderName == 'root':
            folderName = self.getRootID()
            url = url + "?q='"+str(folderName)+"'+in+parents"

        # retrieve folder items
        else:
            url = url + "?q='"+str(folderName)+"'+in+parents"


        mediaFiles = []
        while True:
            req = urllib2.Request(url, None, self.getHeadersList())

            # if action fails, validate login
            try:
              response = urllib2.urlopen(req)
            except urllib2.URLError, e:
              if e.code == 403 or e.code == 401:
                self.refreshToken()
                req = urllib2.Request(url, None, self.getHeadersList())
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                  self.crashreport.sendError('getMediaList',str(e))
                  return
              else:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                self.crashreport.sendError('getMediaList',str(e))
                return

            response_data = response.read()
            response.close()

            # parsing page for videos
            # video-entry
            for r2 in re.finditer('\"items\"\:\s+\[[^\{]+(\{.*?)\s+\]\s+\}' ,response_data, re.DOTALL):
             entryS = r2.group(1)
             for r1 in re.finditer('\{(.*?)\"appDataContents\"\:' ,entryS, re.DOTALL):
                entry = r1.group(1)

                resourceID = 0
                resourceType = ''
                title = ''
                fileSize = 0
                thumbnail = ''
                url = ''
                for r in re.finditer('\"id\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  resourceID = r.group(1)
                  break
                for r in re.finditer('\"mimeType\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  resourceType = r.group(1)
                  break
                for r in re.finditer('\"title\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  title = r.group(1)
                  break
                for r in re.finditer('\"fileSize\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  fileSize = r.group(1)
                  break
                for r in re.finditer('\"thumbnailLink\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  thumbnail = r.group(1)
                  break
                for r in re.finditer('\"downloadUrl\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  url = r.group(1)
                  break

                # entry is a folder
                if (resourceType == 'application/vnd.google-apps.folder'):
                    media = package.package(None,folder.folder(resourceID,title))
                    mediaFiles.append(media)

                # entry is a video
                elif (resourceType == 'application/vnd.google-apps.video' or 'video' in resourceType and contentType in (0,1,2,4,7)):
                    mediaFile = file.file(resourceID, title, title, self.MEDIA_TYPE_VIDEO, '', thumbnail, size=fileSize)

                    media = package.package(mediaFile,folder.folder(folderName,''))
                    media.setMediaURL(mediaurl.mediaurl(url, '','',''))
                    mediaFiles.append(media)

                # entry is a music file
                elif (resourceType == 'application/vnd.google-apps.audio' or 'audio' in resourceType and contentType in (1,2,3,4,6,7)):
                    mediaFile = file.file(resourceID, title, title, self.MEDIA_TYPE_MUSIC, '', '', size=fileSize)
                    #url = re.sub('\&gd\=true', '', url)
                    media = package.package(mediaFile,folder.folder(folderName,''))
                    media.setMediaURL(mediaurl.mediaurl(url, '','',''))
                    mediaFiles.append(media)

                # entry is a photo
                elif (resourceType == 'application/vnd.google-apps.photo' or 'image' in resourceType and contentType in (2,4,5,6,7)):
                    mediaFile = file.file(resourceID, title, title, self.MEDIA_TYPE_PICTURE, '', thumbnail, size=fileSize)

                    media = package.package(mediaFile,folder.folder(folderName,''))
                    media.setMediaURL(mediaurl.mediaurl(url, '','',''))
                    mediaFiles.append(media)

                # entry is unknown
                elif (resourceType == 'application/vnd.google-apps.unknown'):
                    mediaFile = file.file(resourceID, title, title, self.MEDIA_TYPE_VIDEO, '', thumbnail, size=fileSize)

                    media = package.package(mediaFile,folder.folder(folderName,''))
                    media.setMediaURL(mediaurl.mediaurl(url, '','',''))
                    mediaFiles.append(media)

            # look for more pages of videos
            nextURL = ''
            for r in re.finditer('\"nextLink\"\:\s+\"([^\"]+)\"' ,
                             response_data, re.DOTALL):
                nextURL = r.group(1)


            # are there more pages to process?
            if nextURL == '':
                break
            else:
                url = nextURL

        return mediaFiles


    ##
    # retrieve a srt file for playback
    #   parameters: title of the video file
    #   returns: download url for srt
    ##
    def getSRT(self, title):

        # retrieve all items
        url = self.API_URL +'files/'

        # search for title
        if title != False:
            title = os.path.splitext(title)[0]
            encodedTitle = re.sub(' ', '+', title)
            url = url + "?q=title+contains+'" + str(encodedTitle) + "'"


        mediaFiles = []
        while True:
            req = urllib2.Request(url, None, self.getHeadersList())

            # if action fails, validate login
            try:
              response = urllib2.urlopen(req)
            except urllib2.URLError, e:
              if e.code == 403 or e.code == 401:
                self.refreshToken()
                req = urllib2.Request(url, None, self.getHeadersList())
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                  self.crashreport.sendError('getMediaList',str(e))
                  return
              else:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                self.crashreport.sendError('getMediaList',str(e))
                return

            response_data = response.read()
            response.close()

            # parsing page for videos
            # video-entry
            for r2 in re.finditer('\"items\"\:\s+\[[^\{]+(\{.*?)\s+\]\s+\}' ,response_data, re.DOTALL):
             entryS = r2.group(1)
             for r1 in re.finditer('\{(.*?)\"appDataContents\"\:' ,entryS, re.DOTALL):
                entry = r1.group(1)

                resourceID = 0
                resourceType = ''
                title = ''
                url = ''
                fileExtension = ''
                for r in re.finditer('\"fileExtension\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  fileExtension = r.group(1)
                  break
                if fileExtension != 'srt':
                    break
                for r in re.finditer('\"id\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  resourceID = r.group(1)
                  break
                for r in re.finditer('\"title\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  title = r.group(1)
                  break
                for r in re.finditer('\"downloadUrl\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  url = r.group(1)
                  return url
                  break



            # look for more pages of videos
            nextURL = ''
            for r in re.finditer('\"nextLink\"\:\s+\"([^\"]+)\"' ,
                             response_data, re.DOTALL):
                nextURL = r.group(1)


            # are there more pages to process?
            if nextURL == '':
                break
            else:
                url = nextURL

        return ''


    ##
    # retrieve the resource ID for root folder
    #   parameters: none
    #   returns: resource ID
    ##
    def getRootID(self):

        # retrieve all items
        url = self.API_URL +'files/root'

        resourceID = ''
        while True:
            req = urllib2.Request(url, None, self.getHeadersList())

            # if action fails, validate login
            try:
              response = urllib2.urlopen(req)
            except urllib2.URLError, e:
              if e.code == 403 or e.code == 401:
                self.refreshToken()
                req = urllib2.Request(url, None, self.getHeadersList())
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                  self.crashreport.sendError('getMediaList',str(e))
                  return
              else:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                self.crashreport.sendError('getMediaList',str(e))
                return

            response_data = response.read()
            response.close()


            for r1 in re.finditer('\{(.*?)\"appDataContents\"\:' ,response_data, re.DOTALL):
                entry = r1.group(1)

                for r in re.finditer('\"id\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  resourceID = r.group(1)
                  return resourceID

            # look for more pages of videos
            nextURL = ''
            for r in re.finditer('\"nextLink\"\:\s+\"([^\"]+)\"' ,
                             response_data, re.DOTALL):
                nextURL = r.group(1)


            # are there more pages to process?
            if nextURL == '':
                break
            else:
                url = nextURL

        return resourceID

    ##
    # retrieve the download URL for given docid
    #   parameters: resource ID
    #   returns: download URL
    ##
    def getDownloadURL(self, docid):

            url = self.API_URL +'files/' + docid

            req = urllib2.Request(url, None, self.getHeadersList())


            # if action fails, validate login
            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                if e.code == 403 or e.code == 401:
                    self.refreshToken()
                    req = urllib2.Request(url, None, self.getHeadersList())
                    try:
                        response = urllib2.urlopen(req)
                    except urllib2.URLError, e:
                        xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                        self.crashreport.sendError('getPlaybackCall',str(e))
                        return
                else:
                    xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                    self.crashreport.sendError('getPlaybackCall',str(e))
                    return

            response_data = response.read()
            response.close()


            for r1 in re.finditer('\{(.*?)\"appDataContents\"\:' ,response_data, re.DOTALL):
                entry = r1.group(1)


                url = ''
                for r in re.finditer('\"downloadUrl\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  url = r.group(1)
                  return url

    #*** not used
    ##
    # retrieve a list of videos, using playback type stream
    #   parameters: cache type (optional)
    #   returns: list of videos
    ##
    def decryptFolder(self,key,path,folder):

        # retrieve all items
        url = PROTOCOL+'docs.google.com/feeds/default/private/full'

        # retrieve root items
        if folder == '':
            url = url + '/folder%3Aroot/contents'
        # retrieve folder items
        else:
            url = url + '/folder%3A'+folder+'/contents'

        import xbmcvfs
        xbmcvfs.mkdir(path + '/'+folder)

        while True:
            req = urllib2.Request(url, None, self.getHeadersList())

            # if action fails, validate login
            try:
              response = urllib2.urlopen(req)
            except urllib2.URLError, e:
              if e.code == 403 or e.code == 401:
                self.refreshToken()
                req = urllib2.Request(url, None, self.getHeadersList())
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                    xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                    self.crashreport.sendError('decryptFolder',str(e))
                    return
              else:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                self.crashreport.sendError('decryptFolder',str(e))
                return

            response_data = response.read()
            response.close()

            downloadList = []
            # video-entry
            for r in re.finditer('\<entry[^\>]+\>(.*?)\<\/entry\>' ,response_data, re.DOTALL):
                entry = r.group(1)

                # fetch folder
                for r in re.finditer('\<gd\:resourceId\>([^\:]*)\:?([^\<]*)\</gd:resourceId\>' ,
                             entry, re.DOTALL):
                  resourceType,resourceID = r.groups()

                  # entry is NOT a folder
                  if not (resourceType == 'folder'):
                      # fetch video title, download URL and docid for stream link
                      # Google Drive API format
                      for r in re.finditer('<title>([^<]+)</title><content type=\'(video)\/[^\']+\' src=\'([^\']+)\'.+?rel=\'http://schemas.google.com/docs/2007/thumbnail\' type=\'image/[^\']+\' href=\'([^\']+)\'' ,
                             entry, re.DOTALL):
                          title,mediaType,url,thumbnail = r.groups()

                      #for playing video.google.com videos linked to your google drive account
                      # Google Docs & Google Video API format
                      for r in re.finditer('<title>([^<]+)</title><link rel=\'alternate\' type=\'text/html\' href=\'([^\']+).+?rel=\'http://schemas.google.com/docs/2007/thumbnail\' type=\'image/[^\']+\' href=\'([^\']+)\'' ,
                             entry, re.DOTALL):
                          title,url,thumbnail = r.groups()

                      # audio
                      for r in re.finditer('<title>([^<]+)</title><content type=\'audio\/[^\']+\' src=\'([^\']+)\'' ,
                             entry, re.DOTALL):
                          title,url = r.groups()

                      # pictures
                      for r in re.finditer('<title>([^<]+)</title><content type=\'image\/[^\']+\' src=\'([^\']+)\'' ,
                             entry, re.DOTALL):
                          title,url = r.groups()

                          url = re.sub('&amp;', '&', url)
                          filename = path + '/'+folder+'/'+ encryption.decrypt(title)
                          if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                              open(filename, 'a').close()
                              downloadList.append(downloadfile.downloadfile(url,filename))
                              #self.downloadDecryptPicture(key, url,filename)


                      # pictures
                      for r in re.finditer('<title>([^<]+)</title><content type=\'application\/[^\']+\' src=\'([^\']+)\'' ,
                             entry, re.DOTALL):
                          title,url = r.groups()

                          url = re.sub('&amp;', '&', url)
                          filename = path + '/'+folder+'/'+ encryption.decrypt(title)
                          if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                              open(filename, 'a').close()
                              downloadList.append(downloadfile.downloadfile(url,filename))
                              #self.downloadDecryptPicture(key, url,filename)

            if downloadList:
                for file in sorted(downloadList, key=lambda item: item.name):
                    self.downloadDecryptPicture(key, file.url,file.name)

            # look for more pages of videos
            nextURL = ''
            for r in re.finditer('<link rel=\'next\' type=\'[^\']+\' href=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                nextURL = r.groups()


            # are there more pages to process?
            if nextURL == '':
                break
            else:
                url = nextURL[0]


    ##
    # retrieve a playback url
    #   returns: url
    ##
    def getPlaybackCall(self, playbackType, package=None, title='', isExact=True):

        try:
            pquality = int(addon.getSetting('preferred_quality'))
            pformat = int(addon.getSetting('preferred_format'))
            acodec = int(addon.getSetting('avoid_codec'))
        except :
            pquality=-1
            pformat=-1
            acodec=-1

        mediaURLs = []

        docid = ''

        # for playback from STRM with title of video provided (best match)
        if package is None and title != '':

            url = self.API_URL +'files/'
            # search by video title
            encodedTitle = re.sub(' ', '+', title)
            if isExact == True:
                url = url + "?q=title%3d'" + str(encodedTitle) + "'"
            else:
                url = url + "?q=title+contains+'" + str(encodedTitle) + "'"

            req = urllib2.Request(url, None, self.getHeadersList())

            # if action fails, validate login
            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                if e.code == 403 or e.code == 401:
                    self.refreshToken()
                    req = urllib2.Request(url, None, self.getHeadersList())
                    try:
                        response = urllib2.urlopen(req)
                    except urllib2.URLError, e:
                        xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                        self.crashreport.sendError('getPlaybackCall',str(e))
                        return
                else:
                    xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                    self.crashreport.sendError('getPlaybackCall',str(e))
                    return

            response_data = response.read()
            response.close()


            for r1 in re.finditer('\{(.*?)\"appDataContents\"\:' ,response_data, re.DOTALL):
                entry = r1.group(1)


                resourceType = ''
                title = ''
                url = ''
                for r in re.finditer('\"id\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  docid = r.group(1)
                  break
                for r in re.finditer('\"mimeType\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  resourceType = r.group(1)
                  break
                for r in re.finditer('\"title\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  title = r.group(1)
                  break
                for r in re.finditer('\"downloadUrl\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  url = r.group(1)
                  mediaURLs.append(mediaurl.mediaurl(url, 'original', 0, 9999))
                  break

        #given docid, fetch original playback
        else:
            docid = package.file.id

            url = self.API_URL +'files/' + docid

            req = urllib2.Request(url, None, self.getHeadersList())


            # if action fails, validate login
            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                if e.code == 403 or e.code == 401:
                    self.refreshToken()
                    req = urllib2.Request(url, None, self.getHeadersList())
                    try:
                        response = urllib2.urlopen(req)
                    except urllib2.URLError, e:
                        xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                        self.crashreport.sendError('getPlaybackCall',str(e))
                        return
                else:
                    xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                    self.crashreport.sendError('getPlaybackCall',str(e))
                    return

            response_data = response.read()
            response.close()


            for r1 in re.finditer('\{(.*?)\"appDataContents\"\:' ,response_data, re.DOTALL):
                entry = r1.group(1)


                resourceType = ''
                title = ''
                url = ''
                for r in re.finditer('\"id\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  docid = r.group(1)
                  break
                for r in re.finditer('\"mimeType\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  resourceType = r.group(1)
                  break
                for r in re.finditer('\"title\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  title = r.group(1)
                  break
                for r in re.finditer('\"downloadUrl\"\:\s+\"([^\"]+)\"' ,
                             entry, re.DOTALL):
                  url = r.group(1)
                  if package.file.type == self.MEDIA_TYPE_MUSIC:
                      url = re.sub('\&gd\=true', '', url)

                  mediaURLs.append(mediaurl.mediaurl(url, 'original', 0, 9999))
                  break

        if package.file.type == self.MEDIA_TYPE_MUSIC:
            return mediaURLs

        # fetch streams
        if docid != '':
            # player using docid
            params = urllib.urlencode({'docid': docid})
            url = self.PROTOCOL+ 'drive.google.com/get_video_info?docid=' + str(docid)
            req = urllib2.Request(url, None, self.getHeadersList(self.useWRITELY))
            # if action fails, validate login
            try:
                 response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                 if e.code == 403 or e.code == 401:
                     self.refreshToken()
                     req = urllib2.Request(url, None, self.getHeadersList(self.useWRITELY))
                     try:
                         response = urllib2.urlopen(req)
                     except urllib2.URLError, e:
                         xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                         self.crashreport.sendError('getPlaybackCall',str(e))
                         return
                 else:
                     xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                     self.crashreport.sendError('getPlaybackCall',str(e))
                     return

            response_data = response.read()
            response.close()

            # decode resulting player URL (URL is composed of many sub-URLs)
            urls = response_data
            urls = urllib.unquote(urllib.unquote(urllib.unquote(urllib.unquote(urllib.unquote(urls)))))
            urls = re.sub('\\\\u003d', '=', urls)
            urls = re.sub('\\\\u0026', '&', urls)


            self.useWRITELY = True
            req = urllib2.Request(url, None, self.getHeadersList(self.useWRITELY))

            try:
                    response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                    if e.code == 403 or e.code == 401:
                        self.refreshToken()
                        req = urllib2.Request(url, None, self.getHeadersList(self.useWRITELY))
                        try:
                            response = urllib2.urlopen(req)
                        except urllib2.URLError, e:
                            xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                            self.crashreport.sendError('getPlaybackCall',str(e))
                            return
                    else:
                        xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                        self.crashreport.sendError('getPlaybackCall',str(e))
                        return

            response_data = response.read()
            response.close()

            # decode resulting player URL (URL is composed of many sub-URLs)
            urls = response_data
            urls = urllib.unquote(urllib.unquote(urllib.unquote(urllib.unquote(urllib.unquote(urls)))))
            urls = re.sub('\\\\u003d', '=', urls)
            urls = re.sub('\\\\u0026', '&', urls)


        # do some substitutions to make anchoring the URL easier
        urls = re.sub('\&url\='+self.PROTOCOL, '\@', urls)

        # itag code reference http://en.wikipedia.org/wiki/YouTube#Quality_and_codecs
        #itag_dict = {1080: ['137', '37', '46'], 720: ['22', '136', '45'],
        #        480: ['135', '59', '44', '35'], 360: ['43', '134', '34', '18', '6'],
        #        240: ['133', '5', '36'], 144: ['160', '17']}

#        <setting id="preferred_quality" type="enum" label="30011" values="perfer best (1080,720,<720)|prefer 720 (720,<720,>720)|prefer SD (480,<480)" default="0" />
#        <setting id="preferred_format" type="enum" label="30012" values="MP4,WebM,flv|MP4,flv,WebM|flv,WebM,MP4|flv,MP4,WebM|WebM,MP4,flv|WebM,flv,MP4" default="0" />
#        <setting id="avoid_codec" type="enum" label="30013" values="none|VP8/vorbis" default="0"/>

        itagDB={}
        containerDB = {'x-flv':'flv', 'webm': 'WebM', 'mp4;+codecs="avc1.42001E,+mp4a.40.2"': 'MP4'}
        for r in re.finditer('(\d+)/(\d+)x(\d+)/(\d+/\d+/\d+)\&?\,?' ,
                               urls, re.DOTALL):
              (itag,resolution1,resolution2,codec) = r.groups()

              if codec == '9/0/115':
                itagDB[itag] = {'resolution': resolution2, 'codec': 'h.264/aac'}
              elif codec == '99/0/0':
                itagDB[itag] = {'resolution': resolution2, 'codec': 'VP8/vorbis'}
              else:
                itagDB[itag] = {'resolution': resolution2}


        # fetch format type and quality for each stream
        count=0
        for r in re.finditer('\@([^\@]+)' ,urls):
                videoURL = r.group(1)
                for q in re.finditer('itag\=(\d+).*?type\=video\/([^\&]+)\&quality\=(\w+)' ,
                             videoURL, re.DOTALL):
                    (itag,container,quality) = q.groups()
                    count = count + 1
                    order=0
                    if pquality > -1 or pformat > -1 or acodec > -1:
                        if int(itagDB[itag]['resolution']) == 1080:
                            if pquality == 0:
                                order = order + 1000
                            elif pquality == 1:
                                order = order + 3000
                            elif pquality == 3:
                                order = order + 9000
                        elif int(itagDB[itag]['resolution']) == 720:
                            if pquality == 0:
                                order = order + 2000
                            elif pquality == 1:
                                order = order + 1000
                            elif pquality == 3:
                                order = order + 9000
                        elif int(itagDB[itag]['resolution']) == 480:
                            if pquality == 0:
                                order = order + 3000
                            elif pquality == 1:
                                order = order + 2000
                            elif pquality == 3:
                                order = order + 1000
                        elif int(itagDB[itag]['resolution']) < 480:
                            if pquality == 0:
                                order = order + 4000
                            elif pquality == 1:
                                order = order + 3000
                            elif pquality == 3:
                                order = order + 2000
                    try:
                        if itagDB[itag]['codec'] == 'VP8/vorbis':
                            if acodec == 1:
                                order = order + 90000
                            else:
                                order = order + 10000
                    except :
                        order = order + 30000

                    try:
                        if containerDB[container] == 'MP4':
                            if pformat == 0 or pformat == 1:
                                order = order + 100
                            elif pformat == 3 or pformat == 4:
                                order = order + 200
                            else:
                                order = order + 300
                        elif containerDB[container] == 'flv':
                            if pformat == 2 or pformat == 3:
                                order = order + 100
                            elif pformat == 1 or pformat == 5:
                                order = order + 200
                            else:
                                order = order + 300
                        elif containerDB[container] == 'WebM':
                            if pformat == 4 or pformat == 5:
                                order = order + 100
                            elif pformat == 0 or pformat == 1:
                                order = order + 200
                            else:
                                order = order + 300
                        else:
                            order = order + 100
                    except :
                        pass

                    try:
                        mediaURLs.append(mediaurl.mediaurl(self.PROTOCOL + videoURL, itagDB[itag]['resolution'] + ' - ' + containerDB[container] + ' - ' + itagDB[itag]['codec'], str(itagDB[itag]['resolution'])+ '_' + str(order+count), order+count))
                    except KeyError:
                        mediaURLs.append(mediaurl.mediaurl(self.PROTOCOL + videoURL, itagDB[itag]['resolution'] + ' - ' + container, str(itagDB[itag]['resolution'])+ '_' + str(order+count), order+count))

        return mediaURLs



    ##
    # download remote picture
    # parameters: url of picture, file location with path on disk
    ##
    def downloadPicture(self, url, file):

        req = urllib2.Request(url, None, self.getHeadersList())

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
                return

    #*** needs update
    def downloadDecryptPicture(self,key,url, file):

        req = urllib2.Request(url, None, self.getHeadersList())


        # if action fails, validate login
        try:
#          open('/tmp/tmp','wb').write(urllib2.urlopen(req).read())
#          encryption.decrypt_file(key,'/tmp/tmp',file)
          encryption.decrypt_stream(key,urllib2.urlopen(req),file)
        except urllib2.URLError, e:
            if e.code == 403 or e.code == 401:
              self.refreshToken()
              req = urllib2.Request(url, None, self.getHeadersList())
              try:
                encryption.decrypt_stream(key,urllib2.urlopen(req),file)
#                open('/tmp/tmp','wb').write(urllib2.urlopen(req).read())
#                encryption.decrypt_file(key,'/tmp/tmp',file)

              except urllib2.URLError, e:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                self.crashreport.sendError('downloadDecryptPicture',str(e))
                return
            else:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                self.crashreport.sendError('downloadDecryptPicture',str(e))
                return


    # for playing public URLs
    def getPublicStream(self,url):

        try:
            pquality = int(self.addon.getSetting('preferred_quality'))
            pformat = int(self.addon.getSetting('preferred_format'))
            acodec = int(self.addon.getSetting('avoid_codec'))
        except :
            pquality=-1
            pformat=-1
            acodec=-1

        mediaURLs = []

        #try to use no authorization token (for pubic URLs)
#        header = { 'User-Agent' : self.user_agent, 'GData-Version' : self.API_VERSION }

        req = urllib2.Request(url, None, self.getHeadersList())

        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            if e.code == 403 or e.code == 401:
              self.refreshToken()
              req = urllib2.Request(url, None, self.getHeadersList(self.useWRITELY))
              try:
                response = urllib2.urlopen(req)
              except urllib2.URLError, e:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                self.crashreport.sendError('getPublicStream',str(e))
                return
            else:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                self.crashreport.sendError('getPublicStream',str(e))
                return

        response_data = response.read()
        response.close()


        for r in re.finditer('\"fmt_list\"\,\"([^\"]+)\"' ,
                             response_data, re.DOTALL):
            fmtlist = r.group(1)

        title = ''
        for r in re.finditer('\"title\"\,\"([^\"]+)\"' ,
                             response_data, re.DOTALL):
            title = r.group(1)

#thumbnail
#        downloadURL = ''
#        for r in re.finditer('\,\[\,\"[^\"]+\"\,\"([^\"]+)\"' ,
#                             response_data, re.DOTALL):
#            downloadURL = r.group(1)
#            downloadURL = re.sub('\\\\u003d', '=', downloadURL)

        itagDB={}
        containerDB = {'x-flv':'flv', 'webm': 'WebM', 'mp4;+codecs="avc1.42001E,+mp4a.40.2"': 'MP4'}
        for r in re.finditer('(\d+)/(\d+)x(\d+)/(\d+/\d+/\d+)\&?\,?' ,
                               fmtlist, re.DOTALL):
              (itag,resolution1,resolution2,codec) = r.groups()

              if codec == '9/0/115':
                itagDB[itag] = {'resolution': resolution2, 'codec': 'h.264/aac'}
              elif codec == '99/0/0':
                itagDB[itag] = {'resolution': resolution2, 'codec': 'VP8/vorbis'}
              else:
                itagDB[itag] = {'resolution': resolution2}

        for r in re.finditer('\"url_encoded_fmt_stream_map\"\,\"([^\"]+)\"' ,
                             response_data, re.DOTALL):
            urls = r.group(1)



        urls = urllib.unquote(urllib.unquote(urllib.unquote(urllib.unquote(urllib.unquote(urls)))))
        urls = re.sub('\\\\u003d', '=', urls)
        urls = re.sub('\\\\u0026', '&', urls)


#        urls = re.sub('\d+\&url\='+self.PROTOCOL, '\@', urls)
        urls = re.sub('\&url\='+self.PROTOCOL, '\@', urls)

#        for r in re.finditer('\@([^\@]+)' ,urls):
#          videoURL = r.group(0)
#        videoURL1 = self.PROTOCOL + videoURL


        # fetch format type and quality for each stream
        count=0
        for r in re.finditer('\@([^\@]+)' ,urls):
                videoURL = r.group(1)
                for q in re.finditer('itag\=(\d+).*?type\=video\/([^\&]+)\&quality\=(\w+)' ,
                             videoURL, re.DOTALL):
                    (itag,container,quality) = q.groups()
                    count = count + 1
                    order=0
                    if pquality > -1 or pformat > -1 or acodec > -1:
                        if int(itagDB[itag]['resolution']) == 1080:
                            if pquality == 0:
                                order = order + 1000
                            elif pquality == 1:
                                order = order + 3000
                            elif pquality == 3:
                                order = order + 9000
                        elif int(itagDB[itag]['resolution']) == 720:
                            if pquality == 0:
                                order = order + 2000
                            elif pquality == 1:
                                order = order + 1000
                            elif pquality == 3:
                                order = order + 9000
                        elif int(itagDB[itag]['resolution']) == 480:
                            if pquality == 0:
                                order = order + 3000
                            elif pquality == 1:
                                order = order + 2000
                            elif pquality == 3:
                                order = order + 1000
                        elif int(itagDB[itag]['resolution']) < 480:
                            if pquality == 0:
                                order = order + 4000
                            elif pquality == 1:
                                order = order + 3000
                            elif pquality == 3:
                                order = order + 2000
                    try:
                        if itagDB[itag]['codec'] == 'VP8/vorbis':
                            if acodec == 1:
                                order = order + 90000
                            else:
                                order = order + 10000
                    except :
                        order = order + 30000

                    try:
                        if containerDB[container] == 'MP4':
                            if pformat == 0 or pformat == 1:
                                order = order + 100
                            elif pformat == 3 or pformat == 4:
                                order = order + 200
                            else:
                                order = order + 300
                        elif containerDB[container] == 'flv':
                            if pformat == 2 or pformat == 3:
                                order = order + 100
                            elif pformat == 1 or pformat == 5:
                                order = order + 200
                            else:
                                order = order + 300
                        elif containerDB[container] == 'WebM':
                            if pformat == 4 or pformat == 5:
                                order = order + 100
                            elif pformat == 0 or pformat == 1:
                                order = order + 200
                            else:
                                order = order + 300
                        else:
                            order = order + 100
                    except :
                        pass

                    try:
                        mediaURLs.append( mediaurl.mediaurl(self.PROTOCOL + videoURL, itagDB[itag]['resolution'] + ' - ' + containerDB[container] + ' - ' + itagDB[itag]['codec'], str(itagDB[itag]['resolution'])+ '_' + str(order+count), order+count, title=title))
                    except KeyError:
                        mediaURLs.append(mediaurl.mediaurl(self.PROTOCOL + videoURL, itagDB[itag]['resolution'] + ' - ' + container, str(itagDB[itag]['resolution'])+ '_' + str(order+count), order+count, title=title))

        return mediaURLs


    ##
    # retrieve a media file
    #   parameters: title of video, whether to prompt for quality/format (optional),
    ##
    def downloadMediaFile(self, playback, url, title, folderID, filename, fileSize, force=False):


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


        path = ''
        try:
            path = addon.getSetting('cache_folder')
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



