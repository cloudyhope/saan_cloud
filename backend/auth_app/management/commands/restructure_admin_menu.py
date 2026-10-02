"""Preview or apply the shorter admin sidebar: status tabs, hidden legacy items and merged groups.

Works on the existing AdminMenu rows of one project (optionally one role) and never deletes anything:
rows are re-parented, re-labelled or deactivated, so every change can be undone from the menu table.
The preview is the default; add --apply after reading it.

  tabs      status-style groups (visits, surveys, supervision) become one sidebar link; their children are
            shown as tabs above the page (AdminMenu.frontend_route_params = {"display": "tabs"})
  hide      the supervision group (supervisors are not in the field app), the notifications entry (the bell)
            and the legacy stores entry
  merge     content, planning, warehouse and warranty, assets, and a settings group
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from auth_app.menu_icons import data_uri, icons_for
from auth_app.models import AdminMenu, Project, Role

TAB_GROUPS = {
    '/visitmanagment/lists': {'/visitmanagment/lists', '/visitmanagment/notcompeletevisits',
                              '/visitmanagment/completevisited', '/visitmanagment/acceptedvisits'},
    '/suveymanagment/lists': {'/suveymanagment/lists', '/surveymanagment/notcompeletesurvey',
                              '/suveymanagment/completesurvey', '/surveymanagment/acceptedsurvey'},
    '/supervisionmanagment/lists': {'/supervisionmanagment/lists', '/supervisionmanagment/notcompeletesupervision',
                                    '/supervisionmanagment/completesupervision', '/supervisionmanagment/acceptedsupervision'},
}
HIDE_SUPERVISION = '/supervisionmanagment/'
HIDE_NOTIFICATIONS = '/notifications'
HIDE_STORES = '/storemng/'  # the legacy shop screens; this product has no stores

# key, title, route of the new group, groups merged into it (by their route), single pages moved into it (first),
# icon key for settings-like groups (None: the section icon of the route)
MERGES = (
    ('planning', 'برنامه‌ریزی', '/actionplan/listactionplan', ('/actionplan/listactionplan',), ('/assignment',), None),
    ('warehouse', 'انبار و گارانتی', '/warehouse/warelist', ('/warehouse/warelist',), ('/service-cases',), None),
    ('assets', 'دارایی‌ها', '/customermanagement/list', ('/customermanagement/list', '/elevatormanagement/buildinglist'), (), None),
    ('content', 'محتوا', '/medialist/list', ('/medialist/list', '/filemanagement/filelist'), (), None),
    ('settings', 'قواعد و تنظیمات', '/priority', (), ('/priority', '/visitmanagment/visit-types'), 'sliders'),
)


def canonical(url):
    return (url or '').split('?')[0].rstrip('/').lower()


class Command(BaseCommand):
    help = 'Preview or apply the shorter admin sidebar (tabs, hidden legacy items, merged groups).'

    def add_arguments(self, parser):
        parser.add_argument('--project', type=int, required=True)
        parser.add_argument('--role', type=int, help='Limit to one role; default is every role with menu rows.')
        parser.add_argument('--keep-supervision', action='store_true')
        parser.add_argument('--keep-notifications', action='store_true')
        parser.add_argument('--keep-stores', action='store_true')
        parser.add_argument('--skip', action='append', default=[], choices=[item[0] for item in MERGES] + ['tabs'],
                            help='Leave one operation out (repeatable).')
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        project = Project.objects.filter(pk=options['project']).first()
        if project is None:
            raise CommandError('Unknown project.')
        roles = Role.objects.filter(pk__in=AdminMenu.objects.filter(project=project).values('role_id'))
        if options['role']:
            roles = roles.filter(pk=options['role'])
        if not roles.exists():
            raise CommandError('No role with admin menu rows in this project.')
        self.apply = options['apply']
        self.options = options
        with transaction.atomic():
            for role in roles:
                self.stdout.write(f'Role {role.pk} {role.title}:')
                self.plan = []
                self.virtual_moved = set()  # rows a preview treats as already moved by an earlier step
                self.restructure(project, role)
                if not self.plan:
                    self.stdout.write('  nothing to change')
            if not self.apply:
                transaction.set_rollback(True)
        self.stdout.write(self.style.SUCCESS('Applied.') if self.apply else 'Preview only. Add --apply after reviewing.')

    # ------------------------------------------------------------------ helpers
    def log(self, text):
        self.plan.append(text)
        self.stdout.write('  ' + text)

    def rows(self, project, role):
        return AdminMenu.objects.filter(project=project, role=role, is_active=True)

    def by_url(self, rows, url):
        return next((row for row in rows.order_by('parent_id', 'priority') if canonical(row.frontend_route_url) == url), None)

    def children(self, rows, parent):
        return list(rows.filter(parent=parent).order_by('priority', 'id'))

    # ------------------------------------------------------------------ operations
    def restructure(self, project, role):
        self.hide(project, role)
        for key, title, route, groups, leaves, icon in MERGES:
            if key not in self.options['skip']:
                self.merge(project, role, key, title, route, groups, leaves, icon)
        if 'tabs' not in self.options['skip']:
            self.tabs(project, role)

    def hide(self, project, role):
        rows = self.rows(project, role)
        if not self.options['keep_supervision']:
            for row in rows.filter(frontend_route_url__istartswith=HIDE_SUPERVISION):
                self.log(f'hide «{row.verbose_name}» ({row.frontend_route_url})')
                if self.apply:
                    row.is_active = False
                    row.save(update_fields=['is_active'])
        if not self.options['keep_stores']:
            for row in rows.filter(frontend_route_url__istartswith=HIDE_STORES):
                self.log(f'hide «{row.verbose_name}» (legacy shop screens)')
                if self.apply:
                    row.is_active = False
                    row.save(update_fields=['is_active'])
        if not self.options['keep_notifications']:
            row = self.by_url(rows, HIDE_NOTIFICATIONS)
            if row:
                self.log(f'hide «{row.verbose_name}» (the bell in the header replaces it)')
                if self.apply:
                    row.is_active = False
                    row.save(update_fields=['is_active'])

    def merge(self, project, role, key, title, route, groups, leaves, icon):
        if AdminMenu.objects.filter(project=project, role=role, name='mg-' + key).exists():
            return
        rows = self.rows(project, role)
        sources = [row for row in (self.by_url(rows, url) for url in groups) if row is not None]
        moved = []
        for url in leaves:
            row = self.by_url(rows, url)
            if row is not None and not self.children(rows, row):
                moved.append(row)
        for source in sources:
            moved.extend(self.children(rows, source) or [source])
        moved = list({row.pk: row for row in moved}.values())
        if len(moved) < 2:
            return
        self.log(f'group «{title}» ← ' + '، '.join(row.verbose_name or row.name or '?' for row in moved))
        self.virtual_moved.update(row.pk for row in moved)
        if not self.apply:
            return
        siblings = rows.filter(parent=None)
        anchors = [row.priority for row in sources + moved if row.parent_id is None]
        parent = AdminMenu.objects.create(
            project=project, role=role, parent=None, has_submenu=True, priority=min(anchors) if anchors else
            (siblings.order_by('-priority').values_list('priority', flat=True).first() or 0) + 1,
            name='mg-' + key, verbose_name=title, frontend_route_url=route, is_active=True,
            active_icon=(data_uri(icon, '#ffffff') if icon else icons_for(route, True)[0]),
            deactive_icon=(data_uri(icon, '#9fb0cc') if icon else icons_for(route, True)[1]))
        for order, row in enumerate(moved, 1):
            row.parent, row.priority = parent, order
            row.save(update_fields=['parent', 'priority'])
        for source in sources:  # a merged group with nothing left is retired, not deleted
            if source.pk != parent.pk and not self.children(self.rows(project, role), source):
                source.is_active = False
                source.save(update_fields=['is_active'])

    def tabs(self, project, role):
        rows = self.rows(project, role)
        for url, allowed in TAB_GROUPS.items():
            parent = self.by_url(rows.filter(parent=None), url)
            if parent is None or (url.startswith(HIDE_SUPERVISION) and not self.options['keep_supervision']):
                continue
            kids = [kid for kid in self.children(rows, parent) if kid.pk not in self.virtual_moved]
            # Only status pages are tabs; anything else (settings, planning) moves out to the top level.
            for kid in kids:
                if canonical(kid.frontend_route_url) not in allowed:
                    self.log(f'move «{kid.verbose_name}» out of «{parent.verbose_name}» (not a status tab)')
                    if self.apply:
                        kid.parent = None
                        kid.priority = (rows.filter(parent=None).order_by('-priority').values_list('priority', flat=True).first() or 0) + 1
                        kid.save(update_fields=['parent', 'priority'])
            kept = [kid for kid in kids if canonical(kid.frontend_route_url) in allowed]
            params = parent.frontend_route_params or {}
            if len(kept) >= 2 and params.get('display') != 'tabs':
                self.log(f'tabs «{parent.verbose_name}»: one sidebar link, {len(kept)} tabs above the page')
                if self.apply:
                    parent.frontend_route_params = {**params, 'display': 'tabs'}
                    parent.save(update_fields=['frontend_route_params'])
