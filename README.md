## gDrive
A Kodi Add-On for playing videos stored on Google Drive.

## Obtaining Client ID & Client Secret
https://console.cloud.google.com/apis/library/drive.googleapis.com

https://github.com/user-attachments/assets/b3d0e86f-2597-40c8-8485-6d11ad085372

## File & Folder Renaming
### <table><tr><td>Movie</td></tr></table>
| Rename videos to a Kodi friendly format | Create a Kodi friendly directory structure | Output |
| :-------------------------------------: | :----------------------------------------: | ------ |
| ❌ | ❌ | Deadpool.2016.1080p.DTS-HD.MA.5.1.x264.strm                                        |
| ✔️ | ❌ | Deadpool (2016).strm                                                               |
| ❌ | ✔️ | Deadpool (2016)/Deadpool.2016.1080p.DTS-HD.MA.5.1.x264.strm                        |
| ✔️ | ✔️ | Deadpool (2016)/Deadpool (2016).strm                                               |
### <table><tr><td>Episode</td></tr></table>
| Rename videos to a Kodi friendly format | Create a Kodi friendly directory structure | Output |
| :-------------------------------------: | :----------------------------------------: | ------ |
| ❌ | ❌ | Breaking.Bad.S01E01.1080p.DTS-HD.MA.5.1.AVC.strm                                   |
| ✔️ | ❌ | Breaking Bad S01E01.strm                                                           |
| ❌ | ✔️ | Breaking Bad (2008)/Season 1/Breaking.Bad.S01E01.1080p.DTS-HD.MA.5.1.AVC.strm      |
| ✔️ | ✔️ | Breaking Bad (2008)/Season 1/Breaking Bad S01E01.strm                              |
