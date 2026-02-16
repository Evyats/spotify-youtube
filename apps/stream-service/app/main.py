import os

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from packages.shared.db import make_engine, make_session_local
from packages.shared.internal_auth import decode_service_token
from packages.shared.models import Song, UserSong
from packages.shared.security import create_stream_token, decode_stream_token, validate_security_runtime


app = FastAPI(title="stream-service")
from packages.shared.observability import register_observability
register_observability(app, app.title)
validate_security_runtime()
engine = make_engine()
SessionLocal = make_session_local()

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET = os.getenv("S3_BUCKET", "songs")
PUBLIC_STREAM_BASE = os.getenv("PUBLIC_STREAM_BASE", "http://localhost:8005")
SERVICE_NAME = os.getenv("STREAM_SERVICE_NAME", "stream-service")

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)


def db_dep():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def internal_service_dep(x_service_token: str | None = Header(default=None, alias="X-Service-Token")) -> dict:
    if not x_service_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing internal service token")
    try:
        return decode_service_token(x_service_token, SERVICE_NAME)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "stream-service"}


@app.get("/internal/stream-url/{song_id}")
def stream_url(
    song_id: str,
    user_id: str = Query(...),
    _: dict = Depends(internal_service_dep),
    db: Session = Depends(db_dep),
):
    owns = db.scalar(
        select(UserSong).where(and_(UserSong.user_id == user_id, UserSong.song_id == song_id))
    )
    if owns is None:
        raise HTTPException(status_code=404, detail="song not in user library")

    song = db.scalar(select(Song).where(Song.id == song_id))
    if song is None or not song.storage_key:
        raise HTTPException(status_code=404, detail="song storage missing")

    stream_token = create_stream_token(user_id, song_id)
    return {"stream_url": f"{PUBLIC_STREAM_BASE}/public/stream/{song_id}?token={stream_token}"}


@app.get("/public/stream/{song_id}")
def public_stream(song_id: str, token: str, request: Request, db: Session = Depends(db_dep)):
    try:
        claims = decode_stream_token(token, song_id)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    user_id = claims["sub"]
    owns = db.scalar(select(UserSong).where(and_(UserSong.user_id == user_id, UserSong.song_id == song_id)))
    if owns is None:
        raise HTTPException(status_code=404, detail="song not in user library")

    song = db.scalar(select(Song).where(Song.id == song_id))
    if song is None or not song.storage_key:
        raise HTTPException(status_code=404, detail="song storage missing")

    range_header = request.headers.get("range")
    kwargs = {"Bucket": S3_BUCKET, "Key": song.storage_key}
    status_code = 200
    headers = {"Accept-Ranges": "bytes", "Content-Type": "audio/aac"}
    if range_header:
        kwargs["Range"] = range_header
        status_code = 206

    try:
        obj = s3.get_object(**kwargs)
    except ClientError as exc:
        raise HTTPException(status_code=404, detail="audio object not found") from exc

    if "ContentRange" in obj:
        headers["Content-Range"] = obj["ContentRange"]
    if "ContentLength" in obj:
        headers["Content-Length"] = str(obj["ContentLength"])

    return StreamingResponse(obj["Body"].iter_chunks(chunk_size=1024 * 128), status_code=status_code, headers=headers)





