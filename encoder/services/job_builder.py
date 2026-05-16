import os

from encoder.models import EncodeJob, EncodingProfile, VideoFile


def build_handbrake_cmd(video, profile, tmp_output):
    """Build the HandBrakeCLI command string."""
    cmd_parts = [
        "HandBrakeCLI",
        "-i", video.path,
        "-o", tmp_output,
        "--encoder", profile.video_codec,
        "--quality", str(profile.quality_crf),
        "--encoder-preset", profile.encoder_preset,
    ]

    # Resolution scaling
    if profile.resolution == "1080p":
        cmd_parts.extend(["--maxWidth", "1920", "--maxHeight", "1080"])
    elif profile.resolution == "720p":
        cmd_parts.extend(["--maxWidth", "1280", "--maxHeight", "720"])

    # Audio
    if profile.audio_mode == "copy":
        cmd_parts.extend(["--aencoder", "copy"])
    elif profile.audio_mode == "aac":
        cmd_parts.extend(["--aencoder", "av_aac", "--ab", "192"])
    elif profile.audio_mode == "ac3":
        cmd_parts.extend(["--aencoder", "ac3", "--ab", "640"])

    # Markers
    cmd_parts.append("--markers")

    return " ".join(cmd_parts)


def build_mkvmerge_cmd(tmp_output, subtitles, final_output, default_lang):
    """Build the mkvmerge command string for embedding subtitles."""
    cmd_parts = [
        "mkvmerge",
        "-o", final_output,
        tmp_output,
    ]

    for sub in subtitles:
        cmd_parts.extend([
            "--language", f"0:{sub.language}",
            "--track-name", f"0:{sub.language_display}",
        ])
        if sub.language == default_lang:
            cmd_parts.extend(["--default-track", "0:yes"])
        else:
            cmd_parts.extend(["--default-track", "0:no"])
        cmd_parts.append(sub.path)

    return " ".join(cmd_parts)


def compute_output_path(video, session, profile):
    """Compute the final output path for an encoded file."""
    output_base = session.output_path

    if profile and profile.keep_folder_structure:
        # Preserve relative path from source
        rel_path = os.path.relpath(video.path, session.source_path)
        output_path = os.path.join(output_base, rel_path)
    else:
        output_path = os.path.join(output_base, video.filename)

    # Change extension to target container
    container = profile.container if profile else "mkv"
    stem = os.path.splitext(output_path)[0]
    return f"{stem}.{container}"


def build_job(video, profile):
    """Create an EncodeJob with HandBrake and mkvmerge commands."""
    session = video.session
    final_output = compute_output_path(video, session, profile)

    # Temporary file for HandBrake output (before muxing subtitles)
    tmp_output = os.path.splitext(final_output)[0] + ".tmp.mkv"

    handbrake_cmd = build_handbrake_cmd(video, profile, tmp_output)

    # Get selected subtitles
    selected_subs = list(video.subtitles.filter(selected=True))
    mkvmerge_cmd = None
    if selected_subs and profile and profile.soft_subs:
        mkvmerge_cmd = build_mkvmerge_cmd(
            tmp_output, selected_subs, final_output, profile.subtitle_default_lang
        )

    job = EncodeJob.objects.create(
        video=video,
        profile=profile,
        status="queued",
        output_path=final_output,
        input_size_bytes=video.size_bytes,
        handbrake_cmd=handbrake_cmd,
        mkvmerge_cmd=mkvmerge_cmd,
    )

    return job
