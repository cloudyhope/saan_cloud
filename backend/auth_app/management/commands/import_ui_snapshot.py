"""Import API samples into local SQLite without invoking business save hooks."""
import json
import sqlite3
from collections import Counter
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

SOURCES = {
    'profile': 'auth_app.RoleAssignment', 'roles': 'auth_app.Role',
    'assignments': 'auth_app.RoleAssignment', 'cities': 'auth_app.ActiveCity',
    'visit_types': 'visit.VisitType', 'visits': 'visit.Visit',
    'surveys': 'survey.Survey', 'survey_fillouts': 'survey.SurveyFillOut',
    'tickets': 'visit.Ticket', 'ticket_messages': 'visit.TicketMessage',
    'ware_types': 'warehouse.WareType', 'units': 'warehouse.Unit',
    'wares': 'warehouse.Ware', 'locations': 'warehouse.WarehouseLocation',
    'clients': 'visit.Client', 'user_clients': 'visit.UserClient',
    'buildings': 'visit.Building', 'elevators': 'visit.Elevator',
    'building_elevators': 'visit.BuildingElevator',
    'media_types': 'config.MediaType', 'media': 'config.MediaManager',
}
NATIVE_IDS = {'auth_app.Project', 'auth_app.City', 'auth_app.Province'}
OFFSET = 1000000


