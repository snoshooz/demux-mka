from audio_separator.separator import Separator
from PIL import Image
import os, requests, scrapetube_fixed, shutil, subprocess
import download, targets

def extract_song_info(song: dict):
	if not isinstance(song, dict):
		return None, None

	video_id = None
	title = None

	if "contentId" in song:
		video_id = song["contentId"]
		title = (
			song.get("metadata", {})
			.get("lockupMetadataViewModel", {})
			.get("title", {})
			.get("content")
		)
	elif "videoId" in song:
		video_id = song.get("videoId")
		title_obj = song.get("title", {})
		if isinstance(title_obj, dict):
			if "runs" in title_obj and title_obj["runs"]:
				title = title_obj["runs"][0].get("text")
			elif "simpleText" in title_obj:
				title = title_obj["simpleText"]
		elif isinstance(title_obj, str):
			title = title_obj
	
	if not video_id:
		command_context = (
			song.get("rendererContext", {})
			.get("commandContext", {})
			.get("onTap", {})
			.get("innertubeCommand", {})
		)
		watch_ep = command_context.get("watchEndpoint", {})
		video_id = watch_ep.get("videoId")

	if not video_id or not isinstance(video_id, str):
		return None, None

	if not title or not isinstance(title, str):
		title = f"Track_{video_id}"

	return video_id, title

def separate(source):
	outputDir = f"{source}_stems"
	separator = Separator(output_dir=outputDir)
	separator.load_model("htdemucs_ft.yaml")
	separator.separate(source, {
		"Vocals": "vocals",
		"Drums": "drums",
		"Bass": "bass",
		"other": "other",
	})

	cmd = ["ffmpeg", "-y"]

	for stem in os.listdir(outputDir):
		cmd.extend(["-i", f"{outputDir}/{stem}"])

	for idx in range(len(os.listdir(outputDir))):
		cmd.extend(["-map", f"{idx}:a"])

	cmd.extend(["-c:a", "copy"])

	for idx, stem in enumerate(os.listdir(outputDir)):
		cmd.extend([f"-metadata:s:a:{idx}", f"title={os.path.splitext(stem)[0]}"])

	output = f"{os.path.splitext(source)[0]}.mka"
	cmd.append(output)
	subprocess.run(cmd, text=True)

	os.remove(source)
	shutil.rmtree(outputDir)
	
	return output

def tag(source, tags):
	os.rename(source, f"{source}_")
	cmd = ["ffmpeg", "-y", "-i", f"{source}_"]
	cmd.extend(["-map", "0"])

	cmd.extend([
		"-attach", tags["art"],
		"-metadata:s:t", "mimetype=image/png",
		"-metadata:s:t", "filename=cover.png",
	])

	if tags["title"]:
		cmd.extend(["-metadata", f"title={tags['title']}"])
	if tags["artist"]:
		cmd.extend(["-metadata", f"artist={tags['artist']}"])
	if tags["album"]:
		cmd.extend(["-metadata", f"album={tags['album']}"])
	if tags["year"]:
		cmd.extend(["-metadata", f"date={tags['year']}"])
	if tags["track"]:
		cmd.extend(["-metadata", f"track={tags['track']}"])
	if tags["url"]:
		cmd.extend(["-metadata", f"PURL={tags['url']}"])

	cmd.extend(["-c", "copy", source])
	subprocess.run(cmd, text=True)

	os.remove(f"{source}_")

def retrieveArt(url):
	tempArt = ".temp_art"
	if os.path.exists(url):
		art = Image.open(url)
	else:
		response = requests.get(url)
		response.raise_for_status()
		with open(tempArt, "wb") as fp:
			fp.write(response.content)
		art = Image.open(tempArt)
	art.thumbnail((512, 512))
	art.save(tempArt, "PNG")
	return tempArt

if __name__ == "__main__":
	for playlist in targets.album_playlist:
		if not playlist["url"]: continue

		artPath = retrieveArt(playlist["art"])

		playlist_id = download.extractId(playlist["url"])
		destination = f"output/albums/{playlist['artist']}/{playlist['album']}"
		for s, song in enumerate(scrapetube_fixed.get_playlist(playlist_id)):
			video_id, title = extract_song_info(song)
			if not video_id: continue

			output = download.downloadAudio(
				f"https://www.youtube.com/watch?v={video_id}",
				destination,
				f"{s+1} _ {title}",
			)
			output = separate(output)
			tag(output, {
				"title": title,
				"artist": playlist["artist"],
				"album": playlist["album"],
				"year": playlist["year"],
				"art": artPath,
				"track": s + 1,
				"url": download.formatURL(f"{download.BASE_URL}/watch?v={video_id}"),
			})
	
	for built in targets.album_built:
		if not built["artist"]: continue

		artPath = retrieveArt(built["art"])

		destination = f"output/albums/{built['artist']}/{built['album']}"
		for s, song in enumerate(built["songs"]):
			output = download.downloadAudio(
				song["url"],
				destination,
				f"{s+1} _ {song['title']}",
			)

			output = separate(output)
			tag(output, {
				"title": song["title"],
				"artist": built["artist"],
				"album": built["album"],
				"year": built["year"],
				"art": artPath,
				"track": s+1,
				"url": download.formatURL(song["url"]),
			})