"""Tiny JSON-file job log shared by the dashboard and the pipeline."""
import json
import os
import threading
import time

JOBS_FILE = os.path.join(os.path.dirname(__file__), "assets", "jobs.json")
_lock = threading.Lock()


def _read() -> list[dict]:
    if not os.path.exists(JOBS_FILE):
        return []
    with open(JOBS_FILE, "r") as f:
        return json.load(f)


def _write(jobs: list[dict]) -> None:
    os.makedirs(os.path.dirname(JOBS_FILE), exist_ok=True)
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2)


def create_job(topic: str, upload: bool) -> str:
    with _lock:
        jobs = _read()
        job_id = str(int(time.time() * 1000))
        jobs.insert(0, {
            "id": job_id,
            "topic": topic,
            "upload": upload,
            "status": "running",
            "step": "starting",
            "video_path": None,
            "youtube_url": None,
            "error": None,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        _write(jobs)
        return job_id


def update_job(job_id: str, **fields) -> None:
    with _lock:
        jobs = _read()
        for job in jobs:
            if job["id"] == job_id:
                job.update(fields)
                break
        _write(jobs)


def list_jobs() -> list[dict]:
    with _lock:
        return _read()
