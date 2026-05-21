from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, TypeVar


T = TypeVar("T")
JOB_DIR = ".project_launcher"
JOB_FILE = "jobs.json"


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    command: str
    status: str
    started_at: str
    ended_at: str
    duration_seconds: float
    summary: str


def run_with_job(folder: Path, command: str, operation: Callable[[], T], summarize: Callable[[T], str]) -> T:
    folder = folder.expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        return operation()
    started = time.perf_counter()
    started_at = _now()
    job_id = f"job-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    try:
        result = operation()
    except Exception as exc:
        _append_job(
            folder,
            JobRecord(
                job_id=job_id,
                command=command,
                status="failed",
                started_at=started_at,
                ended_at=_now(),
                duration_seconds=time.perf_counter() - started,
                summary=str(exc),
            ),
        )
        raise
    _append_job(
        folder,
        JobRecord(
            job_id=job_id,
            command=command,
            status="completed",
            started_at=started_at,
            ended_at=_now(),
            duration_seconds=time.perf_counter() - started,
            summary=summarize(result),
        ),
    )
    return result


def list_jobs(folder: Path) -> list[JobRecord]:
    return _read_jobs(_require_folder(folder))


def get_job(folder: Path, job_id: str) -> JobRecord:
    for job in list_jobs(folder):
        if job.job_id == job_id:
            return job
    raise ValueError(f"Job not found: {job_id}")


def format_jobs(jobs: list[JobRecord]) -> str:
    lines = ["Jobs", ""]
    if not jobs:
        return "Jobs\n\n- None\n"
    for job in jobs[-10:]:
        lines.append(f"- {job.job_id} [{job.status}] {job.command} ({job.duration_seconds:.1f}s)")
        lines.append(f"  {job.summary}")
    return "\n".join(lines).rstrip() + "\n"


def format_job(job: JobRecord) -> str:
    return "\n".join(
        [
            "Job Status",
            "",
            f"ID: {job.job_id}",
            f"Command: {job.command}",
            f"Status: {job.status}",
            f"Started: {job.started_at}",
            f"Ended: {job.ended_at}",
            f"Duration: {job.duration_seconds:.1f}s",
            f"Summary: {job.summary}",
        ]
    ).rstrip() + "\n"


def _append_job(folder: Path, job: JobRecord) -> None:
    path = _jobs_path(folder)
    path.parent.mkdir(exist_ok=True)
    jobs = _read_jobs(folder)
    jobs.append(job)
    path.write_text(json.dumps({"jobs": [asdict(item) for item in jobs]}, indent=2), encoding="utf-8")


def _read_jobs(folder: Path) -> list[JobRecord]:
    path = _jobs_path(folder)
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [JobRecord(**item) for item in data.get("jobs", [])]


def _jobs_path(folder: Path) -> Path:
    return folder / JOB_DIR / JOB_FILE


def _require_folder(folder: Path) -> Path:
    folder = folder.expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"{folder} is not a project folder.")
    return folder


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
