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

from resources.lib import encryption
from resources.lib import downloadfile



import xbmc, xbmcaddon, xbmcgui, xbmcplugin

# global variables
PLUGIN_NAME = 'plugin.video.gdrive'
PLUGIN_URL = 'plugin://'+PLUGIN_NAME+'/'
ADDON = xbmcaddon.Addon(id=PLUGIN_NAME)
PROTOCOL = 'https://'
SERVICE_NAME = 'dmdgdrive'


# helper methods
def log(msg, err=False):
    if err:
        xbmc.log(ADDON.getAddonInfo('name') + ': ' + msg, xbmc.LOGERROR)
    else:
        xbmc.log(ADDON.getAddonInfo('name') + ': ' + msg, xbmc.LOGDEBUG)



#
# Google Docs API 3 implentation of Google Drive
#
class gdrive:

    # magic numbers
    MEDIA_TYPE_MUSIC = 1
    MEDIA_TYPE_VIDEO = 2
    MEDIA_TYPE_PICTURE = 3

    MEDIA_TYPE_FOLDER = 0

    CACHE_TYPE_MEMORY = 0
    CACHE_TYPE_DISK = 1
    CACHE_TYPE_STREAM = 2

    API_VERSION = '3.0'
    ##
    # initialize (setting 1) username, 2) password, 3) authorization token, 4) user agent string
    ##
    def __init__(self, user, password, auth_writely, auth_wise, user_agent, authenticate=True, useWRITELY=False):
        self.user = user
        self.password = password
        self.writely = auth_writely
        self.wise = auth_wise
        self.user_agent = user_agent
        self.useWRITELY = useWRITELY
        self.decrypt = False

        # if we have an authorization token set, try to use it
        if auth_writely != '' and auth_wise != '':
          log('using token')

          return


        # allow for playback of public videos without authentication
        if (authenticate == True):
          log('no token - logging in')
          self.login();
          self.loginWISE();

        return


    ##
    # perform login
    ##
    def login(self):

        url = PROTOCOL + 'www.google.com/accounts/ClientLogin'
        header = { 'User-Agent' : self.user_agent }
        values = {
          'Email' : self.user,
          'Passwd' : self.password,
          'accountType' : 'HOSTED_OR_GOOGLE',
          'source' : SERVICE_NAME,
          'service' : 'writely'
        }

        req = urllib2.Request(url, urllib.urlencode(values), header)

        # try login
        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            if e.code == 403:
                #login denied
                xbmcgui.Dialog().ok(ADDON.getLocalizedString(30000), ADDON.getLocalizedString(30017))
            log(str(e), True)
            return

        response_data = response.read()
        response.close()

        # retrieve authorization token
        for r in re.finditer('SID=(.*).+?' +
                             'LSID=(.*).+?' +
                             'Auth=(.*).+?' ,
                             response_data, re.DOTALL):
            sid,lsid,auth = r.groups()


        # save authorization token
        self.writely = auth
        return

    ##
    # perform login
    ##
    def loginWISE(self):

        url = PROTOCOL+'www.google.com/accounts/ClientLogin'
        header = { 'User-Agent' : self.user_agent }
        values = {
          'Email' : self.user,
          'Passwd' : self.password,
          'accountType' : 'HOSTED_OR_GOOGLE',
          'source' : SERVICE_NAME,
          'service' : 'wise'
        }

        req = urllib2.Request(url, urllib.urlencode(values), header)

        # try login
        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            if e.code == 403:
                #login denied
                xbmcgui.Dialog().ok(ADDON.getLocalizedString(30000), ADDON.getLocalizedString(30017))
            log(str(e), True)
            return

        response_data = response.read()
        response.close()

        # retrieve authorization token
        for r in re.finditer('SID=(.*).+?' +
                             'LSID=(.*).+?' +
                             'Auth=(.*).+?' ,
                             response_data, re.DOTALL):
            sid,lsid,auth = r.groups()

        # save authorization token
        self.wise = auth
        return



    ##
    # return the appropriate "headers" for Google Drive requests that include 1) user agent, 2) authorization token, 3) api version
    #   returns: list containing the header
    ##
    def getHeadersList(self, forceWritely=True):
        #effective 2014/02, video stream calls require a wise token instead of writely token
        if forceWritely == True:
            return { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.writely, 'GData-Version' : self.API_VERSION }
        else:
            return { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.wise, 'GData-Version' : self.API_VERSION }

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
    #   parameters: cache type (optional)
    #   returns: list of videos
    ##
    def getVideosList(self,cacheType=CACHE_TYPE_MEMORY, folder=False):

        # retrieve all items
        url = PROTOCOL+'docs.google.com/feeds/default/private/full'
        if folder==False:
            url = url + '?showfolders=false'
        # retrieve root items
        elif folder == '':
            url = url + '/folder%3Aroot/contents'
        # retrieve folder items
        else:
            url = url + '/folder%3A'+folder+'/contents'


        videos = {}
        while True:
            req = urllib2.Request(url, None, self.getHeadersList())

            # if action fails, validate login
            try:
              response = urllib2.urlopen(req)
            except urllib2.URLError, e:
              if e.code == 403 or e.code == 401:
                self.login()
                req = urllib2.Request(url, None, self.getHeadersList())
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  log(str(e), True)
                  return
              else:
                log(str(e), True)
                return

            response_data = response.read()
            response.close()

            # parsing page for videos
            # video-entry
            for r in re.finditer('\<entry[^\>]+\>(.*?)\<\/entry\>' ,response_data, re.DOTALL):
                entry = r.group(1)

                # fetch folder
                for r in re.finditer('\<gd\:resourceId\>([^\:]*)\:?([^\<]*)\</gd:resourceId\>' ,
                             entry, re.DOTALL):
                  resourceType,resourceID = r.groups()

                  # entry is a folder
                  if (resourceType == 'folder'):
                      for q in re.finditer('<(title)>([^<]+)</title>' ,
                             entry, re.DOTALL):
                          titleType, title = q.groups()

                          if 0:
                              import base64
                              try:
                                  title = base64.b64decode(title)
                              except:
                                  pass

                          videos[title] = {'mediaType': self.MEDIA_TYPE_FOLDER, 'url': resourceID, 'thumbnail':  ''}

                  # entry is NOT a folder
                  else:
                      processed =0
                      # fetch video title, download URL and docid for stream link
                      # Google Drive API format
                      for r in re.finditer('<title>([^<]+)</title><content type=\'(video)\/[^\']+\' src=\'([^\']+)\'.*?rel=\'http://schemas.google.com/docs/2007/thumbnail\' type=\'image/[^\']+\' href=\'([^\']+)\'.*?<gd:quotaBytesUsed>(\d+)</gd:quotaBytesUsed>' ,
                             entry, re.DOTALL):
                          title,mediaType,url,thumbnail,size = r.groups()

                          # memory-cache
                          if cacheType == self.CACHE_TYPE_MEMORY or cacheType == self.CACHE_TYPE_DISK:
                              videos[title] = {'mediaType': self.MEDIA_TYPE_VIDEO, 'url': str(url)+'&size='+str(size)+ '|' + self.getHeadersEncoded(), 'thumbnail':  thumbnail}

                              # streaming
                          else:
                              videos[title] = {'mediaType': self.MEDIA_TYPE_VIDEO,'url': PLUGIN_URL+'?mode=streamVideo&title=' + str(title), 'thumbnail': thumbnail}
                          processed = 1

                      if processed == 0:
                          #video that can't be processed (no thumbnail)
                          for r in re.finditer('<title>([^<]+)</title><content type=\'(video)\/[^\']+\' src=\'([^\']+)\'.+?\<gd\:quotaBytesUsed\>(\d+)\</gd\:quotaBytesUsed\>' ,
                             entry, re.DOTALL):
                              title,mediaType,url,size = r.groups()

                              # memory-cache
                              if cacheType == self.CACHE_TYPE_MEMORY or cacheType == self.CACHE_TYPE_DISK:
                                  videos[title] = {'mediaType': self.MEDIA_TYPE_VIDEO, 'url': str(url)+'&size='+str(size)+ '|' + self.getHeadersEncoded(), 'thumbnail':  ''}

                              # streaming
                              else:
                                  videos[title] = {'mediaType': self.MEDIA_TYPE_VIDEO,'url': PLUGIN_URL+'?mode=streamVideo&title=' + str(title), 'thumbnail': ''}
                              processed = 1

                      if processed == 0:
                          #for playing video.google.com videos linked to your google drive account
                          # Google Docs & Google Video API format
                          for r in re.finditer('<title>([^<]+)</title><link rel=\'alternate\' type=\'text/html\' href=\'([^\']+).+?rel=\'http://schemas.google.com/docs/2007/thumbnail\' type=\'image/[^\']+\' href=\'([^\']+)\'' ,
                             entry, re.DOTALL):
                              title,url,thumbnail = r.groups()

                              # memory-cache
                              if cacheType == self.CACHE_TYPE_MEMORY:
                                  videos[title] = {'mediaType': self.MEDIA_TYPE_VIDEO, 'url': str(url)+ '|' + self.getHeadersEncoded(), 'thumbnail':  thumbnail}

                              # memory-cache
                              elif cacheType == self.CACHE_TYPE_DISK:
                                  videos[title] = {'mediaType': self.MEDIA_TYPE_VIDEO, 'url': str(url), 'thumbnail':  thumbnail}

                              # streaming
                              else:
                                  videos[title] = {'mediaType': self.MEDIA_TYPE_VIDEO,'url': PLUGIN_URL+'?mode=streamVideo&title=' + str(title), 'thumbnail': thumbnail}
                              processed = 1

                      if processed == 0:
                          # audio
                          for r in re.finditer('<title>([^<]+)</title><content type=\'audio\/[^\']+\' src=\'([^\']+)\'' ,
                             entry, re.DOTALL):
                              title,url = r.groups()

                              # there is no steaming for audio (?), so "download to stream"
                              videos[title] = {'mediaType': self.MEDIA_TYPE_MUSIC, 'url': str(url)+ '|' + self.getHeadersEncoded(), 'thumbnail':  ''}
                              processed = 1
                      if processed == 0:
                          # audio
                          for r in re.finditer('<title>([^<]+)</title><content type=\'application\/x-flac\' src=\'([^\']+)\'' ,
                             entry, re.DOTALL):
                              title,url = r.groups()

                              # there is no steaming for audio (?), so "download to stream"
                              videos[title] = {'mediaType': self.MEDIA_TYPE_MUSIC, 'url': str(url)+ '|' + self.getHeadersEncoded(), 'thumbnail':  ''}
                              processed = 1

                      if processed == 0:
                          # pictures
                          for r in re.finditer('<title>([^<]+)</title><content type=\'image\/[^\']+\' src=\'([^\']+)\'.+?rel=\'http://schemas.google.com/docs/2007/thumbnail\' type=\'image/[^\']+\' href=\'([^\']+)\'' ,
                             entry, re.DOTALL):
                              title,url,thumbnail = r.groups()

                              # there is no steaming for audio (?), so "download to stream"
