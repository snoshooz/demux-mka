from yt_dlp import YoutubeDL
import pydub, urllib

BASE_URL = "https://www.youtube.com"

ytdl_opts = {
	"nocheckcertificate": True,
	"cookiesfrombrowser": ("firefox",),
}

def formatURL(url):
	urlInfo = urllib.parse.urlsplit(url)
	params = urllib.parse.parse_qs(urlInfo.query)

	if urlInfo.path == "/watch":
		return f"{BASE_URL}/watch?v={params['v'][0]}"
	elif urlInfo.path == "/playlist":
		return f"{BASE_URL}/playlist?list={params['list'][0]}"
	elif urlInfo.path.startswith("/channel/"):
		return f"{BASE_URL}{urlInfo.path}"

def extractId(url):
	urlInfo = urllib.parse.urlsplit(formatURL(url))
	params = urllib.parse.parse_qs(urlInfo.query)

	if urlInfo.path == "/watch":
		return params["v"][0]
	elif urlInfo.path == "/playlist":
		return params["list"][0]
	elif urlInfo.path.startswith("/channel/"):
		return urlInfo.path

def downloadAudio(url, destination, title=None, quality=192):
	url = formatURL(url)
	if title: opts = ytdl_opts | {"outtmpl": {"default": title}}
	else: opts = ytdl_opts
	ytdl = YoutubeDL(opts | {
		"paths": {"home": destination},
		"format": "bestaudio/best",
		"postprocessors": [{
			"key": "FFmpegExtractAudio",
			"preferredcodec": "mp3",
			"preferredquality": str(quality),
		}]
	})
	ytdl.download([url])

	output = (ytdl.extract_info(url)["requested_downloads"][0]["filepath"])

	newTrack = pydub.AudioSegment.from_file(output, format="mp3")
	newTrack -= newTrack.max_dBFS
	newTrack.export(output, format="mp3")

	return output