# EasyEnc

A local web service for batch encoding video files with automatic subtitle matching. Uses HandBrakeCLI for encoding and mkvmerge for subtitle embedding.

## Features

- **GUI directory picker** — browse and select folders directly in the web interface
- **PUID/PGID support** — files are written with the permissions of the user you specify
- **Configurable access** — restrict which directories the service can see via `ALLOWED_DIRS`
- Recursive directory scanning for video and subtitle files
- Automatic subtitle matching with confidence levels (high/medium/low)
- Film and series mode with guessit-based filename parsing
- Configurable encoding profiles (codec, CRF, preset, resolution, audio)
- Live encoding queue with progress tracking (HTMX polling)
- Soft subtitle embedding with language detection
- Pre-built Docker image from GitHub Container Registry (no local build needed)

## Tech Stack

- **Backend:** Django 5.x + SQLite
- **Job Queue:** RQ (Redis Queue)
- **Frontend:** HTMX + Alpine.js + Tailwind CSS (CDN)
- **Encoding:** HandBrakeCLI + mkvmerge (MKVToolNix) + ffprobe

## Quick Start (Docker)

The image is published to GitHub Container Registry. No build required.

```bash
git clone https://github.com/Kirederb-Vibing/EasyEnc.git
cd EasyEnc
cp .env.example .env
```

Edit `.env`:

```env
DJANGO_SECRET_KEY=your-random-secret-key

# File permissions — set to match the owner of your media files
# 0:0 = root, 1000:1000 = typical first user
PUID=1000
PGID=1000

# Which directories the GUI can browse (comma-separated)
ALLOWED_DIRS=/mnt/media,/mnt/output

# Host paths to mount into the container (must cover ALLOWED_DIRS)
MEDIA_PATH_1=/mnt/media
MEDIA_PATH_2=/mnt/output
MEDIA_PATH_3=
```

Start all services:

```bash
docker-compose up -d
```

Open http://localhost:8000

### Permissions

Files are read/written as the user specified by `PUID:PGID`. Set these to match the owner of your media directories so encoded files inherit the correct permissions:

- `PUID=0 PGID=0` — run as root
- `PUID=1000 PGID=1000` — run as UID 1000 (typical first user on most Linux distros)

### Directory Access

The `ALLOWED_DIRS` environment variable controls which directories are visible in the GUI folder picker. Only paths listed here (and their subdirectories) can be browsed or scanned. The corresponding `MEDIA_PATH_*` variables mount these host paths into the container.

## Local Development (without Docker)

### Requirements

- Python 3.10+
- Redis server
- HandBrakeCLI
- mkvtoolnix (mkvmerge)
- ffmpeg (ffprobe)

### Setup

```bash
pip install -r requirements.txt
mkdir -p data

# Run migrations
python manage.py migrate

# Load default encoding profiles
python manage.py loaddata initial_profiles.json

# Start Redis (in a separate terminal)
redis-server

# Start the RQ worker (in a separate terminal)
python manage.py rqworker default

# Start the Django dev server
python manage.py runserver
```

## Usage

1. **Scan:** Enter a source directory path, choose Film or Series mode, optionally select an encoding profile, and click "Start scan"
2. **Select:** Review discovered files and matched subtitles. Deselect any files you don't want to encode
3. **Encode:** Click "Start encoding" to queue all selected files
4. **Monitor:** Watch real-time progress on the Queue page (auto-refreshes every 2 seconds)

## Encoding Profiles

Two default profiles are included:

### Film (default)
- Codec: x265 (HEVC), CRF 22, Preset: slow
- Resolution: Same as source
- Audio: Copy all tracks
- Subtitles: Soft embed, Danish default

### Series (default)
- Codec: x265 (HEVC), CRF 24, Preset: medium
- Resolution: 1080p max
- Audio: AAC stereo
- Subtitles: Soft embed, Danish default

Custom profiles can be created on the Settings page.

## Subtitle Matching

Subtitles are matched to video files using a three-tier confidence system:

- **High:** Filename matches exactly (minus language code), or guessit parses same title+season+episode
- **Medium:** Same directory with fuzzy title match (>80% similarity)
- **Low:** Same directory but no clear name relation (not auto-selected)

Supported subtitle formats: `.srt`, `.ass`, `.ssa`, `.vtt`

## License

MIT