#                          videos[title] = {'mediaType': self.MEDIA_TYPE_PICTURE, 'url': url+ '|' + self.getHeadersEncoded(), 'thumbnail':  ''}
                              cleanURL = re.sub('---', '', url)
                              cleanURL = re.sub('&amp;', '---', cleanURL)
#                          cleanURL = re.sub('=', '~~~', cleanURL)
#                          cleanURL = re.sub(';', '~-~-', cleanURL)
                              videos[title] = {'mediaType': self.MEDIA_TYPE_PICTURE,'url': PLUGIN_URL+'?mode=photo&folder='+str(folder)+'&title='+str(title)+'&url=' + str(cleanURL), 'thumbnail': thumbnail}

#                          videos[title] = {'mediaType': self.MEDIA_TYPE_MUSIC, 'url':  PLUGIN_URL+'?mode=photo&url=/u01/test.png', 'thumbnail':  ''}
                              processed = 1

                      if processed == 0:
                          # pictures
                          for r in re.finditer('<title>([^<]+)</title><content type=\'application\/octet-stream\' src=\'([^\']+)\'' ,
                             entry, re.DOTALL):
                            title,url = r.groups()

                          # there is no steaming for audio (?), so "download to stream"
#                          videos[title] = {'mediaType': self.MEDIA_TYPE_PICTURE, 'url': url+ '|' + self.getHeadersEncoded(), 'thumbnail':  ''}
                            cleanURL = re.sub('---', '', url)
                            cleanURL = re.sub('&amp;', '---', cleanURL)
