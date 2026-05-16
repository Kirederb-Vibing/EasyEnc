import django_rq
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ScanForm
from .models import EncodeJob, ScanSession, VideoFile
from .services.job_builder import build_job
from .services.scanner import scan_directory
from .services.worker import run_encode_job


def index(request):
    """Main page with scan form."""
    form = ScanForm()
    return render(request, "index.html", {"form": form})


def scan(request):
    """Start a directory scan."""
    if request.method != "POST":
        return redirect("index")

    form = ScanForm(request.POST)
    if not form.is_valid():
        return render(request, "index.html", {"form": form})

    session = scan_directory(
        source_path=form.cleaned_data["source_path"],
        output_path=form.cleaned_data["output_path"],
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
