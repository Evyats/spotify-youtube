import os
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from packages.shared.db import make_engine, make_session_local
from packages.shared.internal_auth import decode_service_token
from packages.shared.models import EmailVerificationToken, RefreshToken, User
from packages.shared.schemas import (
    RefreshRequest,
    SignInRequest,
    SignUpRequest,
    SignUpResponse,
    TokenPair,
    VerifyEmailRequest,
)
from packages.shared.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    validate_security_runtime,
    verify_password,
)


app = FastAPI(title="auth-service")
from packages.shared.observability import register_observability
register_observability(app, app.title)
validate_security_runtime()
engine = make_engine()
SessionLocal = make_session_local()

EMAIL_VERIFY_REQUIRED = os.getenv("EMAIL_VERIFY_REQUIRED", "1").lower() in {"1", "true", "yes", "on"}
EXPOSE_VERIFICATION_TOKEN = os.getenv("EXPOSE_VERIFICATION_TOKEN", "1").lower() in {"1", "true", "yes", "on"}
OAUTH_GOOGLE_CLIENT_ID = os.getenv("OAUTH_GOOGLE_CLIENT_ID", "")
OAUTH_GOOGLE_CLIENT_SECRET = os.getenv("OAUTH_GOOGLE_CLIENT_SECRET", "")
OAUTH_GOOGLE_REDIRECT_URI = os.getenv("OAUTH_GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
GOOGLE_OAUTH_SCOPE = "openid email profile"
SERVICE_NAME = os.getenv("AUTH_SERVICE_NAME", "auth-service")
ADMIN_BOOTSTRAP_EMAIL = os.getenv("ADMIN_BOOTSTRAP_EMAIL", "").strip().lower()


def db_dep():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def issue_tokens_and_store_refresh(db: Session, user: User) -> TokenPair:
    access_token = create_access_token(user.id, user.role)
    refresh_token, refresh_jti, refresh_expires = create_refresh_token(user.id, user.role)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_jti=refresh_jti,
            revoked=False,
            expires_at=refresh_expires,
        )
    )
    db.commit()
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


def create_email_verification(db: Session, user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    db.add(EmailVerificationToken(user_id=user_id, token=token, used=False, expires_at=expires_at))
    db.commit()
    return token


def internal_service_dep(x_service_token: str | None = Header(default=None, alias="X-Service-Token")) -> dict:
    if not x_service_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing internal service token")
    try:
        return decode_service_token(x_service_token, SERVICE_NAME)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def resolve_role_for_new_user(email: str, db: Session) -> str:
    if ADMIN_BOOTSTRAP_EMAIL and email.lower() == ADMIN_BOOTSTRAP_EMAIL:
        existing_admin = db.scalar(select(User).where(User.role == "admin"))
        if existing_admin is None or existing_admin.email.lower() == ADMIN_BOOTSTRAP_EMAIL:
            return "admin"
    return "user"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "auth-service"}


@app.post("/internal/signup", response_model=SignUpResponse)
def signup(
    payload: SignUpRequest,
    _: dict = Depends(internal_service_dep),
    db: Session = Depends(db_dep),
) -> SignUpResponse:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already exists")

    role = resolve_role_for_new_user(payload.email, db)
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=role,
        verified_at=None if EMAIL_VERIFY_REQUIRED else datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    verification_token = None
    if EMAIL_VERIFY_REQUIRED:
        if EXPOSE_VERIFICATION_TOKEN:
            verification_token = create_email_verification(db, user.id)
        else:
            create_email_verification(db, user.id)
    return SignUpResponse(detail="signup created", verification_token=verification_token)