#                          cleanURL = re.sub('=', '~~~', cleanURL)
#                          cleanURL = re.sub(';', '~-~-', cleanURL)
                            videos[title] = {'mediaType': self.MEDIA_TYPE_PICTURE,'url': PLUGIN_URL+'?mode=photo&folder='+str(folder)+'&title='+str(title)+'&url=' + str(cleanURL), 'thumbnail': ''}

#                          videos[title] = {'mediaType': self.MEDIA_TYPE_MUSIC, 'url':  PLUGIN_URL+'?mode=photo&url=/u01/test.png', 'thumbnail':  ''}


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

        return videos



    ##
    # retrieve a list of videos, using playback type stream
    #   parameters: cache type (optional)
    #   returns: list of videos
    ##
    def downloadFolder(self,path,folder, context):

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
                self.login()
                req = urllib2.Request(url, None, self.getHeadersList())
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  log(str(e), True)
                  return
              else:
                log(str(e), True)
                return

            response_data = response.read()
            response.close()

            # video-entry
            for r in re.finditer('\<entry[^\>]+\>(.*?)\<\/entry\>' ,response_data, re.DOTALL):
                entry = r.group(1)

                # fetch folder
                for r in re.finditer('\<gd\:resourceId\>([^\:]*)\:?([^\<]*)\</gd:resourceId\>' ,
                             entry, re.DOTALL):
                  resourceType,resourceID = r.groups()

                  # entry is NOT a folder
                  if not (resourceType == 'folder'):

                      if context != self.MEDIA_TYPE_PICTURE:
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

                      elif context == self.MEDIA_TYPE_PICTURE:

                          # pictures
                          for r in re.finditer('<title>([^<]+)</title><content type=\'image\/[^\']+\' src=\'([^\']+)\'' ,
                             entry, re.DOTALL):
                               title,url = r.groups()

                               url = re.sub('&amp;', '&', url)
                               if not os.path.exists(path + '/'+folder+'/'+title):
                                   self.downloadPicture(url,path +'/' + folder + '/' + title)


                      # pictures
                      for r in re.finditer('<title>([^<]+)</title><content type=\'application\/[^\']+\' src=\'([^\']+)\'' ,
                             entry, re.DOTALL):
                          title,url = r.groups()

                          url = re.sub('&amp;', '&', url)
                          if not os.path.exists(path + '/'+folder+'/'+title):
                            self.downloadPicture(url,path +'/' + folder + '/' + title)


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
                self.login()
                req = urllib2.Request(url, None, self.getHeadersList())
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  log(str(e), True)
                  return
              else:
                log(str(e), True)
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
    # retrieve a video link
    #   parameters: title of video, whether to prompt for quality/format (optional), cache type (optional)
    #   returns: list of URLs for the video or single URL of video (if not prompting for quality)
    ##
    def getVideoLink(self,title,cacheType=CACHE_TYPE_MEMORY,pquality=-1,pformat=-1,acodec=-1):


        # search by video title
        params = urllib.urlencode({'title': title, 'title-exact': 'true'})
        url = PROTOCOL+'docs.google.com/feeds/default/private/full?' + params

        req = urllib2.Request(url, None, self.getHeadersList())


        # if action fails, validate login
        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            if e.code == 403 or e.code == 401:
              self.login()
              req = urllib2.Request(url, None, self.getHeadersList())
              try:
                response = urllib2.urlopen(req)
              except urllib2.URLError, e:
                log(str(e), True)
                return
            else:
              log(str(e), True)
              return

        response_data = response.read()
        response.close()


        # fetch video title, download URL and docid for stream link
        for r in re.finditer('\<entry[^\>]+\>(.*?)\<\/entry\>' ,response_data, re.DOTALL):
             entry = r.group(1)
             for q in re.finditer('<title>([^<]+)</title><content type=\'([^\/]+)\/[^\']+\' src=\'([^\']+)\'.*\;docid=([^\&]+)\&' ,
                             entry, re.DOTALL):
               title,mediaType,url,docid = q.groups()

        if cacheType == self.CACHE_TYPE_MEMORY or cacheType == self.CACHE_TYPE_DISK:
          return url
        else:
            videos =  self.getVideoStream(docid, pquality,pformat,acodec)
            videos['original'] = url
            return videos



    def downloadPicture(self,url, file):

        req = urllib2.Request(url, None, self.getHeadersList())

