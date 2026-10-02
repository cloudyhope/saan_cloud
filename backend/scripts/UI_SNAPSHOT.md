# Local UI data

The admin stays connected to `http://localhost:18110`. Production is only read
while downloading a bounded sample; editing the local UI does not write to production.

From the backend directory, download with:

```powershell
python scripts/fetch_ui_snapshot.py --username <production-username>
```

The password is prompted and the token stays in memory. The snapshot excludes
passwords, tokens and authentication permissions. Files under `backend/data/`
are ignored by Git.

Import from the monorepo directory:

```powershell
docker compose -f docker-compose.local.yml -p saan-local exec -T api python manage.py import_ui_snapshot data/production-snapshot.json
```

The importer requires `core.local_settings`, DEBUG and SQLite. It first makes
a SQLite backup next to the snapshot. It imports existing API fields using
QuerySet writes to avoid business save hooks. Imported identities get unusable
passwords; the existing local preview account keeps its login.

Source IDs are remapped to avoid local record collisions. Cities, provinces and
projects retain their IDs. Menu IDs also retain their source IDs because picture
routes reference them. The real menu hierarchy is assigned to the local preview
role, preserving its existing permissions.

This is a development sample, not a full production database backup. Paginated
business lists are capped at 100 rows. The import report records unavailable
relations. Endpoints returning 404 are recorded in the snapshot and skipped;
no sample data is invented for them.
