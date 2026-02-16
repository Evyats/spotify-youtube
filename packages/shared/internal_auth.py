import os
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from packages.shared.secrets import read_env_or_file


INTERNAL_ALGORITHM = "HS256"
INTERNAL_TTL_SECONDS = int(os.getenv("INTERNAL_TOKEN_TTL_SECONDS", "60"))


def internal_service_secret() -> str:
    secret = (
        read_env_or_file("INTERNAL_SERVICE_SECRET", "dev-internal-secret-change-me")
        or "dev-internal-secret-change-me"
    )
    if not secret or not secret.strip():
        secret = "dev-internal-secret-change-me"
    enforce_strict = os.getenv("ENFORCE_STRICT_SECURITY", "0").lower() in {"1", "true", "yes", "on"}
    app_env = os.getenv("APP_ENV", "development").lower()
    prod_like = app_env in {"prod", "production", "staging"}
    if enforce_strict or prod_like:
        if secret == "dev-internal-secret-change-me":
            raise RuntimeError("INTERNAL_SERVICE_SECRET must not use development default in strict/prod mode")
        if len(secret) < 32:
            raise RuntimeError("INTERNAL_SERVICE_SECRET must be at least 32 characters in strict/prod mode")
    return secret


def create_service_token(issuer_service: str, audience_service: str) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "iss": issuer_service,
        "aud": audience_service,
        "iat": now,
        "exp": now + timedelta(seconds=INTERNAL_TTL_SECONDS),
        "type": "internal_service",
    }
    return jwt.encode(payload, internal_service_secret(), algorithm=INTERNAL_ALGORITHM)


def decode_service_token(token: str, expected_audience: str) -> dict[str, Any]:
    try:
        claims = jwt.decode(
            token,
            internal_service_secret(),
            algorithms=[INTERNAL_ALGORITHM],
            audience=expected_audience,
        )
    except JWTError as exc:
        raise ValueError("invalid internal service token") from exc
    if claims.get("type") != "internal_service":
        raise ValueError("invalid internal service token type")
    if not claims.get("iss"):
        raise ValueError("internal service token missing issuer")
    return claims