#        import xbmcvfs
#        f = xbmcvfs.File(file, 'w')
#        f = open(file,'wb')
        # if action fails, validate login
        try:
#          f.write(urllib2.urlopen(req).read())
#            f.write(urllib2.urlopen(req).read())
#            f.close()
                open(file,'wb').write(urllib2.urlopen(req).read())

        except urllib2.URLError, e:
              self.login()
              req = urllib2.Request(url, None, self.getHeadersList())
              try:
                open(file,'wb').write(urllib2.urlopen(req).read())
#                f.write(urllib2.urlopen(req).read())
#                f.close()
              except urllib2.URLError, e:
                log(str(e), True)
                return


    def downloadDecryptPicture(self,key,url, file):

        req = urllib2.Request(url, None, self.getHeadersList())


        # if action fails, validate login
        try:
#          open('/tmp/tmp','wb').write(urllib2.urlopen(req).read())
#          encryption.decrypt_file(key,'/tmp/tmp',file)
          encryption.decrypt_stream(key,urllib2.urlopen(req),file)
        except urllib2.URLError, e:
            if e.code == 403 or e.code == 401:
              self.login()
              req = urllib2.Request(url, None, self.getHeadersList())
              try:
                encryption.decrypt_stream(key,urllib2.urlopen(req),file)
