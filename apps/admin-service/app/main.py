from fastapi import Depends, FastAPI, Header, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from packages.shared.db import make_engine, make_session_local
from packages.shared.models import DownloadJob, Song, User
from packages.shared.security import decode_token


app = FastAPI(title="admin-service")
from packages.shared.observability import register_observability
register_observability(app, app.title)
engine = make_engine()
SessionLocal = make_session_local()


def db_dep():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def admin_dep(authorization: str | None = Header(default=None, alias="Authorization")) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    claims = decode_token(authorization.split(" ", 1)[1].strip())
    if claims.get("type") != "access" or claims.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin required")
    return claims


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "admin-service"}


@app.get("/internal/admin/users")
def list_users(_: dict = Depends(admin_dep), db: Session = Depends(db_dep)):
    users = db.execute(select(User).order_by(User.created_at.desc()).limit(200)).scalars()
    return {
        "users": [{"id": u.id, "email": u.email, "role": u.role, "created_at": u.created_at.isoformat()} for u in users]
    }


@app.get("/internal/admin/songs")
def list_songs(_: dict = Depends(admin_dep), db: Session = Depends(db_dep)):
    songs = db.execute(select(Song).order_by(Song.created_at.desc()).limit(200)).scalars()
    return {
        "songs": [
            {
                "id": s.id,
                "title": s.title,
                "artist": s.artist,
                "source_provider": s.source_provider,
                "source_id": s.source_id,
                "storage_key": s.storage_key,
                "created_at": s.created_at.isoformat(),
            }
            for s in songs
        ]
    }


@app.get("/internal/admin/jobs")
def list_jobs(_: dict = Depends(admin_dep), db: Session = Depends(db_dep)):
    jobs = db.execute(select(DownloadJob).order_by(desc(DownloadJob.updated_at)).limit(200)).scalars()
    return {
        "jobs": [
            {
                "id": j.id,
                "user_id": j.user_id,
                "source_provider": j.source_provider,
                "source_id": j.source_id,
                "status": j.status,
                "failure_reason": j.failure_reason,
                "updated_at": j.updated_at.isoformat(),
            }
            for j in jobs
        ]
    }





