# Admin detail development

Run from the monorepo root:

```powershell
docker compose -f docker-compose.local.yml exec -T api python manage.py migrate
docker compose -f docker-compose.local.yml exec -T api python manage.py seed_detail_demo
docker compose -f docker-compose.local.yml exec -T api python manage.py test visit.test_admin_details --noinput
docker compose -f docker-compose.local.yml exec -T admin node scripts/detail-values.test.cjs
```

The seed command accepts only `core.local_settings`, DEBUG and SQLite. It creates
a SQLite backup before writing and uses a transaction. It does not call external
APIs, send SMS or copy credentials. Sample IDs start at 2,000,001 and names include
«نمونه طراحی». Running the command again resets these demo records. Imported
production samples are not changed.

## Preview routes

Admin runs at `http://localhost:18120`.

| Record | Route |
| --- | --- |
| Visit | `/visitmanagment/answerlist/2000001` |
| Survey | `/surveymanagment/answerlist/2000001` |
| Building | `/elevatormanagement/buildingdetail/2000002` |
| Elevator | `/elevatormanagement/elevatordetail/2000001` |
| Customer | `/customermanagement/detail/2000001` |
| Store | `/storemng/detail/2000001` |
| Empty visit | `/visitmanagment/answerlist/2000002` |
| Empty survey | `/surveymanagment/answerlist/2000002` |
| Ticket | `/ticket/ticketdetail/2000001` |
| Empty ticket | `/ticket/ticketdetail/2000002` |
| Warehouse item | `/warehouse/waredetail/2000001` |

The existing local preview account stays read-only. API write tests create their
own users and permissions in an isolated test database. Demo media, backups,
screenshots and the generated route manifest are ignored by Git.

## Store compatibility

Migration 0075 removed the former Outlet model and its visit relations, while
the admin store screens still referenced its URLs. Migration 0087 introduces
independent `Store` and `StoreCategory` records scoped to a project. Existing
admin URLs now read/write those records. Building-based visits retain their
current model and relations; a store is not implicitly linked to a visit.

These views use `DeleteCreateUpdateGetPermission`; roles need explicit view/method
permissions through the existing permission administration. The local seed only
adds GET permissions for the existing preview role.

Image uploads use filesystem storage only with local settings. Face matching is
disabled for localhost previews; the existing external service is used only when
the operator explicitly requests matching in the configured remote environment.
