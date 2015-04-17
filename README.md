KODI-gdrive / XBMC-gdrive
=========================

Google Drive Video add-on for XBMC

A video add-on for XBMC that enables playback of videos stored in a Google Drive account.

Supports [Tested on]:
All XBMC 12/13/14 including Linux, Windows, OS X, Android, Pivos, iOS (including ATV2)

The plugin uses the Google Docs API 3 and Google Drive API 2

Getting Started:
1) download the .zip file
2) transfer the .zip file to XBMC
3) in Video Add-on, select Install from .zip

Before starting the add-on for the first time, either "Configure" or right click and select "Add-on Settings".
Visit www.dmdsoftware.net for directions on setting up an OAUTH2 login.


Modes:
1) standard index
- starting the plugin via video add-ons will display a directory containing all video files within the Google Drive account or those that are shared to that account
- click on the video to playback
- don't create favourites from the index, as the index will contain a URL that will expire after 12-24 hours
2) mode=playvideo
- you can create .strm or .m3u files that run Google Drive videos direct
- create .strm or .m3u files containing the following: plugin://plugin.video.gdrive?mode=playvideo&amp;title=Title_of_video
- if your video is composed of multiple clips, you can create a .m3u that makes the above plugin:// call, one line for each clip.  You can then create a .strm file that points to the .m3u.  XBMC can index movies and shows contained in your Google Drive account by either a .strm containing a single plugin:// call to the video, or a .strm that points to a local .m3u file that contains a list of plugin:// calls representing the video

FAQ:

1) Is there support for Google Apps Google Drive accounts?
Yes.  Use your fully qualified username whether that is username@gmail.com or username@domain

2) Is there support for multiple accounts?
Yes, 9+ accounts are supposed

3) Does thie add-on support Pictures or other filetypes?
Yes, video, music and photos are supported