@app.post("/internal/verify-email")
def verify_email(
    payload: VerifyEmailRequest,
    _: dict = Depends(internal_service_dep),
    db: Session = Depends(db_dep),
) -> dict[str, str]:
    row = db.scalar(
        select(EmailVerificationToken).where(
            and_(EmailVerificationToken.token == payload.token, EmailVerificationToken.used.is_(False))
        )
    )
    if row is None:
        raise HTTPException(status_code=404, detail="verification token not found")
    if row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="verification token expired")

    user = db.scalar(select(User).where(User.id == row.user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")

    row.used = True
    user.verified_at = datetime.now(timezone.utc)
    db.commit()
    return {"detail": "email verified"}


@app.post("/internal/signin", response_model=TokenPair)
def signin(
    payload: SignInRequest,
    _: dict = Depends(internal_service_dep),
    db: Session = Depends(db_dep),
) -> TokenPair:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    if EMAIL_VERIFY_REQUIRED and user.verified_at is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="email not verified")

    return issue_tokens_and_store_refresh(db, user)


@app.post("/internal/refresh", response_model=TokenPair)
def refresh(
    payload: RefreshRequest,
    _: dict = Depends(internal_service_dep),
    db: Session = Depends(db_dep),
) -> TokenPair:
    try:
        claims = decode_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    if claims.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token type")
    token_jti = claims.get("jti")
    if not token_jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token missing jti")

    token_row = db.scalar(select(RefreshToken).where(RefreshToken.token_jti == token_jti))
    if token_row is None or token_row.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token revoked")
    if token_row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token expired")

    user = db.scalar(select(User).where(User.id == claims.get("sub")))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")

    token_row.revoked = True
    db.commit()
    return issue_tokens_and_store_refresh(db, user)


@app.post("/internal/logout")
def logout(
    payload: RefreshRequest,
    _: dict = Depends(internal_service_dep),
    db: Session = Depends(db_dep),
) -> dict[str, str]:
    try:
        claims = decode_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    if claims.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token type")
    token_jti = claims.get("jti")
    if not token_jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token missing jti")

    token_row = db.scalar(select(RefreshToken).where(RefreshToken.token_jti == token_jti))
    if token_row:
        token_row.revoked = True
        db.commit()
    return {"detail": "signed out"}


@app.get("/internal/oauth/google/login")
def google_login(_: dict = Depends(internal_service_dep)) -> dict[str, str]:
    if not OAUTH_GOOGLE_CLIENT_ID or not OAUTH_GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="google oauth is not configured")

    state = create_access_token("oauth", "oauth_state")
    params = {
        "client_id": OAUTH_GOOGLE_CLIENT_ID,
        "redirect_uri": OAUTH_GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": GOOGLE_OAUTH_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return {"redirect_url": f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"}


@app.get("/internal/oauth/google/callback", response_model=TokenPair)
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    _: dict = Depends(internal_service_dep),
    db: Session = Depends(db_dep),
) -> TokenPair:
    if not OAUTH_GOOGLE_CLIENT_ID or not OAUTH_GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="google oauth is not configured")
    try:
        state_claims = decode_token(state)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid oauth state") from exc
    if state_claims.get("type") != "access" or state_claims.get("sub") != "oauth":
        raise HTTPException(status_code=400, detail="invalid oauth state")

    async with httpx.AsyncClient(timeout=30) as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": OAUTH_GOOGLE_CLIENT_ID,
                "client_secret": OAUTH_GOOGLE_CLIENT_SECRET,
                "redirect_uri": OAUTH_GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_res.status_code >= 400:
            raise HTTPException(status_code=400, detail="failed exchanging google code")

        access_token = token_res.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="google access token missing")

        profile_res = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if profile_res.status_code >= 400:
            raise HTTPException(status_code=400, detail="failed fetching google profile")
        profile = profile_res.json()

    email = profile.get("email")
    google_sub = profile.get("sub")
    if not email or not google_sub:
        raise HTTPException(status_code=400, detail="google profile missing required fields")

    user = db.scalar(select(User).where(User.google_sub == google_sub))
    if user is None:
        user = db.scalar(select(User).where(User.email == email))
    if user is None:
        role = resolve_role_for_new_user(email, db)
        user = User(
            email=email,
            password_hash=hash_password(secrets.token_urlsafe(24)),
            role=role,
            google_sub=google_sub,
            verified_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.google_sub = google_sub
        if user.verified_at is None:
            user.verified_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)

    return issue_tokens_and_store_refresh(db, user)



