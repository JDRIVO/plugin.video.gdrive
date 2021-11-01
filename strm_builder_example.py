# To be ran by the script that uploads files to Google Drive. Sync strms with resilio, syncthing etc. Install watchdog on Kodi.

import sys
import json
import shlex
import subprocess

videoPath = sys.argv[1]
encryptedFilePath = sys.argv[2]
strmPath = sys.argv[3]

# videoPath = '/home/jack/movies/best movie 2000.mkv'
# encryptedFilePath = 'remote:/folder/RrtgFuvcxsWfKuFgGJ34VvcgfGFGWEWet'
# strmPath = '/home/jack/strm/movies/best movie 2000.strm'

cmd = 'ffprobe -v quiet -print_format json -show_format -show_streams'
args = shlex.split(cmd)
args.append(videoPath)
ffprobeOutput = subprocess.check_output(args).decode('utf-8')
ffprobeOutput = json.loads(ffprobeOutput)

videoDuration = str(ffprobeOutput['format']['duration'])

for dic in ffprobeOutput['streams']:

	if dic['codec_type'] == 'video':
		videoCodec = dic['codec_name']
		videoWidth = dic['width']
		videoHeight = dic['height']
		aspectRatio = str(videoWidth / videoHeight)
		videoWidth = str(videoWidth)
		videoHeight = str(videoHeight)
	elif dic['codec_type'] == 'audio':
		audioCodec = dic['codec_name']
		audioChannels = dic['channels']

cmd = 'rclone lsf --format i'
args = shlex.split(cmd)
args.append(encryptedFilePath)
fileID = subprocess.check_output(args).strip().decode('utf-8')

with open(strmPath, 'w+') as strm:
	# Every paramater is optional besides the filename (Google Drive File ID) - essential strm format is:
	# plugin://plugin.video.gdrive/?mode=video&encfs=True&filename=7ctPNMUl4m8B4KBwY
	strm.write("plugin://plugin.video.gdrive/?mode=video&encfs=True&video_codec=%s&video_width=%s&video_height=%s&video_duration=%s&aspect_ratio=%s&audio_codec=%s&audio_channels=%s&filename=%s" % (videoCodec, videoWidth, videoHeight, videoDuration, aspectRatio, audioCodec, audioChannels, fileID))
