When mounting Postgres data to a host folder, I should always set `PGDATA` to a clean subdirectory so hidden files like `.gitkeep` do not break initialization.

For multi-service startup, I should never run schema creation from multiple containers at once; only one designated service should own DDL initialization (or migrations), and all worker/app commands should be verified for exact module target syntax before release.

When introducing Alembic into a project that already created tables manually, I should make the first migration backward-compatible (idempotent or baseline-stamp aware) so existing databases do not fail with duplicate-table errors.
