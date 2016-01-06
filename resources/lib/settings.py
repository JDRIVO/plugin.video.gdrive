'''
    Copyright (C) 2014 ddurdle

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

import sys
import cgi


#http://stackoverflow.com/questions/1208916/decoding-html-entities-with-python/1208931#1208931
def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id))
    except:
        return id

def decode(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data).strip()

def getParameter(key,default=''):
    try:
        value = plugin_queries[key]
        if value == 'true':
            return True
        elif value == 'false':
            return False
        else:
            return value
    except:
        return default

def getSetting(key,default=''):
    try:
        value = self.addon.getSetting(key)
        if value == 'true':
            return True
        elif value == 'false':
            return False
        else:
            return value
    except:
        return default

def parse_query(query):
    queries = cgi.parse_qs(query)
    q = {}
    for key, value in queries.items():
        q[key] = value[0]
    q['mode'] = q.get('mode', 'main')
    return q

plugin_queries = parse_query(sys.argv[2][1:])


#
#
#
class settings:
    # Settings

    ##
    ##
    def __init__(self, addon):
        self.addon = addon
        self.integratedPlayer = self.getSetting('integrated_player', False)
        self.cc = self.getParameter('cc', self.getSetting('cc', True))
        self.srt = self.getParameter('srt', self.getSetting('srt', True))
        self.username = self.getParameter('username', '')
        self.setCacheParameters()
        self.promptQuality = self.getParameter('promptquality', self.getSetting('prompt_quality', True))
        self.parseTV = self.getSetting('parse_tv', True)
        self.parseMusic = self.getSetting('parse_music', True)

    def setVideoParameters(self):
        self.seek = self.getParameter('seek', 0)
        self.resume = self.getParameter('resume', False)

        self.playOriginal = self.getParameter('original', self.getSetting('never_stream', False))


    def setCacheParameters(self):
        self.cache = self.getParameter('cache', False)
#        self.download = self.getSetting('always_cache', getParameter('download', False))
        self.download = self.getParameter('download', getSetting('always_cache', False))
        self.play = self.getParameter('play', getSetting('always_cache', False))
        self.cachePath = self.getSetting('cache_folder')
        self.cacheSingle = self.getSetting('cache_single')
        self.cachePercent = self.getSetting('cache_percent', 10)
        self.cacheChunkSize = self.getSetting('chunk_size', 32 * 1024)

        if self.cache:
            self.download = False
            self.play = False

    def getParameter(self, key, default=''):
        try:
            value = plugin_queries[key]
            if value == 'true':
                return True
            elif value == 'false':
                return False
            else:
                return value
        except:
            return default

    def getSetting(self, key, default=''):
        try:
            value = self.addon.getSetting(key)
            if value == 'true':
                return True
            elif value == 'false':
                return False
            else:
                return value
        except:
            return default