#                open('/tmp/tmp','wb').write(urllib2.urlopen(req).read())
#                encryption.decrypt_file(key,'/tmp/tmp',file)

              except urllib2.URLError, e:
                log(str(e), True)
                return
            else:
              log(str(e), True)
              return


    ##
    # retrieve a stream link
    #   parameters: docid of video, whether to prompt for quality/format (optional)
    #   returns: list of streams for the video or single stream of video (if not prompting for quality)
    ##
    def getVideoStream(self,docid='',pquality=-1,pformat=-1,acodec=-1,url=''):

        if docid != '':
            # player using docid
            params = urllib.urlencode({'docid': docid})
            url = PROTOCOL+'docs.google.com/get_video_info?docid=' + str((docid))
            req = urllib2.Request(url, None, self.getHeadersList(self.useWRITELY))
        else:
            #try to use no authorization token (for pubic URLs)
            header = { 'User-Agent' : self.user_agent, 'GData-Version' : self.API_VERSION }
            req = urllib2.Request(url, None, header)


        # if action fails, validate login
        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            if e.code == 403 or e.code == 401:
              self.login()
              req = urllib2.Request(url, None, self.getHeadersList(self.useWRITELY))
              try:
                response = urllib2.urlopen(req)
              except urllib2.URLError, e:
                log(str(e), True)
                return
            else:
              log(str(e), True)
              return

        response_data = response.read()
        response.close()

        # decode resulting player URL (URL is composed of many sub-URLs)
        urls = response_data
        urls = urllib.unquote(urllib.unquote(urllib.unquote(urllib.unquote(urllib.unquote(urls)))))
        urls = re.sub('\\\\u003d', '=', urls)
        urls = re.sub('\\\\u0026', '&', urls)

        serviceRequired = ''
        for r in re.finditer('ServiceLogin\?(service)=([^\&]+)\&' ,
                             urls, re.DOTALL):
            (service, serviceRequired) = r.groups()


        #effective 2014/02, video stream calls require a wise token instead of writely token
        #backward support for account not migrated to the 2014/02 change
        if serviceRequired == 'writely':
          self.useWRITELY = True
          req = urllib2.Request(url, None, self.getHeadersList(self.useWRITELY))

          try:
              response = urllib2.urlopen(req)
          except urllib2.URLError, e:
              if e.code == 403 or e.code == 401:
                self.login()
                req = urllib2.Request(url, None, self.getHeadersList(self.useWRITELY))
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  log(str(e), True)
                  return
              else:
                log(str(e), True)
                return

          response_data = response.read()
          response.close()

          # decode resulting player URL (URL is composed of many sub-URLs)
          urls = response_data
          urls = urllib.unquote(urllib.unquote(urllib.unquote(urllib.unquote(urllib.unquote(urls)))))
          urls = re.sub('\\\\u003d', '=', urls)
          urls = re.sub('\\\\u0026', '&', urls)


          serviceRequired = ''
          for r in re.finditer('ServiceLogin\?(service)=([^\&]+)\&' ,
                               urls, re.DOTALL):
              (service, serviceRequired) = r.groups()


          if serviceRequired != '':
            log('an unexpected service token is required: %s' % (serviceRequired), True)

        elif serviceRequired == 'wise':
          self.useWRITELY = False
          req = urllib2.Request(url, None, self.getHeadersList(self.useWRITELY))

          try:
              response = urllib2.urlopen(req)
          except urllib2.URLError, e:
              if e.code == 403 or e.code == 401:
                self.login()
                req = urllib2.Request(url, None, self.getHeadersList(self.useWRITELY))
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  log(str(e), True)
                  return
              else:
                log(str(e), True)
                return

          response_data = response.read()
          response.close()

          # decode resulting player URL (URL is composed of many sub-URLs)
          urls = response_data
          urls = urllib.unquote(urllib.unquote(urllib.unquote(urllib.unquote(urllib.unquote(urls)))))
          urls = re.sub('\\\\u003d', '=', urls)
          urls = re.sub('\\\\u0026', '&', urls)


          serviceRequired = ''
          for r in re.finditer('ServiceLogin\?(service)=([^\&]+)\&' ,
                               urls, re.DOTALL):
              (service, serviceRequired) = r.groups()


          if serviceRequired != '':
            log('an unexpected service token is required: %s' % (serviceRequired), True)

        elif serviceRequired != '':
          log('an unexpected service token is required: %s' % (serviceRequired), True)


        # do some substitutions to make anchoring the URL easier
        urls = re.sub('\&url\='+PROTOCOL, '\@', urls)

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
        videos = {}
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
                videos[str(order+count) + ' - ' + itagDB[itag]['resolution'] + ' - ' + containerDB[container] + ' - ' + itagDB[itag]['codec']] = PROTOCOL + videoURL
            except KeyError:
                videos[str(order+count) + ' - ' + itagDB[itag]['resolution'] + ' - ' + container] = PROTOCOL + videoURL

        return videos


    # for playing public URLs
    def getPublicStream(self,url):

        #try to use no authorization token (for pubic URLs)
        header = { 'User-Agent' : self.user_agent, 'GData-Version' : self.API_VERSION }

        req = urllib2.Request(url, None, header)

        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            if e.code == 403 or e.code == 401:
              self.loginWISE()
              req = urllib2.Request(url, None, self.getHeadersList(self.useWRITELY))
              try:
                response = urllib2.urlopen(req)
              except urllib2.URLError, e:
                log(str(e), True)
                return
            else:
              log(str(e), True)
              return

        response_data = response.read()
        response.close()


        serviceRequired = ''
        for r in re.finditer('ServiceLogin\?(service)=([^\&]+)\&' ,
                             response_data, re.DOTALL):
            (service, serviceRequired) = r.groups()

        for r in re.finditer('AccountChooser.+?(service)=([^\']+)\'' ,
                             response_data, re.DOTALL):
            (service, serviceRequired) = r.groups()


        #effective 2014/02, video stream calls require a wise token instead of writely token
        #backward support for account not migrated to the 2014/02 change
        if serviceRequired == 'writely':
          self.useWRITELY = True

          if (self.writely == ''):
            self.login();

          req = urllib2.Request(url, None, self.getHeadersList(self.useWRITELY))

          try:
              response = urllib2.urlopen(req)
          except urllib2.URLError, e:
              if e.code == 403 or e.code == 401:
                self.login()
                req = urllib2.Request(url, None, self.getHeadersList(self.useWRITELY))
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  log(str(e), True)
                  return
              else:
                log(str(e), True)
                return

          response_data = response.read()
          response.close()

          for r in re.finditer('"(fmt_stream_map)":"([^\"]+)"' ,
                             response_data, re.DOTALL):
              (urlType, urls) = r.groups()

          urls = re.sub('\\\\u003d', '=', urls)
          urls = re.sub('\\\\u0026', '&', urls)


          serviceRequired = ''
          for r in re.finditer('ServiceLogin\?(service)=([^\&]+)\&' ,
                               urls, re.DOTALL):
              (service, serviceRequired) = r.groups()


          if serviceRequired != '':
            log('an unexpected service token is required: %s' % (serviceRequired), True)

        elif serviceRequired == 'wise':
          self.useWRITELY = False
          if (self.wise == ''):
            self.loginWISE();

          req = urllib2.Request(url, None, self.getHeadersList(self.useWRITELY))

          try:
              response = urllib2.urlopen(req)
          except urllib2.URLError, e:
              if e.code == 403 or e.code == 401:
                self.loginWISE()
                req = urllib2.Request(url, None, self.getHeadersList(self.useWRITELY))
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  log(str(e), True)
                  return
              else:
                log(str(e), True)
                return

          response_data = response.read()
          response.close()


          for r in re.finditer('"(fmt_stream_map)":"([^\"]+)"' ,
                             response_data, re.DOTALL):
              (urlType, urls) = r.groups()

          urls = re.sub('\\\\u003d', '=', urls)
          urls = re.sub('\\\\u0026', '&', urls)


          serviceRequired = ''
          for r in re.finditer('ServiceLogin\?(service)=([^\&]+)\&' ,
                               urls, re.DOTALL):
              (service, serviceRequired) = r.groups()


          if serviceRequired != '':
            log('an unexpected service token is required: %s' % (serviceRequired), True)


        elif serviceRequired != '':
          log('an unexpected service token is required: %s' % (serviceRequired), True)

        for r in re.finditer('"(fmt_stream_map)":"([^\"]+)"' ,
                             response_data, re.DOTALL):
            (urlType, urls) = r.groups()

        urls = re.sub('\\\\u003d', '=', urls)
        urls = re.sub('\\\\u0026', '&', urls)


        urls = re.sub('\d+\|'+PROTOCOL, '\@', urls)

        for r in re.finditer('\@([^\@]+)' ,urls):
          videoURL = r.group(0)
        videoURL1 = PROTOCOL + videoURL


        return videoURL1

    ##
    # retrieve a media file
    #   parameters: title of video, whether to prompt for quality/format (optional), cache type (optional)
    ##
    def downloadMediaFile(self,url, title, fileSize):

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
        opener.addheaders = [('User-Agent', self.user_agent), ('Authorization' , 'GoogleLogin auth='+self.writely), ('GData-Version' , self.API_VERSION)]
        request = urllib2.Request(url)

        # if action fails, validate login

        cachePercent = 0
        try:
            cachePercent = int(ADDON.getSetting('cache_percent'))
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
            CHUNK = int(ADDON.getSetting('chunk_size'))
        except:
            CHUNK = 32 * 1024

        if CHUNK < 1024:
            CHUNK = 16 * 1024

        count = 0
        path = ''
        try:
            path = ADDON.getSetting('cache_folder')
        except:
            pass

        import os.path

        if not os.path.exists(path):
                path = ''

        while path == '':
            path = xbmcgui.Dialog().browse(0,ADDON.getLocalizedString(30026), 'files','',False,False,'')
            if not os.path.exists(path):
                path = ''
            else:
                ADDON.setSetting('cache_folder', path)



        # if action fails, validate login
        try:
            response = opener.open(request)
        except urllib2.URLError, e:
            if e.code == 403 or e.code == 401:
              self.login()
              opener.addheaders = [('User-Agent', self.user_agent), ('Authorization' , 'GoogleLogin auth='+self.writely), ('GData-Version' , self.API_VERSION)]
              request = urllib2.Request(url)
              try:
                  response = opener.open(request)
              except urllib2.URLError, e:
                xbmc.log(ADDON.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                return
            else:
              xbmc.log(ADDON.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
              return

        progress = xbmcgui.DialogProgress()
        progress.create(ADDON.getLocalizedString(30000),ADDON.getLocalizedString(30035),title,'\n')
#        (0,ADDON.getLocalizedString(30026), addon.getLocalizedString(30034),'',False,False,'')

#        with open(path + 'test.mp4', 'wb') as fp:

        filename = 'cache.mp4'

        fp = open(path + filename, 'wb')
        downloadedBytes = 0
        while sizeDownload > downloadedBytes:
                progress.update((int)(float(downloadedBytes)/sizeDownload*100),ADDON.getLocalizedString(30035),(str)(cachePercent) + ' ' +ADDON.getLocalizedString(30036),'\n')
                chunk = response.read(CHUNK)
                if not chunk: break
                fp.write(chunk)
                downloadedBytes = downloadedBytes + CHUNK

        self.response = response
        self.fp = fp
        return path + filename

   ##
    # retrieve a media file
    #   parameters: title of video, whether to prompt for quality/format (optional), cache type (optional)
    ##
    def continuedownloadMediaFile(self, url):

        CHUNK = 0
        try:
            CHUNK = int(ADDON.getSetting('chunk_size'))
        except:
            CHUNK = 32 * 1024

        if CHUNK < 1024:
            CHUNK = 16 * 1024

#        fp = open(url, 'a')
        while True:
                chunk = self.response.read(CHUNK)
                if not chunk: break
                self.fp.write(chunk)
        self.fp.close()


