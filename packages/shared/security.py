import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt
from passlib.exc import MissingBackendError
from passlib.context import CryptContext

from packages.shared.secrets import read_env_or_file


def _build_password_context() -> CryptContext:
    # Prefer Argon2, but fall back for local environments missing argon2 backend.
    preferred = CryptContext(schemes=["argon2"], deprecated="auto")
    try:
        preferred.hash("context-self-check")
        return preferred
    except MissingBackendError:
        return CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


pwd_context = _build_password_context()
USING_ARGON2 = "argon2" in (pwd_context.schemes() or [])


def jwt_secret() -> str:
    secret = read_env_or_file("JWT_SECRET", "dev-secret-change-me") or "dev-secret-change-me"
    if not secret or not secret.strip():
        secret = "dev-secret-change-me"
    enforce_strict = os.getenv("ENFORCE_STRICT_SECURITY", "0").lower() in {"1", "true", "yes", "on"}
    app_env = os.getenv("APP_ENV", "development").lower()
    prod_like = app_env in {"prod", "production", "staging"}
    if enforce_strict or prod_like:
        if secret == "dev-secret-change-me":
            raise RuntimeError("JWT_SECRET must not use the development default in strict/prod mode")
        if len(secret) < 32:
            raise RuntimeError("JWT_SECRET must be at least 32 characters in strict/prod mode")
    return secret


ALGORITHM = "HS256"
ACCESS_TTL_MIN = int(os.getenv("JWT_ACCESS_MINUTES", "30"))
REFRESH_TTL_DAYS = int(os.getenv("JWT_REFRESH_DAYS", "14"))
STREAM_URL_TTL_SECONDS = int(os.getenv("STREAM_URL_TTL_SECONDS", "90"))


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def _create_token(data: dict[str, Any], expires_delta: timedelta, token_type: str) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    to_encode.update({"iat": now, "exp": now + expires_delta, "type": token_type})
    return jwt.encode(to_encode, jwt_secret(), algorithm=ALGORITHM)


def create_access_token(user_id: str, role: str) -> str:
    return _create_token({"sub": user_id, "role": role}, timedelta(minutes=ACCESS_TTL_MIN), "access")


def refresh_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=REFRESH_TTL_DAYS)


def create_refresh_token(user_id: str, role: str) -> tuple[str, str, datetime]:
    jti = uuid4().hex
    expires_at = refresh_expires_at()
    return (
        _create_token({"sub": user_id, "role": role, "jti": jti}, timedelta(days=REFRESH_TTL_DAYS), "refresh"),
        jti,
        expires_at,
    )


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, jwt_secret(), algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("invalid token") from exc


def create_stream_token(user_id: str, song_id: str, ttl_seconds: int | None = None) -> str:
    ttl = ttl_seconds if ttl_seconds is not None else STREAM_URL_TTL_SECONDS
    return _create_token(
        {"sub": user_id, "song_id": song_id, "jti": uuid4().hex},
        timedelta(seconds=ttl),
        "stream",
    )


def decode_stream_token(token: str, expected_song_id: str) -> dict[str, Any]:
    claims = decode_token(token)
    if claims.get("type") != "stream":
        raise ValueError("invalid stream token type")
    if claims.get("song_id") != expected_song_id:
        raise ValueError("stream token song mismatch")
    if not claims.get("sub"):
        raise ValueError("stream token missing user")
    return claims


def validate_security_runtime() -> None:
    # Trigger secret validation and ensure strong hashing in strict/prod mode.
    jwt_secret()
    enforce_strict = os.getenv("ENFORCE_STRICT_SECURITY", "0").lower() in {"1", "true", "yes", "on"}
    app_env = os.getenv("APP_ENV", "development").lower()
    prod_like = app_env in {"prod", "production", "staging"}
    if (enforce_strict or prod_like) and not USING_ARGON2:
        raise RuntimeError("Argon2 hashing backend is required in strict/prod mode")
