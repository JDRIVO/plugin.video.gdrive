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

#
#
#
class downloadfile:


    ##
    ##
    def __init__(self, url, name):
        self.name = name
        self.url = url


    def __repr__(self):
        return '{}: {} {}'.format(self.__class__.__name__,
                                  self.name)

    def __cmp__(self, other):
        if hasattr(other, 'name'):
            return self.name.__cmp__(other.name)

    def getKey(self):
        return self.name

