from django.contrib import admin

from .models import EncodeJob, EncodingProfile, ScanSession, SubtitleFile, VideoFile

admin.site.register(EncodingProfile)
admin.site.register(ScanSession)
admin.site.register(VideoFile)
admin.site.register(SubtitleFile)
admin.site.register(EncodeJob)
