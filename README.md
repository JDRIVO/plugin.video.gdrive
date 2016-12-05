gdrive for KODI / XBMC
======================

Google Drive Video add-on for KODI / XBMC

A video add-on for XBMC that enables playback of videos stored in a Google Drive account.

Supports [Tested on]:
All XBMC 12/13/14 including Linux, Windows, OS X, Android, Pivos, iOS (including ATV2)
Tested successfully on KODI 17 BETA 7.  If you encounter issues, update to BETA 7 or later.

The plugin uses the Google Docs API 3 and Google Drive API 2

Getting Started:
1) download the .zip file
2) transfer the .zip file to XBMC
3) in Video Add-on, select Install from .zip

Before starting the add-on for the first time, either "Configure" or right click and select "Add-on Settings".
Visit www.dmdsoftware.net for directions on setting up an OAUTH2 login.

Acount activation:

GOOGLE APPS OAUTH2 - READ-only (DEFAULT)
Visit in your browser and activate authorization, then create a username and passcode for the app:
https://accounts.google.com/o/oauth2/auth?approval_prompt=force&scope=https://www.googleapis.com/auth/drive.readonly+https://spreadsheets.google.com/feeds&access_type=offline&redirect_uri=https://script.google.com/macros/s/AKfycbzufq8WB4As_ksn28mFbfbX-WX5M75-JjB_AR_fejqXV49-TUvj/exec&response_type=code&client_id=772521706521-f97kus79uouccm1o60g7i08v02kqa584.apps.googleusercontent.com

GOOGLE APPS OAUTH2 - READ/WRITE (for saving resume points)
Visit in your browser and activate authorization, then create a username and passcode for the app:
https://accounts.google.com/o/oauth2/auth?approval_prompt=force&scope=https://www.googleapis.com/auth/drive+https://spreadsheets.google.com/feeds&access_type=offline&redirect_uri=https://script.google.com/macros/s/AKfycbzufq8WB4As_ksn28mFbfbX-WX5M75-JjB_AR_fejqXV49-TUvj/exec&response_type=code&client_id=772521706521-f97kus79uouccm1o60g7i08v02kqa584.apps.googleusercontent.com

Other options:
dmdsoftware.net OAUTH2 - READ-only (DEFAULT)
https://accounts.google.com/o/oauth2/auth?approval_prompt=force&scope=https://www.googleapis.com/auth/drive.readonly+https://spreadsheets.google.com/feeds&redirect_uri=urn:ietf:wg:oauth:2.0:oob&response_type=code&client_id=772521706521-bi11ru1d9h40h1lipvbmp3oddtcgro14.apps.googleusercontent.com
dmdsoftware.net OAUTH2 - READ/WRITE (for saving resume points)
https://accounts.google.com/o/oauth2/auth?approval_prompt=force&scope=https://www.googleapis.com/auth/drive+https://spreadsheets.google.com/feeds&redirect_uri=urn:ietf:wg:oauth:2.0:oob&response_type=code&client_id=772521706521-bi11ru1d9h40h1lipvbmp3oddtcgro14.apps.googleusercontent.com

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


