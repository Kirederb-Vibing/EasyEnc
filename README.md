# EasyEnc

A local web service for batch encoding video files with automatic subtitle matching. Uses HandBrakeCLI for encoding and mkvmerge for subtitle embedding.

## Features

- Recursive directory scanning for video and subtitle files
- Automatic subtitle matching with confidence levels (high/medium/low)
- Film and series mode with guessit-based filename parsing
- Configurable encoding profiles (codec, CRF, preset, resolution, audio)
- Live encoding queue with progress tracking (HTMX polling)
- Soft subtitle embedding with language detection
- Docker-ready with single-command deployment

## Tech Stack

- **Backend:** Django 5.x + SQLite
- **Job Queue:** RQ (Redis Queue)
- **Frontend:** HTMX + Alpine.js + Tailwind CSS (CDN)
- **Encoding:** HandBrakeCLI + mkvmerge (MKVToolNix) + ffprobe

## Quick Start (Docker)

```bash
git clone https://github.com/<username>/EasyEnc.git
cd EasyEnc
cp .env.example .env
```

Edit `.env` with your paths:

```env
DJANGO_SECRET_KEY=your-random-secret-key
MEDIA_SOURCE=/path/to/your/media
MEDIA_OUTPUT=/path/to/output
```

Start all services:

```bash
docker-compose up -d
```

Open http://localhost:8000

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
