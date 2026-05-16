import os

import django_rq
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EncodingProfileForm, ScanForm
from .models import EncodeJob, EncodingProfile, ScanSession, VideoFile
from .services.job_builder import build_job
from .services.scanner import scan_directory
from .services.worker import run_encode_job


def _is_path_allowed(path):
    """Check if path is under one of the allowed directories."""
    real = os.path.realpath(path)
    return any(
        real == allowed or real.startswith(allowed + os.sep)
        for allowed in settings.ALLOWED_DIRS
    )


def browse_dirs(request):
    """API endpoint to browse directories within allowed paths."""
    path = request.GET.get("path", "")

    # If no path given, auto-navigate into the first (or only) allowed root
    if not path:
        roots = [d for d in settings.ALLOWED_DIRS if os.path.isdir(d)]
        if len(roots) == 1:
            # Only one allowed dir — go straight into it
            path = roots[0]
        else:
            # Multiple roots — show them as selectable entries
            return JsonResponse({
                "dirs": [{"name": d, "path": d} for d in roots],
                "current": "",
                "parent": None,
            })

    # Validate the path is allowed
    real_path = os.path.realpath(path)
    if not _is_path_allowed(real_path):
        return JsonResponse({"error": "Adgang nægtet"}, status=403)

    if not os.path.isdir(real_path):
        return JsonResponse({"error": "Mappen findes ikke"}, status=404)

    # List subdirectories
    dirs = []
    try:
        for entry in sorted(os.scandir(real_path), key=lambda e: e.name.lower()):
            if entry.is_dir() and not entry.name.startswith("."):
                dirs.append({"name": entry.name, "path": entry.path})
    except PermissionError:
        return JsonResponse({"error": "Adgang nægtet"}, status=403)

    parent = os.path.dirname(real_path)
    parent_allowed = _is_path_allowed(parent) if parent != real_path else False

    return JsonResponse({
        "dirs": dirs,
        "current": real_path,
        "parent": parent if parent_allowed else None,
    })


def index(request):
    """Main page with scan form."""
    form = ScanForm()
    allowed_dirs = settings.ALLOWED_DIRS
    return render(request, "index.html", {"form": form, "allowed_dirs": allowed_dirs})


def scan(request):
    """Start a directory scan."""
    if request.method != "POST":
        return redirect("index")

    form = ScanForm(request.POST)
    if not form.is_valid():
        return render(request, "index.html", {"form": form})

    source_path = form.cleaned_data["source_path"]
    output_path = form.cleaned_data["output_path"]

    # Validate paths are within allowed directories
    if not _is_path_allowed(source_path):
        form.add_error("source_path", "Denne mappe er ikke tilgængelig.")
        return render(request, "index.html", {"form": form})
    if not _is_path_allowed(output_path):
        form.add_error("output_path", "Denne mappe er ikke tilgængelig.")
        return render(request, "index.html", {"form": form})

    session = scan_directory(
        source_path=source_path,
        output_path=output_path,
        mode=form.cleaned_data["mode"],
        profile=form.cleaned_data.get("profile"),
    )
    return redirect("session_detail", session_id=session.id)


def session_detail(request, session_id):
    """Display scanned files with selection checkboxes."""
    session = get_object_or_404(ScanSession, id=session_id)
    videos = session.videos.prefetch_related("subtitles").order_by("filename")
    return render(request, "session.html", {
        "session": session,
        "videos": videos,
    })


def session_update_selection(request, session_id):
    """Update file selections from checkboxes."""
    if request.method != "POST":
        return redirect("session_detail", session_id=session_id)

    session = get_object_or_404(ScanSession, id=session_id)

    # Get selected video IDs from form
    selected_video_ids = set(request.POST.getlist("selected_videos"))

    for video in session.videos.all():
        video.selected = str(video.id) in selected_video_ids
        video.save()

        # Update subtitle selections
        selected_sub_ids = set(request.POST.getlist(f"subs_{video.id}"))
        for sub in video.subtitles.all():
            sub.selected = str(sub.id) in selected_sub_ids
            sub.save()

    return redirect("session_detail", session_id=session_id)


def session_enqueue(request, session_id):
    """Create encode jobs for selected files and dispatch to RQ."""
    session = get_object_or_404(ScanSession, id=session_id)
    profile = session.profile
    queue = django_rq.get_queue("default")

    selected_videos = session.videos.filter(selected=True)

    for video in selected_videos:
        job = build_job(video, profile)
        rq_job = queue.enqueue(run_encode_job, job.id)
        job.rq_job_id = rq_job.id
        job.save(update_fields=["rq_job_id"])

    return redirect("queue")


def queue(request):
    """Display live queue status page."""
    jobs = EncodeJob.objects.select_related("video", "profile").order_by("-created_at")
    return render(request, "queue.html", {"jobs": jobs})


def queue_status(request):
    """HTMX partial: return only the queue table fragment."""
    jobs = EncodeJob.objects.select_related("video", "profile").order_by("-created_at")
    return render(request, "queue_partial.html", {"jobs": jobs})


def job_log(request, job_id):
    """Display full log for an encode job."""
    job = get_object_or_404(EncodeJob, id=job_id)
    return render(request, "job_log.html", {"job": job})


def settings_list(request):
    """List encoding profiles."""
    profiles = EncodingProfile.objects.order_by("mode", "name")
    return render(request, "settings.html", {"profiles": profiles})


def settings_create(request):
    """Create a new encoding profile."""
    if request.method != "POST":
        return redirect("settings_list")

    form = EncodingProfileForm(request.POST)
    if form.is_valid():
        form.save()
    return redirect("settings_list")


def settings_delete(request, profile_id):
    """Delete an encoding profile."""
    if request.method == "POST":
        profile = get_object_or_404(EncodingProfile, id=profile_id)
        profile.delete()
    return redirect("settings_list")
