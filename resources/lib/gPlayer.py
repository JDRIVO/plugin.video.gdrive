
'''
    gdrive XBMC Plugin
    Copyright (C) 2013-12015 ddurdle

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


class gPlayer(xbmc.Player):

    try:

        import pysrc.pydevd as pydevd
        # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
        pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)
    except :
        pass

    def __init__( self, *args, **kwargs ):
        xbmc.Player.__init__( self )
        self.isExit = 0

    def setScheduler(self,scheduler):
        self.tvScheduler = scheduler

    def setWorksheet(self,worksheet):
        self.worksheet = worksheet


    def setContent(self, episodes):
        self.content = episodes
        self.current = 0

    def next(self):

#            log('video ' + str(episodes[self.current][CONSTANTS.D_SOURCE]) + ',' + str(episodes[self.current][CONSTANTS.D_SHOW]))

#        addVideo('plugin://plugin.video.gdrive?mode=playvideo&amp;title='+episodes[video][0],
#                             { 'title' : str(episodes[video][CONSTANTS.D_SHOW]) + ' - S' + str(episodes[video][CONSTANTS.D_SEASON]) + 'xE' + str(episodes[video][CONSTANTS.D_EPISODE]) + ' ' + str(episodes[video][CONSTANTS.D_PART])  , 'plot' : episodes[video][CONSTANTS.D_SHOW] },
#                             img='None')
        # play video
#            if self.isExit == 0:
#                self.play('plugin://plugin.video.gdrive?mode=playvideo&amp;title='+self.content[self.current][0])
                self.play(self.content[self.current][0])

                self.tvScheduler.setVideoWatched(self.worksheet, self.content[self.current][0])
                if self.current < len(self.content):
                    self.current += 1
                else:
                    self.current = 0

#                while self.isPlaying():
#                    xbmc.sleep(1000)



    def PlayStream(self, url):
        self.play(url)
#        while self.isPlaying(): #<== The should be    while self.isPlaying():
#            xbmc.sleep(1000)

    def onPlayBackStarted(self):
        print "PLAYBACK STARTED"
        print self.getPlayingFile()

    def onPlayBackEnded(self):
        print "PLAYBACK ENDED"
        self.next()

    def onPlayBackStopped(self):
        print "PLAYBACK STOPPED"
        self.isExit = 1
        if self.isExit == 0:
            print "don't exit"

    def onPlayBackPaused(self):
        print "PLAYBACK Paused"
        self.seekTime(10)

