"""First-run setup of a fresh production database: project, roles with grants, menus and the first admin.

Idempotent. Roles that already exist are left alone (use --refresh-grants / --refresh-menus to rewrite them);
the admin account's password comes from BOOTSTRAP_ADMIN_PASSWORD or a prompt and is never printed. Business
data (service types, questionnaires, buildings, ...) is configured afterwards from the admin panel.

  python manage.py bootstrap_saan --admin-phone 09120000000 --admin-name "نام و نام خانوادگی"
"""
import getpass
import os

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from auth_app.management.commands import seed_qa_matrix as spec
from auth_app.menu_icons import icons_for
from auth_app.models import AdminMenu, ExtendedUser, Project, Role, RoleAssignment, RoleView, ViewMethod
from auth_app.permissions import METHOD_CAPABILITIES
from config.models import NavMenu

# key: (title, legacy ExtendedUser.role, Persian name, asset scope, priority)
ROLES = {
    'admin': ('Admin', 'M', 'مدیر کل', 'project', 3),
    'planner': ('Planner', 'M', 'برنامه‌ریز و مدیر خدمات', 'project', 4),
    'support': ('Support', 'S', 'پشتیبان', 'project', 5),
    'warehouse': ('Warehouse', 'S', 'انباردار', 'project', 6),
    'expert': ('Expert', 'P', 'کارشناس میدانی', 'assigned', 7),
    'client': ('Client', 'C', 'مدیر ساختمان (مشتری)', 'client', 8),
    'client_rep': ('ClientRep', 'C', 'نماینده مشتری (فقط مشاهده)', 'client', 9),
}
FIELD_ROLES = ('expert', 'client', 'client_rep')
ADMIN_ROLES = ('admin', 'planner', 'support', 'warehouse')


