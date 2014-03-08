XBMC-gdrive
===========

Google Drive Video add-on for XBMC

A video add-on for XBMC that enables playback of videos stored in a Google Drive account.

Supports [Tested on]:
All XBMC 12 and 12.2 including Linux, Windows, OS X, Android, Pivos, iOS (including ATV2)

*Note for Raspberry Pi users*: Due to a bug in libcurl with HTTPS streams (Google Drive uses HTTPS only), playback of content on these devices may not work.  I have tested on various Raspberry Pi distributions and have personally witnessed about a 90% failure rate for playback of videos over HTTPS.

The plugin uses the Google Docs API 3.

Getting Started:
1) download the .zip file
2) transfer the .zip file to XBMC
3) in Video Add-on, select Install from .zip

Before starting the add-on for the first time, either "Configure" or right click and select "Add-on Settings".  Enter your fully-qualified Username (including @gmail.com or @domain) and Password.

Features and limitations:
- will index videos in your google drive account, sorted by title name
- folders are ignored but the files contained in them are indexed for playback
- only indexes and playback videos; no pictures at this time

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
Sort of.  For now, you should share all your videos from subsquent Google Drive accounts to the main Google Drive account that you use with this add-on.  The shared videos will appear in the index and are viewwable.

3) Does thie add-on support Pictures or other filetypes?
Not at this time.  I had no need for viewing files other then Video, therefore, the initial public release features only the features I have been using.

4) Any limitations?
I've tested the add-on with several Google Drive accounts, including one with over 700 videos.


Roadmap to future releases:
- support for multiple Google Drive accounts
- support for OAUTH
- support for pictures
- support for caching account contents
- support for folders and pagination (crucial for accounts with thousands of videos)
