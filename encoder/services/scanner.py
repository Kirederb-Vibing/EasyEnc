import json
import os
import subprocess

import guessit

from encoder.models import ScanSession, SubtitleFile, VideoFile

from .matcher import match_subtitles

VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".mov", ".m4v", ".ts"}
SUBTITLE_EXTENSIONS = {".srt", ".ass", ".ssa", ".vtt"}


def probe_video(filepath):
    """Run ffprobe on a video file and return stream info."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                filepath,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        pass
    return None


def parse_probe_data(probe_data):
    """Extract codec, resolution, and duration from ffprobe output."""
    codec = None
    resolution = None
    duration = None

    if not probe_data or "streams" not in probe_data:
        return codec, resolution, duration

    for stream in probe_data["streams"]:
        if stream.get("codec_type") == "video":
            codec = stream.get("codec_name")
            width = stream.get("width")
            height = stream.get("height")
            if width and height:
                resolution = f"{width}x{height}"
            dur = stream.get("duration")
            if dur:
                try:
                    duration = int(float(dur))
                except (ValueError, TypeError):
                    pass
            break

    # Try container-level duration if stream didn't have it
    if duration is None and probe_data.get("streams"):
        for stream in probe_data["streams"]:
            dur = stream.get("duration")
            if dur:
                try:
                    duration = int(float(dur))
                    break
                except (ValueError, TypeError):
                    pass

    return codec, resolution, duration


def scan_directory(source_path, output_path, mode, profile=None):
    """
    Recursively scan a directory for video and subtitle files.
    Returns the created ScanSession.
    """
    session = ScanSession.objects.create(
        source_path=source_path,
        output_path=output_path,
        mode=mode,
        profile=profile,
    )

    video_files = []
    subtitle_files = []

    for dirpath, _dirnames, filenames in os.walk(source_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            ext = os.path.splitext(filename)[1].lower()

            if ext in VIDEO_EXTENSIONS:
                video_files.append((filepath, filename))
            elif ext in SUBTITLE_EXTENSIONS:
                subtitle_files.append((filepath, filename))

    # Create VideoFile records
    video_objects = []
    for filepath, filename in video_files:
        size = os.path.getsize(filepath)

        # Probe video for metadata
        probe_data = probe_video(filepath)
        codec, resolution, duration = parse_probe_data(probe_data)

        # Parse filename with guessit
        guess = guessit.guessit(filename)

        video = VideoFile.objects.create(
            session=session,
            path=filepath,
            filename=filename,
            size_bytes=size,
            duration_seconds=duration,
            codec=codec,
            resolution=resolution,
            series_title=guess.get("title") if mode == "serie" else None,
            season=guess.get("season") if mode == "serie" else None,
            episode=guess.get("episode") if mode == "serie" else None,
            episode_title=guess.get("episode_title") if mode == "serie" else None,
        )
        video_objects.append(video)

    # Match subtitles to videos
    match_subtitles(video_objects, subtitle_files)

    return session
