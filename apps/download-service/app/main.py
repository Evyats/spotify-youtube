import json
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.celery_client import celery_client
from packages.shared.db import make_engine, make_session_local
from packages.shared.models import DownloadJob
from packages.shared.schemas import JobOut


app = FastAPI(title="download-service")
from packages.shared.observability import register_observability
register_observability(app, app.title)
engine = make_engine()
SessionLocal = make_session_local()


def db_dep():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CreateJobRequest(BaseModel):
    user_id: str
    source_provider: str = "youtube"
    source_video_id: str
    title: str | None = None
    artist: str | None = None
    candidate_meta: dict = Field(default_factory=dict)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "download-service"}


@app.post("/internal/jobs", response_model=JobOut)
def create_job(payload: CreateJobRequest, db: Session = Depends(db_dep)) -> DownloadJob:
    job = DownloadJob(
        id=str(uuid4()),
        user_id=payload.user_id,
        source_provider=payload.source_provider,
        source_id=payload.source_video_id,
        candidate_meta=json.dumps(
            {
                "title": payload.title,
                "artist": payload.artist,
                **payload.candidate_meta,
            }
        ),
        status="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    celery_client.send_task(
        "app.worker.process_import_job",
        kwargs={
            "job_id": job.id,
            "user_id": payload.user_id,
            "source_provider": payload.source_provider,
            "source_video_id": payload.source_video_id,
            "title": payload.title,
            "artist": payload.artist,
            "candidate_meta": payload.candidate_meta,
        },
    )
    return job


@app.get("/internal/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str, user_id: str, db: Session = Depends(db_dep)) -> DownloadJob:
    job = db.scalar(select(DownloadJob).where(and_(DownloadJob.id == job_id, DownloadJob.user_id == user_id)))
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job





