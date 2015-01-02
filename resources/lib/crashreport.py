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
import os
import re
import urllib, urllib2
import cookielib
import random
import xbmc, xbmcgui, xbmcplugin, xbmcaddon


#
#
#
class crashreport:

    ##
    ##
    def __init__(self, addon):
        self.addon = addon
        self.pluginName = self.addon.getAddonInfo('name') + ' - ' + self.addon.getAddonInfo('id')
        self.pluginVersion = self.addon.getAddonInfo('version')
        self.xbmcVersion = self.addon.getSetting('crashreport_version') + ' - ' + self.addon.getSetting('crashreport_os')

        try:
            self.identifier = (int)(self.addon.getSetting('crashreport_ident'))
            if self.identifier < 1:
                self.identifier = random.randint(1, 10000)
        except:
            self.identifier = random.randint(1, 10000)

        try:
            self.email = self.addon.getSetting('crashreport_email')
            if self.addon.getSetting('crashreport_enable') == 'true':
                self.enabled = True
                self.cookiejar = cookielib.CookieJar()
            else:
                self.enabled = False
        except:
            self.enabled = False

    def sendError(self, error, details):

        if (self.enabled == True):
            diaglog = xbmcgui.Dialog()
            result = diaglog.yesno(self.addon.getLocalizedString(30000), self.addon.getLocalizedString(30070), self.addon.getLocalizedString(30071),self.addon.getLocalizedString(30072))

            if result == True:
                self.identifier = self.identifier + 1
                opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))

                url = 'https://docs.google.com/forms/d/1gTnjJfeNh2wnat7F4QS7aMHQtmYToqHUYilNbo8s8ps/formResponse'

                request = urllib2.Request(url)
                self.cookiejar.add_cookie_header(request)


                data = {}
                data['entry.977603264'] = str(self.identifier)
                data['entry.243770882'] = str(self.pluginName)
                data['entry.878700058'] = str(self.pluginVersion)
                data['entry.1258581285'] = str(self.email)
                data['entry.1260404759'] = str(self.xbmcVersion)
                data['entry.1753855090'] = str(details)
                data['entry.671238889'] = str(error)
                url_values = urllib.urlencode(data)

                # try login
                try:
#                    response = opener.open(request,'entry.977603264='+str(self.identifier)+'&entry.243770882='+str(self.pluginName)+'&entry.878700058='+str(self.pluginVersion)+'&entry.1258581285='+str(self.email)+'&entry.1260404759='+str(self.xbmcVersion)+'&entry.1753855090='+str(details)+'&entry.671238889='+str(error))
                    response = opener.open(request,url_values)

                except urllib2.URLError, e:
                    xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)
                    return
                response.close()
                xbmcgui.Dialog().ok(self.addon.getLocalizedString(30000), self.addon.getLocalizedString(30073), str(self.identifier))
                self.addon.setSetting('crashreport_ident', (str)(self.identifier))



