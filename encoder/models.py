from django.db import models


class EncodingProfile(models.Model):
    MODE_CHOICES = [("film", "Film"), ("serie", "Serie")]
    CODEC_CHOICES = [("x265", "x265"), ("x264", "x264"), ("av1", "AV1")]
    AUDIO_CHOICES = [("copy", "Copy"), ("aac", "AAC"), ("ac3", "AC3")]
    RESOLUTION_CHOICES = [
        ("source", "Same as source"),
        ("1080p", "1080p"),
        ("720p", "720p"),
    ]

    name = models.CharField(max_length=100)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES)
    video_codec = models.CharField(max_length=10, choices=CODEC_CHOICES, default="x265")
    quality_crf = models.IntegerField(default=24)
    encoder_preset = models.CharField(max_length=20, default="medium")
    resolution = models.CharField(max_length=10, choices=RESOLUTION_CHOICES, default="source")
    audio_mode = models.CharField(max_length=10, choices=AUDIO_CHOICES, default="copy")
    container = models.CharField(max_length=10, default="mkv")
    subtitle_default_lang = models.CharField(max_length=10, default="dan")
    burn_forced_subs = models.BooleanField(default=False)
    soft_subs = models.BooleanField(default=True)
    skip_existing = models.BooleanField(default=True)
    keep_folder_structure = models.BooleanField(default=True)
    delete_source = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_mode_display()})"


class ScanSession(models.Model):
    MODE_CHOICES = [("film", "Film"), ("serie", "Serie")]

    source_path = models.CharField(max_length=500)
    output_path = models.CharField(max_length=500)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES)
    scanned_at = models.DateTimeField(auto_now_add=True)
    profile = models.ForeignKey(
        EncodingProfile, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"Scan {self.id}: {self.source_path} ({self.mode})"


class VideoFile(models.Model):
    session = models.ForeignKey(
        ScanSession, on_delete=models.CASCADE, related_name="videos"
    )
    path = models.CharField(max_length=500)
    filename = models.CharField(max_length=255)
    size_bytes = models.BigIntegerField()
    duration_seconds = models.IntegerField(null=True, blank=True)
    codec = models.CharField(max_length=50, null=True, blank=True)
    resolution = models.CharField(max_length=20, null=True, blank=True)
    series_title = models.CharField(max_length=255, null=True, blank=True)
    season = models.IntegerField(null=True, blank=True)
    episode = models.IntegerField(null=True, blank=True)
    episode_title = models.CharField(max_length=255, null=True, blank=True)
    selected = models.BooleanField(default=True)

    def __str__(self):
        return self.filename


class SubtitleFile(models.Model):
    CONFIDENCE_CHOICES = [("high", "High"), ("medium", "Medium"), ("low", "Low")]

    video = models.ForeignKey(
        VideoFile, on_delete=models.CASCADE, related_name="subtitles"
    )
    path = models.CharField(max_length=500)
    filename = models.CharField(max_length=255)
    language = models.CharField(max_length=10)
    language_display = models.CharField(max_length=20)
    confidence = models.CharField(max_length=10, choices=CONFIDENCE_CHOICES)
    selected = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.filename} ({self.language_display})"


class EncodeJob(models.Model):
    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("encoding", "Encoding"),
        ("remuxing", "Remuxing"),
        ("done", "Done"),
        ("failed", "Failed"),
        ("skipped", "Skipped"),
    ]

    video = models.ForeignKey(VideoFile, on_delete=models.CASCADE)
    profile = models.ForeignKey(
        EncodingProfile, on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="queued")
    progress = models.IntegerField(default=0)
    output_path = models.CharField(max_length=500, null=True, blank=True)
    input_size_bytes = models.BigIntegerField(null=True, blank=True)
    output_size_bytes = models.BigIntegerField(null=True, blank=True)
    handbrake_cmd = models.TextField(null=True, blank=True)
    mkvmerge_cmd = models.TextField(null=True, blank=True)
    log = models.TextField(default="")
    rq_job_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Job {self.id}: {self.video.filename} [{self.status}]"
