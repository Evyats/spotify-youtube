import os

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from packages.shared.db import make_engine, make_session_local
from packages.shared.internal_auth import decode_service_token
from packages.shared.models import Song, UserSong
from packages.shared.schemas import SongOut
from packages.shared.security import validate_security_runtime


app = FastAPI(title="catalog-service")
from packages.shared.observability import register_observability
register_observability(app, app.title)
validate_security_runtime()
engine = make_engine()
SessionLocal = make_session_local()
SERVICE_NAME = os.getenv("CATALOG_SERVICE_NAME", "catalog-service")


def db_dep():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class UpsertSongRequest(BaseModel):
    source_provider: str = "youtube"
    source_id: str
    title: str
    artist: str
    album: str | None = None
    duration_sec: int | None = None
    source_channel: str | None = None
    quality_score: float | None = None
    storage_key: str | None = None
    codec: str | None = "aac"
    bitrate_kbps: int | None = 256


class AddUserSongRequest(BaseModel):
    user_id: str
    song_id: str


def internal_service_dep(x_service_token: str | None = Header(default=None, alias="X-Service-Token")) -> dict:
    if not x_service_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing internal service token")
    try:
        return decode_service_token(x_service_token, SERVICE_NAME)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "catalog-service"}


@app.post("/internal/songs/upsert-from-source", response_model=SongOut)
def upsert_song(
    payload: UpsertSongRequest,
    _: dict = Depends(internal_service_dep),
    db: Session = Depends(db_dep),
) -> Song:
    song = db.scalar(
        select(Song).where(
            and_(Song.source_provider == payload.source_provider, Song.source_id == payload.source_id)
        )
    )
    if song:
        changed = False
        if payload.storage_key and song.storage_key != payload.storage_key:
            song.storage_key = payload.storage_key
            changed = True
        if payload.quality_score is not None:
            song.quality_score = payload.quality_score
            changed = True
        if changed:
            db.commit()
            db.refresh(song)
        return song

    song = Song(
        source_provider=payload.source_provider,
        source_id=payload.source_id,
        title=payload.title,
        artist=payload.artist,
        album=payload.album,
        duration_sec=payload.duration_sec,
        source_channel=payload.source_channel,
        quality_score=payload.quality_score,
        storage_key=payload.storage_key,
        codec=payload.codec,
        bitrate_kbps=payload.bitrate_kbps,
    )
    db.add(song)
    db.commit()
    db.refresh(song)
    return song


@app.post("/internal/users/songs")
def add_user_song(
    payload: AddUserSongRequest,
    _: dict = Depends(internal_service_dep),
    db: Session = Depends(db_dep),
) -> dict[str, str]:
    existing = db.scalar(
        select(UserSong).where(and_(UserSong.user_id == payload.user_id, UserSong.song_id == payload.song_id))
    )
    if existing:
        return {"status": "exists", "user_song_id": existing.id}

    link = UserSong(user_id=payload.user_id, song_id=payload.song_id)
    db.add(link)
    db.commit()
    db.refresh(link)
    return {"status": "created", "user_song_id": link.id}


@app.get("/internal/library/{user_id}")
def user_library(user_id: str, _: dict = Depends(internal_service_dep), db: Session = Depends(db_dep)) -> dict[str, list[dict]]:
    rows = db.execute(
        select(Song)
        .join(UserSong, UserSong.song_id == Song.id)
        .where(UserSong.user_id == user_id)
        .order_by(UserSong.added_at.desc())
    ).scalars()
    return {"songs": [SongOut.model_validate(song).model_dump() for song in rows]}


@app.get("/internal/songs/{song_id}", response_model=SongOut)
def get_song(song_id: str, _: dict = Depends(internal_service_dep), db: Session = Depends(db_dep)) -> Song:
    song = db.scalar(select(Song).where(Song.id == song_id))
    if song is None:
        raise HTTPException(status_code=404, detail="song not found")
    return song


@app.get("/internal/songs/by-source/{source_provider}/{source_id}", response_model=SongOut)
def get_song_by_source(
    source_provider: str,
    source_id: str,
    _: dict = Depends(internal_service_dep),
    db: Session = Depends(db_dep),
) -> Song:
    song = db.scalar(
        select(Song).where(and_(Song.source_provider == source_provider, Song.source_id == source_id))
    )
    if song is None:
        raise HTTPException(status_code=404, detail="song not found")
    return song





