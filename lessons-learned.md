When mounting Postgres data to a host folder, I should always set `PGDATA` to a clean subdirectory so hidden files like `.gitkeep` do not break initialization.

For multi-service startup, I should never run schema creation from multiple containers at once; only one designated service should own DDL initialization (or migrations), and all worker/app commands should be verified for exact module target syntax before release.

When introducing Alembic into a project that already created tables manually, I should make the first migration backward-compatible (idempotent or baseline-stamp aware) so existing databases do not fail with duplicate-table errors.

When adding a browser frontend on a different port/origin, I should enable CORS in the API gateway immediately (including preflight handling) to avoid blocked requests from the UI.

When relying on `yt-dlp` inside containers, I should prefer low-dependency extraction settings (`extract_flat`, short timeouts, graceful fallback) so search results are returned quickly even without extra JS runtime tooling.

When introducing a new local frontend origin (like admin UI on port 3001), I should update API gateway CORS allowlist in the same change so authenticated requests do not fail at browser preflight.
