from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from packages.shared.db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Song(Base):
    __tablename__ = "songs"
    __table_args__ = (UniqueConstraint("source_provider", "source_id", name="uq_song_source"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(255))
    artist: Mapped[str] = mapped_column(String(255))
    album: Mapped[str | None] = mapped_column(String(255), nullable=True)
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_provider: Mapped[str] = mapped_column(String(50), default="youtube")
    source_id: Mapped[str] = mapped_column(String(255), index=True)
    source_channel: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    codec: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bitrate_kbps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class UserSong(Base):
    __tablename__ = "user_songs"
    __table_args__ = (UniqueConstraint("user_id", "song_id", name="uq_user_song"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    song_id: Mapped[str] = mapped_column(String(36), ForeignKey("songs.id"), index=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class DownloadJob(Base):
    __tablename__ = "download_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    source_provider: Mapped[str] = mapped_column(String(50), default="youtube")
    source_id: Mapped[str] = mapped_column(String(255), index=True)
    candidate_meta: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (UniqueConstraint("token_jti", name="uq_refresh_token_jti"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    token_jti: Mapped[str] = mapped_column(String(64), index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"
    __table_args__ = (UniqueConstraint("token", name="uq_email_verification_token"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    token: Mapped[str] = mapped_column(String(255), index=True)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
