# To be ran by the script that uploads files to Google Drive. Sync strms with resilio, syncthing etc. Install watchdog on Kodi.

import os
import re
import sys
import json
import shlex
import subprocess

videoPath = sys.argv[1]
remoteVideoPath = sys.argv[2]
strmPath = sys.argv[3]
driveID = sys.argv[4] # Optional - if not specified you will need to set a default playback account in the addon settings
encrypted = sys.argv[5] == "True"

# videoPath = "/home/jack/movies/best movie 2000.mkv"
# remoteVideoPath = "remote:/folder/RrtgFuvcxsWfKuFgGJ34VvcgfGFGWEWet"
# strmPath = "/home/jack/strm/movies/best movie 2000.strm"
# driveID = "0AGHbAfUtSfVATg4F5B" or ""
# encrypted = False

cmd = "ffprobe -v quiet -print_format json -show_format -show_streams"
args = shlex.split(cmd)
args.append(videoPath)
ffprobeOutput = subprocess.check_output(args).decode("utf-8")
ffprobeOutput = json.loads(ffprobeOutput)

strmData = {}
strmData["video_duration"] = ffprobeOutput["format"]["duration"]
video = audio = False

for data in ffprobeOutput["streams"]:
	codecType = data.get("codec_type")

	if codecType == "video":

		if strmData.get("hdr") == "dolbyvision":
			continue

		codecTag = data.get("codec_tag_string")
		colourTransfer = data.get("color_transfer")
		sideData = data.get("side_data_list")

		if codecTag in ("dva1", "dvav", "dvh1", "dvhe"):
			strmData["hdr"] = "dolbyvision"
			codecs = {"dva1": "h264", "dvav": "h264", "dvh1": "hevc", "dvhe": "hevc"}
			strmData["video_codec"] = codecs[codecTag]
		elif sideData and "dv_profile" in str(sideData):
			strmData["hdr"] = "dolbyvision"
		elif colourTransfer in ("smpte2084", "smpte2086", "smpte2094"):
			strmData["hdr"] = "hdr10"
		elif colourTransfer == "arib-std-b67":
			strmData["hdr"] = "hlg"

		if video:
			continue

		video = True
		videoCodec = data.get("codec_name")
		videoWidth = data.get("width")
		videoHeight = data.get("height")

		if videoCodec and not strmData.get("video_codec"):
			strmData["video_codec"] = videoCodec

		if videoWidth:
			strmData["video_width"] = videoWidth

		if videoHeight:
			strmData["video_height"] = videoHeight

		if videoWidth and videoHeight:
			strmData["aspect_ratio"] = videoWidth / videoHeight

	elif codecType == "audio" and not audio:
		audio = True
		audioCodec = data.get("codec_name")
		audioChannels = data.get("channels")

		if audioCodec:
			strmData["audio_codec"] = audioCodec

		if audioChannels:
			strmData["audio_channels"] = audioChannels

filename = os.path.basename(videoPath)

if re.search("[-_. ](dv|dovi|dolby[-_. ]*vision)[-_. ]", filename, re.IGNORECASE):
	strmData["hdr"] = "dolbyvision"
elif not strmData.get("hdr") and re.search("hdr10", filename, re.IGNORECASE):
	strmData["hdr"] = "hdr10"

if encrypted:
	strmData["encrypted"] = True

if driveID:
	strmData["drive_id"] = driveID

cmd = "rclone lsf --format i"
args = shlex.split(cmd)
args.append(remoteVideoPath)
fileID = subprocess.check_output(args).strip().decode("utf-8")
strmData["file_id"] = fileID

with open(strmPath, "w+") as strm:

	# Essential strm format for unencrypted videos:
	# plugin://plugin.video.gdrive/?mode=video&file_id=7ctPNMUl4m8B4KBwY

	# Essential strm format for encrypted videos:
	# plugin://plugin.video.gdrive/?mode=video&encrypted=True&file_id=7ctPNMUl4m8B4KBwY

	url = "plugin://plugin.video.gdrive/?mode=video"
	url += "".join("&{}={}".format(k, v) for k, v in strmData.items())
	strm.write(url)
