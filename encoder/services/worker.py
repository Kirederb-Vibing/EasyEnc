import os
import re
import subprocess

from django.utils import timezone

from encoder.models import EncodeJob


def run_encode_job(job_id):
    """RQ job function: run HandBrake encoding and optional mkvmerge remux."""
    job = EncodeJob.objects.get(id=job_id)

    try:
        job.status = "encoding"
        job.started_at = timezone.now()
        job.save()

        # Ensure output directory exists
        output_dir = os.path.dirname(job.output_path)
        os.makedirs(output_dir, exist_ok=True)

        # Check if output already exists (skip_existing)
        if job.profile and job.profile.skip_existing and os.path.exists(job.output_path):
            job.status = "skipped"
            job.finished_at = timezone.now()
            job.log += "Skipped: output file already exists.\n"
            job.save()
            return

        # Step 1: Run HandBrakeCLI
        job.log += f"Running: {job.handbrake_cmd}\n"
        job.save()

        proc = subprocess.Popen(
            job.handbrake_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Parse progress from HandBrake stderr
        progress_pattern = re.compile(r"(\d+\.\d+) %")
        for line in proc.stderr:
            match = progress_pattern.search(line)
            if match:
                progress = int(float(match.group(1)))
                if progress != job.progress:
                    job.progress = progress
                    job.save(update_fields=["progress"])
            job.log += line

        proc.wait()

        if proc.returncode != 0:
            job.status = "failed"
            job.log += f"\nHandBrake exited with code {proc.returncode}\n"
            job.finished_at = timezone.now()
            job.save()
            return

        # Step 2: mkvmerge remux (if subtitles selected)
        if job.mkvmerge_cmd:
            job.status = "remuxing"
            job.progress = 100
            job.log += f"\nRunning: {job.mkvmerge_cmd}\n"
            job.save()

            result = subprocess.run(
                job.mkvmerge_cmd,
                shell=True,
                capture_output=True,
                text=True,
            )
            job.log += result.stdout + result.stderr

            if result.returncode not in (0, 1):
                # mkvmerge returns 1 for warnings, which is acceptable
                job.status = "failed"
                job.log += f"\nmkvmerge exited with code {result.returncode}\n"
                job.finished_at = timezone.now()
                job.save()
                return

            # Remove temp file, keep final output
            tmp_path = os.path.splitext(job.output_path)[0] + ".tmp.mkv"
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        else:
            # No subtitles — rename tmp to final
            tmp_path = os.path.splitext(job.output_path)[0] + ".tmp.mkv"
            if os.path.exists(tmp_path):
                os.rename(tmp_path, job.output_path)

        # Step 3: Finalize
        if os.path.exists(job.output_path):
            job.output_size_bytes = os.path.getsize(job.output_path)

        job.status = "done"
        job.progress = 100
        job.finished_at = timezone.now()
        job.save()

        # Optionally delete source
        if job.profile and job.profile.delete_source:
            if os.path.exists(job.video.path):
                os.remove(job.video.path)

    except Exception as e:
        job.status = "failed"
        job.log += f"\nException: {e}\n"
        job.finished_at = timezone.now()
        job.save()