def rows(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return payload.get('results', [payload])
    return []


def local_id(model, source_id):
    if source_id is None:
        return None
    return int(source_id) + (0 if model._meta.label in NATIVE_IDS else OFFSET)


class Command(BaseCommand):
    help = 'Import a bounded production API snapshot into LOCAL SQLite for UI development.'

    def add_arguments(self, parser):
        parser.add_argument('snapshot', type=Path)
        parser.add_argument('--preview-user', default='09000000001')

    def handle(self, *args, **options):
        db = settings.DATABASES['default']
        if not settings.DEBUG or db['ENGINE'] != 'django.db.backends.sqlite3' or settings.SETTINGS_MODULE != 'core.local_settings':
            raise CommandError('This command only supports core.local_settings with DEBUG SQLite.')
        source = options['snapshot'].resolve()
        snapshot = json.loads(source.read_text(encoding='utf-8-sig'))
        backup = source.parent / ('db-before-ui-import-' + timezone.now().strftime('%Y%m%d-%H%M%S') + '.sqlite3')
        with sqlite3.connect(str(db['NAME'])) as current, sqlite3.connect(str(backup)) as saved:
            current.backup(saved)
        self.stdout.write('Local database backup: ' + str(backup))
        self.queue = {}
        self.id_map = {}
        self.building_links = set()
        self.counts = Counter()
        self.omitted = Counter()
        for key, label in SOURCES.items():
            response = snapshot.get(key, {})
            if response.get('status') == 200:
                model = apps.get_model(label)
                for row in rows(response['data']):
                    self.collect(model, row)

        user_model = apps.get_model('auth.User')
        usernames = {}
        for (label, source_id), (_, data) in self.queue.items():
            if label == 'auth.User':
                username = data.get('username')
                existing = user_model.objects.filter(username=username).first()
                mapped = existing.pk if existing else usernames.setdefault(username, local_id(user_model, source_id))
                self.id_map[(label, source_id)] = mapped
        extended_model = apps.get_model('auth_app.ExtendedUser')
        for (label, source_id), (_, data) in self.queue.items():
            if label == 'auth_app.ExtendedUser':
                existing = extended_model.objects.filter(user_id=self.mapped_id(user_model, data['user'])).first()
                if existing:
                    self.id_map[(label, source_id)] = existing.pk

        with transaction.atomic():
            pending = dict(self.queue)
            for _ in range(20):
                remaining = {}
                for key, (model, data) in pending.items():
                    try:
                        self.insert(model, data)
                    except LookupError:
                        remaining[key] = (model, data)
                if not remaining or len(remaining) == len(pending):
                    pending = remaining
                    break
                pending = remaining
            self.omitted.update(model._meta.label for model, _ in pending.values())
            for key, (model, data) in self.queue.items():
                if key not in pending:
                    self.link_many_to_many(model, data)
            self.link_buildings()
            self.copy_menu(snapshot.get('menus', {}), options['preview_user'])
        for label, count in sorted(self.counts.items()):
            self.stdout.write(f'{label}: {count}')
        if self.omitted:
            self.stdout.write('Unavailable related records: ' + json.dumps(dict(self.omitted)))
        report = {'imported': dict(self.counts), 'unavailable_relations': dict(self.omitted), 'backup': str(backup)}
        (source.parent / 'ui-import-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')

    def collect(self, model, data):
        if not isinstance(data, dict) or data.get('id') is None:
            return
        key = (model._meta.label, data['id'])
        previous = self.queue.get(key, (model, {}))[1]
        self.queue[key] = (model, {**previous, **data})
        for field in model._meta.get_fields():
            if not field.is_relation or field.auto_created:
                continue
            value = data.get(field.name)
            if isinstance(value, dict):
                self.collect(field.related_model, value)
            elif isinstance(value, list):
                for item in value:
                    self.collect(field.related_model, item)
        if model._meta.label == 'auth.User' and isinstance(data.get('extended'), dict):
            self.collect(apps.get_model('auth_app.ExtendedUser'), {**data['extended'], 'user': data['id']})
        if model._meta.label == 'visit.Building':
            for elevator in data.get('elevators', []):
                self.collect(apps.get_model('visit.Elevator'), elevator)
                if isinstance(elevator, dict) and elevator.get('id'):
                    self.building_links.add((data['id'], elevator['id']))

    def insert(self, model, data):
        values = {}
        for field in model._meta.concrete_fields:
            if field.primary_key:
                continue
            if field.name in {'password', 'groups', 'user_permissions', 'is_superuser', 'is_staff'}:
                continue
            if field.name not in data:
                if not field.null and not field.has_default() and not field.empty_strings_allowed and not getattr(field, 'auto_now_add', False) and not getattr(field, 'auto_now', False):
                    raise LookupError(field.name)
                continue
            value = data[field.name]
            if field.is_relation:
                reference = value.get('id') if isinstance(value, dict) else value
                reference_id = self.mapped_id(field.related_model, reference)
                if reference_id is not None and not field.related_model.objects.filter(pk=reference_id).exists():
                    if (field.related_model._meta.label, reference) in self.queue or not field.null:
                        raise LookupError(field.name)
                    self.omitted[field.related_model._meta.label] += 1
                    reference_id = None
                values[field.attname] = reference_id
            else:
                values[field.name] = value
        pk = self.mapped_id(model, data['id'])
        if model._meta.label == 'auth.User' and not model.objects.filter(pk=pk).exists():
            values.update(password='!', is_superuser=False, is_staff=False)
        # QuerySet writes deliberately avoid SMS, wallet and other save hooks.
        if model.objects.filter(pk=pk).exists():
            model.objects.filter(pk=pk).update(**values)
        else:
            model.objects.bulk_create([model(pk=pk, **values)])
        self.counts[model._meta.label] += 1
    def link_many_to_many(self, model, data):
        pk = self.mapped_id(model, data['id'])
        for field in model._meta.many_to_many:
            if field.remote_field.through._meta.auto_created and isinstance(data.get(field.name), list):
                ids = [self.mapped_id(field.related_model, item.get('id') if isinstance(item, dict) else item) for item in data[field.name]]
                ids = list(field.related_model.objects.filter(pk__in=ids).values_list('pk', flat=True))
                getattr(model.objects.get(pk=pk), field.name).set(ids)

    def mapped_id(self, model, source_id):
        return self.id_map.get((model._meta.label, source_id), local_id(model, source_id))

    def link_buildings(self):
        model = apps.get_model('visit.BuildingElevator')
        for building, elevator in self.building_links:
            building += OFFSET
            elevator += OFFSET
            if not model.objects.filter(building_id=building, elevator_id=elevator).exists():
                model.objects.bulk_create([model(building_id=building, elevator_id=elevator)])

    def copy_menu(self, response, username):
        if response.get('status') != 200:
            return
        assignment = apps.get_model('auth_app.RoleAssignment').objects.filter(user__username=username, project_id=1, is_deleted=False).first()
        if not assignment:
            raise CommandError('Create the local preview account before importing menus.')
        menu_model = apps.get_model('auth_app.AdminMenu')
        menu_model.objects.filter(role=assignment.role, project=assignment.project).update(is_active=False)
        def copy(items, parent=None):
            for item in items:
                values = {field.name: item[field.name] for field in menu_model._meta.concrete_fields if not field.is_relation and not field.primary_key and field.name in item}
                values.update(name='production-preview-' + str(item['id']), parent=parent, role=assignment.role, project=assignment.project)
                # Picture/report routes carry the original menu ID in the URL.
                menu, _ = menu_model.objects.update_or_create(pk=item['id'], defaults=values)
                self.counts['auth_app.AdminMenu'] += 1
                copy(item.get('children', []), menu)
        copy(rows(response['data']))
