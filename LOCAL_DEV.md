# Local development

The local stack runs the Saan API, admin and shared field app with Docker Desktop. Start it from this monorepo directory:

```powershell
docker compose -f docker-compose.local.yml up --build -d
```

| Service | URL |
| --- | --- |
| Admin | http://localhost:18120 |
| Shared field app (Expert and initial Client service flow) | http://localhost:18122 |
| API health | http://localhost:18110/health/ |

View logs with `docker compose -f docker-compose.local.yml logs -f` and stop the stack with `docker compose -f docker-compose.local.yml down`.

The API uses SQLite at `backend/data/db.sqlite3`, which is a separate local copy of `backend/db.sqlite3`; migrations run on this copy. Uploaded files use `backend/local_media/`. Local Django settings are in `backend/core/local_settings.py` and use filesystem storage rather than a MinIO service.

The incorrect standalone client app has been removed. Client and Expert capabilities are developed in `expert/` using backend roles, permissions and menus. Client workflows are not yet complete. See [MASTER_PLAN](docs/MASTER_PLAN.md) and record every work package in [HANDOFF](HANDOFF.md).

For a local Expert preview, supply a password explicitly:

```powershell
docker compose -f docker-compose.local.yml exec api python manage.py seed_expert_preview --password $env:SAAN_LOCAL_PREVIEW_PASSWORD
```

Set the environment variable privately first. The command requires DEBUG and SQLite, backs up the database, and creates a full-access role, menu and representative visits/stock. It does not validate production role boundaries.

The limited Client preview uses a private JSON file in ignored `backend/data` with `username` and `password` keys. The current file is already present locally:

```powershell
docker compose -f docker-compose.local.yml exec -T api python manage.py seed_client_preview --credentials-file /usr/src/app/data/client-preview-credentials.json
```

The command adds synthetic buildings, elevators and boards and narrow Client grants. Sign in to the field app; the backend menu selects the Client or Expert landing page. Both roles share this origin's persisted login; after switching account, reload other tabs to synchronize their session.

Asset roles have `asset_scope`: none, client, assigned, supervised or project. A method grant is also required. New roles default to none. Unassigned legacy assets remain hidden; review multi-project legacy data before rollout.

Focused checks:

```powershell
docker compose -f docker-compose.local.yml exec -T api python manage.py test auth_app.test_security visit.test_admin_details visit.test_assets visit.test_asset_access --noinput
docker compose -f docker-compose.local.yml exec -T expert node scripts/check-field-flows.cjs
docker compose -f docker-compose.local.yml exec -T expert npm run build-production
```

Local database copies, media, screenshots and audit data are ignored. Do not commit production personal data, passwords, tokens or database dumps. SQLite preview results do not certify production database migrations or concurrency. External SMS and media services require separate staging verification before release.
