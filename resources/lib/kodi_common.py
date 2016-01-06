'''
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

# cloudservice - required python modules
import sys
import cgi

# cloudservice - standard XBMC modules
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs


from resources.lib import settings


# global variables
addon = xbmcaddon.Addon(id='plugin.video.gdrive')
#addon = xbmcaddon.Addon(id='plugin.video.gdrive-testing')
PLUGIN_URL = sys.argv[0]
plugin_handle = int(sys.argv[1])


##
# load eclipse debugger
#   parameters: none
##
def debugger():
    try:

        remote_debugger = settings.getSetting('remote_debugger')
        remote_debugger_host = settings.getSetting('remote_debugger_host')

        # append pydev remote debugger
        if remote_debugger == 'true':
            # Make pydev debugger works for auto reload.
            # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
            import pysrc.pydevd as pydevd
            # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
            pydevd.settrace(remote_debugger_host, stdoutToServer=True, stderrToServer=True)
    except ImportError:
        xbmc.log(addon.getLocalizedString(30016), xbmc.LOGERROR)
        sys.exit(1)
    except :
        pass


##
# add a menu to a directory screen
#   parameters: url to resolve, title to display, optional: icon, fanart, total_items, instance name
##
def addMenu(url, title, img='', fanart='', total_items=0, instanceName=''):
        #    listitem = xbmcgui.ListItem(decode(title), iconImage=img, thumbnailImage=img)
        listitem = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        if not fanart:
            fanart = addon.getAddonInfo('path') + '/fanart.jpg'
        listitem.setProperty('fanart_image', fanart)

        # disallow play controls on menus
        listitem.setProperty('IsPlayable', 'false')


        if instanceName != '':
            cm=[]
            cm.append(( addon.getLocalizedString(30159), 'XBMC.RunPlugin('+PLUGIN_URL+ '?mode=delete&instance='+instanceName+')' ))
            listitem.addContextMenuItems(cm, True)



        xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
                                isFolder=True, totalItems=total_items)



##
# Providing a context type, return what content to display based on user's preferences
#   parameters: current context type plugin was invoked in (audio, video, photos)
##
def getContentType(contextType,encfs):

    #contentType
    #video context
    # 0 video
    # 1 video and music
    # 2 everything
    # 9 encrypted video
    #
    #music context
    # 3 music
    # 4 everything
    # 10 encrypted video
    #
    #photo context
    # 5 photo
    # 6 music and photos
    # 7 everything
    # 11 encrypted photo


      contentType = 0

      if contextType == 'video':

        if encfs:
            contentTypeDecider =  int(settings.getSetting('context_evideo',0))

            if contentTypeDecider == 1:
                contentType = 8
            else:
                contentType = 9

        else:
            contentTypeDecider = int(settings.getSetting('context_video',0))

            if contentTypeDecider == 2:
                contentType = 2
            elif contentTypeDecider == 1:
                contentType = 1
            else:
                contentType = 0
        # cloudservice - sorting options
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')

      elif contextType == 'audio':
        if encfs:
            contentTypeDecider =  int(settings.getSetting('context_emusic',0))
            if contentTypeDecider == 1:
                contentType = 8
            else:
                contentType = 10
        else:

            contentTypeDecider = int(settings.getSetting('context_music', 0))

            if contentTypeDecider == 1:
                contentType = 4
            else:
                contentType = 3
        # cloudservice - sorting options
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TRACKNUM)

      elif contextType == 'image':
        if encfs:
            contentTypeDecider =  int(settings.getSetting('context_ephoto',0))
            if contentTypeDecider == 1:
                contentType = 8
            else:
                contentType = 11
        else:
            contentTypeDecider = int(settings.getSetting('context_photo', 0))

            if contentTypeDecider == 2:
                contentType = 7
            elif contentTypeDecider == 1:
                contentType = 6
            else:
                contentType = 5

      # show all (for encfs)
      elif contextType == 'all':
            contentType = 8


      return contentType


