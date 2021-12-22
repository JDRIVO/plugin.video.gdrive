# To be ran by the script that uploads files to Google Drive. Sync strms with resilio, syncthing etc. Install watchdog on Kodi.

import sys
import json
import shlex
import subprocess

videoPath = sys.argv[1]
encryptedFilePath = sys.argv[2]
strmPath = sys.argv[3]

# videoPath = "/home/jack/movies/best movie 2000.mkv"
# encryptedFilePath = "remote:/folder/RrtgFuvcxsWfKuFgGJ34VvcgfGFGWEWet"
# strmPath = "/home/jack/strm/movies/best movie 2000.strm"

cmd = "ffprobe -v quiet -print_format json -show_format -show_streams"
args = shlex.split(cmd)
args.append(videoPath)
ffprobeOutput = subprocess.check_output(args).decode("utf-8")
ffprobeOutput = json.loads(ffprobeOutput)

mediaInfo = {}
mediaInfo["video_duration"] = ffprobeOutput["format"]["duration"]
video = audio = False

for dic in ffprobeOutput["streams"]:
	codecType = dic["codec_type"]

	if codecType == "video" and not video:
		video = True
		colourTransfer = dic.get("color_transfer")

		if colourTransfer:

			if colourTransfer in ("smpte2084", "smpte2086"):
				mediaInfo["hdr"] = "hdr10"
			elif colourTransfer == "arib-std-b67":
				mediaInfo["hdr"] = "hlg"

		else:

			if dic.get("codec_tag_string") == "dvhe":
				mediaInfo["hdr"] = "dolbyvision"

		mediaInfo["video_codec"] = dic["codec_name"]
		mediaInfo["video_width"] = dic["width"]
		mediaInfo["video_height"] = dic["height"]
		mediaInfo["aspect_ratio"] = mediaInfo["video_width"] / mediaInfo["video_height"]

	elif codecType == "audio" and not audio:
		audio = True
		mediaInfo["audio_codec"] = dic["codec_name"]
		mediaInfo["audio_channels"] = dic["channels"]

cmd = "rclone lsf --format i"
args = shlex.split(cmd)
args.append(encryptedFilePath)
fileID = subprocess.check_output(args).strip().decode("utf-8")
mediaInfo["filename"] = fileID

with open(strmPath, "w+") as strm:
	# Every paramater is optional besides the filename (Google Drive File ID) - essential strm format is:
	# plugin://plugin.video.gdrive/?mode=video&encfs=True&filename=7ctPNMUl4m8B4KBwY
	url = "plugin://plugin.video.gdrive/?mode=video&encfs=True" + "".join(["&{}={}".format(k, v) for k, v in mediaInfo.items()])
	strm.write(url)
