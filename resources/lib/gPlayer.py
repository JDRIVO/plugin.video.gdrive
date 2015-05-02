
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
        self.seek = 0
        self.package = None
        self.time = 0


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
                self.play('plugin://plugin.video.gdrive-testing/?mode=video&instance='+str(self.tvScheduler.service.instanceName)+'&title='+self.content[self.current][0])
#                self.play(self.content[self.current][0])

#                self.tvScheduler.setVideoWatched(self.worksheet, self.content[self.current][0])
#                self.tvScheduler.createRow(self.worksheet, '','','','')
                if self.current < len(self.content):
                    self.current += 1
                else:
                    self.current = 0


    def saveTime(self):
        try:
            newTime = self.getTime()
            if newTime > self.seek:
                self.time = newTime
        except:
            pass

    def PlayStream(self, url, item, seek, package=None):
        self.play(url, item)

        if package is not None:
            self.package = package

        if seek != '':
            self.seek = float(seek)
#        self.tvScheduler.setVideoWatched(self.worksheet, self.content[self.current][0])
        if seek > 0 and seek !='':
            while not self.isPlaying(): #<== The should be    while self.isPlaying():
                print "LOOP"
                xbmc.sleep(2000)
            xbmc.sleep(2000)
            print "SEEK "+str(seek)
            self.time = float(seek)
            self.seekTime(float(seek))

    def onPlayBackStarted(self):
        print "PLAYBACK STARTED"
#        if self.seek > 0:
#            self.seekTime(self.seek)

    def onPlayBackEnded(self):
        print "PLAYBACK ENDED"
#        self.next()
        if self.package is not None:
            self.tvScheduler.setMediaStatus(self.worksheet,self.package, watched=1)

    def onPlayBackStopped(self):
        print "PLAYBACK STOPPED"
        if self.package is not None:
            self.tvScheduler.setMediaStatus(self.worksheet,self.package, resume=self.time)
        self.isExit = 1
        if self.isExit == 0:
            print "don't exit"

    def onPlayBackPaused(self):
        print "PLAYBACK Paused"
        #self.seekTime(10)

