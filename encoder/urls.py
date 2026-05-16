from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("scan/", views.scan, name="scan"),
    path("session/<int:session_id>/", views.session_detail, name="session_detail"),
    path("session/<int:session_id>/update/", views.session_update_selection, name="session_update"),
    path("session/<int:session_id>/enqueue/", views.session_enqueue, name="session_enqueue"),
    path("queue/", views.queue, name="queue"),
    path("queue/status/", views.queue_status, name="queue_status"),
    path("job/<int:job_id>/log/", views.job_log, name="job_log"),
]
