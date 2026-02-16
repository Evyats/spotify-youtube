import pytest

from packages.shared.internal_auth import create_service_token, decode_service_token
from packages.shared.security import (
    create_access_token,
    create_refresh_token,
    create_stream_token,
    decode_stream_token,
    decode_token,
    hash_password,
    jwt_secret,
    verify_password,
)


def test_password_hash_roundtrip():
    raw = "strong-password-123"
    digest = hash_password(raw)
    assert digest != raw
    assert verify_password(raw, digest)


def test_access_and_refresh_tokens_have_types():
    access = create_access_token("u1", "user")
    refresh, jti, expires_at = create_refresh_token("u1", "user")

    access_claims = decode_token(access)
    refresh_claims = decode_token(refresh)

    assert jti
    assert expires_at is not None
    assert access_claims["type"] == "access"
    assert refresh_claims["type"] == "refresh"
    assert refresh_claims["jti"] == jti
    assert access_claims["sub"] == "u1"


def test_stream_token_roundtrip():
    token = create_stream_token("u1", "song1", ttl_seconds=60)
    claims = decode_stream_token(token, "song1")
    assert claims["sub"] == "u1"
    assert claims["song_id"] == "song1"
    assert claims["type"] == "stream"


def test_internal_service_token_roundtrip():
    token = create_service_token("api-gateway", "search-service")
    claims = decode_service_token(token, "search-service")
    assert claims["iss"] == "api-gateway"
    assert claims["aud"] == "search-service"
    assert claims["type"] == "internal_service"


def test_strict_mode_rejects_default_jwt_secret(monkeypatch):
    monkeypatch.setenv("ENFORCE_STRICT_SECURITY", "1")
    monkeypatch.setenv("JWT_SECRET", "dev-secret-change-me")
    with pytest.raises(RuntimeError):
        jwt_secret()
