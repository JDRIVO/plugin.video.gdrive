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
import urllib
import re


#
#
#
class offlinefile:
    # CloudService v0.2.4
    #


    ##
    ##
    def __init__(self, title, thumbnail, resolution, stream):
        self.title = title
        self.thumbnail = thumbnail

        self.resolution = resolution
        self.playbackpath = stream


    def displayTitle(self):
        if self.decryptedTitle != '':
            return urllib.unquote(str(self.decryptedTitle) + ' [' + str(self.title) + ']')
        else:
            return urllib.unquote(self.title)

    def displayShowTitle(self):
        if self.decryptedTitle != '':
            return urllib.unquote(str(self.decryptedTitle) + ' [' + str(self.title) + ']')
        elif self.showtitle is not None and self.showtitle != '':
            return urllib.unquote(self.showtitle)
        else:
            return urllib.unquote(self.title)

    def displayTrackTitle(self):
        if self.decryptedTitle != '':
            return urllib.unquote(str(self.decryptedTitle) + ' [' + str(self.title) + ']')
        elif self.showtitle is not None and self.trackTitle != '':
            return urllib.unquote(self.trackTitle)
        else:
            return urllib.unquote(self.title)

    def __repr__(self):
        return '{}: {} {}'.format(self.__class__.__name__,
                                  self.title)

    def __cmp__(self, other):
        if hasattr(other, 'title'):
            return self.title.__cmp__(other.title)

    def getKey(self):
        return self.title
