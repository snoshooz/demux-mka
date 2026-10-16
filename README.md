# demux-mka

An automated audio ingest, deep-learning stem separation, and containerization pipeline.

This tool ingests YouTube playlists or custom tracklists, normalizes track peak audio headroom, splits tracks into 4 distinct stems using the HTDemucs model via `audio-separator`, and multiplexes all separated streams into a single multi-track Matroska (`.mka`) container with embedded metadata and album artwork.

---

## Features

- **Automated Ingestion**: Scrapes and downloads full playlists or custom track lists using `scrapetube` and `yt-dlp`.
- **Peak Dynamic Normalization**: Normalizes downloaded audio to 0 dBFS peak headroom using `pydub` prior to processing.
- **Deep-Learning Stem Separation**: Isolates tracks into 4 constituent stems (Vocals, Drums, Bass, Other) using the `htdemucs_ft` model.
- **Multi-Track MKA Packaging**: Merges stem outputs into a single `.mka` file using stream copy mode (`-c:a copy`), avoiding re-encoding degradation.
- **Rich Metadata & Cover Art**: Injects track titles, artist, album, release year, stream titles, original URL, and resized embedded cover art attachments (`cover.png`) into container headers.

---

## Prerequisites

Ensure the following system packages and external binaries are installed and accessible on your `PATH`:

- **Python 3.10+**
- **FFmpeg** (with Matroska muxing and MP3/image extraction support)
- **Firefox** (or an active session with valid cookies for `yt-dlp` extraction)

---

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/snoshooz/demux-mka.git
   cd demux-mka
   ```
2. Generate and activate the conda environment:

   ```bash
   conda create -f environment.yaml
   conda activate demux-mka
   ```

---

## Configuration

Targets are defined inside `targets.py`. You can configure either full album playlists or manually defined tracklists:

```python
# targets.py

# Download and parse an entire YouTube playlist
album_playlist = [
    {
        "artist": "Artist Name",
        "album": "Album Name",
        "year": 2024,
        "url": "https://www.youtube.com/playlist?list=PLAYLIST_ID",
        "art": "https://example.com/cover.jpg",
    },
]

# Process manually curated tracks
album_built = [
    {
        "artist": "Artist Name",
        "album": "Compilation Album",
        "year": 2024,
        "art": "assets/cover.png",
        "songs": [
            {"title": "Track One", "url": "https://www.youtube.com/watch?v=VIDEO_ID_1"},
            {"title": "Track Two", "url": "https://www.youtube.com/watch?v=VIDEO_ID_2"},
        ],
    }
]
```

---

## Usage

Run the primary pipeline script:

```bash
python main.py
```

### Pipeline Flow

1. **Cover Art Preparation**: Fetches remote art, resizing them to `512x512` PNG thumbnails.
2. **Download & Normalize**: Downloads high-quality MP3 audio via `download.py`, applies peak normalization, and writes to `output/albums/<Artist>/<Album>/`.
3. **Stem Splitting**: Runs HTDemucs model (`htdemucs_ft.yaml`) to output 4 audio stems into a temporary folder.
4. **MKA Multiplexing**: FFmpeg maps every audio stem as an independent stream (`-map <idx>:a`) and tags stream titles accordingly.
5. **Tagging & Cleanup**: Injects global container metadata, attaches cover art, removes intermediate stems, and cleans up raw MP3 files.

---

## Output Structure

Completed containers are organized by artist and album hierarchy:

```text
output/
└── albums/
    └── <Artist>/
        └── <Album>/
            ├── 1 _ Track One.mka
            ├── 2 _ Track Two.mka
            └── ...
```

Each generated `.mka` file contains:

- `Stream 0`: Vocals
- `Stream 1`: Drums
- `Stream 2`: Bass
- `Stream 3`: Other
- `Attachment`: `cover.png` (`image/png`)

---

## Verification & Execution Checklist

1. Verify FFmpeg installation and PATH registration by running `ffmpeg -version`.
2. Ensure Firefox profile cookies exist locally for `yt-dlp` browser cookie extraction.
3. Define at least one target inside `targets.album_playlist` or `targets.album_built`.
4. Execute `python main.py` and inspect stream mapping using:
   ```bash
   ffprobe output/albums/<Artist>/<Album>/<Track>.mka
   ```
