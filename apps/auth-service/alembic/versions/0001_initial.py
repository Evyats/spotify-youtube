"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("email", sa.String(length=320), nullable=False, unique=True),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("google_sub", sa.String(length=255), nullable=True),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    else:
        if not _has_column(inspector, "users", "google_sub"):
            op.add_column("users", sa.Column("google_sub", sa.String(length=255), nullable=True))
        if not _has_column(inspector, "users", "verified_at"):
            op.add_column("users", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))

    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_sub ON users (google_sub)")

    if not inspector.has_table("songs"):
        op.create_table(
            "songs",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("artist", sa.String(length=255), nullable=False),
            sa.Column("album", sa.String(length=255), nullable=True),
            sa.Column("duration_sec", sa.Integer(), nullable=True),
            sa.Column("source_provider", sa.String(length=50), nullable=False),
            sa.Column("source_id", sa.String(length=255), nullable=False),
            sa.Column("source_channel", sa.String(length=255), nullable=True),
            sa.Column("quality_score", sa.Float(), nullable=True),
            sa.Column("storage_key", sa.String(length=512), nullable=True),
            sa.Column("codec", sa.String(length=50), nullable=True),
            sa.Column("bitrate_kbps", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("source_provider", "source_id", name="uq_song_source"),
        )
    op.execute("CREATE INDEX IF NOT EXISTS ix_songs_source_id ON songs (source_id)")

    if not inspector.has_table("user_songs"):
        op.create_table(
            "user_songs",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("song_id", sa.String(length=36), sa.ForeignKey("songs.id"), nullable=False),
            sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("user_id", "song_id", name="uq_user_song"),
        )
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_songs_user_id ON user_songs (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_songs_song_id ON user_songs (song_id)")

    if not inspector.has_table("download_jobs"):
        op.create_table(
            "download_jobs",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("source_provider", sa.String(length=50), nullable=False),
            sa.Column("source_id", sa.String(length=255), nullable=False),
            sa.Column("candidate_meta", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("failure_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
    op.execute("CREATE INDEX IF NOT EXISTS ix_download_jobs_user_id ON download_jobs (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_download_jobs_source_id ON download_jobs (source_id)")

    if not inspector.has_table("refresh_tokens"):
        op.create_table(
            "refresh_tokens",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("token_jti", sa.String(length=64), nullable=False),
            sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("token_jti", name="uq_refresh_token_jti"),
        )
    op.execute("CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_id ON refresh_tokens (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_refresh_tokens_token_jti ON refresh_tokens (token_jti)")

    if not inspector.has_table("email_verification_tokens"):
        op.create_table(
            "email_verification_tokens",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("token", sa.String(length=255), nullable=False),
            sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("token", name="uq_email_verification_token"),
        )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_email_verification_tokens_user_id ON email_verification_tokens (user_id)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_email_verification_tokens_token ON email_verification_tokens (token)")


def downgrade() -> None:
    op.drop_index("ix_email_verification_tokens_token", table_name="email_verification_tokens")
    op.drop_index("ix_email_verification_tokens_user_id", table_name="email_verification_tokens")
    op.drop_table("email_verification_tokens")
    op.drop_index("ix_refresh_tokens_token_jti", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index("ix_download_jobs_source_id", table_name="download_jobs")
    op.drop_index("ix_download_jobs_user_id", table_name="download_jobs")
    op.drop_table("download_jobs")
    op.drop_index("ix_user_songs_song_id", table_name="user_songs")
    op.drop_index("ix_user_songs_user_id", table_name="user_songs")
    op.drop_table("user_songs")
    op.drop_index("ix_songs_source_id", table_name="songs")
    op.drop_table("songs")
    op.drop_index("ix_users_google_sub", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
