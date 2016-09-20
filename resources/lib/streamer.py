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




class MyHTTPServer(HTTPServer):

    def __init__(self, *args, **kw):
        HTTPServer.__init__(self, *args, **kw)

    def setFile(self, playbackURL, chunksize):
        self.playbackURL = playbackURL
        self.chunksize = chunksize
        self.ready = True
        self.state = 0


class myStreamer(BaseHTTPRequestHandler):


    #Handler for the GET requests
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','video/mp4')
        self.end_headers()
        if self.server.state != 0:
            with open(self.server.playbackURL, "rb") as f:
                while True:
                    chunk = f.read(self.server.chunksize)
                    if chunk:
                        self.wfile.write(chunk)
                    else:
                        break
            #self.server.state = 1
            self.server.ready = False
        else:
            self.server.state = 1
            self.server.ready = True
        return

