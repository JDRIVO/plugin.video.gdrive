'''
    gdrive XBMC Plugin
    Copyright (C) 2013 dmdsoftware

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
        
addon = xbmcaddon.Addon(id='plugin.video.gdrive')

def log(msg, err=False):
    if err:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg.encode('utf-8'), xbmc.LOGERROR)    
    else:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg.encode('utf-8'), xbmc.LOGDEBUG)    

class gdrive:


    def __init__(self, user, password, auth, user_agent):
        self.user = user
        self.password = password
        self.writely = auth
        self.user_agent = user_agent

        # if we have an authorization token set, try to use it
        if auth != '':
          log('using token')

          return
        log('logging in gdrive') 
        self.login();

        return


    def login(self):

        url = 'https://www.google.com/accounts/ClientLogin'
        header = { 'User-Agent' : self.user_agent }
        values = {
          'Email' : self.user,
          'Passwd' : self.password,
          'accountType' : 'HOSTED_OR_GOOGLE',
          'source' : 'dmdgdrive',
          'service' : 'writely'
        }

        log('logging in gdrive') 

#        log('username %s %s' % (user,urllib.urlencode(values))) 
        req = urllib2.Request(url, urllib.urlencode(values), header)

        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            if e.code == 403:
              xbmcgui.Dialog().ok(addon.getLocalizedString(30000), 'Login information is incorrect or permission is denied')
            log(str(e), True)
            return

        response_data = response.read()
        log('response %s' % response_data) 
        log('info %s' % str(response.info())) 

        for r in re.finditer('SID=(.*).+?' +
                             'LSID=(.*).+?' +
                             'Auth=(.*).+?' ,
                             response_data, re.DOTALL):
            sid,lsid,auth = r.groups()

        log('parameters: %s %s %s' % (sid, lsid, auth))

        self.writely = auth

        return


    def returnHeaders(self):
        return urllib.urlencode({ 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.writely, 'GData-Version' : '3.0' })
       

    def getList(self):
        log('getting list in gdrive') 


        url = 'https://docs.google.com/feeds/default/private/full?showfolders=true'
        header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.writely, 'GData-Version' : '3.0' }

        req = urllib2.Request(url, None, header)

        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            if e.code == 403 or e.code == 401:
              self.login()
              header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.writely, 'GData-Version' : '3.0' }
              req = urllib2.Request(url, None, header)
              try:
                response = urllib2.urlopen(req)
              except urllib2.URLError, e:
                log(str(e), True)
                return
            else:
              log(str(e), True)
              return

        response_data = response.read()

        nextURL = ''
        for r in re.finditer('<link rel=\'(next)\'' ,
                             response_data, re.DOTALL):
            nextURL = r.groups()
            log('next URL url=%s' % nextURL) 

        log('next URL %s' % nextURL) 


        log('response %s' % response_data) 
        log('info %s' % str(response.info())) 


    def getVideos(self):
        log('getting video list in gdrive') 

        header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.writely, 'GData-Version' : '3.0' }

        url = 'https://docs.google.com/feeds/default/private/full?showfolders=true'

        videos = []
        while True:
            log('url = %s header = %s' % (url, header)) 
            req = urllib2.Request(url, None, header)

            log('loading ' + url) 
            try:
              response = urllib2.urlopen(req)
            except urllib2.URLError, e:
              if e.code == 403 or e.code == 401:
                self.login()
                header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.writely, 'GData-Version' : '3.0' }
                req = urllib2.Request(url, None, header)
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  log(str(e), True)
                  return
              else:
                log(str(e), True)
                return

            response_data = response.read()

            log('checking video list in gdrive') 

            for r in re.finditer('<title>([^<]+)</title><content type=\'video/[^\']+\' src=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                title,url = r.groups()
                log('found video %s %s' % (title, url)) 
                videos.append({'title': title, 'url': url})

            nextURL = ''
            for r in re.finditer('<link rel=\'next\' type=\'[^\']+\' href=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                nextURL = r.groups()
                log('next URL url='+nextURL[0]) 

            response.close()

            if nextURL == '':
                break
            else:
                url = nextURL[0]

        log('exit get video') 
        return videos        

    def getVideosHash(self):
        log('getting video list in gdrive') 

        header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.writely, 'GData-Version' : '3.0' }

        url = 'https://docs.google.com/feeds/default/private/full?showfolders=true'

        videos = {}
        while True:
            log('url = %s header = %s' % (url, header)) 
            req = urllib2.Request(url, None, header)

            log('loading ' + url) 
            try:
              response = urllib2.urlopen(req)
            except urllib2.URLError, e:
              if e.code == 403 or e.code == 401:
                self.login()
                header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.writely, 'GData-Version' : '3.0' }
                req = urllib2.Request(url, None, header)
                try:
                  response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                  log(str(e), True)
                  return
              else:
                log(str(e), True)
                return

            response_data = response.read()

            log('checking video list in gdrive') 

            for r in re.finditer('<title>([^<]+)</title><content type=\'video/[^\']+\' src=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                title,url = r.groups()
                log('found video %s %s' % (title, url)) 
                videos[title] = url

            nextURL = ''
            for r in re.finditer('<link rel=\'next\' type=\'[^\']+\' href=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                nextURL = r.groups()
                log('next URL url='+nextURL[0]) 

            response.close()

            if nextURL == '':
                break
            else:
                url = nextURL[0]

        log('exit get video') 
        return videos 

    def getVideoLink(self,title):
        log('searching for video in gdrive') 

        header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.writely, 'GData-Version' : '3.0' }


	params = urllib.urlencode({'title': title, 'title-exact': 'true'})
        url = 'https://docs.google.com/feeds/default/private/full?' + params
       

        log('url = %s header = %s' % (url, header)) 
        req = urllib2.Request(url, None, header)

        log('loading ' + url) 
        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            if e.code == 403 or e.code == 401:
              self.login()
              header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.writely, 'GData-Version' : '3.0' }
              req = urllib2.Request(url, None, header)
              try:
                response = urllib2.urlopen(req)
              except urllib2.URLError, e:
                log(str(e), True)
                return
            else:
              log(str(e), True)
              return

        response_data = response.read()

        log('checking search result') 

        for r in re.finditer('<title>([^<]+)</title><content type=\'video/[^\']+\' src=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
          title,url = r.groups()
          log('found video %s %s' % (title, url)) 
          videoURL = url

        response.close()

 
        log('exit get video') 
        return videoURL 

    def getVideoPlayerLink(self,title):
        log('searching for video in gdrive') 

        header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.writely, 'GData-Version' : '3.0' }


	params = urllib.urlencode({'title': title, 'title-exact': 'true'})
        url = 'https://docs.google.com/feeds/default/private/full?' + params
       

        log('url = %s header = %s' % (url, header)) 
        req = urllib2.Request(url, None, header)

        log('loading ' + url) 
        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            if e.code == 403 or e.code == 401:
              self.login()
              header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.writely, 'GData-Version' : '3.0' }
              req = urllib2.Request(url, None, header)
              try:
                response = urllib2.urlopen(req)
              except urllib2.URLError, e:
                log(str(e), True)
                return
            else:
              log(str(e), True)
              return

        response_data = response.read()

        log('checking search result') 

        for r in re.finditer('<title>([^<]+)</title><content type=\'video/[^\']+\' src=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
          title,url = r.groups()
          log('found video %s %s' % (title, url)) 
          videoURL = url

        for r in re.finditer('\;docid=([^\&]+)(\&)' ,
                             response_data, re.DOTALL):
          (docid,u) = r.groups()
          log('found docid %s' % (docid)) 
          return self.getPlayerLink(docid)

        response.close()

 
        log('exit get video') 
        return False 
 
    def getPlayerLink(self,docid):
        log('fetching player link') 

        header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.writely, 'GData-Version' : '3.0' }


	params = urllib.urlencode({'docid': docid})
        url = 'https://docs.google.com/get_video_info?docid=' + str((docid))
       

        log('url = %s header = %s' % (url, header)) 
        req = urllib2.Request(url, None, header)

        log('loading ' + url) 
        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            if e.code == 403 or e.code == 401:
              self.login()
              header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.writely, 'GData-Version' : '3.0' }
              req = urllib2.Request(url, None, header)
              try:
                response = urllib2.urlopen(req)
              except urllib2.URLError, e:
                log(str(e), True)
                return
            else:
              log(str(e), True)
              return

        response_data = response.read()

        log('response %s' % response_data) 
        log('info %s' % str(response.info())) 
        log('checking search result') 

        for r in re.finditer('[^\=]+https%3A%2F%2F(.*)url\%3Dhttps\%253A\%252(.*)url\%3Dhttps\%253A\%252' ,
                             response_data, re.DOTALL):
          (videoURL1,videoURL2) = r.groups()
          log('found videoURL1 %s %s' % (urllib.unquote(videoURL1), videoURL2)) 
          videoURL1 = 'https://' + urllib.unquote(videoURL1)

        response.close()

 
        log('exit get video') 
        return videoURL1 

