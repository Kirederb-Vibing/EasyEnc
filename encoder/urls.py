from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("scan/", views.scan, name="scan"),
    path("session/<int:session_id>/", views.session_detail, name="session_detail"),
    path("session/<int:session_id>/update/", views.session_update_selection, name="session_update"),
]
