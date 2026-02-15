import os
import subprocess
import tempfile
from pathlib import Path

import boto3
from botocore.client import Config
from celery import Celery
from sqlalchemy import and_, select

from packages.shared.db import make_engine, make_session_local
from packages.shared.models import DownloadJob, Song, UserSong

try:
    from yt_dlp import YoutubeDL
except Exception:
    YoutubeDL = None

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET = os.getenv("S3_BUCKET", "songs")

celery_app = Celery("download-worker", broker=broker_url, backend=result_backend)
celery_app.conf.broker_connection_retry_on_startup = True
engine = make_engine()
SessionLocal = make_session_local()

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)


def ensure_bucket() -> None:
    buckets = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
    if S3_BUCKET not in buckets:
        s3.create_bucket(Bucket=S3_BUCKET)


def set_job_status(job_id: str, status: str, failure_reason: str | None = None) -> None:
    with SessionLocal() as db:
        job = db.scalar(select(DownloadJob).where(DownloadJob.id == job_id))
        if job is None:
            return
        job.status = status
        job.failure_reason = failure_reason
        db.commit()


def add_user_song_if_missing(db, user_id: str, song_id: str) -> None:
    existing = db.scalar(
        select(UserSong).where(and_(UserSong.user_id == user_id, UserSong.song_id == song_id))
    )
    if existing is None:
        db.add(UserSong(user_id=user_id, song_id=song_id))
        db.commit()


def download_from_youtube(source_video_id: str, output_dir: Path) -> tuple[Path, dict]:
    if YoutubeDL is None:
        raise RuntimeError("yt-dlp is not available")

    output_tpl = str(output_dir / f"{source_video_id}.%(ext)s")
    opts = {
        "quiet": True,
        "noplaylist": True,
        "format": "bestaudio/best",
        "outtmpl": output_tpl,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={source_video_id}", download=True)
        downloaded = Path(ydl.prepare_filename(info))
    return downloaded, info


def transcode_to_aac(source_file: Path, output_dir: Path, source_video_id: str) -> Path:
    output = output_dir / f"{source_video_id}.m4a"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_file),
        "-vn",
        "-c:a",
        "aac",
        "-b:a",
        "256k",
        str(output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-500:]}")
    return output


@celery_app.task(
    name="app.worker.process_import_job",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=4,
)
def process_import_job(
    job_id: str,
    user_id: str,
    source_provider: str,
    source_video_id: str,
    title: str | None = None,
    artist: str | None = None,
    candidate_meta: dict | None = None,
):
    del candidate_meta
    set_job_status(job_id, "processing")
    try:
        with SessionLocal() as db:
            existing_song = db.scalar(
                select(Song).where(and_(Song.source_provider == source_provider, Song.source_id == source_video_id))
            )
            if existing_song:
                add_user_song_if_missing(db, user_id, existing_song.id)
                set_job_status(job_id, "completed")
                return {"job_id": job_id, "song_id": existing_song.id, "status": "completed"}

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            downloaded_file, info = download_from_youtube(source_video_id, tmp_path)
            transcoded_file = transcode_to_aac(downloaded_file, tmp_path, source_video_id)

            ensure_bucket()
            storage_key = f"songs/{source_provider}/{source_video_id}.m4a"
            s3.upload_file(str(transcoded_file), S3_BUCKET, storage_key, ExtraArgs={"ContentType": "audio/aac"})

            with SessionLocal() as db:
                song = db.scalar(
                    select(Song).where(and_(Song.source_provider == source_provider, Song.source_id == source_video_id))
                )
                if song is None:
                    song = Song(
                        source_provider=source_provider,
                        source_id=source_video_id,
                        title=title or info.get("title") or source_video_id,
                        artist=artist or info.get("uploader") or "Unknown Artist",
                        duration_sec=info.get("duration"),
                        source_channel=info.get("channel") or info.get("uploader"),
                        quality_score=0.9,
                        storage_key=storage_key,
                        codec="aac",
                        bitrate_kbps=256,
                    )
                    db.add(song)
                    db.commit()
                    db.refresh(song)

                add_user_song_if_missing(db, user_id, song.id)

        set_job_status(job_id, "completed")
        return {"job_id": job_id, "status": "completed"}
    except Exception as exc:
        set_job_status(job_id, "failed", str(exc)[:500])
        raise


@celery_app.task(name="app.worker.download_audio")
def download_audio(source_video_id: str, job_id: str):
    return {"source_video_id": source_video_id, "job_id": job_id, "detail": "deprecated task"}


@celery_app.task(name="app.worker.transcode_audio")
def transcode_audio(temp_key: str, target_codec: str = "aac", bitrate: str = "256k"):
    return {"temp_key": temp_key, "target_codec": target_codec, "bitrate": bitrate}


@celery_app.task(name="app.worker.store_audio")
def store_audio(file_key: str, metadata: dict):
    return {"file_key": file_key, "metadata": metadata}


@celery_app.task(name="app.worker.finalize_catalog_and_ownership")
def finalize_catalog_and_ownership(job_id: str, user_id: str, source_video_id: str, storage_key: str, metadata: dict):
    return {
        "job_id": job_id,
        "user_id": user_id,
        "source_video_id": source_video_id,
        "storage_key": storage_key,
        "metadata": metadata,
    }


