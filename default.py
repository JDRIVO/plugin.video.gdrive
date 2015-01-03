'''
    gdrive XBMC Plugin
    Copyright (C) 2013-2014 ddurdle

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

from resources.lib import encryption

import sys
import urllib
import cgi
import re

import xbmc, xbmcgui, xbmcplugin, xbmcaddon

# global variables
PLUGIN_NAME = 'gdrive'

#helper methods
def log(msg, err=False):
    if err:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg, xbmc.LOGERROR)
    else:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg, xbmc.LOGDEBUG)

def parse_query(query):
    queries = cgi.parse_qs(query)
    q = {}
    for key, value in queries.items():
        q[key] = value[0]
    q['mode'] = q.get('mode', 'main')
    return q


def addMediaFile(service, package):

    listitem = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail)

    if package.file.type == package.file.AUDIO:
        if package.file.hasMeta:
            infolabels = decode_dict({ 'title' : package.file.displayTitle(), 'tracknumber' : package.file.trackNumber, 'artist': package.file.artist, 'album': package.file.album,'genre': package.file.genre,'premiered': package.file.releaseDate })
        else:
            infolabels = decode_dict({ 'title' : package.file.displayTitle() })
        listitem.setInfo('Music', infolabels)
        playbackURL = '?mode=audio'
    elif package.file.type == package.file.VIDEO:
        infolabels = decode_dict({ 'title' : package.file.displayTitle() , 'plot' : package.file.plot })
        listitem.setInfo('Video', infolabels)
        playbackURL = '?mode=video'
    elif package.file.type == package.file.PICTURE:
        infolabels = decode_dict({ 'title' : package.file.displayTitle() , 'plot' : package.file.plot })
        listitem.setInfo('Pictures', infolabels)
        playbackURL = '?mode=photo'
    else:
        infolabels = decode_dict({ 'title' : package.file.displayTitle() , 'plot' : package.file.plot })
        llistitem.setInfo('Video', infolabels)
        playbackURL = '?mode=video'

    listitem.setProperty('IsPlayable', 'true')
    listitem.setProperty('fanart_image', package.file.fanart)
    cm=[]

    try:
        url = package.getMediaURL()
        cleanURL = re.sub('---', '', url)
        cleanURL = re.sub('&', '---', cleanURL)
    except:
        cleanURL = ''

#    url = PLUGIN_URL+'?mode=streamurl&title='+package.file.title+'&url='+cleanURL
    url = PLUGIN_URL+playbackURL+'&title='+package.file.title+'&filename='+package.file.id

    # gdrive specific ***
    cm.append(( 'Play cache file', 'XBMC.RunPlugin('+PLUGIN_URL+'?mode=cache&file=cache.mp4)', ))
    # ***

    cm.append(( addon.getLocalizedString(30042), 'XBMC.RunPlugin('+PLUGIN_URL+'?mode=buildstrm&title='+package.file.title+'&filename='+package.file.id+')', ))
#    cm.append(( addon.getLocalizedString(30046), 'XBMC.PlayMedia('+playbackURL+'&title='+ package.file.title + '&directory='+ package.folder.id + '&filename='+ package.file.id +'&playback=0)', ))
#    cm.append(( addon.getLocalizedString(30047), 'XBMC.PlayMedia('+playbackURL+'&title='+ package.file.title + '&directory='+ package.folder.id + '&filename='+ package.file.id +'&playback=1)', ))
#    cm.append(( addon.getLocalizedString(30048), 'XBMC.PlayMedia('+playbackURL+'&title='+ package.file.title + '&directory='+ package.folder.id + '&filename='+ package.file.id +'&playback=2)', ))
    #cm.append(( addon.getLocalizedString(30032), 'XBMC.RunPlugin('+PLUGIN_URL+'?mode=download&title='+package.file.title+'&filename='+package.file.id+')', ))

#    listitem.addContextMenuItems( commands )
#    if cm:
    listitem.addContextMenuItems(cm, False)

    # gdrive specific ***
    cacheType = int(addon.getSetting('playback_type'))

    if cacheType == 1:

        fileSize = ''
        for r in re.finditer('(size)\=(\d+)' ,
                             url, re.DOTALL):
            (size, fileSize) = r.groups()

        url = PLUGIN_URL+'?mode=play&size='+fileSize+'&url='+url
    # ***

    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
                                isFolder=False, totalItems=0)


def addDirectory(service, folder):

    listitem = xbmcgui.ListItem(decode(folder.displayTitle()), iconImage=decode(folder.thumb), thumbnailImage=decode(folder.thumb))
    fanart = addon.getAddonInfo('path') + '/fanart.jpg'


    if folder.id != '':
        cm=[]
        cm.append(( addon.getLocalizedString(30042), 'XBMC.RunPlugin('+PLUGIN_URL+'?mode=buildstrm&title='+folder.title+'&instanceName='+str(service.instanceName)+'&folderID='+str(folder.id)+')', ))
#        cm.append(( addon.getLocalizedString(30081), 'XBMC.RunPlugin('+PLUGIN_URL+'?mode=createbookmark&title='+folder.title+'&instanceName='+str(service.instanceName)+'&folderID='+str(folder.id)+')', ))

        # gdrive specific ****
#        cm.append(( 'slideshow', 'XBMC.RunPlugin('+PLUGIN_URL+'?mode=slideshow&folder='+url+')', ))
        # ***

        listitem.addContextMenuItems(cm, False)
    listitem.setProperty('fanart_image', fanart)

    xbmcplugin.addDirectoryItem(plugin_handle, service.getDirectoryCall(folder), listitem,
                                isFolder=True, totalItems=0)


def addMenu(url, title, img='', fanart='', total_items=0):
    listitem = xbmcgui.ListItem(decode(title), iconImage=img, thumbnailImage=img)
    if not fanart:
        fanart = addon.getAddonInfo('path') + '/fanart.jpg'
    listitem.setProperty('fanart_image', fanart)

    # allow play controls on folders
    listitem.setProperty('IsPlayable', 'true')
    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
                                isFolder=True, totalItems=total_items)

#http://stackoverflow.com/questions/1208916/decoding-html-entities-with-python/1208931#1208931
def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id))
    except:
        return id

def decode(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data).strip()

def decode_dict(data):
    for k, v in data.items():
        if type(v) is str or type(v) is unicode:
            data[k] = decode(v)
    return data


def numberOfAccounts(accountType):

    count = 1
    try:
        max_count = int(addon.getSetting(accountType+'_numaccounts'))
    except:
        max_count = 10
    actualCount = 0
    while True:
        try:
            if addon.getSetting(accountType+str(count)+'_username') != '':
                actualCount = actualCount + 1
        except:
            break
        if count == max_count:
            break
        count = count + 1
    return actualCount

#global variables
PLUGIN_URL = sys.argv[0]
plugin_handle = int(sys.argv[1])
plugin_queries = parse_query(sys.argv[2][1:])

addon = xbmcaddon.Addon(id='plugin.video.gdrive-testing')

addon_dir = xbmc.translatePath( addon.getAddonInfo('path') )


import os
sys.path.append(os.path.join( addon_dir, 'resources', 'lib' ) )

import gdrive
import cloudservice
import folder
import file
import package
import mediaurl
import authorization

try:

    remote_debugger = addon.getSetting('remote_debugger')
    remote_debugger_host = addon.getSetting('remote_debugger_host')

    # append pydev remote debugger
    if remote_debugger == 'true':
        # Make pydev debugger works for auto reload.
        # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
        import pysrc.pydevd as pydevd
        # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
        pydevd.settrace(remote_debugger_host, stdoutToServer=True, stderrToServer=True)
except ImportError:
    log(addon.getLocalizedString(30016), True)
    sys.exit(1)
except :
    pass


# retrieve settings
user_agent = addon.getSetting('user_agent')

#promptQuality = addon.getSetting('prompt_quality')

#if promptQuality == 'true':
#    promptQuality = True
#else:
#    promptQuality = False

# hidden parameters which may not even be defined
try:
    useWRITELY = addon.getSetting('force_writely')
    if useWRITELY == 'true':
        useWRITELY = True
    else:
        useWRITELY = False
except :
    useWRITELY = True


mode = plugin_queries['mode']

# make mode case-insensitive
mode = mode.lower()


log('plugin url: ' + PLUGIN_URL)
log('plugin queries: ' + str(plugin_queries))
log('plugin handle: ' + str(plugin_handle))

# allow for playback of public videos without authentication
if (mode == 'streamurl'):
  authenticate = False
else:
  authenticate = True

instanceName = ''
try:
    instanceName = (plugin_queries['instance']).lower()
except:
    pass

#* utilities *
#clear the authorization token(s) from the identified instanceName or all instances
if mode == 'clearauth':

    if instanceName != '':

        try:
            # gdrive specific ***
            addon.setSetting(instanceName + '_auth_writely', '')
            addon.setSetting(instanceName + '_auth_wise', '')
            # ***
            xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30023))
        except:
            #error: instance doesn't exist
            pass

    # clear all accounts
    else:
        count = 1
        max_count = int(addon.getSetting(PLUGIN_NAME+'_numaccounts'))
        while True:
            instanceName = PLUGIN_NAME+str(count)
            try:
                # gdrive specific ***
                addon.setSetting(instanceName + '_auth_writely', '')
                addon.setSetting(instanceName + '_auth_wise', '')
                # ***
            except:
                break
            if count == max_count:
                break
            count = count + 1
        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30023))
    xbmcplugin.endOfDirectory(plugin_handle)


#create strm files
elif mode == 'buildstrm':

    try:
        path = addon.getSetting('path')
    except:
        path = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30026), 'files','',False,False,'')

    if path == '':
        path = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30026), 'files','',False,False,'')

    if path != '':
        returnPrompt = xbmcgui.Dialog().yesno(addon.getLocalizedString(30000), addon.getLocalizedString(30027) + '\n'+path +  '?')


    if path != '' and returnPrompt:

        try:
            url = plugin_queries['streamurl']
            title = plugin_queries['title']
            url = re.sub('---', '&', url)
        except:
            url=''

        if url != '':

                filename = xbmc.translatePath(os.path.join(path, title+'.strm'))
                strmFile = open(filename, "w")

                strmFile.write(url+'\n')
                strmFile.close()
        else:

            try:
                folderID = plugin_queries['folderID']
                title = plugin_queries['title']
                instanceName = plugin_queries['instanceName']
            except:
                folderID = ''

            try:
                filename = plugin_queries['filename']
                title = plugin_queries['title']
            except:
                filename = ''


            if folderID != '':

                try:
                    username = addon.getSetting(instanceName+'_username')
                except:
                    username = ''

                if username != '':
                    service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
                    service.buildSTRM(path + '/'+title,folderID)


            elif filename != '':
                            url = PLUGIN_URL+'?mode=video&title='+title+'&filename='+filename
                            filename = xbmc.translatePath(os.path.join(path, title+'.strm'))
                            strmFile = open(filename, "w")

                            strmFile.write(url+'\n')
                            strmFile.close()

            else:

                count = 1
                max_count = int(addon.getSetting(PLUGIN_NAME+'_numaccounts'))
                while True:
                    instanceName = PLUGIN_NAME+str(count)
                    try:
                        username = addon.getSetting(instanceName+'_username')
                    except:
                        username = ''

                    if username != '':
                        service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
                        service.buildSTRM(path + '/'+username)

                    if count == max_count:
                        break
                    count = count + 1


        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30028))
    xbmcplugin.endOfDirectory(plugin_handle)


numberOfAccounts = numberOfAccounts(PLUGIN_NAME)

# show list of services
if numberOfAccounts > 1 and instanceName == '':
    mode = ''
    count = 1
    max_count = int(addon.getSetting(PLUGIN_NAME+'_numaccounts'))
    while True:
        instanceName = PLUGIN_NAME+str(count)
        try:
            username = addon.getSetting(instanceName+'_username')
            if username != '':
                addMenu(PLUGIN_URL+'?mode=main&instance='+instanceName,username)
        except:
            break
        if count == max_count:
            break
        count = count + 1

else:
    # show index of accounts
    if instanceName == '' and numberOfAccounts == 1:

        count = 1
        loop = True
        while loop:
            instanceName = PLUGIN_NAME+str(count)
            try:
                username = addon.getSetting(instanceName+'_username')
                if username != '':

                    #let's log in
                    service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)
                    loop = False
            except:
                break

            if count == numberOfAccounts:
                break
            count = count + 1

    # no accounts defined
    elif numberOfAccounts == 0:

        #legacy account conversion
        try:
            username = addon.getSetting('username')

            if username != '':
                addon.setSetting(PLUGIN_NAME+'1_username', username)
                addon.setSetting(PLUGIN_NAME+'1_password', addon.getSetting('password'))
                addon.setSetting(PLUGIN_NAME+'1_auth_writely', addon.getSetting('auth_writely'))
                addon.setSetting(PLUGIN_NAME+'1_auth_wise', addon.getSetting('auth_wise'))
                addon.setSetting('username', '')
                addon.setSetting('password', '')
                addon.setSetting('auth_writely', '')
                addon.setSetting('auth_wise', '')
            else:
                xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30015))
                log(addon.getLocalizedString(30015), True)
                xbmcplugin.endOfDirectory(plugin_handle)
        except :
            xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30015))
            log(addon.getLocalizedString(30015), True)
            xbmcplugin.endOfDirectory(plugin_handle)

        #let's log in
        service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)


    # show entries of a single account (such as folder)
    elif instanceName != '':

        service = gdrive.gdrive(PLUGIN_URL,addon,instanceName, user_agent)

if mode == 'main':
    addMenu(PLUGIN_URL+'?mode=options','<< '+addon.getLocalizedString(30043)+' >>')


#dump a list of videos available to play
if mode == 'main' or mode == 'index':
    cacheType = int(addon.getSetting('playback_type'))

    folderName = ''
    try:
      folderName = plugin_queries['folder']
    except:
      folderName = False

    #contentType
    #video context
    # 0 video
    # 1 video and music
    # 2 everything
    #
    #music context
    # 3 music
    # 4 everything
    #
    #photo context
    # 5 photo
    # 6 music and photos
    # 7 everything

    try:
      contextType = plugin_queries['content_type']
      contentType = 0
      if contextType == 'video':
        if (int(addon.getSetting('context_video'))) == 2 and folderName != False:
            contentType = 2
        elif (int(addon.getSetting('context_video'))) == 1 and folderName != False:
            contentType = 1
        else:
            contentType = 0

      elif contextType == 'audio':
        if (int(addon.getSetting('context_music'))) == 1 and folderName != False:
            contentType = 4
        else:
            contentType = 3

      elif contextType == 'image':
        if (int(addon.getSetting('context_photo'))) == 2 and folderName != False:
            contentType = 7
        elif (int(addon.getSetting('context_photo'))) == 1 and folderName != False:
            contentType = 6
        else:
            contentType = 5
    except:
      contentType = 2


    # gdrive specific ***
    try:
      decrypt = plugin_queries['decrypt']
      gdrive.setDecrypt()
      log('decrypt ')
    except:
      decrypt = False
    # ***

    # display option for all Videos/Music/Photos, across gdrive
    # gdrive specific ***
    if mode == 'main':
        if contentType in (2,4,7):
            addMenu(PLUGIN_URL+'?mode=index&folder=&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30030)+' '+addon.getLocalizedString(30039)+']')
        elif contentType == 1:
            addMenu(PLUGIN_URL+'?mode=index&folder=&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30031)+' '+addon.getLocalizedString(30039)+']')
        elif contentType == 0:
            addMenu(PLUGIN_URL+'?mode=index&folder=&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30025)+' '+addon.getLocalizedString(30039)+']')
        elif contentType == 3:
            addMenu(PLUGIN_URL+'?mode=index&folder=&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30093)+' '+addon.getLocalizedString(30039)+']')
        elif contentType == 5:
            addMenu(PLUGIN_URL+'?mode=index&folder=&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30034)+' '+addon.getLocalizedString(30039)+']')
        elif contentType == 6:
            addMenu(PLUGIN_URL+'?mode=index&folder=&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30032)+' '+addon.getLocalizedString(30039)+']')
        folderName = 'root'
    # ***

    try:
        service
    except NameError:
        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30051), addon.getLocalizedString(30052))
        log(addon.getLocalizedString(30050)+ 'gdrive-login', True)
        xbmcplugin.endOfDirectory(plugin_handle)

#    videos = gdrive.getVideosList(cacheType, folder)
    mediaItems = service.getMediaList(folderName,0)

    isSorted = "0"
    try:
        isSorted = addon.getSetting('sorted')
    except:
         pass

    if mediaItems:
        if isSorted == "0":
            for item in sorted(mediaItems, key=lambda package: package.sortTitle):
#                try:
                    if item.file is None:
                        addDirectory(service, item.folder)
                    else:
                        addMediaFile(service, item)
#                except:
#                    addMediaFile(service, item)
        elif isSorted == "1":
            for item in sorted(mediaItems, key=lambda package: package.sortTitle, reverse=True):

#                try:
                    if item.file is None:
                        addDirectory(service, item.folder)
                    else:
                        addMediaFile(service, item)
#                except:
#                    addMediaFile(service, item)
        else:
            for item in mediaItems:

#                try:
                    if item.file is None:
                        addDirectory(service, item.folder)
                    else:
                        addMediaFile(service, item)
#                except:
#                    addMediaFile(service, item)

    service.updateAuthorization(addon)


#play a URL that is passed in (presumably requires authorizated session)
elif mode == 'play':
    url = plugin_queries['url']



    cacheType = int(addon.getSetting('playback_type'))

    fileSize = 0
    try:
      fileSize = plugin_queries['size']
    except:
      fileSize = 0


    if cacheType == 1:
#        url = gdrive.downloadMediaFile(url,url)
        url = gdrive.downloadMediaFile(url,url,fileSize)

    else:
        url = url + '|'+gdrive.getHeadersEncoded(gdrive.useWRITELY)

    item = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

    if cacheType == 1:
        gdrive.continuedownloadMediaFile(url)

#play a video given its exact-title
elif mode == 'cache':
    file = plugin_queries['file']


    path = ''
    try:
        path = addon.getSetting('cache_folder')
    except:
        pass

    import os.path

    if not os.path.exists(path):
        path = ''

    while path == '':
        path = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30026), 'files','',False,False,'')
        if not os.path.exists(path):
            path = ''
        else:
            addon.setSetting('cache_folder', path)

    xbmc.executebuiltin("XBMC.PlayMedia("+path +file+")")

#    item = xbmcgui.ListItem(path=path + file)
#    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

#play a video given its exact-title
elif mode == 'playvideo':
    title = plugin_queries['title']
    cacheType = int(addon.getSetting('playback_type'))

    videoURL = gdrive.getVideoLink(title,cacheType)

    if cacheType == 1:
        videoURL = gdrive.downloadMediaFile(videoURL,title, 0)
    else:
        #effective 2014/02, video stream calls require a wise token instead of writely token
        videoURL = videoURL + '|' + gdrive.getHeadersEncoded(gdrive.useWRITELY)

    item = xbmcgui.ListItem(path=videoURL)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

    if cacheType == 1:
        gdrive.continuedownloadMediaFile(reponse,fp)

#force memory-cache - play a video given its exact-title
elif mode == 'memorycachevideo':
    title = plugin_queries['title']
    videoURL = gdrive.getVideoLink(title)

    #effective 2014/02, video stream calls require a wise token instead of writely token
    videoURL = videoURL + '|' + gdrive.getHeadersEncoded(gdrive.useWRITELY)

    item = xbmcgui.ListItem(path=videoURL)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

elif mode == 'photo':
    try:
      url = plugin_queries['url']
    except:
      url = 0

    try:
      title = plugin_queries['title']
    except:
      title = 0

    try:
      folder = plugin_queries['folder']
    except:
      folder = 0


    path = ''
    try:
        path = addon.getSetting('photo_folder')
    except:
        pass

    import os.path

    if not os.path.exists(path):
        path = ''

    while path == '':
        path = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30038), 'files','',False,False,'')
        if not os.path.exists(path):
            path = ''
        else:
            addon.setSetting('photo_folder', path)

    url = re.sub('---', '&', url)

    import xbmcvfs
    xbmcvfs.mkdir(path + '/'+folder)
#    xbmcvfs.mkdir(path + '/'+folder + '/dir_'+title)
    try:
        xbmcvfs.rmdir(path + '/'+folder+'/'+title)
    except:
        pass

#    gdrive.downloadPicture(url, path + '/'+folder + '/dir_'+title + '/'+title)
    gdrive.downloadPicture(url, path + '/'+folder + '/'+title)
#    item.setInfo(type='pictures',infoLabels={"Title": 'PicasaWeb Photo', "picturepath": '/u01/test.png'})
#    item.setProperty('IsPlayable', 'true')

 #   xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, item)
#    xbmc.executebuiltin("XBMC.SlideShow(/tmp/)")
#    xbmc.executebuiltin("XBMC.SlideShow("+path + '/'+folder+"/)")
#    xbmc.executebuiltin("XBMC.ShowPicture("+path + '/'+folder + '/dir_'+title + '/'+title+")")
    xbmc.executebuiltin("XBMC.ShowPicture("+path + '/'+folder + '/'+title+")")

elif mode == 'downloadfolder':
    try:
      folder = plugin_queries['folder']
    except:
      folder = 0

    try:
      title = plugin_queries['title']
    except:
      title = 0

    path = '/tmp/2/'

    gdrive.downloadFolder(path,folder)

    enc_password = str(addon.getSetting('enc_password'))

    salt = encryption.read_salt(str(addon.getSetting('salt')))

    key = encryption.generate_key(enc_password,salt,encryption.NUMBER_OF_ITERATIONS)
    encryption.decrypt_dir(key,path,folder)

elif mode == 'decryptfolder':
    try:
      folder = plugin_queries['folder']
    except:
      folder = 0

    try:
      title = plugin_queries['title']
    except:
      title = 0

    path = '/tmp/2/'

    enc_password = str(addon.getSetting('enc_password'))

    salt = encryption.read_salt(str(addon.getSetting('salt')))

    key = encryption.generate_key(enc_password,salt,encryption.NUMBER_OF_ITERATIONS)

    gdrive.decryptFolder(key,path,folder)



elif mode == 'slideshow':
    try:
      folder = plugin_queries['folder']
    except:
      folder = 0

    try:
      title = plugin_queries['title']
    except:
      title = 0

    path = ''
    try:
        path = addon.getSetting('photo_folder')
    except:
        pass

    import os.path

    if not os.path.exists(path):
        path = ''

    while path == '':
        path = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30038), 'files','',False,False,'')
        if not os.path.exists(path):
            path = ''
        else:
            addon.setSetting('photo_folder', path)

    #    gdrive.downloadFolder(path,folder)
    gdrive.downloadFolder(path,folder, gdrive.MEDIA_TYPE_PICTURE)

    xbmc.executebuiltin("XBMC.SlideShow("+path + '/'+folder+"/)")

#force stream - play a video given its exact-title
elif mode == 'video':

    filename = plugin_queries['filename']

    try:
      title = plugin_queries['title']
    except:
      title = 0

    promptQuality = True
    try:
        promptQuality = addon.getSetting('prompt_quality')
        if promptQuality == 'false':
            promptQuality = False
    except:
        pass


    mediaFile = file.file(filename, title, '', 0, '','')
    mediaFolder = folder.folder('','')
    mediaURLs = service.getPlaybackCall(0,package=package.package(mediaFile,mediaFolder))

    options = []
    for mediaURL in mediaURLs:
        options.append(mediaURL.qualityDesc)
    if promptQuality:
        ret = xbmcgui.Dialog().select(addon.getLocalizedString(30033), options)
    else:
        ret = 0

    playbackURL = mediaURLs[ret].url

    item = xbmcgui.ListItem(path=playbackURL+'|' + service.getHeadersEncoded(service.useWRITELY))
    item.setInfo( type="Video", infoLabels={ "Title": title , "Plot" : title } )
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

#force stream - play a video given its exact-title
elif mode == 'streamvideo':

    try:
      title = plugin_queries['title']
    except:
      title = 0

    try:
      pquality = int(addon.getSetting('preferred_quality'))
      pformat = int(addon.getSetting('preferred_format'))
      acodec = int(addon.getSetting('avoid_codec'))
    except :
      pquality=-1
      pformat=-1
      acodec=-1

    mediaURLs = service.getPlaybackCall(0,title=title)

    options = []
    for mediaURL in mediaURLs:
        options.append(mediaURL.qualityDesc)
    ret = xbmcgui.Dialog().select(addon.getLocalizedString(30033), options)
    playbackURL = mediaURLs[ret].url

    item = xbmcgui.ListItem(path=playbackURL+'|' + gdrive.getHeadersEncoded(gdrive.useWRITELY))
    item.setInfo( type="Video", infoLabels={ "Title": title , "Plot" : title } )
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


#force stream - play a video given its exact-title
elif mode == 'streamurl':
    try:
      url = plugin_queries['url']
    except:
      url = 0

    # check for promptQuality override
    try:
      pquality = int(addon.getSetting('preferred_quality'))
      pformat = int(addon.getSetting('preferred_format'))
      acodec = int(addon.getSetting('avoid_codec'))
    except :
      pquality=-1
      pformat=-1
      acodec=-1

    singlePlayback=''
    videos = gdrive.getVideoStream(pquality=pquality,pformat=pformat,acodec=acodec, url=url)

    for label in sorted(videos.iterkeys()):
          addVideo(videos[label]+'|'+gdrive.getHeadersEncoded(gdrive.useWRITELY),
                             { 'title' : label , 'plot' : label },label,
                             img='None')
          if singlePlayback == '':
            singlePlayback = label


    if (singlePlayback == ''):
        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30020),addon.getLocalizedString(30021))
        xbmc.log(addon.getAddonInfo('name') + ': ' + addon.getLocalizedString(20021), xbmc.LOGERROR)
    else:
        # if invoked in .strm or as a direct-video (don't prompt for quality)
        item = xbmcgui.ListItem(path=videos[singlePlayback]+ '|' + gdrive.getHeadersEncoded(gdrive.useWRITELY))
        item.setInfo( type="Video", infoLabels={ "Title": label , "Plot" : label } )
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


# migrate *
#if username != prev_username:
#    addon.setSetting('prev_username', username)
# *

# the parameter set for wise vs writely was detected as incorrect during this run; reset as necessary
try:
    if useWRITELY == True  and service.useWRITELY == False:
        addon.setSetting('force_writely','false')
    elif useWRITELY == False and service.useWRITELY == True:
        addon.setSetting('force_writely','true')
except:
    pass
xbmcplugin.endOfDirectory(plugin_handle)

