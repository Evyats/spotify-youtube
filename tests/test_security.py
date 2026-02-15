from packages.shared.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
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
