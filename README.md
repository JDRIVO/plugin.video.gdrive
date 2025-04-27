## gDrive
A Kodi Add-On for playing videos stored on Google Drive.

## Obtaining Client ID & Client Secret
https://console.cloud.google.com/apis/library/drive.googleapis.com

https://github.com/user-attachments/assets/d9ee3658-76b0-435a-bddd-3f4631fdf19a

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
