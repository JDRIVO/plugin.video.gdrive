'''
    Copyright (C) 2014-2016 ddurdle

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


from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

import re
import urllib, urllib2

import xbmc, xbmcaddon, xbmcgui, xbmcplugin


class MyHTTPServer(HTTPServer):

    def __init__(self, *args, **kw):
        HTTPServer.__init__(self, *args, **kw)

    def setFile(self, playbackURL, chunksize, playbackFile, response, fileSize, url, service):
        self.playbackURL = playbackURL
        self.chunksize = chunksize
        self.playbackFile = playbackFile
        self.response = response
        self.fileSize = fileSize
        self.url = url
        self.service = service
        self.ready = True
        self.state = 0
        self.lock = 0


class myStreamer(BaseHTTPRequestHandler):


    #Handler for the GET requests
    def do_GET(self):

        if self.path == '/kill':
            self.server.ready = False
            return

        headers = str(self.headers)
        print(headers)

        start = ''
        end = ''
        count = 0
        for r in re.finditer('Range\:\s+bytes\=(\d+)\-' ,
                     headers, re.DOTALL):
          start = int(r.group(1))
          break
        for r in re.finditer('Range\:\s+bytes\=\d+\-(\d+)' ,
                     headers, re.DOTALL):
          end = int(r.group(1))
          if end == 0:
              end = ''
          break


        if start == '':
            self.send_response(200)
            self.send_header('Content-Length',self.server.fileSize)
        else:
            self.send_response(206)
            if start  > 0:
                count = int(start/int(self.server.chunksize))

            self.send_header('Content-Length',str(self.server.fileSize-(count*int(self.server.chunksize))))
            self.send_header('Content-Range','bytes ' + str(start) + '-' + str(self.server.fileSize-1)+'/'+str(self.server.fileSize))

            req = urllib2.Request(self.server.url, None, self.server.service.getHeadersList(additionalHeader='Range', additionalValue='bytes '+ str(start) + '-' + str(end)))
            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                print "error " + str(e.code) + ' header Range' + str(start) + '-' + str(end)
                self.server.service.refreshToken()
                req = urllib2.Request(self.server.url, None, self.server.service.getHeadersList(additionalHeader='Range', additionalValue='bytes '+ str(start) + '-' + str(end)))
                try:
                    response = urllib2.urlopen(req)
                except urllib2.URLError, e:
                    print "error " + str(e.code)
                    return

        self.send_header('Content-type','video/mp4')

        self.send_header('Accept-Ranges','bytes')
        self.end_headers()

        #while self.server.state == 2:
        #    self.server.state = 3
        #while self.server.state == 3:
        #    xbmc.sleep(10)

        if self.server.state == 0:
            #self.server.state = 2
            #try:
            if count == 0:
                with open(self.server.playbackURL, "rb") as f:
                    while True:
                        chunk = f.read(self.server.chunksize)
                        if chunk:
                            self.wfile.write(chunk)
                            count = count + 1
                        else:
                            break
                f.close()

            #fi = open(self.server.playbackFile, 'ab')
            #self.server.state = 1
            if  self.server.lock != 0:
                 self.server.lock = 2
                 xbmc.sleep(1000)

            self.server.lock = 1
            while self.server.lock ==1:#self.server.state == 2:

                chunk = self.server.response.read(self.server.chunksize)
                if not chunk: break
                fi = open(self.server.playbackFile, 'wb')
                fi.seek(self.server.chunksize*count,0)
                fi.write(chunk)
                fi.close()

                with open(self.server.playbackURL, "rb") as f:
                        f.seek(self.server.chunksize*count,0)
                        chunk = f.read(self.server.chunksize)
                        self.wfile.write(chunk)

                f.close()
                count = count + 1
            self.server.lock = 0
            #fi.close()
            #except: pass
            #if self.server.state == 2:
            #    self.server.ready = False
            #self.server.state = 0
            self.server.ready = False
#        else:
#            self.server.state = 1
#            self.server.ready = False
        return