class Command(BaseCommand):
    help = 'Create the project, roles, grants, menus and first admin of a fresh database (idempotent).'

    def add_arguments(self, parser):
        parser.add_argument('--admin-phone', required=True, help='Login of the first admin (a phone number).')
        parser.add_argument('--admin-name', default='مدیر سامانه')
        parser.add_argument('--project-name', default='saanapp')
        parser.add_argument('--project-name-fa', default='سان')
        parser.add_argument('--refresh-grants', action='store_true', help='Rewrite the grants of existing bootstrap roles.')
        parser.add_argument('--refresh-menus', action='store_true', help='Rebuild the admin menus of existing bootstrap roles.')

    def handle(self, *args, **options):
        phone = options['admin_phone'].strip()
        if not phone.isdigit() or not 10 <= len(phone) <= 15:
            raise CommandError('--admin-phone must be digits only, e.g. 09120000000.')
        existing = User.objects.filter(username=phone).first()
        password = os.environ.get('BOOTSTRAP_ADMIN_PASSWORD') or ''
        if not password and existing is None:
            password = getpass.getpass('Password for the first admin: ') if os.isatty(0) else ''
        if existing is None:
            if not password:
                raise CommandError('Set BOOTSTRAP_ADMIN_PASSWORD (or run interactively) to create the first admin.')
            try:
                validate_password(password)
            except ValidationError as error:
                raise CommandError('Password rejected: ' + ' '.join(error.messages))
        with transaction.atomic():
            project = self.project(options)
            roles, fresh = self.roles(options)
            self.menus(project, roles, fresh, options)
            admin = self.admin(phone, options['admin_name'], password, existing, roles['admin'], project)
        self.stdout.write(self.style.SUCCESS(
            f'Project {project.pk} «{project.name_fa}» ready; roles: {", ".join(role.title for role in roles.values())}; '
            f'admin account {admin.username} {"created" if existing is None else "kept"}.'))

    # ------------------------------------------------------------------ steps
    def project(self, options):
        project, _ = Project.objects.get_or_create(name=options['project_name'], defaults={
            'name_fa': options['project_name_fa'], 'is_active': True})
        return project

    def roles(self, options):
        table = spec.endpoint_table()
        wanted = {
            'admin': {(name, method) for name, routes in table.items() for _, methods in routes for method in methods},
            'planner': spec.pick(table, spec.PLANNER_RULES) | set(spec.SERVICE_ENDPOINTS) | {
                ('ClientListCreateAPIView', 'GET'), ('ProductListCreateAPIView', 'GET')},
            'support': spec.pick(table, spec.SUPPORT_RULES),
            'warehouse': spec.pick(table, spec.WAREHOUSE_RULES),
            'expert': spec.pick(table, spec.EXPERT_FIELD),
            'client': set(spec.CLIENT_GRANTS),
            'client_rep': set(spec.CLIENT_REP_GRANTS),
        }
        roles, fresh = {}, set()
        for key, (title, legacy, verbose, scope, priority) in ROLES.items():
            role = Role.objects.filter(title=title).first()
            created = role is None
            if created:
                role = Role.objects.create(title=title, title_abbreviation=legacy if len(legacy) == 1 else 'M',
                                           verbose_name=verbose, asset_scope=scope, priority=priority, is_active=True)
            roles[key] = role
            if created or options['refresh_grants']:
                fresh.add(key)
                entries = {(name, method) for name, method in wanted[key] if method in METHOD_CAPABILITIES}
                RoleView.objects.filter(role=role).delete()
                views = {entry: ViewMethod.objects.get_or_create(view_name=entry[0], method=entry[1])[0] for entry in entries}
                RoleView.objects.bulk_create([RoleView(role=role, view_method_name=view, **{METHOD_CAPABILITIES[method]: True})
                                              for (name, method), view in views.items()])
                self.stdout.write(f'  role {title}: {len(entries)} grants')
        return roles, fresh

    def menus(self, project, roles, fresh, options):
        for key in FIELD_ROLES:
            if not NavMenu.objects.filter(role=roles[key]).exists():
                for priority, (route, title) in enumerate(spec.FIELD_MENUS[key]):
                    NavMenu.objects.create(role=roles[key], route=route, title=route, title_fa=title,
                                           priority=priority, is_landing=priority == 0)
        for key in ADMIN_ROLES:
            role = roles[key]
            if AdminMenu.objects.filter(project=project, role=role).exists() and not options['refresh_menus']:
                continue
            AdminMenu.objects.filter(project=project, role=role).delete()
            wanted = spec.MENU_FILTERS.get(key)
            priority = 0
            for title, url, children in spec.ADMIN_MENU:
                if wanted is not None and title not in wanted:
                    continue
                priority += 1
                active, inactive = icons_for(url, bool(children))
                parent = AdminMenu.objects.create(
                    project=project, role=role, priority=priority, name=f'sn-{priority}', verbose_name=title,
                    frontend_route_url=url, has_submenu=bool(children), is_active=True, active_icon=active, deactive_icon=inactive)
                for order, (child_title, child_url) in enumerate(children, 1):
                    child_active, child_inactive = icons_for(child_url)
                    AdminMenu.objects.create(
                        project=project, role=role, parent=parent, priority=order, name=f'sn-{priority}-{order}',
                        verbose_name=child_title, frontend_route_url=child_url, is_active=True,
                        active_icon=child_active, deactive_icon=child_inactive)
            # The same command a project runs on an existing menu: status tabs, merged groups, hidden legacy items.
            call_command('restructure_admin_menu', '--project', str(project.pk), '--role', str(role.pk), '--apply',
                         stdout=open(os.devnull, 'w'))

    def admin(self, phone, name, password, existing, role, project):
        user = existing or User(username=phone)
        if existing is None:
            first, _, last = name.partition(' ')
            user.first_name, user.last_name = first, last
            user.is_active = user.is_staff = user.is_superuser = True
            user.set_password(password)
            user.save()
            ExtendedUser.objects.update_or_create(user=user, defaults={'full_name': name, 'role': ExtendedUser.MANAGER})
        RoleAssignment.objects.get_or_create(user=user, role=role, project=project)
        return user
