'''
    gdrive XBMC Plugin
    Copyright (C) 2013-2015 ddurdle

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

import xbmc, xbmcaddon, xbmcgui, xbmcplugin

import authorization
import crashreport


class gSpreadsheets:

    S_CHANNEL=0
    S_MONTH=1
    S_DAY=2
    S_WEEKDAY=3
    S_HOUR=4
    S_MINUTE=5
    S_SHOW=6
    S_ORDER=7
    S_INCLUDE_WATCHED=8


    D_SOURCE=0
    D_NFO=1
    D_SHOW=2
    D_SEASON=3
    D_EPISODE=4
    D_PART=5
    D_WATCHED=6
    D_DURATION=7

    def __init__(self, service, addon, user_agent):
        self.addon = addon
        self.user_agent = user_agent
        self.service = service
#        self.crashreport = crashreport
#        self.crashreport.sendError('test','test')


        self.cookiejar = cookielib.CookieJar()

        self.user_agent = user_agent

        return



    #
    # returns a list of spreadsheets and a link to their worksheets
    #
    def getSpreadsheetList(self):

        url = 'https://spreadsheets.google.com/feeds/spreadsheets/private/full'

        spreadsheets = {}
        while True:
            req = urllib2.Request(url, None, self.service.getHeadersList())

            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                if e.msg != '':
                    xbmcgui.Dialog().ok(self.addon.getLocalizedString(30000), e.msg)
                    xbmc.log(self.addon.getAddonInfo('getSpreadsheetList') + ': ' + str(e), xbmc.LOGERROR)
                    self.crashreport.sendError('getSpreadsheetList',str(e))

            response_data = response.read()
            response.close()


            for r in re.finditer('<title [^\>]+\>([^<]+)</title><content [^\>]+\>[^<]+</content><link rel=\'[^\#]+\#worksheetsfeed\' type=\'application/atom\+xml\' href=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                title,url = r.groups()
                spreadsheets[title] = url

            nextURL = ''
            for r in re.finditer('<link rel=\'next\' type=\'[^\']+\' href=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                nextURL = r.groups()


            if nextURL == '':
                break
            else:
                url = nextURL[0]


        return spreadsheets

    #
    # returns a list of spreadsheets contained in the Google Docs account
    #
    def createWorksheet(self,url,title,cols,rows):

        header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.authorization.getToken('wise'), 'GData-Version' : '3.0',  'Content-Type': 'application/atom+xml' }

        entry = '<?xml version=\'1.0\' encoding=\'UTF-8\'?><entry xmlns="http://www.w3.org/2005/Atom" xmlns:gs="http://schemas.google.com/spreadsheets/2006"><title>A worksheetdadf</title><gs:rowCount>100</gs:rowCount><gs:colCount>20</gs:colCount></entry>'

        req = urllib2.Request(url, entry, header)

        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
            return False

        response_data = response.read()
        response.close()

        return True

    #
    # returns a list of spreadsheets contained in the Google Docs account
    #
    def createRow(self,url, folderID, folderName, fileID, fileName):


        header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.authorization.getToken('wise'), 'GData-Version' : '3.0',  'Content-Type': 'application/atom+xml'}

        entry = '<?xml version=\'1.0\' encoding=\'UTF-8\'?><entry xmlns="http://www.w3.org/2005/Atom" xmlns:gsx="http://schemas.google.com/spreadsheets/2006/extended"> <gsx:foldername>'+folderName+'</gsx:foldername> <gsx:folderuid>'+folderID+'</gsx:folderuid> <gsx:filename>'+fileName+'</gsx:filename> <gsx:fileuid>'+fileID+'</gsx:fileuid>  <gsx:season>1</gsx:season>  <gsx:episode>1</gsx:episode> <gsx:watched>1</gsx:watched> <gsx:sequence>1</gsx:sequence></entry>'

        req = urllib2.Request(url, entry, header)

        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
            return False

        response_data = response.read()
        response.close()

        return True

    #
    # returns a list of spreadsheets contained in the Google Docs account
    #
    def createHeaderRow(self,url):

        header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.authorization.getToken('wise'), 'GData-Version' : '3.0',  "If-Match" : '*', 'Content-Type': 'application/atom+xml'}

        entry = '<?xml version=\'1.0\' encoding=\'UTF-8\'?><entry xmlns="http://www.w3.org/2005/Atom" xmlns:gsx="http://schemas.google.com/spreadsheets/2006/extended"> <gsx:hours>1</gsx:hours></entry>'

        req = urllib2.Request(url, entry, header)

        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
            return False

        response_data = response.read()
        response.close()

        return True

    #
    # returns a list of worksheets with a link to their listfeeds
    #
    def getSpreadsheetWorksheets(self,url):

        worksheets = {}
        while True:
            req = urllib2.Request(url, None, self.service.getHeadersList())

            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                xbmc.log(self.addon.getAddonInfo('getSpreadsheetWorksheets') + ': ' + str(e), xbmc.LOGERROR)

            response_data = response.read()
            response.close()


            for r in re.finditer('<title[^>]+\>([^<]+)</title><content[^>]+\>[^<]+</content><link rel=\'[^\#]+\#listfeed\' type=\'application/atom\+xml\' href=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                title,url = r.groups()
                worksheets[title] = url

            nextURL = ''
            for r in re.finditer('<link rel=\'next\' type=\'[^\']+\' href=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                nextURL = r.groups()


            if nextURL == '':
                break
            else:
                url = nextURL[0]


        return worksheets

    def getShows(self,url,channel):


        params = urllib.urlencode({'channel': channel})
        url = url + '?sq=' + params


        shows = {}
        while True:
            req = urllib2.Request(url, None, self.service.getHeadersList())

            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)

            response_data = response.read()

            count=0;
            for r in re.finditer('<gsx:channel>([^<]*)</gsx:channel><gsx:month>([^<]*)</gsx:month><gsx:day>([^<]*)</gsx:day><gsx:weekday>([^<]*)</gsx:weekday><gsx:hour>([^<]*)</gsx:hour><gsx:minute>([^<]*)</gsx:minute><gsx:show>([^<]*)</gsx:show><gsx:order>([^<]*)</gsx:order><gsx:includewatched>([^<]*)</gsx:includewatched>' ,
                             response_data, re.DOTALL):
                shows[count] = r.groups()
#source,nfo,show,season,episode,part,watched,duration
#channel,month,day,weekday,hour,minute,show,order,includeWatched
                count = count + 1

            nextURL = ''
            for r in re.finditer('<link rel=\'next\' type=\'[^\']+\' href=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                nextURL = r.groups()

            response.close()

            if nextURL == '':
                break
            else:
                url = nextURL[0]


        return shows


    def getMediaInformation(self,url,folderID):

        params = urllib.urlencode({'folderuid': folderID})
        url = url + '?sq=' + params


        media = {}
        while True:
            req = urllib2.Request(url, None, self.service.getHeadersList())

            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                return

            response_data = response.read()

            count=0;
            for r in re.finditer('<gsx:foldername>([^<]*)</gsx:foldername><gsx:folderuid>([^<]*)</gsx:folderuid><gsx:filename>([^<]*)</gsx:filename><gsx:fileuid>([^<]*)</gsx:fileuid><gsx:season>([^<]*)</gsx:season><gsx:episode>([^<]*)</gsx:episode><gsx:watched>([^<]*)</gsx:watched><gsx:sequence>([^<]*)</gsx:sequence>' ,
                             response_data, re.DOTALL):
                media[count] = r.groups()
                count = count + 1

            nextURL = ''
            for r in re.finditer('<link rel=\'next\' type=\'[^\']+\' href=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                nextURL = r.groups()

            response.close()

            if nextURL == '':
                break
            else:
                url = nextURL[0]


        return media

    def getVideo(self,url,show):
        params = urllib.urlencode({'show': show})
        url = url + '?sq=' + params + '+and+watched=0'


        shows = {}
        while True:
            req = urllib2.Request(url, None, self.service.getHeadersList())

            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)

            response_data = response.read()

            count=0;
            for r in re.finditer('<entry[^\>]*>.*?<gsx:source>([^<]*)</gsx:source><gsx:nfo>([^<]*)</gsx:nfo><gsx:show>([^<]*)</gsx:show><gsx:season>([^<]*)</gsx:season><gsx:episode>([^<]*)</gsx:episode><gsx:part>([^<]*)</gsx:part><gsx:watched>([^<]*)</gsx:watched><gsx:duration>([^<]*)</gsx:duration></entry>' ,
                             response_data, re.DOTALL):
                shows[count] = r.groups()
                #source,nfo,show,season,episode,part,watched,duration
                count = count + 1

            nextURL = ''
            for r in re.finditer('<link rel=\'next\' type=\'[^\']+\' href=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                nextURL = r.groups()

            response.close()

            if nextURL == '':
                break
            else:

                url = nextURL[0]

        return shows


    def setVideoWatched(self,url,source):

#        import urllib
#        from cookielib import CookieJar

#        cj = CookieJar()
#        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
#        urllib2.install_opener(opener)


        source = re.sub(' ', '%20', source)
#        params = urllib.urlencode(source)
        url = url + '?sq=source="' + source +'"'

        req = urllib2.Request(url, None, self.service.getHeadersList())

        try:
            response = urllib2.urlopen(req)
#            response = opener.open(url, None,urllib.urlencode(header))
        except urllib2.URLError, e:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)

        response_data = response.read()
        response.close()

        editURL=''
        for r in re.finditer('<link rel=\'(edit)\' type=\'application/atom\+xml\' href=\'([^\']+)\'/>' ,
                             response_data, re.DOTALL):
            (x,editURL) = r.groups(1)

        for r in re.finditer('(.*?)(<entry .*?</entry>)' ,
                             response_data, re.DOTALL):
            (x,entry) = r.groups(1)


#        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
#        urllib2.install_opener(opener)

#        req = urllib2.Request(editURL, None, header)

#        try:
#            response = urllib2.urlopen(req)
#            response = opener.open(url, None,urllib.urlencode(header))
#        except urllib2.URLError, e:
#                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)

#        response_data = response.read()

#        response.close()

#        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

       # data_encoded = urllib.urlencode(formdata)
#        urllib2.install_opener(opener)

        entry = re.sub('<gsx:watched>([^\<]*)</gsx:watched>', '<gsx:watched>1</gsx:watched>', entry)
        #editURL = re.sub('https', 'http', editURL)

        header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.authorization.getToken('wise'), 'GData-Version' : '3.0', "If-Match" : '*', "Content-Type": 'application/atom+xml' }


        entry = re.sub(' gd\:etag[^\>]+>', ' xmlns="http://www.w3.org/2005/Atom" xmlns:gs="http://schemas.google.com/spreadsheets/2006" xmlns:gsx="http://schemas.google.com/spreadsheets/2006/extended">', entry)
#        entry = "<?xml version='1.0' encoding='UTF-8'?>"+entry
#        entry = '<feed xmlns="http://www.w3.org/2005/Atom" xmlns:openSearch="http://a9.com/-/spec/opensearch/1.1/" xmlns:gsx="http://schemas.google.com/spreadsheets/2006/extended" xmlns:gd="http://schemas.google.com/g/2005" gd:etag=\'W/"D0cERnk-eip7ImA9WBBXGEg."\'><entry>  <id>    https://spreadsheets.google.com/feeds/worksheets/key/private/full/worksheetId  </id>  <updated>2007-07-30T18:51:30.666Z</updated>  <category scheme="http://schemas.google.com/spreadsheets/2006"    term="http://schemas.google.com/spreadsheets/2006#worksheet"/>  <title type="text">Income</title>  <content type="text">Expenses</content>  <link rel="http://schemas.google.com/spreadsheets/2006#listfeed"    type="application/atom+xml" href="https://spreadsheets.google.com/feeds/list/key/worksheetId/private/full"/>  <link rel="http://schemas.google.com/spreadsheets/2006#cellsfeed"    type="application/atom+xml" href="https://spreadsheets.google.com/feeds/cells/key/worksheetId/private/full"/>  <link rel="self" type="application/atom+xml"    href="https://spreadsheets.google.com/feeds/worksheets/key/private/full/worksheetId"/>  <link rel="edit" type="application/atom+xml"    href="https://spreadsheets.google.com/feeds/worksheets/key/private/full/worksheetId/version"/>  <gs:rowCount>45</gs:rowCount>  <gs:colCount>15</gs:colCount></entry>'

        req = urllib2.Request(editURL, entry, header)
#        urllib2.HTTPHandler(debuglevel=1)
        req.get_method = lambda: 'PUT'


        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e.read()), xbmc.LOGERROR)

        response_data = response.read()

        response.close()


    def getChannels(self,url):
        params = urllib.urlencode({'orderby': 'channel'})
        url = url + '?' + params


        channels = []
        count=0

        while True:
            req = urllib2.Request(url, None, self.service.getHeadersList())

            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)

            response_data = response.read()


            for r in re.finditer('<gsx:channel>([^<]*)</gsx:channel>' ,
                             response_data, re.DOTALL):
                (channel) = r.groups()
                #channel,month,day,weekday,hour,minute,show,order,includeWatched
                if not channels.__contains__(channel[0]):
                  channels.append(channel[0])
                  count = count + 1

            nextURL = ''
            for r in re.finditer('<link rel=\'next\' type=\'[^\']+\' href=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                nextURL = r.groups()

            response.close()

            if nextURL == '':
                break
            else:
                url = nextURL[0]

        return channels


