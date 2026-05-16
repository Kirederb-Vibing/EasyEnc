import os
import re
from difflib import SequenceMatcher

import guessit

from encoder.models import SubtitleFile

# Language code mapping
LANGUAGE_MAP = {
    "da": ("dan", "Dansk"),
    "dk": ("dan", "Dansk"),
    "dan": ("dan", "Dansk"),
    "dansk": ("dan", "Dansk"),
    "en": ("eng", "English"),
    "eng": ("eng", "English"),
    "english": ("eng", "English"),
    "de": ("deu", "Tysk"),
    "ger": ("deu", "Tysk"),
    "german": ("deu", "Tysk"),
    "deu": ("deu", "Tysk"),
    "fr": ("fra", "Fransk"),
    "fre": ("fra", "Fransk"),
    "french": ("fra", "Fransk"),
    "fra": ("fra", "Fransk"),
}


def detect_language(filename):
    """Detect subtitle language from filename patterns."""
    stem = os.path.splitext(filename)[0]

    # Check for language codes in the filename (e.g., Movie.da.srt, Movie.eng.srt)
    parts = stem.split(".")
    for part in reversed(parts):
        lower = part.lower()
        if lower in LANGUAGE_MAP:
            return LANGUAGE_MAP[lower]

    # Check for language in brackets or parentheses
    pattern = r"[\[\(](\w+)[\]\)]"
    matches = re.findall(pattern, stem)
    for match in matches:
        lower = match.lower()
        if lower in LANGUAGE_MAP:
            return LANGUAGE_MAP[lower]

    return ("und", "Ukendt")


def fuzzy_match(str1, str2, threshold=0.8):
    """Return True if two strings have a similarity ratio above threshold."""
    ratio = SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    return ratio >= threshold


def match_subtitles(video_objects, subtitle_files):
    """
    Match subtitle files to video files using a three-tier confidence approach.
    Creates SubtitleFile records for each match.
    """
    # Unmatched subtitles (track which ones we've already assigned)
    unmatched = list(subtitle_files)

    for video in video_objects:
        video_dir = os.path.dirname(video.path)
        video_stem = os.path.splitext(video.filename)[0]
        video_guess = guessit.guessit(video.filename)
        video_title = video_guess.get("title", "")

        matched_subs = []

        for sub_path, sub_filename in unmatched[:]:
            sub_dir = os.path.dirname(sub_path)
            sub_stem = os.path.splitext(sub_filename)[0]
            # Remove language suffix for comparison (e.g., "Movie.da" -> "Movie")
            sub_stem_base = sub_stem.rsplit(".", 1)[0] if "." in sub_stem else sub_stem

            language, language_display = detect_language(sub_filename)
            confidence = None

            # HIGH confidence: same directory + filename matches (minus lang code)
            if sub_dir == video_dir:
                if sub_stem_base.lower() == video_stem.lower():
                    confidence = "high"
                else:
                    # Check guessit match (same title + season + episode)
                    sub_guess = guessit.guessit(sub_filename)
                    if (
                        sub_guess.get("title", "").lower() == video_title.lower()
                        and video_title
                    ):
                        if video.season is not None and video.episode is not None:
                            if (
                                sub_guess.get("season") == video.season
                                and sub_guess.get("episode") == video.episode
                            ):
                                confidence = "high"
                        else:
                            confidence = "high"

            # MEDIUM confidence: same directory with fuzzy title match
            if confidence is None and sub_dir == video_dir:
                if video_title and fuzzy_match(sub_stem, video_title):
                    confidence = "medium"
                elif fuzzy_match(sub_stem_base, video_stem):
                    confidence = "medium"

            # LOW confidence: same directory but no clear name relation
            if confidence is None and sub_dir == video_dir:
                confidence = "low"

            if confidence:
                matched_subs.append(
                    (sub_path, sub_filename, language, language_display, confidence)
                )
                unmatched.remove((sub_path, sub_filename))

        # Create SubtitleFile records
        for sub_path, sub_filename, language, language_display, confidence in matched_subs:
            SubtitleFile.objects.create(
                video=video,
                path=sub_path,
                filename=sub_filename,
                language=language,
                language_display=language_display,
                confidence=confidence,
                selected=(confidence != "low"),
            )
