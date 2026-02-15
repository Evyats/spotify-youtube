import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt
from passlib.exc import MissingBackendError
from passlib.context import CryptContext


def _build_password_context() -> CryptContext:
    # Prefer Argon2, but fall back for local environments missing argon2 backend.
    preferred = CryptContext(schemes=["argon2"], deprecated="auto")
    try:
        preferred.hash("context-self-check")
        return preferred
    except MissingBackendError:
        return CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


pwd_context = _build_password_context()


def jwt_secret() -> str:
    return os.getenv("JWT_SECRET", "dev-secret-change-me")


ALGORITHM = "HS256"
ACCESS_TTL_MIN = int(os.getenv("JWT_ACCESS_MINUTES", "30"))
REFRESH_TTL_DAYS = int(os.getenv("JWT_REFRESH_DAYS", "14"))


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
